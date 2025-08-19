import redis
import json
import pickle
import hashlib
import time
import asyncio
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import threading
from functools import wraps
import os

logger = logging.getLogger(__name__)

class AdvancedCacheSystem:
    """
    Multi-tier caching system with Redis, in-memory cache, and intelligent 
    cache management with performance optimization.
    """
    
    def __init__(self):
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=False,  # Keep binary for pickle data
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            self.redis_available = True
            logger.info("✅ Redis cache system initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using memory-only cache: {str(e)}")
            self.redis_client = None
            self.redis_available = False
        
        # Multi-tier in-memory cache
        self.l1_cache = OrderedDict()  # Fastest access, smallest size
        self.l2_cache = OrderedDict()  # Medium access, medium size
        self.l3_cache = OrderedDict()  # Slower access, largest size
        
        # Cache configurations
        self.l1_max_size = 100    # Most frequently accessed
        self.l2_max_size = 500    # Frequently accessed
        self.l3_max_size = 2000   # All cached items
        
        self.default_ttl = 3600   # 1 hour
        self.stats = {
            'hits': defaultdict(int),
            'misses': defaultdict(int),
            'sets': defaultdict(int),
            'evictions': defaultdict(int),
            'errors': defaultdict(int)
        }
        
        # Access patterns for intelligent caching
        self.access_patterns = defaultdict(list)
        self.cache_metadata = {}  # Store metadata about cached items
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Start background cleanup task
        asyncio.create_task(self._background_cleanup())
    
    def _generate_cache_key(self, key: str, namespace: str = "default") -> str:
        """Generate standardized cache key with namespace"""
        return f"aether:{namespace}:{hashlib.md5(key.encode()).hexdigest()}"
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get item from cache with intelligent tier management
        """
        cache_key = self._generate_cache_key(key, namespace)
        
        try:
            with self._lock:
                # Check L1 cache first (fastest)
                if cache_key in self.l1_cache:
                    value, expiry = self.l1_cache[cache_key]
                    if expiry > time.time():
                        # Move to end (most recently used)
                        self.l1_cache.move_to_end(cache_key)
                        self.stats['hits']['l1'] += 1
                        self._record_access(cache_key)
                        return self._deserialize_value(value)
                    else:
                        del self.l1_cache[cache_key]
                
                # Check L2 cache
                if cache_key in self.l2_cache:
                    value, expiry = self.l2_cache[cache_key]
                    if expiry > time.time():
                        # Promote to L1 if frequently accessed
                        self._promote_to_l1(cache_key, value, expiry)
                        self.stats['hits']['l2'] += 1
                        self._record_access(cache_key)
                        return self._deserialize_value(value)
                    else:
                        del self.l2_cache[cache_key]
                
                # Check L3 cache
                if cache_key in self.l3_cache:
                    value, expiry = self.l3_cache[cache_key]
                    if expiry > time.time():
                        # Promote to L2
                        self._promote_to_l2(cache_key, value, expiry)
                        self.stats['hits']['l3'] += 1
                        self._record_access(cache_key)
                        return self._deserialize_value(value)
                    else:
                        del self.l3_cache[cache_key]
                
                # Check Redis if available
                if self.redis_available:
                    try:
                        redis_value = self.redis_client.get(cache_key)
                        if redis_value:
                            deserialized = pickle.loads(redis_value)
                            value, expiry = deserialized
                            
                            if expiry > time.time():
                                # Add to L3 cache
                                self._add_to_l3(cache_key, value, expiry)
                                self.stats['hits']['redis'] += 1
                                self._record_access(cache_key)
                                return self._deserialize_value(value)
                            else:
                                self.redis_client.delete(cache_key)
                    except Exception as e:
                        logger.error(f"Redis get error: {str(e)}")
                        self.stats['errors']['redis'] += 1
                
                # Cache miss
                self.stats['misses'][namespace] += 1
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            self.stats['errors']['general'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  namespace: str = "default", priority: str = "normal") -> bool:
        """
        Set item in cache with intelligent tier placement
        """
        cache_key = self._generate_cache_key(key, namespace)
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        try:
            serialized_value = self._serialize_value(value)
            
            with self._lock:
                # Store metadata
                self.cache_metadata[cache_key] = {
                    'created': time.time(),
                    'ttl': ttl,
                    'namespace': namespace,
                    'priority': priority,
                    'access_count': 0,
                    'size': len(str(serialized_value))
                }
                
                # Determine initial tier based on priority and access patterns
                if priority == "high" or self._is_frequently_accessed(cache_key):
                    self._add_to_l1(cache_key, serialized_value, expiry)
                elif priority == "medium":
                    self._add_to_l2(cache_key, serialized_value, expiry)
                else:
                    self._add_to_l3(cache_key, serialized_value, expiry)
                
                # Store in Redis if available
                if self.redis_available:
                    try:
                        redis_data = pickle.dumps((serialized_value, expiry))
                        self.redis_client.setex(cache_key, ttl, redis_data)
                    except Exception as e:
                        logger.error(f"Redis set error: {str(e)}")
                        self.stats['errors']['redis'] += 1
                
                self.stats['sets'][namespace] += 1
                return True
                
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            self.stats['errors']['general'] += 1
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete item from all cache tiers"""
        cache_key = self._generate_cache_key(key, namespace)
        
        try:
            with self._lock:
                # Remove from all memory tiers
                removed = False
                for cache in [self.l1_cache, self.l2_cache, self.l3_cache]:
                    if cache_key in cache:
                        del cache[cache_key]
                        removed = True
                
                # Remove from metadata
                if cache_key in self.cache_metadata:
                    del self.cache_metadata[cache_key]
                
                # Remove from Redis
                if self.redis_available:
                    try:
                        redis_removed = self.redis_client.delete(cache_key)
                        removed = removed or redis_removed > 0
                    except Exception as e:
                        logger.error(f"Redis delete error: {str(e)}")
                        self.stats['errors']['redis'] += 1
                
                return removed
                
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            self.stats['errors']['general'] += 1
            return False
    
    async def clear_namespace(self, namespace: str = "default") -> int:
        """Clear all items in a namespace"""
        cleared_count = 0
        
        try:
            with self._lock:
                # Find keys to remove
                keys_to_remove = []
                for cache_key, metadata in self.cache_metadata.items():
                    if metadata.get('namespace') == namespace:
                        keys_to_remove.append(cache_key)
                
                # Remove from memory caches
                for cache_key in keys_to_remove:
                    for cache in [self.l1_cache, self.l2_cache, self.l3_cache]:
                        if cache_key in cache:
                            del cache[cache_key]
                            cleared_count += 1
                    
                    if cache_key in self.cache_metadata:
                        del self.cache_metadata[cache_key]
                
                # Clear from Redis (pattern-based deletion)
                if self.redis_available:
                    try:
                        pattern = f"aether:{namespace}:*"
                        redis_keys = self.redis_client.keys(pattern)
                        if redis_keys:
                            self.redis_client.delete(*redis_keys)
                            cleared_count += len(redis_keys)
                    except Exception as e:
                        logger.error(f"Redis clear error: {str(e)}")
                        self.stats['errors']['redis'] += 1
                
                return cleared_count
                
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            self.stats['errors']['general'] += 1
            return 0
    
    def _promote_to_l1(self, cache_key: str, value: Any, expiry: float):
        """Promote item to L1 cache"""
        self._add_to_l1(cache_key, value, expiry)
        # Remove from L2 if present
        if cache_key in self.l2_cache:
            del self.l2_cache[cache_key]
    
    def _promote_to_l2(self, cache_key: str, value: Any, expiry: float):
        """Promote item to L2 cache"""
        self._add_to_l2(cache_key, value, expiry)
        # Remove from L3 if present
        if cache_key in self.l3_cache:
            del self.l3_cache[cache_key]
    
    def _add_to_l1(self, cache_key: str, value: Any, expiry: float):
        """Add item to L1 cache with LRU eviction"""
        self.l1_cache[cache_key] = (value, expiry)
        self.l1_cache.move_to_end(cache_key)
        
        # Evict if over limit
        while len(self.l1_cache) > self.l1_max_size:
            evicted_key, _ = self.l1_cache.popitem(last=False)
            self.stats['evictions']['l1'] += 1
            # Demote to L2
            if evicted_key not in self.l2_cache:
                self._add_to_l2(evicted_key, *self.l1_cache.get(evicted_key, (None, 0)))
    
    def _add_to_l2(self, cache_key: str, value: Any, expiry: float):
        """Add item to L2 cache with LRU eviction"""
        if value is None:
            return
            
        self.l2_cache[cache_key] = (value, expiry)
        self.l2_cache.move_to_end(cache_key)
        
        # Evict if over limit
        while len(self.l2_cache) > self.l2_max_size:
            evicted_key, evicted_data = self.l2_cache.popitem(last=False)
            self.stats['evictions']['l2'] += 1
            # Demote to L3
            if evicted_key not in self.l3_cache and evicted_data[1] > time.time():
                self._add_to_l3(evicted_key, *evicted_data)
    
    def _add_to_l3(self, cache_key: str, value: Any, expiry: float):
        """Add item to L3 cache with LRU eviction"""
        if value is None:
            return
            
        self.l3_cache[cache_key] = (value, expiry)
        self.l3_cache.move_to_end(cache_key)
        
        # Evict if over limit
        while len(self.l3_cache) > self.l3_max_size:
            evicted_key, _ = self.l3_cache.popitem(last=False)
            self.stats['evictions']['l3'] += 1
    
    def _record_access(self, cache_key: str):
        """Record access pattern for intelligent caching"""
        current_time = time.time()
        self.access_patterns[cache_key].append(current_time)
        
        # Keep only recent accesses (last hour)
        hour_ago = current_time - 3600
        self.access_patterns[cache_key] = [
            t for t in self.access_patterns[cache_key] if t > hour_ago
        ]
        
        # Update metadata
        if cache_key in self.cache_metadata:
            self.cache_metadata[cache_key]['access_count'] += 1
    
    def _is_frequently_accessed(self, cache_key: str) -> bool:
        """Determine if a key is frequently accessed"""
        if cache_key not in self.access_patterns:
            return False
        
        recent_accesses = len(self.access_patterns[cache_key])
        return recent_accesses >= 5  # 5 accesses in the last hour
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for storage"""
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value, default=str)
        return value
    
    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize value from storage"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value
    
    async def _background_cleanup(self):
        """Background task to clean expired items"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                current_time = time.time()
                
                with self._lock:
                    # Clean expired items from all tiers
                    for cache in [self.l1_cache, self.l2_cache, self.l3_cache]:
                        expired_keys = []
                        for key, (value, expiry) in cache.items():
                            if expiry <= current_time:
                                expired_keys.append(key)
                        
                        for key in expired_keys:
                            del cache[key]
                            if key in self.cache_metadata:
                                del self.cache_metadata[key]
                    
                    # Clean access patterns older than 1 hour
                    hour_ago = current_time - 3600
                    for key in list(self.access_patterns.keys()):
                        self.access_patterns[key] = [
                            t for t in self.access_patterns[key] if t > hour_ago
                        ]
                        if not self.access_patterns[key]:
                            del self.access_patterns[key]
                
                logger.debug("Cache cleanup completed")
                
            except Exception as e:
                logger.error(f"Background cleanup error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            total_hits = sum(self.stats['hits'].values())
            total_misses = sum(self.stats['misses'].values())
            total_requests = total_hits + total_misses
            hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "hit_rate": f"{hit_rate:.1f}%",
                "total_requests": total_requests,
                "hits_by_tier": dict(self.stats['hits']),
                "misses_by_namespace": dict(self.stats['misses']),
                "sets_by_namespace": dict(self.stats['sets']),
                "evictions_by_tier": dict(self.stats['evictions']),
                "errors": dict(self.stats['errors']),
                "cache_sizes": {
                    "l1": len(self.l1_cache),
                    "l2": len(self.l2_cache),
                    "l3": len(self.l3_cache)
                },
                "memory_usage": {
                    "total_keys": len(self.cache_metadata),
                    "average_item_size": sum(
                        meta.get('size', 0) for meta in self.cache_metadata.values()
                    ) / max(len(self.cache_metadata), 1)
                },
                "redis_available": self.redis_available
            }
    
    def cache_decorator(self, ttl: int = None, namespace: str = "default", 
                       priority: str = "normal"):
        """Decorator for automatic function result caching"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                key_parts = [func.__name__, str(args), str(sorted(kwargs.items()))]
                cache_key = hashlib.md5(str(key_parts).encode()).hexdigest()
                
                # Try to get from cache
                cached_result = await self.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl, namespace, priority)
                
                return result
            
            return wrapper
        return decorator

# Global cache system instance
cache_system = AdvancedCacheSystem()

# Export convenience functions
async def get_cached(key: str, namespace: str = "default") -> Optional[Any]:
    """Convenience function to get from cache"""
    return await cache_system.get(key, namespace)

async def set_cached(key: str, value: Any, ttl: Optional[int] = None, 
                    namespace: str = "default", priority: str = "normal") -> bool:
    """Convenience function to set in cache"""
    return await cache_system.set(key, value, ttl, namespace, priority)

async def delete_cached(key: str, namespace: str = "default") -> bool:
    """Convenience function to delete from cache"""
    return await cache_system.delete(key, namespace)

def cached(ttl: int = None, namespace: str = "default", priority: str = "normal"):
    """Decorator for caching function results"""
    return cache_system.cache_decorator(ttl, namespace, priority)