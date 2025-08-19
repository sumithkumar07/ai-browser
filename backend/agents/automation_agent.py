import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import uuid
from .base_agent import BaseAgent, AgentTask, AgentCapability
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time

class AutomationStep:
    def __init__(self, step_type: str, params: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.type = step_type
        self.params = params
        self.status = "pending"
        self.result = None
        self.error = None
        self.executed_at = None

class AutomationWorkflow:
    def __init__(self, name: str, description: str, steps: List[AutomationStep]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.steps = steps
        self.status = "ready"
        self.created_at = datetime.now()
        self.executed_at = None
        self.completed_at = None
        self.results = {}

class AutomationAgent(BaseAgent):
    """Specialized agent for web automation and task execution"""
    
    def __init__(self):
        super().__init__(
            agent_id="automation_agent",
            name="Automation Agent",
            description="Creates and executes web automation workflows"
        )
        
        # Automation configuration
        self.driver = None
        self.wait_timeout = 10
        self.max_retry_attempts = 3
        
        # Workflow management
        self.active_workflows: Dict[str, AutomationWorkflow] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self.execution_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0
        }
        
        self._initialize_templates()
    
    async def initialize(self) -> bool:
        """Initialize the automation agent"""
        try:
            # Initialize browser driver
            await self._setup_browser_driver()
            
            self.logger.info("Automation agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize automation agent: {e}")
            return False
    
    async def _setup_browser_driver(self):
        """Set up Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.wait_timeout)
            
            self.logger.info("Browser driver initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to setup browser driver: {e}")
            raise
    
    def _initialize_templates(self):
        """Initialize common automation templates"""
        self.workflow_templates = {
            "form_fill": {
                "name": "Form Filling Template",
                "description": "Automate form filling with provided data",
                "steps": [
                    {"type": "navigate", "description": "Navigate to form URL"},
                    {"type": "fill_form", "description": "Fill form fields"},
                    {"type": "submit", "description": "Submit the form"}
                ]
            },
            "data_extraction": {
                "name": "Data Extraction Template",
                "description": "Extract data from web pages",
                "steps": [
                    {"type": "navigate", "description": "Navigate to target page"},
                    {"type": "wait_for_load", "description": "Wait for page to load"},
                    {"type": "extract_data", "description": "Extract specified data"},
                    {"type": "save_data", "description": "Save extracted data"}
                ]
            },
            "social_media_posting": {
                "name": "Social Media Posting Template",
                "description": "Post content to social media platforms",
                "steps": [
                    {"type": "navigate", "description": "Navigate to social platform"},
                    {"type": "login", "description": "Login to account"},
                    {"type": "create_post", "description": "Create new post"},
                    {"type": "add_content", "description": "Add text/media content"},
                    {"type": "publish", "description": "Publish the post"}
                ]
            },
            "price_monitoring": {
                "name": "Price Monitoring Template",
                "description": "Monitor product prices across websites",
                "steps": [
                    {"type": "navigate", "description": "Navigate to product page"},
                    {"type": "extract_price", "description": "Extract current price"},
                    {"type": "compare_price", "description": "Compare with previous price"},
                    {"type": "send_alert", "description": "Send alert if price changed"}
                ]
            }
        }
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute an automation task"""
        task_type = task.type
        
        if task_type == "create_workflow":
            return await self._create_workflow(task)
        elif task_type == "execute_workflow":
            return await self._execute_workflow(task)
        elif task_type == "create_from_template":
            return await self._create_from_template(task)
        elif task_type == "batch_automation":
            return await self._batch_automation(task)
        elif task_type == "schedule_automation":
            return await self._schedule_automation(task)
        else:
            return {"error": f"Unknown automation task type: {task_type}"}
    
    async def get_capabilities(self) -> List[AgentCapability]:
        """Return automation agent capabilities"""
        return [
            AgentCapability(
                name="Workflow Creation",
                description="Create custom automation workflows",
                input_types=["create_workflow"],
                output_types=["workflow_definition"],
                estimated_time=3.0,
                success_rate=0.95
            ),
            AgentCapability(
                name="Workflow Execution",
                description="Execute automation workflows on web pages",
                input_types=["execute_workflow"],
                output_types=["execution_result"],
                estimated_time=10.0,
                success_rate=0.85
            ),
            AgentCapability(
                name="Template-Based Creation",
                description="Create workflows from predefined templates",
                input_types=["create_from_template"],
                output_types=["workflow_definition"],
                estimated_time=2.0,
                success_rate=0.98
            ),
            AgentCapability(
                name="Batch Automation",
                description="Execute multiple automation tasks in sequence",
                input_types=["batch_automation"],
                output_types=["batch_result"],
                estimated_time=30.0,
                success_rate=0.80
            ),
            AgentCapability(
                name="Scheduled Automation",
                description="Schedule automation workflows for future execution",
                input_types=["schedule_automation"],
                output_types=["schedule_result"],
                estimated_time=1.0,
                success_rate=0.95
            )
        ]
    
    async def _create_workflow(self, task: AgentTask) -> Dict[str, Any]:
        """Create a new automation workflow"""
        try:
            workflow_config = task.payload
            
            name = workflow_config.get("name", "Untitled Workflow")
            description = workflow_config.get("description", "")
            step_definitions = workflow_config.get("steps", [])
            
            # Create automation steps
            steps = []
            for step_def in step_definitions:
                step = AutomationStep(
                    step_type=step_def["type"],
                    params=step_def.get("params", {})
                )
                steps.append(step)
            
            # Create workflow
            workflow = AutomationWorkflow(
                name=name,
                description=description,
                steps=steps
            )
            
            self.active_workflows[workflow.id] = workflow
            
            return {
                "workflow_id": workflow.id,
                "name": workflow.name,
                "steps": len(workflow.steps),
                "status": "created",
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Workflow creation failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _create_from_template(self, task: AgentTask) -> Dict[str, Any]:
        """Create workflow from template"""
        try:
            template_name = task.payload.get("template")
            customization = task.payload.get("customization", {})
            
            if template_name not in self.workflow_templates:
                return {"error": f"Template '{template_name}' not found", "success": False}
            
            template = self.workflow_templates[template_name]
            
            # Create workflow from template
            workflow_config = {
                "name": customization.get("name", template["name"]),
                "description": customization.get("description", template["description"]),
                "steps": []
            }
            
            # Convert template steps to automation steps
            for step_template in template["steps"]:
                step_config = {
                    "type": step_template["type"],
                    "params": customization.get(step_template["type"], {})
                }
                workflow_config["steps"].append(step_config)
            
            # Create the workflow
            create_task = AgentTask(
                id=str(uuid.uuid4()),
                type="create_workflow",
                description="Create workflow from template",
                priority=task.priority,
                payload=workflow_config,
                created_at=datetime.now()
            )
            
            return await self._create_workflow(create_task)
            
        except Exception as e:
            self.logger.error(f"Template workflow creation failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _execute_workflow(self, task: AgentTask) -> Dict[str, Any]:
        """Execute an automation workflow"""
        try:
            workflow_id = task.payload.get("workflow_id")
            execution_context = task.payload.get("context", {})
            
            if workflow_id not in self.active_workflows:
                return {"error": f"Workflow '{workflow_id}' not found", "success": False}
            
            workflow = self.active_workflows[workflow_id]
            workflow.status = "running"
            workflow.executed_at = datetime.now()
            
            execution_results = []
            
            # Execute each step
            for step in workflow.steps:
                try:
                    step.status = "running"
                    
                    # Execute step based on type
                    step_result = await self._execute_step(step, execution_context)
                    
                    step.result = step_result
                    step.status = "completed"
                    step.executed_at = datetime.now()
                    
                    execution_results.append({
                        "step_id": step.id,
                        "type": step.type,
                        "status": "completed",
                        "result": step_result
                    })
                    
                    # Update context with step results
                    execution_context[f"step_{step.id}_result"] = step_result
                    
                except Exception as e:
                    step.status = "failed"
                    step.error = str(e)
                    
                    execution_results.append({
                        "step_id": step.id,
                        "type": step.type,
                        "status": "failed",
                        "error": str(e)
                    })
                    
                    # Stop execution on failure (can be configurable)
                    break
            
            # Finalize workflow
            workflow.status = "completed" if all(step.status == "completed" for step in workflow.steps) else "failed"
            workflow.completed_at = datetime.now()
            workflow.results = execution_results
            
            # Update stats
            self.execution_stats["total_workflows"] += 1
            if workflow.status == "completed":
                self.execution_stats["successful_workflows"] += 1
            else:
                self.execution_stats["failed_workflows"] += 1
            
            execution_time = (workflow.completed_at - workflow.executed_at).total_seconds()
            
            return {
                "workflow_id": workflow.id,
                "status": workflow.status,
                "execution_time": execution_time,
                "steps_completed": len([s for s in workflow.steps if s.status == "completed"]),
                "total_steps": len(workflow.steps),
                "results": execution_results,
                "success": workflow.status == "completed"
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _execute_step(self, step: AutomationStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single automation step"""
        step_type = step.type
        params = step.params
        
        if step_type == "navigate":
            return await self._step_navigate(params, context)
        elif step_type == "click":
            return await self._step_click(params, context)
        elif step_type == "type":
            return await self._step_type(params, context)
        elif step_type == "wait":
            return await self._step_wait(params, context)
        elif step_type == "extract_text":
            return await self._step_extract_text(params, context)
        elif step_type == "extract_attribute":
            return await self._step_extract_attribute(params, context)
        elif step_type == "fill_form":
            return await self._step_fill_form(params, context)
        elif step_type == "submit":
            return await self._step_submit(params, context)
        elif step_type == "scroll":
            return await self._step_scroll(params, context)
        elif step_type == "screenshot":
            return await self._step_screenshot(params, context)
        else:
            raise Exception(f"Unknown step type: {step_type}")
    
    async def _step_navigate(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to URL"""
        url = params.get("url")
        if not url:
            raise Exception("No URL provided for navigation")
        
        self.driver.get(url)
        await asyncio.sleep(2)  # Wait for page to load
        
        return {
            "action": "navigate",
            "url": url,
            "current_url": self.driver.current_url,
            "title": self.driver.title
        }
    
    async def _step_click(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Click on element"""
        selector = params.get("selector")
        if not selector:
            raise Exception("No selector provided for click")
        
        element = WebDriverWait(self.driver, self.wait_timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        
        element.click()
        await asyncio.sleep(1)
        
        return {
            "action": "click",
            "selector": selector,
            "element_text": element.text
        }
    
    async def _step_type(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into element"""
        selector = params.get("selector")
        text = params.get("text", "")
        
        if not selector:
            raise Exception("No selector provided for typing")
        
        element = WebDriverWait(self.driver, self.wait_timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        
        element.clear()
        element.send_keys(text)
        
        return {
            "action": "type",
            "selector": selector,
            "text": text
        }
    
    async def _step_wait(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for condition or time"""
        wait_type = params.get("type", "time")
        
        if wait_type == "time":
            duration = params.get("duration", 1)
            await asyncio.sleep(duration)
            return {"action": "wait", "type": "time", "duration": duration}
        
        elif wait_type == "element":
            selector = params.get("selector")
            timeout = params.get("timeout", self.wait_timeout)
            
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            return {"action": "wait", "type": "element", "selector": selector, "found": True}
        
        else:
            raise Exception(f"Unknown wait type: {wait_type}")
    
    async def _step_extract_text(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from element"""
        selector = params.get("selector")
        if not selector:
            raise Exception("No selector provided for text extraction")
        
        element = WebDriverWait(self.driver, self.wait_timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        
        text = element.text
        
        return {
            "action": "extract_text",
            "selector": selector,
            "text": text
        }
    
    async def _step_fill_form(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fill form with provided data"""
        form_data = params.get("data", {})
        
        filled_fields = []
        
        for field_name, value in form_data.items():
            try:
                # Try different selector strategies
                selectors = [
                    f"input[name='{field_name}']",
                    f"input[id='{field_name}']",
                    f"textarea[name='{field_name}']",
                    f"select[name='{field_name}']"
                ]
                
                element_found = False
                for selector in selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if element.tag_name == "select":
                            # Handle select elements
                            from selenium.webdriver.support.ui import Select
                            select = Select(element)
                            select.select_by_visible_text(str(value))
                        else:
                            # Handle input/textarea elements
                            element.clear()
                            element.send_keys(str(value))
                        
                        filled_fields.append({
                            "field": field_name,
                            "selector": selector,
                            "value": str(value)
                        })
                        element_found = True
                        break
                        
                    except Exception:
                        continue
                
                if not element_found:
                    self.logger.warning(f"Could not find form field: {field_name}")
                    
            except Exception as e:
                self.logger.error(f"Error filling field {field_name}: {e}")
        
        return {
            "action": "fill_form",
            "filled_fields": filled_fields,
            "total_fields": len(form_data)
        }
    
    async def _step_screenshot(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot"""
        filename = params.get("filename", f"screenshot_{int(time.time())}.png")
        
        screenshot_path = f"/tmp/{filename}"
        self.driver.save_screenshot(screenshot_path)
        
        return {
            "action": "screenshot",
            "filename": filename,
            "path": screenshot_path
        }
    
    async def shutdown(self):
        """Shutdown the automation agent"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        await super().shutdown()
        self.logger.info("Automation agent shut down")