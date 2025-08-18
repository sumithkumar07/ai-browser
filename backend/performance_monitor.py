import time
import psutil
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from collections import deque
import json

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'api_calls': deque(maxlen=1000),  # Last 1000 API calls
            'response_times': deque(maxlen=1000),
            'errors': deque(maxlen=100),  # Last 100 errors
            'system_metrics': deque(maxlen=60),  # Last 60 system snapshots (1 per minute)
            'ai_provider_stats': {},
            'cache_stats': deque(maxlen=60)
        }
        
        # Start background monitoring
        asyncio.create_task(self._background_monitoring())
    
    def record_api_call(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Record API call metrics"""
        timestamp = datetime.utcnow()
        
        call_data = {
            'timestamp': timestamp.isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time
        }
        
        self.metrics['api_calls'].append(call_data)
        self.metrics['response_times'].append(response_time)
        
        # Log slow requests
        if response_time > 5.0:
            logger.warning(f"Slow request: {method} {endpoint} took {response_time:.2f}s")
    
    def record_error(self, error_type: str, message: str, endpoint: str = None):
        """Record error metrics"""
        error_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': error_type,
            'message': message,
            'endpoint': endpoint
        }
        
        self.metrics['errors'].append(error_data)
        logger.error(f"Error recorded: {error_type} - {message}")
    
    def record_ai_provider_usage(self, provider: str, query_type: str, response_time: float, success: bool):
        """Record AI provider performance"""
        if provider not in self.metrics['ai_provider_stats']:
            self.metrics['ai_provider_stats'][provider] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'avg_response_time': 0,
                'response_times': deque(maxlen=100),
                'query_types': {}
            }
        
        stats = self.metrics['ai_provider_stats'][provider]
        stats['total_calls'] += 1
        stats['response_times'].append(response_time)
        
        if success:
            stats['successful_calls'] += 1
        else:
            stats['failed_calls'] += 1
        
        # Update average response time
        if stats['response_times']:
            stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
        
        # Track query types
        if query_type not in stats['query_types']:
            stats['query_types'][query_type] = 0
        stats['query_types'][query_type] += 1
    
    async def _background_monitoring(self):
        """Background task to collect system metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # System metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'disk_percent': disk.percent,
                    'disk_free_gb': disk.free / (1024**3)
                }
                
                self.metrics['system_metrics'].append(system_data)
                
                # Log alerts
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                if memory.percent > 85:
                    logger.warning(f"High memory usage: {memory.percent}%")
                if disk.percent > 90:
                    logger.warning(f"High disk usage: {disk.percent}%")
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        # Recent API calls (last hour)
        recent_calls = [
            call for call in self.metrics['api_calls']
            if datetime.fromisoformat(call['timestamp']) > one_hour_ago
        ]
        
        # Recent errors (last hour)
        recent_errors = [
            error for error in self.metrics['errors']
            if datetime.fromisoformat(error['timestamp']) > one_hour_ago
        ]
        
        # Response time stats
        response_times = list(self.metrics['response_times'])
        
        summary = {
            'timestamp': now.isoformat(),
            'api_calls': {
                'total_last_hour': len(recent_calls),
                'total_all_time': len(self.metrics['api_calls']),
                'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
                'slow_requests_last_hour': len([c for c in recent_calls if c['response_time'] > 2.0])
            },
            'errors': {
                'total_last_hour': len(recent_errors),
                'total_all_time': len(self.metrics['errors']),
                'recent_error_types': list(set([e['type'] for e in recent_errors[-10:]]))
            },
            'system': self.metrics['system_metrics'][-1] if self.metrics['system_metrics'] else {},
            'ai_providers': {
                provider: {
                    'total_calls': stats['total_calls'],
                    'success_rate': (stats['successful_calls'] / stats['total_calls'] * 100) if stats['total_calls'] > 0 else 0,
                    'avg_response_time': stats['avg_response_time'],
                    'popular_query_types': sorted(stats['query_types'].items(), key=lambda x: x[1], reverse=True)[:3]
                }
                for provider, stats in self.metrics['ai_provider_stats'].items()
            }
        }
        
        return summary
    
    def get_health_status(self) -> Dict:
        """Get overall system health status"""
        try:
            # Check recent errors
            recent_errors = [
                error for error in self.metrics['errors']
                if datetime.fromisoformat(error['timestamp']) > datetime.utcnow() - timedelta(minutes=5)
            ]
            
            # Check response times
            recent_response_times = list(self.metrics['response_times'])[-10:]
            avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0
            
            # Check system resources
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Determine health status
            status = "healthy"
            issues = []
            
            if len(recent_errors) > 5:
                status = "degraded"
                issues.append(f"High error rate: {len(recent_errors)} errors in last 5 minutes")
            
            if avg_response_time > 3.0:
                status = "degraded" if status == "healthy" else "unhealthy"
                issues.append(f"Slow response times: {avg_response_time:.2f}s average")
            
            if cpu_percent > 90:
                status = "unhealthy"
                issues.append(f"High CPU usage: {cpu_percent}%")
            
            if memory_percent > 95:
                status = "unhealthy"
                issues.append(f"High memory usage: {memory_percent}%")
            
            return {
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'issues': issues,
                'metrics': {
                    'recent_errors': len(recent_errors),
                    'avg_response_time': avg_response_time,
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent
                }
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                'status': 'unknown',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorator for monitoring API endpoints
def monitor_performance(func):
    """Decorator to monitor API endpoint performance"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = func.__name__
        method = "POST"  # Default, can be enhanced
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            performance_monitor.record_error("API_ERROR", str(e), endpoint)
            raise
        finally:
            response_time = time.time() - start_time
            performance_monitor.record_api_call(endpoint, method, status_code, response_time)
    
    return wrapper