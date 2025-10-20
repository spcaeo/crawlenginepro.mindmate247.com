#!/usr/bin/env python3
"""
LLM Gateway v2.0.0 - Response Caching
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class CacheEntry:
    """Cached response entry"""
    response: Dict[str, Any]
    timestamp: float
    hits: int = 0

class ResponseCache:
    """In-memory response cache with TTL"""

    def __init__(self, ttl: int = 3600, max_size: int = 1000):
        """
        Initialize cache

        Args:
            ttl: Time to live in seconds (default: 1 hour)
            max_size: Maximum number of cached entries (default: 1000)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.ttl = ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _generate_key(self, model: str, messages: list, temperature: float, max_tokens: Optional[int]) -> str:
        """Generate cache key from request parameters"""
        # Create deterministic string from request
        cache_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def get(self, model: str, messages: list, temperature: float, max_tokens: Optional[int]) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        key = self._generate_key(model, messages, temperature, max_tokens)

        if key in self.cache:
            entry = self.cache[key]

            # Check if expired
            if time.time() - entry.timestamp > self.ttl:
                del self.cache[key]
                self.misses += 1
                return None

            # Cache hit
            entry.hits += 1
            self.hits += 1

            # Add cache metadata to response
            response = entry.response.copy()
            response["cached"] = True
            response["cache_age_seconds"] = time.time() - entry.timestamp

            return response

        self.misses += 1
        return None

    def set(self, model: str, messages: list, temperature: float, max_tokens: Optional[int], response: Dict[str, Any]):
        """Cache a response"""
        # Don't cache if at max size - simple eviction
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
            del self.cache[oldest_key]

        key = self._generate_key(model, messages, temperature, max_tokens)
        self.cache[key] = CacheEntry(
            response=response,
            timestamp=time.time()
        )

    def clear(self):
        """Clear all cached entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }

# Global cache instance - configured from environment variables
import os
from pathlib import Path
from dotenv import load_dotenv

# Load common .env from PipeLineServices root
env_path = Path(__file__).resolve().parents[5] / ".env"
load_dotenv(env_path)

# Get cache configuration from environment
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "1000"))
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"

# Create cache instance
response_cache = ResponseCache(ttl=CACHE_TTL, max_size=CACHE_MAX_SIZE)

# Disable cache if environment variable says so
if not ENABLE_CACHE:
    # Override cache methods to disable caching
    response_cache.get = lambda *args, **kwargs: None
    response_cache.set = lambda *args, **kwargs: False
    print("⚠️  LLM Gateway cache DISABLED via ENABLE_CACHE=false")
