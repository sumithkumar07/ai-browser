"""
Collaborative Multi-User Agent System for AETHER
Enables team workflows with AI agent coordination
"""

import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os

class CollaborativeAgentSystem:
    def __init__(self):
        self.users = {}
        self.active_workflows = {}
        self.agent_pools = {}
        self.collaboration_sessions = {}
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        self.client = None
        self.db = None
        
        # Initialize with default agent capabilities
        self.agent_capabilities = {
            "data_analyst": ["data_processing", "visualization", "reporting"],
            "web_scraper": ["content_extraction", "api_calls", "data_collection"],
            "coordinator": ["task_distribution", "workflow_management", "communication"],
            "quality_checker": ["validation", "testing", "review"]
        }

    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a user for collaborative workflows"""
        try:
            user_id = user_data["user_id"]
            
            user_profile = {
                "user_id": user_id,
                "username": user_data["username"],
                "email": user_data["email"],
                "role": user_data.get("role", "member"),
                "skills": user_data.get("skills", []),
                "registered_at": datetime.now().isoformat(),
                "status": "active",
                "collaboration_history": [],
                "preferred_agents": []
            }
            
            self.users[user_id] = user_profile
            
            # Store in database if available
            if self.db:
                await self.db.users.insert_one(user_profile)
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "User registered successfully",
                "available_agent_types": list(self.agent_capabilities.keys())
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_collaborative_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a collaborative workflow with multiple participants"""
        try:
            workflow_id = str(uuid.uuid4())
            
            workflow = {
                "workflow_id": workflow_id,
                "name": workflow_data["name"],
                "description": workflow_data.get("description", ""),
                "created_by": workflow_data["created_by"],
                "participant_ids": workflow_data["participant_ids"],
                "tasks": workflow_data["tasks"],
                "collaboration_mode": workflow_data.get("collaboration_mode", "sequential"),
                "type": workflow_data.get("type", "general"),
                "complexity": workflow_data.get("complexity", "medium"),
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "assigned_agents": {},
                "progress": {
                    "total_tasks": len(workflow_data["tasks"]),
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "pending_tasks": len(workflow_data["tasks"])
                }
            }
            
            # Assign appropriate agents based on workflow requirements
            workflow["assigned_agents"] = await self._assign_agents(workflow)
            
            self.active_workflows[workflow_id] = workflow
            
            # Store in database if available
            if self.db:
                await self.db.collaborative_workflows.insert_one(workflow)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "assigned_agents": workflow["assigned_agents"],
                "estimated_completion": self._estimate_completion_time(workflow),
                "collaboration_url": f"/collaborative/{workflow_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _assign_agents(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently assign AI agents to workflow tasks"""
        try:
            assigned_agents = {}
            workflow_type = workflow.get("type", "general")
            complexity = workflow.get("complexity", "medium")
            tasks = workflow.get("tasks", [])
            
            # Agent assignment logic based on task requirements
            for i, task in enumerate(tasks):
                task_type = task.get("type", "general")
                required_skills = task.get("required_skills", [])
                
                # Match agent capabilities to task requirements
                best_agent = "coordinator"  # Default
                
                if "data" in task_type.lower() or "analysis" in task_type.lower():
                    best_agent = "data_analyst"
                elif "web" in task_type.lower() or "scraping" in task_type.lower():
                    best_agent = "web_scraper"
                elif "review" in task_type.lower() or "quality" in task_type.lower():
                    best_agent = "quality_checker"
                
                agent_id = f"{best_agent}_{uuid.uuid4().hex[:8]}"
                assigned_agents[f"task_{i}"] = {
                    "agent_id": agent_id,
                    "agent_type": best_agent,
                    "capabilities": self.agent_capabilities[best_agent],
                    "status": "ready",
                    "assigned_at": datetime.now().isoformat()
                }
            
            # Always assign a coordinator for multi-task workflows
            if len(tasks) > 1:
                coordinator_id = f"coordinator_{uuid.uuid4().hex[:8]}"
                assigned_agents["coordinator"] = {
                    "agent_id": coordinator_id,
                    "agent_type": "coordinator",
                    "capabilities": self.agent_capabilities["coordinator"],
                    "status": "ready",
                    "role": "workflow_coordinator"
                }
            
            return assigned_agents
        except Exception as e:
            return {"error": str(e)}

    def _estimate_completion_time(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate workflow completion time"""
        try:
            tasks = workflow.get("tasks", [])
            complexity = workflow.get("complexity", "medium")
            collaboration_mode = workflow.get("collaboration_mode", "sequential")
            
            # Base time estimates (in minutes)
            base_times = {
                "simple": 5,
                "medium": 15,
                "complex": 30
            }
            
            base_time = base_times.get(complexity, 15)
            total_time = len(tasks) * base_time
            
            # Adjust based on collaboration mode
            if collaboration_mode == "parallel":
                total_time = total_time * 0.6  # 40% faster with parallel execution
            elif collaboration_mode == "collaborative":
                total_time = total_time * 0.8  # 20% faster with collaboration
            
            return {
                "estimated_minutes": int(total_time),
                "estimated_hours": round(total_time / 60, 1),
                "completion_by": (datetime.now() + timedelta(minutes=total_time)).isoformat(),
                "confidence": "medium"
            }
        except Exception as e:
            return {"error": str(e)}

    async def execute_collaborative_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a collaborative workflow with agent coordination"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            execution_id = str(uuid.uuid4())
            
            # Create execution session
            session = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "participants": workflow["participant_ids"],
                "agent_activities": [],
                "real_time_updates": []
            }
            
            self.collaboration_sessions[execution_id] = session
            workflow["status"] = "executing"
            
            # Start collaborative execution
            asyncio.create_task(self._execute_collaborative_tasks(workflow_id, execution_id))
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "started",
                "participants": len(workflow["participant_ids"]),
                "assigned_agents": len(workflow["assigned_agents"]),
                "real_time_url": f"/collaborative/{workflow_id}/live/{execution_id}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_collaborative_tasks(self, workflow_id: str, execution_id: str):
        """Execute collaborative workflow tasks with agent coordination"""
        try:
            workflow = self.active_workflows[workflow_id]
            session = self.collaboration_sessions[execution_id]
            tasks = workflow["tasks"]
            
            for i, task in enumerate(tasks):
                task_start = datetime.now()
                
                # Simulate agent collaboration
                assigned_agent_key = f"task_{i}"
                agent_info = workflow["assigned_agents"].get(assigned_agent_key, {})
                
                # Record agent activity
                activity = {
                    "agent_id": agent_info.get("agent_id", "unknown"),
                    "agent_type": agent_info.get("agent_type", "unknown"),
                    "task_index": i,
                    "task_name": task.get("name", f"Task {i+1}"),
                    "status": "executing",
                    "started_at": task_start.isoformat()
                }
                
                session["agent_activities"].append(activity)
                
                # Simulate task execution time
                execution_time = task.get("estimated_duration", 30)  # seconds
                await asyncio.sleep(min(execution_time, 5))  # Cap at 5 seconds for demo
                
                # Complete task
                activity["status"] = "completed"
                activity["completed_at"] = datetime.now().isoformat()
                activity["duration_seconds"] = (datetime.now() - task_start).total_seconds()
                
                # Update workflow progress
                workflow["progress"]["completed_tasks"] += 1
                workflow["progress"]["pending_tasks"] -= 1
                
                # Add real-time update
                session["real_time_updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "task_completed",
                    "agent": agent_info.get("agent_type"),
                    "task": task.get("name"),
                    "progress": f"{workflow['progress']['completed_tasks']}/{workflow['progress']['total_tasks']}"
                })
            
            # Complete workflow
            workflow["status"] = "completed"
            workflow["completed_at"] = datetime.now().isoformat()
            session["status"] = "completed"
            
        except Exception as e:
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            session["status"] = "failed"
            session["error"] = str(e)

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get collaborative workflow status"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            
            # Find active sessions
            active_sessions = [
                session for session in self.collaboration_sessions.values()
                if session["workflow_id"] == workflow_id
            ]
            
            return {
                "success": True,
                "workflow": workflow,
                "active_sessions": active_sessions,
                "participants": len(workflow["participant_ids"]),
                "progress": workflow["progress"],
                "agent_status": self._get_agent_status(workflow["assigned_agents"])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_agent_status(self, assigned_agents: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of all assigned agents"""
        try:
            agent_summary = {
                "total_agents": len(assigned_agents),
                "agent_types": {},
                "active_agents": 0,
                "completed_tasks": 0
            }
            
            for task_key, agent_info in assigned_agents.items():
                agent_type = agent_info.get("agent_type", "unknown")
                agent_status = agent_info.get("status", "unknown")
                
                agent_summary["agent_types"][agent_type] = agent_summary["agent_types"].get(agent_type, 0) + 1
                
                if agent_status in ["ready", "executing"]:
                    agent_summary["active_agents"] += 1
                elif agent_status == "completed":
                    agent_summary["completed_tasks"] += 1
            
            return agent_summary
        except Exception as e:
            return {"error": str(e)}

    async def list_active_workflows(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """List active collaborative workflows"""
        try:
            if user_id:
                # Filter workflows for specific user
                user_workflows = [
                    workflow for workflow in self.active_workflows.values()
                    if user_id in workflow["participant_ids"] or workflow["created_by"] == user_id
                ]
                workflows_list = user_workflows
            else:
                workflows_list = list(self.active_workflows.values())
            
            return {
                "success": True,
                "workflows": workflows_list,
                "count": len(workflows_list),
                "active_sessions": len(self.collaboration_sessions)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def cancel_workflow(self, workflow_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel a collaborative workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            
            # Check permissions
            if user_id != workflow["created_by"] and user_id not in workflow["participant_ids"]:
                return {"success": False, "error": "Insufficient permissions"}
            
            # Cancel workflow and associated sessions
            workflow["status"] = "cancelled"
            workflow["cancelled_at"] = datetime.now().isoformat()
            workflow["cancelled_by"] = user_id
            
            # Cancel active sessions
            cancelled_sessions = 0
            for session in self.collaboration_sessions.values():
                if session["workflow_id"] == workflow_id and session["status"] == "running":
                    session["status"] = "cancelled"
                    cancelled_sessions += 1
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "cancelled_sessions": cancelled_sessions,
                "message": "Workflow cancelled successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_user_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get user's collaborative dashboard"""
        try:
            if user_id not in self.users:
                return {"success": False, "error": "User not found"}
            
            user_profile = self.users[user_id]
            
            # Get user's workflows
            user_workflows = [
                workflow for workflow in self.active_workflows.values()
                if user_id in workflow["participant_ids"] or workflow["created_by"] == user_id
            ]
            
            # Calculate statistics
            total_workflows = len(user_workflows)
            completed_workflows = len([w for w in user_workflows if w["status"] == "completed"])
            active_workflows = len([w for w in user_workflows if w["status"] in ["executing", "created"]])
            
            # Get recent activity
            recent_activity = []
            for workflow in user_workflows[-5:]:  # Last 5 workflows
                recent_activity.append({
                    "workflow_name": workflow["name"],
                    "status": workflow["status"],
                    "created_at": workflow["created_at"],
                    "participants": len(workflow["participant_ids"])
                })
            
            dashboard = {
                "user_profile": user_profile,
                "statistics": {
                    "total_workflows": total_workflows,
                    "completed_workflows": completed_workflows,
                    "active_workflows": active_workflows,
                    "success_rate": round(completed_workflows / max(total_workflows, 1) * 100, 1)
                },
                "recent_activity": recent_activity,
                "available_agents": list(self.agent_capabilities.keys()),
                "collaboration_score": self._calculate_collaboration_score(user_workflows)
            }
            
            return {
                "success": True,
                "dashboard": dashboard
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_collaboration_score(self, workflows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate user's collaboration effectiveness score"""
        try:
            if not workflows:
                return {"score": 0, "rating": "New User"}
            
            completed = len([w for w in workflows if w["status"] == "completed"])
            total = len(workflows)
            
            # Base score from completion rate
            completion_rate = completed / total
            base_score = completion_rate * 70
            
            # Bonus points for collaboration features
            multi_participant = len([w for w in workflows if len(w["participant_ids"]) > 1])
            collaboration_bonus = min(multi_participant * 5, 30)
            
            total_score = min(base_score + collaboration_bonus, 100)
            
            rating = "Expert" if total_score > 80 else "Advanced" if total_score > 60 else "Intermediate" if total_score > 40 else "Beginner"
            
            return {
                "score": round(total_score, 1),
                "rating": rating,
                "completion_rate": round(completion_rate * 100, 1),
                "collaboration_workflows": multi_participant
            }
        except Exception as e:
            return {"score": 0, "rating": "Error", "error": str(e)}

    async def test_connection(self) -> Dict[str, Any]:
        """Test the collaborative system connectivity"""
        try:
            # Create test user and workflow
            test_user = {
                "user_id": "test_user",
                "username": "test_user",
                "email": "test@example.com",
                "skills": ["testing"]
            }
            
            register_result = await self.register_user(test_user)
            
            test_workflow = {
                "name": "Test Collaborative Workflow",
                "created_by": "test_user",
                "participant_ids": ["test_user"],
                "tasks": [
                    {"name": "Test Task", "type": "testing", "estimated_duration": 1}
                ],
                "collaboration_mode": "sequential"
            }
            
            workflow_result = await self.create_collaborative_workflow(test_workflow)
            
            # Clean up test data
            if "test_user" in self.users:
                del self.users["test_user"]
            if workflow_result.get("success") and workflow_result.get("workflow_id"):
                workflow_id = workflow_result["workflow_id"]
                if workflow_id in self.active_workflows:
                    del self.active_workflows[workflow_id]
            
            return {
                "success": True,
                "status": "operational",
                "features": [
                    "user_registration",
                    "collaborative_workflows",
                    "agent_coordination",
                    "real_time_collaboration",
                    "workflow_management"
                ],
                "agent_types": list(self.agent_capabilities.keys()),
                "test_results": {
                    "user_registration": register_result["success"],
                    "workflow_creation": workflow_result["success"]
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}