import time
import psutil
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
import threading
import json
import os
from dataclasses import dataclass, asdict
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import httpx

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    load_average: List[float]
    uptime_seconds: float
    timestamp: str

@dataclass
class APIMetrics:
    endpoint: str
    method: str
    response_time: float
    status_code: int
    timestamp: str
    content_length: Optional[int] = None
    error_message: Optional[str] = None

@dataclass
class UserMetrics:
    session_id: str
    action: str
    duration: float
    success: bool
    timestamp: str
    metadata: Dict[str, Any]

class RealTimePerformanceMonitor:
    """
    Advanced real-time performance monitoring system with predictive analytics,
    automatic optimization suggestions, and comprehensive metrics collection.
    """
    
    def __init__(self, max_history=10000):
        self.max_history = max_history
        
        # Metrics storage
        self.system_metrics = deque(maxlen=max_history)
        self.api_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.user_metrics = deque(maxlen=max_history)
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 85.0,
            'memory_warning': 75.0,
            'memory_critical': 90.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0,
            'api_response_warning': 2.0,
            'api_response_critical': 5.0,
            'error_rate_warning': 5.0,
            'error_rate_critical': 10.0
        }
        
        # Statistics and analytics
        self.stats = {
            'system_alerts': defaultdict(int),
            'api_calls_total': defaultdict(int),
            'error_counts': defaultdict(int),
            'user_actions': defaultdict(int),
            'optimization_suggestions': []
        }
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_interval = 10  # seconds
        self.monitoring_task = None
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Predictive analytics
        self.prediction_models = {}
        self.performance_trends = defaultdict(deque)
        
        # Optimization engine
        self.optimization_history = deque(maxlen=100)
        
        # Start monitoring
        self.start_monitoring()
    
    def start_monitoring(self):
        """Start background performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_task = asyncio.create_task(self._background_monitoring())
            logger.info("🔍 Real-time performance monitoring started")
    
    def stop_monitoring(self):
        """Stop background performance monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_task:
                self.monitoring_task.cancel()
            logger.info("🛑 Performance monitoring stopped")
    
    async def _background_monitoring(self):
        """Background task for continuous system monitoring"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Analyze performance trends
                await self._analyze_trends()
                
                # Generate optimization suggestions
                await self._generate_optimization_suggestions()
                
                # Check for alerts
                await self._check_alerts()
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Background monitoring error: {str(e)}")
                await asyncio.sleep(5)  # Retry after 5 seconds
    
    async def _collect_system_metrics(self):
        """Collect comprehensive system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics  
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Load average (Unix-like systems)
            try:
                load_avg = list(psutil.getloadavg())
            except:
                load_avg = [0.0, 0.0, 0.0]
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            # Create metrics object
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                load_average=load_avg,
                uptime_seconds=uptime_seconds,
                timestamp=datetime.utcnow().isoformat()
            )
            
            with self._lock:
                self.system_metrics.append(metrics)
                
                # Update performance trends
                self.performance_trends['cpu'].append(cpu_percent)
                self.performance_trends['memory'].append(memory_percent)
                self.performance_trends['disk'].append(disk_percent)
                
                # Limit trend data
                for trend in self.performance_trends.values():
                    if len(trend) > 100:
                        trend.popleft()
            
        except Exception as e:
            logger.error(f"System metrics collection error: {str(e)}")
    
    def record_api_call(self, endpoint: str, method: str, response_time: float, 
                       status_code: int, content_length: Optional[int] = None,
                       error_message: Optional[str] = None):
        """Record API call metrics"""
        
        metrics = APIMetrics(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code,
            content_length=content_length,
            error_message=error_message,
            timestamp=datetime.utcnow().isoformat()
        )
        
        with self._lock:
            self.api_metrics[endpoint].append(metrics)
            self.stats['api_calls_total'][endpoint] += 1
            
            if status_code >= 400:
                self.stats['error_counts'][endpoint] += 1
    
    def record_user_action(self, session_id: str, action: str, duration: float,
                          success: bool, metadata: Dict[str, Any] = None):
        """Record user action metrics"""
        
        metrics = UserMetrics(
            session_id=session_id,
            action=action,
            duration=duration,
            success=success,
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat()
        )
        
        with self._lock:
            self.user_metrics.append(metrics)
            self.stats['user_actions'][action] += 1
    
    async def _analyze_trends(self):
        """Analyze performance trends for predictive insights"""
        try:
            with self._lock:
                for metric_name, values in self.performance_trends.items():
                    if len(values) >= 10:
                        # Calculate trend direction
                        recent_values = list(values)[-10:]
                        trend = np.polyfit(range(len(recent_values)), recent_values, 1)[0]
                        
                        # Store trend information
                        if metric_name not in self.prediction_models:
                            self.prediction_models[metric_name] = {}
                        
                        self.prediction_models[metric_name]['trend'] = trend
                        self.prediction_models[metric_name]['current'] = recent_values[-1]
                        self.prediction_models[metric_name]['average'] = np.mean(recent_values)
                        self.prediction_models[metric_name]['volatility'] = np.std(recent_values)
                        
        except Exception as e:
            logger.error(f"Trend analysis error: {str(e)}")
    
    async def _generate_optimization_suggestions(self):
        """Generate intelligent optimization suggestions"""
        try:
            suggestions = []
            current_time = datetime.utcnow().isoformat()
            
            with self._lock:
                # System resource optimization
                if self.system_metrics:
                    latest_metrics = self.system_metrics[-1]
                    
                    if latest_metrics.cpu_percent > self.thresholds['cpu_warning']:
                        suggestions.append({
                            "type": "performance",
                            "priority": "high" if latest_metrics.cpu_percent > self.thresholds['cpu_critical'] else "medium",
                            "category": "cpu",
                            "message": f"CPU usage is {latest_metrics.cpu_percent:.1f}%. Consider optimizing resource-intensive operations.",
                            "recommendations": [
                                "Implement request rate limiting",
                                "Optimize database queries",
                                "Consider horizontal scaling",
                                "Review background task efficiency"
                            ],
                            "timestamp": current_time
                        })
                    
                    if latest_metrics.memory_percent > self.thresholds['memory_warning']:
                        suggestions.append({
                            "type": "performance",
                            "priority": "high" if latest_metrics.memory_percent > self.thresholds['memory_critical'] else "medium",
                            "category": "memory",
                            "message": f"Memory usage is {latest_metrics.memory_percent:.1f}%. Memory optimization needed.",
                            "recommendations": [
                                "Implement more aggressive caching policies",
                                "Review memory-intensive operations",
                                "Consider increasing cache TTL",
                                "Optimize data structures"
                            ],
                            "timestamp": current_time
                        })
                
                # API performance optimization
                for endpoint, metrics_list in self.api_metrics.items():
                    if len(metrics_list) >= 10:
                        recent_metrics = list(metrics_list)[-10:]
                        avg_response_time = np.mean([m.response_time for m in recent_metrics])
                        error_rate = sum(1 for m in recent_metrics if m.status_code >= 400) / len(recent_metrics) * 100
                        
                        if avg_response_time > self.thresholds['api_response_warning']:
                            suggestions.append({
                                "type": "api",
                                "priority": "high" if avg_response_time > self.thresholds['api_response_critical'] else "medium",
                                "category": "response_time",
                                "message": f"Endpoint {endpoint} has high average response time: {avg_response_time:.2f}s",
                                "recommendations": [
                                    "Implement endpoint-specific caching",
                                    "Optimize database queries for this endpoint",
                                    "Consider adding request compression",
                                    "Review endpoint logic for bottlenecks"
                                ],
                                "endpoint": endpoint,
                                "timestamp": current_time
                            })
                        
                        if error_rate > self.thresholds['error_rate_warning']:
                            suggestions.append({
                                "type": "reliability",
                                "priority": "high",
                                "category": "error_rate",
                                "message": f"Endpoint {endpoint} has high error rate: {error_rate:.1f}%",
                                "recommendations": [
                                    "Review error handling logic",
                                    "Implement better input validation",
                                    "Add comprehensive logging",
                                    "Consider circuit breaker pattern"
                                ],
                                "endpoint": endpoint,
                                "timestamp": current_time
                            })
                
                # Trend-based predictions
                for metric_name, model in self.prediction_models.items():
                    trend = model.get('trend', 0)
                    current = model.get('current', 0)
                    
                    # Predict future values
                    if trend > 0 and current > 70:  # Rising trend approaching threshold
                        suggestions.append({
                            "type": "predictive",
                            "priority": "medium",
                            "category": metric_name,
                            "message": f"{metric_name.capitalize()} usage trending upward. Current: {current:.1f}%, Trend: +{trend:.2f}%/period",
                            "recommendations": [
                                f"Monitor {metric_name} usage closely",
                                "Consider proactive scaling",
                                "Review recent changes that may impact performance",
                                "Prepare optimization strategies"
                            ],
                            "timestamp": current_time
                        })
                
                # Update optimization suggestions (keep last 50)
                self.stats['optimization_suggestions'].extend(suggestions)
                if len(self.stats['optimization_suggestions']) > 50:
                    self.stats['optimization_suggestions'] = self.stats['optimization_suggestions'][-50:]
                
        except Exception as e:
            logger.error(f"Optimization suggestion generation error: {str(e)}")
    
    async def _check_alerts(self):
        """Check for performance alerts and record them"""
        try:
            with self._lock:
                if self.system_metrics:
                    latest_metrics = self.system_metrics[-1]
                    
                    # CPU alerts
                    if latest_metrics.cpu_percent > self.thresholds['cpu_critical']:
                        self.stats['system_alerts']['cpu_critical'] += 1
                        logger.warning(f"🚨 CRITICAL: CPU usage at {latest_metrics.cpu_percent:.1f}%")
                    elif latest_metrics.cpu_percent > self.thresholds['cpu_warning']:
                        self.stats['system_alerts']['cpu_warning'] += 1
                        logger.warning(f"⚠️ WARNING: CPU usage at {latest_metrics.cpu_percent:.1f}%")
                    
                    # Memory alerts
                    if latest_metrics.memory_percent > self.thresholds['memory_critical']:
                        self.stats['system_alerts']['memory_critical'] += 1
                        logger.warning(f"🚨 CRITICAL: Memory usage at {latest_metrics.memory_percent:.1f}%")
                    elif latest_metrics.memory_percent > self.thresholds['memory_warning']:
                        self.stats['system_alerts']['memory_warning'] += 1
                        logger.warning(f"⚠️ WARNING: Memory usage at {latest_metrics.memory_percent:.1f}%")
                    
                    # Disk alerts
                    if latest_metrics.disk_percent > self.thresholds['disk_critical']:
                        self.stats['system_alerts']['disk_critical'] += 1
                        logger.warning(f"🚨 CRITICAL: Disk usage at {latest_metrics.disk_percent:.1f}%")
                    elif latest_metrics.disk_percent > self.thresholds['disk_warning']:
                        self.stats['system_alerts']['disk_warning'] += 1
                        logger.warning(f"⚠️ WARNING: Disk usage at {latest_metrics.disk_percent:.1f}%")
                        
        except Exception as e:
            logger.error(f"Alert checking error: {str(e)}")
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time performance metrics"""
        with self._lock:
            # Current system metrics
            current_system = asdict(self.system_metrics[-1]) if self.system_metrics else {}
            
            # API performance summary
            api_summary = {}
            for endpoint, metrics_list in self.api_metrics.items():
                if metrics_list:
                    recent_metrics = list(metrics_list)[-10:]  # Last 10 calls
                    api_summary[endpoint] = {
                        "total_calls": len(metrics_list),
                        "avg_response_time": np.mean([m.response_time for m in recent_metrics]),
                        "min_response_time": min([m.response_time for m in recent_metrics]),
                        "max_response_time": max([m.response_time for m in recent_metrics]),
                        "error_rate": sum(1 for m in recent_metrics if m.status_code >= 400) / len(recent_metrics) * 100,
                        "last_call": asdict(recent_metrics[-1])
                    }
            
            # Performance trends
            trend_summary = {}
            for metric_name, model in self.prediction_models.items():
                trend_summary[metric_name] = {
                    "current": model.get('current', 0),
                    "trend": model.get('trend', 0),
                    "average": model.get('average', 0),
                    "volatility": model.get('volatility', 0),
                    "status": "increasing" if model.get('trend', 0) > 0.1 else "decreasing" if model.get('trend', 0) < -0.1 else "stable"
                }
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": current_system,
                "api_performance": api_summary,
                "trends": trend_summary,
                "alerts": dict(self.stats['system_alerts']),
                "optimization_suggestions": self.stats['optimization_suggestions'][-5:],  # Last 5 suggestions
                "health_score": self._calculate_health_score(),
                "monitoring_active": self.monitoring_active
            }
    
    def get_historical_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """Get historical performance metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            # Filter metrics by time range
            recent_system_metrics = [
                m for m in self.system_metrics 
                if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) > cutoff_time
            ]
            
            # Calculate historical statistics
            if recent_system_metrics:
                cpu_values = [m.cpu_percent for m in recent_system_metrics]
                memory_values = [m.memory_percent for m in recent_system_metrics]
                
                historical_stats = {
                    "timerange_hours": hours,
                    "data_points": len(recent_system_metrics),
                    "cpu": {
                        "average": np.mean(cpu_values),
                        "min": min(cpu_values),
                        "max": max(cpu_values),
                        "std": np.std(cpu_values)
                    },
                    "memory": {
                        "average": np.mean(memory_values),
                        "min": min(memory_values),
                        "max": max(memory_values),
                        "std": np.std(memory_values)
                    }
                }
                
                return {
                    "historical_stats": historical_stats,
                    "metrics_data": [asdict(m) for m in recent_system_metrics[-50:]]  # Last 50 points
                }
            
            return {"historical_stats": {}, "metrics_data": []}
    
    def _calculate_health_score(self) -> int:
        """Calculate overall system health score (0-100)"""
        if not self.system_metrics:
            return 50  # Unknown state
        
        latest_metrics = self.system_metrics[-1]
        score = 100
        
        # CPU impact
        if latest_metrics.cpu_percent > 80:
            score -= 25
        elif latest_metrics.cpu_percent > 60:
            score -= 10
        
        # Memory impact
        if latest_metrics.memory_percent > 85:
            score -= 25
        elif latest_metrics.memory_percent > 70:
            score -= 10
        
        # Disk impact
        if latest_metrics.disk_percent > 90:
            score -= 15
        elif latest_metrics.disk_percent > 80:
            score -= 5
        
        # API performance impact
        recent_errors = sum(self.stats['error_counts'].values())
        total_calls = sum(self.stats['api_calls_total'].values())
        if total_calls > 0:
            error_rate = (recent_errors / total_calls) * 100
            if error_rate > 10:
                score -= 20
            elif error_rate > 5:
                score -= 10
        
        return max(0, score)
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in various formats"""
        data = self.get_real_time_metrics()
        
        if format_type == "json":
            return json.dumps(data, indent=2, default=str)
        elif format_type == "summary":
            return self._generate_summary_report(data)
        else:
            return str(data)
    
    def _generate_summary_report(self, data: Dict[str, Any]) -> str:
        """Generate human-readable summary report"""
        report = []
        report.append("=== AETHER Performance Monitor Summary ===")
        report.append(f"Timestamp: {data['timestamp']}")
        report.append(f"Health Score: {data['health_score']}/100")
        report.append("")
        
        # System metrics
        if 'system' in data and data['system']:
            sys = data['system']
            report.append("System Resources:")
            report.append(f"  CPU: {sys.get('cpu_percent', 0):.1f}%")
            report.append(f"  Memory: {sys.get('memory_percent', 0):.1f}% ({sys.get('memory_used_gb', 0):.1f}GB / {sys.get('memory_total_gb', 0):.1f}GB)")
            report.append(f"  Disk: {sys.get('disk_percent', 0):.1f}% ({sys.get('disk_used_gb', 0):.1f}GB / {sys.get('disk_total_gb', 0):.1f}GB)")
            report.append("")
        
        # Top API endpoints
        if 'api_performance' in data and data['api_performance']:
            report.append("API Performance (Top 5):")
            api_items = sorted(data['api_performance'].items(), 
                             key=lambda x: x[1].get('total_calls', 0), reverse=True)[:5]
            for endpoint, metrics in api_items:
                report.append(f"  {endpoint}:")
                report.append(f"    Calls: {metrics.get('total_calls', 0)}")
                report.append(f"    Avg Response: {metrics.get('avg_response_time', 0):.3f}s")
                report.append(f"    Error Rate: {metrics.get('error_rate', 0):.1f}%")
            report.append("")
        
        # Recent optimization suggestions
        if 'optimization_suggestions' in data and data['optimization_suggestions']:
            report.append("Recent Optimization Suggestions:")
            for suggestion in data['optimization_suggestions'][-3:]:
                report.append(f"  [{suggestion.get('priority', 'medium').upper()}] {suggestion.get('message', '')}")
            report.append("")
        
        report.append("=== End Report ===")
        return "\n".join(report)

# Global performance monitor instance
performance_monitor = RealTimePerformanceMonitor()

# Export convenience functions
def record_api_call(endpoint: str, method: str, response_time: float, status_code: int, 
                   content_length: Optional[int] = None, error_message: Optional[str] = None):
    """Convenience function to record API call"""
    performance_monitor.record_api_call(endpoint, method, response_time, status_code, 
                                      content_length, error_message)

def record_user_action(session_id: str, action: str, duration: float, success: bool, 
                      metadata: Dict[str, Any] = None):
    """Convenience function to record user action"""
    performance_monitor.record_user_action(session_id, action, duration, success, metadata)

def get_performance_metrics():
    """Get current performance metrics"""
    return performance_monitor.get_real_time_metrics()

def get_historical_metrics(hours: int = 1):
    """Get historical performance metrics"""
    return performance_monitor.get_historical_metrics(hours)