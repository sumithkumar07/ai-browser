import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import httpx
import psutil
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"
    UNKNOWN = "unknown"

class IntegrationType(Enum):
    API = "api"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    WEBHOOK = "webhook"
    AUTHENTICATION = "authentication"
    FILE_SYSTEM = "file_system"
    MESSAGING = "messaging"

@dataclass
class HealthCheck:
    """Health check configuration"""
    check_id: str
    name: str
    integration_type: IntegrationType
    check_method: str  # 'http', 'database', 'custom'
    endpoint: Optional[str] = None
    expected_status: int = 200
    timeout_seconds: int = 10
    check_interval_seconds: int = 60
    failure_threshold: int = 3
    success_threshold: int = 2
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class HealthResult:
    """Health check result"""
    check_id: str
    status: HealthStatus
    response_time: float
    timestamp: datetime
    message: str
    details: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}

class IntegrationHealthMonitor:
    """Comprehensive integration health monitoring system"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.health_checks = self.db.health_checks
        self.health_results = self.db.health_results
        self.health_alerts = self.db.health_alerts
        self.health_metrics = self.db.health_metrics
        
        # Runtime state
        self.registered_checks = {}  # check_id -> HealthCheck
        self.check_results = defaultdict(lambda: deque(maxlen=100))  # check_id -> results
        self.check_states = {}  # check_id -> current state
        
        # Monitoring configuration
        self.alert_handlers = {}
        self.notification_channels = []
        
        # Performance tracking
        self.system_metrics = deque(maxlen=1000)
        self.integration_metrics = defaultdict(lambda: deque(maxlen=200))
        
        # Background tasks
        self.monitor_task = None
        self.metrics_task = None
        self.alert_task = None
        
        # Statistics
        self.stats = {
            "total_checks": 0,
            "healthy_integrations": 0,
            "unhealthy_integrations": 0,
            "checks_per_minute": 0,
            "average_response_time": 0.0,
            "uptime_percentage": 100.0
        }
        
        # Initialize default health checks
        self._initialize_default_checks()
    
    def _initialize_default_checks(self):
        """Initialize default health checks for core services"""
        
        default_checks = [
            HealthCheck(
                check_id="mongodb_connection",
                name="MongoDB Connection",
                integration_type=IntegrationType.DATABASE,
                check_method="database",
                timeout_seconds=5,
                check_interval_seconds=30,
                metadata={"critical": True}
            ),
            HealthCheck(
                check_id="groq_api",
                name="Groq AI API",
                integration_type=IntegrationType.API,
                check_method="http",
                endpoint="https://api.groq.com/openai/v1/models",
                timeout_seconds=10,
                check_interval_seconds=60,
                metadata={"api_key_required": True}
            ),
            HealthCheck(
                check_id="system_resources",
                name="System Resources",
                integration_type=IntegrationType.FILE_SYSTEM,
                check_method="custom",
                timeout_seconds=5,
                check_interval_seconds=30,
                metadata={"check_cpu": True, "check_memory": True, "check_disk": True}
            ),
            HealthCheck(
                check_id="redis_cache",
                name="Redis Cache",
                integration_type=IntegrationType.DATABASE,
                check_method="custom",
                timeout_seconds=5,
                check_interval_seconds=45,
                metadata={"optional": True}
            )
        ]
        
        for check in default_checks:
            self.register_health_check(check)
    
    async def start_monitoring(self):
        """Start health monitoring background tasks"""
        
        if self.monitor_task is not None:
            return
        
        logger.info("Starting integration health monitoring")
        
        # Load existing health checks from database
        await self._load_health_checks()
        
        # Start monitoring tasks
        self.monitor_task = asyncio.create_task(self._health_monitor_loop())
        self.metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self.alert_task = asyncio.create_task(self._alert_processing_loop())
        
        logger.info(f"Health monitoring started with {len(self.registered_checks)} checks")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        
        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None
        
        if self.metrics_task:
            self.metrics_task.cancel()
            self.metrics_task = None
        
        if self.alert_task:
            self.alert_task.cancel()
            self.alert_task = None
        
        logger.info("Health monitoring stopped")
    
    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check"""
        
        self.registered_checks[health_check.check_id] = health_check
        
        # Initialize check state
        self.check_states[health_check.check_id] = {
            "status": HealthStatus.UNKNOWN,
            "consecutive_failures": 0,
            "consecutive_successes": 0,
            "last_check": None,
            "next_check": datetime.utcnow()
        }
        
        # Store in database
        check_doc = asdict(health_check)
        check_doc["integration_type"] = health_check.integration_type.value
        check_doc["registered_at"] = datetime.utcnow()
        
        self.health_checks.replace_one(
            {"check_id": health_check.check_id},
            check_doc,
            upsert=True
        )
        
        logger.info(f"Registered health check: {health_check.name}")
    
    def unregister_health_check(self, check_id: str):
        """Unregister a health check"""
        
        if check_id in self.registered_checks:
            del self.registered_checks[check_id]
        
        if check_id in self.check_states:
            del self.check_states[check_id]
        
        if check_id in self.check_results:
            del self.check_results[check_id]
        
        # Remove from database
        self.health_checks.delete_one({"check_id": check_id})
        
        logger.info(f"Unregistered health check: {check_id}")
    
    async def _load_health_checks(self):
        """Load health checks from database"""
        
        try:
            stored_checks = list(self.health_checks.find({"enabled": True}))
            
            for check_doc in stored_checks:
                try:
                    health_check = HealthCheck(
                        check_id=check_doc["check_id"],
                        name=check_doc["name"],
                        integration_type=IntegrationType(check_doc["integration_type"]),
                        check_method=check_doc["check_method"],
                        endpoint=check_doc.get("endpoint"),
                        expected_status=check_doc.get("expected_status", 200),
                        timeout_seconds=check_doc.get("timeout_seconds", 10),
                        check_interval_seconds=check_doc.get("check_interval_seconds", 60),
                        failure_threshold=check_doc.get("failure_threshold", 3),
                        success_threshold=check_doc.get("success_threshold", 2),
                        enabled=check_doc.get("enabled", True),
                        metadata=check_doc.get("metadata", {})
                    )
                    
                    if health_check.check_id not in self.registered_checks:
                        self.register_health_check(health_check)
                        
                except Exception as e:
                    logger.error(f"Error loading health check {check_doc.get('check_id', 'unknown')}: {e}")
            
        except Exception as e:
            logger.error(f"Error loading health checks from database: {e}")
    
    async def _health_monitor_loop(self):
        """Main health monitoring loop"""
        
        logger.info("Started health monitor loop")
        
        while True:
            try:
                current_time = datetime.utcnow()
                checks_performed = 0
                
                for check_id, health_check in self.registered_checks.items():
                    if not health_check.enabled:
                        continue
                    
                    check_state = self.check_states[check_id]
                    
                    # Check if it's time to run this check
                    if current_time >= check_state["next_check"]:
                        try:
                            result = await self._perform_health_check(health_check)
                            await self._process_check_result(health_check, result)
                            checks_performed += 1
                            
                            # Schedule next check
                            check_state["next_check"] = current_time + timedelta(
                                seconds=health_check.check_interval_seconds
                            )
                            
                        except Exception as e:
                            logger.error(f"Error performing health check {check_id}: {e}")
                            
                            # Create error result
                            error_result = HealthResult(
                                check_id=check_id,
                                status=HealthStatus.CRITICAL,
                                response_time=0.0,
                                timestamp=current_time,
                                message="Health check execution failed",
                                error=str(e)
                            )
                            await self._process_check_result(health_check, error_result)
                
                # Update statistics
                if checks_performed > 0:
                    self.stats["checks_per_minute"] = (self.stats["checks_per_minute"] * 0.9) + (checks_performed * 0.1)
                
                # Sleep for a short interval before checking again
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor loop error: {e}")
                await asyncio.sleep(10)
        
        logger.info("Health monitor loop stopped")
    
    async def _perform_health_check(self, health_check: HealthCheck) -> HealthResult:
        """Perform a single health check"""
        
        start_time = time.time()
        
        try:
            if health_check.check_method == "http":
                result = await self._perform_http_check(health_check)
            elif health_check.check_method == "database":
                result = await self._perform_database_check(health_check)
            elif health_check.check_method == "custom":
                result = await self._perform_custom_check(health_check)
            else:
                raise ValueError(f"Unknown check method: {health_check.check_method}")
            
            result.response_time = time.time() - start_time
            return result
            
        except asyncio.TimeoutError:
            return HealthResult(
                check_id=health_check.check_id,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                message="Health check timeout",
                error="Request timed out"
            )
        except Exception as e:
            return HealthResult(
                check_id=health_check.check_id,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                timestamp=datetime.utcnow(),
                message="Health check failed",
                error=str(e)
            )
    
    async def _perform_http_check(self, health_check: HealthCheck) -> HealthResult:
        """Perform HTTP-based health check"""
        
        if not health_check.endpoint:
            raise ValueError("HTTP check requires endpoint")
        
        headers = {}
        
        # Add API key if required
        if health_check.metadata.get("api_key_required"):
            if "groq" in health_check.endpoint.lower():
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            elif "openai" in health_check.endpoint.lower():
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            elif "anthropic" in health_check.endpoint.lower():
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    headers["x-api-key"] = api_key
        
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.get(health_check.endpoint, headers=headers),
                timeout=health_check.timeout_seconds
            )
            
            if response.status_code == health_check.expected_status:
                status = HealthStatus.HEALTHY
                message = f"HTTP check successful ({response.status_code})"
            elif 200 <= response.status_code < 300:
                status = HealthStatus.HEALTHY
                message = f"HTTP check successful ({response.status_code})"
            elif 400 <= response.status_code < 500:
                status = HealthStatus.WARNING
                message = f"HTTP check returned client error ({response.status_code})"
            else:
                status = HealthStatus.CRITICAL
                message = f"HTTP check failed ({response.status_code})"
            
            return HealthResult(
                check_id=health_check.check_id,
                status=status,
                response_time=0.0,  # Will be set by caller
                timestamp=datetime.utcnow(),
                message=message,
                details={
                    "status_code": response.status_code,
                    "response_size": len(response.text),
                    "headers": dict(response.headers)
                }
            )
    
    async def _perform_database_check(self, health_check: HealthCheck) -> HealthResult:
        """Perform database health check"""
        
        try:
            if health_check.check_id == "mongodb_connection":
                # Test MongoDB connection
                await asyncio.wait_for(
                    self._test_mongodb_connection(),
                    timeout=health_check.timeout_seconds
                )
                
                return HealthResult(
                    check_id=health_check.check_id,
                    status=HealthStatus.HEALTHY,
                    response_time=0.0,
                    timestamp=datetime.utcnow(),
                    message="MongoDB connection successful",
                    details={"database": "aether_browser"}
                )
            
            elif health_check.check_id == "redis_cache":
                # Test Redis connection (optional)
                try:
                    import redis
                    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
                    redis_client.ping()
                    
                    return HealthResult(
                        check_id=health_check.check_id,
                        status=HealthStatus.HEALTHY,
                        response_time=0.0,
                        timestamp=datetime.utcnow(),
                        message="Redis connection successful"
                    )
                except Exception as e:
                    if health_check.metadata.get("optional"):
                        return HealthResult(
                            check_id=health_check.check_id,
                            status=HealthStatus.WARNING,
                            response_time=0.0,
                            timestamp=datetime.utcnow(),
                            message="Redis unavailable (using fallback)",
                            details={"fallback_active": True}
                        )
                    else:
                        raise e
            
            else:
                raise ValueError(f"Unknown database check: {health_check.check_id}")
                
        except Exception as e:
            return HealthResult(
                check_id=health_check.check_id,
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                timestamp=datetime.utcnow(),
                message="Database check failed",
                error=str(e)
            )
    
    async def _test_mongodb_connection(self):
        """Test MongoDB connection"""
        
        # Simple ping to test connection
        result = self.db.command("ping")
        if result.get("ok") != 1:
            raise Exception("MongoDB ping failed")
    
    async def _perform_custom_check(self, health_check: HealthCheck) -> HealthResult:
        """Perform custom health checks"""
        
        if health_check.check_id == "system_resources":
            return await self._check_system_resources(health_check)
        else:
            raise ValueError(f"Unknown custom check: {health_check.check_id}")
    
    async def _check_system_resources(self, health_check: HealthCheck) -> HealthResult:
        """Check system resource usage"""
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            warnings = []
            
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                warnings.append(f"CPU usage critical: {cpu_percent}%")
            elif cpu_percent > 80:
                status = HealthStatus.WARNING
                warnings.append(f"CPU usage high: {cpu_percent}%")
            
            if memory.percent > 95:
                status = HealthStatus.CRITICAL
                warnings.append(f"Memory usage critical: {memory.percent}%")
            elif memory.percent > 85:
                status = HealthStatus.WARNING
                warnings.append(f"Memory usage high: {memory.percent}%")
            
            if disk.percent > 95:
                status = HealthStatus.CRITICAL
                warnings.append(f"Disk usage critical: {disk.percent}%")
            elif disk.percent > 90:
                status = HealthStatus.WARNING
                warnings.append(f"Disk usage high: {disk.percent}%")
            
            message = "System resources normal"
            if warnings:
                message = "; ".join(warnings)
            
            return HealthResult(
                check_id=health_check.check_id,
                status=status,
                response_time=0.0,
                timestamp=datetime.utcnow(),
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            return HealthResult(
                check_id=health_check.check_id,
                status=HealthStatus.CRITICAL,
                response_time=0.0,
                timestamp=datetime.utcnow(),
                message="System resource check failed",
                error=str(e)
            )
    
    async def _process_check_result(self, health_check: HealthCheck, result: HealthResult):
        """Process health check result and update state"""
        
        check_state = self.check_states[health_check.check_id]
        check_state["last_check"] = result.timestamp
        
        # Store result
        self.check_results[health_check.check_id].append(result)
        
        # Store in database
        result_doc = asdict(result)
        result_doc["status"] = result.status.value
        self.health_results.insert_one(result_doc)
        
        # Update consecutive counters
        if result.status == HealthStatus.HEALTHY:
            check_state["consecutive_failures"] = 0
            check_state["consecutive_successes"] += 1
        else:
            check_state["consecutive_successes"] = 0
            check_state["consecutive_failures"] += 1
        
        # Determine overall status
        previous_status = check_state["status"]
        
        if (check_state["consecutive_successes"] >= health_check.success_threshold and
            check_state["status"] != HealthStatus.HEALTHY):
            check_state["status"] = HealthStatus.HEALTHY
        elif (check_state["consecutive_failures"] >= health_check.failure_threshold and
              result.status in [HealthStatus.CRITICAL, HealthStatus.DOWN]):
            check_state["status"] = result.status
        elif result.status == HealthStatus.WARNING:
            check_state["status"] = HealthStatus.WARNING
        
        # Check for status changes and generate alerts
        if previous_status != check_state["status"]:
            await self._generate_status_change_alert(health_check, previous_status, check_state["status"], result)
        
        # Update integration metrics
        self.integration_metrics[health_check.check_id].append({
            "timestamp": result.timestamp,
            "status": result.status.value,
            "response_time": result.response_time,
            "success": result.status == HealthStatus.HEALTHY
        })
        
        # Update overall statistics
        self._update_statistics()
    
    async def _generate_status_change_alert(self, health_check: HealthCheck, 
                                          old_status: HealthStatus, new_status: HealthStatus, 
                                          result: HealthResult):
        """Generate alert for status changes"""
        
        try:
            alert = {
                "alert_id": str(time.time()),
                "check_id": health_check.check_id,
                "check_name": health_check.name,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "timestamp": result.timestamp,
                "message": result.message,
                "severity": self._get_alert_severity(new_status),
                "resolved": new_status == HealthStatus.HEALTHY,
                "details": result.details or {}
            }
            
            # Store alert
            self.health_alerts.insert_one(alert)
            
            # Log status change
            logger.info(f"Health check {health_check.name} status changed: {old_status.value} -> {new_status.value}")
            
            if new_status in [HealthStatus.CRITICAL, HealthStatus.DOWN]:
                logger.error(f"CRITICAL: {health_check.name} is {new_status.value}: {result.message}")
            elif new_status == HealthStatus.WARNING:
                logger.warning(f"WARNING: {health_check.name} is {new_status.value}: {result.message}")
            elif new_status == HealthStatus.HEALTHY and old_status != HealthStatus.UNKNOWN:
                logger.info(f"RECOVERED: {health_check.name} is now healthy")
            
        except Exception as e:
            logger.error(f"Error generating alert: {e}")
    
    def _get_alert_severity(self, status: HealthStatus) -> str:
        """Get alert severity based on status"""
        
        if status == HealthStatus.DOWN:
            return "critical"
        elif status == HealthStatus.CRITICAL:
            return "high"
        elif status == HealthStatus.WARNING:
            return "medium"
        elif status == HealthStatus.HEALTHY:
            return "info"
        else:
            return "low"
    
    def _update_statistics(self):
        """Update overall health statistics"""
        
        total_checks = len(self.registered_checks)
        healthy_count = 0
        unhealthy_count = 0
        total_response_time = 0
        response_count = 0
        
        for check_id, check_state in self.check_states.items():
            if check_state["status"] == HealthStatus.HEALTHY:
                healthy_count += 1
            else:
                unhealthy_count += 1
        
        # Calculate average response time from recent results
        for check_id, results in self.check_results.items():
            recent_results = list(results)[-10:]  # Last 10 results
            for result in recent_results:
                total_response_time += result.response_time
                response_count += 1
        
        self.stats.update({
            "total_checks": total_checks,
            "healthy_integrations": healthy_count,
            "unhealthy_integrations": unhealthy_count,
            "average_response_time": total_response_time / response_count if response_count > 0 else 0.0,
            "uptime_percentage": (healthy_count / total_checks * 100) if total_checks > 0 else 100.0
        })
    
    async def _metrics_collection_loop(self):
        """Background metrics collection loop"""
        
        logger.info("Started metrics collection loop")
        
        while True:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute
                
                # Collect system metrics
                system_metric = {
                    "timestamp": datetime.utcnow(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                    "active_checks": len([s for s in self.check_states.values() 
                                        if s["status"] != HealthStatus.UNKNOWN])
                }
                
                self.system_metrics.append(system_metric)
                
                # Store metrics in database
                metric_doc = system_metric.copy()
                self.health_metrics.insert_one(metric_doc)
                
                # Clean up old metrics (keep last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.health_results.delete_many({"timestamp": {"$lt": cutoff_time}})
                self.health_metrics.delete_many({"timestamp": {"$lt": cutoff_time}})
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
        
        logger.info("Metrics collection loop stopped")
    
    async def _alert_processing_loop(self):
        """Background alert processing loop"""
        
        logger.info("Started alert processing loop")
        
        while True:
            try:
                await asyncio.sleep(30)  # Process alerts every 30 seconds
                
                # Process any pending alerts
                # This could include sending notifications, updating dashboards, etc.
                
                # Clean up old alerts (keep last 7 days)
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                self.health_alerts.delete_many({"timestamp": {"$lt": cutoff_time}})
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
        
        logger.info("Alert processing loop stopped")
    
    # Public API Methods
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        
        return {
            "overall_status": self._calculate_overall_status(),
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": self.stats,
            "active_checks": len(self.registered_checks),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_total_gb": psutil.disk_usage('/').total / (1024**3)
            }
        }
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system health status"""
        
        if not self.check_states:
            return HealthStatus.UNKNOWN.value
        
        statuses = [state["status"] for state in self.check_states.values()]
        
        if any(status == HealthStatus.DOWN for status in statuses):
            return HealthStatus.DOWN.value
        elif any(status == HealthStatus.CRITICAL for status in statuses):
            return HealthStatus.CRITICAL.value
        elif any(status == HealthStatus.WARNING for status in statuses):
            return HealthStatus.WARNING.value
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY.value
        else:
            return HealthStatus.UNKNOWN.value
    
    def get_integration_status(self, check_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific integration"""
        
        if check_id not in self.registered_checks:
            return None
        
        health_check = self.registered_checks[check_id]
        check_state = self.check_states[check_id]
        recent_results = list(self.check_results[check_id])[-5:]  # Last 5 results
        
        return {
            "check_id": check_id,
            "name": health_check.name,
            "status": check_state["status"].value,
            "last_check": check_state["last_check"].isoformat() if check_state["last_check"] else None,
            "consecutive_failures": check_state["consecutive_failures"],
            "consecutive_successes": check_state["consecutive_successes"],
            "recent_results": [
                {
                    "status": result.status.value,
                    "response_time": result.response_time,
                    "timestamp": result.timestamp.isoformat(),
                    "message": result.message
                } for result in recent_results
            ],
            "metadata": health_check.metadata
        }
    
    def get_all_integrations_status(self) -> List[Dict[str, Any]]:
        """Get status of all registered integrations"""
        
        return [
            self.get_integration_status(check_id) 
            for check_id in self.registered_checks.keys()
        ]
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent health alerts"""
        
        alerts = list(self.health_alerts.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(limit))
        
        # Convert datetime objects
        for alert in alerts:
            if alert.get("timestamp"):
                alert["timestamp"] = alert["timestamp"].isoformat()
        
        return alerts
    
    def get_health_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get health metrics for specified time period"""
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get system metrics
        system_metrics = list(self.health_metrics.find(
            {"timestamp": {"$gte": start_time}},
            {"_id": 0}
        ).sort("timestamp", 1))
        
        # Convert datetime objects
        for metric in system_metrics:
            if metric.get("timestamp"):
                metric["timestamp"] = metric["timestamp"].isoformat()
        
        # Get integration uptime
        integration_uptime = {}
        for check_id in self.registered_checks:
            results = list(self.health_results.find(
                {
                    "check_id": check_id,
                    "timestamp": {"$gte": start_time}
                },
                {"status": 1, "timestamp": 1, "_id": 0}
            ))
            
            if results:
                healthy_count = len([r for r in results if r["status"] == HealthStatus.HEALTHY.value])
                uptime_percentage = (healthy_count / len(results)) * 100
                integration_uptime[check_id] = {
                    "uptime_percentage": uptime_percentage,
                    "total_checks": len(results),
                    "healthy_checks": healthy_count
                }
        
        return {
            "time_period_hours": hours,
            "system_metrics": system_metrics,
            "integration_uptime": integration_uptime,
            "overall_statistics": self.stats
        }

# Global integration health monitor instance
integration_health_monitor = None  # Will be initialized in server.py