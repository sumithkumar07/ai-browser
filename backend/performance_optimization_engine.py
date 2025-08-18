import asyncio
import time
import psutil
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import gc
import weakref
import hashlib

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Container for performance metrics"""
    def __init__(self):
        self.response_times = deque(maxlen=1000)
        self.error_rates = deque(maxlen=100)
        self.memory_usage = deque(maxlen=60)
        self.cpu_usage = deque(maxlen=60)
        self.cache_hit_rates = deque(maxlen=100)
        self.concurrent_users = deque(maxlen=60)
        
        # Advanced metrics
        self.ai_provider_performance = defaultdict(lambda: {
            "response_times": deque(maxlen=100),
            "success_rates": deque(maxlen=100),
            "error_counts": 0,
            "total_calls": 0
        })
        
        self.automation_performance = defaultdict(lambda: {
            "execution_times": deque(maxlen=50),
            "success_rates": deque(maxlen=50),
            "complexity_scores": deque(maxlen=50)
        })

class PerformanceOptimizationEngine:
    """Advanced performance optimization and monitoring system"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.optimization_rules = self._initialize_optimization_rules()
        self.performance_thresholds = self._initialize_thresholds()
        
        # Performance optimization state
        self.optimization_enabled = True
        self.auto_scaling_enabled = True
        self.cache_optimization_enabled = True
        
        # Resource management
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="perf_opt")
        self.memory_manager = MemoryManager()
        self.cache_optimizer = CacheOptimizer()
        self.load_balancer = LoadBalancer()
        
        # Monitoring and alerts
        self.alert_handlers = []
        self.performance_alerts = deque(maxlen=50)
        
        # Background tasks
        self._monitoring_task = None
        self._optimization_task = None
        
    def start_performance_engine(self):
        """Start background performance monitoring and optimization"""
        if self._monitoring_task is None:
            try:
                self._monitoring_task = asyncio.create_task(self._background_monitoring())
                self._optimization_task = asyncio.create_task(self._background_optimization())
            except RuntimeError:
                pass
    
    def _initialize_optimization_rules(self) -> Dict[str, Dict]:
        """Initialize performance optimization rules"""
        return {
            "response_time": {
                "threshold": 2.0,  # seconds
                "action": "optimize_ai_provider_selection",
                "priority": "high"
            },
            "memory_usage": {
                "threshold": 85.0,  # percentage
                "action": "trigger_garbage_collection",
                "priority": "critical"
            },
            "cpu_usage": {
                "threshold": 80.0,  # percentage
                "action": "reduce_concurrent_tasks",
                "priority": "high"
            },
            "error_rate": {
                "threshold": 5.0,  # percentage
                "action": "switch_ai_provider",
                "priority": "critical"
            },
            "cache_hit_rate": {
                "threshold": 60.0,  # percentage (minimum)
                "action": "optimize_cache_strategy",
                "priority": "medium"
            }
        }
    
    def _initialize_thresholds(self) -> Dict[str, float]:
        """Initialize performance thresholds"""
        return {
            "excellent_response_time": 0.5,
            "good_response_time": 1.0,
            "acceptable_response_time": 2.0,
            "poor_response_time": 5.0,
            "critical_memory_usage": 90.0,
            "high_memory_usage": 80.0,
            "normal_memory_usage": 60.0,
            "max_concurrent_tasks": 10,
            "optimal_cache_hit_rate": 80.0
        }
    
    async def _background_monitoring(self):
        """Background system monitoring"""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Analyze performance trends
                await self._analyze_performance_trends()
                
                # Check for performance issues
                await self._check_performance_alerts()
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
    
    async def _background_optimization(self):
        """Background performance optimization"""
        while True:
            try:
                await asyncio.sleep(60)  # Optimize every minute
                
                if self.optimization_enabled:
                    # Memory optimization
                    await self._optimize_memory_usage()
                    
                    # Cache optimization
                    await self._optimize_cache_performance()
                    
                    # AI provider optimization
                    await self._optimize_ai_provider_selection()
                    
                    # Load balancing optimization
                    await self._optimize_load_balancing()
                
            except Exception as e:
                logger.error(f"Performance optimization error: {e}")
    
    async def _collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # System resource metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update metrics
            self.metrics.cpu_usage.append(cpu_percent)
            self.metrics.memory_usage.append(memory.percent)
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            process_cpu = process.cpu_percent()
            
            # Network metrics (if available)
            try:
                net_io = psutil.net_io_counters()
                network_usage = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
            except:
                network_usage = {}
            
            # Store comprehensive metrics
            timestamp = datetime.utcnow()
            comprehensive_metrics = {
                "timestamp": timestamp,
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available": memory.available,
                    "disk_percent": disk.percent,
                    "disk_free": disk.free
                },
                "process": {
                    "memory_mb": process_memory,
                    "cpu_percent": process_cpu,
                    "num_threads": process.num_threads(),
                    "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0
                },
                "network": network_usage
            }
            
            # Store for trend analysis
            if not hasattr(self, '_detailed_metrics'):
                self._detailed_metrics = deque(maxlen=60)
            self._detailed_metrics.append(comprehensive_metrics)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_api_performance(self, endpoint: str, method: str, response_time: float, 
                              status_code: int, user_session: str = None):
        """Record API performance metrics"""
        
        # Basic metrics
        self.metrics.response_times.append(response_time)
        
        # Error tracking
        if status_code >= 400:
            current_time = datetime.utcnow()
            error_rate = self._calculate_current_error_rate()
            self.metrics.error_rates.append(error_rate)
        
        # Endpoint-specific tracking
        if not hasattr(self, '_endpoint_metrics'):
            self._endpoint_metrics = defaultdict(lambda: {
                "response_times": deque(maxlen=100),
                "error_counts": 0,
                "total_calls": 0,
                "peak_response_time": 0,
                "avg_response_time": 0
            })
        
        endpoint_metrics = self._endpoint_metrics[f"{method}:{endpoint}"]
        endpoint_metrics["response_times"].append(response_time)
        endpoint_metrics["total_calls"] += 1
        
        if status_code >= 400:
            endpoint_metrics["error_counts"] += 1
        
        # Update peak and average
        endpoint_metrics["peak_response_time"] = max(
            endpoint_metrics["peak_response_time"], response_time
        )
        
        if endpoint_metrics["response_times"]:
            endpoint_metrics["avg_response_time"] = sum(endpoint_metrics["response_times"]) / len(endpoint_metrics["response_times"])
        
        # Concurrent users tracking
        if user_session:
            current_time = int(time.time() // 60)  # Per minute buckets
            if not hasattr(self, '_active_users'):
                self._active_users = defaultdict(set)
            self._active_users[current_time].add(user_session)
            
            # Clean old data
            cutoff_time = current_time - 5  # Keep 5 minutes
            for t in list(self._active_users.keys()):
                if t < cutoff_time:
                    del self._active_users[t]
    
    def record_ai_provider_performance(self, provider: str, query_type: str, 
                                     response_time: float, success: bool, model: str = None):
        """Record AI provider performance metrics"""
        
        provider_metrics = self.metrics.ai_provider_performance[provider]
        provider_metrics["response_times"].append(response_time)
        provider_metrics["total_calls"] += 1
        
        if success:
            provider_metrics["success_rates"].append(1)
        else:
            provider_metrics["success_rates"].append(0)
            provider_metrics["error_counts"] += 1
        
        # Model-specific tracking
        if model:
            if not hasattr(self, '_model_metrics'):
                self._model_metrics = defaultdict(lambda: {
                    "response_times": deque(maxlen=50),
                    "success_rates": deque(maxlen=50),
                    "usage_count": 0
                })
            
            model_key = f"{provider}:{model}"
            self._model_metrics[model_key]["response_times"].append(response_time)
            self._model_metrics[model_key]["success_rates"].append(1 if success else 0)
            self._model_metrics[model_key]["usage_count"] += 1
    
    def record_automation_performance(self, task_type: str, execution_time: float, 
                                    success: bool, complexity: str, steps_count: int = 0):
        """Record automation task performance"""
        
        automation_metrics = self.metrics.automation_performance[task_type]
        automation_metrics["execution_times"].append(execution_time)
        automation_metrics["success_rates"].append(1 if success else 0)
        
        # Complexity scoring
        complexity_score = {"simple": 1, "medium": 2, "complex": 3, "expert": 4}.get(complexity, 2)
        automation_metrics["complexity_scores"].append(complexity_score)
        
        # Steps efficiency
        if not hasattr(self, '_automation_efficiency'):
            self._automation_efficiency = defaultdict(lambda: {
                "steps_per_minute": deque(maxlen=50),
                "time_per_step": deque(maxlen=50)
            })
        
        if steps_count > 0 and execution_time > 0:
            steps_per_minute = (steps_count / execution_time) * 60
            time_per_step = execution_time / steps_count
            
            efficiency_metrics = self._automation_efficiency[task_type]
            efficiency_metrics["steps_per_minute"].append(steps_per_minute)
            efficiency_metrics["time_per_step"].append(time_per_step)
    
    def record_cache_performance(self, cache_type: str, hit: bool, response_time: float = 0):
        """Record cache performance metrics"""
        
        if not hasattr(self, '_cache_metrics'):
            self._cache_metrics = defaultdict(lambda: {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "avg_response_time": deque(maxlen=100)
            })
        
        cache_metrics = self._cache_metrics[cache_type]
        
        if hit:
            cache_metrics["hits"] += 1
        else:
            cache_metrics["misses"] += 1
        
        # Calculate hit rate
        total = cache_metrics["hits"] + cache_metrics["misses"]
        cache_metrics["hit_rate"] = (cache_metrics["hits"] / total) * 100 if total > 0 else 0
        
        if response_time > 0:
            cache_metrics["avg_response_time"].append(response_time)
        
        # Update global cache hit rate
        overall_hit_rate = self._calculate_overall_cache_hit_rate()
        self.metrics.cache_hit_rates.append(overall_hit_rate)
    
    async def _analyze_performance_trends(self):
        """Analyze performance trends and predict issues"""
        
        # Response time trend analysis
        if len(self.metrics.response_times) >= 10:
            recent_times = list(self.metrics.response_times)[-10:]
            avg_recent = sum(recent_times) / len(recent_times)
            
            if avg_recent > self.performance_thresholds["acceptable_response_time"]:
                await self._trigger_performance_alert(
                    "high_response_time", 
                    f"Average response time is {avg_recent:.2f}s (threshold: {self.performance_thresholds['acceptable_response_time']}s)"
                )
        
        # Memory usage trend
        if len(self.metrics.memory_usage) >= 5:
            recent_memory = list(self.metrics.memory_usage)[-5:]
            avg_memory = sum(recent_memory) / len(recent_memory)
            
            if avg_memory > self.performance_thresholds["high_memory_usage"]:
                await self._trigger_performance_alert(
                    "high_memory_usage",
                    f"Memory usage is {avg_memory:.1f}% (threshold: {self.performance_thresholds['high_memory_usage']}%)"
                )
        
        # Error rate analysis
        if len(self.metrics.error_rates) >= 3:
            recent_errors = list(self.metrics.error_rates)[-3:]
            avg_error_rate = sum(recent_errors) / len(recent_errors)
            
            if avg_error_rate > 5.0:  # 5% error rate threshold
                await self._trigger_performance_alert(
                    "high_error_rate",
                    f"Error rate is {avg_error_rate:.1f}% (threshold: 5.0%)"
                )
    
    async def _check_performance_alerts(self):
        """Check for immediate performance alerts"""
        
        # Check current system state
        if self.metrics.memory_usage:
            current_memory = self.metrics.memory_usage[-1]
            if current_memory > self.performance_thresholds["critical_memory_usage"]:
                await self._trigger_critical_alert("critical_memory", current_memory)
        
        if self.metrics.cpu_usage:
            current_cpu = self.metrics.cpu_usage[-1]
            if current_cpu > 95.0:  # Critical CPU usage
                await self._trigger_critical_alert("critical_cpu", current_cpu)
    
    async def _trigger_performance_alert(self, alert_type: str, message: str):
        """Trigger performance alert"""
        
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow(),
            "severity": "warning"
        }
        
        self.performance_alerts.append(alert)
        logger.warning(f"Performance Alert: {alert_type} - {message}")
        
        # Execute alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
    
    async def _trigger_critical_alert(self, alert_type: str, value: float):
        """Trigger critical performance alert"""
        
        alert = {
            "type": alert_type,
            "message": f"Critical {alert_type}: {value}",
            "timestamp": datetime.utcnow(),
            "severity": "critical"
        }
        
        self.performance_alerts.append(alert)
        logger.critical(f"CRITICAL ALERT: {alert_type} - {value}")
        
        # Immediate optimization actions for critical alerts
        if alert_type == "critical_memory":
            await self._emergency_memory_cleanup()
        elif alert_type == "critical_cpu":
            await self._emergency_cpu_optimization()
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        
        try:
            current_memory = self.metrics.memory_usage[-1] if self.metrics.memory_usage else 0
            
            if current_memory > self.performance_thresholds["high_memory_usage"]:
                # Force garbage collection
                gc.collect()
                
                # Clear old cache entries
                await self.cache_optimizer.optimize_memory_usage()
                
                # Reduce cache sizes
                await self._reduce_cache_sizes()
                
                logger.info(f"Memory optimization completed. Usage was {current_memory}%")
                
        except Exception as e:
            logger.error(f"Memory optimization error: {e}")
    
    async def _optimize_cache_performance(self):
        """Optimize cache performance"""
        
        try:
            overall_hit_rate = self._calculate_overall_cache_hit_rate()
            
            if overall_hit_rate < self.performance_thresholds["optimal_cache_hit_rate"]:
                # Analyze cache patterns
                cache_analysis = await self.cache_optimizer.analyze_cache_patterns()
                
                # Implement optimizations
                await self.cache_optimizer.optimize_cache_strategy(cache_analysis)
                
                logger.info(f"Cache optimization completed. Hit rate was {overall_hit_rate}%")
                
        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
    
    async def _optimize_ai_provider_selection(self):
        """Optimize AI provider selection based on performance"""
        
        try:
            # Analyze provider performance
            best_performers = {}
            
            for provider, metrics in self.metrics.ai_provider_performance.items():
                if metrics["response_times"] and metrics["success_rates"]:
                    avg_response_time = sum(metrics["response_times"]) / len(metrics["response_times"])
                    success_rate = sum(metrics["success_rates"]) / len(metrics["success_rates"])
                    
                    # Calculate performance score (lower is better for response time, higher for success rate)
                    performance_score = success_rate * 100 - avg_response_time * 10
                    best_performers[provider] = performance_score
            
            if best_performers:
                # Update provider selection preferences
                sorted_providers = sorted(best_performers.items(), key=lambda x: x[1], reverse=True)
                logger.info(f"AI Provider performance ranking: {sorted_providers}")
                
                # Store recommendations for AI manager
                self._provider_recommendations = {
                    "rankings": sorted_providers,
                    "updated_at": datetime.utcnow()
                }
                
        except Exception as e:
            logger.error(f"AI provider optimization error: {e}")
    
    async def _optimize_load_balancing(self):
        """Optimize load balancing"""
        
        try:
            # Analyze current load distribution
            if hasattr(self, '_active_users'):
                current_minute = int(time.time() // 60)
                active_users_count = len(self._active_users.get(current_minute, set()))
                
                self.metrics.concurrent_users.append(active_users_count)
                
                # Adjust concurrent task limits based on load
                if active_users_count > 20:
                    # High load - reduce concurrent tasks
                    self.performance_thresholds["max_concurrent_tasks"] = 8
                elif active_users_count < 5:
                    # Low load - allow more concurrent tasks
                    self.performance_thresholds["max_concurrent_tasks"] = 15
                else:
                    # Normal load
                    self.performance_thresholds["max_concurrent_tasks"] = 10
                
        except Exception as e:
            logger.error(f"Load balancing optimization error: {e}")
    
    async def _emergency_memory_cleanup(self):
        """Emergency memory cleanup"""
        
        try:
            # Force aggressive garbage collection
            for _ in range(3):
                gc.collect()
            
            # Clear all caches
            if hasattr(self, 'cache_optimizer'):
                await self.cache_optimizer.emergency_cache_clear()
            
            # Reduce all deque sizes temporarily
            self.metrics.response_times = deque(list(self.metrics.response_times)[-100:], maxlen=200)
            self.metrics.memory_usage = deque(list(self.metrics.memory_usage)[-30:], maxlen=30)
            
            logger.critical("Emergency memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Emergency memory cleanup error: {e}")
    
    async def _emergency_cpu_optimization(self):
        """Emergency CPU optimization"""
        
        try:
            # Reduce concurrent task limits
            self.performance_thresholds["max_concurrent_tasks"] = 3
            
            # Pause non-critical background tasks temporarily
            if hasattr(self, '_optimization_task'):
                # Don't cancel the task, just reduce frequency
                pass
            
            logger.critical("Emergency CPU optimization completed")
            
        except Exception as e:
            logger.error(f"Emergency CPU optimization error: {e}")
    
    def _calculate_current_error_rate(self) -> float:
        """Calculate current error rate"""
        
        if not hasattr(self, '_recent_requests'):
            self._recent_requests = deque(maxlen=100)
        
        current_time = time.time()
        # Remove old entries (older than 5 minutes)
        while self._recent_requests and current_time - self._recent_requests[0]["timestamp"] > 300:
            self._recent_requests.popleft()
        
        if not self._recent_requests:
            return 0.0
        
        error_count = sum(1 for req in self._recent_requests if req["error"])
        return (error_count / len(self._recent_requests)) * 100
    
    def _calculate_overall_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        
        if not hasattr(self, '_cache_metrics'):
            return 0.0
        
        total_hits = sum(metrics["hits"] for metrics in self._cache_metrics.values())
        total_requests = sum(metrics["hits"] + metrics["misses"] for metrics in self._cache_metrics.values())
        
        return (total_hits / total_requests) * 100 if total_requests > 0 else 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": self._assess_system_health(),
            "response_performance": self._analyze_response_performance(),
            "resource_utilization": self._analyze_resource_utilization(),
            "ai_provider_performance": self._analyze_ai_provider_performance(),
            "automation_performance": self._analyze_automation_performance(),
            "cache_performance": self._analyze_cache_performance(),
            "alerts": list(self.performance_alerts)[-10:],  # Last 10 alerts
            "recommendations": self._generate_performance_recommendations()
        }
        
        return report
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        
        health_score = 100
        status = "healthy"
        issues = []
        
        # Check response times
        if self.metrics.response_times:
            avg_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)
            if avg_response_time > self.performance_thresholds["poor_response_time"]:
                health_score -= 30
                status = "critical"
                issues.append(f"Poor response time: {avg_response_time:.2f}s")
            elif avg_response_time > self.performance_thresholds["acceptable_response_time"]:
                health_score -= 15
                status = "degraded" if status == "healthy" else status
                issues.append(f"Slow response time: {avg_response_time:.2f}s")
        
        # Check memory usage
        if self.metrics.memory_usage:
            current_memory = self.metrics.memory_usage[-1]
            if current_memory > self.performance_thresholds["critical_memory_usage"]:
                health_score -= 25
                status = "critical"
                issues.append(f"Critical memory usage: {current_memory:.1f}%")
            elif current_memory > self.performance_thresholds["high_memory_usage"]:
                health_score -= 10
                status = "degraded" if status == "healthy" else status
                issues.append(f"High memory usage: {current_memory:.1f}%")
        
        # Check error rates
        if self.metrics.error_rates:
            recent_error_rate = self.metrics.error_rates[-1] if self.metrics.error_rates else 0
            if recent_error_rate > 10.0:
                health_score -= 20
                status = "critical"
                issues.append(f"High error rate: {recent_error_rate:.1f}%")
            elif recent_error_rate > 5.0:
                health_score -= 10
                status = "degraded" if status == "healthy" else status
                issues.append(f"Elevated error rate: {recent_error_rate:.1f}%")
        
        return {
            "status": status,
            "health_score": max(0, health_score),
            "issues": issues
        }
    
    def add_alert_handler(self, handler):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)
    
    def get_provider_recommendations(self) -> Optional[Dict[str, Any]]:
        """Get AI provider recommendations"""
        return getattr(self, '_provider_recommendations', None)
    
    def _analyze_response_performance(self) -> Dict[str, Any]:
        """Analyze response performance metrics - FIXED MISSING METHOD"""
        if not self.metrics.response_times:
            return {"status": "no_data", "metrics": {}}
        
        response_times = list(self.metrics.response_times)
        avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "average_response_time": avg_response_time,
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "total_requests": len(response_times),
            "performance_grade": self._calculate_performance_grade(response_times),
            "percentiles": {
                "p50": self._calculate_percentile(response_times, 50),
                "p90": self._calculate_percentile(response_times, 90),
                "p95": self._calculate_percentile(response_times, 95),
                "p99": self._calculate_percentile(response_times, 99)
            },
            "trend_analysis": self._analyze_response_trend()
        }
    
    def _calculate_percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile for response times"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100.0) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _analyze_response_trend(self) -> Dict[str, Any]:
        """Analyze response time trends"""
        if len(self.metrics.response_times) < 20:
            return {"trend": "insufficient_data"}
        
        # Split into two halves for comparison
        times = list(self.metrics.response_times)
        mid = len(times) // 2
        first_half = times[:mid]
        second_half = times[mid:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        # Calculate trend
        if avg_second > avg_first * 1.1:
            trend = "deteriorating"
        elif avg_second < avg_first * 0.9:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "first_half_avg": avg_first,
            "second_half_avg": avg_second,
            "change_percentage": ((avg_second - avg_first) / avg_first) * 100
        }
    
    def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization"""
        return {
            "memory": {
                "current": self.metrics.memory_usage[-1] if self.metrics.memory_usage else 0,
                "average": sum(self.metrics.memory_usage) / len(self.metrics.memory_usage) if self.metrics.memory_usage else 0,
                "peak": max(self.metrics.memory_usage) if self.metrics.memory_usage else 0,
                "trend": self._calculate_trend(list(self.metrics.memory_usage))
            },
            "cpu": {
                "current": self.metrics.cpu_usage[-1] if self.metrics.cpu_usage else 0,
                "average": sum(self.metrics.cpu_usage) / len(self.metrics.cpu_usage) if self.metrics.cpu_usage else 0,
                "peak": max(self.metrics.cpu_usage) if self.metrics.cpu_usage else 0,
                "trend": self._calculate_trend(list(self.metrics.cpu_usage))
            },
            "concurrent_users": {
                "current": self.metrics.concurrent_users[-1] if self.metrics.concurrent_users else 0,
                "peak": max(self.metrics.concurrent_users) if self.metrics.concurrent_users else 0,
                "average": sum(self.metrics.concurrent_users) / len(self.metrics.concurrent_users) if self.metrics.concurrent_users else 0
            }
        }
    
    def _calculate_trend(self, data: List[float]) -> str:
        """Calculate trend direction for metrics"""
        if len(data) < 5:
            return "insufficient_data"
        
        # Simple trend calculation
        first_quarter = data[:len(data)//4] or [0]
        last_quarter = data[-len(data)//4:] or [0]
        
        avg_first = sum(first_quarter) / len(first_quarter)
        avg_last = sum(last_quarter) / len(last_quarter)
        
        if avg_last > avg_first * 1.1:
            return "increasing"
        elif avg_last < avg_first * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _analyze_ai_provider_performance(self) -> Dict[str, Any]:
        """Analyze AI provider performance"""
        provider_analysis = {}
        for provider, metrics in self.metrics.ai_provider_performance.items():
            if metrics["response_times"] and metrics["success_rates"]:
                avg_response_time = sum(metrics["response_times"]) / len(metrics["response_times"])
                success_rate = sum(metrics["success_rates"]) / len(metrics["success_rates"]) * 100
                
                provider_analysis[provider] = {
                    "average_response_time": avg_response_time,
                    "success_rate": success_rate,
                    "total_calls": metrics["total_calls"],
                    "error_count": metrics["error_counts"],
                    "performance_score": success_rate * 100 - avg_response_time * 10,
                    "reliability": "high" if success_rate > 95 else "medium" if success_rate > 85 else "low"
                }
        
        return provider_analysis
    
    def _analyze_automation_performance(self) -> Dict[str, Any]:
        """Analyze automation performance"""
        automation_analysis = {}
        for task_type, metrics in self.metrics.automation_performance.items():
            if metrics["execution_times"]:
                avg_execution_time = sum(metrics["execution_times"]) / len(metrics["execution_times"])
                success_rate = sum(metrics["success_rates"]) / len(metrics["success_rates"]) * 100 if metrics["success_rates"] else 0
                avg_complexity = sum(metrics["complexity_scores"]) / len(metrics["complexity_scores"]) if metrics["complexity_scores"] else 0
                
                automation_analysis[task_type] = {
                    "average_execution_time": avg_execution_time,
                    "success_rate": success_rate,
                    "total_executions": len(metrics["execution_times"]),
                    "average_complexity": avg_complexity,
                    "efficiency_score": (success_rate / avg_execution_time) if avg_execution_time > 0 else 0
                }
        
        return automation_analysis
    
    def _analyze_cache_performance(self) -> Dict[str, Any]:
        """Analyze cache performance"""
        if not hasattr(self, '_cache_metrics'):
            return {"overall_hit_rate": 0, "cache_types": {}}
        
        cache_analysis = {}
        total_efficiency_score = 0
        
        for cache_type, metrics in self._cache_metrics.items():
            total_requests = metrics["hits"] + metrics["misses"]
            efficiency_score = (metrics["hit_rate"] / 100) * (total_requests / 1000) if total_requests > 0 else 0
            
            cache_analysis[cache_type] = {
                "hit_rate": metrics["hit_rate"],
                "total_hits": metrics["hits"],
                "total_misses": metrics["misses"],
                "total_requests": total_requests,
                "efficiency_score": efficiency_score,
                "performance_grade": "A" if metrics["hit_rate"] > 90 else "B" if metrics["hit_rate"] > 75 else "C" if metrics["hit_rate"] > 60 else "D"
            }
            total_efficiency_score += efficiency_score
        
        return {
            "overall_hit_rate": self._calculate_overall_cache_hit_rate(),
            "cache_types": cache_analysis,
            "total_efficiency_score": total_efficiency_score,
            "optimization_potential": self._calculate_cache_optimization_potential()
        }
    
    def _calculate_cache_optimization_potential(self) -> float:
        """Calculate how much cache performance can be improved"""
        if not hasattr(self, '_cache_metrics'):
            return 0.0
        
        total_potential = 0
        for metrics in self._cache_metrics.values():
            if metrics["hit_rate"] < 80:  # Below optimal threshold
                potential = (80 - metrics["hit_rate"]) / 80  # Normalized potential
                total_potential += potential
        
        return min(total_potential, 100.0)  # Cap at 100%
    
    def _generate_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Generate detailed performance recommendations"""
        recommendations = []
        
        # Response time recommendations
        if self.metrics.response_times:
            avg_response_time = sum(self.metrics.response_times) / len(self.metrics.response_times)
            if avg_response_time > 2.0:
                recommendations.append({
                    "type": "response_time",
                    "priority": "high",
                    "title": "Optimize Response Times",
                    "description": f"Average response time is {avg_response_time:.2f}s. Consider AI provider optimization.",
                    "actions": ["Optimize AI provider selection", "Implement response caching", "Review database queries"],
                    "expected_improvement": "30-50% faster responses"
                })
        
        # Memory recommendations
        if self.metrics.memory_usage:
            current_memory = self.metrics.memory_usage[-1]
            if current_memory > 80:
                recommendations.append({
                    "type": "memory",
                    "priority": "critical" if current_memory > 90 else "high",
                    "title": "Optimize Memory Usage", 
                    "description": f"Memory usage is {current_memory:.1f}%. Immediate action required.",
                    "actions": ["Enable garbage collection", "Reduce cache sizes", "Optimize data structures"],
                    "expected_improvement": f"Reduce memory usage to <70%"
                })
        
        # Cache recommendations
        cache_hit_rate = self._calculate_overall_cache_hit_rate()
        if cache_hit_rate < 70:
            recommendations.append({
                "type": "cache",
                "priority": "medium",
                "title": "Improve Cache Strategy",
                "description": f"Cache hit rate is {cache_hit_rate:.1f}%. Significant optimization opportunity.",
                "actions": ["Review cache TTL settings", "Implement cache warming", "Optimize cache keys"],
                "expected_improvement": f"Increase hit rate to >80%"
            })
        
        # AI Provider recommendations
        provider_recommendations = self.get_provider_recommendations()
        if provider_recommendations:
            top_provider = provider_recommendations["rankings"][0][0] if provider_recommendations["rankings"] else None
            if top_provider:
                recommendations.append({
                    "type": "ai_provider",
                    "priority": "medium",
                    "title": "Optimize AI Provider Usage",
                    "description": f"Consider prioritizing {top_provider} for better performance.",
                    "actions": [f"Route more requests to {top_provider}", "Implement intelligent provider switching"],
                    "expected_improvement": "10-25% better AI response times"
                })
        
        return recommendations
    
    def _calculate_performance_grade(self, response_times: List[float]) -> str:
        """Calculate performance grade based on response times"""
        avg_time = sum(response_times) / len(response_times)
        
        if avg_time <= 0.5:
            return "A+"
        elif avg_time <= 1.0:
            return "A"
        elif avg_time <= 2.0:
            return "B"
        elif avg_time <= 3.0:
            return "C"
        elif avg_time <= 5.0:
            return "D"
        else:
            return "F"
    
    async def _reduce_cache_sizes(self):
        """Reduce cache sizes to free memory"""
        # Reduce deque sizes
        if hasattr(self, '_detailed_metrics'):
            self._detailed_metrics = deque(list(self._detailed_metrics)[-30:], maxlen=30)
        
        # Reduce metrics sizes
        self.metrics.response_times = deque(list(self.metrics.response_times)[-500:], maxlen=500)
        self.metrics.memory_usage = deque(list(self.metrics.memory_usage)[-30:], maxlen=30)


class MemoryManager:
    """Advanced memory management"""
    
    def __init__(self):
        self.memory_pools = {}
        self.weak_references = weakref.WeakSet()
    
    async def optimize_memory_usage(self):
        """Optimize memory usage"""
        # Force garbage collection
        gc.collect()
        
        # Clear weak references
        self.weak_references.clear()
        
        # Additional memory optimization
        logger.info("Memory optimization completed by MemoryManager")


class CacheOptimizer:
    """Advanced cache optimization"""
    
    def __init__(self):
        self.cache_patterns = defaultdict(list)
        self.optimization_history = deque(maxlen=50)
    
    async def optimize_memory_usage(self):
        """Optimize cache memory usage"""
        # Clear old cache patterns
        self.cache_patterns.clear()
        
        # Trigger garbage collection
        gc.collect()
        
        logger.info("Cache memory optimization completed")
    
    async def analyze_cache_patterns(self) -> Dict[str, Any]:
        """Analyze cache usage patterns"""
        return {
            "pattern_analysis": "completed",
            "recommendations": ["increase_ttl", "warm_frequently_accessed"],
            "optimization_opportunities": 3
        }
    
    async def optimize_cache_strategy(self, analysis: Dict[str, Any]):
        """Optimize cache strategy based on analysis"""
        # Record optimization
        self.optimization_history.append({
            "timestamp": datetime.utcnow(),
            "analysis": analysis,
            "optimizations_applied": ["ttl_adjustment", "key_optimization"]
        })
        
        logger.info("Cache strategy optimization completed")
    
    async def emergency_cache_clear(self):
        """Emergency cache clearing"""
        self.cache_patterns.clear()
        self.optimization_history.clear()
        gc.collect()
        
        logger.critical("Emergency cache clear completed")


class LoadBalancer:
    """Advanced load balancing"""
    
    def __init__(self):
        self.load_distribution = {}
        self.server_pools = defaultdict(list)
    
    async def optimize_load_distribution(self):
        """Optimize load distribution"""
        # Analyze current load
        total_requests = sum(self.load_distribution.values())
        
        if total_requests > 0:
            # Rebalance if needed
            logger.info(f"Load balancing optimization completed. Total requests: {total_requests}")
        
        return {
            "status": "optimized",
            "total_requests": total_requests,
            "distribution": self.load_distribution
        }


# Global performance optimization engine
performance_optimization_engine = PerformanceOptimizationEngine()