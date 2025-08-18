import asyncio
import uuid
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import logging
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class VirtualWorkspaceType(Enum):
    BACKGROUND_PROCESSING = "background_processing"
    AUTOMATION_RUNNER = "automation_runner"
    DATA_PROCESSOR = "data_processor"
    MONITORING = "monitoring"
    INTEGRATION_SYNC = "integration_sync"
    SCHEDULED_TASKS = "scheduled_tasks"
    RESEARCH_AGENT = "research_agent"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class VirtualTask:
    """Represents a task running in virtual workspace"""
    id: str
    user_session: str
    workspace_id: str
    task_type: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    config: Dict[str, Any] = None
    result: Dict[str, Any] = None
    error_message: str = None
    progress: float = 0.0
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    estimated_duration: int = 0  # seconds
    actual_duration: int = 0
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.result is None:
            self.result = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class VirtualWorkspace:
    """Virtual workspace for background processing"""
    id: str
    user_session: str
    name: str
    workspace_type: VirtualWorkspaceType
    description: str = ""
    is_active: bool = True
    max_concurrent_tasks: int = 5
    resource_limits: Dict[str, Any] = None
    settings: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                "max_memory_mb": 512,
                "max_cpu_percent": 25,
                "max_execution_time": 3600  # 1 hour
            }
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class VirtualWorkspaceManager:
    """Advanced virtual workspace manager for background processing and automation"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        
        # Collections
        self.virtual_workspaces = self.db.virtual_workspaces
        self.virtual_tasks = self.db.virtual_tasks
        self.task_results = self.db.task_results
        self.resource_usage = self.db.resource_usage
        
        # Runtime state
        self.active_workspaces = {}  # workspace_id -> workspace_context
        self.running_tasks = {}      # task_id -> task_context
        self.task_queues = {}        # workspace_id -> task_queue
        
        # Resource management
        self.thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="virtual_ws")
        self.resource_monitor = ResourceMonitor()
        
        # Task handlers
        self.task_handlers = self._initialize_task_handlers()
        
        # Background management
        self._manager_task = None
        self._resource_monitor_task = None
        
    def start_virtual_workspace_manager(self):
        """Start the virtual workspace management system"""
        if self._manager_task is None:
            try:
                self._manager_task = asyncio.create_task(self._background_management())
                self._resource_monitor_task = asyncio.create_task(self._background_resource_monitoring())
                logger.info("Virtual Workspace Manager started")
            except RuntimeError:
                pass
    
    def _initialize_task_handlers(self) -> Dict[str, Callable]:
        """Initialize task handlers for different task types"""
        return {
            "web_scraping": self._handle_web_scraping_task,
            "data_processing": self._handle_data_processing_task,
            "automation_workflow": self._handle_automation_workflow_task,
            "integration_sync": self._handle_integration_sync_task,
            "scheduled_action": self._handle_scheduled_action_task,
            "monitoring": self._handle_monitoring_task,
            "research": self._handle_research_task,
            "file_processing": self._handle_file_processing_task,
            "ai_analysis": self._handle_ai_analysis_task,
            "notification": self._handle_notification_task
        }
    
    # Virtual Workspace Management
    
    async def create_virtual_workspace(self, user_session: str, name: str, 
                                     workspace_type: VirtualWorkspaceType, **kwargs) -> str:
        """Create a new virtual workspace"""
        
        workspace_id = str(uuid.uuid4())
        
        workspace = VirtualWorkspace(
            id=workspace_id,
            user_session=user_session,
            name=name,
            workspace_type=workspace_type,
            description=kwargs.get('description', ''),
            max_concurrent_tasks=kwargs.get('max_concurrent_tasks', 5),
            resource_limits=kwargs.get('resource_limits'),
            settings=kwargs.get('settings', {})
        )
        
        # Store in database
        workspace_doc = asdict(workspace)
        workspace_doc['workspace_type'] = workspace.workspace_type.value
        
        self.virtual_workspaces.insert_one(workspace_doc)
        
        # Initialize runtime state
        self.active_workspaces[workspace_id] = {
            "workspace": workspace,
            "active_tasks": [],
            "resource_usage": {"memory_mb": 0, "cpu_percent": 0}
        }
        
        self.task_queues[workspace_id] = asyncio.Queue()
        
        logger.info(f"Created virtual workspace {workspace_id}: {name}")
        return workspace_id
    
    async def get_virtual_workspaces(self, user_session: str) -> List[Dict[str, Any]]:
        """Get all virtual workspaces for a user"""
        
        workspaces = list(self.virtual_workspaces.find(
            {"user_session": user_session},
            {"_id": 0}
        ).sort("updated_at", -1))
        
        # Add runtime information
        for workspace in workspaces:
            workspace_id = workspace["id"]
            
            # Convert timestamps
            for time_field in ["created_at", "updated_at"]:
                if workspace.get(time_field):
                    workspace[time_field] = workspace[time_field].isoformat()
            
            # Add task counts
            active_tasks = self.virtual_tasks.count_documents({
                "workspace_id": workspace_id,
                "status": {"$in": [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]}
            })
            
            completed_tasks = self.virtual_tasks.count_documents({
                "workspace_id": workspace_id,
                "status": TaskStatus.COMPLETED.value
            })
            
            workspace["active_tasks"] = active_tasks
            workspace["completed_tasks"] = completed_tasks
            
            # Add resource usage if workspace is active
            if workspace_id in self.active_workspaces:
                workspace["resource_usage"] = self.active_workspaces[workspace_id]["resource_usage"]
        
        return workspaces
    
    async def get_virtual_workspace_details(self, user_session: str, workspace_id: str) -> Dict[str, Any]:
        """Get detailed virtual workspace information"""
        
        workspace = self.virtual_workspaces.find_one(
            {"id": workspace_id, "user_session": user_session},
            {"_id": 0}
        )
        
        if not workspace:
            raise ValueError(f"Virtual workspace {workspace_id} not found")
        
        # Convert timestamps
        for time_field in ["created_at", "updated_at"]:
            if workspace.get(time_field):
                workspace[time_field] = workspace[time_field].isoformat()
        
        # Get tasks
        tasks = await self.get_workspace_tasks(user_session, workspace_id)
        
        # Get resource usage history
        resource_history = await self.get_workspace_resource_history(user_session, workspace_id)
        
        return {
            **workspace,
            "tasks": tasks,
            "resource_history": resource_history
        }
    
    # Task Management
    
    async def create_virtual_task(self, user_session: str, workspace_id: str, 
                                task_type: str, name: str, config: Dict[str, Any], **kwargs) -> str:
        """Create a new virtual task"""
        
        task_id = str(uuid.uuid4())
        
        task = VirtualTask(
            id=task_id,
            user_session=user_session,
            workspace_id=workspace_id,
            task_type=task_type,
            name=name,
            description=kwargs.get('description', ''),
            priority=kwargs.get('priority', TaskPriority.MEDIUM),
            config=config,
            estimated_duration=kwargs.get('estimated_duration', 300),  # 5 minutes default
            max_retries=kwargs.get('max_retries', 3)
        )
        
        # Store in database
        task_doc = asdict(task)
        task_doc['status'] = task.status.value
        task_doc['priority'] = task.priority.value
        
        self.virtual_tasks.insert_one(task_doc)
        
        # Add to task queue
        if workspace_id in self.task_queues:
            await self.task_queues[workspace_id].put(task_id)
        
        logger.info(f"Created virtual task {task_id}: {name} in workspace {workspace_id}")
        return task_id
    
    async def get_workspace_tasks(self, user_session: str, workspace_id: str, 
                                 status_filter: List[str] = None) -> List[Dict[str, Any]]:
        """Get tasks in a virtual workspace"""
        
        query = {"user_session": user_session, "workspace_id": workspace_id}
        
        if status_filter:
            query["status"] = {"$in": status_filter}
        
        tasks = list(self.virtual_tasks.find(query, {"_id": 0}).sort("created_at", -1))
        
        # Convert timestamps
        for task in tasks:
            for time_field in ["created_at", "started_at", "completed_at"]:
                if task.get(time_field):
                    task[time_field] = task[time_field].isoformat()
        
        return tasks
    
    async def get_task_status(self, user_session: str, task_id: str) -> Dict[str, Any]:
        """Get detailed task status"""
        
        task = self.virtual_tasks.find_one(
            {"id": task_id, "user_session": user_session},
            {"_id": 0}
        )
        
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Convert timestamps
        for time_field in ["created_at", "started_at", "completed_at"]:
            if task.get(time_field):
                task[time_field] = task[time_field].isoformat()
        
        # Add runtime information if task is running
        if task_id in self.running_tasks:
            runtime_info = self.running_tasks[task_id]
            task["runtime_info"] = {
                "current_step": runtime_info.get("current_step", ""),
                "resource_usage": runtime_info.get("resource_usage", {}),
                "live_progress": runtime_info.get("progress", task["progress"])
            }
        
        return task
    
    async def cancel_task(self, user_session: str, task_id: str) -> bool:
        """Cancel a running or pending task"""
        
        # Update task status
        result = self.virtual_tasks.update_one(
            {
                "id": task_id,
                "user_session": user_session,
                "status": {"$in": [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]}
            },
            {
                "$set": {
                    "status": TaskStatus.CANCELLED.value,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count > 0:
            # Cancel runtime task if running
            if task_id in self.running_tasks:
                self.running_tasks[task_id]["cancelled"] = True
            
            logger.info(f"Cancelled task {task_id}")
            return True
        
        return False
    
    # Task Execution System
    
    async def _background_management(self):
        """Background task management and execution"""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                # Process task queues for all active workspaces
                for workspace_id in list(self.task_queues.keys()):
                    await self._process_workspace_queue(workspace_id)
                
                # Clean up completed tasks
                await self._cleanup_completed_tasks()
                
            except Exception as e:
                logger.error(f"Virtual workspace management error: {e}")
    
    async def _process_workspace_queue(self, workspace_id: str):
        """Process task queue for a specific workspace"""
        
        if workspace_id not in self.active_workspaces:
            return
        
        workspace_context = self.active_workspaces[workspace_id]
        workspace = workspace_context["workspace"]
        
        # Check if we can run more tasks
        current_active = len(workspace_context["active_tasks"])
        
        if current_active >= workspace.max_concurrent_tasks:
            return
        
        # Get pending tasks from queue
        queue = self.task_queues[workspace_id]
        
        try:
            # Non-blocking queue check
            if not queue.empty():
                task_id = await asyncio.wait_for(queue.get(), timeout=0.1)
                
                # Start task execution
                asyncio.create_task(self._execute_task(workspace_id, task_id))
        
        except asyncio.TimeoutError:
            pass  # No tasks in queue
        except Exception as e:
            logger.error(f"Error processing queue for workspace {workspace_id}: {e}")
    
    async def _execute_task(self, workspace_id: str, task_id: str):
        """Execute a virtual task"""
        
        try:
            # Get task details
            task = self.virtual_tasks.find_one({"id": task_id})
            if not task:
                return
            
            # Update task status to running
            self.virtual_tasks.update_one(
                {"id": task_id},
                {
                    "$set": {
                        "status": TaskStatus.RUNNING.value,
                        "started_at": datetime.utcnow()
                    }
                }
            )
            
            # Add to active tasks
            if workspace_id in self.active_workspaces:
                self.active_workspaces[workspace_id]["active_tasks"].append(task_id)
            
            # Initialize runtime context
            self.running_tasks[task_id] = {
                "workspace_id": workspace_id,
                "started_at": datetime.utcnow(),
                "progress": 0.0,
                "current_step": "initializing",
                "resource_usage": {"memory_mb": 0, "cpu_percent": 0},
                "cancelled": False
            }
            
            logger.info(f"Starting task execution: {task_id}")
            
            # Get task handler
            task_type = task["task_type"]
            handler = self.task_handlers.get(task_type)
            
            if not handler:
                raise ValueError(f"No handler for task type: {task_type}")
            
            # Execute task
            result = await handler(task_id, task["config"])
            
            # Update task with result
            self.virtual_tasks.update_one(
                {"id": task_id},
                {
                    "$set": {
                        "status": TaskStatus.COMPLETED.value,
                        "result": result,
                        "progress": 100.0,
                        "completed_at": datetime.utcnow(),
                        "actual_duration": (datetime.utcnow() - self.running_tasks[task_id]["started_at"]).total_seconds()
                    }
                }
            )
            
            logger.info(f"Task completed successfully: {task_id}")
            
        except Exception as e:
            # Handle task failure
            error_message = str(e)
            logger.error(f"Task {task_id} failed: {error_message}")
            
            # Check if we should retry
            task = self.virtual_tasks.find_one({"id": task_id})
            if task and task["retry_count"] < task["max_retries"]:
                # Retry task
                self.virtual_tasks.update_one(
                    {"id": task_id},
                    {
                        "$set": {
                            "status": TaskStatus.PENDING.value,
                            "error_message": error_message
                        },
                        "$inc": {"retry_count": 1}
                    }
                )
                
                # Re-queue task
                if workspace_id in self.task_queues:
                    await self.task_queues[workspace_id].put(task_id)
            else:
                # Mark as failed
                self.virtual_tasks.update_one(
                    {"id": task_id},
                    {
                        "$set": {
                            "status": TaskStatus.FAILED.value,
                            "error_message": error_message,
                            "completed_at": datetime.utcnow()
                        }
                    }
                )
        
        finally:
            # Cleanup runtime state
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            if workspace_id in self.active_workspaces:
                active_tasks = self.active_workspaces[workspace_id]["active_tasks"]
                if task_id in active_tasks:
                    active_tasks.remove(task_id)
    
    # Task Handlers
    
    async def _handle_web_scraping_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web scraping task"""
        
        await self._update_task_progress(task_id, 10, "Initializing web scraper")
        
        url = config.get("url")
        selectors = config.get("selectors", {})
        
        # Simulate web scraping
        await asyncio.sleep(2)
        await self._update_task_progress(task_id, 50, "Loading webpage")
        
        await asyncio.sleep(2)
        await self._update_task_progress(task_id, 80, "Extracting data")
        
        await asyncio.sleep(1)
        await self._update_task_progress(task_id, 100, "Scraping completed")
        
        return {
            "url": url,
            "scraped_data": {
                "title": "Example Page Title",
                "content": "Scraped content would be here",
                "links": ["https://example.com/link1", "https://example.com/link2"],
                "metadata": {"scraped_at": datetime.utcnow().isoformat()}
            },
            "selectors_used": selectors
        }
    
    async def _handle_data_processing_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data processing task"""
        
        await self._update_task_progress(task_id, 10, "Loading dataset")
        
        data_source = config.get("data_source")
        operations = config.get("operations", [])
        
        # Simulate data processing
        for i, operation in enumerate(operations):
            progress = 20 + (60 * i / len(operations))
            await self._update_task_progress(task_id, progress, f"Applying {operation}")
            await asyncio.sleep(1)
        
        await self._update_task_progress(task_id, 90, "Generating results")
        await asyncio.sleep(1)
        
        return {
            "data_source": data_source,
            "operations_applied": operations,
            "processed_records": 1000,
            "result_summary": {
                "total_processed": 1000,
                "successful": 980,
                "errors": 20,
                "processing_time": 5.2
            }
        }
    
    async def _handle_automation_workflow_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle automation workflow task"""
        
        await self._update_task_progress(task_id, 10, "Initializing workflow")
        
        workflow_steps = config.get("workflow_steps", [])
        
        results = []
        
        for i, step in enumerate(workflow_steps):
            progress = 20 + (70 * i / len(workflow_steps))
            await self._update_task_progress(task_id, progress, f"Executing step: {step.get('name', 'Unknown')}")
            
            # Simulate step execution
            await asyncio.sleep(2)
            
            results.append({
                "step": step.get("name", "Unknown"),
                "status": "completed",
                "result": "Step completed successfully"
            })
        
        await self._update_task_progress(task_id, 100, "Workflow completed")
        
        return {
            "workflow_name": config.get("workflow_name", "Unnamed Workflow"),
            "steps_executed": len(workflow_steps),
            "step_results": results,
            "overall_status": "completed"
        }
    
    async def _handle_integration_sync_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle integration synchronization task"""
        
        await self._update_task_progress(task_id, 10, "Connecting to integration")
        
        integration_type = config.get("integration_type")
        sync_direction = config.get("sync_direction", "bidirectional")
        
        await asyncio.sleep(1)
        await self._update_task_progress(task_id, 30, "Fetching remote data")
        
        await asyncio.sleep(2)
        await self._update_task_progress(task_id, 60, "Synchronizing changes")
        
        await asyncio.sleep(1)
        await self._update_task_progress(task_id, 90, "Finalizing sync")
        
        await asyncio.sleep(1)
        
        return {
            "integration_type": integration_type,
            "sync_direction": sync_direction,
            "records_synced": 150,
            "sync_summary": {
                "created": 45,
                "updated": 80,
                "deleted": 25,
                "conflicts": 0
            }
        }
    
    async def _handle_scheduled_action_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduled action task"""
        
        await self._update_task_progress(task_id, 20, "Preparing scheduled action")
        
        action_type = config.get("action_type")
        target = config.get("target")
        
        await asyncio.sleep(1)
        await self._update_task_progress(task_id, 60, f"Executing {action_type}")
        
        await asyncio.sleep(2)
        await self._update_task_progress(task_id, 100, "Action completed")
        
        return {
            "action_type": action_type,
            "target": target,
            "execution_time": datetime.utcnow().isoformat(),
            "status": "completed"
        }
    
    async def _handle_monitoring_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitoring task"""
        
        await self._update_task_progress(task_id, 10, "Setting up monitors")
        
        urls_to_monitor = config.get("urls", [])
        check_interval = config.get("check_interval", 300)
        
        results = []
        
        for i, url in enumerate(urls_to_monitor):
            progress = 20 + (70 * i / len(urls_to_monitor))
            await self._update_task_progress(task_id, progress, f"Checking {url}")
            
            await asyncio.sleep(1)
            
            # Simulate monitoring check
            results.append({
                "url": url,
                "status": "online",
                "response_time": 0.25,
                "status_code": 200,
                "checked_at": datetime.utcnow().isoformat()
            })
        
        await self._update_task_progress(task_id, 100, "Monitoring completed")
        
        return {
            "monitored_urls": len(urls_to_monitor),
            "check_interval": check_interval,
            "results": results,
            "summary": {
                "online": len([r for r in results if r["status"] == "online"]),
                "offline": 0,
                "average_response_time": sum(r["response_time"] for r in results) / len(results) if results else 0
            }
        }
    
    async def _handle_research_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle research task"""
        
        await self._update_task_progress(task_id, 10, "Initializing research")
        
        research_query = config.get("query")
        sources = config.get("sources", ["web", "academic", "news"])
        
        research_results = []
        
        for i, source in enumerate(sources):
            progress = 20 + (60 * i / len(sources))
            await self._update_task_progress(task_id, progress, f"Searching {source}")
            
            await asyncio.sleep(2)
            
            # Simulate research results
            research_results.append({
                "source": source,
                "results_count": 25,
                "top_results": [
                    {"title": f"Research Result {j+1} from {source}", "url": f"https://example.com/{source}/{j+1}"}
                    for j in range(3)
                ]
            })
        
        await self._update_task_progress(task_id, 90, "Compiling research report")
        await asyncio.sleep(1)
        
        return {
            "research_query": research_query,
            "sources_searched": sources,
            "total_results": sum(r["results_count"] for r in research_results),
            "research_results": research_results,
            "summary": f"Found comprehensive information about '{research_query}' from {len(sources)} sources."
        }
    
    async def _handle_file_processing_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file processing task"""
        
        await self._update_task_progress(task_id, 10, "Loading files")
        
        file_paths = config.get("file_paths", [])
        operation = config.get("operation", "analyze")
        
        processed_files = []
        
        for i, file_path in enumerate(file_paths):
            progress = 20 + (70 * i / len(file_paths))
            await self._update_task_progress(task_id, progress, f"Processing {file_path}")
            
            await asyncio.sleep(1)
            
            processed_files.append({
                "file_path": file_path,
                "operation": operation,
                "status": "processed",
                "size_bytes": 1024 * (i + 1),
                "processing_time": 1.2
            })
        
        await self._update_task_progress(task_id, 100, "File processing completed")
        
        return {
            "operation": operation,
            "files_processed": len(file_paths),
            "processed_files": processed_files,
            "total_size": sum(f["size_bytes"] for f in processed_files),
            "total_time": sum(f["processing_time"] for f in processed_files)
        }
    
    async def _handle_ai_analysis_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AI analysis task"""
        
        await self._update_task_progress(task_id, 10, "Initializing AI analysis")
        
        analysis_type = config.get("analysis_type", "general")
        data_input = config.get("data_input")
        
        await asyncio.sleep(1)
        await self._update_task_progress(task_id, 30, "Loading AI models")
        
        await asyncio.sleep(2)
        await self._update_task_progress(task_id, 60, "Running analysis")
        
        await asyncio.sleep(3)
        await self._update_task_progress(task_id, 90, "Generating insights")
        
        await asyncio.sleep(1)
        
        return {
            "analysis_type": analysis_type,
            "input_processed": True,
            "insights": [
                "Key insight 1: Data shows positive trend",
                "Key insight 2: Anomaly detected in sector B",
                "Key insight 3: Recommendation for optimization"
            ],
            "confidence_score": 0.87,
            "processing_time": 7.2
        }
    
    async def _handle_notification_task(self, task_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification task"""
        
        await self._update_task_progress(task_id, 30, "Preparing notification")
        
        notification_type = config.get("type", "info")
        message = config.get("message")
        recipients = config.get("recipients", [])
        
        await asyncio.sleep(1)
        await self._update_task_progress(task_id, 80, "Sending notifications")
        
        await asyncio.sleep(1)
        
        return {
            "notification_type": notification_type,
            "message": message,
            "recipients_count": len(recipients),
            "sent_at": datetime.utcnow().isoformat(),
            "delivery_status": "delivered"
        }
    
    # Utility Methods
    
    async def _update_task_progress(self, task_id: str, progress: float, current_step: str):
        """Update task progress"""
        
        # Update in database
        self.virtual_tasks.update_one(
            {"id": task_id},
            {"$set": {"progress": progress}}
        )
        
        # Update runtime state
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["progress"] = progress
            self.running_tasks[task_id]["current_step"] = current_step
    
    async def _cleanup_completed_tasks(self):
        """Clean up old completed tasks"""
        
        # Remove completed tasks older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        result = self.virtual_tasks.delete_many({
            "status": {"$in": [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]},
            "completed_at": {"$lt": cutoff_date}
        })
        
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} old tasks")
    
    async def _background_resource_monitoring(self):
        """Background resource monitoring"""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                # Monitor resource usage for active workspaces
                for workspace_id, context in self.active_workspaces.items():
                    resource_usage = await self.resource_monitor.get_workspace_usage(workspace_id)
                    context["resource_usage"] = resource_usage
                    
                    # Store resource usage history
                    usage_doc = {
                        "workspace_id": workspace_id,
                        "timestamp": datetime.utcnow(),
                        "memory_mb": resource_usage["memory_mb"],
                        "cpu_percent": resource_usage["cpu_percent"],
                        "active_tasks": len(context["active_tasks"])
                    }
                    
                    self.resource_usage.insert_one(usage_doc)
                
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
    
    async def get_workspace_resource_history(self, user_session: str, workspace_id: str, 
                                           hours: int = 24) -> List[Dict[str, Any]]:
        """Get resource usage history for a workspace"""
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        history = list(self.resource_usage.find(
            {
                "workspace_id": workspace_id,
                "timestamp": {"$gte": start_time}
            },
            {"_id": 0}
        ).sort("timestamp", 1))
        
        # Convert timestamps
        for record in history:
            if record.get("timestamp"):
                record["timestamp"] = record["timestamp"].isoformat()
        
        return history


class ResourceMonitor:
    """Monitor resource usage for virtual workspaces"""
    
    def __init__(self):
        self.workspace_metrics = {}
    
    async def get_workspace_usage(self, workspace_id: str) -> Dict[str, Any]:
        """Get current resource usage for workspace"""
        
        # Simulate resource monitoring
        # In real implementation, this would track actual resource usage
        
        return {
            "memory_mb": 64 + (hash(workspace_id) % 200),  # Simulated memory usage
            "cpu_percent": 5 + (hash(workspace_id) % 20),   # Simulated CPU usage
            "disk_usage_mb": 100 + (hash(workspace_id) % 500),
            "network_io": {
                "bytes_in": 1024 * (hash(workspace_id) % 1000),
                "bytes_out": 512 * (hash(workspace_id) % 800)
            }
        }


# Global virtual workspace manager instance
virtual_workspace_manager = None  # Will be initialized in server.py