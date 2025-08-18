import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import logging
from pymongo import MongoClient
import os

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.workflows_collection = self.db.workflows
        self.workflow_templates_collection = self.db.workflow_templates
        self.user_patterns_collection = self.db.user_patterns
        
        # Initialize default workflow templates
        asyncio.create_task(self._initialize_templates())
    
    async def _initialize_templates(self):
        """Initialize default workflow templates"""
        
        default_templates = [
            {
                "template_id": "job_search_linkedin",
                "name": "LinkedIn Job Search & Apply", 
                "description": "Search for jobs on LinkedIn and auto-apply to relevant positions",
                "category": "job_search",
                "steps": [
                    {
                        "action": "navigate",
                        "target": "linkedin.com/jobs",
                        "description": "Navigate to LinkedIn Jobs"
                    },
                    {
                        "action": "search",
                        "parameters": ["job_title", "location"],
                        "description": "Search for jobs with specified criteria"
                    },
                    {
                        "action": "filter",
                        "parameters": ["experience_level", "company_size"],
                        "description": "Apply job filters"
                    },
                    {
                        "action": "apply_jobs",
                        "parameters": ["max_applications", "auto_message"],
                        "description": "Apply to filtered job listings"
                    }
                ],
                "estimated_time": 600,
                "success_rate": 85,
                "created_at": datetime.utcnow()
            },
            {
                "template_id": "content_research",
                "name": "Multi-Source Research",
                "description": "Research a topic across multiple sources and compile results",
                "category": "research",
                "steps": [
                    {
                        "action": "search_google",
                        "parameters": ["search_query", "result_count"],
                        "description": "Search Google for primary sources"
                    },
                    {
                        "action": "search_scholar",
                        "parameters": ["academic_query"],
                        "description": "Search Google Scholar for academic sources"
                    },
                    {
                        "action": "extract_content",
                        "parameters": ["content_type", "summary_length"],
                        "description": "Extract and summarize content from sources"
                    },
                    {
                        "action": "compile_report",
                        "parameters": ["report_format", "export_location"],
                        "description": "Compile research into comprehensive report"
                    }
                ],
                "estimated_time": 450,
                "success_rate": 90,
                "created_at": datetime.utcnow()
            },
            {
                "template_id": "social_media_cross_post",
                "name": "Cross-Platform Social Posting",
                "description": "Post content across multiple social media platforms",
                "category": "social_media",
                "steps": [
                    {
                        "action": "prepare_content",
                        "parameters": ["content_text", "image_url", "hashtags"],
                        "description": "Prepare and optimize content for each platform"
                    },
                    {
                        "action": "post_linkedin",
                        "parameters": ["professional_tone"],
                        "description": "Post to LinkedIn with professional formatting"
                    },
                    {
                        "action": "post_twitter",
                        "parameters": ["thread_mode", "character_limit"],
                        "description": "Post to Twitter with optimal formatting"
                    },
                    {
                        "action": "schedule_posts",
                        "parameters": ["posting_schedule"],
                        "description": "Schedule posts for optimal engagement times"
                    }
                ],
                "estimated_time": 180,
                "success_rate": 95,
                "created_at": datetime.utcnow()
            }
        ]
        
        # Insert templates if they don't exist
        for template in default_templates:
            existing = self.workflow_templates_collection.find_one({"template_id": template["template_id"]})
            if not existing:
                self.workflow_templates_collection.insert_one(template)
                logger.info(f"Inserted workflow template: {template['name']}")
    
    async def create_workflow(self, user_session: str, template_id: str, parameters: Dict[str, Any]) -> str:
        """Create a new workflow instance from a template"""
        
        # Get template
        template = self.workflow_templates_collection.find_one({"template_id": template_id})
        if not template:
            raise ValueError(f"Workflow template {template_id} not found")
        
        workflow_id = str(uuid.uuid4())
        
        # Create workflow instance
        workflow = {
            "workflow_id": workflow_id,
            "user_session": user_session,
            "template_id": template_id,
            "name": template["name"],
            "description": template["description"],
            "category": template["category"],
            "parameters": parameters,
            "steps": template["steps"],
            "status": "created",
            "progress": 0,
            "current_step": 0,
            "results": [],
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "estimated_time": template["estimated_time"],
            "error_message": None
        }
        
        self.workflows_collection.insert_one(workflow)
        logger.info(f"Created workflow {workflow_id} from template {template_id}")
        
        return workflow_id
    
    async def get_workflow_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available workflow templates"""
        
        query = {}
        if category:
            query["category"] = category
        
        templates = list(self.workflow_templates_collection.find(
            query,
            {"_id": 0}
        ).sort("name", 1))
        
        return templates
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        
        workflow = self.workflows_collection.find_one(
            {"workflow_id": workflow_id},
            {"_id": 0}
        )
        
        if workflow:
            # Convert datetime objects to ISO format
            if workflow.get("created_at"):
                workflow["created_at"] = workflow["created_at"].isoformat()
            if workflow.get("started_at"):
                workflow["started_at"] = workflow["started_at"].isoformat()
            if workflow.get("completed_at"):
                workflow["completed_at"] = workflow["completed_at"].isoformat()
        
        return workflow
    
    async def execute_workflow_step(self, workflow_id: str, step_index: int, result: Dict[str, Any]):
        """Record the result of a workflow step execution"""
        
        update_data = {
            "current_step": step_index + 1,
            "progress": int(((step_index + 1) / 10) * 100),  # Assume max 10 steps
            f"results.{step_index}": result,
            "last_updated": datetime.utcnow()
        }
        
        # Update workflow in database
        self.workflows_collection.update_one(
            {"workflow_id": workflow_id},
            {"$set": update_data}
        )
    
    async def complete_workflow(self, workflow_id: str, final_results: Dict[str, Any]):
        """Mark a workflow as completed"""
        
        self.workflows_collection.update_one(
            {"workflow_id": workflow_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.utcnow(),
                "final_results": final_results
            }}
        )
        
        # Learn from successful workflow
        await self._learn_from_workflow(workflow_id)
    
    async def fail_workflow(self, workflow_id: str, error_message: str):
        """Mark a workflow as failed"""
        
        self.workflows_collection.update_one(
            {"workflow_id": workflow_id},
            {"$set": {
                "status": "failed",
                "completed_at": datetime.utcnow(),
                "error_message": error_message
            }}
        )
    
    async def get_user_workflows(self, user_session: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflows for a specific user"""
        
        query = {"user_session": user_session}
        if status:
            query["status"] = status
        
        workflows = list(self.workflows_collection.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(20))
        
        # Convert datetime objects
        for workflow in workflows:
            if workflow.get("created_at"):
                workflow["created_at"] = workflow["created_at"].isoformat()
            if workflow.get("started_at"):
                workflow["started_at"] = workflow["started_at"].isoformat()
            if workflow.get("completed_at"):
                workflow["completed_at"] = workflow["completed_at"].isoformat()
        
        return workflows
    
    async def _learn_from_workflow(self, workflow_id: str):
        """Learn user patterns from completed workflows"""
        
        workflow = self.workflows_collection.find_one({"workflow_id": workflow_id})
        if not workflow:
            return
        
        user_session = workflow["user_session"]
        template_id = workflow["template_id"]
        parameters = workflow["parameters"]
        
        # Update user patterns
        pattern_data = {
            "user_session": user_session,
            "template_id": template_id,
            "parameters": parameters,
            "success": workflow["status"] == "completed",
            "execution_time": (workflow.get("completed_at", datetime.utcnow()) - 
                             workflow.get("started_at", workflow["created_at"])).total_seconds(),
            "updated_at": datetime.utcnow()
        }
        
        # Store or update user pattern
        self.user_patterns_collection.replace_one(
            {"user_session": user_session, "template_id": template_id},
            pattern_data,
            upsert=True
        )
        
        logger.info(f"Learned pattern for user {user_session} and template {template_id}")
    
    async def get_personalized_suggestions(self, user_session: str, current_url: str) -> List[Dict[str, Any]]:
        """Get personalized workflow suggestions based on user patterns and current context"""
        
        suggestions = []
        
        # Get user's successful patterns
        user_patterns = list(self.user_patterns_collection.find({
            "user_session": user_session,
            "success": True
        }).sort("updated_at", -1).limit(5))
        
        # Context-based suggestions
        context_suggestions = await self._get_context_suggestions(current_url)
        
        # Combine personalized and context-based suggestions
        for pattern in user_patterns:
            template = self.workflow_templates_collection.find_one({"template_id": pattern["template_id"]})
            if template:
                suggestions.append({
                    "template_id": template["template_id"],
                    "name": template["name"],
                    "description": template["description"],
                    "category": template["category"],
                    "personalized": True,
                    "success_rate": 95,  # High because user has used it successfully before
                    "estimated_time": template["estimated_time"],
                    "suggested_parameters": pattern["parameters"]
                })
        
        # Add context-based suggestions
        suggestions.extend(context_suggestions)
        
        # Remove duplicates and limit to top 5
        seen_templates = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion["template_id"] not in seen_templates:
                seen_templates.add(suggestion["template_id"])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]
    
    async def _get_context_suggestions(self, current_url: str) -> List[Dict[str, Any]]:
        """Get workflow suggestions based on current page context"""
        
        suggestions = []
        
        # LinkedIn context
        if "linkedin.com" in current_url:
            if "/jobs/" in current_url:
                suggestions.append({
                    "template_id": "job_search_linkedin",
                    "name": "LinkedIn Job Search & Apply",
                    "description": "Auto-apply to similar job positions",
                    "category": "job_search",
                    "personalized": False,
                    "success_rate": 85,
                    "estimated_time": 600
                })
        
        # Research context
        elif any(domain in current_url for domain in ["google.com", "scholar.google.com", "wikipedia.org"]):
            suggestions.append({
                "template_id": "content_research",
                "name": "Multi-Source Research",
                "description": "Expand research across multiple academic and web sources",
                "category": "research",
                "personalized": False,
                "success_rate": 90,
                "estimated_time": 450
            })
        
        # Social media context
        elif any(domain in current_url for domain in ["twitter.com", "facebook.com", "instagram.com"]):
            suggestions.append({
                "template_id": "social_media_cross_post",
                "name": "Cross-Platform Social Posting",
                "description": "Share content across all your social media accounts",
                "category": "social_media", 
                "personalized": False,
                "success_rate": 95,
                "estimated_time": 180
            })
        
        return suggestions

# Global workflow manager instance will be initialized in server.py
workflow_manager = None