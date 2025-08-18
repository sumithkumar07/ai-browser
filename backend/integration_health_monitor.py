# Phase 4: Integration Health Monitoring System
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
import uuid
import httpx
import statistics
from enum import Enum

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"

class IntegrationHealthMonitor:
    """
    Phase 4: Advanced Integration Health Monitoring System
    Monitors health and performance of all integrations
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.monitoring_tasks = {}
        self.health_checks = {}
        self.alert_thresholds = self._initialize_alert_thresholds()
        
    async def start_monitoring(self, integration_id: str, monitoring_config: Dict[str, Any] = None) -> bool:
        """Start monitoring an integration"""
        try:
            if integration_id in self.monitoring_tasks:
                await self.stop_monitoring(integration_id)
            
            # Get integration details
            integration = self.db.custom_integrations.find_one({"integration_id": integration_id})
            if not integration and not self.db.integration_auth.find_one({"integration": integration_id}):
                logger.error(f"Integration {integration_id} not found")
                return False
            
            # Create monitoring configuration
            config = monitoring_config or self._get_default_monitoring_config()
            
            # Initialize health check record
            health_record = {
                "integration_id": integration_id,
                "monitoring_started": datetime.utcnow(),
                "status": HealthStatus.HEALTHY.value,
                "last_check": None,
                "check_interval": config.get("check_interval", 300),  # 5 minutes default
                "consecutive_failures": 0,
                "total_checks": 0,
                "successful_checks": 0,
                "average_response_time": 0.0,
                "uptime_percentage": 100.0,
                "alerts_sent": 0,
                "config": config
            }
            
            self.db.integration_health.insert_one(health_record)
            
            # Start monitoring task
            task = asyncio.create_task(self._monitor_integration_loop(integration_id, config))
            self.monitoring_tasks[integration_id] = task
            
            logger.info(f"Started monitoring integration: {integration_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start monitoring for {integration_id}: {e}")
            return False
    
    async def stop_monitoring(self, integration_id: str) -> bool:
        """Stop monitoring an integration"""
        try:
            if integration_id in self.monitoring_tasks:
                self.monitoring_tasks[integration_id].cancel()
                del self.monitoring_tasks[integration_id]
            
            # Update health record
            self.db.integration_health.update_one(
                {"integration_id": integration_id},
                {
                    "$set": {
                        "monitoring_stopped": datetime.utcnow(),
                        "status": "monitoring_disabled"
                    }
                }
            )
            
            logger.info(f"Stopped monitoring integration: {integration_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop monitoring for {integration_id}: {e}")
            return False
    
    async def _monitor_integration_loop(self, integration_id: str, config: Dict[str, Any]) -> None:
        """Main monitoring loop for an integration"""
        
        check_interval = config.get("check_interval", 300)
        
        while True:
            try:
                # Perform health check
                health_result = await self._perform_health_check(integration_id, config)
                
                # Update health record
                await self._update_health_record(integration_id, health_result)
                
                # Check for alerts
                await self._check_and_send_alerts(integration_id, health_result)
                
                # Store detailed metrics
                await self._store_health_metrics(integration_id, health_result)
                
                # Wait for next check
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check failed for {integration_id}: {e}")
                await asyncio.sleep(check_interval)
    
    async def _perform_health_check(self, integration_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        health_result = {
            "integration_id": integration_id,
            "check_timestamp": datetime.utcnow(),
            "status": HealthStatus.HEALTHY.value,
            "response_time": 0.0,
            "success": False,
            "checks_performed": [],
            "issues_detected": [],
            "metrics": {}
        }
        
        try:
            # Get integration details
            integration = await self._get_integration_details(integration_id)
            if not integration:
                health_result["status"] = HealthStatus.CRITICAL.value
                health_result["issues_detected"].append("Integration configuration not found")
                return health_result
            
            # Perform different types of health checks
            checks = config.get("health_checks", ["connectivity", "response_time", "authentication"])
            
            for check_type in checks:
                check_result = await self._perform_specific_check(integration, check_type)
                health_result["checks_performed"].append(check_result)
                
                if not check_result["success"]:
                    health_result["issues_detected"].append(check_result["issue"])
            
            # Determine overall status
            health_result["status"] = self._determine_overall_status(health_result["checks_performed"])
            health_result["success"] = health_result["status"] in [HealthStatus.HEALTHY.value, HealthStatus.WARNING.value]
            
            # Calculate metrics
            health_result["metrics"] = self._calculate_health_metrics(health_result["checks_performed"])
            health_result["response_time"] = health_result["metrics"].get("average_response_time", 0.0)
            
        except Exception as e:
            health_result["status"] = HealthStatus.CRITICAL.value
            health_result["issues_detected"].append(f"Health check exception: {str(e)}")
        
        return health_result
    
    async def _perform_specific_check(self, integration: Dict[str, Any], check_type: str) -> Dict[str, Any]:
        """Perform specific type of health check"""
        
        check_result = {
            "check_type": check_type,
            "success": False,
            "response_time": 0.0,
            "issue": None,
            "details": {}
        }
        
        try:
            if check_type == "connectivity":
                check_result = await self._check_connectivity(integration)
            elif check_type == "response_time":
                check_result = await self._check_response_time(integration)
            elif check_type == "authentication":
                check_result = await self._check_authentication(integration)
            elif check_type == "endpoints":
                check_result = await self._check_endpoints(integration)
            elif check_type == "rate_limits":
                check_result = await self._check_rate_limits(integration)
            else:
                check_result["issue"] = f"Unknown check type: {check_type}"
        
        except Exception as e:
            check_result["issue"] = f"Check failed: {str(e)}"
        
        return check_result
    
    async def _check_connectivity(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Check basic connectivity to integration"""
        
        start_time = datetime.utcnow()
        
        try:
            # Get base URL or endpoint to test
            base_url = integration.get("base_url") or integration.get("config", {}).get("base_url", "")
            
            if not base_url:
                return {
                    "check_type": "connectivity",
                    "success": False,
                    "issue": "No base URL configured for connectivity check"
                }
            
            # Simple connectivity check
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(base_url)
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "check_type": "connectivity",
                    "success": response.status_code < 500,
                    "response_time": response_time,
                    "issue": None if response.status_code < 500 else f"Server error: {response.status_code}",
                    "details": {
                        "status_code": response.status_code,
                        "response_time_ms": response_time * 1000
                    }
                }
        
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            return {
                "check_type": "connectivity",
                "success": False,
                "response_time": response_time,
                "issue": f"Connectivity failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_response_time(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Check response time performance"""
        
        try:
            # Get test endpoint
            endpoints = integration.get("config", {}).get("endpoints", [])
            if not endpoints:
                return {
                    "check_type": "response_time",
                    "success": False,
                    "issue": "No endpoints configured for response time check"
                }
            
            # Test first GET endpoint
            test_endpoint = None
            for endpoint in endpoints:
                if endpoint.get("method", "").upper() == "GET":
                    test_endpoint = endpoint
                    break
            
            if not test_endpoint:
                return {
                    "check_type": "response_time",
                    "success": True,  # Not critical if no GET endpoints
                    "issue": "No GET endpoints available for response time testing",
                    "response_time": 0.0
                }
            
            # Perform response time test
            start_time = datetime.utcnow()
            
            base_url = integration.get("config", {}).get("base_url", "")
            url = f"{base_url.rstrip('/')}/{test_endpoint['url'].lstrip('/')}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Check if response time is acceptable (< 5 seconds)
                is_acceptable = response_time < 5.0
                
                return {
                    "check_type": "response_time",
                    "success": is_acceptable,
                    "response_time": response_time,
                    "issue": None if is_acceptable else f"Slow response time: {response_time:.2f}s",
                    "details": {
                        "response_time_ms": response_time * 1000,
                        "endpoint_tested": test_endpoint["url"],
                        "threshold_ms": 5000
                    }
                }
        
        except Exception as e:
            return {
                "check_type": "response_time",
                "success": False,
                "response_time": 0.0,
                "issue": f"Response time check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_authentication(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Check authentication functionality"""
        
        try:
            auth_config = integration.get("config", {}).get("authentication", {})
            if not auth_config:
                return {
                    "check_type": "authentication",
                    "success": True,  # No auth to check
                    "issue": None,
                    "details": {"auth_type": "none"}
                }
            
            auth_type = auth_config.get("type", "")
            
            # Check if credentials are available
            integration_auth = self.db.integration_auth.find_one({
                "integration": integration.get("integration_id", "")
            })
            
            if not integration_auth and auth_type != "none":
                return {
                    "check_type": "authentication",
                    "success": False,
                    "issue": "No authentication credentials configured",
                    "details": {"auth_type": auth_type}
                }
            
            # For now, just verify credentials exist
            # In production, this would test actual authentication
            return {
                "check_type": "authentication",
                "success": True,
                "issue": None,
                "details": {
                    "auth_type": auth_type,
                    "credentials_present": bool(integration_auth)
                }
            }
        
        except Exception as e:
            return {
                "check_type": "authentication",
                "success": False,
                "issue": f"Authentication check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_endpoints(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Check all endpoints availability"""
        
        try:
            endpoints = integration.get("config", {}).get("endpoints", [])
            if not endpoints:
                return {
                    "check_type": "endpoints",
                    "success": True,
                    "issue": None,
                    "details": {"total_endpoints": 0}
                }
            
            base_url = integration.get("config", {}).get("base_url", "")
            
            endpoint_results = []
            successful_endpoints = 0
            
            for endpoint in endpoints:
                try:
                    url = f"{base_url.rstrip('/')}/{endpoint['url'].lstrip('/')}"
                    method = endpoint.get("method", "GET").upper()
                    
                    # Only test GET endpoints for health check
                    if method == "GET":
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            response = await client.get(url)
                            
                            success = response.status_code < 500
                            if success:
                                successful_endpoints += 1
                            
                            endpoint_results.append({
                                "endpoint": endpoint["name"],
                                "url": endpoint["url"],
                                "method": method,
                                "status_code": response.status_code,
                                "success": success
                            })
                    else:
                        # Skip non-GET endpoints
                        endpoint_results.append({
                            "endpoint": endpoint["name"],
                            "url": endpoint["url"],
                            "method": method,
                            "status": "skipped",
                            "reason": "Non-GET endpoint"
                        })
                
                except Exception as e:
                    endpoint_results.append({
                        "endpoint": endpoint["name"],
                        "url": endpoint.get("url", ""),
                        "error": str(e),
                        "success": False
                    })
            
            get_endpoints = [e for e in endpoints if e.get("method", "GET").upper() == "GET"]
            success_rate = successful_endpoints / len(get_endpoints) if get_endpoints else 1.0
            
            return {
                "check_type": "endpoints",
                "success": success_rate >= 0.8,  # 80% success rate threshold
                "issue": None if success_rate >= 0.8 else f"Low endpoint success rate: {success_rate:.1%}",
                "details": {
                    "total_endpoints": len(endpoints),
                    "testable_endpoints": len(get_endpoints),
                    "successful_endpoints": successful_endpoints,
                    "success_rate": success_rate,
                    "endpoint_results": endpoint_results
                }
            }
        
        except Exception as e:
            return {
                "check_type": "endpoints",
                "success": False,
                "issue": f"Endpoint check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    async def _check_rate_limits(self, integration: Dict[str, Any]) -> Dict[str, Any]:
        """Check rate limit status"""
        
        try:
            # Get recent API calls for this integration
            recent_calls = list(self.db.integration_usage.find({
                "integration_id": integration.get("integration_id", ""),
                "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=1)}
            }))
            
            # Calculate current usage rate
            calls_per_hour = len(recent_calls)
            
            # Get rate limit configuration (if any)
            rate_limit_config = integration.get("config", {}).get("rate_limits", {})
            max_calls_per_hour = rate_limit_config.get("calls_per_hour", 1000)  # Default limit
            
            usage_percentage = (calls_per_hour / max_calls_per_hour) * 100
            
            # Check if approaching rate limit
            is_healthy = usage_percentage < 80  # Warning at 80%
            
            return {
                "check_type": "rate_limits",
                "success": is_healthy,
                "issue": None if is_healthy else f"High API usage: {usage_percentage:.1f}% of rate limit",
                "details": {
                    "calls_last_hour": calls_per_hour,
                    "rate_limit": max_calls_per_hour,
                    "usage_percentage": usage_percentage,
                    "remaining_calls": max(0, max_calls_per_hour - calls_per_hour)
                }
            }
        
        except Exception as e:
            return {
                "check_type": "rate_limits",
                "success": True,  # Non-critical check
                "issue": f"Rate limit check failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _determine_overall_status(self, checks: List[Dict[str, Any]]) -> str:
        """Determine overall health status from individual checks"""
        
        if not checks:
            return HealthStatus.CRITICAL.value
        
        critical_failures = 0
        warning_issues = 0
        total_checks = len(checks)
        
        for check in checks:
            if not check["success"]:
                if check["check_type"] in ["connectivity", "authentication"]:
                    critical_failures += 1
                else:
                    warning_issues += 1
        
        # Determine status based on failures
        if critical_failures > 0:
            return HealthStatus.CRITICAL.value
        elif warning_issues > total_checks * 0.5:  # More than 50% warnings
            return HealthStatus.WARNING.value
        elif warning_issues > 0:
            return HealthStatus.WARNING.value
        else:
            return HealthStatus.HEALTHY.value
    
    def _calculate_health_metrics(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate health metrics from check results"""
        
        metrics = {
            "total_checks": len(checks),
            "successful_checks": 0,
            "failed_checks": 0,
            "average_response_time": 0.0,
            "success_rate": 0.0
        }
        
        if not checks:
            return metrics
        
        response_times = []
        
        for check in checks:
            if check["success"]:
                metrics["successful_checks"] += 1
            else:
                metrics["failed_checks"] += 1
            
            response_time = check.get("response_time", 0.0)
            if response_time > 0:
                response_times.append(response_time)
        
        metrics["success_rate"] = metrics["successful_checks"] / metrics["total_checks"]
        
        if response_times:
            metrics["average_response_time"] = statistics.mean(response_times)
            metrics["max_response_time"] = max(response_times)
            metrics["min_response_time"] = min(response_times)
        
        return metrics
    
    async def _update_health_record(self, integration_id: str, health_result: Dict[str, Any]) -> None:
        """Update integration health record"""
        
        try:
            current_record = self.db.integration_health.find_one({"integration_id": integration_id})
            
            if not current_record:
                logger.warning(f"No health record found for integration {integration_id}")
                return
            
            # Calculate updated metrics
            total_checks = current_record.get("total_checks", 0) + 1
            successful_checks = current_record.get("successful_checks", 0)
            
            if health_result["success"]:
                successful_checks += 1
                consecutive_failures = 0
            else:
                consecutive_failures = current_record.get("consecutive_failures", 0) + 1
            
            # Calculate uptime percentage
            uptime_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 100
            
            # Update average response time
            current_avg_rt = current_record.get("average_response_time", 0.0)
            new_response_time = health_result.get("response_time", 0.0)
            
            if current_avg_rt == 0:
                updated_avg_rt = new_response_time
            else:
                # Rolling average
                updated_avg_rt = ((current_avg_rt * (total_checks - 1)) + new_response_time) / total_checks
            
            # Update record
            update_data = {
                "status": health_result["status"],
                "last_check": health_result["check_timestamp"],
                "consecutive_failures": consecutive_failures,
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "average_response_time": updated_avg_rt,
                "uptime_percentage": uptime_percentage,
                "last_issues": health_result.get("issues_detected", []),
                "last_metrics": health_result.get("metrics", {})
            }
            
            self.db.integration_health.update_one(
                {"integration_id": integration_id},
                {"$set": update_data}
            )
        
        except Exception as e:
            logger.error(f"Failed to update health record for {integration_id}: {e}")
    
    async def _store_health_metrics(self, integration_id: str, health_result: Dict[str, Any]) -> None:
        """Store detailed health metrics for analytics"""
        
        try:
            metrics_record = {
                "integration_id": integration_id,
                "timestamp": health_result["check_timestamp"],
                "status": health_result["status"],
                "response_time": health_result.get("response_time", 0.0),
                "success": health_result["success"],
                "checks_performed": health_result["checks_performed"],
                "issues_detected": health_result["issues_detected"],
                "metrics": health_result.get("metrics", {}),
                "ttl": datetime.utcnow() + timedelta(days=30)  # Auto-expire after 30 days
            }
            
            self.db.integration_health_metrics.insert_one(metrics_record)
        
        except Exception as e:
            logger.error(f"Failed to store health metrics for {integration_id}: {e}")
    
    async def _check_and_send_alerts(self, integration_id: str, health_result: Dict[str, Any]) -> None:
        """Check if alerts should be sent and send them"""
        
        try:
            health_record = self.db.integration_health.find_one({"integration_id": integration_id})
            if not health_record:
                return
            
            status = health_result["status"]
            consecutive_failures = health_record.get("consecutive_failures", 0)
            
            # Determine if alert should be sent
            should_alert = False
            alert_level = "info"
            alert_message = ""
            
            if status == HealthStatus.CRITICAL.value:
                should_alert = True
                alert_level = "critical"
                alert_message = f"Integration {integration_id} is in CRITICAL state"
            
            elif status == HealthStatus.DOWN.value:
                should_alert = True
                alert_level = "critical"
                alert_message = f"Integration {integration_id} is DOWN"
            
            elif consecutive_failures >= self.alert_thresholds["consecutive_failures"]:
                should_alert = True
                alert_level = "warning"
                alert_message = f"Integration {integration_id} has {consecutive_failures} consecutive failures"
            
            elif health_record.get("uptime_percentage", 100) < self.alert_thresholds["uptime_threshold"]:
                should_alert = True
                alert_level = "warning"
                alert_message = f"Integration {integration_id} uptime is below threshold: {health_record.get('uptime_percentage', 0):.1f}%"
            
            if should_alert:
                await self._send_health_alert(integration_id, alert_level, alert_message, health_result)
        
        except Exception as e:
            logger.error(f"Alert checking failed for {integration_id}: {e}")
    
    async def _send_health_alert(self, integration_id: str, level: str, message: str, health_result: Dict[str, Any]) -> None:
        """Send health alert"""
        
        try:
            alert_record = {
                "alert_id": str(uuid.uuid4()),
                "integration_id": integration_id,
                "level": level,
                "message": message,
                "timestamp": datetime.utcnow(),
                "health_result": health_result,
                "acknowledged": False
            }
            
            self.db.integration_alerts.insert_one(alert_record)
            
            # Update alerts sent counter
            self.db.integration_health.update_one(
                {"integration_id": integration_id},
                {"$inc": {"alerts_sent": 1}}
            )
            
            logger.warning(f"Health alert sent for {integration_id}: {message}")
        
        except Exception as e:
            logger.error(f"Failed to send alert for {integration_id}: {e}")
    
    async def get_integration_health_status(self, integration_id: str) -> Dict[str, Any]:
        """Get current health status for an integration"""
        
        try:
            health_record = self.db.integration_health.find_one(
                {"integration_id": integration_id},
                {"_id": 0}
            )
            
            if not health_record:
                return {
                    "success": False,
                    "error": "No health monitoring data found"
                }
            
            # Get recent metrics
            recent_metrics = list(self.db.integration_health_metrics.find({
                "integration_id": integration_id,
                "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}
            }).sort("timestamp", -1).limit(24))
            
            # Get recent alerts
            recent_alerts = list(self.db.integration_alerts.find({
                "integration_id": integration_id,
                "timestamp": {"$gte": datetime.utcnow() - timedelta(days=7)}
            }, {"_id": 0}).sort("timestamp", -1).limit(10))
            
            return {
                "success": True,
                "health_status": health_record,
                "recent_metrics": recent_metrics,
                "recent_alerts": recent_alerts,
                "is_monitoring": integration_id in self.monitoring_tasks
            }
        
        except Exception as e:
            logger.error(f"Failed to get health status for {integration_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_health_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for all monitored integrations"""
        
        try:
            # Get all health records
            health_records = list(self.db.integration_health.find({}, {"_id": 0}))
            
            # Calculate overall statistics
            total_integrations = len(health_records)
            healthy_count = len([r for r in health_records if r.get("status") == HealthStatus.HEALTHY.value])
            warning_count = len([r for r in health_records if r.get("status") == HealthStatus.WARNING.value])
            critical_count = len([r for r in health_records if r.get("status") == HealthStatus.CRITICAL.value])
            down_count = len([r for r in health_records if r.get("status") == HealthStatus.DOWN.value])
            
            # Calculate overall uptime
            uptimes = [r.get("uptime_percentage", 100) for r in health_records if r.get("uptime_percentage") is not None]
            overall_uptime = statistics.mean(uptimes) if uptimes else 100.0
            
            # Get recent alerts
            recent_alerts = list(self.db.integration_alerts.find({
                "timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)},
                "acknowledged": False
            }, {"_id": 0}).sort("timestamp", -1).limit(20))
            
            return {
                "success": True,
                "dashboard_data": {
                    "overview": {
                        "total_integrations": total_integrations,
                        "healthy": healthy_count,
                        "warning": warning_count,
                        "critical": critical_count,
                        "down": down_count,
                        "overall_uptime": overall_uptime,
                        "monitoring_active": len(self.monitoring_tasks)
                    },
                    "integrations": health_records,
                    "recent_alerts": recent_alerts,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        
        try:
            result = self.db.integration_alerts.update_one(
                {"alert_id": alert_id},
                {
                    "$set": {
                        "acknowledged": True,
                        "acknowledged_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    async def _get_integration_details(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Get integration details for health checking"""
        
        # Check custom integrations first
        integration = self.db.custom_integrations.find_one({"integration_id": integration_id})
        if integration:
            return integration
        
        # Check standard integrations
        auth_record = self.db.integration_auth.find_one({"integration": integration_id})
        if auth_record:
            # For standard integrations, we need to construct the details
            return {
                "integration_id": integration_id,
                "type": "standard",
                "config": {
                    "base_url": self._get_standard_integration_base_url(integration_id),
                    "endpoints": self._get_standard_integration_endpoints(integration_id),
                    "authentication": {"type": "configured"}
                }
            }
        
        return None
    
    def _get_standard_integration_base_url(self, integration_id: str) -> str:
        """Get base URL for standard integrations"""
        
        standard_urls = {
            "github": "https://api.github.com",
            "slack": "https://slack.com/api",
            "google": "https://www.googleapis.com",
            "twitter": "https://api.twitter.com",
            "linkedin": "https://api.linkedin.com"
        }
        
        return standard_urls.get(integration_id.lower(), "")
    
    def _get_standard_integration_endpoints(self, integration_id: str) -> List[Dict[str, Any]]:
        """Get endpoints for standard integrations"""
        
        standard_endpoints = {
            "github": [
                {"name": "user", "method": "GET", "url": "/user"},
                {"name": "repos", "method": "GET", "url": "/user/repos"}
            ],
            "slack": [
                {"name": "auth_test", "method": "GET", "url": "/auth.test"}
            ],
            "google": [
                {"name": "userinfo", "method": "GET", "url": "/oauth2/v2/userinfo"}
            ]
        }
        
        return standard_endpoints.get(integration_id.lower(), [])
    
    def _get_default_monitoring_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration"""
        
        return {
            "check_interval": 300,  # 5 minutes
            "health_checks": [
                "connectivity",
                "response_time", 
                "authentication",
                "endpoints"
            ],
            "alert_on_failure": True,
            "alert_thresholds": {
                "consecutive_failures": 3,
                "response_time_ms": 5000,
                "uptime_percentage": 95.0
            }
        }
    
    def _initialize_alert_thresholds(self) -> Dict[str, Any]:
        """Initialize alert thresholds"""
        
        return {
            "consecutive_failures": 3,
            "response_time_threshold": 5.0,  # seconds
            "uptime_threshold": 95.0,  # percentage
            "alert_cooldown": 1800  # 30 minutes between similar alerts
        }

# Global instance
integration_health_monitor = None

def initialize_integration_health_monitor(mongo_client: MongoClient):
    global integration_health_monitor
    integration_health_monitor = IntegrationHealthMonitor(mongo_client)
    return integration_health_monitor