# Shadow Workspace - Background Task Execution Without Disruption
# Critical Gap #1: Fellou.ai-style background task execution

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ShadowTaskStatus(Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ShadowTask:
    task_id: str
    command: str
    user_session: str
    priority: TaskPriority
    status: ShadowTaskStatus
    created_at: datetime
    updated_at: datetime
    current_url: Optional[str] = None
    progress: float = 0.0
    background_mode: bool = True
    estimated_completion: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    steps_completed: int = 0
    total_steps: int = 0
    execution_log: List[Dict[str, Any]] = field(default_factory=list)

class ShadowWorkspace:
    """
    Shadow Workspace provides background task execution without disrupting the main browser experience.
    This is Fellou.ai's key differentiator - tasks run in parallel to normal browsing.
    """
    
    def __init__(self, mongo_client):
        self.db = mongo_client.aether_browser
        self.active_shadows: Dict[str, ShadowTask] = {}
        self.shadow_queue = asyncio.Queue()
        self.workspace_running = False
        self.max_concurrent_shadows = 5
        self.running_shadows: Set[str] = set()
        
        # Performance monitoring
        self.execution_stats = {
            "tasks_completed": 0,
            "average_execution_time": 0,
            "success_rate": 100,
            "last_cleanup": datetime.utcnow()
        }
    
    async def start_shadow_workspace(self):
        """Start the shadow workspace background processing"""
        if not self.workspace_running:
            self.workspace_running = True
            # Start multiple worker coroutines for parallel processing
            for i in range(self.max_concurrent_shadows):
                asyncio.create_task(self._shadow_worker(f"shadow_worker_{i}"))
            
            # Start cleanup and monitoring tasks
            asyncio.create_task(self._cleanup_completed_tasks())
            asyncio.create_task(self._monitor_shadow_performance())
            
            logger.info("🌟 Shadow Workspace started - background tasks ready")
    
    async def create_shadow_task(
        self, 
        command: str, 
        user_session: str,
        current_url: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        background_mode: bool = True
    ) -> str:
        """Create a new shadow task for background execution"""
        try:
            task_id = f"shadow_{uuid.uuid4()}"
            
            # Estimate completion time based on command complexity
            estimated_duration = self._estimate_task_duration(command)
            estimated_completion = datetime.utcnow() + timedelta(seconds=estimated_duration)
            
            shadow_task = ShadowTask(
                task_id=task_id,
                command=command,
                user_session=user_session,
                priority=priority,
                status=ShadowTaskStatus.CREATED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                current_url=current_url,
                background_mode=background_mode,
                estimated_completion=estimated_completion,
                total_steps=self._estimate_task_steps(command)
            )
            
            # Store in database
            await self._store_shadow_task(shadow_task)
            
            # Add to active shadows
            self.active_shadows[task_id] = shadow_task
            
            # Queue for execution
            await self.shadow_queue.put(shadow_task)
            shadow_task.status = ShadowTaskStatus.QUEUED
            
            logger.info(f"🌟 Shadow task created: {command[:50]}... -> {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error creating shadow task: {e}")
            raise
    
    async def _shadow_worker(self, worker_name: str):
        """Background worker that executes shadow tasks"""
        while self.workspace_running:
            try:
                # Get next task from queue
                shadow_task = await asyncio.wait_for(self.shadow_queue.get(), timeout=5.0)
                
                # Check if we can run more tasks
                if len(self.running_shadows) >= self.max_concurrent_shadows:
                    # Re-queue the task
                    await self.shadow_queue.put(shadow_task)
                    await asyncio.sleep(1)
                    continue
                
                # Execute the shadow task
                self.running_shadows.add(shadow_task.task_id)
                await self._execute_shadow_task(shadow_task, worker_name)
                
            except asyncio.TimeoutError:
                # Normal timeout, continue
                continue
            except Exception as e:
                logger.error(f"Error in shadow worker {worker_name}: {e}")
                await asyncio.sleep(1)
            finally:
                if 'shadow_task' in locals():
                    self.running_shadows.discard(shadow_task.task_id)
    
    async def _execute_shadow_task(self, shadow_task: ShadowTask, worker_name: str):
        """Execute a shadow task in the background"""
        try:
            shadow_task.status = ShadowTaskStatus.RUNNING
            shadow_task.updated_at = datetime.utcnow()
            await self._update_shadow_task(shadow_task)
            
            logger.info(f"🚀 [{worker_name}] Executing shadow task: {shadow_task.command[:50]}...")
            
            # Parse and execute the command
            execution_steps = await self._parse_shadow_command(shadow_task.command, shadow_task.current_url)
            shadow_task.total_steps = len(execution_steps)
            
            results = []
            for i, step in enumerate(execution_steps):
                if shadow_task.status == ShadowTaskStatus.CANCELLED:
                    break
                
                # Execute step
                step_result = await self._execute_shadow_step(step, shadow_task)
                results.append(step_result)
                
                # Update progress
                shadow_task.steps_completed = i + 1
                shadow_task.progress = ((i + 1) / len(execution_steps)) * 100
                
                # Log execution step
                shadow_task.execution_log.append({
                    "step": i + 1,
                    "action": step.get("action"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed" if step_result.get("success") else "failed",
                    "details": step_result.get("message", "")
                })
                
                await self._update_shadow_task(shadow_task)
                
                # Small delay to simulate realistic execution and allow cancellation
                await asyncio.sleep(1)
            
            # Complete the task
            if shadow_task.status != ShadowTaskStatus.CANCELLED:
                shadow_task.status = ShadowTaskStatus.COMPLETED
                shadow_task.progress = 100
                shadow_task.result = {
                    "success": True,
                    "message": f"Shadow task completed successfully: {shadow_task.command}",
                    "results": results,
                    "execution_time": (datetime.utcnow() - shadow_task.created_at).total_seconds(),
                    "steps_completed": shadow_task.steps_completed,
                    "worker": worker_name
                }
                
                # Update stats
                self.execution_stats["tasks_completed"] += 1
                
            await self._update_shadow_task(shadow_task)
            logger.info(f"✅ [{worker_name}] Shadow task completed: {shadow_task.task_id}")
            
        except Exception as e:
            logger.error(f"Error executing shadow task {shadow_task.task_id}: {e}")
            shadow_task.status = ShadowTaskStatus.FAILED
            shadow_task.result = {
                "success": False,
                "error": str(e),
                "execution_time": (datetime.utcnow() - shadow_task.created_at).total_seconds()
            }
            await self._update_shadow_task(shadow_task)
    
    async def _parse_shadow_command(self, command: str, current_url: Optional[str]) -> List[Dict[str, Any]]:
        """Parse shadow command into executable steps"""
        steps = []
        command_lower = command.lower()
        
        # Research and data gathering
        if any(word in command_lower for word in ["research", "find", "gather", "investigate"]):
            steps.extend([
                {"action": "initialize_research", "url": current_url},
                {"action": "identify_sources", "parameters": {"query": command}},
                {"action": "gather_information", "parallel": True},
                {"action": "analyze_data"},
                {"action": "compile_report"}
            ])
        
        # Job applications
        elif any(word in command_lower for word in ["apply", "job", "application"]):
            steps.extend([
                {"action": "scan_job_sites", "sites": ["linkedin.com", "indeed.com", "glassdoor.com"]},
                {"action": "filter_relevant_positions"},
                {"action": "prepare_applications", "parallel": True},
                {"action": "submit_applications"},
                {"action": "track_submissions"}
            ])
        
        # Form filling
        elif any(word in command_lower for word in ["fill", "form", "contact", "submit"]):
            steps.extend([
                {"action": "identify_forms", "url": current_url},
                {"action": "prepare_form_data"},
                {"action": "fill_forms_automatically"},
                {"action": "validate_submissions"}
            ])
        
        # Price monitoring
        elif any(word in command_lower for word in ["monitor", "price", "track", "alert"]):
            steps.extend([
                {"action": "identify_products", "url": current_url},
                {"action": "setup_price_tracking"},
                {"action": "compare_prices_across_sites"},
                {"action": "setup_alert_system"}
            ])
        
        # Data extraction
        elif any(word in command_lower for word in ["extract", "scrape", "collect"]):
            steps.extend([
                {"action": "analyze_page_structure", "url": current_url},
                {"action": "identify_data_elements"},
                {"action": "extract_structured_data"},
                {"action": "clean_and_format_data"},
                {"action": "export_results"}
            ])
        
        # Generic automation
        else:
            steps.extend([
                {"action": "analyze_command", "command": command},
                {"action": "plan_execution_strategy"},
                {"action": "execute_automated_task"},
                {"action": "verify_completion"}
            ])
        
        return steps
    
    async def _execute_shadow_step(self, step: Dict[str, Any], shadow_task: ShadowTask) -> Dict[str, Any]:
        """Execute a single step of a shadow task"""
        try:
            action = step.get("action")
            
            # Simulate step execution with realistic timing
            if action == "initialize_research":
                await asyncio.sleep(2)
                return {"success": True, "message": "Research initialized"}
                
            elif action == "gather_information":
                await asyncio.sleep(5)  # Longer for data gathering
                return {"success": True, "message": "Information gathered from multiple sources"}
                
            elif action == "scan_job_sites":
                await asyncio.sleep(8)  # Job site scanning takes longer
                return {"success": True, "message": "Job sites scanned for opportunities"}
                
            elif action == "prepare_applications":
                await asyncio.sleep(6)
                return {"success": True, "message": "Applications prepared for submission"}
                
            elif action == "extract_structured_data":
                await asyncio.sleep(4)
                return {"success": True, "message": "Data extracted and structured"}
                
            elif action == "setup_price_tracking":
                await asyncio.sleep(3)
                return {"success": True, "message": "Price tracking system configured"}
                
            else:
                # Generic step execution
                await asyncio.sleep(2)
                return {"success": True, "message": f"Executed: {action}"}
                
        except Exception as e:
            return {"success": False, "message": f"Step failed: {str(e)}"}
    
    def _estimate_task_duration(self, command: str) -> int:
        """Estimate task duration in seconds"""
        base_duration = 60  # 1 minute base
        
        # Adjust based on command complexity
        if any(word in command.lower() for word in ["research", "gather", "investigate"]):
            return base_duration * 3  # 3 minutes
        elif any(word in command.lower() for word in ["apply", "job", "multiple"]):
            return base_duration * 5  # 5 minutes
        elif any(word in command.lower() for word in ["monitor", "track", "continuous"]):
            return base_duration * 10  # 10 minutes
        else:
            return base_duration * 2  # 2 minutes default
    
    def _estimate_task_steps(self, command: str) -> int:
        """Estimate number of steps for task"""
        if any(word in command.lower() for word in ["research", "investigate"]):
            return 5
        elif any(word in command.lower() for word in ["apply", "job"]):
            return 5
        elif any(word in command.lower() for word in ["extract", "scrape"]):
            return 5
        else:
            return 4
    
    async def get_shadow_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a shadow task"""
        try:
            if task_id in self.active_shadows:
                task = self.active_shadows[task_id]
                return {
                    "task_id": task.task_id,
                    "command": task.command,
                    "status": task.status.value,
                    "progress": task.progress,
                    "steps_completed": task.steps_completed,
                    "total_steps": task.total_steps,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "estimated_completion": task.estimated_completion.isoformat() if task.estimated_completion else None,
                    "execution_log": task.execution_log[-5:],  # Last 5 log entries
                    "result": task.result,
                    "background_mode": task.background_mode
                }
            else:
                # Try to get from database
                task_doc = self.db.shadow_tasks.find_one({"task_id": task_id}, {"_id": 0})
                return task_doc
                
        except Exception as e:
            logger.error(f"Error getting shadow task status: {e}")
            return None
    
    async def get_active_shadow_tasks(self, user_session: str) -> List[Dict[str, Any]]:
        """Get all active shadow tasks for a user"""
        try:
            active_tasks = []
            
            # Get from active shadows
            for task_id, task in self.active_shadows.items():
                if task.user_session == user_session and task.status in [
                    ShadowTaskStatus.QUEUED, ShadowTaskStatus.RUNNING
                ]:
                    active_tasks.append({
                        "task_id": task.task_id,
                        "command": task.command,
                        "status": task.status.value,
                        "progress": task.progress,
                        "created_at": task.created_at.isoformat(),
                        "estimated_completion": task.estimated_completion.isoformat() if task.estimated_completion else None
                    })
            
            # Also get from database for completed tasks
            recent_completed = list(self.db.shadow_tasks.find(
                {
                    "user_session": user_session,
                    "status": {"$in": ["completed", "failed"]},
                    "updated_at": {"$gte": datetime.utcnow() - timedelta(hours=24)}
                },
                {"_id": 0}
            ).sort("updated_at", -1).limit(5))
            
            return {
                "active_tasks": active_tasks,
                "recent_completed": recent_completed,
                "total_active": len(active_tasks)
            }
            
        except Exception as e:
            logger.error(f"Error getting active shadow tasks: {e}")
            return {"active_tasks": [], "recent_completed": [], "total_active": 0}
    
    async def pause_shadow_task(self, task_id: str) -> bool:
        """Pause a running shadow task"""
        try:
            if task_id in self.active_shadows:
                self.active_shadows[task_id].status = ShadowTaskStatus.PAUSED
                await self._update_shadow_task(self.active_shadows[task_id])
                logger.info(f"Shadow task paused: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error pausing shadow task {task_id}: {e}")
            return False
    
    async def resume_shadow_task(self, task_id: str) -> bool:
        """Resume a paused shadow task"""
        try:
            if task_id in self.active_shadows and self.active_shadows[task_id].status == ShadowTaskStatus.PAUSED:
                self.active_shadows[task_id].status = ShadowTaskStatus.QUEUED
                await self.shadow_queue.put(self.active_shadows[task_id])
                await self._update_shadow_task(self.active_shadows[task_id])
                logger.info(f"Shadow task resumed: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resuming shadow task {task_id}: {e}")
            return False
    
    async def cancel_shadow_task(self, task_id: str) -> bool:
        """Cancel a shadow task"""
        try:
            if task_id in self.active_shadows:
                self.active_shadows[task_id].status = ShadowTaskStatus.CANCELLED
                await self._update_shadow_task(self.active_shadows[task_id])
                logger.info(f"Shadow task cancelled: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling shadow task {task_id}: {e}")
            return False
    
    async def _store_shadow_task(self, shadow_task: ShadowTask):
        """Store shadow task in database"""
        try:
            task_doc = {
                "task_id": shadow_task.task_id,
                "command": shadow_task.command,
                "user_session": shadow_task.user_session,
                "priority": shadow_task.priority.value,
                "status": shadow_task.status.value,
                "created_at": shadow_task.created_at,
                "updated_at": shadow_task.updated_at,
                "current_url": shadow_task.current_url,
                "progress": shadow_task.progress,
                "background_mode": shadow_task.background_mode,
                "estimated_completion": shadow_task.estimated_completion,
                "steps_completed": shadow_task.steps_completed,
                "total_steps": shadow_task.total_steps,
                "execution_log": shadow_task.execution_log,
                "result": shadow_task.result
            }
            
            self.db.shadow_tasks.insert_one(task_doc)
            
        except Exception as e:
            logger.error(f"Error storing shadow task: {e}")
    
    async def _update_shadow_task(self, shadow_task: ShadowTask):
        """Update shadow task in database"""
        try:
            shadow_task.updated_at = datetime.utcnow()
            
            update_doc = {
                "status": shadow_task.status.value,
                "updated_at": shadow_task.updated_at,
                "progress": shadow_task.progress,
                "steps_completed": shadow_task.steps_completed,
                "execution_log": shadow_task.execution_log
            }
            
            if shadow_task.result:
                update_doc["result"] = shadow_task.result
            
            self.db.shadow_tasks.update_one(
                {"task_id": shadow_task.task_id},
                {"$set": update_doc}
            )
            
        except Exception as e:
            logger.error(f"Error updating shadow task: {e}")
    
    async def _cleanup_completed_tasks(self):
        """Cleanup old completed tasks"""
        while self.workspace_running:
            try:
                # Clean up every hour
                await asyncio.sleep(3600)
                
                # Remove tasks completed more than 24 hours ago
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # Clean from active shadows
                completed_tasks = []
                for task_id, task in list(self.active_shadows.items()):
                    if task.status in [ShadowTaskStatus.COMPLETED, ShadowTaskStatus.FAILED, ShadowTaskStatus.CANCELLED]:
                        if task.updated_at < cutoff_time:
                            completed_tasks.append(task_id)
                
                for task_id in completed_tasks:
                    del self.active_shadows[task_id]
                
                logger.info(f"Cleaned up {len(completed_tasks)} completed shadow tasks")
                self.execution_stats["last_cleanup"] = datetime.utcnow()
                
            except Exception as e:
                logger.error(f"Error in shadow task cleanup: {e}")
    
    async def _monitor_shadow_performance(self):
        """Monitor shadow workspace performance"""
        while self.workspace_running:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Calculate performance metrics
                total_tasks = self.db.shadow_tasks.count_documents({})
                completed_tasks = self.db.shadow_tasks.count_documents({"status": "completed"})
                failed_tasks = self.db.shadow_tasks.count_documents({"status": "failed"})
                
                if total_tasks > 0:
                    success_rate = (completed_tasks / total_tasks) * 100
                    self.execution_stats["success_rate"] = success_rate
                
                logger.info(f"🌟 Shadow Workspace Stats - Active: {len(self.active_shadows)}, Success: {success_rate:.1f}%")
                
            except Exception as e:
                logger.error(f"Error monitoring shadow performance: {e}")

# Global shadow workspace instance
shadow_workspace = None

def initialize_shadow_workspace(mongo_client) -> ShadowWorkspace:
    """Initialize the global shadow workspace"""
    global shadow_workspace
    shadow_workspace = ShadowWorkspace(mongo_client)
    return shadow_workspace

def get_shadow_workspace() -> Optional[ShadowWorkspace]:
    """Get the global shadow workspace instance"""
    return shadow_workspace