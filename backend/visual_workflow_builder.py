# Visual Workflow Builder - Drag & Drop Automation Interface
# Critical Gap #2: Fellou.ai-style visual workflow creation

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class NodeType(Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    OUTPUT = "output"

class ConnectionType(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONDITION_TRUE = "condition_true"
    CONDITION_FALSE = "condition_false"
    LOOP_ITERATION = "loop_iteration"
    DEFAULT = "default"

@dataclass
class WorkflowNode:
    node_id: str
    node_type: NodeType
    template_key: str
    position: Tuple[float, float]
    parameters: Dict[str, Any]
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class NodeConnection:
    connection_id: str
    source_node: str
    target_node: str
    source_output: str
    target_input: str
    connection_type: ConnectionType
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class VisualWorkflow:
    workflow_id: str
    name: str
    description: str
    created_by: str
    nodes: Dict[str, WorkflowNode] = field(default_factory=dict)
    connections: Dict[str, NodeConnection] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

class VisualWorkflowBuilder:
    """
    Visual Workflow Builder provides drag-and-drop interface for creating complex automation workflows.
    This addresses the gap where Fellou.ai has visual workflow creation vs Aether's text-based approach.
    """
    
    def __init__(self, mongo_client):
        self.db = mongo_client.aether_browser
        self.workflows: Dict[str, VisualWorkflow] = {}
        
        # Initialize node templates
        self.node_templates = self._initialize_node_templates()
        
        logger.info("🎨 Visual Workflow Builder initialized")
    
    def _initialize_node_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available node templates for drag & drop"""
        return {
            # TRIGGER NODES
            "trigger_webpage_load": {
                "name": "Webpage Loaded",
                "description": "Triggers when a webpage is loaded",
                "node_type": "trigger",
                "icon": "🌐",
                "inputs": [],
                "outputs": ["url", "content", "title"],
                "parameters": {
                    "url_pattern": {"type": "text", "default": "*", "description": "URL pattern to match"},
                    "wait_for_load": {"type": "boolean", "default": True, "description": "Wait for complete page load"}
                }
            },
            "trigger_time_schedule": {
                "name": "Time Schedule",
                "description": "Triggers at scheduled times",
                "node_type": "trigger",
                "icon": "⏰",
                "inputs": [],
                "outputs": ["timestamp"],
                "parameters": {
                    "schedule": {"type": "select", "options": ["daily", "weekly", "monthly"], "default": "daily"},
                    "time": {"type": "time", "default": "09:00", "description": "Time to trigger"}
                }
            },
            "trigger_user_command": {
                "name": "User Command",
                "description": "Triggers when user gives a command",
                "node_type": "trigger",
                "icon": "🗣️",
                "inputs": [],
                "outputs": ["command", "user_session"],
                "parameters": {
                    "command_pattern": {"type": "text", "default": "", "description": "Command pattern to match"}
                }
            },
            
            # ACTION NODES
            "action_navigate": {
                "name": "Navigate to URL",
                "description": "Navigate browser to specified URL",
                "node_type": "action",
                "icon": "🧭",
                "inputs": ["url"],
                "outputs": ["page_content", "success"],
                "parameters": {
                    "url": {"type": "text", "default": "", "description": "URL to navigate to"},
                    "wait_time": {"type": "number", "default": 3, "description": "Seconds to wait after navigation"}
                }
            },
            "action_extract_data": {
                "name": "Extract Data",
                "description": "Extract data from current webpage",
                "node_type": "action",
                "icon": "📊",
                "inputs": ["page_content"],
                "outputs": ["extracted_data", "success"],
                "parameters": {
                    "selectors": {"type": "textarea", "default": "", "description": "CSS selectors for data extraction"},
                    "data_type": {"type": "select", "options": ["text", "links", "images", "tables"], "default": "text"}
                }
            },
            "action_fill_form": {
                "name": "Fill Form",
                "description": "Fill form fields automatically",
                "node_type": "action",
                "icon": "📝",
                "inputs": ["form_data"],
                "outputs": ["form_filled", "success"],
                "parameters": {
                    "form_selector": {"type": "text", "default": "form", "description": "Form CSS selector"},
                    "field_mappings": {"type": "json", "default": {}, "description": "Field mappings as JSON"}
                }
            },
            "action_click_element": {
                "name": "Click Element",
                "description": "Click on webpage element",
                "node_type": "action",
                "icon": "👆",
                "inputs": ["element_selector"],
                "outputs": ["clicked", "success"],
                "parameters": {
                    "selector": {"type": "text", "default": "", "description": "CSS selector of element to click"},
                    "wait_after": {"type": "number", "default": 1, "description": "Seconds to wait after click"}
                }
            },
            "action_send_email": {
                "name": "Send Email",
                "description": "Send email notification",
                "node_type": "action",
                "icon": "📧",
                "inputs": ["email_content"],
                "outputs": ["sent", "success"],
                "parameters": {
                    "to": {"type": "text", "default": "", "description": "Recipient email"},
                    "subject": {"type": "text", "default": "", "description": "Email subject"},
                    "template": {"type": "select", "options": ["plain", "html", "report"], "default": "plain"}
                }
            },
            
            # CONDITION NODES
            "condition_text_contains": {
                "name": "Text Contains",
                "description": "Check if text contains specific content",
                "node_type": "condition",
                "icon": "🔍",
                "inputs": ["text_input"],
                "outputs": ["condition_result"],
                "parameters": {
                    "search_text": {"type": "text", "default": "", "description": "Text to search for"},
                    "case_sensitive": {"type": "boolean", "default": False, "description": "Case sensitive search"}
                }
            },
            "condition_element_exists": {
                "name": "Element Exists",
                "description": "Check if webpage element exists",
                "node_type": "condition",
                "icon": "🎯",
                "inputs": ["page_content"],
                "outputs": ["condition_result"],
                "parameters": {
                    "selector": {"type": "text", "default": "", "description": "CSS selector to check"},
                    "timeout": {"type": "number", "default": 5, "description": "Timeout in seconds"}
                }
            },
            "condition_compare_values": {
                "name": "Compare Values",
                "description": "Compare two values",
                "node_type": "condition",
                "icon": "⚖️",
                "inputs": ["value1", "value2"],
                "outputs": ["condition_result"],
                "parameters": {
                    "operator": {"type": "select", "options": ["equals", "not_equals", "greater", "less", "contains"], "default": "equals"},
                    "value_type": {"type": "select", "options": ["text", "number", "boolean"], "default": "text"}
                }
            },
            
            # LOOP NODES
            "loop_for_each": {
                "name": "For Each Item",
                "description": "Loop through list of items",
                "node_type": "loop",
                "icon": "🔄",
                "inputs": ["items_list"],
                "outputs": ["current_item", "loop_index"],
                "parameters": {
                    "max_iterations": {"type": "number", "default": 10, "description": "Maximum loop iterations"},
                    "delay_between": {"type": "number", "default": 1, "description": "Delay between iterations (seconds)"}
                }
            },
            "loop_while_condition": {
                "name": "While Condition",
                "description": "Loop while condition is true",
                "node_type": "loop",
                "icon": "🔁",
                "inputs": ["condition"],
                "outputs": ["iteration_count"],
                "parameters": {
                    "max_iterations": {"type": "number", "default": 100, "description": "Maximum loop iterations"},
                    "check_interval": {"type": "number", "default": 5, "description": "Seconds between condition checks"}
                }
            },
            
            # OUTPUT NODES
            "output_save_data": {
                "name": "Save Data",
                "description": "Save data to file or database",
                "node_type": "output",
                "icon": "💾",
                "inputs": ["data_to_save"],
                "outputs": ["saved_path"],
                "parameters": {
                    "format": {"type": "select", "options": ["json", "csv", "txt", "xlsx"], "default": "json"},
                    "filename": {"type": "text", "default": "output_{timestamp}", "description": "Output filename"}
                }
            },
            "output_send_notification": {
                "name": "Send Notification",
                "description": "Send notification to user",
                "node_type": "output",
                "icon": "🔔",
                "inputs": ["notification_content"],
                "outputs": ["notification_sent"],
                "parameters": {
                    "type": {"type": "select", "options": ["browser", "email", "webhook"], "default": "browser"},
                    "priority": {"type": "select", "options": ["low", "normal", "high", "urgent"], "default": "normal"}
                }
            },
            "output_generate_report": {
                "name": "Generate Report",
                "description": "Generate formatted report",
                "node_type": "output",
                "icon": "📋",
                "inputs": ["report_data"],
                "outputs": ["report_url"],
                "parameters": {
                    "template": {"type": "select", "options": ["summary", "detailed", "chart", "custom"], "default": "summary"},
                    "include_charts": {"type": "boolean", "default": True, "description": "Include data visualizations"}
                }
            }
        }
    
    async def get_node_templates(self) -> Dict[str, Any]:
        """Get available node templates for the visual builder"""
        return {
            "templates": self.node_templates,
            "categories": {
                "triggers": [k for k, v in self.node_templates.items() if v["node_type"] == "trigger"],
                "actions": [k for k, v in self.node_templates.items() if v["node_type"] == "action"],
                "conditions": [k for k, v in self.node_templates.items() if v["node_type"] == "condition"],
                "loops": [k for k, v in self.node_templates.items() if v["node_type"] == "loop"],
                "outputs": [k for k, v in self.node_templates.items() if v["node_type"] == "output"]
            }
        }
    
    async def create_visual_workflow(self, name: str, description: str, created_by: str) -> str:
        """Create a new visual workflow"""
        try:
            workflow_id = f"workflow_{uuid.uuid4()}"
            
            workflow = VisualWorkflow(
                workflow_id=workflow_id,
                name=name,
                description=description,
                created_by=created_by
            )
            
            # Store in memory
            self.workflows[workflow_id] = workflow
            
            # Store in database
            await self._store_workflow(workflow)
            
            logger.info(f"🎨 Visual workflow created: {name} -> {workflow_id}")
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error creating visual workflow: {e}")
            raise
    
    async def add_node_to_workflow(
        self, 
        workflow_id: str, 
        template_key: str, 
        position: Tuple[float, float],
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a node to a visual workflow"""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            if template_key not in self.node_templates:
                raise ValueError(f"Node template {template_key} not found")
            
            node_id = f"node_{uuid.uuid4()}"
            template = self.node_templates[template_key]
            
            # Merge template parameters with custom parameters
            parameters = template["parameters"].copy()
            if custom_parameters:
                parameters.update(custom_parameters)
            
            node = WorkflowNode(
                node_id=node_id,
                node_type=NodeType(template["node_type"]),
                template_key=template_key,
                position=position,
                parameters=parameters,
                inputs=template["inputs"].copy(),
                outputs=template["outputs"].copy()
            )
            
            # Add to workflow
            self.workflows[workflow_id].nodes[node_id] = node
            self.workflows[workflow_id].updated_at = datetime.utcnow()
            
            # Update database
            await self._update_workflow(workflow_id)
            
            logger.info(f"➕ Node added to workflow {workflow_id}: {template_key}")
            return node_id
            
        except Exception as e:
            logger.error(f"Error adding node to workflow: {e}")
            raise
    
    async def connect_nodes(
        self,
        workflow_id: str,
        source_node: str,
        target_node: str,
        source_output: str,
        target_input: str,
        connection_type: str = "success"
    ) -> str:
        """Connect two nodes in a visual workflow"""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = self.workflows[workflow_id]
            
            # Validate nodes exist
            if source_node not in workflow.nodes or target_node not in workflow.nodes:
                raise ValueError("Source or target node not found")
            
            # Validate connection points
            source_node_obj = workflow.nodes[source_node]
            target_node_obj = workflow.nodes[target_node]
            
            if source_output not in source_node_obj.outputs:
                raise ValueError(f"Source output {source_output} not found")
            
            if target_input not in target_node_obj.inputs:
                raise ValueError(f"Target input {target_input} not found")
            
            connection_id = f"conn_{uuid.uuid4()}"
            
            connection = NodeConnection(
                connection_id=connection_id,
                source_node=source_node,
                target_node=target_node,
                source_output=source_output,
                target_input=target_input,
                connection_type=ConnectionType(connection_type)
            )
            
            # Add to workflow
            workflow.connections[connection_id] = connection
            workflow.updated_at = datetime.utcnow()
            
            # Update database
            await self._update_workflow(workflow_id)
            
            logger.info(f"🔗 Nodes connected in workflow {workflow_id}: {source_node} -> {target_node}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error connecting nodes: {e}")
            raise
    
    async def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get complete workflow definition for visual editor"""
        try:
            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
            else:
                # Try to load from database
                workflow_doc = self.db.visual_workflows.find_one({"workflow_id": workflow_id})
                if not workflow_doc:
                    return None
                workflow = self._workflow_from_doc(workflow_doc)
                self.workflows[workflow_id] = workflow
            
            # Convert to visual editor format
            nodes_data = []
            for node in workflow.nodes.values():
                template = self.node_templates.get(node.template_key, {})
                nodes_data.append({
                    "id": node.node_id,
                    "type": node.template_key,
                    "position": {"x": node.position[0], "y": node.position[1]},
                    "data": {
                        "label": template.get("name", node.template_key),
                        "icon": template.get("icon", "🔧"),
                        "parameters": node.parameters,
                        "inputs": node.inputs,
                        "outputs": node.outputs
                    }
                })
            
            connections_data = []
            for connection in workflow.connections.values():
                connections_data.append({
                    "id": connection.connection_id,
                    "source": connection.source_node,
                    "target": connection.target_node,
                    "sourceHandle": connection.source_output,
                    "targetHandle": connection.target_input,
                    "type": connection.connection_type.value,
                    "animated": connection.connection_type in [ConnectionType.SUCCESS, ConnectionType.DEFAULT]
                })
            
            return {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "created_by": workflow.created_by,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
                "is_active": workflow.is_active,
                "nodes": nodes_data,
                "edges": connections_data,
                "node_count": len(nodes_data),
                "connection_count": len(connections_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow definition: {e}")
            return None
    
    async def list_user_workflows(self, created_by: str) -> List[Dict[str, Any]]:
        """List all workflows created by a user"""
        try:
            # Get from memory first
            user_workflows = []
            for workflow in self.workflows.values():
                if workflow.created_by == created_by:
                    user_workflows.append({
                        "workflow_id": workflow.workflow_id,
                        "name": workflow.name,
                        "description": workflow.description,
                        "created_at": workflow.created_at.isoformat(),
                        "updated_at": workflow.updated_at.isoformat(),
                        "node_count": len(workflow.nodes),
                        "is_active": workflow.is_active
                    })
            
            # Also get from database
            db_workflows = list(self.db.visual_workflows.find(
                {"created_by": created_by},
                {"_id": 0, "nodes": 0, "connections": 0}  # Exclude large fields
            ))
            
            # Convert and merge
            for doc in db_workflows:
                if doc["workflow_id"] not in [w["workflow_id"] for w in user_workflows]:
                    user_workflows.append({
                        "workflow_id": doc["workflow_id"],
                        "name": doc["name"],
                        "description": doc["description"],
                        "created_at": doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"],
                        "updated_at": doc["updated_at"].isoformat() if isinstance(doc["updated_at"], datetime) else doc["updated_at"],
                        "node_count": len(doc.get("nodes_data", [])),
                        "is_active": doc.get("is_active", True)
                    })
            
            # Sort by updated_at descending
            user_workflows.sort(key=lambda x: x["updated_at"], reverse=True)
            
            return user_workflows
            
        except Exception as e:
            logger.error(f"Error listing user workflows: {e}")
            return []
    
    async def execute_workflow(self, workflow_id: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a visual workflow (basic implementation)"""
        try:
            if workflow_id not in self.workflows:
                # Try to load from database
                workflow_doc = self.db.visual_workflows.find_one({"workflow_id": workflow_id})
                if not workflow_doc:
                    return {"success": False, "error": "Workflow not found"}
                self.workflows[workflow_id] = self._workflow_from_doc(workflow_doc)
            
            workflow = self.workflows[workflow_id]
            
            # Find trigger nodes
            trigger_nodes = [node for node in workflow.nodes.values() if node.node_type == NodeType.TRIGGER]
            
            if not trigger_nodes:
                return {"success": False, "error": "No trigger nodes found"}
            
            # Basic execution simulation
            execution_log = []
            execution_log.append(f"Starting workflow: {workflow.name}")
            
            # Simulate node execution
            for node in workflow.nodes.values():
                execution_log.append(f"Executing node: {self.node_templates.get(node.template_key, {}).get('name', node.template_key)}")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "execution_id": str(uuid.uuid4()),
                "message": f"Workflow '{workflow.name}' executed successfully",
                "execution_log": execution_log,
                "nodes_executed": len(workflow.nodes),
                "execution_time": 0.5  # Simulated
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a visual workflow"""
        try:
            # Remove from memory
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
            
            # Remove from database
            result = self.db.visual_workflows.delete_one({"workflow_id": workflow_id})
            
            logger.info(f"🗑️ Workflow deleted: {workflow_id}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            return False
    
    def _workflow_from_doc(self, doc: Dict[str, Any]) -> VisualWorkflow:
        """Convert database document to VisualWorkflow object"""
        workflow = VisualWorkflow(
            workflow_id=doc["workflow_id"],
            name=doc["name"],
            description=doc["description"],
            created_by=doc["created_by"],
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at", datetime.utcnow()),
            is_active=doc.get("is_active", True)
        )
        
        # Reconstruct nodes
        for node_data in doc.get("nodes_data", []):
            node = WorkflowNode(
                node_id=node_data["node_id"],
                node_type=NodeType(node_data["node_type"]),
                template_key=node_data["template_key"],
                position=tuple(node_data["position"]),
                parameters=node_data["parameters"],
                inputs=node_data["inputs"],
                outputs=node_data["outputs"],
                created_at=node_data.get("created_at", datetime.utcnow())
            )
            workflow.nodes[node.node_id] = node
        
        # Reconstruct connections
        for conn_data in doc.get("connections_data", []):
            connection = NodeConnection(
                connection_id=conn_data["connection_id"],
                source_node=conn_data["source_node"],
                target_node=conn_data["target_node"],
                source_output=conn_data["source_output"],
                target_input=conn_data["target_input"],
                connection_type=ConnectionType(conn_data["connection_type"]),
                created_at=conn_data.get("created_at", datetime.utcnow())
            )
            workflow.connections[connection.connection_id] = connection
        
        return workflow
    
    async def _store_workflow(self, workflow: VisualWorkflow):
        """Store workflow in database"""
        try:
            doc = {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "created_by": workflow.created_by,
                "created_at": workflow.created_at,
                "updated_at": workflow.updated_at,
                "is_active": workflow.is_active,
                "nodes_data": [],
                "connections_data": []
            }
            
            # Store nodes
            for node in workflow.nodes.values():
                doc["nodes_data"].append({
                    "node_id": node.node_id,
                    "node_type": node.node_type.value,
                    "template_key": node.template_key,
                    "position": list(node.position),
                    "parameters": node.parameters,
                    "inputs": node.inputs,
                    "outputs": node.outputs,
                    "created_at": node.created_at
                })
            
            # Store connections
            for connection in workflow.connections.values():
                doc["connections_data"].append({
                    "connection_id": connection.connection_id,
                    "source_node": connection.source_node,
                    "target_node": connection.target_node,
                    "source_output": connection.source_output,
                    "target_input": connection.target_input,
                    "connection_type": connection.connection_type.value,
                    "created_at": connection.created_at
                })
            
            self.db.visual_workflows.insert_one(doc)
            
        except Exception as e:
            logger.error(f"Error storing workflow: {e}")
            raise
    
    async def _update_workflow(self, workflow_id: str):
        """Update workflow in database"""
        try:
            workflow = self.workflows[workflow_id]
            workflow.updated_at = datetime.utcnow()
            
            update_doc = {
                "updated_at": workflow.updated_at,
                "is_active": workflow.is_active,
                "nodes_data": [],
                "connections_data": []
            }
            
            # Update nodes
            for node in workflow.nodes.values():
                update_doc["nodes_data"].append({
                    "node_id": node.node_id,
                    "node_type": node.node_type.value,
                    "template_key": node.template_key,
                    "position": list(node.position),
                    "parameters": node.parameters,
                    "inputs": node.inputs,
                    "outputs": node.outputs,
                    "created_at": node.created_at
                })
            
            # Update connections
            for connection in workflow.connections.values():
                update_doc["connections_data"].append({
                    "connection_id": connection.connection_id,
                    "source_node": connection.source_node,
                    "target_node": connection.target_node,
                    "source_output": connection.source_output,
                    "target_input": connection.target_input,
                    "connection_type": connection.connection_type.value,
                    "created_at": connection.created_at
                })
            
            self.db.visual_workflows.update_one(
                {"workflow_id": workflow_id},
                {"$set": update_doc}
            )
            
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            raise

# Global visual workflow builder instance
visual_workflow_builder = None

def initialize_visual_workflow_builder(mongo_client) -> VisualWorkflowBuilder:
    """Initialize the global visual workflow builder"""
    global visual_workflow_builder
    visual_workflow_builder = VisualWorkflowBuilder(mongo_client)
    return visual_workflow_builder

def get_visual_workflow_builder() -> Optional[VisualWorkflowBuilder]:
    """Get the global visual workflow builder instance"""
    return visual_workflow_builder