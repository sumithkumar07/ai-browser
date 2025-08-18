import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import re

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AutomationTask:
    def __init__(self, task_id: str, description: str, workflow_steps: List[Dict], user_session: str):
        self.task_id = task_id
        self.description = description
        self.workflow_steps = workflow_steps
        self.user_session = user_session
        self.status = TaskStatus.PENDING
        self.current_step = 0
        self.results = []
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.progress_percentage = 0

class AutomationEngine:
    def __init__(self):
        self.active_tasks: Dict[str, AutomationTask] = {}
        self.task_history: List[AutomationTask] = []
        self.driver_pool = []
        self.max_concurrent_tasks = 3
        
        # Pre-defined automation patterns
        self.automation_patterns = {
            "job_application": {
                "description": "Apply to jobs on job sites",
                "sites": ["linkedin.com", "indeed.com", "glassdoor.com"],
                "steps": ["search_jobs", "filter_results", "apply_to_jobs", "save_applications"]
            },
            "content_research": {
                "description": "Research and collect content from multiple sources",
                "sites": ["google.com", "scholar.google.com", "wikipedia.org"],
                "steps": ["search_query", "collect_results", "summarize_content", "save_research"]
            },
            "social_media_posting": {
                "description": "Post content across social media platforms",
                "sites": ["linkedin.com", "twitter.com", "facebook.com"],
                "steps": ["prepare_content", "post_to_platforms", "schedule_posts", "track_engagement"]
            },
            "data_collection": {
                "description": "Collect data from websites and export",
                "sites": ["any"],
                "steps": ["navigate_to_data", "extract_information", "process_data", "export_results"]
            }
        }
    
    def get_driver(self) -> webdriver.Chrome:
        """Get a Chrome WebDriver instance with optimal settings for automation"""
        options = Options()
        options.add_argument("--headless")  # Run in background
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-web-security")
        options.add_argument("--user-agent=AETHER Browser/2.0 (+http://aether.browser)")
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        return driver
    
    async def parse_natural_language_task(self, description: str, current_url: str = None) -> Dict[str, Any]:
        """Parse natural language task description into actionable workflow steps"""
        
        # Task classification patterns
        task_patterns = {
            r"apply.*job|job.*applic": "job_application",
            r"research|find.*information|collect.*data": "content_research", 
            r"post.*social|share.*social": "social_media_posting",
            r"extract.*data|scrape|collect": "data_collection"
        }
        
        # Detect task type
        task_type = "generic"
        for pattern, task_name in task_patterns.items():
            if re.search(pattern, description.lower()):
                task_type = task_name
                break
        
        # Extract key entities from description
        entities = {
            "keywords": self._extract_keywords(description),
            "sites": self._extract_sites(description),
            "actions": self._extract_actions(description),
            "quantities": self._extract_quantities(description)
        }
        
        # Generate workflow steps based on task type and entities
        workflow_steps = self._generate_workflow_steps(task_type, entities, current_url)
        
        return {
            "task_type": task_type,
            "entities": entities,
            "workflow_steps": workflow_steps,
            "estimated_duration": self._estimate_duration(workflow_steps),
            "complexity": self._calculate_complexity(workflow_steps)
        }
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract important keywords from task description"""
        # Remove common words and extract meaningful terms
        stop_words = {"the", "a", "an", "to", "for", "of", "in", "on", "with", "by"}
        words = re.findall(r'\w+', description.lower())
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _extract_sites(self, description: str) -> List[str]:
        """Extract website names from description"""
        site_patterns = [
            r'linkedin', r'indeed', r'glassdoor', r'twitter', r'facebook',
            r'instagram', r'youtube', r'google', r'github', r'notion'
        ]
        sites = []
        for pattern in site_patterns:
            if re.search(pattern, description.lower()):
                sites.append(f"{pattern}.com")
        return sites
    
    def _extract_actions(self, description: str) -> List[str]:
        """Extract action verbs from description"""
        action_patterns = {
            r'apply': 'apply',
            r'search|find': 'search',
            r'collect|gather': 'collect',
            r'save|store': 'save',
            r'post|share|publish': 'post',
            r'send|email': 'send'
        }
        
        actions = []
        for pattern, action in action_patterns.items():
            if re.search(pattern, description.lower()):
                actions.append(action)
        return actions
    
    def _extract_quantities(self, description: str) -> Dict[str, int]:
        """Extract numerical quantities from description"""
        quantities = {}
        
        # Look for numbers followed by context
        number_patterns = [
            (r'(\d+)\s*jobs?', 'job_count'),
            (r'(\d+)\s*posts?', 'post_count'),
            (r'(\d+)\s*results?', 'result_count'),
            (r'(\d+)\s*pages?', 'page_count')
        ]
        
        for pattern, key in number_patterns:
            match = re.search(pattern, description.lower())
            if match:
                quantities[key] = int(match.group(1))
        
        return quantities
    
    def _generate_workflow_steps(self, task_type: str, entities: Dict, current_url: str) -> List[Dict]:
        """Generate specific workflow steps based on task type and entities"""
        
        if task_type == "job_application":
            return [
                {
                    "step": "navigate_to_job_sites",
                    "description": "Navigate to job search websites",
                    "sites": entities.get("sites", ["linkedin.com", "indeed.com"]),
                    "estimated_time": 30
                },
                {
                    "step": "search_jobs", 
                    "description": f"Search for jobs with keywords: {', '.join(entities.get('keywords', []))}",
                    "keywords": entities.get("keywords", []),
                    "estimated_time": 60
                },
                {
                    "step": "filter_and_apply",
                    "description": f"Apply to {entities.get('quantities', {}).get('job_count', 5)} relevant positions",
                    "target_count": entities.get("quantities", {}).get("job_count", 5),
                    "estimated_time": 300
                },
                {
                    "step": "track_applications",
                    "description": "Save application details and track status",
                    "estimated_time": 60
                }
            ]
        
        elif task_type == "content_research":
            return [
                {
                    "step": "multi_site_search",
                    "description": f"Research: {', '.join(entities.get('keywords', []))}",
                    "keywords": entities.get("keywords", []),
                    "sites": ["google.com", "scholar.google.com", "wikipedia.org"],
                    "estimated_time": 120
                },
                {
                    "step": "collect_information",
                    "description": "Extract and compile relevant information",
                    "target_count": entities.get("quantities", {}).get("result_count", 10),
                    "estimated_time": 180
                },
                {
                    "step": "summarize_findings", 
                    "description": "Create comprehensive research summary",
                    "estimated_time": 90
                }
            ]
        
        elif task_type == "social_media_posting":
            return [
                {
                    "step": "prepare_content",
                    "description": "Prepare content for social media platforms",
                    "platforms": entities.get("sites", ["linkedin.com", "twitter.com"]),
                    "estimated_time": 60
                },
                {
                    "step": "cross_platform_posting",
                    "description": "Post content across selected platforms",
                    "estimated_time": 120
                },
                {
                    "step": "track_engagement",
                    "description": "Monitor post performance and engagement",
                    "estimated_time": 60
                }
            ]
        
        else:  # generic task
            return [
                {
                    "step": "analyze_current_page",
                    "description": f"Analyze current page: {current_url}",
                    "url": current_url,
                    "estimated_time": 30
                },
                {
                    "step": "execute_actions",
                    "description": f"Execute requested actions: {', '.join(entities.get('actions', []))}",
                    "actions": entities.get("actions", []),
                    "estimated_time": 120
                }
            ]
    
    def _estimate_duration(self, workflow_steps: List[Dict]) -> int:
        """Estimate total task duration in seconds"""
        return sum(step.get("estimated_time", 60) for step in workflow_steps)
    
    def _calculate_complexity(self, workflow_steps: List[Dict]) -> str:
        """Calculate task complexity level"""
        total_steps = len(workflow_steps)
        total_time = self._estimate_duration(workflow_steps)
        
        if total_steps <= 2 and total_time <= 120:
            return "simple"
        elif total_steps <= 4 and total_time <= 300:
            return "medium"
        else:
            return "complex"
    
    async def create_automation_task(self, description: str, user_session: str, current_url: str = None) -> str:
        """Create a new automation task from natural language description"""
        
        # Parse the task description
        parsed_task = await self.parse_natural_language_task(description, current_url)
        
        # Create unique task ID
        task_id = str(uuid.uuid4())
        
        # Create automation task
        task = AutomationTask(
            task_id=task_id,
            description=description,
            workflow_steps=parsed_task["workflow_steps"],
            user_session=user_session
        )
        
        # Store additional metadata
        task.task_type = parsed_task["task_type"]
        task.estimated_duration = parsed_task["estimated_duration"]
        task.complexity = parsed_task["complexity"]
        
        self.active_tasks[task_id] = task
        
        logger.info(f"Created automation task {task_id}: {description}")
        return task_id
    
    async def execute_automation_task(self, task_id: str) -> bool:
        """Execute an automation task in the background"""
        
        if task_id not in self.active_tasks:
            return False
        
        task = self.active_tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            # Execute workflow steps
            for i, step in enumerate(task.workflow_steps):
                if task.status == TaskStatus.CANCELLED:
                    break
                
                task.current_step = i
                task.progress_percentage = int((i / len(task.workflow_steps)) * 100)
                
                logger.info(f"Executing step {i+1}/{len(task.workflow_steps)}: {step.get('description', '')}")
                
                # Execute the specific step
                step_result = await self._execute_workflow_step(step, task)
                task.results.append(step_result)
                
                # Small delay between steps
                await asyncio.sleep(2)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100
            
            logger.info(f"Automation task {task_id} completed successfully")
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            
            logger.error(f"Automation task {task_id} failed: {e}")
            return False
        
        finally:
            # Move to history after completion
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                self.task_history.append(task)
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
    
    async def _execute_workflow_step(self, step: Dict, task: AutomationTask) -> Dict[str, Any]:
        """Execute a single workflow step"""
        
        step_type = step.get("step", "")
        result = {
            "step_type": step_type,
            "status": "success",
            "data": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Simulate step execution based on type
            if step_type == "navigate_to_job_sites":
                result["data"] = {
                    "sites_visited": step.get("sites", []),
                    "navigation_time": step.get("estimated_time", 30)
                }
                
            elif step_type == "search_jobs":
                result["data"] = {
                    "keywords_used": step.get("keywords", []),
                    "jobs_found": 25,  # Simulated
                    "search_time": step.get("estimated_time", 60)
                }
                
            elif step_type == "filter_and_apply":
                target_count = step.get("target_count", 5)
                result["data"] = {
                    "applications_submitted": min(target_count, 8),  # Simulated
                    "target_count": target_count,
                    "success_rate": "80%"
                }
                
            elif step_type == "multi_site_search":
                result["data"] = {
                    "sites_searched": step.get("sites", []),
                    "results_found": 15,  # Simulated
                    "keywords": step.get("keywords", [])
                }
                
            else:
                # Generic step execution
                result["data"] = {
                    "step_completed": True,
                    "execution_time": step.get("estimated_time", 60)
                }
            
            # Simulate processing time
            await asyncio.sleep(min(step.get("estimated_time", 60) / 10, 5))
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an automation task"""
        
        # Check active tasks first
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
        else:
            # Check history
            task = next((t for t in self.task_history if t.task_id == task_id), None)
            if not task:
                return None
        
        return {
            "task_id": task.task_id,
            "description": task.description,
            "status": task.status.value,
            "progress_percentage": task.progress_percentage,
            "current_step": task.current_step,
            "total_steps": len(task.workflow_steps),
            "current_step_description": task.workflow_steps[task.current_step].get("description", "") if task.current_step < len(task.workflow_steps) else "",
            "results": task.results,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "estimated_duration": getattr(task, 'estimated_duration', 0),
            "complexity": getattr(task, 'complexity', 'medium'),
            "error_message": task.error_message
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running automation task"""
        
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            logger.info(f"Cancelled automation task {task_id}")
            return True
        
        return False
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of all active automation tasks"""
        return [await self.get_task_status(task_id) for task_id in self.active_tasks.keys()]
    
    async def suggest_automations(self, current_url: str, page_content: str = "") -> List[Dict[str, Any]]:
        """Suggest relevant automations based on current page context"""
        
        suggestions = []
        
        # LinkedIn suggestions
        if "linkedin.com" in current_url:
            if "/jobs/" in current_url:
                suggestions.append({
                    "title": "Auto-Apply to Similar Jobs",
                    "description": "Apply to jobs matching your criteria automatically",
                    "command": "Apply to 5 similar data science jobs",
                    "estimated_time": "5-10 minutes",
                    "complexity": "medium"
                })
            elif "/in/" in current_url or "/profile/" in current_url:
                suggestions.append({
                    "title": "Connect with Similar Professionals", 
                    "description": "Send connection requests to professionals in your field",
                    "command": "Connect with 10 data scientists in my network",
                    "estimated_time": "3-5 minutes",
                    "complexity": "simple"
                })
        
        # Job site suggestions
        elif any(site in current_url for site in ["indeed.com", "glassdoor.com", "dice.com"]):
            suggestions.append({
                "title": "Mass Job Application",
                "description": "Apply to multiple relevant positions at once",
                "command": "Apply to 10 software engineer jobs",
                "estimated_time": "10-15 minutes", 
                "complexity": "complex"
            })
        
        # Research sites
        elif any(site in current_url for site in ["google.com", "scholar.google.com", "wikipedia.org"]):
            suggestions.append({
                "title": "Research Assistant",
                "description": "Gather comprehensive research on a topic",
                "command": "Research artificial intelligence trends and create summary",
                "estimated_time": "5-8 minutes",
                "complexity": "medium"
            })
        
        # Social media suggestions
        elif any(site in current_url for site in ["twitter.com", "facebook.com"]):
            suggestions.append({
                "title": "Cross-Platform Content Sharing",
                "description": "Share this content across your social media accounts", 
                "command": "Share this article on LinkedIn and Twitter",
                "estimated_time": "2-3 minutes",
                "complexity": "simple"
            })
        
        # Generic suggestions for any site
        suggestions.extend([
            {
                "title": "Save to Research Collection",
                "description": "Save this page content for later research",
                "command": "Save this page to my research collection",
                "estimated_time": "1 minute",
                "complexity": "simple"
            },
            {
                "title": "Smart Summary & Share",
                "description": "Create AI summary and share with team",
                "command": "Summarize this page and email to my team",
                "estimated_time": "2-3 minutes", 
                "complexity": "simple"
            }
        ])
        
        return suggestions[:3]  # Return top 3 suggestions

# Global automation engine instance
automation_engine = AutomationEngine()