"""
Cross-Page Workflow Engine for AETHER
Advanced multi-site automation and workflow orchestration
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging

class WorkflowStepType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    EXTRACT = "extract"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    CONDITION = "condition"
    LOOP = "loop"
    API_CALL = "api_call"
    DATA_TRANSFORM = "data_transform"

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    id: str
    type: WorkflowStepType
    params: Dict[str, Any]
    conditions: Optional[List[Dict]] = None
    retry_count: int = 3
    timeout: int = 30000
    delay_after: int = 1000
    
@dataclass
class WorkflowContext:
    variables: Dict[str, Any]
    session_data: Dict[str, Any]
    cookies: List[Dict] = None
    localStorage: Dict[str, Any] = None
    
@dataclass
class CrossPageWorkflow:
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    context: WorkflowContext
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class CrossPageWorkflowEngine:
    def __init__(self):
        self.active_workflows: Dict[str, CrossPageWorkflow] = {}
        self.browser: Optional[Browser] = None
        self.browser_context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def initialize(self):
        """Initialize the browser engine"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,
                args=[
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            self.browser_context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            print("✅ Cross-Page Workflow Engine initialized")
            return {"success": True, "message": "Engine ready"}
        except Exception as e:
            print(f"❌ Engine initialization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new cross-page workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Parse workflow steps
            steps = []
            for step_config in workflow_config.get("steps", []):
                step = WorkflowStep(
                    id=str(uuid.uuid4()),
                    type=WorkflowStepType(step_config["type"]),
                    params=step_config.get("params", {}),
                    conditions=step_config.get("conditions"),
                    retry_count=step_config.get("retry_count", 3),
                    timeout=step_config.get("timeout", 30000),
                    delay_after=step_config.get("delay_after", 1000)
                )
                steps.append(step)
            
            # Create workflow context
            context = WorkflowContext(
                variables=workflow_config.get("variables", {}),
                session_data=workflow_config.get("session_data", {}),
                cookies=workflow_config.get("cookies", []),
                localStorage=workflow_config.get("localStorage", {})
            )
            
            # Create workflow
            workflow = CrossPageWorkflow(
                id=workflow_id,
                name=workflow_config["name"],
                description=workflow_config.get("description", ""),
                steps=steps,
                context=context,
                created_at=datetime.now()
            )
            
            self.active_workflows[workflow_id] = workflow
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "workflow": asdict(workflow),
                "message": "Workflow created successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a cross-page workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            
            if not self.browser:
                await self.initialize()
            
            # Create new page for this workflow
            page = await self.browser_context.new_page()
            
            # Set up context (cookies, localStorage, etc.)
            if workflow.context.cookies:
                await self.browser_context.add_cookies(workflow.context.cookies)
            
            execution_results = []
            
            try:
                for step in workflow.steps:
                    step_result = await self._execute_step(page, step, workflow.context)
                    execution_results.append(step_result)
                    
                    if not step_result["success"]:
                        if step.retry_count > 0:
                            # Retry logic
                            for retry in range(step.retry_count):
                                print(f"Retrying step {step.id} (attempt {retry + 1})")
                                await asyncio.sleep(2)
                                step_result = await self._execute_step(page, step, workflow.context)
                                if step_result["success"]:
                                    break
                        
                        if not step_result["success"]:
                            workflow.status = WorkflowStatus.FAILED
                            workflow.error = step_result.get("error", "Step execution failed")
                            break
                    
                    # Add delay after step
                    await asyncio.sleep(step.delay_after / 1000)
                
                if workflow.status != WorkflowStatus.FAILED:
                    workflow.status = WorkflowStatus.COMPLETED
                    workflow.completed_at = datetime.now()
                
            finally:
                await page.close()
            
            return {
                "success": workflow.status == WorkflowStatus.COMPLETED,
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "execution_results": execution_results,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "error": workflow.error
            }
            
        except Exception as e:
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id].status = WorkflowStatus.FAILED
                self.active_workflows[workflow_id].error = str(e)
            return {"success": False, "error": str(e)}
    
    async def _execute_step(self, page: Page, step: WorkflowStep, context: WorkflowContext) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            print(f"Executing step: {step.type.value} - {step.params}")
            
            # Check conditions if any
            if step.conditions:
                condition_met = await self._check_conditions(page, step.conditions, context)
                if not condition_met:
                    return {"success": True, "skipped": True, "reason": "Condition not met"}
            
            # Execute step based on type
            if step.type == WorkflowStepType.NAVIGATE:
                url = self._resolve_variables(step.params["url"], context.variables)
                await page.goto(url, timeout=step.timeout, wait_until='networkidle')
                return {"success": True, "action": "navigate", "url": url}
            
            elif step.type == WorkflowStepType.CLICK:
                selector = step.params["selector"]
                await page.click(selector, timeout=step.timeout)
                return {"success": True, "action": "click", "selector": selector}
            
            elif step.type == WorkflowStepType.TYPE:
                selector = step.params["selector"]
                text = self._resolve_variables(step.params["text"], context.variables)
                await page.fill(selector, text)
                return {"success": True, "action": "type", "selector": selector, "text": text}
            
            elif step.type == WorkflowStepType.WAIT:
                if "selector" in step.params:
                    await page.wait_for_selector(step.params["selector"], timeout=step.timeout)
                    return {"success": True, "action": "wait", "selector": step.params["selector"]}
                elif "timeout" in step.params:
                    await asyncio.sleep(step.params["timeout"] / 1000)
                    return {"success": True, "action": "wait", "duration": step.params["timeout"]}
            
            elif step.type == WorkflowStepType.EXTRACT:
                selector = step.params["selector"]
                attribute = step.params.get("attribute", "textContent")
                variable_name = step.params["variable"]
                
                if attribute == "textContent":
                    value = await page.text_content(selector)
                elif attribute == "value":
                    value = await page.input_value(selector)
                else:
                    value = await page.get_attribute(selector, attribute)
                
                # Store in context variables
                context.variables[variable_name] = value
                
                return {
                    "success": True, 
                    "action": "extract", 
                    "selector": selector, 
                    "variable": variable_name, 
                    "value": value
                }
            
            elif step.type == WorkflowStepType.SCROLL:
                if "selector" in step.params:
                    await page.locator(step.params["selector"]).scroll_into_view_if_needed()
                else:
                    await page.evaluate(f"window.scrollBy(0, {step.params.get('pixels', 500)})")
                return {"success": True, "action": "scroll"}
            
            elif step.type == WorkflowStepType.SCREENSHOT:
                filename = step.params.get("filename", f"screenshot_{datetime.now().timestamp()}.png")
                await page.screenshot(path=filename)
                return {"success": True, "action": "screenshot", "filename": filename}
            
            elif step.type == WorkflowStepType.CONDITION:
                result = await self._evaluate_condition(page, step.params, context)
                return {"success": True, "action": "condition", "result": result}
            
            elif step.type == WorkflowStepType.LOOP:
                loop_results = await self._execute_loop(page, step.params, context)
                return {"success": True, "action": "loop", "results": loop_results}
            
            elif step.type == WorkflowStepType.API_CALL:
                api_result = await self._make_api_call(step.params, context)
                return {"success": True, "action": "api_call", "result": api_result}
            
            elif step.type == WorkflowStepType.DATA_TRANSFORM:
                transform_result = self._transform_data(step.params, context)
                return {"success": True, "action": "data_transform", "result": transform_result}
            
            else:
                return {"success": False, "error": f"Unknown step type: {step.type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _check_conditions(self, page: Page, conditions: List[Dict], context: WorkflowContext) -> bool:
        """Check if all conditions are met"""
        for condition in conditions:
            if not await self._evaluate_condition(page, condition, context):
                return False
        return True
    
    async def _evaluate_condition(self, page: Page, condition: Dict, context: WorkflowContext) -> bool:
        """Evaluate a single condition"""
        try:
            condition_type = condition["type"]
            
            if condition_type == "element_exists":
                selector = condition["selector"]
                element = await page.query_selector(selector)
                return element is not None
            
            elif condition_type == "element_visible":
                selector = condition["selector"]
                return await page.is_visible(selector)
            
            elif condition_type == "text_contains":
                selector = condition["selector"]
                expected_text = condition["text"]
                actual_text = await page.text_content(selector)
                return expected_text in (actual_text or "")
            
            elif condition_type == "variable_equals":
                variable_name = condition["variable"]
                expected_value = condition["value"]
                actual_value = context.variables.get(variable_name)
                return actual_value == expected_value
            
            elif condition_type == "url_contains":
                expected_url_part = condition["url"]
                current_url = page.url
                return expected_url_part in current_url
            
            return False
        except Exception as e:
            print(f"Condition evaluation error: {e}")
            return False
    
    async def _execute_loop(self, page: Page, loop_config: Dict, context: WorkflowContext) -> List[Dict]:
        """Execute a loop with multiple iterations"""
        results = []
        
        loop_type = loop_config["type"]
        max_iterations = loop_config.get("max_iterations", 10)
        
        if loop_type == "element_list":
            selector = loop_config["selector"]
            elements = await page.query_selector_all(selector)
            
            for i, element in enumerate(elements[:max_iterations]):
                # Execute loop body for each element
                iteration_context = WorkflowContext(
                    variables={**context.variables, "loop_index": i, "loop_element": element},
                    session_data=context.session_data
                )
                
                # Execute loop steps (if provided)
                if "steps" in loop_config:
                    for step_config in loop_config["steps"]:
                        step = WorkflowStep(
                            id=str(uuid.uuid4()),
                            type=WorkflowStepType(step_config["type"]),
                            params=step_config["params"]
                        )
                        step_result = await self._execute_step(page, step, iteration_context)
                        results.append(step_result)
        
        elif loop_type == "count":
            count = loop_config["count"]
            for i in range(min(count, max_iterations)):
                iteration_context = WorkflowContext(
                    variables={**context.variables, "loop_index": i},
                    session_data=context.session_data
                )
                
                if "steps" in loop_config:
                    for step_config in loop_config["steps"]:
                        step = WorkflowStep(
                            id=str(uuid.uuid4()),
                            type=WorkflowStepType(step_config["type"]),
                            params=step_config["params"]
                        )
                        step_result = await self._execute_step(page, step, iteration_context)
                        results.append(step_result)
        
        return results
    
    async def _make_api_call(self, api_config: Dict, context: WorkflowContext) -> Dict[str, Any]:
        """Make an external API call during workflow"""
        try:
            url = self._resolve_variables(api_config["url"], context.variables)
            method = api_config.get("method", "GET")
            headers = api_config.get("headers", {})
            data = api_config.get("data")
            
            if data:
                data = self._resolve_variables(data, context.variables)
            
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=headers, json=data) as response:
                    result_data = await response.json()
                    
                    # Store result in context if variable name provided
                    if "result_variable" in api_config:
                        context.variables[api_config["result_variable"]] = result_data
                    
                    return {
                        "status": response.status,
                        "data": result_data,
                        "success": response.status < 400
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _transform_data(self, transform_config: Dict, context: WorkflowContext) -> Any:
        """Transform data using specified operations"""
        try:
            operation = transform_config["operation"]
            source_variable = transform_config["source"]
            source_data = context.variables.get(source_variable)
            
            if operation == "json_parse":
                result = json.loads(source_data) if isinstance(source_data, str) else source_data
            
            elif operation == "extract_field":
                field_path = transform_config["field"]
                result = self._get_nested_value(source_data, field_path)
            
            elif operation == "list_map":
                map_expression = transform_config["expression"]
                result = [eval(map_expression.replace("$item", repr(item))) for item in source_data]
            
            elif operation == "filter":
                filter_expression = transform_config["filter"]
                result = [item for item in source_data if eval(filter_expression.replace("$item", repr(item)))]
            
            elif operation == "string_format":
                template = transform_config["template"]
                result = template.format(**context.variables)
            
            else:
                result = source_data
            
            # Store result if target variable specified
            if "target_variable" in transform_config:
                context.variables[transform_config["target_variable"]] = result
            
            return result
        except Exception as e:
            print(f"Data transformation error: {e}")
            return None
    
    def _resolve_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Resolve variables in text using {{variable}} syntax"""
        if not isinstance(text, str):
            return text
        
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(var_value))
        
        return text
    
    def _get_nested_value(self, data: Any, path: str) -> Any:
        """Get nested value from data using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                current = current[index] if index < len(current) else None
            else:
                return None
        
        return current
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a specific workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            return {
                "success": True,
                "workflow": asdict(workflow)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel a running workflow"""
        try:
            if workflow_id not in self.active_workflows:
                return {"success": False, "error": "Workflow not found"}
            
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": WorkflowStatus.CANCELLED.value
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_workflows(self) -> Dict[str, Any]:
        """List all active workflows"""
        try:
            workflows = []
            for workflow_id, workflow in self.active_workflows.items():
                workflows.append({
                    "id": workflow.id,
                    "name": workflow.name,
                    "status": workflow.status.value,
                    "created_at": workflow.created_at.isoformat(),
                    "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
                })
            
            return {
                "success": True,
                "workflows": workflows,
                "count": len(workflows)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.browser_context:
                await self.browser_context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("✅ Cross-Page Workflow Engine cleaned up")
        except Exception as e:
            print(f"❌ Cleanup error: {e}")

# Example workflow configurations
EXAMPLE_WORKFLOWS = {
    "social_media_posting": {
        "name": "Cross-Platform Social Media Posting",
        "description": "Post content across Twitter, LinkedIn, and Facebook",
        "variables": {
            "post_content": "Check out our new AI tool! #AI #Technology",
            "image_path": "/path/to/image.jpg"
        },
        "steps": [
            {
                "type": "navigate",
                "params": {"url": "https://twitter.com/compose/tweet"}
            },
            {
                "type": "wait",
                "params": {"selector": "[data-testid='tweetTextarea_0']"}
            },
            {
                "type": "type",
                "params": {
                    "selector": "[data-testid='tweetTextarea_0']",
                    "text": "{{post_content}}"
                }
            },
            {
                "type": "click",
                "params": {"selector": "[data-testid='tweetButtonInline']"}
            }
        ]
    },
    
    "ecommerce_price_monitoring": {
        "name": "E-commerce Price Monitoring",
        "description": "Monitor prices across multiple e-commerce sites",
        "variables": {
            "product_urls": ["https://amazon.com/product1", "https://ebay.com/product1"],
            "price_threshold": 100
        },
        "steps": [
            {
                "type": "loop",
                "params": {
                    "type": "list",
                    "list_variable": "product_urls",
                    "steps": [
                        {
                            "type": "navigate",
                            "params": {"url": "{{loop_item}}"}
                        },
                        {
                            "type": "extract",
                            "params": {
                                "selector": ".price",
                                "variable": "current_price",
                                "attribute": "textContent"
                            }
                        },
                        {
                            "type": "condition",
                            "params": {
                                "type": "variable_less_than",
                                "variable": "current_price",
                                "value": "{{price_threshold}}"
                            }
                        }
                    ]
                }
            }
        ]
    }
}