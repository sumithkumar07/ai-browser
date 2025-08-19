from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import uuid
import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AgentTask(BaseModel):
    id: str
    type: str
    description: str
    priority: TaskPriority
    payload: Dict[str, Any]
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentCapability(BaseModel):
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    estimated_time: float  # seconds
    success_rate: float  # 0.0 to 1.0

class BaseAgent(ABC):
    """Base class for all AI agents in the AETHER multi-agent system"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities: List[AgentCapability] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[str] = []
        self.error_count = 0
        self.success_count = 0
        self.total_execution_time = 0.0
        
        # Agent memory and learning
        self.memory: Dict[str, Any] = {}
        self.learning_data: List[Dict[str, Any]] = []
        
        # Communication
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.coordinator = None
        
        # Logging
        self.logger = logging.getLogger(f"agent.{self.agent_id}")
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the agent and its capabilities"""
        pass
    
    @abstractmethod
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a specific task"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """Return list of agent capabilities"""
        pass
    
    async def can_handle_task(self, task: AgentTask) -> float:
        """Return confidence score (0.0-1.0) for handling this task"""
        capabilities = await self.get_capabilities()
        
        # Simple matching based on task type
        for cap in capabilities:
            if task.type in cap.input_types:
                return cap.success_rate
        
        return 0.0
    
    async def start_task(self, task: AgentTask) -> bool:
        """Start executing a task"""
        if self.status != AgentStatus.IDLE:
            return False
        
        try:
            self.status = AgentStatus.BUSY
            task.assigned_agent = self.agent_id
            task.status = "running"
            task.started_at = datetime.now()
            
            self.active_tasks[task.id] = task
            
            self.logger.info(f"Started task {task.id}: {task.description}")
            
            # Execute task in background
            asyncio.create_task(self._execute_task_wrapper(task))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start task {task.id}: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def _execute_task_wrapper(self, task: AgentTask):
        """Wrapper for task execution with error handling and metrics"""
        start_time = datetime.now()
        
        try:
            # Execute the task
            result = await self.execute_task(task)
            
            # Update task status
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()
            
            # Update agent metrics
            execution_time = (task.completed_at - task.started_at).total_seconds()
            self.total_execution_time += execution_time
            self.success_count += 1
            
            # Learn from successful execution
            await self._record_learning_data(task, True, execution_time)
            
            # Notify coordinator
            if self.coordinator:
                await self.coordinator.task_completed(task, self)
            
            self.logger.info(f"Completed task {task.id} in {execution_time:.2f}s")
            
        except Exception as e:
            # Update task status
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            
            # Update agent metrics
            execution_time = (task.completed_at - task.started_at).total_seconds()
            self.error_count += 1
            
            # Learn from failure
            await self._record_learning_data(task, False, execution_time, str(e))
            
            # Notify coordinator
            if self.coordinator:
                await self.coordinator.task_failed(task, self, str(e))
            
            self.logger.error(f"Failed task {task.id}: {e}")
            
        finally:
            # Clean up
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            self.completed_tasks.append(task.id)
            self.status = AgentStatus.IDLE
    
    async def _record_learning_data(self, task: AgentTask, success: bool, 
                                   execution_time: float, error: Optional[str] = None):
        """Record data for learning and improvement"""
        learning_entry = {
            "task_id": task.id,
            "task_type": task.type,
            "priority": task.priority.name,
            "success": success,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "payload_size": len(json.dumps(task.payload)) if task.payload else 0
        }
        
        self.learning_data.append(learning_entry)
        
        # Keep only last 1000 entries
        if len(self.learning_data) > 1000:
            self.learning_data = self.learning_data[-1000:]
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        total_tasks = self.success_count + self.error_count
        success_rate = self.success_count / total_tasks if total_tasks > 0 else 0.0
        avg_execution_time = self.total_execution_time / self.success_count if self.success_count > 0 else 0.0
        
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "success_rate": success_rate,
            "error_count": self.error_count,
            "avg_execution_time": avg_execution_time,
            "capabilities": [cap.dict() for cap in await self.get_capabilities()],
            "memory_size": len(self.memory),
            "learning_entries": len(self.learning_data)
        }
    
    async def send_message(self, recipient_id: str, message: Dict[str, Any]):
        """Send message to another agent"""
        if self.coordinator:
            await self.coordinator.route_message(self.agent_id, recipient_id, message)
    
    async def receive_message(self, sender_id: str, message: Dict[str, Any]):
        """Receive message from another agent"""
        await self.message_queue.put({
            "sender": sender_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    async def process_messages(self):
        """Process incoming messages (should be called periodically)"""
        while not self.message_queue.empty():
            try:
                msg = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                await self.handle_message(msg["sender"], msg["message"])
            except asyncio.TimeoutError:
                break
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def handle_message(self, sender_id: str, message: Dict[str, Any]):
        """Handle incoming message (override in subclasses)"""
        self.logger.debug(f"Received message from {sender_id}: {message}")
    
    async def update_memory(self, key: str, value: Any):
        """Update agent memory"""
        self.memory[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_memory(self, key: str) -> Optional[Any]:
        """Get value from agent memory"""
        if key in self.memory:
            return self.memory[key]["value"]
        return None
    
    async def analyze_performance(self) -> Dict[str, Any]:
        """Analyze agent performance and suggest improvements"""
        if not self.learning_data:
            return {"message": "No learning data available"}
        
        # Analyze recent performance
        recent_data = self.learning_data[-100:] if len(self.learning_data) >= 100 else self.learning_data
        
        success_rate = sum(1 for entry in recent_data if entry["success"]) / len(recent_data)
        avg_time = sum(entry["execution_time"] for entry in recent_data) / len(recent_data)
        
        # Identify patterns
        error_patterns = {}
        for entry in recent_data:
            if not entry["success"] and entry["error"]:
                error_type = entry["error"].split(":")[0]
                error_patterns[error_type] = error_patterns.get(error_type, 0) + 1
        
        # Performance trends
        time_trend = "stable"
        if len(recent_data) >= 10:
            early_avg = sum(entry["execution_time"] for entry in recent_data[:10]) / 10
            late_avg = sum(entry["execution_time"] for entry in recent_data[-10:]) / 10
            
            if late_avg > early_avg * 1.2:
                time_trend = "degrading"
            elif late_avg < early_avg * 0.8:
                time_trend = "improving"
        
        return {
            "success_rate": success_rate,
            "avg_execution_time": avg_time,
            "time_trend": time_trend,
            "common_errors": error_patterns,
            "total_learning_entries": len(self.learning_data),
            "recommendations": self._generate_recommendations(success_rate, avg_time, error_patterns)
        }
    
    def _generate_recommendations(self, success_rate: float, avg_time: float, 
                                error_patterns: Dict[str, int]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if success_rate < 0.8:
            recommendations.append("Consider retraining or adjusting task assignment criteria")
        
        if avg_time > 10.0:
            recommendations.append("Performance may benefit from optimization")
        
        if error_patterns:
            most_common_error = max(error_patterns.items(), key=lambda x: x[1])
            recommendations.append(f"Focus on resolving '{most_common_error[0]}' errors")
        
        if not recommendations:
            recommendations.append("Performance is good, continue current approach")
        
        return recommendations
    
    async def shutdown(self):
        """Shutdown the agent gracefully"""
        self.status = AgentStatus.OFFLINE
        
        # Wait for active tasks to complete (with timeout)
        timeout = 30  # seconds
        start_time = datetime.now()
        
        while self.active_tasks and (datetime.now() - start_time).seconds < timeout:
            await asyncio.sleep(1)
        
        # Cancel remaining tasks
        for task in self.active_tasks.values():
            task.status = "cancelled"
            task.error = "Agent shutdown"
        
        self.logger.info(f"Agent {self.agent_id} shut down")