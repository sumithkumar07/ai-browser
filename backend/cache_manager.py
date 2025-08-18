import redis
import json
import hashlib
import asyncio
from typing import Optional, Dict, Any, List
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        try:
            self.redis_client = redis.Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            self.redis_available = True
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Using in-memory cache.")
            self.redis_available = False
            self.memory_cache = {}
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate cache key with hash"""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        try:
            if self.redis_available:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set item in cache with TTL"""
        try:
            if self.redis_available:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                # Simple memory cache with cleanup
                self.memory_cache[key] = {
                    'data': value,
                    'expires': datetime.utcnow() + timedelta(seconds=ttl)
                }
                # Cleanup expired items (simple approach)
                if len(self.memory_cache) > 1000:
                    self._cleanup_memory_cache()
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Clean up expired items from memory cache"""
        now = datetime.utcnow()
        expired_keys = [
            k for k, v in self.memory_cache.items() 
            if isinstance(v, dict) and v.get('expires', now) < now
        ]
        for key in expired_keys:
            del self.memory_cache[key]
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache"""
        try:
            if self.redis_available:
                self.redis_client.delete(key)
            else:
                self.memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            if self.redis_available:
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            else:
                # Simple pattern matching for memory cache
                import fnmatch
                matching_keys = [
                    k for k in self.memory_cache.keys() 
                    if fnmatch.fnmatch(k, pattern)
                ]
                for key in matching_keys:
                    del self.memory_cache[key]
                return len(matching_keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
        return 0
    
    # Specific cache methods for AETHER
    
    async def cache_page_content(self, url: str, content: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache webpage content (30 minutes default)"""
        key = self._generate_key("page", url)
        return await self.set(key, content, ttl)
    
    async def get_cached_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached webpage content"""
        key = self._generate_key("page", url)
        return await self.get(key)
    
    async def cache_ai_response(self, query: str, context: str, response: str, provider: str, ttl: int = 300) -> bool:
        """Cache AI response (5 minutes default)"""
        cache_data = {
            'response': response,
            'provider': provider,
            'timestamp': datetime.utcnow().isoformat()
        }
        key = self._generate_key("ai", f"{query}_{context}")
        return await self.set(key, cache_data, ttl)
    
    async def get_cached_ai_response(self, query: str, context: str) -> Optional[Dict[str, Any]]:
        """Get cached AI response"""
        key = self._generate_key("ai", f"{query}_{context}")
        return await self.get(key)
    
    async def cache_recommendations(self, user_pattern: str, recommendations: List[Dict], ttl: int = 900) -> bool:
        """Cache AI recommendations (15 minutes default)"""
        key = self._generate_key("rec", user_pattern)
        return await self.set(key, recommendations, ttl)
    
    async def get_cached_recommendations(self, user_pattern: str) -> Optional[List[Dict]]:
        """Get cached recommendations"""
        key = self._generate_key("rec", user_pattern)
        return await self.get(key)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'type': 'redis' if self.redis_available else 'memory',
            'connected': self.redis_available
        }
        
        try:
            if self.redis_available:
                info = self.redis_client.info()
                stats.update({
                    'keys': self.redis_client.dbsize(),
                    'memory_usage': info.get('used_memory_human', 'N/A'),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                })
            else:
                stats.update({
                    'keys': len(self.memory_cache),
                    'memory_usage': f"{len(str(self.memory_cache))} bytes (approx)"
                })
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            
        return stats

# Global cache manager instance
cache_manager = CacheManager()