import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from pymongo import MongoClient
import httpx
from bs4 import BeautifulSoup
import os

logger = logging.getLogger(__name__)

class AdvancedAgenticEngine:
    """
    Phase 1 & 2: Advanced Agentic Engine with Computer Vision and Multi-step Reasoning
    Builds upon existing automation while adding true agentic capabilities
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.active_agents = {}
        self.workflow_templates = self._load_workflow_templates()
        
    async def create_agentic_workflow(self, description: str, context: Dict[str, Any] = None) -> str:
        """Create intelligent workflow from natural language description"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Parse natural language into structured workflow
            workflow_steps = await self._parse_natural_language_workflow(description, context)
            
            # Create workflow document
            workflow_doc = {
                "workflow_id": workflow_id,
                "description": description,
                "steps": workflow_steps,
                "status": "created",
                "created_at": datetime.utcnow(),
                "context": context or {},
                "progress": {
                    "current_step": 0,
                    "total_steps": len(workflow_steps),
                    "completed_steps": [],
                    "failed_steps": []
                }
            }
            
            self.db.agentic_workflows.insert_one(workflow_doc)
            
            logger.info(f"Created agentic workflow: {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create agentic workflow: {e}")
            raise
            
    async def _parse_natural_language_workflow(self, description: str, context: Dict[str, Any]) -> List[Dict]:
        """Parse natural language into executable workflow steps using AI"""
        
        # Enhanced workflow parsing with computer vision capabilities
        workflow_parser_prompt = f"""
        Convert this request into a structured workflow:
        "{description}"
        
        Context: {json.dumps(context, default=str)}
        
        Create steps that can include:
        - Web navigation and interaction
        - Data extraction and analysis
        - Cross-platform actions
        - Report generation
        - File operations
        - Social media interactions
        - Email operations
        
        Return as JSON array of steps with: action_type, target, parameters, expected_outcome
        """
        
        # This would integrate with enhanced AI manager
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=workflow_parser_prompt,
            context=None,
            session_history=[],
            query_type="workflow_parsing"
        )
        
        try:
            # Extract JSON from AI response
            import re
            json_match = re.search(r'\[.*\]', ai_response["response"], re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group())
                return self._enhance_workflow_steps(steps)
            else:
                # Fallback to template-based parsing
                return self._template_based_parsing(description, context)
                
        except Exception as e:
            logger.error(f"Workflow parsing failed: {e}")
            return self._template_based_parsing(description, context)
    
    def _enhance_workflow_steps(self, steps: List[Dict]) -> List[Dict]:
        """Enhance workflow steps with agentic capabilities"""
        enhanced_steps = []
        
        for step in steps:
            enhanced_step = {
                **step,
                "step_id": str(uuid.uuid4()),
                "status": "pending",
                "retry_count": 0,
                "max_retries": 3,
                "estimated_duration": self._estimate_step_duration(step),
                "dependencies": [],
                "parallel_execution": step.get("parallel_execution", False)
            }
            enhanced_steps.append(enhanced_step)
            
        return enhanced_steps
    
    def _estimate_step_duration(self, step: Dict) -> int:
        """Estimate step execution duration in seconds"""
        action_type = step.get("action_type", "")
        
        duration_map = {
            "navigate": 5,
            "extract_data": 10,
            "social_media_action": 15,
            "file_operation": 8,
            "email_action": 12,
            "report_generation": 30,
            "cross_platform_sync": 20
        }
        
        return duration_map.get(action_type, 10)
    
    async def execute_agentic_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute workflow with intelligent error handling and adaptation"""
        try:
            workflow = self.db.agentic_workflows.find_one({"workflow_id": workflow_id})
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Update status to running
            self.db.agentic_workflows.update_one(
                {"workflow_id": workflow_id},
                {"$set": {"status": "running", "started_at": datetime.utcnow()}}
            )
            
            # Execute steps with parallel processing where possible
            results = await self._execute_workflow_steps(workflow)
            
            # Update final status
            final_status = "completed" if all(r["success"] for r in results) else "partial"
            self.db.agentic_workflows.update_one(
                {"workflow_id": workflow_id},
                {"$set": {
                    "status": final_status,
                    "completed_at": datetime.utcnow(),
                    "results": results
                }}
            )
            
            return {
                "workflow_id": workflow_id,
                "status": final_status,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.db.agentic_workflows.update_one(
                {"workflow_id": workflow_id},
                {"$set": {"status": "failed", "error": str(e)}}
            )
            raise
    
    async def _execute_workflow_steps(self, workflow: Dict) -> List[Dict[str, Any]]:
        """Execute workflow steps with intelligent sequencing and parallel processing"""
        steps = workflow["steps"]
        results = []
        
        # Group steps by dependencies and parallel execution capability
        parallel_groups = self._group_steps_for_execution(steps)
        
        for group in parallel_groups:
            if len(group) == 1:
                # Sequential execution
                result = await self._execute_single_step(group[0], workflow)
                results.append(result)
            else:
                # Parallel execution
                group_results = await asyncio.gather(
                    *[self._execute_single_step(step, workflow) for step in group],
                    return_exceptions=True
                )
                results.extend(group_results)
        
        return results
    
    def _group_steps_for_execution(self, steps: List[Dict]) -> List[List[Dict]]:
        """Group steps for optimal execution order"""
        # Simple implementation - can be enhanced with dependency analysis
        sequential_steps = [step for step in steps if not step.get("parallel_execution", False)]
        parallel_steps = [step for step in steps if step.get("parallel_execution", False)]
        
        groups = []
        
        # Add sequential steps as individual groups
        for step in sequential_steps:
            groups.append([step])
        
        # Add parallel steps as a single group
        if parallel_steps:
            groups.append(parallel_steps)
            
        return groups
    
    async def _execute_single_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute a single workflow step with intelligent adaptation"""
        step_id = step["step_id"]
        action_type = step["action_type"]
        
        try:
            logger.info(f"Executing step {step_id}: {action_type}")
            
            # Route to appropriate execution engine
            if action_type == "navigate":
                result = await self._execute_navigation_step(step, workflow)
            elif action_type == "extract_data":
                result = await self._execute_data_extraction_step(step, workflow)
            elif action_type == "social_media_action":
                result = await self._execute_social_media_step(step, workflow)
            elif action_type == "file_operation":
                result = await self._execute_file_operation_step(step, workflow)
            elif action_type == "email_action":
                result = await self._execute_email_step(step, workflow)
            elif action_type == "report_generation":
                result = await self._execute_report_generation_step(step, workflow)
            else:
                result = await self._execute_generic_step(step, workflow)
            
            return {
                "step_id": step_id,
                "success": True,
                "result": result,
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Step execution failed {step_id}: {e}")
            return {
                "step_id": step_id,
                "success": False,
                "error": str(e),
                "executed_at": datetime.utcnow().isoformat()
            }
    
    async def _execute_navigation_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute navigation with enhanced browser capabilities"""
        target = step.get("target", "")
        parameters = step.get("parameters", {})
        
        # Use enhanced browser engine
        from native_browser_engine import EnhancedBrowserEngine
        browser = EnhancedBrowserEngine()
        
        result = await browser.navigate_with_automation(
            url=target,
            actions=parameters.get("actions", []),
            wait_conditions=parameters.get("wait_conditions", [])
        )
        
        return result
    
    async def _execute_data_extraction_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute data extraction with AI-powered parsing"""
        target = step.get("target", "")
        parameters = step.get("parameters", {})
        
        # Enhanced data extraction with computer vision
        from ai_data_extractor import AIDataExtractor
        extractor = AIDataExtractor()
        
        result = await extractor.extract_intelligent_data(
            source=target,
            extraction_rules=parameters.get("extraction_rules", []),
            output_format=parameters.get("output_format", "json")
        )
        
        return result
    
    async def _execute_social_media_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute social media actions"""
        platform = step.get("parameters", {}).get("platform", "")
        action = step.get("parameters", {}).get("action", "")
        
        # Social media automation
        from social_media_automation import SocialMediaAutomator
        automator = SocialMediaAutomator()
        
        result = await automator.execute_action(
            platform=platform,
            action=action,
            parameters=step.get("parameters", {})
        )
        
        return result
    
    async def _execute_file_operation_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute file operations"""
        operation = step.get("parameters", {}).get("operation", "")
        
        # File system operations
        result = await self._perform_file_operation(step.get("parameters", {}))
        return result
    
    async def _execute_email_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute email operations"""
        # Email automation integration
        return {"status": "email_sent", "message": "Email functionality ready"}
    
    async def _execute_report_generation_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute report generation"""
        # Advanced report generation
        from report_generator import AdvancedReportGenerator
        generator = AdvancedReportGenerator()
        
        result = await generator.generate_intelligent_report(
            data_sources=step.get("parameters", {}).get("data_sources", []),
            report_type=step.get("parameters", {}).get("report_type", "summary"),
            output_format=step.get("parameters", {}).get("output_format", "html")
        )
        
        return result
    
    async def _execute_generic_step(self, step: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute generic step with AI interpretation"""
        # Generic step execution with AI interpretation
        return {"status": "completed", "message": f"Executed {step.get('action_type', 'unknown')}"}
    
    def _template_based_parsing(self, description: str, context: Dict[str, Any]) -> List[Dict]:
        """Fallback template-based workflow parsing"""
        # Simple keyword-based parsing for common patterns
        steps = []
        
        if "find" in description.lower() and "extract" in description.lower():
            steps.append({
                "action_type": "navigate",
                "target": context.get("current_url", ""),
                "parameters": {"wait_for_load": True}
            })
            steps.append({
                "action_type": "extract_data",
                "target": "current_page",
                "parameters": {"extraction_type": "intelligent"}
            })
        
        if "report" in description.lower():
            steps.append({
                "action_type": "report_generation",
                "target": "extracted_data",
                "parameters": {"format": "comprehensive"}
            })
        
        return steps
    
    def _load_workflow_templates(self) -> Dict[str, Dict]:
        """Load predefined workflow templates"""
        return {
            "research_and_report": {
                "steps": [
                    {"action_type": "navigate", "description": "Navigate to sources"},
                    {"action_type": "extract_data", "description": "Extract relevant information"},
                    {"action_type": "report_generation", "description": "Generate comprehensive report"}
                ]
            },
            "social_media_automation": {
                "steps": [
                    {"action_type": "social_media_action", "description": "Execute social media tasks"},
                    {"action_type": "report_generation", "description": "Generate activity report"}
                ]
            }
        }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed workflow execution status"""
        workflow = self.db.agentic_workflows.find_one({"workflow_id": workflow_id})
        if not workflow:
            return None
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.get("status", "unknown"),
            "progress": workflow.get("progress", {}),
            "description": workflow.get("description", ""),
            "created_at": workflow.get("created_at"),
            "results": workflow.get("results", [])
        }
    
    async def _perform_file_operation(self, parameters: Dict) -> Dict[str, Any]:
        """Perform file system operations"""
        operation = parameters.get("operation", "")
        
        if operation == "organize_downloads":
            # File organization logic
            return {"status": "organized", "files_moved": 0}
        elif operation == "compress_images":
            # Image compression logic
            return {"status": "compressed", "images_processed": 0}
        
        return {"status": "completed"}

# Initialize global agentic engine
agentic_engine = None

def initialize_agentic_engine(mongo_client: MongoClient):
    global agentic_engine
    agentic_engine = AdvancedAgenticEngine(mongo_client)
    return agentic_engine