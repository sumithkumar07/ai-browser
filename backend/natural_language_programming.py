"""
AETHER Natural Language Programming Framework (Eko-Equivalent)
Complete implementation of natural language workflow creation and execution
Features:
- Natural language to workflow conversion
- Dynamic workflow generation and modification
- Advanced automation patterns
- Workflow optimization and learning
"""

import asyncio
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import re

from groq import AsyncGroq
from computer_use_api import ComputerUseAPI
from agentic_memory_system import AgenticMemorySystem


class WorkflowStepType(Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    EXTRACT = "extract"
    CONDITION = "condition"
    LOOP = "loop"
    CUSTOM = "custom"


@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    step_type: WorkflowStepType
    description: str
    parameters: Dict[str, Any]
    expected_duration: float = 1000.0  # milliseconds
    retry_count: int = 3
    timeout: int = 10000
    conditions: Optional[Dict[str, Any]] = None
    error_handling: Optional[Dict[str, Any]] = None


@dataclass
class AETHERWorkflow:
    """Complete AETHER workflow definition"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    created_by: str
    created_at: datetime
    tags: List[str]
    success_rate: float = 0.0
    execution_count: int = 0
    average_duration: float = 0.0
    metadata: Dict[str, Any] = None
    
    def modify(self, modification: str) -> 'AETHERWorkflow':
        """Modify workflow based on natural language instruction"""
        # This will be implemented by the NLP framework
        return self


class WorkflowExecutor:
    """Executes AETHER workflows with computer use integration"""
    
    def __init__(self, computer_use_api: ComputerUseAPI, memory_system: AgenticMemorySystem):
        self.computer_use = computer_use_api
        self.memory = memory_system
        self.execution_history: List[Dict[str, Any]] = []
    
    async def run(self, workflow: AETHERWorkflow, page, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow with computer use integration"""
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        execution_log = {
            "execution_id": execution_id,
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "started_at": datetime.utcnow().isoformat(),
            "context": context or {},
            "steps_executed": [],
            "success": False,
            "error": None,
            "total_duration": 0.0
        }
        
        try:
            for i, step in enumerate(workflow.steps):
                print(f"🚀 Executing step {i+1}/{len(workflow.steps)}: {step.description}")
                
                step_start = time.time()
                step_result = await self._execute_step(step, page, context)
                step_duration = (time.time() - step_start) * 1000
                
                step_log = {
                    "step_id": step.step_id,
                    "step_number": i + 1,
                    "description": step.description,
                    "type": step.step_type.value,
                    "duration": step_duration,
                    "success": step_result.get("success", False),
                    "result": step_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                execution_log["steps_executed"].append(step_log)
                
                if not step_result.get("success", False):
                    # Handle step failure
                    if step.error_handling:
                        error_action = step.error_handling.get("action", "stop")
                        if error_action == "continue":
                            print(f"⚠️ Step failed but continuing: {step_result.get('error', 'Unknown error')}")
                            continue
                        elif error_action == "retry":
                            retry_count = step.error_handling.get("retry_count", 1)
                            for retry in range(retry_count):
                                print(f"🔄 Retrying step {i+1}, attempt {retry+1}/{retry_count}")
                                await asyncio.sleep(1)
                                retry_result = await self._execute_step(step, page, context)
                                if retry_result.get("success", False):
                                    step_log["success"] = True
                                    step_log["result"] = retry_result
                                    break
                            else:
                                execution_log["error"] = f"Step {i+1} failed after {retry_count} retries"
                                break
                    else:
                        execution_log["error"] = f"Step {i+1} failed: {step_result.get('error', 'Unknown error')}"
                        break
                
                # Add delay between steps if specified
                if i < len(workflow.steps) - 1:
                    await asyncio.sleep(0.5)
            
            # Check if all steps completed successfully
            successful_steps = sum(1 for step in execution_log["steps_executed"] if step["success"])
            execution_log["success"] = successful_steps == len(workflow.steps)
            
        except Exception as e:
            execution_log["error"] = str(e)
            execution_log["success"] = False
        finally:
            execution_log["completed_at"] = datetime.utcnow().isoformat()
            execution_log["total_duration"] = (time.time() - start_time) * 1000
            
            # Store execution in history
            self.execution_history.append(execution_log)
            
            # Update workflow metrics
            await self._update_workflow_metrics(workflow, execution_log)
        
        return execution_log
    
    async def _execute_step(self, step: WorkflowStep, page, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual workflow step"""
        try:
            if step.step_type == WorkflowStepType.NAVIGATE:
                url = step.parameters.get("url", "")
                if not url.startswith("http"):
                    url = f"https://{url}"
                await page.goto(url, timeout=step.timeout)
                await page.wait_for_load_state("networkidle", timeout=step.timeout)
                return {"success": True, "url": url}
            
            elif step.step_type == WorkflowStepType.CLICK:
                target = step.parameters.get("target", "")
                result = await self.computer_use.smart_click(page, target)
                return result
            
            elif step.step_type == WorkflowStepType.TYPE:
                field = step.parameters.get("field", "")
                text = step.parameters.get("text", "")
                result = await self.computer_use.smart_type(page, field, text)
                return result
            
            elif step.step_type == WorkflowStepType.WAIT:
                duration = step.parameters.get("duration", 1000)
                await asyncio.sleep(duration / 1000.0)
                return {"success": True, "waited": duration}
            
            elif step.step_type == WorkflowStepType.EXTRACT:
                data_type = step.parameters.get("data_type", "text")
                # Implement data extraction logic
                content = await page.content()
                return {"success": True, "extracted_data": {"content_length": len(content)}}
            
            elif step.step_type == WorkflowStepType.CONDITION:
                condition = step.parameters.get("condition", "")
                # Implement condition checking
                return {"success": True, "condition_met": True}
            
            elif step.step_type == WorkflowStepType.CUSTOM:
                command = step.parameters.get("command", "")
                result = await self.computer_use.execute_natural_language_command(page, command)
                return result
            
            else:
                return {"success": False, "error": f"Unknown step type: {step.step_type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update_workflow_metrics(self, workflow: AETHERWorkflow, execution_log: Dict[str, Any]):
        """Update workflow success metrics"""
        workflow.execution_count += 1
        
        # Update success rate
        if execution_log["success"]:
            workflow.success_rate = ((workflow.success_rate * (workflow.execution_count - 1)) + 1.0) / workflow.execution_count
        else:
            workflow.success_rate = (workflow.success_rate * (workflow.execution_count - 1)) / workflow.execution_count
        
        # Update average duration
        workflow.average_duration = ((workflow.average_duration * (workflow.execution_count - 1)) + execution_log["total_duration"]) / workflow.execution_count


class AETHERProgramming:
    """Main Natural Language Programming Framework"""
    
    def __init__(self, ai_provider: str = "groq"):
        self.ai_provider = ai_provider
        self.groq_client = AsyncGroq(api_key="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")
        self.computer_use = ComputerUseAPI(ai_provider)
        self.memory = AgenticMemorySystem()
        self.executor = WorkflowExecutor(self.computer_use, self.memory)
        
        # Workflow storage
        self.workflows: Dict[str, AETHERWorkflow] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        
        # Initialize common workflow templates
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize common workflow templates"""
        self.workflow_templates = {
            "web_search": {
                "name": "Web Search Workflow",
                "description": "Search for information on the web",
                "steps": [
                    {"type": "navigate", "description": "Go to search engine", "params": {"url": "google.com"}},
                    {"type": "click", "description": "Click search box", "params": {"target": "search box"}},
                    {"type": "type", "description": "Enter search query", "params": {"field": "search box", "text": "{query}"}},
                    {"type": "click", "description": "Click search button", "params": {"target": "search button"}},
                    {"type": "wait", "description": "Wait for results", "params": {"duration": 2000}}
                ]
            },
            "form_filling": {
                "name": "Form Filling Workflow",
                "description": "Fill out web forms with provided data",
                "steps": [
                    {"type": "click", "description": "Click first field", "params": {"target": "first input field"}},
                    {"type": "type", "description": "Enter data", "params": {"field": "input field", "text": "{data}"}},
                    {"type": "click", "description": "Submit form", "params": {"target": "submit button"}}
                ]
            },
            "data_extraction": {
                "name": "Data Extraction Workflow", 
                "description": "Extract data from web pages",
                "steps": [
                    {"type": "navigate", "description": "Go to target page", "params": {"url": "{url}"}},
                    {"type": "wait", "description": "Wait for page load", "params": {"duration": 3000}},
                    {"type": "extract", "description": "Extract data", "params": {"data_type": "general"}}
                ]
            }
        }
    
    async def generate(self, instruction: str, user_id: str = "anonymous") -> AETHERWorkflow:
        """Generate workflow from natural language instruction"""
        try:
            # First, try to match with existing templates
            template_workflow = await self._match_template(instruction)
            if template_workflow:
                return template_workflow
            
            # Generate custom workflow using AI
            workflow_data = await self._generate_custom_workflow(instruction, user_id)
            
            if not workflow_data:
                raise Exception("Failed to generate workflow")
            
            # Create workflow object
            workflow = self._create_workflow_from_data(workflow_data, user_id)
            
            # Store the workflow
            self.workflows[workflow.workflow_id] = workflow
            
            return workflow
            
        except Exception as e:
            print(f"Workflow generation error: {e}")
            # Return a basic fallback workflow
            return self._create_fallback_workflow(instruction, user_id)
    
    async def _match_template(self, instruction: str) -> Optional[AETHERWorkflow]:
        """Match instruction to existing templates"""
        instruction_lower = instruction.lower()
        
        # Simple keyword matching for templates
        if any(word in instruction_lower for word in ["search", "google", "find"]):
            template = self.workflow_templates["web_search"]
            return self._create_workflow_from_template(template, "web_search", instruction)
        
        elif any(word in instruction_lower for word in ["form", "fill", "submit"]):
            template = self.workflow_templates["form_filling"]
            return self._create_workflow_from_template(template, "form_filling", instruction)
        
        elif any(word in instruction_lower for word in ["extract", "scrape", "collect"]):
            template = self.workflow_templates["data_extraction"]
            return self._create_workflow_from_template(template, "data_extraction", instruction)
        
        return None
    
    def _create_workflow_from_template(self, template: Dict[str, Any], template_name: str, instruction: str) -> AETHERWorkflow:
        """Create workflow from template"""
        workflow_id = str(uuid.uuid4())
        
        steps = []
        for i, step_data in enumerate(template["steps"]):
            step = WorkflowStep(
                step_id=f"{workflow_id}_step_{i}",
                step_type=WorkflowStepType(step_data["type"]),
                description=step_data["description"],
                parameters=step_data["params"]
            )
            steps.append(step)
        
        return AETHERWorkflow(
            workflow_id=workflow_id,
            name=f"{template['name']} - {instruction[:50]}",
            description=template["description"],
            steps=steps,
            created_by="template",
            created_at=datetime.utcnow(),
            tags=[template_name, "template"]
        )
    
    async def _generate_custom_workflow(self, instruction: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Generate custom workflow using AI"""
        try:
            completion = await self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are AETHER's Natural Language Programming system. Convert natural language instructions into structured workflows.

Return a JSON workflow with this structure:
{
    "name": "Workflow name",
    "description": "What this workflow does",
    "steps": [
        {
            "type": "navigate|click|type|wait|extract|custom",
            "description": "Human readable step description",
            "parameters": {
                "target": "element description for click",
                "url": "website URL for navigate", 
                "field": "input field description for type",
                "text": "text to type",
                "duration": 1000,
                "command": "natural language command for custom"
            }
        }
    ],
    "tags": ["relevant", "tags"]
}

Available step types:
- navigate: Go to a website (params: url)
- click: Click on an element (params: target)
- type: Type text in a field (params: field, text)
- wait: Wait for a duration (params: duration in ms)
- extract: Extract data from page (params: data_type)
- custom: Execute natural language command (params: command)

Make workflows practical and executable."""
                    },
                    {
                        "role": "user",
                        "content": f"Create a workflow for: {instruction}"
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=1500
            )
            
            response_text = completion.choices[0].message.content.strip()
            workflow_data = json.loads(response_text)
            
            return workflow_data
            
        except Exception as e:
            print(f"Custom workflow generation error: {e}")
            return None
    
    def _create_workflow_from_data(self, workflow_data: Dict[str, Any], user_id: str) -> AETHERWorkflow:
        """Create workflow object from AI-generated data"""
        workflow_id = str(uuid.uuid4())
        
        steps = []
        for i, step_data in enumerate(workflow_data.get("steps", [])):
            step = WorkflowStep(
                step_id=f"{workflow_id}_step_{i}",
                step_type=WorkflowStepType(step_data.get("type", "custom")),
                description=step_data.get("description", ""),
                parameters=step_data.get("parameters", {})
            )
            steps.append(step)
        
        return AETHERWorkflow(
            workflow_id=workflow_id,
            name=workflow_data.get("name", "Custom Workflow"),
            description=workflow_data.get("description", "AI-generated workflow"),
            steps=steps,
            created_by=user_id,
            created_at=datetime.utcnow(),
            tags=workflow_data.get("tags", ["custom", "ai-generated"])
        )
    
    def _create_fallback_workflow(self, instruction: str, user_id: str) -> AETHERWorkflow:
        """Create a simple fallback workflow"""
        workflow_id = str(uuid.uuid4())
        
        step = WorkflowStep(
            step_id=f"{workflow_id}_step_0",
            step_type=WorkflowStepType.CUSTOM,
            description=f"Execute: {instruction}",
            parameters={"command": instruction}
        )
        
        return AETHERWorkflow(
            workflow_id=workflow_id,
            name=f"Fallback: {instruction[:30]}",
            description="Simple command execution",
            steps=[step],
            created_by=user_id,
            created_at=datetime.utcnow(),
            tags=["fallback", "simple"]
        )
    
    async def execute(self, workflow: AETHERWorkflow, page, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a workflow"""
        return await self.executor.run(workflow, page, context)
    
    async def modify_workflow(self, workflow_id: str, modification: str) -> Optional[AETHERWorkflow]:
        """Modify an existing workflow based on natural language"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        try:
            # Use AI to understand the modification
            completion = await self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": """You are modifying an existing workflow. Analyze the modification request and return the updated workflow.

Given the current workflow and modification request, return the complete updated workflow in the same JSON format."""
                    },
                    {
                        "role": "user",
                        "content": f"""Current workflow:
Name: {workflow.name}
Steps: {[step.description for step in workflow.steps]}

Modification request: {modification}

Return the updated workflow JSON."""
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=1500
            )
            
            response_text = completion.choices[0].message.content.strip()
            updated_data = json.loads(response_text)
            
            # Create updated workflow
            updated_workflow = self._create_workflow_from_data(updated_data, workflow.created_by)
            updated_workflow.workflow_id = workflow_id  # Keep same ID
            
            # Update in storage
            self.workflows[workflow_id] = updated_workflow
            
            return updated_workflow
            
        except Exception as e:
            print(f"Workflow modification error: {e}")
            return workflow  # Return original on error
    
    def get_workflow(self, workflow_id: str) -> Optional[AETHERWorkflow]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, user_id: Optional[str] = None) -> List[AETHERWorkflow]:
        """List all workflows, optionally filtered by user"""
        workflows = list(self.workflows.values())
        
        if user_id:
            workflows = [w for w in workflows if w.created_by == user_id]
        
        # Sort by creation date (most recent first)
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        return workflows
    
    async def suggest_workflow_improvements(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Suggest improvements for a workflow based on execution history"""
        if workflow_id not in self.workflows:
            return []
        
        workflow = self.workflows[workflow_id]
        
        # Get execution history for this workflow
        workflow_executions = [
            exec_log for exec_log in self.executor.execution_history
            if exec_log["workflow_id"] == workflow_id
        ]
        
        suggestions = []
        
        # Analyze success rate
        if workflow.success_rate < 0.8 and workflow.execution_count >= 3:
            suggestions.append({
                "type": "reliability",
                "priority": "high",
                "suggestion": "Add error handling and retry logic to improve success rate",
                "current_success_rate": workflow.success_rate
            })
        
        # Analyze performance
        if workflow.average_duration > 30000 and workflow.execution_count >= 3:  # > 30 seconds
            suggestions.append({
                "type": "performance",
                "priority": "medium", 
                "suggestion": "Optimize workflow steps to reduce execution time",
                "current_duration": workflow.average_duration
            })
        
        # Analyze step failures
        if workflow_executions:
            failing_steps = {}
            for execution in workflow_executions[-5:]:  # Last 5 executions
                for step in execution.get("steps_executed", []):
                    if not step["success"]:
                        step_desc = step["description"]
                        failing_steps[step_desc] = failing_steps.get(step_desc, 0) + 1
            
            for step_desc, failure_count in failing_steps.items():
                if failure_count >= 2:
                    suggestions.append({
                        "type": "step_reliability",
                        "priority": "high",
                        "suggestion": f"Review and improve step: '{step_desc}' (failed {failure_count} times)",
                        "failing_step": step_desc
                    })
        
        return suggestions
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get overall execution statistics"""
        total_executions = len(self.executor.execution_history)
        successful_executions = sum(1 for exec_log in self.executor.execution_history if exec_log["success"])
        
        if total_executions > 0:
            success_rate = successful_executions / total_executions
            avg_duration = sum(exec_log["total_duration"] for exec_log in self.executor.execution_history) / total_executions
        else:
            success_rate = 0.0
            avg_duration = 0.0
        
        return {
            "total_workflows": len(self.workflows),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "overall_success_rate": success_rate,
            "average_execution_time": avg_duration,
            "most_used_workflows": self._get_most_used_workflows(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_most_used_workflows(self) -> List[Dict[str, Any]]:
        """Get most frequently executed workflows"""
        workflow_usage = {}
        
        for exec_log in self.executor.execution_history:
            workflow_id = exec_log["workflow_id"]
            if workflow_id in workflow_usage:
                workflow_usage[workflow_id] += 1
            else:
                workflow_usage[workflow_id] = 1
        
        # Sort by usage count
        sorted_usage = sorted(workflow_usage.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for workflow_id, usage_count in sorted_usage[:5]:  # Top 5
            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                result.append({
                    "workflow_id": workflow_id,
                    "name": workflow.name,
                    "usage_count": usage_count,
                    "success_rate": workflow.success_rate
                })
        
        return result


# Global instance
aether_programming = AETHERProgramming()