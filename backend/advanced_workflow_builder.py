"""
AETHER Advanced Multi-Step Workflow Builder Engine
Implements visual workflow creation with drag-and-drop interface support
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pymongo import MongoClient
from dataclasses import dataclass
import networkx as nx

logger = logging.getLogger(__name__)

@dataclass
class WorkflowNode:
    """Represents a single workflow step/node"""
    id: str
    type: str  # 'action', 'condition', 'trigger', 'delay'
    name: str
    config: Dict[str, Any]
    position: Dict[str, int]  # x, y coordinates for UI
    inputs: List[str]  # Connected input node IDs
    outputs: List[str]  # Connected output node IDs

@dataclass 
class WorkflowConnection:
    """Represents connection between workflow nodes"""
    id: str
    source_id: str
    target_id: str
    source_handle: str
    target_handle: str
    condition: Optional[Dict[str, Any]] = None

class AdvancedWorkflowBuilder:
    """Advanced Multi-Step Workflow Engine with Visual Builder Support"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.workflows = self.db.advanced_workflows
        self.executions = self.db.workflow_executions
        self.templates = self.db.workflow_templates
        
        # Initialize workflow templates
        asyncio.create_task(self._initialize_templates())
        
        # Workflow execution graph
        self.execution_graphs = {}
        
    async def _initialize_templates(self):
        """Initialize predefined workflow templates"""
        templates = [
            {
                "id": "social_media_automation",
                "name": "Social Media Cross-Posting",
                "description": "Post content across multiple social media platforms",
                "category": "social_media",
                "nodes": [
                    {
                        "id": "trigger_1",
                        "type": "trigger",
                        "name": "Content Input",
                        "config": {"trigger_type": "manual", "inputs": ["text", "image"]},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action_1", 
                        "type": "action",
                        "name": "Post to Twitter",
                        "config": {"platform": "twitter", "action": "create_post"},
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "action_2",
                        "type": "action", 
                        "name": "Post to LinkedIn",
                        "config": {"platform": "linkedin", "action": "create_post"},
                        "position": {"x": 300, "y": 200}
                    },
                    {
                        "id": "condition_1",
                        "type": "condition",
                        "name": "Success Check",
                        "config": {"condition": "all_success"},
                        "position": {"x": 500, "y": 150}
                    }
                ],
                "connections": [
                    {"source": "trigger_1", "target": "action_1"},
                    {"source": "trigger_1", "target": "action_2"}, 
                    {"source": "action_1", "target": "condition_1"},
                    {"source": "action_2", "target": "condition_1"}
                ]
            },
            {
                "id": "data_collection_analysis", 
                "name": "Web Data Collection & Analysis",
                "description": "Scrape website data and generate analytical reports",
                "category": "data_analysis",
                "nodes": [
                    {
                        "id": "trigger_1",
                        "type": "trigger",
                        "name": "URL Input",
                        "config": {"trigger_type": "manual", "inputs": ["url_list"]},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action_1",
                        "type": "action",
                        "name": "Scrape Data",
                        "config": {"action": "web_scraping", "parallel": True},
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "action_2",
                        "type": "action",
                        "name": "Analyze Data", 
                        "config": {"action": "data_analysis", "ai_enhanced": True},
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "action_3",
                        "type": "action",
                        "name": "Generate Report",
                        "config": {"action": "report_generation", "format": "pdf"},
                        "position": {"x": 700, "y": 100}
                    }
                ],
                "connections": [
                    {"source": "trigger_1", "target": "action_1"},
                    {"source": "action_1", "target": "action_2"},
                    {"source": "action_2", "target": "action_3"}
                ]
            },
            {
                "id": "email_automation",
                "name": "Advanced Email Campaign",
                "description": "Automated email sequences with personalization",
                "category": "email_marketing",
                "nodes": [
                    {
                        "id": "trigger_1",
                        "type": "trigger", 
                        "name": "Contact Import",
                        "config": {"trigger_type": "schedule", "source": "csv_upload"},
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action_1",
                        "type": "action",
                        "name": "Personalize Content",
                        "config": {"action": "ai_personalization", "fields": ["name", "company", "interests"]},
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "delay_1",
                        "type": "delay",
                        "name": "Wait 2 Hours",
                        "config": {"delay_type": "hours", "duration": 2},
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "action_2",
                        "type": "action",
                        "name": "Send Email",
                        "config": {"action": "send_email", "template": "campaign_1"},
                        "position": {"x": 700, "y": 100}
                    }
                ],
                "connections": [
                    {"source": "trigger_1", "target": "action_1"},
                    {"source": "action_1", "target": "delay_1"},
                    {"source": "delay_1", "target": "action_2"}
                ]
            }
        ]
        
        for template in templates:
            await self._save_template(template)
    
    async def _save_template(self, template: Dict[str, Any]):
        """Save workflow template to database"""
        try:
            template["created_at"] = datetime.utcnow()
            template["updated_at"] = datetime.utcnow()
            
            # Check if template exists
            existing = self.templates.find_one({"id": template["id"]})
            if existing:
                self.templates.replace_one({"id": template["id"]}, template)
            else:
                self.templates.insert_one(template)
                
        except Exception as e:
            logger.error(f"Failed to save workflow template: {e}")
    
    async def get_workflow_templates(self, category: str = None) -> List[Dict[str, Any]]:
        """Get available workflow templates"""
        try:
            query = {}
            if category:
                query["category"] = category
                
            templates = list(self.templates.find(query, {"_id": 0}))
            return templates
            
        except Exception as e:
            logger.error(f"Failed to get workflow templates: {e}")
            return []
    
    async def create_workflow_from_template(self, template_id: str, user_session: str, 
                                         custom_config: Dict[str, Any] = None) -> str:
        """Create new workflow instance from template"""
        try:
            # Get template
            template = self.templates.find_one({"id": template_id})
            if not template:
                raise Exception(f"Template {template_id} not found")
            
            # Create new workflow instance
            workflow_id = str(uuid.uuid4())
            
            workflow = {
                "id": workflow_id,
                "name": template["name"],
                "description": template["description"],
                "template_id": template_id,
                "user_session": user_session,
                "nodes": template["nodes"].copy(),
                "connections": template["connections"].copy(),
                "status": "draft",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "config": custom_config or {}
            }
            
            # Apply custom configuration
            if custom_config:
                workflow = self._apply_custom_config(workflow, custom_config)
            
            self.workflows.insert_one(workflow)
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create workflow from template: {e}")
            return None
    
    async def create_custom_workflow(self, user_session: str, workflow_data: Dict[str, Any]) -> str:
        """Create completely custom workflow"""
        try:
            workflow_id = str(uuid.uuid4())
            
            workflow = {
                "id": workflow_id,
                "name": workflow_data.get("name", "Custom Workflow"),
                "description": workflow_data.get("description", ""),
                "template_id": None,
                "user_session": user_session,
                "nodes": workflow_data.get("nodes", []),
                "connections": workflow_data.get("connections", []),
                "status": "draft",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "config": workflow_data.get("config", {})
            }
            
            # Validate workflow structure
            if not self._validate_workflow(workflow):
                raise Exception("Invalid workflow structure")
            
            self.workflows.insert_one(workflow)
            return workflow_id
            
        except Exception as e:
            logger.error(f"Failed to create custom workflow: {e}")
            return None
    
    def _validate_workflow(self, workflow: Dict[str, Any]) -> bool:
        """Validate workflow structure and connections"""
        try:
            nodes = workflow.get("nodes", [])
            connections = workflow.get("connections", [])
            
            # Check if there's at least one trigger node
            trigger_nodes = [n for n in nodes if n.get("type") == "trigger"]
            if not trigger_nodes:
                return False
            
            # Validate node structure
            for node in nodes:
                required_fields = ["id", "type", "name", "config", "position"]
                if not all(field in node for field in required_fields):
                    return False
            
            # Validate connections
            node_ids = [n["id"] for n in nodes]
            for conn in connections:
                if conn["source"] not in node_ids or conn["target"] not in node_ids:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Workflow validation error: {e}")
            return False
    
    def _apply_custom_config(self, workflow: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply custom configuration to workflow"""
        try:
            # Apply node-specific configurations
            if "node_configs" in config:
                for node_id, node_config in config["node_configs"].items():
                    for node in workflow["nodes"]:
                        if node["id"] == node_id:
                            node["config"].update(node_config)
            
            # Apply global configurations
            if "global_config" in config:
                workflow["config"].update(config["global_config"])
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to apply custom config: {e}")
            return workflow
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None) -> str:
        """Execute workflow with advanced orchestration"""
        try:
            # Get workflow
            workflow = self.workflows.find_one({"id": workflow_id})
            if not workflow:
                raise Exception(f"Workflow {workflow_id} not found")
            
            # Create execution record
            execution_id = str(uuid.uuid4())
            execution = {
                "id": execution_id,
                "workflow_id": workflow_id,
                "status": "running",
                "started_at": datetime.utcnow(),
                "input_data": input_data or {},
                "steps": [],
                "current_step": 0,
                "total_steps": len(workflow["nodes"]),
                "results": {},
                "error_message": None
            }
            
            self.executions.insert_one(execution)
            
            # Build execution graph
            execution_graph = self._build_execution_graph(workflow)
            self.execution_graphs[execution_id] = execution_graph
            
            # Start workflow execution in background
            asyncio.create_task(self._execute_workflow_async(execution_id, workflow, input_data))
            
            return execution_id
            
        except Exception as e:
            logger.error(f"Failed to start workflow execution: {e}")
            return None
    
    def _build_execution_graph(self, workflow: Dict[str, Any]) -> nx.DiGraph:
        """Build networkx directed graph for workflow execution"""
        try:
            graph = nx.DiGraph()
            
            # Add nodes
            for node in workflow["nodes"]:
                graph.add_node(node["id"], **node)
            
            # Add edges (connections)
            for conn in workflow["connections"]:
                graph.add_edge(conn["source"], conn["target"], **conn)
            
            return graph
            
        except Exception as e:
            logger.error(f"Failed to build execution graph: {e}")
            return nx.DiGraph()
    
    async def _execute_workflow_async(self, execution_id: str, workflow: Dict[str, Any], input_data: Dict[str, Any]):
        """Execute workflow asynchronously with proper orchestration"""
        try:
            graph = self.execution_graphs.get(execution_id)
            if not graph:
                raise Exception("Execution graph not found")
            
            # Find starting nodes (triggers)
            start_nodes = [n for n in graph.nodes() if graph.in_degree(n) == 0]
            
            # Execute nodes in topological order
            execution_order = list(nx.topological_sort(graph))
            
            results = {}
            context = input_data.copy()
            
            for node_id in execution_order:
                node_data = graph.nodes[node_id]
                
                # Update execution status
                self._update_execution_step(execution_id, node_id, "running")
                
                try:
                    # Execute node
                    result = await self._execute_node(node_data, context, results)
                    results[node_id] = result
                    
                    # Update context with results
                    if isinstance(result, dict):
                        context.update(result)
                    
                    self._update_execution_step(execution_id, node_id, "completed", result)
                    
                except Exception as node_error:
                    logger.error(f"Node {node_id} execution failed: {node_error}")
                    self._update_execution_step(execution_id, node_id, "failed", str(node_error))
                    
                    # Mark entire execution as failed
                    self.executions.update_one(
                        {"id": execution_id},
                        {
                            "$set": {
                                "status": "failed",
                                "error_message": f"Node {node_id} failed: {str(node_error)}",
                                "completed_at": datetime.utcnow()
                            }
                        }
                    )
                    return
            
            # Mark execution as completed
            self.executions.update_one(
                {"id": execution_id},
                {
                    "$set": {
                        "status": "completed",
                        "results": results,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            self.executions.update_one(
                {"id": execution_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(e),
                        "completed_at": datetime.utcnow()
                    }
                }
            )
    
    async def _execute_node(self, node: Dict[str, Any], context: Dict[str, Any], 
                           previous_results: Dict[str, Any]) -> Any:
        """Execute individual workflow node"""
        try:
            node_type = node["type"]
            config = node["config"]
            
            if node_type == "trigger":
                return await self._execute_trigger_node(config, context)
            elif node_type == "action":
                return await self._execute_action_node(config, context, previous_results)
            elif node_type == "condition":
                return await self._execute_condition_node(config, context, previous_results)
            elif node_type == "delay":
                return await self._execute_delay_node(config)
            else:
                raise Exception(f"Unknown node type: {node_type}")
                
        except Exception as e:
            logger.error(f"Node execution error: {e}")
            raise
    
    async def _execute_trigger_node(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trigger node"""
        trigger_type = config.get("trigger_type", "manual")
        
        if trigger_type == "manual":
            return {"trigger": "manual", "data": context}
        elif trigger_type == "schedule":
            return {"trigger": "schedule", "timestamp": datetime.utcnow().isoformat()}
        else:
            return {"trigger": trigger_type, "context": context}
    
    async def _execute_action_node(self, config: Dict[str, Any], context: Dict[str, Any], 
                                 previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action node with platform integration"""
        action = config.get("action")
        
        if action == "web_scraping":
            return await self._execute_web_scraping(config, context)
        elif action == "send_email":
            return await self._execute_email_action(config, context)
        elif action == "create_post":
            return await self._execute_social_post(config, context)
        elif action == "data_analysis":
            return await self._execute_data_analysis(config, context, previous_results)
        elif action == "report_generation":
            return await self._execute_report_generation(config, context, previous_results)
        else:
            # Generic action execution
            return {"action": action, "status": "completed", "config": config}
    
    async def _execute_condition_node(self, config: Dict[str, Any], context: Dict[str, Any], 
                                    previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute condition node"""
        condition = config.get("condition", "true")
        
        if condition == "all_success":
            # Check if all previous nodes succeeded
            all_success = all(
                result.get("status") == "completed" 
                for result in previous_results.values()
                if isinstance(result, dict)
            )
            return {"condition_met": all_success, "condition": condition}
        else:
            # Default condition evaluation
            return {"condition_met": True, "condition": condition}
    
    async def _execute_delay_node(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delay node"""
        delay_type = config.get("delay_type", "seconds")
        duration = config.get("duration", 1)
        
        if delay_type == "seconds":
            await asyncio.sleep(duration)
        elif delay_type == "minutes":
            await asyncio.sleep(duration * 60)
        elif delay_type == "hours":
            await asyncio.sleep(duration * 3600)
        
        return {"delay_completed": True, "duration": duration, "type": delay_type}
    
    async def _execute_web_scraping(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web scraping action"""
        # This would integrate with the web scraping module
        return {
            "action": "web_scraping",
            "status": "completed",
            "data": {"scraped_urls": context.get("url_list", []), "results": "Sample scraped data"}
        }
    
    async def _execute_email_action(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email sending action"""
        return {
            "action": "send_email",
            "status": "completed", 
            "template": config.get("template"),
            "recipients": context.get("recipients", [])
        }
    
    async def _execute_social_post(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute social media posting action"""
        platform = config.get("platform", "twitter")
        return {
            "action": "create_post",
            "platform": platform,
            "status": "completed",
            "content": context.get("content", "")
        }
    
    async def _execute_data_analysis(self, config: Dict[str, Any], context: Dict[str, Any], 
                                   previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data analysis action"""
        return {
            "action": "data_analysis", 
            "status": "completed",
            "analysis_type": config.get("analysis_type", "general"),
            "insights": ["Sample insight 1", "Sample insight 2"]
        }
    
    async def _execute_report_generation(self, config: Dict[str, Any], context: Dict[str, Any], 
                                       previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation action"""
        return {
            "action": "report_generation",
            "status": "completed",
            "format": config.get("format", "pdf"),
            "report_id": str(uuid.uuid4())
        }
    
    def _update_execution_step(self, execution_id: str, node_id: str, status: str, result: Any = None):
        """Update execution step status"""
        try:
            step_data = {
                "node_id": node_id,
                "status": status,
                "timestamp": datetime.utcnow(),
                "result": result
            }
            
            self.executions.update_one(
                {"id": execution_id},
                {
                    "$push": {"steps": step_data},
                    "$inc": {"current_step": 1}
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to update execution step: {e}")
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        try:
            execution = self.executions.find_one({"id": execution_id}, {"_id": 0})
            return execution or {}
            
        except Exception as e:
            logger.error(f"Failed to get execution status: {e}")
            return {}
    
    async def get_user_workflows(self, user_session: str, status: str = None) -> List[Dict[str, Any]]:
        """Get workflows for specific user"""
        try:
            query = {"user_session": user_session}
            if status:
                query["status"] = status
            
            workflows = list(self.workflows.find(query, {"_id": 0}))
            return workflows
            
        except Exception as e:
            logger.error(f"Failed to get user workflows: {e}")
            return []
    
    async def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing workflow"""
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = self.workflows.update_one(
                {"id": workflow_id},
                {"$set": updates}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update workflow: {e}")
            return False
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow"""
        try:
            result = self.workflows.delete_one({"id": workflow_id})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            return False

# Initialize global instance
advanced_workflow_builder = None

def initialize_advanced_workflow_builder(mongo_client: MongoClient):
    """Initialize advanced workflow builder"""
    global advanced_workflow_builder
    advanced_workflow_builder = AdvancedWorkflowBuilder(mongo_client)
    return advanced_workflow_builder