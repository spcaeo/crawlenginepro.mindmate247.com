#!/usr/bin/env python3
"""
Background Pattern Learning Thread
Auto-discovers new patterns from LLM fallback queries

This runs in the background, analyzing queries that required LLM classification
to discover new regex patterns that could speed up future classifications.
"""

import asyncio
import json
import logging
import httpx
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)

class PatternLearner:
    """
    Background thread that learns new patterns from LLM fallback queries

    Process:
    1. Collects queries that required LLM classification
    2. Every N queries (batch_size), analyzes them with meta-LLM
    3. Meta-LLM suggests new regex patterns
    4. Patterns are added to pattern_library.json (with approval if needed)
    """

    def __init__(
        self,
        library_path: str = None,
        queue_path: str = None,
        llm_gateway_url: str = "http://localhost:8075",
        batch_size: int = 10,
        auto_approve_threshold: float = 0.95,
        learning_enabled: bool = True
    ):
        """
        Initialize pattern learner

        Args:
            library_path: Path to pattern_library.json
            queue_path: Path to learning_queue.jsonl
            llm_gateway_url: LLM Gateway URL for meta-analysis
            batch_size: Number of queries to batch before analysis
            auto_approve_threshold: Confidence threshold for auto-approval
            learning_enabled: Enable/disable auto-learning
        """
        if library_path is None:
            library_path = Path(__file__).parent / "pattern_library.json"
        if queue_path is None:
            queue_path = Path(__file__).parent / "learning_queue.jsonl"

        self.library_path = Path(library_path)
        self.queue_path = Path(queue_path)
        self.llm_gateway_url = llm_gateway_url
        self.batch_size = batch_size
        self.auto_approve_threshold = auto_approve_threshold
        self.learning_enabled = learning_enabled

        # In-memory queue
        self.queue = []
        self.processing = False

        # Load existing queue from disk
        self._load_queue()

    def _load_queue(self):
        """Load learning queue from disk"""
        if self.queue_path.exists():
            try:
                with open(self.queue_path, 'r') as f:
                    self.queue = [json.loads(line) for line in f if line.strip()]
                logger.info(f"Loaded {len(self.queue)} queued queries for learning")
            except Exception as e:
                logger.error(f"Failed to load learning queue: {e}")
                self.queue = []

    def _save_queue(self):
        """Save learning queue to disk"""
        try:
            with open(self.queue_path, 'w') as f:
                for item in self.queue:
                    f.write(json.dumps(item) + '\n')
        except Exception as e:
            logger.error(f"Failed to save learning queue: {e}")

    async def add_to_queue(
        self,
        query: str,
        llm_intent: str,
        llm_confidence: float,
        pattern_intent: str = None,
        pattern_confidence: float = None
    ):
        """
        Add query to learning queue

        Args:
            query: The query string
            llm_intent: Intent classified by LLM
            llm_confidence: LLM classification confidence
            pattern_intent: Intent from pattern match (if any)
            pattern_confidence: Pattern match confidence (if any)
        """
        if not self.learning_enabled:
            return

        # Add to queue
        self.queue.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "llm_intent": llm_intent,
            "llm_confidence": llm_confidence,
            "pattern_intent": pattern_intent,
            "pattern_confidence": pattern_confidence,
            "mismatch": pattern_intent is not None and pattern_intent != llm_intent
        })

        # Save to disk periodically
        if len(self.queue) % 5 == 0:
            self._save_queue()

        # Trigger learning if batch is ready
        if len(self.queue) >= self.batch_size and not self.processing:
            await self.run_learning_cycle()

    async def run_learning_cycle(self):
        """
        Analyze queued queries and discover new patterns
        Runs in background, non-blocking
        """
        if self.processing or not self.learning_enabled:
            return

        self.processing = True
        logger.info(f"🎓 Starting pattern learning cycle with {len(self.queue)} queries")

        try:
            # Group queries by intent
            intent_groups = defaultdict(list)
            for item in self.queue:
                intent_groups[item["llm_intent"]].append(item["query"])

            # Analyze each intent group
            new_patterns_discovered = 0
            for intent, queries in intent_groups.items():
                if len(queries) < 3:  # Need at least 3 examples
                    continue

                # Ask meta-LLM to discover patterns
                suggestions = await self._discover_patterns(intent, queries)

                if suggestions:
                    # Add to pattern library
                    added = await self._add_patterns_to_library(intent, suggestions)
                    new_patterns_discovered += added

            # Clear processed queue
            self.queue.clear()
            self._save_queue()

            logger.info(f"✅ Learning cycle complete. Discovered {new_patterns_discovered} new patterns")

        except Exception as e:
            logger.error(f"Pattern learning cycle failed: {e}")

        finally:
            self.processing = False

    async def _discover_patterns(self, intent: str, queries: List[str]) -> List[Dict]:
        """
        Use meta-LLM to discover regex patterns from example queries

        Args:
            intent: The intent type
            queries: List of example queries for this intent

        Returns:
            List of suggested pattern objects
        """
        # Build meta-prompt for pattern discovery
        meta_prompt = self._build_discovery_prompt(intent, queries)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.llm_gateway_url}/v1/chat/completions",
                    json={
                        "model": "Qwen3-32B",  # Use reasoning model for pattern discovery
                        "messages": [
                            {"role": "user", "content": meta_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1024
                    }
                )
                response.raise_for_status()

                data = response.json()
                llm_response = data["choices"][0]["message"]["content"]

                # Clean and parse JSON response
                llm_response = llm_response.strip()
                if llm_response.startswith("```json"):
                    llm_response = llm_response[7:]
                if llm_response.startswith("```"):
                    llm_response = llm_response[3:]
                if llm_response.endswith("```"):
                    llm_response = llm_response[:-3]
                llm_response = llm_response.strip()

                suggestions = json.loads(llm_response)
                return suggestions.get("patterns", [])

        except Exception as e:
            logger.error(f"Pattern discovery failed for intent '{intent}': {e}")
            return []

    def _build_discovery_prompt(self, intent: str, queries: List[str]) -> str:
        """Build meta-prompt for pattern discovery"""
        query_list = "\n".join([f"- \"{q}\"" for q in queries[:20]])  # Limit to 20 examples

        return f"""You are a regex pattern discovery expert. Analyze these queries and suggest regex patterns.

Intent Type: {intent}

Example Queries:
{query_list}

Task:
1. Identify common linguistic patterns across these queries
2. Suggest 1-3 regex patterns that would match 70%+ of these examples
3. Ensure patterns are specific enough (avoid overly broad matches)
4. Provide confidence score based on pattern specificity

Output JSON format:
{{
  "patterns": [
    {{
      "regex": "<regex pattern>",
      "confidence": 0.0-1.0,
      "examples": ["example 1", "example 2"],
      "description": "Brief description of what this pattern matches"
    }}
  ]
}}

IMPORTANT:
- Use case-insensitive patterns (we'll add re.IGNORECASE flag)
- Escape special regex characters properly
- Avoid patterns that would match unrelated intents
- Focus on query structure, not specific domain words
- Be conservative - better to have fewer high-quality patterns

Respond with ONLY valid JSON."""

    async def _add_patterns_to_library(self, intent: str, suggestions: List[Dict]) -> int:
        """
        Add discovered patterns to pattern_library.json

        Args:
            intent: The intent type
            suggestions: List of pattern suggestions from meta-LLM

        Returns:
            Number of patterns added
        """
        try:
            # Load current library
            with open(self.library_path, 'r') as f:
                library = json.load(f)

            if intent not in library["patterns"]:
                library["patterns"][intent] = {
                    "priority": 2,
                    "description": f"Auto-learned patterns for {intent}",
                    "patterns": []
                }

            added_count = 0
            for suggestion in suggestions:
                confidence = suggestion.get("confidence", 0.8)

                # Auto-approve high-confidence patterns
                if confidence >= self.auto_approve_threshold:
                    approve = True
                else:
                    # Log for manual review
                    logger.warning(
                        f"Pattern suggestion below auto-approve threshold ({confidence:.2f} < {self.auto_approve_threshold}): "
                        f"{suggestion.get('regex')} for intent '{intent}'"
                    )
                    approve = False  # Could add human-in-the-loop here

                if approve:
                    # Add to library
                    library["patterns"][intent]["patterns"].append({
                        "regex": suggestion["regex"],
                        "confidence": confidence,
                        "examples": suggestion.get("examples", []),
                        "match_count": 0,
                        "accuracy": None,
                        "added_date": datetime.now().isoformat(),
                        "source": "auto_learned",
                        "description": suggestion.get("description", "")
                    })
                    added_count += 1
                    logger.info(f"✨ New pattern learned for '{intent}': {suggestion['regex']} (confidence: {confidence:.2f})")

            # Update library metadata
            library["last_updated"] = datetime.now().isoformat()
            library["learning_stats"]["patterns_learned"] = library.get("learning_stats", {}).get("patterns_learned", 0) + added_count

            # Save updated library
            with open(self.library_path, 'w') as f:
                json.dump(library, f, indent=2)

            # Reload patterns in matcher
            from pattern_matcher import get_matcher
            matcher = get_matcher()
            matcher.reload_patterns()

            return added_count

        except Exception as e:
            logger.error(f"Failed to add patterns to library: {e}")
            return 0


# Global learner instance
_global_learner = None

def get_learner(**kwargs) -> PatternLearner:
    """Get global PatternLearner instance"""
    global _global_learner
    if _global_learner is None:
        _global_learner = PatternLearner(**kwargs)
    return _global_learner
