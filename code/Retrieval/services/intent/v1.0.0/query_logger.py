#!/usr/bin/env python3
"""
Query Logger for Intent Service
Logs low-confidence and rejected queries to JSONL files for monitoring
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import config


def log_query_event(
    query: str,
    intent: str,
    confidence: float,
    language: str,
    complexity: str,
    event_type: str,  # "rejected" or "low_confidence"
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    reasoning: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Log query event to JSONL file

    Args:
        query: User query text
        intent: Detected intent
        confidence: Confidence score (0-1)
        language: Detected language
        complexity: Query complexity
        event_type: "rejected" or "low_confidence"
        tenant_id: Optional tenant/organization ID
        user_id: Optional user ID
        session_id: Optional session ID
        reasoning: LLM reasoning for classification
        error_message: Error message if rejected
    """
    # Create log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "query": query[:500],  # Limit to 500 chars
        "query_length": len(query),
        "intent": intent,
        "confidence": round(confidence, 4),
        "language": language,
        "complexity": complexity,
        "thresholds": {
            "reject": config.CONFIDENCE_THRESHOLD_REJECT,
            "fallback": config.CONFIDENCE_THRESHOLD_FALLBACK
        }
    }

    # Add optional fields
    if tenant_id:
        log_entry["tenant_id"] = tenant_id
    if user_id:
        log_entry["user_id"] = user_id
    if session_id:
        log_entry["session_id"] = session_id
    if reasoning:
        log_entry["reasoning"] = reasoning[:200]  # Limit reasoning text
    if error_message:
        log_entry["error_message"] = error_message

    # Select appropriate log file
    if event_type == "rejected":
        log_file = config.REJECTED_QUERIES_LOG_FILE
    else:
        log_file = config.LOW_CONFIDENCE_LOG_FILE

    # Append to JSONL file (one JSON object per line)
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        # Don't crash service if logging fails
        import logging
        logging.error(f"Failed to write query log: {str(e)}")


def cleanup_old_logs(log_file: Path, retention_days: int) -> int:
    """
    Remove log entries older than retention period

    Args:
        log_file: Path to JSONL log file
        retention_days: Number of days to keep

    Returns:
        Number of entries removed
    """
    from datetime import timedelta

    if not log_file.exists():
        return 0

    cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
    entries_kept = []
    entries_removed = 0

    try:
        # Read all entries
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line.strip())
                entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", ""))

                # Keep if within retention period
                if entry_time >= cutoff_time:
                    entries_kept.append(line)
                else:
                    entries_removed += 1

        # Rewrite file with only recent entries
        if entries_removed > 0:
            with open(log_file, "w", encoding="utf-8") as f:
                f.writelines(entries_kept)

        return entries_removed

    except Exception as e:
        import logging
        logging.error(f"Failed to cleanup old logs: {str(e)}")
        return 0


def get_query_stats(log_file: Path, hours: int = 168) -> dict:  # Default 7 days
    """
    Get statistics from query log file

    Args:
        log_file: Path to JSONL log file
        hours: Number of hours to analyze

    Returns:
        Dictionary with statistics
    """
    from datetime import timedelta

    if not log_file.exists():
        return {"total_queries": 0, "message": "No log file found"}

    stats = {
        "total_queries": 0,
        "by_intent": {},
        "by_language": {},
        "avg_confidence": 0.0,
        "min_confidence": 1.0,
        "max_confidence": 0.0
    }

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    confidences = []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line.strip())
                # Parse timestamp and make timezone-aware comparison
                entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", ""))
                cutoff_time_naive = datetime.utcnow() - timedelta(hours=hours)

                # Filter by time window
                if entry_time < cutoff_time_naive:
                    continue

                stats["total_queries"] += 1

                # Count by intent
                intent = entry.get("intent", "unknown")
                stats["by_intent"][intent] = stats["by_intent"].get(intent, 0) + 1

                # Count by language
                lang = entry.get("language", "unknown")
                stats["by_language"][lang] = stats["by_language"].get(lang, 0) + 1

                # Track confidence
                conf = entry.get("confidence", 0.0)
                confidences.append(conf)
                stats["min_confidence"] = min(stats["min_confidence"], conf)
                stats["max_confidence"] = max(stats["max_confidence"], conf)

        if confidences:
            stats["avg_confidence"] = round(sum(confidences) / len(confidences), 4)

        return stats

    except Exception as e:
        return {"error": str(e)}
