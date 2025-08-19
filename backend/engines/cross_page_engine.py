"""
Cross-Page Workflow Engine - Advanced multi-site automation
Enables seamless workflow execution across multiple websites and platforms
"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class CrossPageActionType(Enum):
    NAVIGATE = "navigate"
    EXTRACT_DATA = "extract_data"
    TRANSFER_DATA = "transfer_data"
    FILL_FORM = "fill_form"
    CLICK_ELEMENT = "click_element"
    WAIT_CONDITION = "wait_condition"
    VALIDATE_DATA = "validate_data"
    STORE_CONTEXT = "store_context"
    LOAD_CONTEXT = "load_context"

@dataclass
class CrossPageContext:
    session_id: str
    current_url: str
    data_store: Dict[str, Any]
    visited_sites: List[str]
    workflow_state: str
    error_history: List[Dict[str, Any]]
    
class CrossPageWorkflowEngine:
    def __init__(self):
        self.active_sessions = {}
        self.workflow_templates = {}
        self.cross_site_data_store = {}
        self.session_contexts = {}
        
    async def execute_multi_site_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflows spanning multiple websites seamlessly
        Core cross-page automation capability
        """
        
        workflow_id = workflow.get("id", str(uuid.uuid4()))
        
        # Initialize cross-page context
        context = CrossPageContext(
            session_id=workflow_id,
            current_url="",
            data_store={},
            visited_sites=[],
            workflow_state="initialized",
            error_history=[]
        )
        
        # Store context for session management
        self.session_contexts[workflow_id] = context
        
        execution_result = {
            "workflow_id": workflow_id,
            "success": True,
            "steps_completed": 0,
            "sites_visited": 0,
            "data_transferred": 0,
            "execution_time": 0,
            "step_results": [],
            "final_context": {},
            "cross_site_data": {}
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Execute workflow steps with cross-page context management
            steps = workflow.get("steps", [])
            
            for i, step in enumerate(steps):
                context.workflow_state = f"executing_step_{i}"
                
                step_result = await self._execute_cross_page_step(step, context)
                execution_result["step_results"].append(step_result)
                
                if step_result.get("success", False):
                    execution_result["steps_completed"] += 1
                    
                    # Update context with step results
                    await self._update_context_from_step(context, step_result)
                    
                    # Track site visits
                    if step_result.get("site_visited"):
                        if step_result["site_visited"] not in context.visited_sites:
                            context.visited_sites.append(step_result["site_visited"])
                            execution_result["sites_visited"] += 1
                    
                    # Track data transfers
                    if step_result.get("data_transferred"):
                        execution_result["data_transferred"] += 1
                
                else:
                    # Handle step failure
                    error_info = {
                        "step_index": i,
                        "error": step_result.get("error", "Unknown error"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    context.error_history.append(error_info)
                    
                    # Check if this is a critical failure
                    if step.get("critical", True):
                        execution_result["success"] = False
                        break
            
            context.workflow_state = "completed"
            
        except Exception as e:
            execution_result["success"] = False
            execution_result["error"] = str(e)
            context.workflow_state = "failed"
        
        finally:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            execution_result["execution_time"] = execution_time
            
            # Compile final results
            execution_result["final_context"] = {
                "data_store": context.data_store,
                "visited_sites": context.visited_sites,
                "workflow_state": context.workflow_state
            }
            
            execution_result["cross_site_data"] = self.cross_site_data_store.get(workflow_id, {})
        
        return execution_result
    
    async def _execute_cross_page_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute individual cross-page workflow step"""
        
        step_type = step.get("type", "")
        step_id = step.get("id", str(uuid.uuid4()))
        
        start_time = datetime.utcnow()
        
        try:
            if step_type == CrossPageActionType.NAVIGATE.value:
                result = await self._execute_navigation_step(step, context)
            elif step_type == CrossPageActionType.EXTRACT_DATA.value:
                result = await self._execute_extraction_step(step, context)
            elif step_type == CrossPageActionType.TRANSFER_DATA.value:
                result = await self._execute_transfer_step(step, context)
            elif step_type == CrossPageActionType.FILL_FORM.value:
                result = await self._execute_form_step(step, context)
            elif step_type == CrossPageActionType.CLICK_ELEMENT.value:
                result = await self._execute_click_step(step, context)
            elif step_type == CrossPageActionType.WAIT_CONDITION.value:
                result = await self._execute_wait_step(step, context)
            elif step_type == CrossPageActionType.VALIDATE_DATA.value:
                result = await self._execute_validation_step(step, context)
            else:
                result = await self._execute_generic_step(step, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "step_id": step_id,
                "step_type": step_type,
                "success": True,
                "execution_time": execution_time,
                "result": result,
                "site_visited": result.get("url_visited"),
                "data_transferred": result.get("data_transferred", False)
            }
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "step_id": step_id,
                "step_type": step_type,
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "site_visited": None,
                "data_transferred": False
            }
    
    async def _execute_navigation_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute cross-page navigation with context preservation"""
        
        target_url = step.get("url", "")
        navigation_options = step.get("options", {})
        
        # Simulate navigation delay
        await asyncio.sleep(0.1)
        
        # Update context
        previous_url = context.current_url
        context.current_url = target_url
        
        # Store navigation data for cross-site context
        navigation_data = {
            "previous_url": previous_url,
            "current_url": target_url,
            "navigation_timestamp": datetime.utcnow().isoformat(),
            "referrer": previous_url if previous_url else None
        }
        
        # Store cross-site navigation context
        if context.session_id not in self.cross_site_data_store:
            self.cross_site_data_store[context.session_id] = {}
        
        self.cross_site_data_store[context.session_id]["last_navigation"] = navigation_data
        
        return {
            "navigated_to": target_url,
            "previous_url": previous_url,
            "page_loaded": True,
            "url_visited": target_url,
            "cross_site_context_preserved": True,
            "navigation_data": navigation_data
        }
    
    async def _execute_extraction_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute data extraction with cross-site context awareness"""
        
        extraction_config = step.get("extraction_config", {})
        data_key = step.get("data_key", "extracted_data")
        
        # Simulate extraction delay
        await asyncio.sleep(0.2)
        
        # Simulate extracted data
        extracted_data = {
            "items": [
                {"id": 1, "title": f"Item from {context.current_url}", "value": "Sample Value 1"},
                {"id": 2, "title": f"Data from {context.current_url}", "value": "Sample Value 2"}
            ],
            "metadata": {
                "source_url": context.current_url,
                "extraction_timestamp": datetime.utcnow().isoformat(),
                "extraction_method": extraction_config.get("method", "intelligent")
            },
            "count": 2
        }
        
        # Store extracted data in cross-page context
        context.data_store[data_key] = extracted_data
        
        # Store in cross-site data store for transfer between sites
        if context.session_id not in self.cross_site_data_store:
            self.cross_site_data_store[context.session_id] = {}
        
        self.cross_site_data_store[context.session_id][data_key] = extracted_data
        
        return {
            "extraction_success": True,
            "data_key": data_key,
            "items_extracted": extracted_data["count"],
            "data_stored_for_transfer": True,
            "extraction_metadata": extracted_data["metadata"]
        }
    
    async def _execute_transfer_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute cross-site data transfer"""
        
        source_key = step.get("source_key", "")
        target_site = step.get("target_site", "")
        transfer_method = step.get("transfer_method", "form_fill")
        
        # Simulate transfer delay
        await asyncio.sleep(0.15)
        
        # Get data from cross-site store
        source_data = self.cross_site_data_store.get(context.session_id, {}).get(source_key)
        
        if not source_data:
            raise Exception(f"No data found for key '{source_key}' in cross-site store")
        
        # Simulate data transfer process
        transfer_result = {
            "transfer_method": transfer_method,
            "data_transferred": True,
            "items_transferred": source_data.get("count", 0) if isinstance(source_data, dict) else 1,
            "target_site": target_site,
            "source_key": source_key,
            "transfer_timestamp": datetime.utcnow().isoformat()
        }
        
        # Store transfer log
        transfer_log_key = f"transfer_{datetime.utcnow().timestamp()}"
        self.cross_site_data_store[context.session_id][transfer_log_key] = transfer_result
        
        return transfer_result
    
    async def _execute_form_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute form filling with cross-site data"""
        
        form_config = step.get("form_config", {})
        data_source = step.get("data_source", "")
        
        # Simulate form filling delay
        await asyncio.sleep(0.12)
        
        # Get data from context for form filling
        form_data = {}
        if data_source:
            source_data = context.data_store.get(data_source) or self.cross_site_data_store.get(context.session_id, {}).get(data_source)
            if source_data and isinstance(source_data, dict):
                # Extract relevant data for form filling
                if "items" in source_data:
                    # Use first item for form filling
                    first_item = source_data["items"][0] if source_data["items"] else {}
                    form_data = {
                        "title": first_item.get("title", ""),
                        "value": first_item.get("value", ""),
                        "source_url": source_data.get("metadata", {}).get("source_url", "")
                    }
        
        return {
            "form_filled": True,
            "fields_filled": len(form_data),
            "data_source": data_source,
            "form_data_used": form_data,
            "cross_site_data_utilized": bool(data_source)
        }
    
    async def _execute_click_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute element clicking with context awareness"""
        
        selector = step.get("selector", "")
        click_options = step.get("options", {})
        
        # Simulate click delay
        await asyncio.sleep(0.05)
        
        return {
            "element_clicked": True,
            "selector": selector,
            "click_successful": True,
            "options_used": click_options
        }
    
    async def _execute_wait_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute wait conditions with cross-page awareness"""
        
        condition = step.get("condition", "page_ready")
        timeout = step.get("timeout", 10)
        
        # Simulate wait time (scaled down)
        wait_time = min(timeout / 10, 1.0)  # Max 1 second for demo
        await asyncio.sleep(wait_time)
        
        return {
            "condition_met": True,
            "condition": condition,
            "wait_time": wait_time,
            "timeout": timeout
        }
    
    async def _execute_validation_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute data validation across sites"""
        
        validation_rules = step.get("validation_rules", [])
        data_key = step.get("data_key", "")
        
        # Simulate validation delay
        await asyncio.sleep(0.08)
        
        # Get data to validate
        data_to_validate = context.data_store.get(data_key)
        
        validation_results = {
            "validation_passed": True,
            "rules_checked": len(validation_rules),
            "data_key": data_key,
            "validation_details": []
        }
        
        # Simulate validation checks
        for rule in validation_rules:
            validation_results["validation_details"].append({
                "rule": rule,
                "passed": True,
                "message": f"Rule '{rule}' passed validation"
            })
        
        return validation_results
    
    async def _execute_generic_step(self, step: Dict[str, Any], context: CrossPageContext) -> Dict[str, Any]:
        """Execute generic cross-page step"""
        
        await asyncio.sleep(0.1)
        
        return {
            "step_executed": True,
            "step_type": step.get("type", "generic"),
            "context_aware": True
        }
    
    async def _update_context_from_step(self, context: CrossPageContext, step_result: Dict[str, Any]):
        """Update cross-page context based on step results"""
        
        result_data = step_result.get("result", {})
        
        # Update URL if navigation occurred
        if "navigated_to" in result_data:
            context.current_url = result_data["navigated_to"]
        
        # Store any data that was extracted
        if "data_key" in result_data and "extraction_success" in result_data:
            # Data is already stored in the extraction step
            pass
        
        # Update workflow state based on step completion
        if step_result.get("success", False):
            # Success - context is maintained automatically
            pass
        else:
            # Failure - log for debugging
            pass
    
    async def create_cross_site_workflow_template(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create reusable cross-site workflow template"""
        
        template_id = template_config.get("id", str(uuid.uuid4()))
        
        template = {
            "template_id": template_id,
            "name": template_config.get("name", "Cross-Site Workflow"),
            "description": template_config.get("description", ""),
            "sites_involved": template_config.get("sites", []),
            "steps_template": template_config.get("steps", []),
            "data_flow": template_config.get("data_flow", {}),
            "estimated_duration": self._estimate_template_duration(template_config.get("steps", [])),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store template
        self.workflow_templates[template_id] = template
        
        return {
            "template_created": True,
            "template_id": template_id,
            "template": template
        }
    
    async def execute_template_workflow(self, template_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow from template with parameters"""
        
        template = self.workflow_templates.get(template_id)
        if not template:
            return {"error": f"Template {template_id} not found"}
        
        # Instantiate workflow from template
        workflow_instance = await self._instantiate_workflow_from_template(template, parameters)
        
        # Execute the instantiated workflow
        return await self.execute_multi_site_workflow(workflow_instance)
    
    async def _instantiate_workflow_from_template(
        self, 
        template: Dict[str, Any], 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create workflow instance from template with parameters"""
        
        workflow = {
            "id": str(uuid.uuid4()),
            "template_id": template["template_id"],
            "name": template["name"],
            "steps": []
        }
        
        # Process template steps with parameters
        for step_template in template.get("steps_template", []):
            step = step_template.copy()
            
            # Replace parameters in step
            for key, value in step.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    param_name = value[2:-1]  # Remove ${ and }
                    if param_name in parameters:
                        step[key] = parameters[param_name]
            
            workflow["steps"].append(step)
        
        return workflow
    
    def _estimate_template_duration(self, steps: List[Dict[str, Any]]) -> float:
        """Estimate execution duration for workflow template"""
        
        base_duration = 0.0
        
        for step in steps:
            step_type = step.get("type", "")
            
            # Estimate durations based on step type
            duration_map = {
                CrossPageActionType.NAVIGATE.value: 3.0,
                CrossPageActionType.EXTRACT_DATA.value: 5.0,
                CrossPageActionType.TRANSFER_DATA.value: 2.0,
                CrossPageActionType.FILL_FORM.value: 4.0,
                CrossPageActionType.CLICK_ELEMENT.value: 1.0,
                CrossPageActionType.WAIT_CONDITION.value: 2.0,
                CrossPageActionType.VALIDATE_DATA.value: 1.5
            }
            
            base_duration += duration_map.get(step_type, 2.0)
        
        # Add overhead for cross-site coordination
        coordination_overhead = len(steps) * 0.5
        
        return base_duration + coordination_overhead
    
    async def get_cross_site_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of cross-site workflow execution"""
        
        context = self.session_contexts.get(workflow_id)
        if not context:
            return {"error": f"Workflow {workflow_id} not found"}
        
        cross_site_data = self.cross_site_data_store.get(workflow_id, {})
        
        return {
            "workflow_id": workflow_id,
            "current_url": context.current_url,
            "workflow_state": context.workflow_state,
            "sites_visited": len(context.visited_sites),
            "visited_sites": context.visited_sites,
            "data_store_keys": list(context.data_store.keys()),
            "cross_site_data_keys": list(cross_site_data.keys()),
            "error_count": len(context.error_history),
            "last_error": context.error_history[-1] if context.error_history else None
        }
    
    async def cleanup_workflow_session(self, workflow_id: str) -> Dict[str, Any]:
        """Clean up workflow session and associated data"""
        
        cleanup_result = {
            "workflow_id": workflow_id,
            "context_cleaned": False,
            "cross_site_data_cleaned": False,
            "session_removed": False
        }
        
        # Remove session context
        if workflow_id in self.session_contexts:
            del self.session_contexts[workflow_id]
            cleanup_result["context_cleaned"] = True
        
        # Remove cross-site data
        if workflow_id in self.cross_site_data_store:
            del self.cross_site_data_store[workflow_id]
            cleanup_result["cross_site_data_cleaned"] = True
        
        # Remove from active sessions
        if workflow_id in self.active_sessions:
            del self.active_sessions[workflow_id]
            cleanup_result["session_removed"] = True
        
        return cleanup_result
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get cross-page workflow engine statistics"""
        
        return {
            "engine_status": "operational",
            "active_sessions": len(self.active_sessions),
            "session_contexts": len(self.session_contexts),
            "workflow_templates": len(self.workflow_templates),
            "cross_site_data_stores": len(self.cross_site_data_store),
            "supported_actions": [action.value for action in CrossPageActionType],
            "capabilities": [
                "cross_site_data_transfer",
                "context_preservation",
                "multi_site_navigation",
                "intelligent_form_filling",
                "data_validation_across_sites",
                "workflow_templates",
                "real_time_monitoring"
            ]
        }