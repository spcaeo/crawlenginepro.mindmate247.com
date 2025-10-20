#!/usr/bin/env python3
"""
Response caching for Embeddings Service v3.0.1
LRU cache with TTL for embeddings responses
"""

import time
from collections import OrderedDict
from typing import Optional, List, Any


class EmbeddingsCache:
    """LRU cache with TTL for embeddings responses"""

    def __init__(self, max_size: int = 10000, ttl: int = 7200):
        """
        Initialize cache

        Args:
            max_size: Maximum number of entries
            ttl: Time-to-live in seconds (default 2 hours)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _generate_key(self, texts: List[str], model: str, normalize: bool) -> str:
        """Generate cache key from request parameters"""
        text_key = "|".join(texts)
        return f"{text_key}_{model}_{normalize}"

    def get(self, texts: List[str], model: str, normalize: bool) -> Optional[Any]:
        """
        Get cached embeddings response

        Args:
            texts: Input texts
            model: Model name
            normalize: Normalization flag

        Returns:
            Cached response or None if not found/expired
        """
        key = self._generate_key(texts, model, normalize)

        if key in self.cache:
            entry = self.cache[key]
            age = time.time() - entry["timestamp"]

            # Check if expired
            if age > self.ttl:
                del self.cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1

            # Add cache age to response
            response = entry["response"].copy()
            response["cached"] = True
            response["cache_age_seconds"] = age

            return response

        self.misses += 1
        return None

    def set(self, texts: List[str], model: str, normalize: bool, response: Any):
        """
        Cache embeddings response

        Args:
            texts: Input texts
            model: Model name
            normalize: Normalization flag
            response: Response to cache
        """
        key = self._generate_key(texts, model, normalize)

        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)

        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "enabled": True,  # Cache object exists, so it's enabled
            "entries": len(self.cache),  # Changed from "size" to match health response
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl
        }


# Global cache instance
embeddings_cache = EmbeddingsCache()
