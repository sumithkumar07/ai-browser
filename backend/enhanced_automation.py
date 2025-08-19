# Enhanced Automation Engine - NLP Processor and Task Executor
# Provides Fellou.ai-style natural language command processing and background execution

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    CREATED = "created"
    PARSING = "parsing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TaskPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class TaskStep:
    action: str
    url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    expected_duration: int = 30  # seconds
    status: str = "pending"

@dataclass
class Task:
    task_id: str
    command: str
    steps: List[TaskStep]
    context: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None

class NLPProcessor:
    """Natural Language Processing for automation commands"""
    
    def __init__(self):
        self.automation_patterns = {
            "research": {
                "keywords": ["research", "find information", "gather data", "investigate"],
                "actions": ["navigate", "extract", "compile", "summarize"],
                "sites": ["google.com", "wikipedia.org", "arxiv.org", "scholar.google.com"]
            },
            "job_application": {
                "keywords": ["apply", "job", "position", "application", "career"],
                "actions": ["navigate", "fill_form", "upload_resume", "submit"],
                "sites": ["linkedin.com", "indeed.com", "glassdoor.com", "monster.com"]
            },
            "form_filling": {
                "keywords": ["fill", "form", "contact", "submit", "application"],
                "actions": ["navigate", "fill_fields", "validate", "submit"],
                "sites": []
            },
            "price_monitoring": {
                "keywords": ["monitor", "price", "track", "alert", "deal"],
                "actions": ["navigate", "extract_price", "compare", "alert"],
                "sites": ["amazon.com", "ebay.com", "bestbuy.com", "walmart.com"]
            },
            "data_extraction": {
                "keywords": ["extract", "scrape", "collect", "gather", "download"],
                "actions": ["navigate", "extract", "process", "save"],
                "sites": []
            }
        }
    
    async def parse_command(self, command: str, context: Dict[str, Any]) -> Task:
        """Parse natural language command into executable task"""
        try:
            task_id = str(uuid.uuid4())
            command_lower = command.lower()
            
            # Detect task type
            task_type = self._detect_task_type(command_lower)
            
            # Extract parameters
            parameters = self._extract_parameters(command, context)
            
            # Generate steps based on task type
            steps = await self._generate_task_steps(task_type, command, parameters, context)
            
            # Determine priority
            priority = self._determine_priority(command_lower, len(steps))
            
            task = Task(
                task_id=task_id,
                command=command,
                steps=steps,
                context=context,
                priority=priority,
                status=TaskStatus.CREATED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"Parsed command: {command} -> {len(steps)} steps, priority: {priority}")
            return task
            
        except Exception as e:
            logger.error(f"Error parsing command '{command}': {e}")
            raise
    
    def _detect_task_type(self, command: str) -> str:
        """Detect the type of automation task"""
        for task_type, config in self.automation_patterns.items():
            for keyword in config["keywords"]:
                if keyword in command:
                    return task_type
        return "general"
    
    def _extract_parameters(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters from command"""
        parameters = {
            "urls": [],
            "keywords": [],
            "quantity": 1,
            "time_limit": 300,  # 5 minutes default
            "current_url": context.get("current_url")
        }
        
        # Extract URLs
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, command)
        parameters["urls"] = urls
        
        # Extract quantities
        quantity_match = re.search(r'(\d+)\s*(sites?|jobs?|forms?|pages?)', command.lower())
        if quantity_match:
            parameters["quantity"] = int(quantity_match.group(1))
        
        # Extract keywords/search terms
        if "search" in command.lower() or "find" in command.lower():
            # Extract quoted terms or terms after "for"
            quoted_terms = re.findall(r'"([^"]*)"', command)
            for_terms = re.findall(r'for\s+([^,\.\!]+)', command.lower())
            parameters["keywords"] = quoted_terms + for_terms
        
        return parameters
    
    async def _generate_task_steps(self, task_type: str, command: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> List[TaskStep]:
        """Generate executable steps for the task"""
        steps = []
        
        if task_type == "research":
            steps = await self._generate_research_steps(command, parameters)
        elif task_type == "job_application":
            steps = await self._generate_job_application_steps(command, parameters)
        elif task_type == "form_filling":
            steps = await self._generate_form_filling_steps(command, parameters)
        elif task_type == "price_monitoring":
            steps = await self._generate_price_monitoring_steps(command, parameters)
        elif task_type == "data_extraction":
            steps = await self._generate_data_extraction_steps(command, parameters)
        else:
            # General automation steps
            steps = [
                TaskStep(action="analyze_command", parameters={"command": command}),
                TaskStep(action="execute_general_task", parameters=parameters),
                TaskStep(action="compile_results")
            ]
        
        return steps
    
    async def _generate_research_steps(self, command: str, parameters: Dict[str, Any]) -> List[TaskStep]:
        """Generate research automation steps"""
        steps = [
            TaskStep(action="prepare_research", parameters={"query": " ".join(parameters.get("keywords", []))}),
        ]
        
        # Add search steps for multiple sites
        research_sites = ["google.com", "wikipedia.org", "arxiv.org", "scholar.google.com"]
        quantity = min(parameters.get("quantity", 3), 5)  # Max 5 sites
        
        for i in range(quantity):
            site = research_sites[i % len(research_sites)]
            steps.append(TaskStep(
                action="search_site",
                url=f"https://{site}",
                parameters={"query": " ".join(parameters.get("keywords", [])), "site": site}
            ))
        
        steps.extend([
            TaskStep(action="extract_research_data"),
            TaskStep(action="compile_research_report"),
            TaskStep(action="save_results")
        ])
        
        return steps
    
    async def _generate_job_application_steps(self, command: str, parameters: Dict[str, Any]) -> List[TaskStep]:
        """Generate job application automation steps"""
        job_sites = ["linkedin.com", "indeed.com", "glassdoor.com"]
        steps = [
            TaskStep(action="prepare_application_data"),
        ]
        
        for site in job_sites[:parameters.get("quantity", 3)]:
            steps.extend([
                TaskStep(action="navigate_to_job_site", url=f"https://{site}"),
                TaskStep(action="search_jobs", parameters={"site": site}),
                TaskStep(action="apply_to_jobs", parameters={"site": site, "max_applications": 5})
            ])
        
        steps.append(TaskStep(action="compile_application_report"))
        return steps
    
    async def _generate_form_filling_steps(self, command: str, parameters: Dict[str, Any]) -> List[TaskStep]:
        """Generate form filling automation steps"""
        return [
            TaskStep(action="identify_forms", parameters=parameters),
            TaskStep(action="prepare_form_data"),
            TaskStep(action="fill_forms", parameters={"auto_submit": "submit" in command.lower()}),
            TaskStep(action="verify_submissions")
        ]
    
    async def _generate_price_monitoring_steps(self, command: str, parameters: Dict[str, Any]) -> List[TaskStep]:
        """Generate price monitoring automation steps"""
        return [
            TaskStep(action="setup_price_monitoring", parameters=parameters),
            TaskStep(action="extract_current_prices"),
            TaskStep(action="setup_price_alerts"),
            TaskStep(action="schedule_price_checks")
        ]
    
    async def _generate_data_extraction_steps(self, command: str, parameters: Dict[str, Any]) -> List[TaskStep]:
        """Generate data extraction automation steps"""
        return [
            TaskStep(action="identify_data_sources", parameters=parameters),
            TaskStep(action="extract_structured_data"),
            TaskStep(action="clean_and_process_data"),
            TaskStep(action="export_data_results")
        ]
    
    def _determine_priority(self, command: str, step_count: int) -> TaskPriority:
        """Determine task priority based on command and complexity"""
        urgent_keywords = ["urgent", "asap", "immediately", "now", "emergency"]
        high_keywords = ["important", "priority", "quickly", "fast"]
        
        if any(keyword in command for keyword in urgent_keywords):
            return TaskPriority.URGENT
        elif any(keyword in command for keyword in high_keywords) or step_count > 10:
            return TaskPriority.HIGH
        elif step_count > 5:
            return TaskPriority.NORMAL
        else:
            return TaskPriority.LOW

class TaskExecutor:
    """Execute automation tasks in background"""
    
    def __init__(self, mongo_client):
        self.db = mongo_client.aether_browser
        self.active_tasks = {}
        self.task_queue = asyncio.Queue()
        self.executor_running = False
    
    async def start_executor(self):
        """Start the background task executor"""
        if not self.executor_running:
            self.executor_running = True
            asyncio.create_task(self._executor_loop())
            logger.info("Task executor started")
    
    async def stop_executor(self):
        """Stop the background task executor"""
        self.executor_running = False
        logger.info("Task executor stopped")
    
    async def execute_task(self, task: Task) -> str:
        """Queue task for background execution"""
        try:
            # Store task in database
            task_doc = {
                "task_id": task.task_id,
                "command": task.command,
                "steps": [{"action": step.action, "url": step.url, "parameters": step.parameters, "status": step.status} for step in task.steps],
                "context": task.context,
                "priority": task.priority.value,
                "status": task.status.value,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "progress": task.progress,
                "user_session": task.context.get("session_id")
            }
            
            self.db.automation_tasks.insert_one(task_doc)
            
            # Add to active tasks
            self.active_tasks[task.task_id] = task
            
            # Queue for execution
            await self.task_queue.put(task)
            
            logger.info(f"Task {task.task_id} queued for execution")
            return task.task_id
            
        except Exception as e:
            logger.error(f"Error queuing task {task.task_id}: {e}")
            raise
    
    async def _executor_loop(self):
        """Main executor loop for processing tasks"""
        while self.executor_running:
            try:
                # Get next task (with timeout to allow checking if we should stop)
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Execute the task
                await self._execute_single_task(task)
                
            except asyncio.TimeoutError:
                # Timeout is normal, just continue the loop
                continue
            except Exception as e:
                logger.error(f"Error in executor loop: {e}")
                await asyncio.sleep(1)
    
    async def _execute_single_task(self, task: Task):
        """Execute a single automation task"""
        try:
            task.status = TaskStatus.EXECUTING
            await self._update_task_status(task)
            
            logger.info(f"Executing task {task.task_id}: {task.command}")
            
            # Execute each step
            for i, step in enumerate(task.steps):
                if task.status == TaskStatus.CANCELLED:
                    break
                    
                try:
                    step.status = "executing"
                    await self._execute_step(step, task.context)
                    step.status = "completed"
                    
                    # Update progress
                    task.progress = ((i + 1) / len(task.steps)) * 100
                    await self._update_task_status(task)
                    
                    # Simulate step execution time
                    await asyncio.sleep(min(step.expected_duration, 5))  # Max 5 seconds per step in simulation
                    
                except Exception as e:
                    logger.error(f"Error executing step {i} for task {task.task_id}: {e}")
                    step.status = "failed"
                    # Continue with next step
            
            # Mark task as completed
            if task.status != TaskStatus.CANCELLED:
                task.status = TaskStatus.COMPLETED
                task.result = {
                    "message": f"Successfully completed: {task.command}",
                    "steps_completed": sum(1 for step in task.steps if step.status == "completed"),
                    "total_steps": len(task.steps),
                    "execution_time": (datetime.utcnow() - task.created_at).total_seconds()
                }
            
            await self._update_task_status(task)
            logger.info(f"Task {task.task_id} completed with status: {task.status}")
            
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            await self._update_task_status(task)
        
        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    async def _execute_step(self, step: TaskStep, context: Dict[str, Any]):
        """Execute a single task step"""
        try:
            action = step.action
            
            if action == "navigate":
                logger.info(f"Navigating to: {step.url}")
                # Simulate navigation
                await asyncio.sleep(2)
                
            elif action == "search_site":
                site = step.parameters.get("site", "google.com")
                query = step.parameters.get("query", "")
                logger.info(f"Searching {site} for: {query}")
                # Simulate search
                await asyncio.sleep(3)
                
            elif action == "extract_data" or action == "extract_research_data":
                logger.info("Extracting data from page")
                # Simulate data extraction
                await asyncio.sleep(2)
                
            elif action == "fill_form" or action == "fill_forms":
                logger.info("Filling form fields")
                # Simulate form filling
                await asyncio.sleep(4)
                
            elif action == "compile_research_report" or action == "compile_results":
                logger.info("Compiling research report")
                # Simulate report compilation
                await asyncio.sleep(3)
                
            else:
                logger.info(f"Executing generic action: {action}")
                # Generic action simulation
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Error executing step {action}: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        try:
            task_doc = self.db.automation_tasks.find_one({"task_id": task_id}, {"_id": 0})
            if task_doc:
                return task_doc
            return None
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return None
    
    async def get_user_tasks(self, user_session: str) -> Dict[str, Any]:
        """Get all tasks for a user session"""
        try:
            # Get active tasks
            active_tasks = list(self.db.automation_tasks.find(
                {"user_session": user_session, "status": {"$in": ["created", "executing", "parsing"]}},
                {"_id": 0}
            ))
            
            # Get completed tasks (last 10)
            completed_tasks = list(self.db.automation_tasks.find(
                {"user_session": user_session, "status": {"$in": ["completed", "failed", "cancelled"]}},
                {"_id": 0}
            ).sort("updated_at", -1).limit(10))
            
            return {
                "active_tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "total_active": len(active_tasks)
            }
            
        except Exception as e:
            logger.error(f"Error getting user tasks for {user_session}: {e}")
            return {"active_tasks": [], "completed_tasks": [], "total_active": 0}
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = TaskStatus.CANCELLED
                await self._update_task_status(self.active_tasks[task_id])
                return True
            else:
                # Update in database only
                result = self.db.automation_tasks.update_one(
                    {"task_id": task_id},
                    {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
                )
                return result.modified_count > 0
                
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def _update_task_status(self, task: Task):
        """Update task status in database"""
        try:
            task.updated_at = datetime.utcnow()
            
            update_doc = {
                "status": task.status.value,
                "updated_at": task.updated_at,
                "progress": task.progress,
                "steps": [{"action": step.action, "url": step.url, "parameters": step.parameters, "status": step.status} for step in task.steps]
            }
            
            if task.result:
                update_doc["result"] = task.result
            
            self.db.automation_tasks.update_one(
                {"task_id": task.task_id},
                {"$set": update_doc}
            )
            
        except Exception as e:
            logger.error(f"Error updating task status for {task.task_id}: {e}")

# Global instances
nlp_processor = NLPProcessor()
task_executor = None

def initialize_task_executor(mongo_client) -> TaskExecutor:
    """Initialize the global task executor"""
    global task_executor
    task_executor = TaskExecutor(mongo_client)
    asyncio.create_task(task_executor.start_executor())
    return task_executor

def get_task_executor() -> Optional[TaskExecutor]:
    """Get the global task executor instance"""
    return task_executor