#!/usr/bin/env python3
"""
Fast Pattern Matcher for Intent Detection
Provides 0ms intent classification for common query patterns
"""

import re
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class PatternMatcher:
    """
    Fast regex-based pattern matcher for intent detection

    Performance:
    - Pattern match: ~0-5ms (regex compilation cached)
    - LLM fallback: ~2000-3000ms

    Achieves 70-80% pattern match rate on typical queries
    """

    def __init__(self, library_path: str = None):
        """
        Initialize pattern matcher with pattern library

        Args:
            library_path: Path to pattern_library.json (auto-detected if None)
        """
        if library_path is None:
            library_path = Path(__file__).parent / "pattern_library.json"

        self.library_path = Path(library_path)
        self.patterns = {}
        self.compiled_patterns = {}
        self.stats = {
            "total_queries": 0,
            "pattern_hits": 0,
            "llm_fallbacks": 0,
            "avg_confidence": 0.0
        }

        # Load pattern library
        self.reload_patterns()

    def reload_patterns(self):
        """
        Reload patterns from JSON file
        Called on startup and after pattern learning updates
        """
        try:
            with open(self.library_path, 'r') as f:
                library = json.load(f)

            self.patterns = library.get("patterns", {})
            self.confidence_thresholds = library.get("confidence_thresholds", {
                "high": 0.90,
                "medium": 0.70,
                "low": 0.50
            })

            # Compile regex patterns for speed
            self.compiled_patterns = {}
            for intent, intent_data in self.patterns.items():
                self.compiled_patterns[intent] = []

                for pattern_obj in intent_data.get("patterns", []):
                    try:
                        compiled = re.compile(
                            pattern_obj["regex"],
                            re.IGNORECASE | re.MULTILINE
                        )
                        self.compiled_patterns[intent].append({
                            "regex": compiled,
                            "confidence": pattern_obj.get("confidence", 0.85),
                            "pattern_obj": pattern_obj  # Keep reference for stats
                        })
                    except re.error as e:
                        logger.error(f"Invalid regex pattern for {intent}: {pattern_obj['regex']} - {e}")

            logger.info(f"Loaded {len(self.compiled_patterns)} intent patterns from {self.library_path}")

        except FileNotFoundError:
            logger.error(f"Pattern library not found: {self.library_path}")
            self.patterns = {}
            self.compiled_patterns = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in pattern library: {e}")
            self.patterns = {}
            self.compiled_patterns = {}

    def match(self, query: str) -> Optional[Tuple[str, float, str]]:
        """
        Fast pattern-based intent matching

        Args:
            query: User query string

        Returns:
            Tuple of (intent, confidence, matched_pattern) if match found
            None if no confident pattern match

        Example:
            >>> matcher.match("Compare iPhone and Samsung")
            ('comparison', 0.95, '^compare\\s+')
        """
        self.stats["total_queries"] += 1

        query_normalized = query.strip()

        # Try to match patterns in priority order
        # Higher priority intents are checked first (e.g., comparison before factual_retrieval)
        intent_priorities = sorted(
            self.compiled_patterns.items(),
            key=lambda x: self.patterns.get(x[0], {}).get("priority", 99)
        )

        best_match = None
        best_confidence = 0.0
        best_pattern = None

        for intent, pattern_list in intent_priorities:
            for pattern_data in pattern_list:
                regex = pattern_data["regex"]
                confidence = pattern_data["confidence"]

                if regex.search(query_normalized):
                    # Match found!
                    if confidence > best_confidence:
                        best_match = intent
                        best_confidence = confidence
                        best_pattern = pattern_data["pattern_obj"]["regex"]

                        # Update pattern statistics
                        pattern_data["pattern_obj"]["match_count"] = \
                            pattern_data["pattern_obj"].get("match_count", 0) + 1

        if best_match and best_confidence >= self.confidence_thresholds["low"]:
            self.stats["pattern_hits"] += 1
            self.stats["avg_confidence"] = (
                (self.stats["avg_confidence"] * (self.stats["pattern_hits"] - 1) + best_confidence)
                / self.stats["pattern_hits"]
            )

            logger.debug(f"Pattern match: '{query[:50]}...' → {best_match} (confidence: {best_confidence:.2f})")
            return (best_match, best_confidence, best_pattern)

        # No confident pattern match - needs LLM
        self.stats["llm_fallbacks"] += 1
        return None

    def get_confidence_level(self, confidence: float) -> str:
        """Get confidence level label"""
        if confidence >= self.confidence_thresholds["high"]:
            return "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "medium"
        else:
            return "low"

    def get_stats(self) -> Dict:
        """Get matcher statistics"""
        hit_rate = (
            self.stats["pattern_hits"] / self.stats["total_queries"] * 100
            if self.stats["total_queries"] > 0
            else 0.0
        )

        return {
            **self.stats,
            "pattern_hit_rate": round(hit_rate, 2),
            "llm_fallback_rate": round(100 - hit_rate, 2)
        }

    def update_pattern_stats(self, intent: str, pattern_regex: str, correct: bool):
        """
        Update pattern accuracy based on LLM verification

        Args:
            intent: The intent that was pattern-matched
            pattern_regex: The regex that matched
            correct: Whether LLM agreed with the pattern classification
        """
        if intent not in self.patterns:
            return

        for pattern_obj in self.patterns[intent].get("patterns", []):
            if pattern_obj["regex"] == pattern_regex:
                # Update accuracy tracking
                if pattern_obj.get("accuracy") is None:
                    pattern_obj["accuracy"] = {"correct": 0, "incorrect": 0}

                if correct:
                    pattern_obj["accuracy"]["correct"] += 1
                else:
                    pattern_obj["accuracy"]["incorrect"] += 1

                # Save updated stats back to file
                self._save_library()
                break

    def _save_library(self):
        """Save updated pattern library to disk"""
        try:
            with open(self.library_path, 'r') as f:
                library = json.load(f)

            # Update patterns with new stats
            library["patterns"] = self.patterns
            library["last_updated"] = datetime.now().isoformat()

            with open(self.library_path, 'w') as f:
                json.dump(library, f, indent=2)

            logger.debug(f"Updated pattern library: {self.library_path}")

        except Exception as e:
            logger.error(f"Failed to save pattern library: {e}")


# Global instance (singleton pattern)
_global_matcher = None

def get_matcher() -> PatternMatcher:
    """Get global PatternMatcher instance"""
    global _global_matcher
    if _global_matcher is None:
        _global_matcher = PatternMatcher()
    return _global_matcher
