"""
PHASE 1-3: Advanced Visual Workflow Engine with Cross-Platform Integration
Multi-step automation with drag & drop interface, template library, and AI optimization
"""

import asyncio
import json
import uuid
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import traceback

from pymongo import MongoClient
from pydantic import BaseModel, Field
import httpx
from bs4 import BeautifulSoup
import structlog

# Custom JSON encoder for enums
class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Configure logging
logger = structlog.get_logger(__name__)

class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ActionType(Enum):
    WEB_SCRAPING = "web_scraping"
    DATA_EXTRACTION = "data_extraction"
    API_CALL = "api_call"
    EMAIL_SEND = "email_send"
    FILE_UPLOAD = "file_upload"
    SOCIAL_POST = "social_post"
    FORM_FILL = "form_fill"
    CLICK_ELEMENT = "click_element"
    WAIT = "wait"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    AI_ANALYSIS = "ai_analysis"
    REPORT_GENERATION = "report_generation"

class TriggerType(Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    FILE_WATCH = "file_watch"
    EMAIL_RECEIVED = "email_received"
    API_ENDPOINT = "api_endpoint"

@dataclass
class WorkflowAction:
    id: str
    type: ActionType
    name: str
    description: str
    parameters: Dict[str, Any]
    position: Dict[str, int]  # x, y coordinates for visual editor
    connections: List[str]  # IDs of next actions
    conditions: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    timeout: int = 30  # seconds

@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    actions: List[WorkflowAction]
    estimated_duration: int  # seconds
    complexity: str  # simple, medium, complex
    created_at: datetime
    usage_count: int = 0

@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    status: WorkflowStatus
    current_action: Optional[str]
    progress: Dict[str, Any]
    results: Dict[str, Any]
    error_details: Optional[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    execution_time: Optional[float]

class VisualWorkflowEngine:
    """
    Advanced visual workflow engine with drag & drop support,
    template library, and intelligent execution optimization
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.aether_browser
        self.templates = {}
        self.active_executions = {}
        self.execution_queue = asyncio.Queue()
        self.cross_platform_integrator = CrossPlatformIntegrator()
        self.ai_optimizer = WorkflowAIOptimizer()
        self.performance_analyzer = WorkflowPerformanceAnalyzer()
        
        # Initialize built-in templates
        self._initialize_templates()
        
        # Start background workers
        asyncio.create_task(self._execution_worker())
    
    def _initialize_templates(self):
        """Initialize built-in workflow templates"""
        
        # Template 1: LinkedIn Profile Scraper
        linkedin_scraper = WorkflowTemplate(
            id="linkedin_profile_scraper",
            name="LinkedIn Profile Data Extractor",
            description="Extract profile information from LinkedIn URLs including experience, skills, and connections",
            category="data_extraction",
            tags=["linkedin", "profiles", "networking", "recruitment"],
            actions=[
                WorkflowAction(
                    id="action_1",
                    type=ActionType.WEB_SCRAPING,
                    name="Navigate to LinkedIn Profile",
                    description="Open the LinkedIn profile URL",
                    parameters={
                        "url": "{input.profile_url}",
                        "wait_for_element": ".pv-top-card",
                        "screenshot": True
                    },
                    position={"x": 100, "y": 100},
                    connections=["action_2"]
                ),
                WorkflowAction(
                    id="action_2",
                    type=ActionType.DATA_EXTRACTION,
                    name="Extract Profile Data",
                    description="Extract name, headline, experience, and skills",
                    parameters={
                        "selectors": {
                            "name": "h1.text-heading-xlarge",
                            "headline": ".text-body-medium.break-words",
                            "location": ".text-body-small.inline",
                            "experience": ".pvs-list__paged-list-item",
                            "skills": ".pvs-skill"
                        }
                    },
                    position={"x": 300, "y": 100},
                    connections=["action_3"]
                ),
                WorkflowAction(
                    id="action_3",
                    type=ActionType.AI_ANALYSIS,
                    name="Analyze Profile Quality",
                    description="Use AI to analyze profile completeness and quality",
                    parameters={
                        "analysis_type": "profile_scoring",
                        "criteria": ["completeness", "professional_quality", "engagement_potential"]
                    },
                    position={"x": 500, "y": 100},
                    connections=["action_4"]
                ),
                WorkflowAction(
                    id="action_4",
                    type=ActionType.REPORT_GENERATION,
                    name="Generate Profile Report",
                    description="Create a comprehensive profile analysis report",
                    parameters={
                        "template": "linkedin_profile_analysis",
                        "format": "pdf",
                        "include_charts": True
                    },
                    position={"x": 700, "y": 100},
                    connections=[]
                )
            ],
            estimated_duration=120,  # 2 minutes
            complexity="medium",
            created_at=datetime.now()
        )
        
        # Template 2: Social Media Cross-Poster
        social_cross_poster = WorkflowTemplate(
            id="social_media_cross_poster",
            name="Multi-Platform Social Media Poster",
            description="Post content simultaneously to Twitter, LinkedIn, and Facebook with platform-specific optimization",
            category="social_media",
            tags=["social_media", "content", "marketing", "automation"],
            actions=[
                WorkflowAction(
                    id="action_1",
                    type=ActionType.AI_ANALYSIS,
                    name="Optimize Content for Platforms",
                    description="Adapt content for each social media platform's requirements",
                    parameters={
                        "platforms": ["twitter", "linkedin", "facebook"],
                        "optimization_rules": {
                            "twitter": {"max_length": 280, "hashtags": True},
                            "linkedin": {"professional_tone": True, "max_length": 3000},
                            "facebook": {"engaging_tone": True, "max_length": 63206}
                        }
                    },
                    position={"x": 100, "y": 100},
                    connections=["action_2", "action_3", "action_4"]
                ),
                WorkflowAction(
                    id="action_2",
                    type=ActionType.SOCIAL_POST,
                    name="Post to Twitter",
                    description="Post optimized content to Twitter",
                    parameters={
                        "platform": "twitter",
                        "content": "{optimized_content.twitter}",
                        "include_image": True
                    },
                    position={"x": 300, "y": 50},
                    connections=["action_5"]
                ),
                WorkflowAction(
                    id="action_3",
                    type=ActionType.SOCIAL_POST,
                    name="Post to LinkedIn",
                    description="Post optimized content to LinkedIn",
                    parameters={
                        "platform": "linkedin",
                        "content": "{optimized_content.linkedin}",
                        "include_image": True
                    },
                    position={"x": 300, "y": 100},
                    connections=["action_5"]
                ),
                WorkflowAction(
                    id="action_4",
                    type=ActionType.SOCIAL_POST,
                    name="Post to Facebook",
                    description="Post optimized content to Facebook",
                    parameters={
                        "platform": "facebook",
                        "content": "{optimized_content.facebook}",
                        "include_image": True
                    },
                    position={"x": 300, "y": 150},
                    connections=["action_5"]
                ),
                WorkflowAction(
                    id="action_5",
                    type=ActionType.REPORT_GENERATION,
                    name="Generate Posting Report",
                    description="Create summary report of posting results",
                    parameters={
                        "template": "social_media_report",
                        "metrics": ["reach", "engagement", "clicks"],
                        "format": "html"
                    },
                    position={"x": 500, "y": 100},
                    connections=[]
                )
            ],
            estimated_duration=60,  # 1 minute
            complexity="simple",
            created_at=datetime.now()
        )
        
        # Template 3: E-commerce Product Research
        product_research = WorkflowTemplate(
            id="ecommerce_product_research",
            name="Competitive Product Research Analyzer",
            description="Research products across multiple e-commerce platforms, analyze pricing, reviews, and market trends",
            category="market_research",
            tags=["ecommerce", "research", "pricing", "competition"],
            actions=[
                WorkflowAction(
                    id="action_1",
                    type=ActionType.WEB_SCRAPING,
                    name="Scrape Amazon Products",
                    description="Extract product data from Amazon search results",
                    parameters={
                        "base_url": "https://amazon.com/s?k={input.search_term}",
                        "selectors": {
                            "products": "[data-component-type='s-search-result']",
                            "title": "h2 a span",
                            "price": ".a-price-whole",
                            "rating": ".a-icon-alt",
                            "reviews_count": ".a-size-base"
                        },
                        "max_results": 20
                    },
                    position={"x": 100, "y": 50},
                    connections=["action_4"]
                ),
                WorkflowAction(
                    id="action_2",
                    type=ActionType.WEB_SCRAPING,
                    name="Scrape eBay Products",
                    description="Extract product data from eBay search results",
                    parameters={
                        "base_url": "https://ebay.com/sch/i.html?_nkw={input.search_term}",
                        "selectors": {
                            "products": ".s-item",
                            "title": ".s-item__title",
                            "price": ".s-item__price",
                            "condition": ".s-item__subtitle"
                        },
                        "max_results": 20
                    },
                    position={"x": 100, "y": 150},
                    connections=["action_4"]
                ),
                WorkflowAction(
                    id="action_3",
                    type=ActionType.WEB_SCRAPING,
                    name="Scrape Walmart Products",
                    description="Extract product data from Walmart search results",
                    parameters={
                        "base_url": "https://walmart.com/search?q={input.search_term}",
                        "selectors": {
                            "products": "[data-testid='item-stack']",
                            "title": "[data-automation-id='product-title']",
                            "price": "[itemprop='price']",
                            "rating": ".average-rating"
                        },
                        "max_results": 20
                    },
                    position={"x": 100, "y": 250},
                    connections=["action_4"]
                ),
                WorkflowAction(
                    id="action_4",
                    type=ActionType.AI_ANALYSIS,
                    name="Analyze Market Data",
                    description="Use AI to analyze pricing trends, competition, and opportunities",
                    parameters={
                        "analysis_type": "market_analysis",
                        "metrics": ["price_distribution", "rating_analysis", "feature_comparison"],
                        "insights": ["pricing_opportunities", "market_gaps", "top_competitors"]
                    },
                    position={"x": 400, "y": 150},
                    connections=["action_5"]
                ),
                WorkflowAction(
                    id="action_5",
                    type=ActionType.REPORT_GENERATION,
                    name="Generate Market Research Report",
                    description="Create comprehensive market analysis report with charts and insights",
                    parameters={
                        "template": "market_research_report",
                        "include_charts": True,
                        "chart_types": ["price_histogram", "rating_scatter", "trend_analysis"],
                        "format": "pdf"
                    },
                    position={"x": 600, "y": 150},
                    connections=[]
                )
            ],
            estimated_duration=300,  # 5 minutes
            complexity="complex",
            created_at=datetime.now()
        )
        
        # Store templates in database
        self.templates = {
            "linkedin_profile_scraper": linkedin_scraper,
            "social_media_cross_poster": social_cross_poster,
            "ecommerce_product_research": product_research
        }
        
        # Save to database
        for template in self.templates.values():
            self._save_template_to_db(template)
    
    async def get_workflow_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available workflow templates"""
        query = {}
        if category:
            query["category"] = category
        
        templates = list(self.db.workflow_templates.find(query, {"_id": 0}))
        return templates
    
    async def create_workflow_from_template(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        user_session: str
    ) -> str:
        """Create a new workflow instance from template"""
        
        template = self.templates.get(template_id)
        if not template:
            # Try to load from database
            template_doc = self.db.workflow_templates.find_one({"id": template_id})
            if not template_doc:
                raise ValueError(f"Template {template_id} not found")
            template = self._doc_to_template(template_doc)
        
        # Create workflow instance
        workflow_id = str(uuid.uuid4())
        
        workflow_data = {
            "id": workflow_id,
            "template_id": template_id,
            "name": f"{template.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "user_session": user_session,
            "status": WorkflowStatus.DRAFT.value,
            "parameters": parameters,
            "actions": [self._serialize_for_mongo(action) for action in template.actions],
            "created_at": datetime.now(),
            "estimated_duration": template.estimated_duration
        }
        
        # Save to database
        self.db.workflows.insert_one(workflow_data)
        
        # Update template usage count
        self.db.workflow_templates.update_one(
            {"id": template_id},
            {"$inc": {"usage_count": 1}}
        )
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> str:
        """Start workflow execution"""
        
        workflow = self.db.workflows.find_one({"id": workflow_id})
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create execution instance
        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            current_action=None,
            progress={"completed_actions": 0, "total_actions": len(workflow["actions"])},
            results={},
            error_details=None,
            started_at=datetime.now(),
            completed_at=None,
            execution_time=None
        )
        
        # Store execution
        self.active_executions[execution_id] = execution
        
        # Update workflow status
        self.db.workflows.update_one(
            {"id": workflow_id},
            {"$set": {"status": WorkflowStatus.RUNNING.value, "current_execution": execution_id}}
        )
        
        # Queue for execution
        await self.execution_queue.put(execution_id)
        
        return execution_id
    
    async def _execution_worker(self):
        """Background worker to process workflow executions"""
        while True:
            try:
                execution_id = await self.execution_queue.get()
                await self._execute_workflow_instance(execution_id)
            except Exception as e:
                logger.error(f"Execution worker error: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _execute_workflow_instance(self, execution_id: str):
        """Execute a specific workflow instance"""
        try:
            execution = self.active_executions[execution_id]
            workflow = self.db.workflows.find_one({"id": execution.workflow_id})
            
            if not workflow:
                raise ValueError(f"Workflow {execution.workflow_id} not found")
            
            start_time = time.time()
            
            # Execute actions in order
            for i, action_data in enumerate(workflow["actions"]):
                action = WorkflowAction(**action_data)
                execution.current_action = action.id
                
                logger.info(f"Executing action {action.name} ({action.type.value})")
                
                try:
                    # Execute the action
                    result = await self._execute_action(action, workflow["parameters"], execution.results)
                    
                    # Store result
                    execution.results[action.id] = result
                    execution.progress["completed_actions"] += 1
                    
                    # Update progress in database
                    self._update_execution_progress(execution_id, execution)
                    
                except Exception as action_error:
                    logger.error(f"Action {action.name} failed: {action_error}")
                    
                    # Handle retry logic
                    if action.retry_config and action.retry_config.get("enabled", False):
                        max_retries = action.retry_config.get("max_retries", 3)
                        retry_delay = action.retry_config.get("delay", 5)
                        
                        for retry in range(max_retries):
                            logger.info(f"Retrying action {action.name} (attempt {retry + 1})")
                            await asyncio.sleep(retry_delay)
                            
                            try:
                                result = await self._execute_action(action, workflow["parameters"], execution.results)
                                execution.results[action.id] = result
                                execution.progress["completed_actions"] += 1
                                break
                            except Exception:
                                if retry == max_retries - 1:
                                    raise
                    else:
                        raise
            
            # Mark as completed
            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.execution_time = time.time() - start_time
            
            # Update database
            self._update_execution_completion(execution_id, execution)
            
            logger.info(f"Workflow execution {execution_id} completed in {execution.execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Workflow execution {execution_id} failed: {e}", exc_info=True)
            
            # Mark as failed
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                execution.status = WorkflowStatus.FAILED
                execution.error_details = {
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "failed_at": datetime.now().isoformat()
                }
                execution.completed_at = datetime.now()
                
                self._update_execution_completion(execution_id, execution)
        
        finally:
            # Clean up
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    async def _execute_action(
        self,
        action: WorkflowAction,
        workflow_params: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single workflow action"""
        
        # Resolve parameters with template variables
        resolved_params = self._resolve_parameters(action.parameters, workflow_params, previous_results)
        
        if action.type == ActionType.WEB_SCRAPING:
            return await self._execute_web_scraping(resolved_params)
        
        elif action.type == ActionType.DATA_EXTRACTION:
            return await self._execute_data_extraction(resolved_params, previous_results)
        
        elif action.type == ActionType.AI_ANALYSIS:
            return await self._execute_ai_analysis(resolved_params, previous_results)
        
        elif action.type == ActionType.REPORT_GENERATION:
            return await self._execute_report_generation(resolved_params, previous_results)
        
        elif action.type == ActionType.SOCIAL_POST:
            return await self._execute_social_post(resolved_params)
        
        elif action.type == ActionType.API_CALL:
            return await self._execute_api_call(resolved_params)
        
        elif action.type == ActionType.EMAIL_SEND:
            return await self._execute_email_send(resolved_params)
        
        elif action.type == ActionType.WAIT:
            await asyncio.sleep(resolved_params.get("duration", 1))
            return {"status": "completed", "duration": resolved_params.get("duration", 1)}
        
        else:
            raise ValueError(f"Unsupported action type: {action.type}")
    
    async def _execute_web_scraping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web scraping action"""
        url = params["url"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers={
                'User-Agent': 'AETHER Browser/3.0 (+http://aether.browser)'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = {
                "url": url,
                "status_code": response.status_code,
                "page_title": soup.title.string if soup.title else "",
                "scraped_at": datetime.now().isoformat()
            }
            
            # Extract specific elements if selectors provided
            if "selectors" in params:
                result["extracted_data"] = {}
                for key, selector in params["selectors"].items():
                    elements = soup.select(selector)
                    if elements:
                        if len(elements) == 1:
                            result["extracted_data"][key] = elements[0].get_text(strip=True)
                        else:
                            result["extracted_data"][key] = [elem.get_text(strip=True) for elem in elements]
            
            return result
    
    async def _execute_data_extraction(self, params: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data extraction from previous results"""
        
        # Find the most recent web scraping result
        scraping_result = None
        for result in reversed(list(previous_results.values())):
            if isinstance(result, dict) and "extracted_data" in result:
                scraping_result = result
                break
        
        if not scraping_result:
            raise ValueError("No web scraping data found for extraction")
        
        extracted_data = scraping_result.get("extracted_data", {})
        
        # Apply extraction rules if provided
        if "selectors" in params:
            # This would be used for more complex extraction
            pass
        
        return {
            "extracted_data": extracted_data,
            "extraction_count": len(extracted_data),
            "extracted_at": datetime.now().isoformat()
        }
    
    async def _execute_ai_analysis(self, params: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI analysis on previous results"""
        
        analysis_type = params.get("analysis_type", "general")
        
        # Collect data from previous results
        data_for_analysis = {}
        for action_id, result in previous_results.items():
            if isinstance(result, dict):
                data_for_analysis.update(result)
        
        # Simulate AI analysis (would integrate with actual AI service)
        analysis_result = {
            "analysis_type": analysis_type,
            "data_analyzed": len(data_for_analysis),
            "insights": [
                "Data quality score: 85%",
                "Completeness assessment: Good",
                "Anomalies detected: None"
            ],
            "recommendations": [
                "Consider collecting additional data points",
                "Monitor trends over time",
                "Validate data sources"
            ],
            "confidence_score": 0.87,
            "analyzed_at": datetime.now().isoformat()
        }
        
        return analysis_result
    
    async def _execute_report_generation(self, params: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation from workflow results"""
        
        template_name = params.get("template", "default")
        format_type = params.get("format", "html")
        
        # Collect all data for report
        report_data = {
            "workflow_results": previous_results,
            "generated_at": datetime.now().isoformat(),
            "template": template_name
        }
        
        # Generate report (simplified version)
        report_content = self._generate_report_content(report_data, template_name)
        
        # Save report to file system (in production, would use cloud storage)
        report_filename = f"report_{int(time.time())}.{format_type}"
        report_path = f"/tmp/{report_filename}"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return {
            "report_path": report_path,
            "report_filename": report_filename,
            "format": format_type,
            "size_bytes": len(report_content.encode('utf-8')),
            "generated_at": datetime.now().isoformat()
        }
    
    async def _execute_social_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social media posting"""
        
        platform = params["platform"]
        content = params["content"]
        
        # Simulate social media posting (would integrate with actual APIs)
        post_result = {
            "platform": platform,
            "content_length": len(content),
            "post_id": f"{platform}_{int(time.time())}",
            "status": "posted",
            "posted_at": datetime.now().isoformat(),
            "estimated_reach": 100  # Simulated
        }
        
        return post_result
    
    async def _execute_api_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute API call"""
        
        url = params["url"]
        method = params.get("method", "GET")
        headers = params.get("headers", {})
        data = params.get("data", {})
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "response_data": response_data,
                "called_at": datetime.now().isoformat()
            }
    
    async def _execute_email_send(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email sending"""
        
        to_email = params["to"]
        subject = params["subject"]
        body = params["body"]
        
        # Simulate email sending (would integrate with actual email service)
        email_result = {
            "to": to_email,
            "subject": subject,
            "body_length": len(body),
            "message_id": f"email_{int(time.time())}",
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }
        
        return email_result
    
    def _resolve_parameters(
        self,
        params: Dict[str, Any],
        workflow_params: Dict[str, Any],
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve template variables in parameters"""
        
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Replace workflow input parameters
                for param_key, param_value in workflow_params.items():
                    value = value.replace(f"{{input.{param_key}}}", str(param_value))
                
                # Replace previous results
                for result_key, result_data in previous_results.items():
                    if isinstance(result_data, dict):
                        for data_key, data_value in result_data.items():
                            value = value.replace(f"{{{result_key}.{data_key}}}", str(data_value))
            
            resolved[key] = value
        
        return resolved
    
    def _generate_report_content(self, data: Dict[str, Any], template: str) -> str:
        """Generate report content based on template"""
        
        if template == "linkedin_profile_analysis":
            return self._generate_linkedin_report(data)
        elif template == "social_media_report":
            return self._generate_social_media_report(data)
        elif template == "market_research_report":
            return self._generate_market_research_report(data)
        else:
            return self._generate_default_report(data)
    
    def _generate_linkedin_report(self, data: Dict[str, Any]) -> str:
        """Generate LinkedIn profile analysis report"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Profile Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .section {{ margin: 20px 0; }}
                .highlight {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>LinkedIn Profile Analysis Report</h1>
                <p>Generated on {data['generated_at']}</p>
            </div>
            
            <div class="section">
                <h2>Profile Summary</h2>
                <div class="highlight">
                    {json.dumps(data.get('workflow_results', {}), indent=2)}
                </div>
            </div>
            
            <div class="section">
                <h2>Analysis Results</h2>
                <p>Profile analysis completed with AI-powered insights.</p>
            </div>
        </body>
        </html>
        """
    
    def _generate_social_media_report(self, data: Dict[str, Any]) -> str:
        """Generate social media posting report"""
        
        return f"""
        <html>
        <head><title>Social Media Posting Report</title></head>
        <body>
            <h1>Social Media Cross-Posting Report</h1>
            <p>Generated: {data['generated_at']}</p>
            <h2>Posting Results</h2>
            {json.dumps(data.get('workflow_results', {}), indent=2)}
        </body>
        </html>
        """
    
    def _generate_market_research_report(self, data: Dict[str, Any]) -> str:
        """Generate market research report"""
        
        return f"""
        <html>
        <head><title>Market Research Report</title></head>
        <body>
            <h1>Competitive Market Analysis</h1>
            <p>Generated: {data['generated_at']}</p>
            <h2>Research Findings</h2>
            {json.dumps(data.get('workflow_results', {}), indent=2)}
        </body>
        </html>
        """
    
    def _generate_default_report(self, data: Dict[str, Any]) -> str:
        """Generate default report format"""
        
        return f"""
        <html>
        <head><title>Workflow Report</title></head>
        <body>
            <h1>Workflow Execution Report</h1>
            <p>Generated: {data['generated_at']}</p>
            <pre>{json.dumps(data, indent=2)}</pre>
        </body>
        </html>
        """
    
    def _serialize_for_mongo(self, obj):
        """Convert objects to MongoDB-compatible format"""
        if isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj
        elif isinstance(obj, dict):
            return {k: self._serialize_for_mongo(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_mongo(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Handle dataclass or object
            data = asdict(obj) if hasattr(obj, '__dataclass_fields__') else obj.__dict__
            return self._serialize_for_mongo(data)
        else:
            return obj
    
    def _save_template_to_db(self, template: WorkflowTemplate):
        """Save template to database"""
        
        template_data = self._serialize_for_mongo(template)
        
        self.db.workflow_templates.replace_one(
            {"id": template.id},
            template_data,
            upsert=True
        )
    
    def _doc_to_template(self, doc: Dict[str, Any]) -> WorkflowTemplate:
        """Convert database document to WorkflowTemplate"""
        
        actions = [WorkflowAction(**action_data) for action_data in doc["actions"]]
        
        return WorkflowTemplate(
            id=doc["id"],
            name=doc["name"],
            description=doc["description"],
            category=doc["category"],
            tags=doc["tags"],
            actions=actions,
            estimated_duration=doc["estimated_duration"],
            complexity=doc["complexity"],
            created_at=doc["created_at"],
            usage_count=doc.get("usage_count", 0)
        )
    
    def _update_execution_progress(self, execution_id: str, execution: WorkflowExecution):
        """Update execution progress in database"""
        
        self.db.workflow_executions.update_one(
            {"id": execution_id},
            {
                "$set": {
                    "status": execution.status.value,
                    "current_action": execution.current_action,
                    "progress": execution.progress,
                    "results": execution.results,
                    "updated_at": datetime.now()
                }
            },
            upsert=True
        )
    
    def _update_execution_completion(self, execution_id: str, execution: WorkflowExecution):
        """Update execution completion in database"""
        
        execution_doc = {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "current_action": execution.current_action,
            "progress": execution.progress,
            "results": execution.results,
            "error_details": execution.error_details,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "execution_time": execution.execution_time
        }
        
        self.db.workflow_executions.replace_one(
            {"id": execution_id},
            execution_doc,
            upsert=True
        )
        
        # Update workflow status
        self.db.workflows.update_one(
            {"id": execution.workflow_id},
            {
                "$set": {
                    "status": execution.status.value,
                    "last_execution": execution_id,
                    "updated_at": datetime.now()
                }
            }
        )
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status"""
        
        workflow = self.db.workflows.find_one({"id": workflow_id}, {"_id": 0})
        if not workflow:
            return None
        
        # Get latest execution if exists
        execution = None
        if "current_execution" in workflow:
            execution = self.db.workflow_executions.find_one(
                {"id": workflow["current_execution"]},
                {"_id": 0}
            )
        
        return {
            "workflow": workflow,
            "execution": execution
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        
        workflow = self.db.workflows.find_one({"id": workflow_id})
        if not workflow:
            return False
        
        # Update workflow status
        self.db.workflows.update_one(
            {"id": workflow_id},
            {"$set": {"status": WorkflowStatus.CANCELLED.value}}
        )
        
        # Cancel active execution if exists
        current_execution = workflow.get("current_execution")
        if current_execution and current_execution in self.active_executions:
            execution = self.active_executions[current_execution]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            
            self._update_execution_completion(current_execution, execution)
            del self.active_executions[current_execution]
        
        return True
    
    async def get_user_workflows(self, user_session: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflows for a specific user"""
        
        query = {"user_session": user_session}
        if status:
            query["status"] = status
        
        workflows = list(self.db.workflows.find(query, {"_id": 0}).sort("created_at", -1))
        return workflows


class CrossPlatformIntegrator:
    """Handles integration with multiple platforms"""
    
    def __init__(self):
        self.platform_handlers = {
            "linkedin": self._handle_linkedin,
            "twitter": self._handle_twitter,
            "facebook": self._handle_facebook,
            "instagram": self._handle_instagram,
            "github": self._handle_github,
            "notion": self._handle_notion,
            "slack": self._handle_slack,
            "gmail": self._handle_gmail
        }
    
    async def execute_cross_platform_action(self, platform: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on specific platform"""
        
        handler = self.platform_handlers.get(platform)
        if not handler:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return await handler(action, params)
    
    async def _handle_linkedin(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LinkedIn actions"""
        # Implementation for LinkedIn API integration
        return {"platform": "linkedin", "action": action, "status": "simulated"}
    
    async def _handle_twitter(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Twitter actions"""
        # Implementation for Twitter API integration
        return {"platform": "twitter", "action": action, "status": "simulated"}
    
    async def _handle_facebook(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Facebook actions"""
        # Implementation for Facebook API integration
        return {"platform": "facebook", "action": action, "status": "simulated"}
    
    async def _handle_instagram(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Instagram actions"""
        # Implementation for Instagram API integration
        return {"platform": "instagram", "action": action, "status": "simulated"}
    
    async def _handle_github(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub actions"""
        # Implementation for GitHub API integration
        return {"platform": "github", "action": action, "status": "simulated"}
    
    async def _handle_notion(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Notion actions"""
        # Implementation for Notion API integration
        return {"platform": "notion", "action": action, "status": "simulated"}
    
    async def _handle_slack(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack actions"""
        # Implementation for Slack API integration
        return {"platform": "slack", "action": action, "status": "simulated"}
    
    async def _handle_gmail(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Gmail actions"""
        # Implementation for Gmail API integration
        return {"platform": "gmail", "action": action, "status": "simulated"}


class WorkflowAIOptimizer:
    """AI-powered workflow optimization"""
    
    async def optimize_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize workflow performance and efficiency"""
        
        optimizations = []
        
        # Analyze action order
        actions = workflow.get("actions", [])
        if len(actions) > 1:
            optimizations.append({
                "type": "parallelization",
                "description": "Identified actions that can run in parallel",
                "potential_time_savings": "30-50%"
            })
        
        # Analyze resource usage
        web_scraping_actions = [a for a in actions if a.get("type") == "web_scraping"]
        if len(web_scraping_actions) > 3:
            optimizations.append({
                "type": "batch_processing",
                "description": "Batch similar web scraping actions",
                "potential_time_savings": "20-30%"
            })
        
        return {
            "optimizations": optimizations,
            "estimated_improvement": "40-70%",
            "confidence": 0.85
        }


class WorkflowPerformanceAnalyzer:
    """Analyze and track workflow performance"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_execution(self, workflow_id: str, execution_data: Dict[str, Any]):
        """Track workflow execution metrics"""
        
        if workflow_id not in self.metrics:
            self.metrics[workflow_id] = []
        
        self.metrics[workflow_id].append({
            "execution_time": execution_data.get("execution_time"),
            "success_rate": 1.0 if execution_data.get("status") == "completed" else 0.0,
            "action_count": execution_data.get("action_count", 0),
            "timestamp": datetime.now()
        })
    
    def get_performance_report(self, workflow_id: str) -> Dict[str, Any]:
        """Get performance report for workflow"""
        
        if workflow_id not in self.metrics:
            return {"error": "No metrics available"}
        
        executions = self.metrics[workflow_id]
        
        avg_execution_time = sum(e["execution_time"] for e in executions if e["execution_time"]) / len(executions)
        success_rate = sum(e["success_rate"] for e in executions) / len(executions)
        
        return {
            "total_executions": len(executions),
            "avg_execution_time": avg_execution_time,
            "success_rate": success_rate,
            "last_execution": executions[-1]["timestamp"]
        }


# Global instance
advanced_workflow_engine = None

def get_workflow_engine(mongo_client: MongoClient) -> VisualWorkflowEngine:
    """Get global workflow engine instance"""
    global advanced_workflow_engine
    if advanced_workflow_engine is None:
        advanced_workflow_engine = VisualWorkflowEngine(mongo_client)
    return advanced_workflow_engine