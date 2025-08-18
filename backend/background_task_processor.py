import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import time
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import queue
import signal
import os

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5

class TaskType(Enum):
    AI_PROCESSING = "ai_processing"
    WEB_SCRAPING = "web_scraping"
    DATA_ANALYSIS = "data_analysis"
    FILE_PROCESSING = "file_processing"
    INTEGRATION_SYNC = "integration_sync"
    WORKFLOW_EXECUTION = "workflow_execution"
    REPORT_GENERATION = "report_generation"
    EMAIL_PROCESSING = "email_processing"
    SOCIAL_MEDIA = "social_media"
    DATABASE_MAINTENANCE = "database_maintenance"

@dataclass
class BackgroundTask:
    """Background task data structure"""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    handler: str  # Function name to call
    parameters: Dict[str, Any]
    user_session: Optional[str] = None
    depends_on: List[str] = None
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 300
    scheduled_at: Optional[datetime] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.depends_on is None:
            self.depends_on = []

class BackgroundTaskProcessor:
    """Advanced background task processing system with parallel execution and intelligent scheduling"""
    
    def __init__(self, db_client: MongoClient, max_workers: int = None):
        self.db = db_client.aether_browser
        self.tasks_collection = self.db.background_tasks
        self.task_logs = self.db.task_execution_logs
        
        # Worker configuration
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.max_process_workers = max(1, (os.cpu_count() or 1) // 2)
        
        # Execution pools
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="bg_task")
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_process_workers)
        
        # Task queues by priority
        self.task_queues = {
            TaskPriority.URGENT: asyncio.Queue(maxsize=50),
            TaskPriority.CRITICAL: asyncio.Queue(maxsize=100),
            TaskPriority.HIGH: asyncio.Queue(maxsize=200),
            TaskPriority.NORMAL: asyncio.Queue(maxsize=500),
            TaskPriority.LOW: asyncio.Queue(maxsize=1000)
        }
        
        # Runtime state
        self.running_tasks = {}  # task_id -> task_context
        self.completed_tasks = {}  # task_id -> result
        self.task_handlers = self._initialize_task_handlers()
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "tasks_by_type": {},
            "worker_utilization": 0.0
        }
        
        # Control flags
        self.is_running = False
        self.shutdown_requested = False
        
        # Background workers
        self.worker_tasks = []
        self.scheduler_task = None
        self.monitor_task = None
        
    def _initialize_task_handlers(self) -> Dict[TaskType, Callable]:
        """Initialize task type handlers"""
        return {
            TaskType.AI_PROCESSING: self._handle_ai_processing,
            TaskType.WEB_SCRAPING: self._handle_web_scraping,
            TaskType.DATA_ANALYSIS: self._handle_data_analysis,
            TaskType.FILE_PROCESSING: self._handle_file_processing,
            TaskType.INTEGRATION_SYNC: self._handle_integration_sync,
            TaskType.WORKFLOW_EXECUTION: self._handle_workflow_execution,
            TaskType.REPORT_GENERATION: self._handle_report_generation,
            TaskType.EMAIL_PROCESSING: self._handle_email_processing,
            TaskType.SOCIAL_MEDIA: self._handle_social_media,
            TaskType.DATABASE_MAINTENANCE: self._handle_database_maintenance
        }
    
    async def start(self):
        """Start the background task processor"""
        if self.is_running:
            return
        
        self.is_running = True
        self.shutdown_requested = False
        
        logger.info(f"Starting background task processor with {self.max_workers} workers")
        
        # Start worker tasks for each priority level
        for priority in TaskPriority:
            worker_count = self._get_worker_count_for_priority(priority)
            for i in range(worker_count):
                worker_task = asyncio.create_task(
                    self._worker(priority, f"{priority.name.lower()}_worker_{i}")
                )
                self.worker_tasks.append(worker_task)
        
        # Start scheduler and monitor
        self.scheduler_task = asyncio.create_task(self._task_scheduler())
        self.monitor_task = asyncio.create_task(self._task_monitor())
        
        # Load pending tasks from database
        await self._load_pending_tasks()
        
        logger.info(f"Background task processor started with {len(self.worker_tasks)} workers")
    
    async def stop(self, timeout: int = 30):
        """Stop the background task processor gracefully"""
        if not self.is_running:
            return
        
        logger.info("Stopping background task processor...")
        self.shutdown_requested = True
        
        # Cancel all worker tasks
        for worker_task in self.worker_tasks:
            worker_task.cancel()
        
        # Cancel scheduler and monitor
        if self.scheduler_task:
            self.scheduler_task.cancel()
        if self.monitor_task:
            self.monitor_task.cancel()
        
        # Wait for tasks to complete or timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.worker_tasks, return_exceptions=True), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Some background tasks did not complete within timeout")
        
        # Shutdown thread pools
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        
        self.is_running = False
        self.worker_tasks.clear()
        
        logger.info("Background task processor stopped")
    
    def _get_worker_count_for_priority(self, priority: TaskPriority) -> int:
        """Get worker count based on priority level"""
        if priority == TaskPriority.URGENT:
            return 3
        elif priority == TaskPriority.CRITICAL:
            return 2
        elif priority == TaskPriority.HIGH:
            return 2
        elif priority == TaskPriority.NORMAL:
            return max(2, self.max_workers // 4)
        else:  # LOW
            return 1
    
    async def submit_task(self, task_type: TaskType, parameters: Dict[str, Any], 
                         priority: TaskPriority = TaskPriority.NORMAL,
                         user_session: str = None, depends_on: List[str] = None,
                         scheduled_at: datetime = None, **kwargs) -> str:
        """Submit a new background task"""
        
        task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            handler=self.task_handlers.get(task_type, self._handle_generic_task).__name__,
            parameters=parameters,
            user_session=user_session,
            depends_on=depends_on or [],
            scheduled_at=scheduled_at,
            max_retries=kwargs.get('max_retries', 3),
            timeout_seconds=kwargs.get('timeout_seconds', 300)
        )
        
        # Store in database
        task_doc = asdict(task)
        task_doc['task_type'] = task.task_type.value
        task_doc['priority'] = task.priority.value
        task_doc['status'] = task.status.value
        
        self.tasks_collection.insert_one(task_doc)
        
        # Add to appropriate queue if ready to execute
        if self._is_task_ready(task):
            await self.task_queues[priority].put(task)
        
        # Update statistics
        self.stats["total_tasks"] += 1
        self.stats["tasks_by_type"][task_type.value] = self.stats["tasks_by_type"].get(task_type.value, 0) + 1
        
        logger.info(f"Submitted background task {task_id}: {task_type.value} (priority: {priority.value})")
        
        return task_id
    
    def _is_task_ready(self, task: BackgroundTask) -> bool:
        """Check if task is ready to execute"""
        
        # Check if scheduled time has passed
        if task.scheduled_at and task.scheduled_at > datetime.utcnow():
            return False
        
        # Check dependencies
        if task.depends_on:
            for dep_task_id in task.depends_on:
                dep_task = self.tasks_collection.find_one({"task_id": dep_task_id})
                if not dep_task or dep_task["status"] != TaskStatus.COMPLETED.value:
                    return False
        
        return True
    
    async def _load_pending_tasks(self):
        """Load pending tasks from database on startup"""
        
        try:
            pending_tasks = list(self.tasks_collection.find({
                "status": {"$in": [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]}
            }))
            
            loaded_count = 0
            
            for task_doc in pending_tasks:
                try:
                    task = BackgroundTask(
                        task_id=task_doc["task_id"],
                        task_type=TaskType(task_doc["task_type"]),
                        priority=TaskPriority(task_doc["priority"]),
                        handler=task_doc["handler"],
                        parameters=task_doc["parameters"],
                        user_session=task_doc.get("user_session"),
                        depends_on=task_doc.get("depends_on", []),
                        max_retries=task_doc.get("max_retries", 3),
                        retry_count=task_doc.get("retry_count", 0),
                        timeout_seconds=task_doc.get("timeout_seconds", 300),
                        scheduled_at=task_doc.get("scheduled_at"),
                        created_at=task_doc.get("created_at"),
                        status=TaskStatus(task_doc["status"])
                    )
                    
                    if self._is_task_ready(task):
                        await self.task_queues[task.priority].put(task)
                        loaded_count += 1
                
                except Exception as e:
                    logger.error(f"Error loading task {task_doc.get('task_id', 'unknown')}: {e}")
            
            if loaded_count > 0:
                logger.info(f"Loaded {loaded_count} pending tasks from database")
                
        except Exception as e:
            logger.error(f"Error loading pending tasks: {e}")
    
    async def _worker(self, priority: TaskPriority, worker_name: str):
        """Background task worker for specific priority queue"""
        
        logger.info(f"Started worker {worker_name} for {priority.name} priority tasks")
        
        while not self.shutdown_requested:
            try:
                # Get task from queue with timeout
                try:
                    task = await asyncio.wait_for(
                        self.task_queues[priority].get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Execute the task
                await self._execute_task(task, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)  # Brief pause on error
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _execute_task(self, task: BackgroundTask, worker_name: str):
        """Execute a single background task"""
        
        start_time = time.time()
        task.started_at = datetime.utcnow()
        task.status = TaskStatus.RUNNING
        
        # Update task status in database
        self.tasks_collection.update_one(
            {"task_id": task.task_id},
            {"$set": {
                "status": task.status.value,
                "started_at": task.started_at,
                "progress": 0.0
            }}
        )
        
        # Add to running tasks
        self.running_tasks[task.task_id] = {
            "task": task,
            "worker": worker_name,
            "start_time": start_time
        }
        
        try:
            logger.info(f"Executing task {task.task_id}: {task.task_type.value} on worker {worker_name}")
            
            # Get task handler
            handler = self.task_handlers.get(task.task_type, self._handle_generic_task)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                handler(task),
                timeout=task.timeout_seconds
            )
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            task.progress = 100.0
            
            execution_time = time.time() - start_time
            
            # Update database
            self.tasks_collection.update_one(
                {"task_id": task.task_id},
                {"$set": {
                    "status": task.status.value,
                    "completed_at": task.completed_at,
                    "result": result,
                    "progress": 100.0,
                    "execution_time_seconds": execution_time
                }}
            )
            
            # Update statistics
            self.stats["completed_tasks"] += 1
            self._update_average_execution_time(execution_time)
            
            # Store in completed tasks cache
            self.completed_tasks[task.task_id] = result
            
            # Log execution
            self._log_task_execution(task, worker_name, execution_time, True)
            
            logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            await self._handle_task_failure(task, "Task execution timeout", worker_name)
        except asyncio.CancelledError:
            await self._handle_task_cancellation(task, worker_name)
        except Exception as e:
            await self._handle_task_failure(task, str(e), worker_name)
        
        finally:
            # Remove from running tasks
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]
    
    async def _handle_task_failure(self, task: BackgroundTask, error_message: str, worker_name: str):
        """Handle task execution failure"""
        
        task.error_message = error_message
        execution_time = time.time() - self.running_tasks.get(task.task_id, {}).get("start_time", time.time())
        
        # Check if we should retry
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            
            # Calculate retry delay (exponential backoff)
            retry_delay = min(300, 5 * (2 ** task.retry_count))  # Max 5 minutes
            task.scheduled_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            
            # Update database
            self.tasks_collection.update_one(
                {"task_id": task.task_id},
                {"$set": {
                    "status": task.status.value,
                    "retry_count": task.retry_count,
                    "error_message": error_message,
                    "scheduled_at": task.scheduled_at
                }}
            )
            
            logger.warning(f"Task {task.task_id} failed, retrying in {retry_delay}s (attempt {task.retry_count}/{task.max_retries}): {error_message}")
            
        else:
            # Max retries exceeded
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            # Update database
            self.tasks_collection.update_one(
                {"task_id": task.task_id},
                {"$set": {
                    "status": task.status.value,
                    "completed_at": task.completed_at,
                    "error_message": error_message
                }}
            )
            
            # Update statistics
            self.stats["failed_tasks"] += 1
            
            logger.error(f"Task {task.task_id} failed permanently after {task.retry_count} retries: {error_message}")
        
        # Log execution
        self._log_task_execution(task, worker_name, execution_time, False, error_message)
    
    async def _handle_task_cancellation(self, task: BackgroundTask, worker_name: str):
        """Handle task cancellation"""
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        task.error_message = "Task was cancelled"
        
        execution_time = time.time() - self.running_tasks.get(task.task_id, {}).get("start_time", time.time())
        
        # Update database
        self.tasks_collection.update_one(
            {"task_id": task.task_id},
            {"$set": {
                "status": task.status.value,
                "completed_at": task.completed_at,
                "error_message": task.error_message
            }}
        )
        
        # Log execution
        self._log_task_execution(task, worker_name, execution_time, False, "Cancelled")
        
        logger.info(f"Task {task.task_id} was cancelled")
    
    def _log_task_execution(self, task: BackgroundTask, worker_name: str, 
                          execution_time: float, success: bool, error_message: str = None):
        """Log task execution details"""
        
        try:
            log_entry = {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "priority": task.priority.value,
                "worker_name": worker_name,
                "user_session": task.user_session,
                "success": success,
                "execution_time_seconds": execution_time,
                "error_message": error_message,
                "retry_count": task.retry_count,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "logged_at": datetime.utcnow()
            }
            
            self.task_logs.insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Error logging task execution: {e}")
    
    def _update_average_execution_time(self, execution_time: float):
        """Update average execution time statistic"""
        
        current_avg = self.stats["average_execution_time"]
        completed_count = self.stats["completed_tasks"]
        
        if completed_count == 1:
            self.stats["average_execution_time"] = execution_time
        else:
            # Exponential moving average
            self.stats["average_execution_time"] = (current_avg * 0.9) + (execution_time * 0.1)
    
    async def _task_scheduler(self):
        """Background task scheduler for scheduled and retry tasks"""
        
        logger.info("Started background task scheduler")
        
        while not self.shutdown_requested:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                current_time = datetime.utcnow()
                
                # Find scheduled tasks that are ready to run
                ready_tasks = list(self.tasks_collection.find({
                    "status": {"$in": [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]},
                    "$or": [
                        {"scheduled_at": {"$lte": current_time}},
                        {"scheduled_at": {"$exists": False}}
                    ]
                }))
                
                for task_doc in ready_tasks:
                    try:
                        task = BackgroundTask(
                            task_id=task_doc["task_id"],
                            task_type=TaskType(task_doc["task_type"]),
                            priority=TaskPriority(task_doc["priority"]),
                            handler=task_doc["handler"],
                            parameters=task_doc["parameters"],
                            user_session=task_doc.get("user_session"),
                            depends_on=task_doc.get("depends_on", []),
                            max_retries=task_doc.get("max_retries", 3),
                            retry_count=task_doc.get("retry_count", 0),
                            timeout_seconds=task_doc.get("timeout_seconds", 300),
                            scheduled_at=task_doc.get("scheduled_at"),
                            created_at=task_doc.get("created_at"),
                            status=TaskStatus(task_doc["status"])
                        )
                        
                        if self._is_task_ready(task):
                            await self.task_queues[task.priority].put(task)
                            
                    except Exception as e:
                        logger.error(f"Error scheduling task {task_doc.get('task_id', 'unknown')}: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task scheduler error: {e}")
        
        logger.info("Background task scheduler stopped")
    
    async def _task_monitor(self):
        """Background task monitor for health checks and cleanup"""
        
        logger.info("Started background task monitor")
        
        while not self.shutdown_requested:
            try:
                await asyncio.sleep(60)  # Monitor every minute
                
                # Update worker utilization
                active_workers = len(self.running_tasks)
                total_workers = len(self.worker_tasks)
                self.stats["worker_utilization"] = (active_workers / total_workers * 100) if total_workers > 0 else 0
                
                # Clean up old completed tasks
                await self._cleanup_old_tasks()
                
                # Monitor stuck tasks
                await self._monitor_stuck_tasks()
                
                # Update queue sizes in stats
                queue_sizes = {
                    priority.name: self.task_queues[priority].qsize() 
                    for priority in TaskPriority
                }
                self.stats["queue_sizes"] = queue_sizes
                
                # Log status
                if self.running_tasks or any(q.qsize() > 0 for q in self.task_queues.values()):
                    logger.info(f"Task processor status: {len(self.running_tasks)} running, queues: {queue_sizes}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task monitor error: {e}")
        
        logger.info("Background task monitor stopped")
    
    async def _cleanup_old_tasks(self):
        """Clean up old completed tasks"""
        
        try:
            # Remove completed tasks older than 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            result = self.tasks_collection.delete_many({
                "status": {"$in": [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]},
                "completed_at": {"$lt": cutoff_time}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old tasks")
            
            # Clean up task logs older than 7 days
            log_cutoff = datetime.utcnow() - timedelta(days=7)
            
            log_result = self.task_logs.delete_many({
                "logged_at": {"$lt": log_cutoff}
            })
            
            if log_result.deleted_count > 0:
                logger.info(f"Cleaned up {log_result.deleted_count} old task logs")
            
        except Exception as e:
            logger.error(f"Task cleanup error: {e}")
    
    async def _monitor_stuck_tasks(self):
        """Monitor for stuck tasks and handle them"""
        
        try:
            # Find tasks running longer than their timeout + buffer
            for task_id, context in list(self.running_tasks.items()):
                task = context["task"]
                start_time = context["start_time"]
                
                # Check if task has been running too long
                runtime = time.time() - start_time
                if runtime > task.timeout_seconds + 60:  # 1 minute buffer
                    logger.warning(f"Task {task_id} appears stuck (runtime: {runtime:.1f}s), attempting cleanup")
                    
                    # Mark as failed due to timeout
                    await self._handle_task_failure(task, "Task stuck - exceeded timeout with buffer", context["worker"])
            
        except Exception as e:
            logger.error(f"Stuck task monitoring error: {e}")
    
    # Task Handler Methods
    
    async def _handle_ai_processing(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle AI processing tasks"""
        
        params = task.parameters
        ai_task_type = params.get("type", "text_generation")
        
        # Update progress
        await self._update_task_progress(task.task_id, 25.0, "Starting AI processing")
        
        try:
            if ai_task_type == "text_generation":
                result = await self._process_text_generation(params)
            elif ai_task_type == "image_analysis":
                result = await self._process_image_analysis(params)
            elif ai_task_type == "data_summarization":
                result = await self._process_data_summarization(params)
            else:
                result = {"error": f"Unknown AI task type: {ai_task_type}"}
            
            await self._update_task_progress(task.task_id, 100.0, "AI processing completed")
            
            return {
                "success": True,
                "ai_task_type": ai_task_type,
                "result": result,
                "processing_time": time.time()
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _process_text_generation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process text generation request"""
        
        # Simulate text generation
        await asyncio.sleep(2)  # Simulate processing time
        
        return {
            "generated_text": f"Generated text for prompt: {params.get('prompt', 'N/A')}",
            "model_used": params.get('model', 'default'),
            "tokens_generated": 150
        }
    
    async def _process_image_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process image analysis request"""
        
        # Simulate image analysis
        await asyncio.sleep(3)  # Simulate processing time
        
        return {
            "analysis": "Image contains various objects and elements",
            "confidence": 0.85,
            "objects_detected": ["person", "car", "building"]
        }
    
    async def _process_data_summarization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process data summarization request"""
        
        # Simulate data summarization
        await asyncio.sleep(1.5)
        
        return {
            "summary": "Data summarization completed",
            "key_insights": ["insight1", "insight2", "insight3"],
            "data_points_processed": params.get('data_size', 100)
        }
    
    async def _handle_web_scraping(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle web scraping tasks"""
        
        params = task.parameters
        urls = params.get("urls", [])
        
        await self._update_task_progress(task.task_id, 10.0, "Starting web scraping")
        
        results = []
        for i, url in enumerate(urls):
            try:
                # Simulate web scraping
                await asyncio.sleep(1)  # Simulate request time
                
                result = {
                    "url": url,
                    "title": f"Title for {url}",
                    "content": f"Scraped content from {url}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                results.append(result)
                
                # Update progress
                progress = 10.0 + (80.0 * (i + 1) / len(urls))
                await self._update_task_progress(task.task_id, progress, f"Scraped {i+1}/{len(urls)} URLs")
                
            except Exception as e:
                results.append({"url": url, "error": str(e)})
        
        await self._update_task_progress(task.task_id, 100.0, "Web scraping completed")
        
        return {
            "success": True,
            "scraped_count": len([r for r in results if "error" not in r]),
            "failed_count": len([r for r in results if "error" in r]),
            "results": results
        }
    
    async def _handle_data_analysis(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle data analysis tasks"""
        
        params = task.parameters
        analysis_type = params.get("type", "basic")
        
        await self._update_task_progress(task.task_id, 20.0, "Loading data")
        await asyncio.sleep(1)
        
        await self._update_task_progress(task.task_id, 50.0, "Processing data")
        await asyncio.sleep(2)
        
        await self._update_task_progress(task.task_id, 80.0, "Generating insights")
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "analysis_type": analysis_type,
            "insights": ["Data trend shows upward movement", "Anomalies detected in 3% of records"],
            "statistics": {"mean": 45.2, "median": 43.1, "std_dev": 12.8},
            "processed_records": params.get("record_count", 1000)
        }
    
    async def _handle_file_processing(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle file processing tasks"""
        
        params = task.parameters
        file_type = params.get("file_type", "unknown")
        
        await self._update_task_progress(task.task_id, 30.0, "Reading file")
        await asyncio.sleep(0.5)
        
        await self._update_task_progress(task.task_id, 70.0, "Processing content")
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "file_type": file_type,
            "processed_size": params.get("file_size", "unknown"),
            "processing_time": 1.5
        }
    
    async def _handle_integration_sync(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle integration synchronization tasks"""
        
        params = task.parameters
        integration_name = params.get("integration", "unknown")
        
        await self._update_task_progress(task.task_id, 25.0, "Connecting to integration")
        await asyncio.sleep(1)
        
        await self._update_task_progress(task.task_id, 75.0, "Synchronizing data")
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "integration": integration_name,
            "synced_records": params.get("record_count", 50),
            "sync_time": datetime.utcnow().isoformat()
        }
    
    async def _handle_workflow_execution(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle workflow execution tasks"""
        
        params = task.parameters
        workflow_id = params.get("workflow_id")
        
        await self._update_task_progress(task.task_id, 20.0, "Initializing workflow")
        await asyncio.sleep(0.5)
        
        # Simulate workflow steps
        steps = params.get("steps", 5)
        for i in range(steps):
            progress = 20.0 + (60.0 * (i + 1) / steps)
            await self._update_task_progress(task.task_id, progress, f"Executing step {i+1}/{steps}")
            await asyncio.sleep(0.5)
        
        await self._update_task_progress(task.task_id, 90.0, "Finalizing workflow")
        await asyncio.sleep(0.3)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "steps_completed": steps,
            "execution_time": steps * 0.5 + 0.8
        }
    
    async def _handle_report_generation(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle report generation tasks"""
        
        params = task.parameters
        report_type = params.get("type", "standard")
        
        await self._update_task_progress(task.task_id, 15.0, "Gathering data")
        await asyncio.sleep(1)
        
        await self._update_task_progress(task.task_id, 45.0, "Analyzing data")
        await asyncio.sleep(1.5)
        
        await self._update_task_progress(task.task_id, 75.0, "Generating report")
        await asyncio.sleep(1)
        
        await self._update_task_progress(task.task_id, 95.0, "Formatting report")
        await asyncio.sleep(0.5)
        
        return {
            "success": True,
            "report_type": report_type,
            "pages_generated": params.get("pages", 10),
            "format": params.get("format", "PDF"),
            "file_path": f"/tmp/report_{task.task_id}.pdf"
        }
    
    async def _handle_email_processing(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle email processing tasks"""
        
        params = task.parameters
        email_count = params.get("count", 1)
        
        await self._update_task_progress(task.task_id, 30.0, "Processing emails")
        await asyncio.sleep(email_count * 0.2)  # Simulate processing time per email
        
        return {
            "success": True,
            "emails_processed": email_count,
            "action": params.get("action", "send"),
            "processing_time": email_count * 0.2
        }
    
    async def _handle_social_media(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle social media tasks"""
        
        params = task.parameters
        platform = params.get("platform", "unknown")
        
        await self._update_task_progress(task.task_id, 40.0, f"Connecting to {platform}")
        await asyncio.sleep(1)
        
        await self._update_task_progress(task.task_id, 80.0, "Executing action")
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "platform": platform,
            "action": params.get("action", "post"),
            "engagement": {"likes": 15, "shares": 3, "comments": 7}
        }
    
    async def _handle_database_maintenance(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle database maintenance tasks"""
        
        params = task.parameters
        maintenance_type = params.get("type", "cleanup")
        
        await self._update_task_progress(task.task_id, 50.0, f"Performing {maintenance_type}")
        await asyncio.sleep(2)  # Database operations can take longer
        
        return {
            "success": True,
            "maintenance_type": maintenance_type,
            "records_affected": params.get("affected_count", 100),
            "duration": 2.0
        }
    
    async def _handle_generic_task(self, task: BackgroundTask) -> Dict[str, Any]:
        """Handle generic/unknown task types"""
        
        await self._update_task_progress(task.task_id, 50.0, "Processing generic task")
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "message": f"Generic task {task.task_type.value} completed",
            "parameters": task.parameters
        }
    
    async def _update_task_progress(self, task_id: str, progress: float, status_message: str):
        """Update task progress in database and running tasks"""
        
        # Update database
        self.tasks_collection.update_one(
            {"task_id": task_id},
            {"$set": {
                "progress": progress,
                "status_message": status_message,
                "last_updated": datetime.utcnow()
            }}
        )
        
        # Update running task context
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["task"].progress = progress
    
    # Public API Methods
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        
        task_doc = self.tasks_collection.find_one({"task_id": task_id}, {"_id": 0})
        
        if task_doc:
            # Convert datetime objects to ISO strings
            for field in ["created_at", "started_at", "completed_at", "scheduled_at"]:
                if task_doc.get(field):
                    task_doc[field] = task_doc[field].isoformat()
            
            # Add runtime information if task is running
            if task_id in self.running_tasks:
                task_doc["worker_name"] = self.running_tasks[task_id]["worker"]
                task_doc["runtime_seconds"] = time.time() - self.running_tasks[task_id]["start_time"]
        
        return task_doc
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        
        # Update task status to cancelled
        result = self.tasks_collection.update_one(
            {"task_id": task_id, "status": {"$in": [TaskStatus.PENDING.value, TaskStatus.RETRYING.value]}},
            {"$set": {
                "status": TaskStatus.CANCELLED.value,
                "completed_at": datetime.utcnow(),
                "error_message": "Task cancelled by user"
            }}
        )
        
        return result.modified_count > 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get task processor statistics"""
        
        stats = self.stats.copy()
        stats.update({
            "is_running": self.is_running,
            "active_workers": len(self.worker_tasks),
            "running_tasks": len(self.running_tasks),
            "queue_sizes": {
                priority.name: self.task_queues[priority].qsize() 
                for priority in TaskPriority
            }
        })
        
        return stats
    
    async def get_task_history(self, user_session: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task execution history"""
        
        query = {}
        if user_session:
            query["user_session"] = user_session
        
        tasks = list(self.task_logs.find(
            query,
            {"_id": 0}
        ).sort("logged_at", -1).limit(limit))
        
        # Convert datetime objects
        for task in tasks:
            for field in ["created_at", "started_at", "completed_at", "logged_at"]:
                if task.get(field):
                    task[field] = task[field].isoformat()
        
        return tasks

# Global background task processor instance
background_task_processor = None  # Will be initialized in server.py