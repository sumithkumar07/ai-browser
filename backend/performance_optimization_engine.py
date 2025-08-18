"""
PHASE 2: Advanced Performance Optimization Engine
Real-time performance monitoring, intelligent caching, and auto-optimization
"""

import asyncio
import time
import json
import logging
import statistics
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import psutil
import threading
from collections import defaultdict, deque
import hashlib

import redis
import aiofiles
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configure logging
logger = structlog.get_logger(__name__)

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DISK = "l3_disk"

class PerformanceMetric(Enum):
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    CACHE_HIT_RATE = "cache_hit_rate"
    DB_QUERY_TIME = "db_query_time"

@dataclass
class PerformanceThreshold:
    metric: PerformanceMetric
    warning_level: float
    critical_level: float
    unit: str

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    ttl: Optional[int] = None
    size_bytes: int = 0

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    response_times: List[float] = field(default_factory=list)

class IntelligentCacheManager:
    """
    Multi-layer intelligent caching system with AI-powered optimization
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        # L1: In-memory cache (fastest)
        self.l1_cache: Dict[str, CacheEntry] = {}
        self.l1_max_size = 1000
        self.l1_max_memory = 100 * 1024 * 1024  # 100MB
        
        # L2: Redis cache (fast, persistent)
        self.redis_client = redis_client
        self.l2_enabled = redis_client is not None
        
        # L3: Disk cache (slower, large capacity)
        self.l3_cache_dir = "/tmp/aether_cache"
        self.l3_max_size = 10 * 1024 * 1024 * 1024  # 10GB
        
        # Cache statistics
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "evictions": 0,
            "promotions": 0
        }
        
        # Access patterns for AI optimization
        self.access_patterns = defaultdict(list)
        self.hot_keys = set()
        
        # Background optimization
        self.optimization_enabled = True
        asyncio.create_task(self._optimization_worker())
    
    async def get(self, key: str, context: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Get value from cache with intelligent promotion and optimization
        """
        # Try L1 cache first
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not self._is_expired(entry):
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                self.stats["l1_hits"] += 1
                self._record_access_pattern(key, "l1_hit", context)
                return entry.value
            else:
                del self.l1_cache[key]
        
        # Try L2 cache (Redis)
        if self.l2_enabled:
            try:
                cached_data = await asyncio.to_thread(self.redis_client.get, key)
                if cached_data:
                    value = json.loads(cached_data)
                    self.stats["l2_hits"] += 1
                    self._record_access_pattern(key, "l2_hit", context)
                    
                    # Promote to L1 if frequently accessed
                    if await self._should_promote_to_l1(key, context):
                        await self.set(key, value, level=CacheLevel.L1_MEMORY, ttl=3600)
                        self.stats["promotions"] += 1
                    
                    return value
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Try L3 cache (Disk)
        try:
            l3_path = self._get_l3_path(key)
            if await aiofiles.os.path.exists(l3_path):
                async with aiofiles.open(l3_path, 'r') as f:
                    cached_data = await f.read()
                    cache_entry = json.loads(cached_data)
                    
                    if not self._is_l3_expired(cache_entry):
                        value = cache_entry["value"]
                        self.stats["l3_hits"] += 1
                        self._record_access_pattern(key, "l3_hit", context)
                        
                        # Consider promotion based on access frequency
                        if await self._should_promote_to_l2(key, context):
                            await self.set(key, value, level=CacheLevel.L2_REDIS, ttl=7200)
                            self.stats["promotions"] += 1
                        
                        return value
        except Exception as e:
            logger.warning(f"L3 cache error: {e}")
        
        # Cache miss
        self.stats["misses"] += 1
        self._record_access_pattern(key, "miss", context)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        level: Optional[CacheLevel] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set value in cache with intelligent placement
        """
        if level is None:
            level = await self._determine_optimal_level(key, value, context)
        
        value_size = len(json.dumps(value).encode('utf-8'))
        
        if level == CacheLevel.L1_MEMORY:
            await self._ensure_l1_capacity(value_size)
            
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                ttl=ttl,
                size_bytes=value_size
            )
            
            self.l1_cache[key] = entry
            return True
        
        elif level == CacheLevel.L2_REDIS and self.l2_enabled:
            try:
                serialized = json.dumps(value)
                ttl_seconds = ttl or 3600
                await asyncio.to_thread(
                    self.redis_client.setex,
                    key,
                    ttl_seconds,
                    serialized
                )
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                return False
        
        elif level == CacheLevel.L3_DISK:
            try:
                l3_path = self._get_l3_path(key)
                await aiofiles.os.makedirs(os.path.dirname(l3_path), exist_ok=True)
                
                cache_entry = {
                    "value": value,
                    "created_at": datetime.now().isoformat(),
                    "ttl": ttl
                }
                
                async with aiofiles.open(l3_path, 'w') as f:
                    await f.write(json.dumps(cache_entry))
                
                return True
            except Exception as e:
                logger.error(f"L3 set error: {e}")
                return False
        
        return False
    
    async def _determine_optimal_level(
        self,
        key: str,
        value: Any,
        context: Optional[Dict[str, Any]]
    ) -> CacheLevel:
        """
        Use AI to determine optimal cache level
        """
        value_size = len(json.dumps(value).encode('utf-8'))
        
        # Small, frequently accessed items go to L1
        if value_size < 1024 and key in self.hot_keys:
            return CacheLevel.L1_MEMORY
        
        # Medium items with moderate access go to L2
        if value_size < 1024 * 1024 and self.l2_enabled:
            return CacheLevel.L2_REDIS
        
        # Large items or infrequent access go to L3
        return CacheLevel.L3_DISK
    
    async def _should_promote_to_l1(self, key: str, context: Optional[Dict[str, Any]]) -> bool:
        """Determine if key should be promoted to L1 cache"""
        access_history = self.access_patterns[key]
        
        if len(access_history) < 3:
            return False
        
        # Promote if accessed frequently in last hour
        recent_accesses = [
            a for a in access_history 
            if datetime.now() - a["timestamp"] < timedelta(hours=1)
        ]
        
        return len(recent_accesses) >= 3
    
    async def _should_promote_to_l2(self, key: str, context: Optional[Dict[str, Any]]) -> bool:
        """Determine if key should be promoted to L2 cache"""
        access_history = self.access_patterns[key]
        
        if len(access_history) < 2:
            return False
        
        # Promote if accessed in last 24 hours
        recent_accesses = [
            a for a in access_history 
            if datetime.now() - a["timestamp"] < timedelta(hours=24)
        ]
        
        return len(recent_accesses) >= 2
    
    async def _ensure_l1_capacity(self, new_item_size: int):
        """Ensure L1 cache has capacity for new item"""
        current_memory = sum(entry.size_bytes for entry in self.l1_cache.values())
        
        # Evict items if necessary
        while (len(self.l1_cache) >= self.l1_max_size or 
               current_memory + new_item_size > self.l1_max_memory):
            
            # Find least recently used item
            lru_key = min(
                self.l1_cache.keys(),
                key=lambda k: self.l1_cache[k].accessed_at
            )
            
            evicted_entry = self.l1_cache.pop(lru_key)
            current_memory -= evicted_entry.size_bytes
            self.stats["evictions"] += 1
            
            # Demote to L2 if valuable
            if (evicted_entry.access_count > 2 and 
                self.l2_enabled and 
                not self._is_expired(evicted_entry)):
                
                await self.set(
                    lru_key,
                    evicted_entry.value,
                    level=CacheLevel.L2_REDIS,
                    ttl=7200
                )
    
    def _record_access_pattern(self, key: str, access_type: str, context: Optional[Dict[str, Any]]):
        """Record access pattern for AI optimization"""
        pattern = {
            "timestamp": datetime.now(),
            "access_type": access_type,
            "context": context or {}
        }
        
        self.access_patterns[key].append(pattern)
        
        # Keep only recent patterns (last 1000)
        if len(self.access_patterns[key]) > 1000:
            self.access_patterns[key] = self.access_patterns[key][-1000:]
        
        # Update hot keys
        if access_type.endswith("_hit"):
            recent_hits = sum(
                1 for p in self.access_patterns[key][-10:]
                if p["access_type"].endswith("_hit")
            )
            
            if recent_hits >= 7:  # 70% hit rate in last 10 accesses
                self.hot_keys.add(key)
    
    async def _optimization_worker(self):
        """Background worker for cache optimization"""
        while self.optimization_enabled:
            try:
                await self._optimize_cache_placement()
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Cache optimization error: {e}")
                await asyncio.sleep(60)
    
    async def _optimize_cache_placement(self):
        """Optimize cache placement based on access patterns"""
        
        # Analyze access patterns
        for key, patterns in self.access_patterns.items():
            if len(patterns) < 10:
                continue
            
            recent_patterns = patterns[-50:]  # Last 50 accesses
            
            hit_rate = sum(
                1 for p in recent_patterns 
                if p["access_type"].endswith("_hit")
            ) / len(recent_patterns)
            
            access_frequency = len([
                p for p in recent_patterns
                if datetime.now() - p["timestamp"] < timedelta(hours=1)
            ])
            
            # Promote frequently accessed items
            if hit_rate > 0.8 and access_frequency > 10:
                if key not in self.l1_cache and self.l2_enabled:
                    # Try to get from L2 and promote to L1
                    try:
                        cached_data = await asyncio.to_thread(self.redis_client.get, key)
                        if cached_data:
                            value = json.loads(cached_data)
                            await self.set(key, value, level=CacheLevel.L1_MEMORY)
                            logger.info(f"Promoted key {key} to L1 cache")
                    except Exception as e:
                        logger.warning(f"Promotion error for {key}: {e}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        if entry.ttl is None:
            return False
        
        age = (datetime.now() - entry.created_at).total_seconds()
        return age > entry.ttl
    
    def _is_l3_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if L3 cache entry is expired"""
        ttl = cache_entry.get("ttl")
        if ttl is None:
            return False
        
        created_at = datetime.fromisoformat(cache_entry["created_at"])
        age = (datetime.now() - created_at).total_seconds()
        return age > ttl
    
    def _get_l3_path(self, key: str) -> str:
        """Get file path for L3 cache entry"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{self.l3_cache_dir}/{key_hash[:2]}/{key_hash}.json"
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        total_requests = sum(self.stats.values())
        
        l1_size = len(self.l1_cache)
        l1_memory = sum(entry.size_bytes for entry in self.l1_cache.values())
        
        return {
            "l1_cache": {
                "size": l1_size,
                "memory_usage": l1_memory,
                "max_size": self.l1_max_size,
                "max_memory": self.l1_max_memory
            },
            "l2_cache": {
                "enabled": self.l2_enabled
            },
            "stats": self.stats,
            "hit_rates": {
                "l1": self.stats["l1_hits"] / max(total_requests, 1),
                "l2": self.stats["l2_hits"] / max(total_requests, 1),
                "l3": self.stats["l3_hits"] / max(total_requests, 1),
                "overall": (self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]) / max(total_requests, 1)
            },
            "hot_keys_count": len(self.hot_keys)
        }


class PerformanceMonitoringSystem:
    """
    Real-time system performance monitoring with predictive analytics
    """
    
    def __init__(self):
        # Performance thresholds
        self.thresholds = {
            PerformanceMetric.RESPONSE_TIME: PerformanceThreshold(
                PerformanceMetric.RESPONSE_TIME, 1.0, 5.0, "seconds"
            ),
            PerformanceMetric.CPU_USAGE: PerformanceThreshold(
                PerformanceMetric.CPU_USAGE, 70.0, 90.0, "percent"
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                PerformanceMetric.MEMORY_USAGE, 75.0, 90.0, "percent"
            ),
            PerformanceMetric.ERROR_RATE: PerformanceThreshold(
                PerformanceMetric.ERROR_RATE, 1.0, 5.0, "percent"
            )
        }
        
        # Metrics storage
        self.metrics_buffer = deque(maxlen=1000)
        self.system_metrics = deque(maxlen=100)
        self.api_metrics = defaultdict(list)
        
        # Prometheus metrics
        self.response_time_histogram = Histogram(
            'aether_response_time_seconds',
            'Response time in seconds',
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.request_counter = Counter(
            'aether_requests_total',
            'Total requests',
            ['method', 'endpoint', 'status']
        )
        
        self.active_connections = Gauge(
            'aether_active_connections',
            'Number of active connections'
        )
        
        self.system_cpu_usage = Gauge('aether_cpu_usage_percent', 'CPU usage percentage')
        self.system_memory_usage = Gauge('aether_memory_usage_percent', 'Memory usage percentage')
        
        # Background monitoring
        self.monitoring_enabled = True
        asyncio.create_task(self._monitoring_worker())
        
        # Start Prometheus metrics server
        try:
            start_http_server(8000)
            logger.info("Prometheus metrics server started on port 8000")
        except Exception as e:
            logger.warning(f"Failed to start Prometheus server: {e}")
    
    def record_api_performance(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int,
        user_session: Optional[str] = None
    ):
        """Record API performance metrics"""
        
        # Update Prometheus metrics
        self.response_time_histogram.observe(response_time)
        self.request_counter.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        # Store detailed metrics
        metric = {
            "timestamp": datetime.now(),
            "endpoint": endpoint,
            "method": method,
            "response_time": response_time,
            "status_code": status_code,
            "user_session": user_session
        }
        
        self.metrics_buffer.append(metric)
        self.api_metrics[endpoint].append(metric)
        
        # Keep only recent metrics per endpoint
        if len(self.api_metrics[endpoint]) > 1000:
            self.api_metrics[endpoint] = self.api_metrics[endpoint][-1000:]
        
        # Check for performance issues
        self._check_performance_thresholds(metric)
    
    def record_ai_provider_performance(
        self,
        provider: str,
        query_type: str,
        response_time: float,
        success: bool,
        model: str = ""
    ):
        """Record AI provider performance"""
        
        metric = {
            "timestamp": datetime.now(),
            "provider": provider,
            "query_type": query_type,
            "response_time": response_time,
            "success": success,
            "model": model
        }
        
        provider_key = f"ai_provider_{provider}"
        self.api_metrics[provider_key].append(metric)
        
        if len(self.api_metrics[provider_key]) > 500:
            self.api_metrics[provider_key] = self.api_metrics[provider_key][-500:]
    
    async def _monitoring_worker(self):
        """Background worker for system monitoring"""
        while self.monitoring_enabled:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(10)  # Collect every 10 seconds
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network_io = psutil.net_io_counters()
        
        # Active connections (simplified)
        active_connections = len(psutil.net_connections(kind='inet'))
        
        # Calculate recent response times
        recent_metrics = [
            m for m in self.metrics_buffer
            if datetime.now() - m["timestamp"] < timedelta(minutes=1)
        ]
        
        recent_response_times = [m["response_time"] for m in recent_metrics]
        
        metric = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage=disk.percent,
            network_io={
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv
            },
            active_connections=active_connections,
            response_times=recent_response_times
        )
        
        self.system_metrics.append(metric)
        
        # Update Prometheus metrics
        self.system_cpu_usage.set(cpu_percent)
        self.system_memory_usage.set(memory.percent)
        self.active_connections.set(active_connections)
        
        # Check system thresholds
        self._check_system_thresholds(metric)
    
    def _check_performance_thresholds(self, metric: Dict[str, Any]):
        """Check if performance metric exceeds thresholds"""
        
        response_time = metric["response_time"]
        threshold = self.thresholds[PerformanceMetric.RESPONSE_TIME]
        
        if response_time > threshold.critical_level:
            logger.error(
                f"CRITICAL: Response time {response_time:.2f}s exceeds critical threshold "
                f"{threshold.critical_level}s for {metric['endpoint']}"
            )
        elif response_time > threshold.warning_level:
            logger.warning(
                f"WARNING: Response time {response_time:.2f}s exceeds warning threshold "
                f"{threshold.warning_level}s for {metric['endpoint']}"
            )
    
    def _check_system_thresholds(self, metric: SystemMetrics):
        """Check if system metrics exceed thresholds"""
        
        # CPU usage
        cpu_threshold = self.thresholds[PerformanceMetric.CPU_USAGE]
        if metric.cpu_percent > cpu_threshold.critical_level:
            logger.error(f"CRITICAL: CPU usage {metric.cpu_percent:.1f}% exceeds critical threshold")
        elif metric.cpu_percent > cpu_threshold.warning_level:
            logger.warning(f"WARNING: CPU usage {metric.cpu_percent:.1f}% exceeds warning threshold")
        
        # Memory usage
        memory_threshold = self.thresholds[PerformanceMetric.MEMORY_USAGE]
        if metric.memory_percent > memory_threshold.critical_level:
            logger.error(f"CRITICAL: Memory usage {metric.memory_percent:.1f}% exceeds critical threshold")
        elif metric.memory_percent > memory_threshold.warning_level:
            logger.warning(f"WARNING: Memory usage {metric.memory_percent:.1f}% exceeds warning threshold")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        
        if not self.metrics_buffer:
            return {"status": "No metrics available"}
        
        # Calculate summary statistics
        recent_metrics = [
            m for m in self.metrics_buffer
            if datetime.now() - m["timestamp"] < timedelta(minutes=5)
        ]
        
        if not recent_metrics:
            return {"status": "No recent metrics"}
        
        response_times = [m["response_time"] for m in recent_metrics]
        avg_response_time = statistics.mean(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 10 else max(response_times)
        
        error_count = sum(1 for m in recent_metrics if m["status_code"] >= 400)
        error_rate = (error_count / len(recent_metrics)) * 100
        
        # System metrics
        latest_system = self.system_metrics[-1] if self.system_metrics else None
        
        return {
            "timestamp": datetime.now().isoformat(),
            "api_performance": {
                "total_requests": len(recent_metrics),
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "error_rate": error_rate,
                "throughput": len(recent_metrics) / 5  # requests per second over 5 minutes
            },
            "system_performance": {
                "cpu_percent": latest_system.cpu_percent if latest_system else 0,
                "memory_percent": latest_system.memory_percent if latest_system else 0,
                "disk_usage": latest_system.disk_usage if latest_system else 0,
                "active_connections": latest_system.active_connections if latest_system else 0
            },
            "ai_providers": self._get_ai_provider_summary()
        }
    
    def _get_ai_provider_summary(self) -> Dict[str, Any]:
        """Get AI provider performance summary"""
        
        ai_summary = {}
        
        for key, metrics in self.api_metrics.items():
            if key.startswith("ai_provider_"):
                provider = key.replace("ai_provider_", "")
                
                recent_metrics = [
                    m for m in metrics
                    if datetime.now() - m["timestamp"] < timedelta(minutes=10)
                ]
                
                if recent_metrics:
                    response_times = [m["response_time"] for m in recent_metrics]
                    success_rate = sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics)
                    
                    ai_summary[provider] = {
                        "total_requests": len(recent_metrics),
                        "avg_response_time": statistics.mean(response_times),
                        "success_rate": success_rate,
                        "last_used": max(m["timestamp"] for m in recent_metrics).isoformat()
                    }
        
        return ai_summary
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate detailed performance report"""
        
        summary = self.get_performance_summary()
        
        # Add trending information
        if len(self.system_metrics) >= 2:
            current = self.system_metrics[-1]
            previous = self.system_metrics[-2]
            
            cpu_trend = current.cpu_percent - previous.cpu_percent
            memory_trend = current.memory_percent - previous.memory_percent
            
            summary["trends"] = {
                "cpu_trend": cpu_trend,
                "memory_trend": memory_trend,
                "trend_direction": "improving" if cpu_trend < 0 and memory_trend < 0 else "degrading"
            }
        
        # Add recommendations
        summary["recommendations"] = self._generate_performance_recommendations()
        
        return summary
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        if not self.system_metrics:
            return recommendations
        
        latest_system = self.system_metrics[-1]
        
        # CPU recommendations
        if latest_system.cpu_percent > 80:
            recommendations.append(
                "High CPU usage detected. Consider implementing request rate limiting or scaling horizontally."
            )
        
        # Memory recommendations
        if latest_system.memory_percent > 85:
            recommendations.append(
                "High memory usage detected. Consider optimizing cache sizes or implementing memory cleanup."
            )
        
        # Response time recommendations
        if latest_system.response_times:
            avg_response_time = statistics.mean(latest_system.response_times)
            if avg_response_time > 2.0:
                recommendations.append(
                    "Slow response times detected. Consider optimizing database queries or implementing caching."
                )
        
        # Connection recommendations
        if latest_system.active_connections > 100:
            recommendations.append(
                "High number of active connections. Consider implementing connection pooling."
            )
        
        return recommendations


class AutoOptimizationEngine:
    """
    Automated performance optimization based on real-time metrics
    """
    
    def __init__(self, cache_manager: IntelligentCacheManager, monitor: PerformanceMonitoringSystem):
        self.cache_manager = cache_manager
        self.monitor = monitor
        self.optimization_history = []
        self.optimization_enabled = True
        
        # Optimization rules
        self.optimization_rules = [
            self._optimize_cache_strategy,
            self._optimize_resource_allocation,
            self._optimize_query_performance,
            self._optimize_background_tasks
        ]
        
        # Start optimization worker
        asyncio.create_task(self._optimization_worker())
    
    async def _optimization_worker(self):
        """Background worker for automated optimizations"""
        while self.optimization_enabled:
            try:
                await self._run_optimization_cycle()
                await asyncio.sleep(300)  # Run every 5 minutes
            except Exception as e:
                logger.error(f"Auto-optimization error: {e}")
                await asyncio.sleep(60)
    
    async def _run_optimization_cycle(self):
        """Run a complete optimization cycle"""
        
        # Get current performance metrics
        performance_report = await self.monitor.get_performance_report()
        
        optimizations_applied = []
        
        # Run optimization rules
        for rule in self.optimization_rules:
            try:
                optimization = await rule(performance_report)
                if optimization:
                    optimizations_applied.append(optimization)
            except Exception as e:
                logger.error(f"Optimization rule error: {e}")
        
        # Record optimization history
        if optimizations_applied:
            self.optimization_history.append({
                "timestamp": datetime.now(),
                "optimizations": optimizations_applied,
                "performance_before": performance_report
            })
            
            # Keep only recent history
            if len(self.optimization_history) > 100:
                self.optimization_history = self.optimization_history[-100:]
            
            logger.info(f"Applied {len(optimizations_applied)} automatic optimizations")
    
    async def _optimize_cache_strategy(self, performance_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize caching strategy based on performance"""
        
        cache_stats = await self.cache_manager.get_cache_stats()
        overall_hit_rate = cache_stats["hit_rates"]["overall"]
        
        # If hit rate is low, adjust cache sizes
        if overall_hit_rate < 0.6:
            # Increase L1 cache size if memory allows
            system_memory = performance_report.get("system_performance", {}).get("memory_percent", 0)
            
            if system_memory < 70:  # Plenty of memory available
                old_size = self.cache_manager.l1_max_size
                self.cache_manager.l1_max_size = min(old_size * 1.2, 2000)
                
                return {
                    "type": "cache_optimization",
                    "action": "increase_l1_cache_size",
                    "old_value": old_size,
                    "new_value": self.cache_manager.l1_max_size,
                    "reason": f"Low hit rate: {overall_hit_rate:.2f}"
                }
        
        return None
    
    async def _optimize_resource_allocation(self, performance_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize resource allocation based on usage patterns"""
        
        system_perf = performance_report.get("system_performance", {})
        cpu_percent = system_perf.get("cpu_percent", 0)
        memory_percent = system_perf.get("memory_percent", 0)
        
        # If CPU is high but memory is low, suggest memory-for-CPU trade-offs
        if cpu_percent > 80 and memory_percent < 60:
            return {
                "type": "resource_optimization",
                "action": "increase_memory_usage_for_cpu_savings",
                "recommendation": "Increase cache sizes to reduce CPU-intensive operations",
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent
            }
        
        return None
    
    async def _optimize_query_performance(self, performance_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize database query performance"""
        
        api_perf = performance_report.get("api_performance", {})
        avg_response_time = api_perf.get("avg_response_time", 0)
        
        # If response times are slow, suggest optimizations
        if avg_response_time > 1.0:
            return {
                "type": "query_optimization",
                "action": "suggest_query_improvements",
                "recommendation": "Consider adding database indexes or implementing query caching",
                "avg_response_time": avg_response_time
            }
        
        return None
    
    async def _optimize_background_tasks(self, performance_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Optimize background task execution"""
        
        system_perf = performance_report.get("system_performance", {})
        cpu_percent = system_perf.get("cpu_percent", 0)
        
        # If CPU is consistently high, reduce background task frequency
        if cpu_percent > 85:
            return {
                "type": "background_task_optimization",
                "action": "reduce_background_task_frequency",
                "recommendation": "Temporarily reduce frequency of non-critical background tasks",
                "cpu_usage": cpu_percent
            }
        
        return None
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get optimization report"""
        
        if not self.optimization_history:
            return {"status": "No optimizations performed yet"}
        
        recent_optimizations = [
            opt for opt in self.optimization_history
            if datetime.now() - opt["timestamp"] < timedelta(hours=24)
        ]
        
        optimization_types = defaultdict(int)
        for opt in recent_optimizations:
            for optimization in opt["optimizations"]:
                optimization_types[optimization["type"]] += 1
        
        return {
            "total_optimizations": len(self.optimization_history),
            "recent_optimizations": len(recent_optimizations),
            "optimization_types": dict(optimization_types),
            "last_optimization": self.optimization_history[-1]["timestamp"].isoformat(),
            "optimization_enabled": self.optimization_enabled
        }


# Global instances
intelligent_cache_manager = None
performance_monitoring_system = None
auto_optimization_engine = None

def initialize_performance_systems(redis_client: Optional[redis.Redis] = None):
    """Initialize global performance systems"""
    global intelligent_cache_manager, performance_monitoring_system, auto_optimization_engine
    
    intelligent_cache_manager = IntelligentCacheManager(redis_client)
    performance_monitoring_system = PerformanceMonitoringSystem()
    auto_optimization_engine = AutoOptimizationEngine(
        intelligent_cache_manager,
        performance_monitoring_system
    )
    
    logger.info("Performance optimization systems initialized")

def get_cache_manager() -> IntelligentCacheManager:
    """Get global cache manager instance"""
    if intelligent_cache_manager is None:
        raise RuntimeError("Performance systems not initialized")
    return intelligent_cache_manager

def get_performance_monitor() -> PerformanceMonitoringSystem:
    """Get global performance monitor instance"""
    if performance_monitoring_system is None:
        raise RuntimeError("Performance systems not initialized")
    return performance_monitoring_system

def get_optimization_engine() -> AutoOptimizationEngine:
    """Get global optimization engine instance"""
    if auto_optimization_engine is None:
        raise RuntimeError("Performance systems not initialized")
    return auto_optimization_engine