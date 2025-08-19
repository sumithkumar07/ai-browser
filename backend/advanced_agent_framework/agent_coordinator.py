"""
Advanced Multi-Agent Coordinator for AETHER
Orchestrates complex agent collaborations and task distribution
"""

import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    COORDINATING = "coordinating"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class AgentCapability:
    name: str
    description: str
    proficiency: float  # 0.0 to 1.0
    cost: int  # Resource cost
    estimated_time: int  # Seconds

@dataclass
class Task:
    id: str
    type: str
    description: str
    priority: TaskPriority
    requirements: List[str]
    input_data: Dict[str, Any]
    dependencies: List[str]
    deadline: Optional[datetime] = None
    estimated_duration: int = 300  # 5 minutes default
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Agent:
    id: str
    name: str
    type: str
    capabilities: List[AgentCapability]
    status: AgentStatus
    current_task: Optional[str] = None
    performance_score: float = 1.0
    total_tasks_completed: int = 0
    average_completion_time: float = 300.0
    last_activity: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.last_activity is None:
            self.last_activity = datetime.now()

class AgentCoordinator:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.completed_tasks: List[str] = []
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, Any] = {}
        self.logger = logging.getLogger("AgentCoordinator")
        
        # Advanced coordination features
        self.agent_relationships: Dict[str, List[str]] = {}  # Agent compatibility
        self.learning_system = AgentLearningSystem()
        self.load_balancer = AgentLoadBalancer()
        
    async def register_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent with the coordinator"""
        try:
            agent_id = agent_config.get("id") or str(uuid.uuid4())
            
            # Create capabilities from config
            capabilities = []
            for cap_config in agent_config.get("capabilities", []):
                capability = AgentCapability(
                    name=cap_config["name"],
                    description=cap_config.get("description", ""),
                    proficiency=cap_config.get("proficiency", 0.8),
                    cost=cap_config.get("cost", 1),
                    estimated_time=cap_config.get("estimated_time", 300)
                )
                capabilities.append(capability)
            
            agent = Agent(
                id=agent_id,
                name=agent_config["name"],
                type=agent_config["type"],
                capabilities=capabilities,
                status=AgentStatus.IDLE,
                metadata=agent_config.get("metadata", {})
            )
            
            self.agents[agent_id] = agent
            
            # Initialize relationships
            self.agent_relationships[agent_id] = []
            
            # Update load balancer
            await self.load_balancer.register_agent(agent)
            
            self.logger.info(f"Agent {agent.name} ({agent_id}) registered successfully")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "agent": asdict(agent),
                "message": "Agent registered successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def submit_task(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a new task for agent execution"""
        try:
            task_id = task_config.get("id") or str(uuid.uuid4())
            
            # Parse deadline if provided
            deadline = None
            if task_config.get("deadline"):
                if isinstance(task_config["deadline"], str):
                    deadline = datetime.fromisoformat(task_config["deadline"])
                else:
                    deadline = task_config["deadline"]
            
            task = Task(
                id=task_id,
                type=task_config["type"],
                description=task_config["description"],
                priority=TaskPriority(task_config.get("priority", 2)),
                requirements=task_config.get("requirements", []),
                input_data=task_config.get("input_data", {}),
                dependencies=task_config.get("dependencies", []),
                deadline=deadline,
                estimated_duration=task_config.get("estimated_duration", 300)
            )
            
            self.tasks[task_id] = task
            
            # Check if task can be executed immediately
            suitable_agents = await self.find_suitable_agents(task)
            
            if suitable_agents:
                # Schedule task execution
                await self.schedule_task_execution(task_id)
                status = "scheduled"
            else:
                # Add to queue
                self.task_queue.append(task_id)
                status = "queued"
            
            return {
                "success": True,
                "task_id": task_id,
                "status": status,
                "suitable_agents": len(suitable_agents),
                "estimated_start": self.estimate_task_start_time(task_id)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def find_suitable_agents(self, task: Task) -> List[str]:
        """Find agents suitable for executing a task"""
        suitable_agents = []
        
        for agent_id, agent in self.agents.items():
            if agent.status != AgentStatus.IDLE:
                continue
            
            # Check if agent has required capabilities
            agent_capability_names = [cap.name for cap in agent.capabilities]
            has_required_capabilities = all(
                req in agent_capability_names for req in task.requirements
            )
            
            if has_required_capabilities:
                # Calculate suitability score
                score = self.calculate_agent_suitability(agent, task)
                suitable_agents.append((agent_id, score))
        
        # Sort by suitability score (descending)
        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, score in suitable_agents]

    def calculate_agent_suitability(self, agent: Agent, task: Task) -> float:
        """Calculate how suitable an agent is for a task"""
        score = 0.0
        
        # Base score from performance
        score += agent.performance_score * 0.4
        
        # Capability proficiency score
        relevant_capabilities = [
            cap for cap in agent.capabilities 
            if cap.name in task.requirements
        ]
        
        if relevant_capabilities:
            avg_proficiency = sum(cap.proficiency for cap in relevant_capabilities) / len(relevant_capabilities)
            score += avg_proficiency * 0.3
        
        # Time efficiency score
        if agent.average_completion_time > 0:
            time_efficiency = min(task.estimated_duration / agent.average_completion_time, 2.0)
            score += time_efficiency * 0.2
        
        # Workload consideration
        workload_factor = 1.0  # Agent is idle, so full capacity
        score += workload_factor * 0.1
        
        return min(score, 1.0)

    async def schedule_task_execution(self, task_id: str) -> Dict[str, Any]:
        """Schedule a task for execution"""
        try:
            task = self.tasks[task_id]
            suitable_agents = await self.find_suitable_agents(task)
            
            if not suitable_agents:
                return {"success": False, "error": "No suitable agents available"}
            
            # Select best agent
            selected_agent_id = suitable_agents[0]
            agent = self.agents[selected_agent_id]
            
            # Check if task requires collaboration
            if len(task.requirements) > 2 or task.priority == TaskPriority.CRITICAL:
                return await self.create_collaboration(task_id, suitable_agents[:3])
            
            # Single agent execution
            return await self.assign_task_to_agent(task_id, selected_agent_id)
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def assign_task_to_agent(self, task_id: str, agent_id: str) -> Dict[str, Any]:
        """Assign a task to a specific agent"""
        try:
            task = self.tasks[task_id]
            agent = self.agents[agent_id]
            
            # Update agent status
            agent.status = AgentStatus.BUSY
            agent.current_task = task_id
            agent.last_activity = datetime.now()
            
            # Start task execution
            execution_result = await self.execute_task(task_id, agent_id)
            
            return {
                "success": True,
                "task_id": task_id,
                "agent_id": agent_id,
                "execution_result": execution_result,
                "assigned_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_collaboration(self, task_id: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Create a collaborative execution for complex tasks"""
        try:
            collaboration_id = str(uuid.uuid4())
            task = self.tasks[task_id]
            
            # Create collaboration configuration
            collaboration = {
                "id": collaboration_id,
                "task_id": task_id,
                "agent_ids": agent_ids,
                "type": "parallel" if task.priority >= TaskPriority.HIGH else "sequential",
                "created_at": datetime.now(),
                "status": "active",
                "coordination_strategy": self.determine_coordination_strategy(task, agent_ids),
                "communication_channels": {}
            }
            
            self.active_collaborations[collaboration_id] = collaboration
            
            # Update agent statuses
            for agent_id in agent_ids:
                agent = self.agents[agent_id]
                agent.status = AgentStatus.COORDINATING
                agent.current_task = task_id
            
            # Start collaborative execution
            execution_result = await self.execute_collaborative_task(collaboration_id)
            
            return {
                "success": True,
                "collaboration_id": collaboration_id,
                "task_id": task_id,
                "participating_agents": len(agent_ids),
                "coordination_strategy": collaboration["coordination_strategy"],
                "execution_result": execution_result
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def determine_coordination_strategy(self, task: Task, agent_ids: List[str]) -> Dict[str, Any]:
        """Determine the best coordination strategy for a collaborative task"""
        agents = [self.agents[agent_id] for agent_id in agent_ids]
        
        # Analyze agent capabilities
        all_capabilities = set()
        for agent in agents:
            all_capabilities.update(cap.name for cap in agent.capabilities)
        
        strategy = {
            "type": "parallel" if len(all_capabilities) >= len(task.requirements) else "sequential",
            "communication_pattern": "broadcast" if len(agents) <= 3 else "hierarchical",
            "decision_making": "consensus" if task.priority >= TaskPriority.HIGH else "coordinator_led",
            "task_decomposition": "capability_based",
            "conflict_resolution": "voting" if len(agents) % 2 == 1 else "mediator"
        }
        
        return strategy

    async def execute_task(self, task_id: str, agent_id: str) -> Dict[str, Any]:
        """Execute a task with a single agent"""
        try:
            task = self.tasks[task_id]
            agent = self.agents[agent_id]
            
            start_time = datetime.now()
            
            # Simulate task execution (in real implementation, this would call actual agent)
            await asyncio.sleep(min(task.estimated_duration / 100, 5))  # Simulated work
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Update agent metrics
            agent.total_tasks_completed += 1
            agent.average_completion_time = (
                (agent.average_completion_time * (agent.total_tasks_completed - 1) + execution_time) /
                agent.total_tasks_completed
            )
            
            # Calculate performance adjustment
            expected_time = task.estimated_duration
            performance_ratio = expected_time / execution_time if execution_time > 0 else 1.0
            agent.performance_score = (agent.performance_score * 0.8) + (performance_ratio * 0.2)
            agent.performance_score = max(0.1, min(2.0, agent.performance_score))
            
            # Complete task
            agent.status = AgentStatus.IDLE
            agent.current_task = None
            self.completed_tasks.append(task_id)
            
            # Update learning system
            await self.learning_system.record_task_completion(agent_id, task_id, execution_time, True)
            
            result = {
                "success": True,
                "task_id": task_id,
                "agent_id": agent_id,
                "execution_time": execution_time,
                "performance_score": agent.performance_score,
                "completed_at": end_time.isoformat(),
                "output": {"message": f"Task {task.type} completed successfully"}
            }
            
            # Process queued tasks
            await self.process_task_queue()
            
            return result
            
        except Exception as e:
            # Handle task failure
            agent = self.agents[agent_id]
            agent.status = AgentStatus.ERROR
            agent.current_task = None
            
            await self.learning_system.record_task_completion(agent_id, task_id, 0, False)
            
            return {"success": False, "error": str(e)}

    async def execute_collaborative_task(self, collaboration_id: str) -> Dict[str, Any]:
        """Execute a collaborative task with multiple agents"""
        try:
            collaboration = self.active_collaborations[collaboration_id]
            task_id = collaboration["task_id"]
            task = self.tasks[task_id]
            agent_ids = collaboration["agent_ids"]
            
            start_time = datetime.now()
            
            # Execute based on coordination strategy
            strategy = collaboration["coordination_strategy"]
            
            if strategy["type"] == "parallel":
                # Parallel execution
                execution_tasks = []
                for agent_id in agent_ids:
                    execution_tasks.append(self.execute_subtask(task_id, agent_id, collaboration_id))
                
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            else:
                # Sequential execution
                results = []
                for agent_id in agent_ids:
                    result = await self.execute_subtask(task_id, agent_id, collaboration_id)
                    results.append(result)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Aggregate results
            successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
            
            # Update all participating agents
            for agent_id in agent_ids:
                agent = self.agents[agent_id]
                agent.status = AgentStatus.IDLE
                agent.current_task = None
                agent.total_tasks_completed += 1
            
            # Complete collaboration
            collaboration["status"] = "completed"
            collaboration["completed_at"] = end_time
            collaboration["results"] = results
            
            self.completed_tasks.append(task_id)
            
            return {
                "success": len(successful_results) > 0,
                "collaboration_id": collaboration_id,
                "task_id": task_id,
                "execution_time": execution_time,
                "participating_agents": len(agent_ids),
                "successful_subtasks": len(successful_results),
                "total_subtasks": len(results),
                "coordination_efficiency": len(successful_results) / len(results),
                "results": results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def execute_subtask(self, task_id: str, agent_id: str, collaboration_id: str) -> Dict[str, Any]:
        """Execute a subtask as part of a collaboration"""
        try:
            # Simulate subtask execution
            await asyncio.sleep(1)  # Simulated work
            
            return {
                "success": True,
                "agent_id": agent_id,
                "collaboration_id": collaboration_id,
                "output": {"message": f"Subtask completed by agent {agent_id}"}
            }
        except Exception as e:
            return {"success": False, "agent_id": agent_id, "error": str(e)}

    async def process_task_queue(self):
        """Process pending tasks in the queue"""
        try:
            if not self.task_queue:
                return
            
            # Get available agents
            available_agents = [
                agent_id for agent_id, agent in self.agents.items()
                if agent.status == AgentStatus.IDLE
            ]
            
            if not available_agents:
                return
            
            # Process tasks that can be started
            tasks_to_remove = []
            for task_id in self.task_queue[:]:
                task = self.tasks[task_id]
                
                # Check dependencies
                dependencies_complete = all(
                    dep_id in self.completed_tasks for dep_id in task.dependencies
                )
                
                if dependencies_complete:
                    suitable_agents = await self.find_suitable_agents(task)
                    if suitable_agents:
                        await self.schedule_task_execution(task_id)
                        tasks_to_remove.append(task_id)
            
            # Remove scheduled tasks from queue
            for task_id in tasks_to_remove:
                self.task_queue.remove(task_id)
                
        except Exception as e:
            self.logger.error(f"Error processing task queue: {e}")

    def estimate_task_start_time(self, task_id: str) -> str:
        """Estimate when a task will start execution"""
        try:
            task = self.tasks[task_id]
            
            # If already scheduled, start time is now
            if task_id not in self.task_queue:
                return datetime.now().isoformat()
            
            # Estimate based on queue position and agent availability
            queue_position = self.task_queue.index(task_id)
            
            # Calculate average task completion time
            if self.agents:
                avg_completion_time = sum(
                    agent.average_completion_time for agent in self.agents.values()
                ) / len(self.agents)
            else:
                avg_completion_time = 300  # 5 minutes default
            
            estimated_wait_time = queue_position * avg_completion_time
            estimated_start = datetime.now() + timedelta(seconds=estimated_wait_time)
            
            return estimated_start.isoformat()
        except Exception:
            return datetime.now().isoformat()

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Agent statistics
            agent_status_counts = {}
            for agent in self.agents.values():
                status = agent.status.value
                agent_status_counts[status] = agent_status_counts.get(status, 0) + 1
            
            # Task statistics  
            total_tasks = len(self.tasks)
            completed_tasks = len(self.completed_tasks)
            queued_tasks = len(self.task_queue)
            active_tasks = total_tasks - completed_tasks - queued_tasks
            
            # Performance metrics
            if self.agents:
                avg_performance = sum(agent.performance_score for agent in self.agents.values()) / len(self.agents)
                total_completed = sum(agent.total_tasks_completed for agent in self.agents.values())
            else:
                avg_performance = 0.0
                total_completed = 0
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "agents": {
                    "total": len(self.agents),
                    "status_breakdown": agent_status_counts,
                    "average_performance": round(avg_performance, 2)
                },
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "active": active_tasks,
                    "queued": queued_tasks,
                    "completion_rate": round(completed_tasks / max(total_tasks, 1) * 100, 1)
                },
                "collaborations": {
                    "active": len([c for c in self.active_collaborations.values() if c["status"] == "active"]),
                    "total": len(self.active_collaborations)
                },
                "performance": {
                    "total_tasks_completed": total_completed,
                    "average_agent_performance": round(avg_performance, 2),
                    "system_efficiency": self.calculate_system_efficiency()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def calculate_system_efficiency(self) -> float:
        """Calculate overall system efficiency"""
        try:
            if not self.agents or not self.completed_tasks:
                return 0.0
            
            # Base efficiency from agent performance
            avg_performance = sum(agent.performance_score for agent in self.agents.values()) / len(self.agents)
            
            # Task completion efficiency
            total_tasks = len(self.tasks)
            completion_rate = len(self.completed_tasks) / max(total_tasks, 1)
            
            # Resource utilization
            busy_agents = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
            utilization_rate = busy_agents / max(len(self.agents), 1)
            
            # Combined efficiency score
            efficiency = (avg_performance * 0.4) + (completion_rate * 0.4) + (utilization_rate * 0.2)
            
            return round(min(efficiency, 1.0), 2)
        except Exception:
            return 0.0

# Supporting classes
class AgentLearningSystem:
    """Learning system to improve agent performance over time"""
    
    def __init__(self):
        self.performance_history = {}
        self.capability_improvements = {}
    
    async def record_task_completion(self, agent_id: str, task_id: str, execution_time: float, success: bool):
        """Record task completion for learning"""
        if agent_id not in self.performance_history:
            self.performance_history[agent_id] = []
        
        self.performance_history[agent_id].append({
            "task_id": task_id,
            "execution_time": execution_time,
            "success": success,
            "timestamp": datetime.now()
        })

class AgentLoadBalancer:
    """Load balancer to distribute tasks efficiently"""
    
    def __init__(self):
        self.agent_workloads = {}
    
    async def register_agent(self, agent: Agent):
        """Register agent with load balancer"""
        self.agent_workloads[agent.id] = 0
    
    async def get_least_loaded_agent(self, suitable_agents: List[str]) -> str:
        """Get the least loaded agent from suitable candidates"""
        if not suitable_agents:
            return None
        
        return min(suitable_agents, key=lambda agent_id: self.agent_workloads.get(agent_id, 0))