"""
Collaborative AI Agents System for AETHER
Multi-user collaborative workflows and team automation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import logging

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    EXECUTOR = "executor"
    ANALYST = "analyst"
    COMMUNICATOR = "communicator"
    MONITOR = "monitor"
    SPECIALIST = "specialist"

class CollaborationMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    PEER_TO_PEER = "peer_to_peer"

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class CollaborativeUser:
    user_id: str
    username: str
    email: str
    role: str
    skills: List[str]
    availability: bool = True
    current_task: Optional[str] = None
    last_activity: datetime = None

@dataclass
class CollaborativeAgent:
    agent_id: str
    agent_type: AgentRole
    specialization: List[str]
    current_load: int = 0
    max_concurrent_tasks: int = 5
    performance_metrics: Dict[str, float] = None
    assigned_users: Set[str] = None

@dataclass
class CollaborativeTask:
    task_id: str
    title: str
    description: str
    assigned_agents: List[str]
    assigned_users: List[str]
    dependencies: List[str]
    status: TaskStatus
    priority: int
    estimated_duration: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None

@dataclass
class CollaborativeWorkflow:
    workflow_id: str
    name: str
    description: str
    participants: List[CollaborativeUser]
    agents: List[CollaborativeAgent]
    tasks: List[CollaborativeTask]
    collaboration_mode: CollaborationMode
    status: str
    created_by: str
    created_at: datetime

class CollaborativeAgentSystem:
    def __init__(self):
        self.active_users: Dict[str, CollaborativeUser] = {}
        self.available_agents: Dict[str, CollaborativeAgent] = {}
        self.active_workflows: Dict[str, CollaborativeWorkflow] = {}
        self.websocket_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.task_queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Initialize default agents
        self.initialize_default_agents()
        
    def initialize_default_agents(self):
        """Initialize default collaborative agents"""
        default_agents = [
            CollaborativeAgent(
                agent_id="coord-001",
                agent_type=AgentRole.COORDINATOR,
                specialization=["task_management", "workflow_orchestration", "resource_allocation"],
                max_concurrent_tasks=10,
                performance_metrics={"success_rate": 0.95, "efficiency": 0.9},
                assigned_users=set()
            ),
            CollaborativeAgent(
                agent_id="exec-001",
                agent_type=AgentRole.EXECUTOR,
                specialization=["automation", "browser_actions", "form_filling"],
                max_concurrent_tasks=5,
                performance_metrics={"success_rate": 0.88, "speed": 0.92},
                assigned_users=set()
            ),
            CollaborativeAgent(
                agent_id="analyst-001",
                agent_type=AgentRole.ANALYST,
                specialization=["data_analysis", "report_generation", "insights"],
                max_concurrent_tasks=3,
                performance_metrics={"accuracy": 0.94, "depth": 0.91},
                assigned_users=set()
            ),
            CollaborativeAgent(
                agent_id="comm-001",
                agent_type=AgentRole.COMMUNICATOR,
                specialization=["notifications", "status_updates", "team_communication"],
                max_concurrent_tasks=20,
                performance_metrics={"response_time": 0.98, "clarity": 0.89},
                assigned_users=set()
            ),
            CollaborativeAgent(
                agent_id="monitor-001",
                agent_type=AgentRole.MONITOR,
                specialization=["progress_tracking", "performance_monitoring", "quality_assurance"],
                max_concurrent_tasks=15,
                performance_metrics={"accuracy": 0.96, "reliability": 0.93},
                assigned_users=set()
            )
        ]
        
        for agent in default_agents:
            self.available_agents[agent.agent_id] = agent
        
        print(f"✅ Initialized {len(default_agents)} collaborative agents")

    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user for collaborative workflows"""
        try:
            user = CollaborativeUser(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data.get("role", "member"),
                skills=user_data.get("skills", []),
                availability=True,
                last_activity=datetime.now()
            )
            
            self.active_users[user.user_id] = user
            
            return {
                "success": True,
                "user_id": user.user_id,
                "message": f"User {user.username} registered successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_collaborative_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaborative workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Parse participants
            participants = []
            for participant_id in workflow_config.get("participant_ids", []):
                if participant_id in self.active_users:
                    participants.append(self.active_users[participant_id])
            
            # Assign agents based on workflow requirements
            required_agents = await self._assign_agents_for_workflow(workflow_config)
            
            # Create tasks from workflow configuration
            tasks = await self._create_tasks_from_config(workflow_config, workflow_id)
            
            # Create collaborative workflow
            workflow = CollaborativeWorkflow(
                workflow_id=workflow_id,
                name=workflow_config["name"],
                description=workflow_config.get("description", ""),
                participants=participants,
                agents=required_agents,
                tasks=tasks,
                collaboration_mode=CollaborationMode(workflow_config.get("collaboration_mode", "sequential")),
                status="created",
                created_by=workflow_config["created_by"],
                created_at=datetime.now()
            )
            
            self.active_workflows[workflow_id] = workflow
            
            # Notify participants
            await self._notify_workflow_participants(workflow, "workflow_created")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow": asdict(workflow),
                "message": "Collaborative workflow created successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _assign_agents_for_workflow(self, workflow_config: Dict[str, Any]) -> List[CollaborativeAgent]:
        """Assign appropriate agents for workflow requirements"""
        required_agents = []
        workflow_type = workflow_config.get("type", "general")
        complexity = workflow_config.get("complexity", "medium")
        
        # Always assign a coordinator for multi-task workflows
        if len(workflow_config.get("tasks", [])) > 1:
            coordinator = self._find_available_agent(AgentRole.COORDINATOR)
            if coordinator:
                required_agents.append(coordinator)
        
        # Assign specialized agents based on workflow type
        if workflow_type == "data_processing":
            analyst = self._find_available_agent(AgentRole.ANALYST)
            if analyst:
                required_agents.append(analyst)
        
        elif workflow_type == "automation":
            executor = self._find_available_agent(AgentRole.EXECUTOR)
            if executor:
                required_agents.append(executor)
        
        elif workflow_type == "monitoring":
            monitor = self._find_available_agent(AgentRole.MONITOR)
            if monitor:
                required_agents.append(monitor)
        
        # Always assign a communicator for team coordination
        communicator = self._find_available_agent(AgentRole.COMMUNICATOR)
        if communicator:
            required_agents.append(communicator)
        
        # Assign additional agents for complex workflows
        if complexity == "high":
            # Add backup executor
            backup_executor = self._find_available_agent(AgentRole.EXECUTOR, exclude=[agent.agent_id for agent in required_agents])
            if backup_executor:
                required_agents.append(backup_executor)
        
        return required_agents

    def _find_available_agent(self, agent_type: AgentRole, exclude: List[str] = None) -> Optional[CollaborativeAgent]:
        """Find an available agent of specific type"""
        exclude = exclude or []
        
        for agent in self.available_agents.values():
            if (agent.agent_type == agent_type and 
                agent.agent_id not in exclude and
                agent.current_load < agent.max_concurrent_tasks):
                return agent
        return None

    async def _create_tasks_from_config(self, workflow_config: Dict[str, Any], workflow_id: str) -> List[CollaborativeTask]:
        """Create tasks from workflow configuration"""
        tasks = []
        
        for i, task_config in enumerate(workflow_config.get("tasks", [])):
            task = CollaborativeTask(
                task_id=str(uuid.uuid4()),
                title=task_config["title"],
                description=task_config.get("description", ""),
                assigned_agents=[],
                assigned_users=task_config.get("assigned_users", []),
                dependencies=task_config.get("dependencies", []),
                status=TaskStatus.PENDING,
                priority=task_config.get("priority", 5),
                estimated_duration=task_config.get("estimated_duration", 3600),  # 1 hour default
                created_at=datetime.now()
            )
            tasks.append(task)
        
        return tasks

    async def execute_collaborative_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a collaborative workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            workflow.status = "running"
            
            # Start workflow execution based on collaboration mode
            if workflow.collaboration_mode == CollaborationMode.SEQUENTIAL:
                results = await self._execute_sequential_workflow(workflow)
            elif workflow.collaboration_mode == CollaborationMode.PARALLEL:
                results = await self._execute_parallel_workflow(workflow)
            elif workflow.collaboration_mode == CollaborationMode.HIERARCHICAL:
                results = await self._execute_hierarchical_workflow(workflow)
            else:  # PEER_TO_PEER
                results = await self._execute_peer_to_peer_workflow(workflow)
            
            workflow.status = "completed" if results["success"] else "failed"
            
            # Notify participants of completion
            await self._notify_workflow_participants(workflow, "workflow_completed")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "execution_results": results,
                "status": workflow.status
            }
        except Exception as e:
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id].status = "failed"
            return {"success": False, "error": str(e)}

    async def _execute_sequential_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute tasks sequentially"""
        results = []
        
        # Sort tasks by priority and dependencies
        sorted_tasks = self._sort_tasks_by_dependencies(workflow.tasks)
        
        for task in sorted_tasks:
            task_result = await self._execute_collaborative_task(task, workflow)
            results.append(task_result)
            
            if not task_result["success"]:
                # Handle task failure
                failure_handling = await self._handle_task_failure(task, workflow)
                if not failure_handling["continue"]:
                    break
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count == len(sorted_tasks),
            "total_tasks": len(sorted_tasks),
            "successful_tasks": success_count,
            "task_results": results
        }

    async def _execute_parallel_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute independent tasks in parallel"""
        # Group tasks by dependencies
        task_groups = self._group_tasks_for_parallel_execution(workflow.tasks)
        
        all_results = []
        
        for group in task_groups:
            # Execute tasks in current group in parallel
            group_tasks = [self._execute_collaborative_task(task, workflow) for task in group]
            group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
            
            all_results.extend(group_results)
            
            # Check if any critical tasks failed
            critical_failures = [r for r in group_results if isinstance(r, dict) and not r.get("success") and r.get("critical", False)]
            if critical_failures:
                break
        
        success_count = sum(1 for r in all_results if isinstance(r, dict) and r.get("success"))
        return {
            "success": success_count == len(workflow.tasks),
            "total_tasks": len(workflow.tasks),
            "successful_tasks": success_count,
            "task_results": all_results
        }

    async def _execute_hierarchical_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow with hierarchical task distribution"""
        # Find coordinator agent
        coordinator = next((agent for agent in workflow.agents if agent.agent_type == AgentRole.COORDINATOR), None)
        
        if not coordinator:
            return {"success": False, "error": "No coordinator agent available"}
        
        # Coordinator manages task distribution
        task_assignments = await self._coordinator_assign_tasks(coordinator, workflow.tasks, workflow.agents)
        
        # Execute assigned tasks
        results = []
        for assignment in task_assignments:
            task_result = await self._execute_agent_task_assignment(assignment, workflow)
            results.append(task_result)
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count == len(workflow.tasks),
            "total_tasks": len(workflow.tasks),
            "successful_tasks": success_count,
            "coordinator": coordinator.agent_id,
            "task_results": results
        }

    async def _execute_peer_to_peer_workflow(self, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute workflow with peer-to-peer collaboration"""
        # Create peer-to-peer task marketplace
        available_tasks = list(workflow.tasks)
        results = []
        
        while available_tasks:
            # Each agent/user can claim tasks they can handle
            task_claims = await self._process_peer_task_claims(available_tasks, workflow.agents, workflow.participants)
            
            if not task_claims:
                # No one can handle remaining tasks
                break
            
            # Execute claimed tasks
            claim_tasks = [self._execute_peer_task_claim(claim, workflow) for claim in task_claims]
            claim_results = await asyncio.gather(*claim_tasks, return_exceptions=True)
            
            results.extend(claim_results)
            
            # Remove completed tasks
            completed_task_ids = [r.get("task_id") for r in claim_results if isinstance(r, dict) and r.get("success")]
            available_tasks = [t for t in available_tasks if t.task_id not in completed_task_ids]
        
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        return {
            "success": success_count == len(workflow.tasks),
            "total_tasks": len(workflow.tasks),
            "successful_tasks": success_count,
            "collaboration_mode": "peer_to_peer",
            "task_results": results
        }

    async def _execute_collaborative_task(self, task: CollaborativeTask, workflow: CollaborativeWorkflow) -> Dict[str, Any]:
        """Execute a single collaborative task"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # Assign best agents for this task
            assigned_agents = await self._assign_agents_for_task(task, workflow.agents)
            task.assigned_agents = [agent.agent_id for agent in assigned_agents]
            
            # Notify assigned users and agents
            await self._notify_task_assignment(task, workflow)
            
            # Execute task based on type and assigned resources
            if assigned_agents:
                # Agent-driven execution
                execution_result = await self._execute_agent_driven_task(task, assigned_agents)
            else:
                # User-driven execution
                execution_result = await self._execute_user_driven_task(task, workflow.participants)
            
            task.status = TaskStatus.COMPLETED if execution_result["success"] else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = execution_result
            
            # Update agent workloads
            for agent in assigned_agents:
                agent.current_load = max(0, agent.current_load - 1)
            
            return {
                "success": execution_result["success"],
                "task_id": task.task_id,
                "result": execution_result,
                "duration": (task.completed_at - task.started_at).total_seconds(),
                "assigned_agents": task.assigned_agents
            }
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            return {"success": False, "task_id": task.task_id, "error": str(e)}

    async def _assign_agents_for_task(self, task: CollaborativeTask, available_agents: List[CollaborativeAgent]) -> List[CollaborativeAgent]:
        """Assign best agents for a specific task"""
        suitable_agents = []
        
        # Analyze task requirements (simplified heuristic)
        task_keywords = (task.title + " " + task.description).lower()
        
        for agent in available_agents:
            if agent.current_load < agent.max_concurrent_tasks:
                # Check if agent specialization matches task
                match_score = 0
                for spec in agent.specialization:
                    if spec.replace("_", " ") in task_keywords:
                        match_score += 1
                
                if match_score > 0:
                    suitable_agents.append((agent, match_score))
        
        # Sort by match score and performance
        suitable_agents.sort(key=lambda x: (x[1], x[0].performance_metrics.get("success_rate", 0.5)), reverse=True)
        
        # Return top 2 agents for collaboration
        assigned = [agent for agent, score in suitable_agents[:2]]
        
        # Update agent workloads
        for agent in assigned:
            agent.current_load += 1
        
        return assigned

    async def _execute_agent_driven_task(self, task: CollaborativeTask, agents: List[CollaborativeAgent]) -> Dict[str, Any]:
        """Execute task with agent collaboration"""
        try:
            # Simulate agent collaboration
            primary_agent = agents[0]
            
            # Agent executes based on specialization
            if "automation" in primary_agent.specialization:
                result = await self._simulate_automation_task(task)
            elif "data_analysis" in primary_agent.specialization:
                result = await self._simulate_analysis_task(task)
            elif "coordination" in primary_agent.specialization:
                result = await self._simulate_coordination_task(task)
            else:
                result = await self._simulate_general_task(task)
            
            # Add collaboration metrics
            result["collaboration_agents"] = [agent.agent_id for agent in agents]
            result["primary_agent"] = primary_agent.agent_id
            
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _simulate_automation_task(self, task: CollaborativeTask) -> Dict[str, Any]:
        """Simulate automation task execution"""
        # Simulate task execution time
        await asyncio.sleep(min(5, task.estimated_duration / 1000))
        
        return {
            "success": True,
            "task_type": "automation",
            "actions_performed": ["navigate", "click", "extract_data"],
            "data_extracted": {"sample": "data"},
            "execution_time": task.estimated_duration / 1000
        }

    async def _simulate_analysis_task(self, task: CollaborativeTask) -> Dict[str, Any]:
        """Simulate data analysis task execution"""
        await asyncio.sleep(min(3, task.estimated_duration / 1000))
        
        return {
            "success": True,
            "task_type": "analysis",
            "analysis_results": {
                "insights": ["insight_1", "insight_2"],
                "metrics": {"accuracy": 0.92, "confidence": 0.88},
                "recommendations": ["recommendation_1", "recommendation_2"]
            },
            "execution_time": task.estimated_duration / 1000
        }

    async def _simulate_coordination_task(self, task: CollaborativeTask) -> Dict[str, Any]:
        """Simulate coordination task execution"""
        await asyncio.sleep(min(2, task.estimated_duration / 1000))
        
        return {
            "success": True,
            "task_type": "coordination",
            "coordination_actions": ["resource_allocation", "task_distribution", "progress_monitoring"],
            "efficiency_gain": 0.85,
            "execution_time": task.estimated_duration / 1000
        }

    async def _simulate_general_task(self, task: CollaborativeTask) -> Dict[str, Any]:
        """Simulate general task execution"""
        await asyncio.sleep(min(4, task.estimated_duration / 1000))
        
        return {
            "success": True,
            "task_type": "general",
            "completion_status": "completed",
            "execution_time": task.estimated_duration / 1000
        }

    async def _execute_user_driven_task(self, task: CollaborativeTask, participants: List[CollaborativeUser]) -> Dict[str, Any]:
        """Execute task requiring human input"""
        try:
            # Find suitable user for task
            suitable_users = [user for user in participants if user.availability and user.user_id in task.assigned_users]
            
            if not suitable_users:
                return {"success": False, "error": "No available users for task"}
            
            # Assign to first available user
            assigned_user = suitable_users[0]
            assigned_user.current_task = task.task_id
            
            # Simulate user task execution (in real system, this would wait for user completion)
            await asyncio.sleep(2)  # Simulated user work time
            
            assigned_user.current_task = None
            assigned_user.last_activity = datetime.now()
            
            return {
                "success": True,
                "task_type": "user_driven",
                "assigned_user": assigned_user.username,
                "user_id": assigned_user.user_id,
                "completion_method": "manual"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _sort_tasks_by_dependencies(self, tasks: List[CollaborativeTask]) -> List[CollaborativeTask]:
        """Sort tasks based on dependencies and priority"""
        # Simple topological sort
        sorted_tasks = []
        remaining_tasks = list(tasks)
        
        while remaining_tasks:
            # Find tasks with no unresolved dependencies
            ready_tasks = []
            for task in remaining_tasks:
                dependencies_met = all(
                    dep_id in [t.task_id for t in sorted_tasks] 
                    for dep_id in task.dependencies
                )
                if dependencies_met:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Circular dependency or error - add remaining tasks
                ready_tasks = remaining_tasks
            
            # Sort ready tasks by priority
            ready_tasks.sort(key=lambda x: x.priority, reverse=True)
            
            # Add highest priority task
            if ready_tasks:
                next_task = ready_tasks[0]
                sorted_tasks.append(next_task)
                remaining_tasks.remove(next_task)
        
        return sorted_tasks

    def _group_tasks_for_parallel_execution(self, tasks: List[CollaborativeTask]) -> List[List[CollaborativeTask]]:
        """Group tasks that can be executed in parallel"""
        groups = []
        remaining_tasks = list(tasks)
        completed_task_ids = set()
        
        while remaining_tasks:
            # Find tasks that can run now (dependencies completed)
            current_group = []
            for task in remaining_tasks[:]:
                dependencies_met = all(dep_id in completed_task_ids for dep_id in task.dependencies)
                if dependencies_met:
                    current_group.append(task)
                    remaining_tasks.remove(task)
            
            if current_group:
                groups.append(current_group)
                completed_task_ids.update(task.task_id for task in current_group)
            else:
                # Handle remaining tasks with unmet dependencies
                groups.append(remaining_tasks)
                break
        
        return groups

    async def _notify_workflow_participants(self, workflow: CollaborativeWorkflow, event_type: str):
        """Notify all workflow participants of events"""
        notification = {
            "type": event_type,
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "timestamp": datetime.now().isoformat(),
            "status": workflow.status
        }
        
        # Send to all participants
        for participant in workflow.participants:
            await self._send_user_notification(participant.user_id, notification)

    async def _notify_task_assignment(self, task: CollaborativeTask, workflow: CollaborativeWorkflow):
        """Notify users and agents of task assignment"""
        notification = {
            "type": "task_assigned",
            "task_id": task.task_id,
            "task_title": task.title,
            "workflow_id": workflow.workflow_id,
            "assigned_agents": task.assigned_agents,
            "assigned_users": task.assigned_users,
            "timestamp": datetime.now().isoformat()
        }
        
        # Notify assigned users
        for user_id in task.assigned_users:
            await self._send_user_notification(user_id, notification)

    async def _send_user_notification(self, user_id: str, notification: Dict[str, Any]):
        """Send notification to a specific user"""
        try:
            # In a real system, this would send via WebSocket, email, or push notification
            print(f"📬 Notification to {user_id}: {notification['type']}")
            
            # If user has active WebSocket connection, send real-time notification
            if user_id in self.websocket_connections:
                websocket = self.websocket_connections[user_id]
                await websocket.send(json.dumps(notification))
        except Exception as e:
            print(f"Failed to send notification to {user_id}: {e}")

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed status of a collaborative workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            
            # Calculate progress metrics
            total_tasks = len(workflow.tasks)
            completed_tasks = len([t for t in workflow.tasks if t.status == TaskStatus.COMPLETED])
            in_progress_tasks = len([t for t in workflow.tasks if t.status == TaskStatus.IN_PROGRESS])
            failed_tasks = len([t for t in workflow.tasks if t.status == TaskStatus.FAILED])
            
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "success": True,
                "workflow": asdict(workflow),
                "progress": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "in_progress_tasks": in_progress_tasks,
                    "failed_tasks": failed_tasks,
                    "progress_percentage": round(progress_percentage, 2)
                },
                "active_participants": len([p for p in workflow.participants if p.availability]),
                "agent_utilization": {
                    agent.agent_id: {
                        "current_load": agent.current_load,
                        "max_capacity": agent.max_concurrent_tasks,
                        "utilization_percentage": round((agent.current_load / agent.max_concurrent_tasks) * 100, 2)
                    }
                    for agent in workflow.agents
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_active_workflows(self, user_id: str = None) -> Dict[str, Any]:
        """List active workflows for a user or all workflows"""
        try:
            workflows = []
            
            for workflow in self.active_workflows.values():
                # Filter by user if specified
                if user_id and not any(p.user_id == user_id for p in workflow.participants):
                    continue
                
                workflow_summary = {
                    "workflow_id": workflow.workflow_id,
                    "name": workflow.name,
                    "status": workflow.status,
                    "created_at": workflow.created_at.isoformat(),
                    "participant_count": len(workflow.participants),
                    "task_count": len(workflow.tasks),
                    "collaboration_mode": workflow.collaboration_mode.value
                }
                workflows.append(workflow_summary)
            
            return {
                "success": True,
                "workflows": workflows,
                "count": len(workflows)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cancel_workflow(self, workflow_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel a collaborative workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            
            # Check if user has permission to cancel
            if workflow.created_by != user_id:
                return {"success": False, "error": "Permission denied"}
            
            workflow.status = "cancelled"
            
            # Cancel all pending and in-progress tasks
            for task in workflow.tasks:
                if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                    task.status = TaskStatus.FAILED
            
            # Free up agent resources
            for agent in workflow.agents:
                agent.current_load = max(0, agent.current_load - len([t for t in workflow.tasks if agent.agent_id in t.assigned_agents]))
            
            # Notify all participants
            await self._notify_workflow_participants(workflow, "workflow_cancelled")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": "cancelled"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get user dashboard with personalized information"""
        try:
            if user_id not in self.active_users:
                return {"success": False, "error": "User not found"}
            
            user = self.active_users[user_id]
            
            # Get user's workflows
            user_workflows = [w for w in self.active_workflows.values() 
                            if any(p.user_id == user_id for p in w.participants)]
            
            # Get user's tasks
            user_tasks = []
            for workflow in user_workflows:
                for task in workflow.tasks:
                    if user_id in task.assigned_users:
                        user_tasks.append({
                            "task_id": task.task_id,
                            "title": task.title,
                            "status": task.status.value,
                            "workflow_name": workflow.name,
                            "priority": task.priority,
                            "estimated_duration": task.estimated_duration
                        })
            
            # Calculate user metrics
            completed_tasks = len([t for t in user_tasks if t["status"] == "completed"])
            total_tasks = len(user_tasks)
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            return {
                "success": True,
                "user": asdict(user),
                "dashboard": {
                    "active_workflows": len(user_workflows),
                    "assigned_tasks": len(user_tasks),
                    "completed_tasks": completed_tasks,
                    "completion_rate": round(completion_rate, 2),
                    "current_task": user.current_task,
                    "last_activity": user.last_activity.isoformat() if user.last_activity else None
                },
                "recent_tasks": user_tasks[:5],  # Last 5 tasks
                "active_workflows_summary": [
                    {
                        "workflow_id": w.workflow_id,
                        "name": w.name,
                        "status": w.status,
                        "role": "participant"
                    }
                    for w in user_workflows
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def test_connection(self) -> Dict[str, Any]:
        """Test the collaborative system connection"""
        try:
            return {
                "success": True,
                "active_users": len(self.active_users),
                "available_agents": len(self.available_agents),
                "active_workflows": len(self.active_workflows),
                "system_status": "operational"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}