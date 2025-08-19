import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
import logging
from .base_agent import BaseAgent, AgentTask, TaskPriority, AgentCapability, AgentStatus

class ExecutionPlan(BaseModel):
    id: str
    description: str
    steps: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]
    estimated_time: float
    priority: TaskPriority
    created_at: datetime

class CoordinationAgent(BaseAgent):
    """Coordinates and orchestrates multiple agents for complex tasks"""
    
    def __init__(self):
        super().__init__(
            agent_id="coordinator",
            name="Coordination Agent",
            description="Orchestrates multi-agent workflows and task distribution"
        )
        
        # Agent registry
        self.registered_agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, List[AgentCapability]] = {}
        
        # Task management
        self.pending_tasks: List[AgentTask] = []
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        
        # Workflow management
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.task_routing_history: List[Dict[str, Any]] = []
        
    async def initialize(self) -> bool:
        """Initialize the coordination agent"""
        try:
            await self.update_memory("initialization_time", datetime.now().isoformat())
            self.logger.info("Coordination Agent initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize coordination agent: {e}")
            return False
    
    async def register_agent(self, agent: BaseAgent) -> bool:
        """Register a new agent with the coordinator"""
        try:
            agent.coordinator = self
            self.registered_agents[agent.agent_id] = agent
            
            # Get agent capabilities
            capabilities = await agent.get_capabilities()
            self.agent_capabilities[agent.agent_id] = capabilities
            
            self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent"""
        try:
            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]
                await agent.shutdown()
                del self.registered_agents[agent_id]
                
                if agent_id in self.agent_capabilities:
                    del self.agent_capabilities[agent_id]
                
                self.logger.info(f"Unregistered agent: {agent_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a coordination task"""
        if task.type == "complex_workflow":
            return await self._execute_complex_workflow(task)
        elif task.type == "task_distribution":
            return await self._distribute_tasks(task)
        elif task.type == "agent_optimization":
            return await self._optimize_agent_allocation(task)
        else:
            return {"error": f"Unknown coordination task type: {task.type}"}
    
    async def get_capabilities(self) -> List[AgentCapability]:
        """Return coordination agent capabilities"""
        return [
            AgentCapability(
                name="Complex Workflow Execution",
                description="Orchestrate multi-step workflows across multiple agents",
                input_types=["complex_workflow"],
                output_types=["workflow_result"],
                estimated_time=10.0,
                success_rate=0.95
            ),
            AgentCapability(
                name="Task Distribution",
                description="Distribute tasks optimally across available agents",
                input_types=["task_distribution"],
                output_types=["distribution_result"],
                estimated_time=2.0,
                success_rate=0.98
            ),
            AgentCapability(
                name="Agent Optimization",
                description="Analyze and optimize agent performance and allocation",
                input_types=["agent_optimization"],
                output_types=["optimization_result"],
                estimated_time=5.0,
                success_rate=0.90
            )
        ]
    
    async def create_execution_plan(self, task_description: str, 
                                  requirements: Dict[str, Any]) -> ExecutionPlan:
        """Create an execution plan for a complex task"""
        
        plan_id = str(uuid.uuid4())
        
        # Analyze task and break it down
        steps = await self._analyze_and_decompose_task(task_description, requirements)
        
        # Identify dependencies between steps
        dependencies = await self._identify_dependencies(steps)
        
        # Estimate total execution time
        estimated_time = await self._estimate_execution_time(steps)
        
        # Determine priority
        priority = TaskPriority(requirements.get("priority", TaskPriority.MEDIUM.value))
        
        plan = ExecutionPlan(
            id=plan_id,
            description=task_description,
            steps=steps,
            dependencies=dependencies,
            estimated_time=estimated_time,
            priority=priority,
            created_at=datetime.now()
        )
        
        self.execution_plans[plan_id] = plan
        
        self.logger.info(f"Created execution plan {plan_id} with {len(steps)} steps")
        return plan
    
    async def _analyze_and_decompose_task(self, description: str, 
                                        requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Break down complex task into manageable steps"""
        
        # Simple task decomposition logic (can be enhanced with ML)
        steps = []
        
        # Analyze task type
        if "research" in description.lower():
            steps.extend([
                {
                    "id": f"step_{len(steps) + 1}",
                    "type": "web_research",
                    "description": "Gather relevant information from web sources",
                    "agent_type": "research_agent",
                    "estimated_time": 5.0,
                    "inputs": {"query": description}
                },
                {
                    "id": f"step_{len(steps) + 1}",
                    "type": "analyze_data",
                    "description": "Analyze and synthesize gathered information",
                    "agent_type": "analysis_agent",
                    "estimated_time": 3.0,
                    "inputs": {"data_source": "step_1"}
                }
            ])
        
        if "automation" in description.lower():
            steps.extend([
                {
                    "id": f"step_{len(steps) + 1}",
                    "type": "create_automation",
                    "description": "Create automation workflow",
                    "agent_type": "automation_agent",
                    "estimated_time": 4.0,
                    "inputs": {"task_description": description}
                },
                {
                    "id": f"step_{len(steps) + 1}",
                    "type": "test_automation",
                    "description": "Test and validate automation",
                    "agent_type": "automation_agent",
                    "estimated_time": 2.0,
                    "inputs": {"workflow_source": f"step_{len(steps)}"}
                }
            ])
        
        if "analysis" in description.lower():
            steps.append({
                "id": f"step_{len(steps) + 1}",
                "type": "deep_analysis",
                "description": "Perform comprehensive analysis",
                "agent_type": "analysis_agent",
                "estimated_time": 6.0,
                "inputs": {"analysis_target": requirements.get("target")}
            })
        
        # Default fallback
        if not steps:
            steps.append({
                "id": "step_1",
                "type": "general_task",
                "description": description,
                "agent_type": "general_agent",
                "estimated_time": 3.0,
                "inputs": requirements
            })
        
        return steps
    
    async def _identify_dependencies(self, steps: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Identify dependencies between execution steps"""
        dependencies = {}
        
        for i, step in enumerate(steps):
            step_id = step["id"]
            deps = []
            
            # Check if step depends on previous steps
            if "inputs" in step:
                for input_key, input_value in step["inputs"].items():
                    if isinstance(input_value, str) and input_value.startswith("step_"):
                        deps.append(input_value)
            
            # Sequential dependency (each step depends on previous by default)
            if i > 0:
                prev_step_id = steps[i-1]["id"]
                if prev_step_id not in deps:
                    deps.append(prev_step_id)
            
            dependencies[step_id] = deps
        
        return dependencies
    
    async def _estimate_execution_time(self, steps: List[Dict[str, Any]]) -> float:
        """Estimate total execution time for steps"""
        total_time = 0.0
        
        # Simple sequential estimation (can be enhanced for parallel execution)
        for step in steps:
            total_time += step.get("estimated_time", 3.0)
        
        # Add coordination overhead (10%)
        total_time *= 1.1
        
        return total_time
    
    async def find_best_agent_for_task(self, task: AgentTask) -> Optional[BaseAgent]:
        """Find the best available agent for a task"""
        best_agent = None
        best_score = 0.0
        
        for agent_id, agent in self.registered_agents.items():
            if agent.status == AgentStatus.IDLE:
                score = await agent.can_handle_task(task)
                
                # Adjust score based on agent performance history
                agent_stats = await agent.get_status()
                performance_multiplier = min(agent_stats["success_rate"] + 0.5, 1.0)
                adjusted_score = score * performance_multiplier
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_agent = agent
        
        return best_agent
    
    async def assign_task_to_agent(self, task: AgentTask, agent_id: Optional[str] = None) -> bool:
        """Assign a task to a specific agent or find the best one"""
        
        if agent_id and agent_id in self.registered_agents:
            agent = self.registered_agents[agent_id]
        else:
            agent = await self.find_best_agent_for_task(task)
        
        if not agent:
            self.logger.warning(f"No available agent found for task {task.id}")
            return False
        
        success = await agent.start_task(task)
        
        if success:
            # Record routing decision for learning
            routing_record = {
                "task_id": task.id,
                "task_type": task.type,
                "assigned_agent": agent.agent_id,
                "timestamp": datetime.now().isoformat(),
                "success": None  # Will be updated when task completes
            }
            self.task_routing_history.append(routing_record)
            
            self.logger.info(f"Assigned task {task.id} to agent {agent.agent_id}")
        
        return success
    
    async def _execute_complex_workflow(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a complex multi-agent workflow"""
        workflow_id = str(uuid.uuid4())
        
        try:
            # Create execution plan
            plan = await self.create_execution_plan(
                task.description,
                task.payload
            )
            
            # Initialize workflow state
            workflow_state = {
                "id": workflow_id,
                "plan_id": plan.id,
                "status": "running",
                "completed_steps": [],
                "failed_steps": [],
                "step_results": {},
                "start_time": datetime.now(),
                "end_time": None
            }
            
            self.active_workflows[workflow_id] = workflow_state
            
            # Execute steps
            for step in plan.steps:
                # Check dependencies
                dependencies_met = await self._check_step_dependencies(
                    step, plan.dependencies, workflow_state
                )
                
                if not dependencies_met:
                    self.logger.error(f"Dependencies not met for step {step['id']}")
                    workflow_state["failed_steps"].append(step["id"])
                    continue
                
                # Create task for step
                step_task = AgentTask(
                    id=str(uuid.uuid4()),
                    type=step["type"],
                    description=step["description"],
                    priority=plan.priority,
                    payload=step.get("inputs", {}),
                    created_at=datetime.now()
                )
                
                # Execute step
                success = await self.assign_task_to_agent(step_task)
                
                if success:
                    # Wait for completion (simplified - should handle async better)
                    await self._wait_for_task_completion(step_task, timeout=30)
                    
                    if step_task.status == "completed":
                        workflow_state["completed_steps"].append(step["id"])
                        workflow_state["step_results"][step["id"]] = step_task.result
                    else:
                        workflow_state["failed_steps"].append(step["id"])
                else:
                    workflow_state["failed_steps"].append(step["id"])
            
            # Finalize workflow
            workflow_state["end_time"] = datetime.now()
            workflow_state["status"] = "completed" if not workflow_state["failed_steps"] else "partial"
            
            return {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "completed_steps": len(workflow_state["completed_steps"]),
                "failed_steps": len(workflow_state["failed_steps"]),
                "results": workflow_state["step_results"],
                "execution_time": (workflow_state["end_time"] - workflow_state["start_time"]).total_seconds()
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {"error": str(e), "workflow_id": workflow_id}
    
    async def _check_step_dependencies(self, step: Dict[str, Any], 
                                     dependencies: Dict[str, List[str]],
                                     workflow_state: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        step_id = step["id"]
        required_deps = dependencies.get(step_id, [])
        
        for dep_id in required_deps:
            if dep_id not in workflow_state["completed_steps"]:
                return False
        
        return True
    
    async def _wait_for_task_completion(self, task: AgentTask, timeout: int = 30):
        """Wait for task completion with timeout"""
        start_time = datetime.now()
        
        while task.status in ["pending", "running"]:
            if (datetime.now() - start_time).seconds > timeout:
                break
            await asyncio.sleep(1)
    
    async def task_completed(self, task: AgentTask, agent: BaseAgent):
        """Handle task completion notification from agent"""
        # Update routing history
        for record in self.task_routing_history:
            if record["task_id"] == task.id:
                record["success"] = True
                break
        
        self.logger.info(f"Task {task.id} completed by agent {agent.agent_id}")
    
    async def task_failed(self, task: AgentTask, agent: BaseAgent, error: str):
        """Handle task failure notification from agent"""
        # Update routing history
        for record in self.task_routing_history:
            if record["task_id"] == task.id:
                record["success"] = False
                record["error"] = error
                break
        
        self.logger.error(f"Task {task.id} failed on agent {agent.agent_id}: {error}")
    
    async def route_message(self, sender_id: str, recipient_id: str, message: Dict[str, Any]):
        """Route message between agents"""
        if recipient_id in self.registered_agents:
            recipient = self.registered_agents[recipient_id]
            await recipient.receive_message(sender_id, message)
        else:
            self.logger.warning(f"Cannot route message: recipient {recipient_id} not found")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        agent_statuses = {}
        
        for agent_id, agent in self.registered_agents.items():
            agent_statuses[agent_id] = await agent.get_status()
        
        return {
            "coordinator_status": await self.get_status(),
            "registered_agents": len(self.registered_agents),
            "active_workflows": len(self.active_workflows),
            "execution_plans": len(self.execution_plans),
            "agent_statuses": agent_statuses,
            "routing_history_size": len(self.task_routing_history)
        }