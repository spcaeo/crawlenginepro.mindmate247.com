#!/usr/bin/env python3
"""
Redis cache for Answer Generation Service
"""

import redis
import json
import hashlib
from typing import Optional
import config

class AnswerCache:
    """Redis-based cache for answer generation results"""

    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.enabled = config.ENABLE_CACHE
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("   Cache disabled - will generate fresh answers each time")
            self.redis_client = None
            self.enabled = False

    def _make_key(self, query: str, context_hash: str, model: str, temp: float) -> str:
        """Generate cache key from query and context"""
        # Create unique key based on query, context, and parameters
        key_data = f"{query}|{context_hash}|{model}|{temp}"
        hash_value = hashlib.md5(key_data.encode()).hexdigest()
        return f"answer:v1:{hash_value}"

    def _hash_context(self, context_chunks: list) -> str:
        """Create hash of context chunks for cache key"""
        # Use chunk IDs and scores for hash
        context_str = "|".join([
            f"{chunk.get('chunk_id', '')}:{chunk.get('score', 0)}"
            for chunk in context_chunks
        ])
        return hashlib.md5(context_str.encode()).hexdigest()[:16]

    def get(
        self,
        query: str,
        context_chunks: list,
        model: str,
        temperature: float
    ) -> Optional[dict]:
        """
        Get cached answer

        Returns:
            Cached answer dict, or None if not cached
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            context_hash = self._hash_context(context_chunks)
            cache_key = self._make_key(query, context_hash, model, temperature)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"⚠️  Cache get error: {e}")
            return None

    def set(
        self,
        query: str,
        context_chunks: list,
        model: str,
        temperature: float,
        answer_data: dict
    ) -> bool:
        """
        Cache answer

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            context_hash = self._hash_context(context_chunks)
            cache_key = self._make_key(query, context_hash, model, temperature)
            cache_value = json.dumps(answer_data)
            self.redis_client.setex(
                cache_key,
                config.CACHE_TTL,
                cache_value
            )
            return True
        except Exception as e:
            print(f"⚠️  Cache set error: {e}")
            return False

    def clear(self) -> int:
        """
        Clear all answer cache entries

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            # Find all answer cache keys
            pattern = "answer:v1:*"
            keys = self.redis_client.keys(pattern)

            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"⚠️  Cache clear error: {e}")
            return 0

# Global cache instance
answer_cache = AnswerCache()
