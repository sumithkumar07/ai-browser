import asyncio
import json
import uuid
import re
import httpx
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import copy

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class TriggerType(Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT_DRIVEN = "event_driven"
    CONDITIONAL = "conditional"

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    id: str
    name: str
    type: str  # 'action', 'condition', 'loop', 'parallel_group'
    config: Dict[str, Any]
    dependencies: List[str] = None
    retry_config: Dict[str, Any] = None
    timeout_seconds: int = 300
    on_success: str = "continue"  # 'continue', 'jump_to', 'end'
    on_failure: str = "fail"      # 'fail', 'retry', 'continue', 'jump_to'
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.retry_config is None:
            self.retry_config = {"max_retries": 3, "retry_delay": 5}

@dataclass
class WorkflowTrigger:
    """Defines when a workflow should be triggered"""
    type: TriggerType
    config: Dict[str, Any]
    
@dataclass
class WorkflowTemplate:
    """Template for creating workflows"""
    id: str
    name: str
    description: str
    category: str
    steps: List[WorkflowStep]
    triggers: List[WorkflowTrigger]
    variables: Dict[str, Any] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.tags is None:
            self.tags = []

class AdvancedWorkflowEngine:
    """Advanced workflow management system with visual builder, conditional logic, and real-time execution"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        
        # Collections
        self.workflow_templates = self.db.workflow_templates
        self.workflow_instances = self.db.workflow_instances
        self.workflow_executions = self.db.workflow_executions
        self.workflow_schedules = self.db.workflow_schedules
        
        # Runtime state
        self.active_workflows = {}  # workflow_id -> execution context
        self.step_handlers = self._initialize_step_handlers()
        self.condition_evaluators = self._initialize_condition_evaluators()
        
        # Background tasks
        self._scheduler_task = None
        self._monitor_task = None
        
    def start_workflow_engine(self):
        """Start background workflow management tasks"""
        if self._scheduler_task is None:
            try:
                self._scheduler_task = asyncio.create_task(self._workflow_scheduler())
                self._monitor_task = asyncio.create_task(self._workflow_monitor())
            except RuntimeError:
                pass
    
    def _initialize_step_handlers(self) -> Dict[str, Callable]:
        """Initialize handlers for different step types"""
        return {
            "http_request": self._handle_http_request,
            "integration_action": self._handle_integration_action,
            "data_transformation": self._handle_data_transformation,
            "condition": self._handle_condition,
            "loop": self._handle_loop,
            "parallel_group": self._handle_parallel_group,
            "delay": self._handle_delay,
            "notification": self._handle_notification,
            "code_execution": self._handle_code_execution,
            "ai_processing": self._handle_ai_processing,
            "file_operation": self._handle_file_operation,
            "database_operation": self._handle_database_operation
        }
    
    def _initialize_condition_evaluators(self) -> Dict[str, Callable]:
        """Initialize condition evaluators"""
        return {
            "equals": lambda a, b: a == b,
            "not_equals": lambda a, b: a != b,
            "greater_than": lambda a, b: float(a) > float(b),
            "less_than": lambda a, b: float(a) < float(b),
            "contains": lambda a, b: str(b) in str(a),
            "starts_with": lambda a, b: str(a).startswith(str(b)),
            "ends_with": lambda a, b: str(a).endswith(str(b)),
            "is_empty": lambda a, _: not bool(a),
            "is_not_empty": lambda a, _: bool(a),
            "regex_match": lambda a, b: bool(re.match(str(b), str(a))),
        }
    
    async def create_workflow_template(self, template_data: Dict[str, Any], user_session: str) -> str:
        """Create a new workflow template"""
        
        template_id = str(uuid.uuid4())
        
        # Parse and validate steps
        steps = []
        for step_data in template_data.get("steps", []):
            step = WorkflowStep(
                id=step_data.get("id", str(uuid.uuid4())),
                name=step_data["name"],
                type=step_data["type"],
                config=step_data.get("config", {}),
                dependencies=step_data.get("dependencies", []),
                retry_config=step_data.get("retry_config"),
                timeout_seconds=step_data.get("timeout_seconds", 300),
                on_success=step_data.get("on_success", "continue"),
                on_failure=step_data.get("on_failure", "fail")
            )
            steps.append(step)
        
        # Parse triggers
        triggers = []
        for trigger_data in template_data.get("triggers", []):
            trigger = WorkflowTrigger(
                type=TriggerType(trigger_data["type"]),
                config=trigger_data.get("config", {})
            )
            triggers.append(trigger)
        
        # Create template
        template = WorkflowTemplate(
            id=template_id,
            name=template_data["name"],
            description=template_data.get("description", ""),
            category=template_data.get("category", "custom"),
            steps=steps,
            triggers=triggers,
            variables=template_data.get("variables", {}),
            tags=template_data.get("tags", [])
        )
        
        # Store in database
        template_doc = {
            "template_id": template_id,
            "user_session": user_session,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **asdict(template)
        }
        
        # Convert dataclass instances to dicts for storage
        template_doc["steps"] = [asdict(step) for step in template.steps]
        template_doc["triggers"] = [asdict(trigger) for trigger in template.triggers]
        
        self.workflow_templates.insert_one(template_doc)
        
        logger.info(f"Created workflow template {template_id}: {template.name}")
        return template_id
    
    async def create_workflow_instance(self, template_id: str, user_session: str, 
                                     parameters: Dict[str, Any] = None) -> str:
        """Create a workflow instance from a template"""
        
        # Get template
        template_doc = self.workflow_templates.find_one({"template_id": template_id})
        if not template_doc:
            raise ValueError(f"Workflow template {template_id} not found")
        
        instance_id = str(uuid.uuid4())
        
        # Merge parameters with template variables
        variables = copy.deepcopy(template_doc["variables"])
        if parameters:
            variables.update(parameters)
        
        # Create instance
        instance = {
            "instance_id": instance_id,
            "template_id": template_id,
            "user_session": user_session,
            "name": template_doc["name"],
            "description": template_doc["description"],
            "status": WorkflowStatus.DRAFT.value,
            "variables": variables,
            "steps": copy.deepcopy(template_doc["steps"]),
            "triggers": copy.deepcopy(template_doc["triggers"]),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "execution_count": 0,
            "last_execution": None
        }
        
        self.workflow_instances.insert_one(instance)
        
        logger.info(f"Created workflow instance {instance_id} from template {template_id}")
        return instance_id
    
    async def execute_workflow(self, instance_id: str, trigger_data: Dict[str, Any] = None) -> str:
        """Execute a workflow instance"""
        
        # Get instance
        instance = self.workflow_instances.find_one({"instance_id": instance_id})
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")
        
        execution_id = str(uuid.uuid4())
        
        # Create execution record
        execution = {
            "execution_id": execution_id,
            "instance_id": instance_id,
            "user_session": instance["user_session"],
            "status": WorkflowStatus.ACTIVE.value,
            "trigger_data": trigger_data or {},
            "variables": copy.deepcopy(instance["variables"]),
            "step_results": {},
            "error_log": [],
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "execution_time_seconds": 0
        }
        
        self.workflow_executions.insert_one(execution)
        
        # Update instance
        self.workflow_instances.update_one(
            {"instance_id": instance_id},
            {
                "$set": {
                    "status": WorkflowStatus.ACTIVE.value,
                    "last_execution": execution_id,
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"execution_count": 1}
            }
        )
        
        # Start execution in background
        asyncio.create_task(self._execute_workflow_steps(execution_id, instance["steps"]))
        
        logger.info(f"Started workflow execution {execution_id}")
        return execution_id
    
    async def _execute_workflow_steps(self, execution_id: str, steps: List[Dict[str, Any]]):
        """Execute workflow steps"""
        
        try:
            # Get execution context
            execution = self.workflow_executions.find_one({"execution_id": execution_id})
            if not execution:
                return
            
            self.active_workflows[execution_id] = {
                "execution": execution,
                "current_step": 0,
                "step_contexts": {}
            }
            
            # Execute steps
            step_index = 0
            while step_index < len(steps):
                step = steps[step_index]
                
                # Check if execution was cancelled
                if self._is_execution_cancelled(execution_id):
                    break
                
                # Check dependencies
                if not await self._check_step_dependencies(execution_id, step):
                    step_index += 1
                    continue
                
                # Execute step
                try:
                    result = await self._execute_step(execution_id, step)
                    
                    # Handle step result
                    next_step = await self._handle_step_result(execution_id, step, result)
                    
                    if next_step == "end":
                        break
                    elif next_step.isdigit():
                        step_index = int(next_step)
                    else:
                        step_index += 1
                        
                except Exception as e:
                    await self._handle_step_error(execution_id, step, e)
                    
                    # Check failure handling
                    if step.get("on_failure") == "fail":
                        break
                    elif step.get("on_failure") == "continue":
                        step_index += 1
                    # Add other failure handling logic
            
            # Complete execution
            await self._complete_workflow_execution(execution_id)
            
        except Exception as e:
            logger.error(f"Workflow execution {execution_id} failed: {e}")
            await self._fail_workflow_execution(execution_id, str(e))
        
        finally:
            # Cleanup
            if execution_id in self.active_workflows:
                del self.active_workflows[execution_id]
    
    async def _execute_step(self, execution_id: str, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        step_type = step["type"]
        step_config = step["config"]
        
        # Update step status
        await self._update_step_status(execution_id, step["id"], StepStatus.RUNNING)
        
        # Get step handler
        handler = self.step_handlers.get(step_type)
        if not handler:
            raise ValueError(f"Unknown step type: {step_type}")
        
        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                handler(execution_id, step_config),
                timeout=step.get("timeout_seconds", 300)
            )
            
            await self._update_step_status(execution_id, step["id"], StepStatus.COMPLETED)
            await self._store_step_result(execution_id, step["id"], result)
            
            return result
            
        except asyncio.TimeoutError:
            await self._update_step_status(execution_id, step["id"], StepStatus.FAILED)
            raise Exception(f"Step {step['name']} timed out")
        
        except Exception as e:
            await self._update_step_status(execution_id, step["id"], StepStatus.FAILED)
            raise e
    
    # Step handlers
    
    async def _handle_http_request(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HTTP request step"""
        
        url = config["url"]
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        data = config.get("data")
        
        # Replace variables in URL and data
        url = self._replace_variables(execution_id, url)
        if data:
            data = self._replace_variables(execution_id, json.dumps(data))
            data = json.loads(data)
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            }
    
    async def _handle_integration_action(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle integration action step"""
        
        # This would integrate with the enhanced integration manager
        integration_id = config["integration_id"]
        action = config["action"]
        parameters = config.get("parameters", {})
        
        # Replace variables in parameters
        parameters_json = self._replace_variables(execution_id, json.dumps(parameters))
        parameters = json.loads(parameters_json)
        
        # Execute integration action (placeholder)
        return {
            "integration_id": integration_id,
            "action": action,
            "result": "executed",
            "parameters": parameters
        }
    
    async def _handle_condition(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle condition evaluation step"""
        
        left_value = self._replace_variables(execution_id, str(config["left_value"]))
        operator = config["operator"]
        right_value = self._replace_variables(execution_id, str(config["right_value"]))
        
        evaluator = self.condition_evaluators.get(operator)
        if not evaluator:
            raise ValueError(f"Unknown condition operator: {operator}")
        
        result = evaluator(left_value, right_value)
        
        return {
            "condition_result": result,
            "left_value": left_value,
            "operator": operator,
            "right_value": right_value
        }
    
    async def _handle_loop(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle loop step"""
        
        loop_type = config.get("type", "count")  # 'count', 'while', 'for_each'
        
        if loop_type == "count":
            count = int(self._replace_variables(execution_id, str(config["count"])))
            results = []
            
            for i in range(count):
                # Set loop variable
                self._set_variable(execution_id, "loop_index", i)
                
                # Execute loop body steps
                body_steps = config.get("body_steps", [])
                for step in body_steps:
                    step_result = await self._execute_step(execution_id, step)
                    results.append(step_result)
            
            return {"loop_results": results, "iterations": count}
        
        # Add other loop types as needed
        return {"loop_type": loop_type, "result": "completed"}
    
    async def _handle_parallel_group(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle parallel execution of steps"""
        
        parallel_steps = config.get("steps", [])
        
        # Execute all steps in parallel
        tasks = [self._execute_step(execution_id, step) for step in parallel_steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "step_index": i,
                    "error": str(result)
                })
            else:
                successful_results.append({
                    "step_index": i,
                    "result": result
                })
        
        return {
            "successful_results": successful_results,
            "errors": errors,
            "total_steps": len(parallel_steps)
        }
    
    async def _handle_delay(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delay/wait step"""
        
        delay_seconds = int(self._replace_variables(execution_id, str(config["seconds"])))
        await asyncio.sleep(delay_seconds)
        
        return {"delayed_seconds": delay_seconds}
    
    async def _handle_ai_processing(self, execution_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AI processing step"""
        
        # This would integrate with the enhanced AI manager
        prompt = self._replace_variables(execution_id, config["prompt"])
        model_type = config.get("model_type", "general")
        
        # Simulate AI processing
        return {
            "prompt": prompt,
            "model_type": model_type,
            "ai_response": f"AI processed: {prompt[:100]}...",
            "processing_time": 2.5
        }
    
    # Utility methods
    
    def _replace_variables(self, execution_id: str, text: str) -> str:
        """Replace variables in text with actual values"""
        
        if execution_id not in self.active_workflows:
            return text
        
        execution = self.active_workflows[execution_id]["execution"]
        variables = execution["variables"]
        
        # Simple variable replacement
        for var_name, var_value in variables.items():
            placeholder = f"${{{var_name}}}"
            text = text.replace(placeholder, str(var_value))
        
        # Add step result variables
        step_results = execution.get("step_results", {})
        for step_id, result in step_results.items():
            if isinstance(result, dict):
                for key, value in result.items():
                    placeholder = f"${{{step_id}.{key}}}"
                    text = text.replace(placeholder, str(value))
        
        return text
    
    def _set_variable(self, execution_id: str, var_name: str, var_value: Any):
        """Set a variable in the execution context"""
        
        if execution_id in self.active_workflows:
            self.active_workflows[execution_id]["execution"]["variables"][var_name] = var_value
            
            # Also update in database
            self.workflow_executions.update_one(
                {"execution_id": execution_id},
                {"$set": {f"variables.{var_name}": var_value}}
            )
    
    async def _check_step_dependencies(self, execution_id: str, step: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        
        dependencies = step.get("dependencies", [])
        if not dependencies:
            return True
        
        execution = self.workflow_executions.find_one({"execution_id": execution_id})
        if not execution:
            return False
        
        step_results = execution.get("step_results", {})
        
        # Check if all dependencies are completed
        for dep_id in dependencies:
            if dep_id not in step_results:
                return False
        
        return True
    
    async def _update_step_status(self, execution_id: str, step_id: str, status: StepStatus):
        """Update step status"""
        
        self.workflow_executions.update_one(
            {"execution_id": execution_id},
            {"$set": {f"step_statuses.{step_id}": status.value}}
        )
    
    async def _store_step_result(self, execution_id: str, step_id: str, result: Dict[str, Any]):
        """Store step execution result"""
        
        self.workflow_executions.update_one(
            {"execution_id": execution_id},
            {"$set": {f"step_results.{step_id}": result}}
        )
        
        # Update in-memory context
        if execution_id in self.active_workflows:
            self.active_workflows[execution_id]["execution"]["step_results"][step_id] = result
    
    async def _handle_step_result(self, execution_id: str, step: Dict[str, Any], result: Dict[str, Any]) -> str:
        """Handle step result and determine next step"""
        
        on_success = step.get("on_success", "continue")
        
        # For condition steps, check result
        if step["type"] == "condition":
            condition_result = result.get("condition_result", False)
            if condition_result:
                return step.get("on_true", "continue")
            else:
                return step.get("on_false", "continue")
        
        return on_success
    
    async def _handle_step_error(self, execution_id: str, step: Dict[str, Any], error: Exception):
        """Handle step execution error"""
        
        error_info = {
            "step_id": step["id"],
            "step_name": step["name"],
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log error
        self.workflow_executions.update_one(
            {"execution_id": execution_id},
            {"$push": {"error_log": error_info}}
        )
        
        logger.error(f"Step {step['name']} failed in execution {execution_id}: {error}")
    
    def _is_execution_cancelled(self, execution_id: str) -> bool:
        """Check if execution was cancelled"""
        
        execution = self.workflow_executions.find_one(
            {"execution_id": execution_id},
            {"status": 1}
        )
        
        return execution and execution["status"] == WorkflowStatus.CANCELLED.value
    
    async def _complete_workflow_execution(self, execution_id: str):
        """Complete workflow execution"""
        
        end_time = datetime.utcnow()
        
        # Get start time
        execution = self.workflow_executions.find_one({"execution_id": execution_id})
        start_time = execution["started_at"]
        execution_time = (end_time - start_time).total_seconds()
        
        # Update execution
        self.workflow_executions.update_one(
            {"execution_id": execution_id},
            {
                "$set": {
                    "status": WorkflowStatus.COMPLETED.value,
                    "completed_at": end_time,
                    "execution_time_seconds": execution_time
                }
            }
        )
        
        logger.info(f"Workflow execution {execution_id} completed in {execution_time:.2f}s")
    
    async def _fail_workflow_execution(self, execution_id: str, error: str):
        """Mark workflow execution as failed"""
        
        end_time = datetime.utcnow()
        
        self.workflow_executions.update_one(
            {"execution_id": execution_id},
            {
                "$set": {
                    "status": WorkflowStatus.FAILED.value,
                    "completed_at": end_time,
                    "final_error": error
                }
            }
        )
        
        logger.error(f"Workflow execution {execution_id} failed: {error}")
    
    # Background tasks
    
    async def _workflow_scheduler(self):
        """Background workflow scheduler"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check for scheduled workflows
                current_time = datetime.utcnow()
                
                # Find workflows that should be triggered
                scheduled_workflows = self.workflow_schedules.find({
                    "next_run": {"$lte": current_time},
                    "active": True
                })
                
                for schedule in scheduled_workflows:
                    try:
                        # Execute workflow
                        await self.execute_workflow(
                            schedule["instance_id"],
                            {"trigger": "scheduled", "schedule_id": schedule["_id"]}
                        )
                        
                        # Update next run time
                        self._update_next_run_time(schedule)
                        
                    except Exception as e:
                        logger.error(f"Failed to execute scheduled workflow {schedule['instance_id']}: {e}")
                
            except Exception as e:
                logger.error(f"Workflow scheduler error: {e}")
    
    async def _workflow_monitor(self):
        """Background workflow monitoring"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Monitor active executions
                active_executions = self.workflow_executions.find({
                    "status": WorkflowStatus.ACTIVE.value
                })
                
                for execution in active_executions:
                    execution_id = execution["execution_id"]
                    
                    # Check for stuck executions
                    start_time = execution["started_at"]
                    if datetime.utcnow() - start_time > timedelta(hours=1):  # 1 hour timeout
                        await self._fail_workflow_execution(
                            execution_id, 
                            "Execution timeout - exceeded 1 hour limit"
                        )
                
            except Exception as e:
                logger.error(f"Workflow monitor error: {e}")
    
    # Public API methods
    
    async def get_workflow_templates(self, user_session: str = None, category: str = None) -> List[Dict[str, Any]]:
        """Get workflow templates"""
        
        query = {}
        if user_session:
            query["user_session"] = user_session
        if category:
            query["category"] = category
        
        templates = list(self.workflow_templates.find(query, {"_id": 0}).sort("created_at", -1))
        return templates
    
    async def get_workflow_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        
        execution = self.workflow_executions.find_one(
            {"execution_id": execution_id},
            {"_id": 0}
        )
        
        if execution:
            # Convert datetime objects
            if execution.get("started_at"):
                execution["started_at"] = execution["started_at"].isoformat()
            if execution.get("completed_at"):
                execution["completed_at"] = execution["completed_at"].isoformat()
        
        return execution
    
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        
        result = self.workflow_executions.update_one(
            {"execution_id": execution_id, "status": WorkflowStatus.ACTIVE.value},
            {"$set": {"status": WorkflowStatus.CANCELLED.value, "completed_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0

# Global advanced workflow engine instance
advanced_workflow_engine = None  # Will be initialized in server.py