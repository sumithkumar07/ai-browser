"""
AETHER Real-time Analytics Dashboard
Advanced analytics and monitoring with live data visualization
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pymongo import MongoClient
from dataclasses import dataclass, asdict
import time
import psutil
import numpy as np
from collections import deque, defaultdict
import threading
from statistics import mean, median, mode

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: str
    metric_name: str
    condition: str  # 'greater_than', 'less_than', 'equals', 'threshold'
    threshold: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True

class MetricsCollector:
    """Real-time metrics collection system"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.metrics = self.db.realtime_metrics
        self.alerts = self.db.alert_history
        
        # In-memory storage for real-time data (last 1000 points per metric)
        self.live_data = defaultdict(lambda: deque(maxlen=1000))
        self.alert_rules = {}
        self.collection_active = True
        
        # Start background collection
        self.collection_thread = threading.Thread(target=self._start_collection_loop, daemon=True)
        self.collection_thread.start()
    
    def _start_collection_loop(self):
        """Start async collection loop in thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._collection_loop())
    
    async def _collection_loop(self):
        """Main metrics collection loop"""
        while self.collection_active:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._collect_user_metrics()
                await asyncio.sleep(5)  # Collect every 5 seconds
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)
    
    async def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            now = datetime.utcnow()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            await self._store_metric("system.cpu.usage", cpu_percent, now)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            await self._store_metric("system.memory.usage_percent", memory.percent, now)
            await self._store_metric("system.memory.available_gb", memory.available / (1024**3), now)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self._store_metric("system.disk.usage_percent", disk_percent, now)
            
            # Network metrics (simplified)
            net_io = psutil.net_io_counters()
            await self._store_metric("system.network.bytes_sent", net_io.bytes_sent, now)
            await self._store_metric("system.network.bytes_recv", net_io.bytes_recv, now)
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    async def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        try:
            now = datetime.utcnow()
            
            # Database metrics
            db_stats = self.db.command("dbStats")
            await self._store_metric("app.db.collections", db_stats.get("collections", 0), now)
            await self._store_metric("app.db.data_size_mb", db_stats.get("dataSize", 0) / (1024**2), now)
            
            # API metrics (from collections)
            recent_chats = self.db.chat_sessions.count_documents({
                "timestamp": {"$gte": now - timedelta(minutes=5)}
            })
            await self._store_metric("app.api.chat_requests_5min", recent_chats, now)
            
            recent_browse = self.db.recent_tabs.count_documents({
                "timestamp": {"$gte": now - timedelta(minutes=5)}
            })
            await self._store_metric("app.api.browse_requests_5min", recent_browse, now)
            
            # Automation metrics
            active_automations = self.db.workflow_executions.count_documents({
                "status": "running"
            })
            await self._store_metric("app.automation.active_workflows", active_automations, now)
            
            # Integration metrics
            recent_integrations = self.db.integration_logs.count_documents({
                "timestamp": {"$gte": now - timedelta(minutes=5)}
            })
            await self._store_metric("app.integrations.requests_5min", recent_integrations, now)
            
        except Exception as e:
            logger.error(f"Application metrics collection failed: {e}")
    
    async def _collect_user_metrics(self):
        """Collect user engagement metrics"""
        try:
            now = datetime.utcnow()
            
            # Active users (last 5 minutes)
            active_users = len(self.db.chat_sessions.distinct("session_id", {
                "timestamp": {"$gte": now - timedelta(minutes=5)}
            }))
            await self._store_metric("app.users.active_5min", active_users, now)
            
            # Active users (last hour)
            active_users_hour = len(self.db.chat_sessions.distinct("session_id", {
                "timestamp": {"$gte": now - timedelta(hours=1)}
            }))
            await self._store_metric("app.users.active_1hour", active_users_hour, now)
            
            # Total sessions today
            today_sessions = self.db.chat_sessions.count_documents({
                "timestamp": {"$gte": now.replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            await self._store_metric("app.users.sessions_today", today_sessions, now)
            
        except Exception as e:
            logger.error(f"User metrics collection failed: {e}")
    
    async def _store_metric(self, metric_name: str, value: float, timestamp: datetime):
        """Store metric in both live cache and database"""
        try:
            # Store in live cache
            metric_point = MetricPoint(timestamp, metric_name, value)
            self.live_data[metric_name].append(metric_point)
            
            # Store in database (with aggregation to reduce storage)
            metric_doc = {
                "metric_name": metric_name,
                "value": value,
                "timestamp": timestamp,
                "date": timestamp.date(),
                "hour": timestamp.hour,
                "minute": timestamp.minute
            }
            
            # Only store every minute to reduce database size
            if timestamp.second < 5:  # Store at beginning of collection cycle
                self.metrics.insert_one(metric_doc)
            
            # Check alert rules
            await self._check_alert_rules(metric_name, value, timestamp)
            
        except Exception as e:
            logger.error(f"Metric storage failed: {e}")
    
    async def _check_alert_rules(self, metric_name: str, value: float, timestamp: datetime):
        """Check alert rules for metric"""
        try:
            for rule in self.alert_rules.values():
                if rule.metric_name == metric_name and rule.enabled:
                    triggered = False
                    
                    if rule.condition == "greater_than" and value > rule.threshold:
                        triggered = True
                    elif rule.condition == "less_than" and value < rule.threshold:
                        triggered = True
                    elif rule.condition == "equals" and abs(value - rule.threshold) < 0.01:
                        triggered = True
                    
                    if triggered:
                        await self._trigger_alert(rule, value, timestamp)
                        
        except Exception as e:
            logger.error(f"Alert rule checking failed: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, value: float, timestamp: datetime):
        """Trigger alert"""
        try:
            alert_doc = {
                "alert_id": str(uuid.uuid4()),
                "rule_id": rule.rule_id,
                "metric_name": rule.metric_name,
                "triggered_value": value,
                "threshold": rule.threshold,
                "severity": rule.severity,
                "condition": rule.condition,
                "timestamp": timestamp,
                "acknowledged": False
            }
            
            self.alerts.insert_one(alert_doc)
            logger.warning(f"Alert triggered: {rule.metric_name} {rule.condition} {rule.threshold}, actual: {value}")
            
        except Exception as e:
            logger.error(f"Alert triggering failed: {e}")
    
    def get_live_metrics(self, metric_names: List[str] = None, minutes: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """Get live metrics from cache"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            result = {}
            
            metrics_to_fetch = metric_names or list(self.live_data.keys())
            
            for metric_name in metrics_to_fetch:
                if metric_name in self.live_data:
                    points = [
                        {
                            "timestamp": point.timestamp.isoformat(),
                            "value": point.value,
                            "metadata": point.metadata
                        }
                        for point in self.live_data[metric_name]
                        if point.timestamp >= cutoff_time
                    ]
                    result[metric_name] = points
            
            return result
            
        except Exception as e:
            logger.error(f"Live metrics retrieval failed: {e}")
            return {}
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.alert_rules[rule.rule_id] = rule
    
    def remove_alert_rule(self, rule_id: str):
        """Remove alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
    
    def stop_collection(self):
        """Stop metrics collection"""
        self.collection_active = False

class AnalyticsAggregator:
    """Analytics data aggregation and processing"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.metrics = self.db.realtime_metrics
    
    async def get_metric_summary(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get metric summary statistics"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Aggregate data from database
            pipeline = [
                {
                    "$match": {
                        "metric_name": metric_name,
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_value": {"$avg": "$value"},
                        "min_value": {"$min": "$value"},
                        "max_value": {"$max": "$value"},
                        "count": {"$sum": 1},
                        "latest_value": {"$last": "$value"}
                    }
                }
            ]
            
            result = list(self.metrics.aggregate(pipeline))
            
            if result:
                stats = result[0]
                return {
                    "metric_name": metric_name,
                    "period_hours": hours,
                    "average": round(stats["avg_value"], 2),
                    "minimum": round(stats["min_value"], 2),
                    "maximum": round(stats["max_value"], 2),
                    "latest": round(stats["latest_value"], 2),
                    "data_points": stats["count"]
                }
            else:
                return {"metric_name": metric_name, "error": "No data found"}
                
        except Exception as e:
            logger.error(f"Metric summary failed: {e}")
            return {"error": str(e)}
    
    async def get_trend_analysis(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze metric trends"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get hourly aggregations
            pipeline = [
                {
                    "$match": {
                        "metric_name": metric_name,
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"},
                            "hour": {"$hour": "$timestamp"}
                        },
                        "avg_value": {"$avg": "$value"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            hourly_data = list(self.metrics.aggregate(pipeline))
            
            if len(hourly_data) < 2:
                return {"error": "Insufficient data for trend analysis"}
            
            # Calculate trend
            values = [point["avg_value"] for point in hourly_data]
            
            # Simple linear trend calculation
            x = list(range(len(values)))
            if len(x) > 1:
                slope = np.polyfit(x, values, 1)[0]
                
                trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                trend_strength = abs(slope) / (max(values) - min(values)) if max(values) != min(values) else 0
                
                return {
                    "metric_name": metric_name,
                    "trend_direction": trend_direction,
                    "trend_strength": round(trend_strength, 3),
                    "slope": round(slope, 3),
                    "data_points": len(hourly_data),
                    "period_hours": hours
                }
            else:
                return {"error": "Insufficient data points"}
                
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {"error": str(e)}
    
    async def get_correlation_analysis(self, metric_names: List[str], hours: int = 24) -> Dict[str, Any]:
        """Analyze correlations between metrics"""
        try:
            if len(metric_names) < 2:
                return {"error": "Need at least 2 metrics for correlation"}
            
            start_time = datetime.utcnow() - timedelta(hours=hours)
            correlations = {}
            
            # Get data for all metrics
            metric_data = {}
            for metric_name in metric_names:
                data = list(self.metrics.find(
                    {
                        "metric_name": metric_name,
                        "timestamp": {"$gte": start_time}
                    },
                    {"value": 1, "timestamp": 1}
                ).sort("timestamp", 1))
                
                metric_data[metric_name] = data
            
            # Calculate pairwise correlations
            for i, metric1 in enumerate(metric_names):
                for metric2 in metric_names[i+1:]:
                    if metric1 in metric_data and metric2 in metric_data:
                        data1 = metric_data[metric1]
                        data2 = metric_data[metric2]
                        
                        # Align data by timestamp (simplified)
                        values1 = [point["value"] for point in data1]
                        values2 = [point["value"] for point in data2]
                        
                        if len(values1) > 1 and len(values2) > 1:
                            # Simple correlation calculation
                            min_len = min(len(values1), len(values2))
                            corr = np.corrcoef(values1[:min_len], values2[:min_len])[0, 1]
                            
                            if not np.isnan(corr):
                                correlations[f"{metric1}_{metric2}"] = round(corr, 3)
            
            return {
                "correlations": correlations,
                "period_hours": hours,
                "metrics_analyzed": metric_names
            }
            
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            return {"error": str(e)}

class DashboardManager:
    """Real-time dashboard management"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.dashboards = self.db.user_dashboards
        
        # Initialize metrics collector
        self.metrics_collector = MetricsCollector(mongo_client)
        self.analytics_aggregator = AnalyticsAggregator(mongo_client)
        
        # Setup default alert rules
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule("cpu_high", "system.cpu.usage", "greater_than", 80.0, "high"),
            AlertRule("memory_high", "system.memory.usage_percent", "greater_than", 85.0, "high"),
            AlertRule("disk_high", "system.disk.usage_percent", "greater_than", 90.0, "critical"),
            AlertRule("active_users_low", "app.users.active_1hour", "less_than", 1.0, "medium"),
        ]
        
        for rule in default_rules:
            self.metrics_collector.add_alert_rule(rule)
    
    async def get_dashboard_data(self, user_session: str, dashboard_type: str = "overview") -> Dict[str, Any]:
        """Get complete dashboard data"""
        try:
            if dashboard_type == "overview":
                return await self._get_overview_dashboard()
            elif dashboard_type == "system":
                return await self._get_system_dashboard()
            elif dashboard_type == "application":
                return await self._get_application_dashboard()
            elif dashboard_type == "users":
                return await self._get_users_dashboard()
            else:
                return {"error": "Unknown dashboard type"}
                
        except Exception as e:
            logger.error(f"Dashboard data retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _get_overview_dashboard(self) -> Dict[str, Any]:
        """Get overview dashboard data"""
        try:
            # Get key metrics
            live_metrics = self.metrics_collector.get_live_metrics([
                "system.cpu.usage",
                "system.memory.usage_percent",
                "app.users.active_1hour",
                "app.automation.active_workflows"
            ], minutes=60)
            
            # Get latest values
            kpis = {}
            for metric_name, points in live_metrics.items():
                if points:
                    latest_point = max(points, key=lambda p: p["timestamp"])
                    kpis[metric_name.split(".")[-1]] = latest_point["value"]
            
            # Get system health status
            health_status = "healthy"
            if kpis.get("cpu_usage", 0) > 80:
                health_status = "warning"
            if kpis.get("memory_usage_percent", 0) > 85:
                health_status = "critical"
            
            # Get recent alerts
            recent_alerts = list(self.db.alert_history.find(
                {"timestamp": {"$gte": datetime.utcnow() - timedelta(hours=24)}},
                {"_id": 0}
            ).sort("timestamp", -1).limit(5))
            
            return {
                "dashboard_type": "overview",
                "timestamp": datetime.utcnow().isoformat(),
                "kpis": kpis,
                "health_status": health_status,
                "live_metrics": live_metrics,
                "recent_alerts": recent_alerts,
                "active_users": kpis.get("active_1hour", 0),
                "active_workflows": kpis.get("active_workflows", 0)
            }
            
        except Exception as e:
            logger.error(f"Overview dashboard failed: {e}")
            return {"error": str(e)}
    
    async def _get_system_dashboard(self) -> Dict[str, Any]:
        """Get system performance dashboard"""
        try:
            system_metrics = [
                "system.cpu.usage",
                "system.memory.usage_percent",
                "system.disk.usage_percent",
                "system.network.bytes_sent",
                "system.network.bytes_recv"
            ]
            
            live_metrics = self.metrics_collector.get_live_metrics(system_metrics, minutes=120)
            
            # Get metric summaries
            summaries = {}
            for metric in system_metrics:
                summary = await self.analytics_aggregator.get_metric_summary(metric, hours=6)
                summaries[metric] = summary
            
            # Get trend analysis
            trends = {}
            for metric in system_metrics:
                trend = await self.analytics_aggregator.get_trend_analysis(metric, hours=6)
                trends[metric] = trend
            
            return {
                "dashboard_type": "system",
                "timestamp": datetime.utcnow().isoformat(),
                "live_metrics": live_metrics,
                "metric_summaries": summaries,
                "trend_analysis": trends
            }
            
        except Exception as e:
            logger.error(f"System dashboard failed: {e}")
            return {"error": str(e)}
    
    async def _get_application_dashboard(self) -> Dict[str, Any]:
        """Get application metrics dashboard"""
        try:
            app_metrics = [
                "app.api.chat_requests_5min",
                "app.api.browse_requests_5min",
                "app.automation.active_workflows",
                "app.integrations.requests_5min",
                "app.db.collections",
                "app.db.data_size_mb"
            ]
            
            live_metrics = self.metrics_collector.get_live_metrics(app_metrics, minutes=120)
            
            # Get API performance metrics
            api_performance = {}
            for metric in ["app.api.chat_requests_5min", "app.api.browse_requests_5min"]:
                summary = await self.analytics_aggregator.get_metric_summary(metric, hours=6)
                api_performance[metric] = summary
            
            # Get database metrics
            db_metrics = {}
            for metric in ["app.db.collections", "app.db.data_size_mb"]:
                summary = await self.analytics_aggregator.get_metric_summary(metric, hours=6)
                db_metrics[metric] = summary
            
            return {
                "dashboard_type": "application",
                "timestamp": datetime.utcnow().isoformat(),
                "live_metrics": live_metrics,
                "api_performance": api_performance,
                "database_metrics": db_metrics
            }
            
        except Exception as e:
            logger.error(f"Application dashboard failed: {e}")
            return {"error": str(e)}
    
    async def _get_users_dashboard(self) -> Dict[str, Any]:
        """Get user engagement dashboard"""
        try:
            user_metrics = [
                "app.users.active_5min",
                "app.users.active_1hour",
                "app.users.sessions_today"
            ]
            
            live_metrics = self.metrics_collector.get_live_metrics(user_metrics, minutes=240)
            
            # Get user engagement summaries
            engagement_summaries = {}
            for metric in user_metrics:
                summary = await self.analytics_aggregator.get_metric_summary(metric, hours=24)
                engagement_summaries[metric] = summary
            
            # Get user activity trends
            activity_trends = {}
            for metric in user_metrics:
                trend = await self.analytics_aggregator.get_trend_analysis(metric, hours=24)
                activity_trends[metric] = trend
            
            return {
                "dashboard_type": "users",
                "timestamp": datetime.utcnow().isoformat(),
                "live_metrics": live_metrics,
                "engagement_summaries": engagement_summaries,
                "activity_trends": activity_trends
            }
            
        except Exception as e:
            logger.error(f"Users dashboard failed: {e}")
            return {"error": str(e)}
    
    async def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metric data"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            data = list(self.db.realtime_metrics.find(
                {
                    "metric_name": metric_name,
                    "timestamp": {"$gte": start_time}
                },
                {"_id": 0, "value": 1, "timestamp": 1}
            ).sort("timestamp", 1))
            
            return [
                {
                    "timestamp": point["timestamp"].isoformat(),
                    "value": point["value"]
                }
                for point in data
            ]
            
        except Exception as e:
            logger.error(f"Metric history retrieval failed: {e}")
            return []
    
    async def create_custom_alert(self, user_session: str, alert_config: Dict[str, Any]) -> str:
        """Create custom alert rule"""
        try:
            rule_id = str(uuid.uuid4())
            
            rule = AlertRule(
                rule_id=rule_id,
                metric_name=alert_config["metric_name"],
                condition=alert_config["condition"],
                threshold=float(alert_config["threshold"]),
                severity=alert_config.get("severity", "medium"),
                enabled=alert_config.get("enabled", True)
            )
            
            self.metrics_collector.add_alert_rule(rule)
            
            # Store rule in database for persistence
            rule_doc = asdict(rule)
            rule_doc["user_session"] = user_session
            rule_doc["created_at"] = datetime.utcnow()
            
            self.db.alert_rules.insert_one(rule_doc)
            
            return rule_id
            
        except Exception as e:
            logger.error(f"Custom alert creation failed: {e}")
            return None
    
    async def get_alerts_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alerts summary"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get alert counts by severity
            pipeline = [
                {"$match": {"timestamp": {"$gte": start_time}}},
                {"$group": {
                    "_id": "$severity",
                    "count": {"$sum": 1}
                }}
            ]
            
            severity_counts = {item["_id"]: item["count"] for item in self.db.alert_history.aggregate(pipeline)}
            
            # Get recent alerts
            recent_alerts = list(self.db.alert_history.find(
                {"timestamp": {"$gte": start_time}},
                {"_id": 0}
            ).sort("timestamp", -1).limit(10))
            
            return {
                "period_hours": hours,
                "severity_counts": severity_counts,
                "recent_alerts": recent_alerts,
                "total_alerts": sum(severity_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Alerts summary failed: {e}")
            return {"error": str(e)}

# Initialize global instance
realtime_analytics_dashboard = None

def initialize_realtime_analytics_dashboard(mongo_client: MongoClient):
    """Initialize real-time analytics dashboard"""
    global realtime_analytics_dashboard
    realtime_analytics_dashboard = DashboardManager(mongo_client)
    return realtime_analytics_dashboard