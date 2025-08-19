"""
Base Agent Class for Multi-Agent System
Implements core functionality that all specialized agents inherit
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, agent_type: str, capabilities: List[str]):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.status = "idle"
        self.current_task = None
        self.execution_history = []
        self.learning_data = {}
        
    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task assigned to this agent"""
        pass
    
    async def can_handle_task(self, task: Dict[str, Any]) -> bool:
        """Check if this agent can handle the given task"""
        required_capabilities = task.get("required_capabilities", [])
        return all(cap in self.capabilities for cap in required_capabilities)
    
    async def update_status(self, status: str, task: Optional[Dict] = None):
        """Update agent status and current task"""
        self.status = status
        self.current_task = task
        
        # Log status change
        status_update = {
            "timestamp": datetime.utcnow(),
            "status": status,
            "task_id": task.get("id") if task else None
        }
        self.execution_history.append(status_update)
    
    async def learn_from_execution(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Learn from task execution to improve future performance"""
        learning_entry = {
            "task_type": task.get("type"),
            "complexity": task.get("complexity", "medium"),
            "success": result.get("success", False),
            "execution_time": result.get("execution_time", 0),
            "timestamp": datetime.utcnow()
        }
        
        task_type = task.get("type", "unknown")
        if task_type not in self.learning_data:
            self.learning_data[task_type] = []
        
        self.learning_data[task_type].append(learning_entry)
        
        # Keep only recent learning data (last 100 entries per task type)
        if len(self.learning_data[task_type]) > 100:
            self.learning_data[task_type] = self.learning_data[task_type][-100:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        total_tasks = len(self.execution_history)
        successful_tasks = sum(1 for entry in self.execution_history if entry.get("success"))
        
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "total_tasks_executed": total_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "current_status": self.status,
            "capabilities": self.capabilities,
            "learning_data_size": sum(len(entries) for entries in self.learning_data.values())
        }