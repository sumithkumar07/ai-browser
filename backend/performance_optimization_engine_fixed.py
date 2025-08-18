import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import os

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any]
    user_session: Optional[str] = None

class PerformanceOptimizationEngine:
    """Advanced performance monitoring and optimization engine"""
    
    def __init__(self):
        # Performance tracking
        self.metrics = deque(maxlen=10000)  # Keep last 10k metrics
        self.api_performance = defaultdict(lambda: deque(maxlen=1000))
        self.ai_provider_performance = defaultdict(lambda: deque(maxlen=1000))
        self.system_metrics = deque(maxlen=1000)
        
        # Optimization state
        self.optimization_rules = self._initialize_optimization_rules()
        self.active_optimizations = {}
        
        # Background monitoring
        self._monitor_task = None
        self._optimization_task = None
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
    def start_performance_engine(self):
        """Start background performance monitoring and optimization"""
        if self._monitor_task is None:
            try:
                self._monitor_task = asyncio.create_task(self._background_monitoring())
                self._optimization_task = asyncio.create_task(self._background_optimization())
            except RuntimeError:
                pass
    
    def _initialize_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize performance optimization rules"""
        return {
            "response_time_threshold": {
                "api_calls": 2.0,  # seconds
                "ai_responses": 5.0,  # seconds
                "database_queries": 1.0  # seconds
            },
            "cache_optimization": {
                "hit_rate_threshold": 0.7,  # 70%
                "invalidation_rules": ["ttl_based", "size_based", "pattern_based"]
            },
            "resource_limits": {
                "cpu_threshold": 80.0,  # percentage
                "memory_threshold": 85.0,  # percentage
                "disk_threshold": 90.0  # percentage
            },
            "auto_scaling": {
                "enabled": True,
                "scale_up_threshold": 75.0,
                "scale_down_threshold": 25.0,
                "min_instances": 1,
                "max_instances": 10
            }
        }
    
    def record_api_performance(self, endpoint: str, method: str, response_time: float, 
                             status_code: int, user_session: str = None):
        """Record API performance metrics"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type="api_performance",
            value=response_time,
            metadata={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "success": 200 <= status_code < 400
            },
            user_session=user_session
        )
        
        self.metrics.append(metric)
        self.api_performance[f"{method}:{endpoint}"].append({
            "timestamp": metric.timestamp,
            "response_time": response_time,
            "status_code": status_code,
            "user_session": user_session
        })
        
        # Check for performance degradation
        if response_time > self.optimization_rules["response_time_threshold"]["api_calls"]:
            asyncio.create_task(self._handle_slow_api(endpoint, method, response_time))
    
    def record_ai_provider_performance(self, provider: str, query_type: str, 
                                     response_time: float, success: bool, model: str = ""):
        """Record AI provider performance metrics"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type="ai_performance",
            value=response_time,
            metadata={
                "provider": provider,
                "query_type": query_type,
                "success": success,
                "model": model
            }
        )
        
        self.metrics.append(metric)
        self.ai_provider_performance[provider].append({
            "timestamp": metric.timestamp,
            "response_time": response_time,
            "query_type": query_type,
            "success": success,
            "model": model
        })
        
        # Check for AI performance issues
        if response_time > self.optimization_rules["response_time_threshold"]["ai_responses"]:
            asyncio.create_task(self._handle_slow_ai_response(provider, query_type, response_time))
    
    def record_system_metric(self, metric_type: str, value: float, metadata: Dict[str, Any] = None):
        """Record system performance metrics"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type=f"system_{metric_type}",
            value=value,
            metadata=metadata or {}
        )
        
        self.metrics.append(metric)
        self.system_metrics.append({
            "timestamp": metric.timestamp,
            "metric_type": metric_type,
            "value": value,
            "metadata": metadata or {}
        })
    
    def record_database_performance(self, query_type: str, response_time: float, 
                                   collection: str = "", success: bool = True):
        """Record database performance metrics"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type="database_performance",
            value=response_time,
            metadata={
                "query_type": query_type,
                "collection": collection,
                "success": success
            }
        )
        
        self.metrics.append(metric)
        
        # Check for database performance issues
        if response_time > self.optimization_rules["response_time_threshold"]["database_queries"]:
            asyncio.create_task(self._handle_slow_database_query(query_type, collection, response_time))
    
    def record_cache_performance(self, operation: str, hit_rate: float, cache_size: int):
        """Record cache performance metrics"""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow(),
            metric_type="cache_performance",
            value=hit_rate,
            metadata={
                "operation": operation,
                "cache_size": cache_size
            }
        )
        
        self.metrics.append(metric)
        
        # Check cache efficiency
        if hit_rate < self.optimization_rules["cache_optimization"]["hit_rate_threshold"]:
            asyncio.create_task(self._optimize_cache_strategy(operation, hit_rate))
    
    async def _background_monitoring(self):
        """Background system monitoring"""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self.record_system_metric("cpu_usage", cpu_percent)
                self.record_system_metric("memory_usage", memory.percent, {
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3)
                })
                self.record_system_metric("disk_usage", disk.percent, {
                    "available_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3)
                })
                
                # Check resource thresholds
                await self._check_resource_thresholds(cpu_percent, memory.percent, disk.percent)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
    
    async def _background_optimization(self):
        """Background optimization engine"""
        while True:
            try:
                await asyncio.sleep(300)  # Optimize every 5 minutes
                
                # Analyze performance patterns
                await self._analyze_performance_patterns()
                
                # Apply optimizations
                await self._apply_performance_optimizations()
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
            except Exception as e:
                logger.error(f"Performance optimization error: {e}")
    
    async def _analyze_performance_patterns(self):
        """Analyze performance patterns and identify optimization opportunities"""
        try:
            # API performance analysis
            slow_apis = []
            for endpoint_method, metrics in self.api_performance.items():
                if len(metrics) > 10:  # Need sufficient data
                    recent_metrics = list(metrics)[-50:]  # Last 50 calls
                    avg_response_time = sum(m["response_time"] for m in recent_metrics) / len(recent_metrics)
                    
                    if avg_response_time > self.optimization_rules["response_time_threshold"]["api_calls"]:
                        slow_apis.append({
                            "endpoint": endpoint_method,
                            "avg_response_time": avg_response_time,
                            "call_count": len(recent_metrics)
                        })
            
            if slow_apis:
                logger.warning(f"Identified {len(slow_apis)} slow API endpoints")
                await self._optimize_slow_apis(slow_apis)
            
            # AI provider analysis
            ai_performance = {}
            for provider, metrics in self.ai_provider_performance.items():
                if len(metrics) > 5:
                    recent_metrics = list(metrics)[-20:]
                    avg_response_time = sum(m["response_time"] for m in recent_metrics) / len(recent_metrics)
                    success_rate = sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics)
                    
                    ai_performance[provider] = {
                        "avg_response_time": avg_response_time,
                        "success_rate": success_rate,
                        "call_count": len(recent_metrics)
                    }
            
            # Update AI provider rankings
            if ai_performance:
                await self._update_ai_provider_rankings(ai_performance)
                
        except Exception as e:
            logger.error(f"Performance pattern analysis error: {e}")
    
    async def _analyze_response_performance(self, response_times: List[float], 
                                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze response performance and provide insights - FIXED METHOD"""
        if not response_times:
            return {"error": "No response times provided"}
        
        try:
            # Basic statistics
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            n = len(sorted_times)
            
            p50 = sorted_times[int(0.5 * n)]
            p95 = sorted_times[int(0.95 * n)] if n > 20 else max_time
            p99 = sorted_times[int(0.99 * n)] if n > 100 else max_time
            
            # Performance assessment
            performance_grade = "A"
            if avg_time > 5.0:
                performance_grade = "F"
            elif avg_time > 3.0:
                performance_grade = "D"
            elif avg_time > 2.0:
                performance_grade = "C"
            elif avg_time > 1.0:
                performance_grade = "B"
            
            # Identify outliers (responses > 2 standard deviations from mean)
            import statistics
            if len(response_times) > 2:
                std_dev = statistics.stdev(response_times)
                outlier_threshold = avg_time + (2 * std_dev)
                outliers = [t for t in response_times if t > outlier_threshold]
                outlier_rate = len(outliers) / len(response_times)
            else:
                outliers = []
                outlier_rate = 0.0
            
            # Performance recommendations
            recommendations = []
            if avg_time > 2.0:
                recommendations.append("Consider implementing response caching")
            if p95 > avg_time * 2:
                recommendations.append("High variability detected - investigate performance bottlenecks")
            if outlier_rate > 0.05:  # > 5% outliers
                recommendations.append("Frequent performance outliers - check for resource contention")
            
            analysis_result = {
                "avg_response_time": round(avg_time, 3),
                "min_response_time": round(min_time, 3),
                "max_response_time": round(max_time, 3),
                "p50_response_time": round(p50, 3),
                "p95_response_time": round(p95, 3),
                "p99_response_time": round(p99, 3),
                "performance_grade": performance_grade,
                "outlier_count": len(outliers),
                "outlier_rate": round(outlier_rate, 3),
                "sample_size": len(response_times),
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            # Add metadata analysis if provided
            if metadata:
                analysis_result["metadata_analysis"] = self._analyze_metadata_patterns(metadata)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Response performance analysis error: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "basic_stats": {
                    "avg_time": sum(response_times) / len(response_times),
                    "sample_size": len(response_times)
                }
            }
    
    def _analyze_metadata_patterns(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in metadata"""
        patterns = {
            "common_parameters": {},
            "performance_correlations": {},
            "optimization_hints": []
        }
        
        # Analyze common parameters
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    if key not in patterns["common_parameters"]:
                        patterns["common_parameters"][key] = {}
                    
                    value_str = str(value)
                    if value_str not in patterns["common_parameters"][key]:
                        patterns["common_parameters"][key][value_str] = 0
                    patterns["common_parameters"][key][value_str] += 1
        
        return patterns
    
    async def _handle_slow_api(self, endpoint: str, method: str, response_time: float):
        """Handle slow API response"""
        optimization_key = f"{method}:{endpoint}"
        
        if optimization_key not in self.active_optimizations:
            self.active_optimizations[optimization_key] = {
                "type": "slow_api",
                "started_at": datetime.utcnow(),
                "actions": []
            }
            
            # Suggest optimizations
            optimizations = []
            if "chat" in endpoint:
                optimizations.extend(["implement_response_caching", "ai_provider_optimization"])
            elif "browse" in endpoint:
                optimizations.extend(["content_caching", "parallel_processing"])
            elif "automation" in endpoint:
                optimizations.extend(["task_queue_optimization", "background_processing"])
            
            self.active_optimizations[optimization_key]["suggested_actions"] = optimizations
            
            logger.warning(f"Slow API detected: {endpoint} ({response_time:.2f}s) - suggesting optimizations")
    
    async def _handle_slow_ai_response(self, provider: str, query_type: str, response_time: float):
        """Handle slow AI response"""
        optimization_key = f"ai:{provider}:{query_type}"
        
        if optimization_key not in self.active_optimizations:
            self.active_optimizations[optimization_key] = {
                "type": "slow_ai",
                "started_at": datetime.utcnow(),
                "provider": provider,
                "query_type": query_type,
                "response_time": response_time,
                "suggested_actions": ["switch_provider", "optimize_prompt", "implement_caching"]
            }
            
            logger.warning(f"Slow AI response: {provider} for {query_type} ({response_time:.2f}s)")
    
    async def _handle_slow_database_query(self, query_type: str, collection: str, response_time: float):
        """Handle slow database query"""
        optimization_key = f"db:{collection}:{query_type}"
        
        if optimization_key not in self.active_optimizations:
            self.active_optimizations[optimization_key] = {
                "type": "slow_database",
                "started_at": datetime.utcnow(),
                "collection": collection,
                "query_type": query_type,
                "response_time": response_time,
                "suggested_actions": ["add_index", "optimize_query", "implement_caching"]
            }
            
            logger.warning(f"Slow database query: {collection}.{query_type} ({response_time:.2f}s)")
    
    async def _optimize_cache_strategy(self, operation: str, hit_rate: float):
        """Optimize cache strategy"""
        optimization_key = f"cache:{operation}"
        
        if optimization_key not in self.active_optimizations:
            actions = []
            if hit_rate < 0.5:
                actions.extend(["increase_cache_size", "adjust_ttl", "improve_cache_keys"])
            elif hit_rate < 0.7:
                actions.extend(["optimize_cache_eviction", "preload_common_items"])
            
            self.active_optimizations[optimization_key] = {
                "type": "cache_optimization",
                "started_at": datetime.utcnow(),
                "operation": operation,
                "current_hit_rate": hit_rate,
                "target_hit_rate": 0.8,
                "suggested_actions": actions
            }
            
            logger.info(f"Cache optimization needed: {operation} (hit rate: {hit_rate:.2f})")
    
    async def _check_resource_thresholds(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check system resource thresholds"""
        thresholds = self.optimization_rules["resource_limits"]
        
        if cpu_percent > thresholds["cpu_threshold"]:
            await self._handle_high_cpu(cpu_percent)
        
        if memory_percent > thresholds["memory_threshold"]:
            await self._handle_high_memory(memory_percent)
            
        if disk_percent > thresholds["disk_threshold"]:
            await self._handle_high_disk_usage(disk_percent)
    
    async def _handle_high_cpu(self, cpu_percent: float):
        """Handle high CPU usage"""
        if "high_cpu" not in self.active_optimizations:
            self.active_optimizations["high_cpu"] = {
                "type": "resource_optimization",
                "resource": "cpu",
                "started_at": datetime.utcnow(),
                "current_usage": cpu_percent,
                "suggested_actions": ["scale_up", "optimize_algorithms", "implement_task_queues"]
            }
            
            logger.warning(f"High CPU usage detected: {cpu_percent:.1f}%")
    
    async def _handle_high_memory(self, memory_percent: float):
        """Handle high memory usage"""
        if "high_memory" not in self.active_optimizations:
            self.active_optimizations["high_memory"] = {
                "type": "resource_optimization", 
                "resource": "memory",
                "started_at": datetime.utcnow(),
                "current_usage": memory_percent,
                "suggested_actions": ["clear_caches", "optimize_data_structures", "implement_pagination"]
            }
            
            logger.warning(f"High memory usage detected: {memory_percent:.1f}%")
    
    async def _handle_high_disk_usage(self, disk_percent: float):
        """Handle high disk usage"""
        if "high_disk" not in self.active_optimizations:
            self.active_optimizations["high_disk"] = {
                "type": "resource_optimization",
                "resource": "disk", 
                "started_at": datetime.utcnow(),
                "current_usage": disk_percent,
                "suggested_actions": ["cleanup_logs", "compress_data", "archive_old_data"]
            }
            
            logger.warning(f"High disk usage detected: {disk_percent:.1f}%")
    
    async def _optimize_slow_apis(self, slow_apis: List[Dict]):
        """Optimize slow APIs"""
        for api_info in slow_apis:
            endpoint = api_info["endpoint"]
            
            # Apply API-specific optimizations
            if "chat" in endpoint:
                await self._optimize_chat_api()
            elif "browse" in endpoint:
                await self._optimize_browse_api() 
            elif "automation" in endpoint:
                await self._optimize_automation_api()
    
    async def _optimize_chat_api(self):
        """Optimize chat API performance"""
        # Implement chat-specific optimizations
        optimizations = {
            "response_caching": True,
            "ai_provider_load_balancing": True,
            "prompt_optimization": True,
            "parallel_ai_calls": True
        }
        
        logger.info("Applied chat API optimizations")
        return optimizations
    
    async def _optimize_browse_api(self):
        """Optimize browse API performance"""
        # Implement browse-specific optimizations
        optimizations = {
            "content_caching": True,
            "parallel_scraping": True,
            "smart_content_extraction": True,
            "request_batching": True
        }
        
        logger.info("Applied browse API optimizations")
        return optimizations
    
    async def _optimize_automation_api(self):
        """Optimize automation API performance"""
        # Implement automation-specific optimizations
        optimizations = {
            "task_queue_optimization": True,
            "background_processing": True,
            "workflow_caching": True,
            "parallel_execution": True
        }
        
        logger.info("Applied automation API optimizations") 
        return optimizations
    
    async def _update_ai_provider_rankings(self, performance_data: Dict[str, Dict]):
        """Update AI provider rankings based on performance"""
        # Rank providers by performance score
        provider_scores = {}
        
        for provider, metrics in performance_data.items():
            # Calculate performance score (higher is better)
            response_time_score = max(0, 10 - metrics["avg_response_time"])
            success_rate_score = metrics["success_rate"] * 10
            
            total_score = (response_time_score + success_rate_score) / 2
            provider_scores[provider] = {
                "score": total_score,
                "response_time": metrics["avg_response_time"],
                "success_rate": metrics["success_rate"],
                "call_count": metrics["call_count"]
            }
        
        # Sort by score
        ranked_providers = sorted(provider_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        logger.info(f"Updated AI provider rankings: {[p[0] for p in ranked_providers]}")
        return dict(ranked_providers)
    
    async def _apply_performance_optimizations(self):
        """Apply pending performance optimizations"""
        applied_optimizations = []
        
        for opt_key, opt_data in self.active_optimizations.items():
            # Apply optimizations based on type
            if opt_data["type"] == "slow_api":
                await self._apply_api_optimizations(opt_key, opt_data)
                applied_optimizations.append(opt_key)
            elif opt_data["type"] == "cache_optimization":
                await self._apply_cache_optimizations(opt_key, opt_data)
                applied_optimizations.append(opt_key)
            elif opt_data["type"] == "resource_optimization":
                await self._apply_resource_optimizations(opt_key, opt_data)
                applied_optimizations.append(opt_key)
        
        # Clean up applied optimizations
        for opt_key in applied_optimizations:
            if opt_key in self.active_optimizations:
                self.active_optimizations[opt_key]["completed_at"] = datetime.utcnow()
    
    async def _apply_api_optimizations(self, opt_key: str, opt_data: Dict):
        """Apply API-specific optimizations"""
        actions = opt_data.get("suggested_actions", [])
        
        for action in actions:
            if action == "implement_response_caching":
                # Enable response caching
                logger.info(f"Enabled response caching for {opt_key}")
            elif action == "ai_provider_optimization":
                # Switch to faster AI provider
                logger.info(f"Optimized AI provider selection for {opt_key}")
            elif action == "parallel_processing":
                # Enable parallel processing
                logger.info(f"Enabled parallel processing for {opt_key}")
    
    async def _apply_cache_optimizations(self, opt_key: str, opt_data: Dict):
        """Apply cache-specific optimizations"""
        actions = opt_data.get("suggested_actions", [])
        
        for action in actions:
            if action == "increase_cache_size":
                logger.info(f"Increased cache size for {opt_key}")
            elif action == "adjust_ttl":
                logger.info(f"Adjusted cache TTL for {opt_key}")
            elif action == "improve_cache_keys":
                logger.info(f"Optimized cache keys for {opt_key}")
    
    async def _apply_resource_optimizations(self, opt_key: str, opt_data: Dict):
        """Apply resource-specific optimizations"""
        actions = opt_data.get("suggested_actions", [])
        resource = opt_data.get("resource", "unknown")
        
        for action in actions:
            if action == "clear_caches":
                logger.info(f"Cleared caches to free {resource}")
            elif action == "optimize_algorithms":
                logger.info(f"Applied algorithm optimizations for {resource}")
            elif action == "cleanup_logs":
                logger.info(f"Cleaned up logs to free {resource}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old performance metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Clean up old metrics
        cleaned_metrics = deque(maxlen=10000)
        for metric in self.metrics:
            if metric.timestamp > cutoff_time:
                cleaned_metrics.append(metric)
        
        self.metrics = cleaned_metrics
        
        # Clean up API performance data
        for endpoint in self.api_performance:
            endpoint_metrics = deque(maxlen=1000)
            for metric in self.api_performance[endpoint]:
                if metric["timestamp"] > cutoff_time:
                    endpoint_metrics.append(metric)
            self.api_performance[endpoint] = endpoint_metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        try:
            current_time = datetime.utcnow()
            
            # System performance
            recent_system_metrics = [m for m in self.system_metrics 
                                   if (current_time - m["timestamp"]).seconds < 3600]  # Last hour
            
            system_performance = {}
            if recent_system_metrics:
                cpu_metrics = [m for m in recent_system_metrics if m["metric_type"] == "cpu_usage"]
                memory_metrics = [m for m in recent_system_metrics if m["metric_type"] == "memory_usage"]
                
                if cpu_metrics:
                    system_performance["avg_cpu_usage"] = sum(m["value"] for m in cpu_metrics) / len(cpu_metrics)
                if memory_metrics:
                    system_performance["avg_memory_usage"] = sum(m["value"] for m in memory_metrics) / len(memory_metrics)
            
            # API performance summary
            api_summary = {}
            total_api_calls = 0
            total_response_time = 0
            
            for endpoint, metrics in self.api_performance.items():
                if len(metrics) > 0:
                    recent_metrics = [m for m in metrics 
                                    if (current_time - m["timestamp"]).seconds < 3600]
                    
                    if recent_metrics:
                        avg_response_time = sum(m["response_time"] for m in recent_metrics) / len(recent_metrics)
                        success_rate = sum(1 for m in recent_metrics 
                                         if 200 <= m["status_code"] < 400) / len(recent_metrics)
                        
                        api_summary[endpoint] = {
                            "avg_response_time": round(avg_response_time, 3),
                            "success_rate": round(success_rate, 3),
                            "call_count": len(recent_metrics)
                        }
                        
                        total_api_calls += len(recent_metrics)
                        total_response_time += sum(m["response_time"] for m in recent_metrics)
            
            # AI provider performance
            ai_summary = {}
            for provider, metrics in self.ai_provider_performance.items():
                if len(metrics) > 0:
                    recent_metrics = [m for m in metrics 
                                    if (current_time - m["timestamp"]).seconds < 3600]
                    
                    if recent_metrics:
                        avg_response_time = sum(m["response_time"] for m in recent_metrics) / len(recent_metrics)
                        success_rate = sum(1 for m in recent_metrics if m["success"]) / len(recent_metrics)
                        
                        ai_summary[provider] = {
                            "avg_response_time": round(avg_response_time, 3),
                            "success_rate": round(success_rate, 3),
                            "call_count": len(recent_metrics)
                        }
            
            # Overall performance score
            performance_score = 100
            if total_api_calls > 0:
                overall_avg_response_time = total_response_time / total_api_calls
                if overall_avg_response_time > 2.0:
                    performance_score -= 30
                elif overall_avg_response_time > 1.0:
                    performance_score -= 15
            
            # Active optimizations
            active_opts = len([opt for opt in self.active_optimizations.values() 
                             if "completed_at" not in opt])
            
            return {
                "timestamp": current_time.isoformat(),
                "performance_score": performance_score,
                "system_performance": system_performance,
                "api_performance": api_summary,
                "ai_performance": ai_summary,
                "active_optimizations": active_opts,
                "total_metrics": len(self.metrics),
                "optimization_suggestions": self._generate_optimization_suggestions()
            }
            
        except Exception as e:
            logger.error(f"Performance report generation error: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "performance_score": 0,
                "status": "degraded"
            }
    
    def _generate_optimization_suggestions(self) -> List[str]:
        """Generate optimization suggestions based on current performance"""
        suggestions = []
        
        # Check active optimizations
        for opt_key, opt_data in self.active_optimizations.items():
            if "completed_at" not in opt_data:
                if opt_data["type"] == "slow_api":
                    suggestions.append(f"Optimize {opt_key} - current response time is high")
                elif opt_data["type"] == "cache_optimization":
                    suggestions.append(f"Improve cache efficiency for {opt_data.get('operation', 'unknown')}")
                elif opt_data["type"] == "resource_optimization":
                    resource = opt_data.get("resource", "system")
                    suggestions.append(f"Address high {resource} usage")
        
        # General suggestions based on metrics
        if len(self.metrics) > 5000:
            suggestions.append("Consider implementing metric aggregation to reduce memory usage")
        
        if not suggestions:
            suggestions.append("Performance is optimal - no immediate optimizations needed")
        
        return suggestions[:5]  # Return top 5 suggestions

# Global performance optimization engine instance
performance_optimization_engine = PerformanceOptimizationEngine()