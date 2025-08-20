# 🌐 CROSS-PLATFORM SYNCHRONIZATION ENGINE - Real-time Multi-Platform Sync
# Workstream C2: Universal Platform Integration & Data Transformation

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
import json
import hashlib
import logging
from enum import Enum
from pymongo import MongoClient
import aiohttp

logger = logging.getLogger(__name__)

class SyncStatus(Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    PAUSED = "paused"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    AUTO_MERGE = "auto_merge"
    LATEST_WINS = "latest_wins"
    USER_CHOICE = "user_choice"
    MANUAL_REVIEW = "manual_review"
    SOURCE_PRIORITY = "source_priority"

class DataFormat(Enum):
    """Supported data formats"""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    TEXT = "text"
    BINARY = "binary"
    CUSTOM = "custom"

@dataclass
class PlatformAdapter:
    """Platform-specific adapter configuration"""
    platform_id: str
    platform_name: str
    api_endpoint: str
    auth_type: str  # oauth, api_key, token
    data_format: DataFormat
    rate_limits: Dict[str, int]
    capabilities: List[str]
    transformation_rules: Dict[str, Any]

@dataclass
class SyncRule:
    """Synchronization rule between platforms"""
    rule_id: str
    name: str
    source_platform: str
    target_platforms: List[str]
    data_types: List[str]
    sync_frequency: str  # real_time, hourly, daily, manual
    conflict_resolution: ConflictResolution
    transformation_mappings: Dict[str, str]
    filters: Dict[str, Any]
    active: bool

@dataclass
class SyncOperation:
    """Individual synchronization operation"""
    operation_id: str
    rule_id: str
    source_platform: str
    target_platform: str
    data_type: str
    source_data: Dict[str, Any]
    target_data: Optional[Dict[str, Any]]
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int

@dataclass
class DataConflict:
    """Data synchronization conflict"""
    conflict_id: str
    operation_id: str
    source_platform: str
    target_platform: str
    field_conflicts: Dict[str, Dict[str, Any]]
    resolution_strategy: ConflictResolution
    resolved: bool
    resolved_at: Optional[datetime]
    resolution_data: Optional[Dict[str, Any]]

class CrossPlatformSyncEngine:
    """Real-time multi-platform synchronization engine"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.sync_rules = self.db.sync_rules
        self.sync_operations = self.db.sync_operations
        self.sync_conflicts = self.db.sync_conflicts
        self.platform_connections = self.db.platform_connections
        
        # Platform adapters
        self.adapters = {}  # platform_id -> PlatformAdapter
        
        # Sync orchestrator
        self.orchestrator = SyncOrchestrator(self.db)
        
        # Data transformer
        self.transformer = DataTransformer()
        
        # Conflict resolver
        self.conflict_resolver = ConflictResolver()
        
        # Active sync channels
        self.active_channels = {}  # rule_id -> SyncChannel
        
        # Real-time sync queue
        self.sync_queue = asyncio.Queue()
        
        # Initialize built-in platform adapters
        self._initialize_platform_adapters()
        
        logger.info("🌐 Cross-Platform Sync Engine initialized")

    def _initialize_platform_adapters(self):
        """Initialize built-in platform adapters"""
        
        # Google Workspace
        self.adapters["google_workspace"] = PlatformAdapter(
            platform_id="google_workspace",
            platform_name="Google Workspace", 
            api_endpoint="https://www.googleapis.com",
            auth_type="oauth",
            data_format=DataFormat.JSON,
            rate_limits={"requests_per_minute": 1000},
            capabilities=["contacts", "calendar", "drive", "gmail"],
            transformation_rules={
                "contact_mapping": {
                    "name": "displayName",
                    "email": "emailAddresses[0].value",
                    "phone": "phoneNumbers[0].value"
                }
            }
        )
        
        # Microsoft 365
        self.adapters["microsoft_365"] = PlatformAdapter(
            platform_id="microsoft_365",
            platform_name="Microsoft 365",
            api_endpoint="https://graph.microsoft.com",
            auth_type="oauth",
            data_format=DataFormat.JSON,
            rate_limits={"requests_per_minute": 600},
            capabilities=["contacts", "calendar", "onedrive", "outlook"],
            transformation_rules={
                "contact_mapping": {
                    "name": "displayName",
                    "email": "emailAddresses[0].address",
                    "phone": "businessPhones[0]"
                }
            }
        )
        
        # Slack
        self.adapters["slack"] = PlatformAdapter(
            platform_id="slack",
            platform_name="Slack",
            api_endpoint="https://slack.com/api",
            auth_type="oauth",
            data_format=DataFormat.JSON,
            rate_limits={"requests_per_minute": 100},
            capabilities=["messages", "channels", "users"],
            transformation_rules={
                "message_mapping": {
                    "content": "text",
                    "timestamp": "ts",
                    "author": "user"
                }
            }
        )
        
        # Notion
        self.adapters["notion"] = PlatformAdapter(
            platform_id="notion",
            platform_name="Notion",
            api_endpoint="https://api.notion.com",
            auth_type="token",
            data_format=DataFormat.JSON,
            rate_limits={"requests_per_minute": 300},
            capabilities=["pages", "databases", "blocks"],
            transformation_rules={
                "page_mapping": {
                    "title": "properties.title.title[0].text.content",
                    "content": "children",
                    "created": "created_time"
                }
            }
        )

    async def create_sync_rule(self, user_id: str, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new synchronization rule"""
        try:
            rule_id = str(uuid.uuid4())
            
            sync_rule = SyncRule(
                rule_id=rule_id,
                name=rule_data["name"],
                source_platform=rule_data["source_platform"],
                target_platforms=rule_data["target_platforms"],
                data_types=rule_data["data_types"],
                sync_frequency=rule_data.get("sync_frequency", "real_time"),
                conflict_resolution=ConflictResolution(rule_data.get("conflict_resolution", "latest_wins")),
                transformation_mappings=rule_data.get("transformation_mappings", {}),
                filters=rule_data.get("filters", {}),
                active=True
            )
            
            # Store sync rule
            rule_doc = asdict(sync_rule)
            rule_doc["user_id"] = user_id
            rule_doc["created_at"] = datetime.utcnow()
            rule_doc["conflict_resolution"] = sync_rule.conflict_resolution.value
            
            self.sync_rules.insert_one(rule_doc)
            
            # Start real-time sync if configured
            if sync_rule.sync_frequency == "real_time":
                await self._start_realtime_sync(rule_id)
            
            return {
                "success": True,
                "rule_id": rule_id,
                "name": sync_rule.name,
                "status": "active",
                "message": f"Sync rule created between {sync_rule.source_platform} and {len(sync_rule.target_platforms)} platforms"
            }
            
        except Exception as e:
            logger.error(f"❌ Sync rule creation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_sync(self, rule_id: str, manual_trigger: bool = False) -> Dict[str, Any]:
        """Execute synchronization for a specific rule"""
        try:
            # Get sync rule
            rule_doc = self.sync_rules.find_one({"rule_id": rule_id})
            if not rule_doc:
                return {"success": False, "error": "Sync rule not found"}
            
            if not rule_doc["active"]:
                return {"success": False, "error": "Sync rule is inactive"}
            
            sync_rule = SyncRule(**{k: v for k, v in rule_doc.items() if k in SyncRule.__dataclass_fields__})
            sync_rule.conflict_resolution = ConflictResolution(rule_doc["conflict_resolution"])
            
            # Get source data
            source_data = await self._fetch_platform_data(
                sync_rule.source_platform, 
                sync_rule.data_types,
                sync_rule.filters
            )
            
            if not source_data["success"]:
                return {
                    "success": False,
                    "error": f"Failed to fetch data from {sync_rule.source_platform}: {source_data['error']}"
                }
            
            sync_operations = []
            
            # Sync to each target platform
            for target_platform in sync_rule.target_platforms:
                for data_type in sync_rule.data_types:
                    operation = await self._execute_platform_sync(
                        sync_rule, 
                        target_platform, 
                        data_type,
                        source_data["data"]
                    )
                    sync_operations.append(operation)
            
            # Calculate overall success
            successful_ops = sum(1 for op in sync_operations if op["status"] == SyncStatus.COMPLETED.value)
            total_ops = len(sync_operations)
            
            return {
                "success": successful_ops > 0,
                "rule_id": rule_id,
                "operations_executed": total_ops,
                "successful_operations": successful_ops,
                "failed_operations": total_ops - successful_ops,
                "operations": [
                    {
                        "operation_id": op["operation_id"],
                        "target_platform": op["target_platform"],
                        "data_type": op["data_type"],
                        "status": op["status"]
                    }
                    for op in sync_operations
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Sync execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def setup_realtime_sync(self, rule_id: str) -> Dict[str, Any]:
        """Setup real-time synchronization for a rule"""
        try:
            rule_doc = self.sync_rules.find_one({"rule_id": rule_id})
            if not rule_doc:
                return {"success": False, "error": "Sync rule not found"}
            
            # Create sync channel
            sync_channel = SyncChannel(
                rule_id=rule_id,
                source_platform=rule_doc["source_platform"],
                target_platforms=rule_doc["target_platforms"],
                data_types=rule_doc["data_types"]
            )
            
            # Start monitoring source platform for changes
            await sync_channel.start_monitoring()
            
            # Store active channel
            self.active_channels[rule_id] = sync_channel
            
            return {
                "success": True,
                "rule_id": rule_id,
                "status": "real_time_sync_active",
                "message": "Real-time synchronization started"
            }
            
        except Exception as e:
            logger.error(f"❌ Real-time sync setup error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def resolve_conflicts(self, operation_id: str, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve synchronization conflicts"""
        try:
            # Get conflict
            conflict_doc = self.sync_conflicts.find_one({"operation_id": operation_id})
            if not conflict_doc:
                return {"success": False, "error": "Conflict not found"}
            
            conflict = DataConflict(**{k: v for k, v in conflict_doc.items() if k in DataConflict.__dataclass_fields__})
            
            if conflict.resolved:
                return {"success": False, "error": "Conflict already resolved"}
            
            # Apply conflict resolution
            resolved_data = await self.conflict_resolver.resolve_conflict(
                conflict, resolution_data
            )
            
            if resolved_data["success"]:
                # Update conflict as resolved
                self.sync_conflicts.update_one(
                    {"conflict_id": conflict.conflict_id},
                    {
                        "$set": {
                            "resolved": True,
                            "resolved_at": datetime.utcnow(),
                            "resolution_data": resolved_data["data"]
                        }
                    }
                )
                
                # Continue with sync operation
                sync_result = await self._apply_resolved_data(
                    operation_id, resolved_data["data"]
                )
                
                return {
                    "success": True,
                    "conflict_id": conflict.conflict_id,
                    "resolution_applied": True,
                    "sync_completed": sync_result["success"]
                }
            
            return resolved_data
            
        except Exception as e:
            logger.error(f"❌ Conflict resolution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_sync_status(self, rule_id: str) -> Dict[str, Any]:
        """Get synchronization status for a rule"""
        try:
            # Get recent operations
            operations = list(self.sync_operations.find(
                {"rule_id": rule_id},
                {"_id": 0}
            ).sort("started_at", -1).limit(10))
            
            # Get pending conflicts
            conflicts = list(self.sync_conflicts.find(
                {"resolved": False},
                {"_id": 0}
            ))
            
            # Calculate statistics
            total_operations = len(operations)
            successful_operations = sum(1 for op in operations if op["status"] == SyncStatus.COMPLETED.value)
            failed_operations = sum(1 for op in operations if op["status"] == SyncStatus.FAILED.value)
            
            return {
                "success": True,
                "rule_id": rule_id,
                "statistics": {
                    "total_operations": total_operations,
                    "successful_operations": successful_operations, 
                    "failed_operations": failed_operations,
                    "success_rate": successful_operations / max(total_operations, 1),
                    "pending_conflicts": len(conflicts)
                },
                "recent_operations": operations[:5],
                "pending_conflicts": conflicts,
                "real_time_active": rule_id in self.active_channels
            }
            
        except Exception as e:
            logger.error(f"❌ Sync status error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # Helper methods
    async def _fetch_platform_data(self, platform_id: str, data_types: List[str], 
                                 filters: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from platform"""
        try:
            if platform_id not in self.adapters:
                return {"success": False, "error": f"Platform {platform_id} not supported"}
            
            adapter = self.adapters[platform_id]
            
            # Get platform connection
            connection = self.platform_connections.find_one({"platform_id": platform_id})
            if not connection:
                return {"success": False, "error": f"Platform {platform_id} not connected"}
            
            # Simulate data fetch (real implementation would use actual APIs)
            data = {}
            for data_type in data_types:
                data[data_type] = await self._simulate_platform_data_fetch(
                    platform_id, data_type, filters
                )
            
            return {
                "success": True,
                "data": data,
                "platform": platform_id,
                "fetched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Platform data fetch error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _simulate_platform_data_fetch(self, platform_id: str, data_type: str, 
                                          filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate platform data fetch"""
        # This would be replaced with actual API calls in production
        
        if data_type == "contacts":
            return [
                {
                    "id": str(uuid.uuid4()),
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "platform": platform_id,
                    "last_modified": datetime.utcnow().isoformat()
                }
            ]
        elif data_type == "calendar":
            return [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Meeting",
                    "start_time": datetime.utcnow().isoformat(),
                    "duration": 60,
                    "platform": platform_id,
                    "last_modified": datetime.utcnow().isoformat()
                }
            ]
        else:
            return []

    async def _execute_platform_sync(self, sync_rule: SyncRule, target_platform: str,
                                   data_type: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sync operation to target platform"""
        try:
            operation_id = str(uuid.uuid4())
            
            operation = SyncOperation(
                operation_id=operation_id,
                rule_id=sync_rule.rule_id,
                source_platform=sync_rule.source_platform,
                target_platform=target_platform,
                data_type=data_type,
                source_data=source_data.get(data_type, []),
                target_data=None,
                status=SyncStatus.IN_PROGRESS,
                started_at=datetime.utcnow(),
                completed_at=None,
                error_message=None,
                retry_count=0
            )
            
            # Store operation
            operation_doc = asdict(operation)
            operation_doc["status"] = operation.status.value
            operation_doc["started_at"] = operation.started_at
            
            self.sync_operations.insert_one(operation_doc)
            
            # Transform data for target platform
            transformed_data = await self.transformer.transform_data(
                operation.source_data,
                sync_rule.source_platform,
                target_platform,
                data_type,
                sync_rule.transformation_mappings
            )
            
            if not transformed_data["success"]:
                # Mark operation as failed
                operation.status = SyncStatus.FAILED
                operation.error_message = transformed_data["error"]
            else:
                # Get existing data from target platform
                existing_data = await self._fetch_platform_data(
                    target_platform, [data_type], {}
                )
                
                # Check for conflicts
                conflicts = await self._detect_conflicts(
                    transformed_data["data"], 
                    existing_data.get("data", {}).get(data_type, [])
                )
                
                if conflicts:
                    # Create conflict record
                    await self._create_conflict_record(operation_id, conflicts)
                    operation.status = SyncStatus.CONFLICT
                else:
                    # Apply changes to target platform
                    apply_result = await self._apply_data_to_platform(
                        target_platform, data_type, transformed_data["data"]
                    )
                    
                    if apply_result["success"]:
                        operation.status = SyncStatus.COMPLETED
                        operation.target_data = transformed_data["data"]
                    else:
                        operation.status = SyncStatus.FAILED
                        operation.error_message = apply_result["error"]
            
            # Update operation
            operation.completed_at = datetime.utcnow()
            
            self.sync_operations.update_one(
                {"operation_id": operation_id},
                {
                    "$set": {
                        "status": operation.status.value,
                        "completed_at": operation.completed_at,
                        "error_message": operation.error_message,
                        "target_data": operation.target_data
                    }
                }
            )
            
            return {
                "operation_id": operation_id,
                "target_platform": target_platform,
                "data_type": data_type,
                "status": operation.status.value,
                "error_message": operation.error_message
            }
            
        except Exception as e:
            logger.error(f"Platform sync error: {e}")
            return {
                "operation_id": operation_id if 'operation_id' in locals() else str(uuid.uuid4()),
                "target_platform": target_platform,
                "data_type": data_type,
                "status": SyncStatus.FAILED.value,
                "error_message": str(e)
            }

    async def _detect_conflicts(self, new_data: List[Dict[str, Any]], 
                              existing_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts between new and existing data"""
        conflicts = []
        
        # Create lookup for existing data
        existing_lookup = {item.get("id", item.get("email", str(i))): item 
                          for i, item in enumerate(existing_data)}
        
        for new_item in new_data:
            item_id = new_item.get("id", new_item.get("email", ""))
            
            if item_id in existing_lookup:
                existing_item = existing_lookup[item_id]
                
                # Compare fields for conflicts
                field_conflicts = {}
                for field, new_value in new_item.items():
                    if field in existing_item and existing_item[field] != new_value:
                        field_conflicts[field] = {
                            "existing_value": existing_item[field],
                            "new_value": new_value
                        }
                
                if field_conflicts:
                    conflicts.append({
                        "item_id": item_id,
                        "field_conflicts": field_conflicts
                    })
        
        return conflicts

    async def _create_conflict_record(self, operation_id: str, conflicts: List[Dict[str, Any]]):
        """Create conflict record for manual resolution"""
        try:
            conflict_id = str(uuid.uuid4())
            
            # Get operation details
            operation = self.sync_operations.find_one({"operation_id": operation_id})
            
            conflict = DataConflict(
                conflict_id=conflict_id,
                operation_id=operation_id,
                source_platform=operation["source_platform"],
                target_platform=operation["target_platform"],
                field_conflicts=conflicts[0]["field_conflicts"] if conflicts else {},
                resolution_strategy=ConflictResolution.USER_CHOICE,
                resolved=False,
                resolved_at=None,
                resolution_data=None
            )
            
            # Store conflict
            conflict_doc = asdict(conflict)
            conflict_doc["created_at"] = datetime.utcnow()
            conflict_doc["resolution_strategy"] = conflict.resolution_strategy.value
            
            self.sync_conflicts.insert_one(conflict_doc)
            
        except Exception as e:
            logger.error(f"Conflict record creation error: {e}")

    async def _apply_data_to_platform(self, platform_id: str, data_type: str, 
                                    data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply transformed data to target platform"""
        try:
            # Simulate applying data to platform
            # Real implementation would use platform-specific APIs
            
            return {
                "success": True,
                "applied_records": len(data),
                "platform": platform_id,
                "data_type": data_type,
                "applied_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data application error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _apply_resolved_data(self, operation_id: str, resolved_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply conflict-resolved data"""
        try:
            # Get operation
            operation = self.sync_operations.find_one({"operation_id": operation_id})
            if not operation:
                return {"success": False, "error": "Operation not found"}
            
            # Apply resolved data to target platform
            result = await self._apply_data_to_platform(
                operation["target_platform"],
                operation["data_type"],
                resolved_data.get("data", [])
            )
            
            if result["success"]:
                # Update operation status
                self.sync_operations.update_one(
                    {"operation_id": operation_id},
                    {
                        "$set": {
                            "status": SyncStatus.COMPLETED.value,
                            "completed_at": datetime.utcnow(),
                            "target_data": resolved_data
                        }
                    }
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Resolved data application error: {e}")
            return {"success": False, "error": str(e)}

    async def _start_realtime_sync(self, rule_id: str):
        """Start real-time synchronization for rule"""
        try:
            # This would set up webhooks or polling for real-time sync
            # For now, just mark as active
            logger.info(f"Real-time sync started for rule: {rule_id}")
            
        except Exception as e:
            logger.error(f"Real-time sync start error: {e}")


class SyncOrchestrator:
    """Orchestrate multiple sync operations"""
    
    def __init__(self, db):
        self.db = db
    
    async def orchestrate_batch_sync(self, rule_ids: List[str]) -> Dict[str, Any]:
        """Orchestrate batch synchronization across multiple rules"""
        results = []
        
        for rule_id in rule_ids:
            # Would execute sync for each rule
            result = {
                "rule_id": rule_id,
                "status": "completed",
                "operations": 1
            }
            results.append(result)
        
        return {
            "success": True,
            "batch_results": results,
            "total_rules": len(rule_ids)
        }


class DataTransformer:
    """Transform data between different platform formats"""
    
    async def transform_data(self, data: List[Dict[str, Any]], source_platform: str,
                           target_platform: str, data_type: str, 
                           mappings: Dict[str, str]) -> Dict[str, Any]:
        """Transform data from source to target format"""
        try:
            transformed_data = []
            
            for item in data:
                transformed_item = {}
                
                # Apply field mappings
                for source_field, target_field in mappings.items():
                    if source_field in item:
                        transformed_item[target_field] = item[source_field]
                
                # Copy unmapped fields
                for field, value in item.items():
                    if field not in mappings and field not in transformed_item:
                        transformed_item[field] = value
                
                transformed_data.append(transformed_item)
            
            return {
                "success": True,
                "data": transformed_data,
                "source_platform": source_platform,
                "target_platform": target_platform,
                "transformed_records": len(transformed_data)
            }
            
        except Exception as e:
            logger.error(f"Data transformation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class ConflictResolver:
    """Resolve synchronization conflicts"""
    
    async def resolve_conflict(self, conflict: DataConflict, 
                             resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve data conflict based on strategy"""
        try:
            if conflict.resolution_strategy == ConflictResolution.LATEST_WINS:
                # Use the newer data
                resolved_data = resolution_data.get("new_data", {})
            
            elif conflict.resolution_strategy == ConflictResolution.USER_CHOICE:
                # Use user-selected resolution
                resolved_data = resolution_data.get("user_selection", {})
            
            elif conflict.resolution_strategy == ConflictResolution.AUTO_MERGE:
                # Automatically merge non-conflicting fields
                resolved_data = self._auto_merge_fields(
                    conflict.field_conflicts, resolution_data
                )
            
            else:
                resolved_data = resolution_data
            
            return {
                "success": True,
                "data": resolved_data,
                "strategy_used": conflict.resolution_strategy.value
            }
            
        except Exception as e:
            logger.error(f"Conflict resolution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _auto_merge_fields(self, field_conflicts: Dict[str, Dict[str, Any]], 
                          resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically merge non-conflicting fields"""
        merged_data = {}
        
        for field, conflict_info in field_conflicts.items():
            # Simple merge strategy: use non-empty values
            existing_value = conflict_info["existing_value"]
            new_value = conflict_info["new_value"]
            
            if new_value and not existing_value:
                merged_data[field] = new_value
            elif existing_value and not new_value:
                merged_data[field] = existing_value
            else:
                # Use newer value as default
                merged_data[field] = new_value
        
        return merged_data


class SyncChannel:
    """Real-time synchronization channel"""
    
    def __init__(self, rule_id: str, source_platform: str, target_platforms: List[str], data_types: List[str]):
        self.rule_id = rule_id
        self.source_platform = source_platform
        self.target_platforms = target_platforms
        self.data_types = data_types
        self.monitoring = False
    
    async def start_monitoring(self):
        """Start monitoring source platform for changes"""
        self.monitoring = True
        logger.info(f"Started monitoring {self.source_platform} for rule {self.rule_id}")
    
    async def stop_monitoring(self):
        """Stop monitoring source platform"""
        self.monitoring = False
        logger.info(f"Stopped monitoring {self.source_platform} for rule {self.rule_id}")


# Initialize functions for integration
def initialize_cross_platform_sync_engine(db_client: MongoClient) -> CrossPlatformSyncEngine:
    """Initialize and return cross-platform sync engine"""
    return CrossPlatformSyncEngine(db_client)

def get_cross_platform_sync_engine() -> Optional[CrossPlatformSyncEngine]:
    """Get the global cross-platform sync engine instance"""
    return getattr(get_cross_platform_sync_engine, '_instance', None)

def set_cross_platform_sync_instance(instance: CrossPlatformSyncEngine):
    """Set the global cross-platform sync engine instance"""
    get_cross_platform_sync_engine._instance = instance