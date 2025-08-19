# Visual Workflow Builder - Drag & Drop Interface Backend
# Critical Gap #2: Implement Fellou.ai's Visual Workflow Builder

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pymongo import MongoClient

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
    CONDITIONAL = "conditional"

@dataclass
class WorkflowNode:
    """Visual workflow node (drag & drop component)"""
    node_id: str
    type: NodeType
    title: str
    description: str
    position: Tuple[float, float]
    parameters: Dict[str, Any]
    inputs: List[str]
    outputs: List[str]
    icon: str
    color: str

@dataclass
class WorkflowConnection:
    """Connection between workflow nodes"""
    connection_id: str
    source_node: str
    target_node: str
    source_output: str
    target_input: str
    connection_type: ConnectionType
    condition: Optional[str] = None

@dataclass
class VisualWorkflow:
    """Complete visual workflow definition"""
    workflow_id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    nodes: List[WorkflowNode]
    connections: List[WorkflowConnection]
    canvas_settings: Dict[str, Any]
    is_template: bool = False
    execution_count: int = 0

class VisualWorkflowBuilder:
    """Fellou.ai-style Visual Workflow Builder with drag & drop interface"""
    
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.aether_browser
        
        # Initialize node templates
        self.node_templates = self._initialize_node_templates()
        
    def _initialize_node_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize drag & drop node templates (Fellou.ai-style)"""
        return {
            # Trigger Nodes
            "url_trigger": {
                "type": "trigger",
                "title": "URL Trigger",
                "description": "Triggers when navigating to specific URL",
                "icon": "🌐",
                "color": "#22c55e",
                "parameters": {"url_pattern": "", "match_type": "exact"},
                "inputs": [],
                "outputs": ["url", "page_data"]
            },
            "time_trigger": {
                "type": "trigger", 
                "title": "Time Trigger",
                "description": "Triggers at scheduled time",
                "icon": "⏰",
                "color": "#22c55e",
                "parameters": {"schedule": "0 9 * * *", "timezone": "UTC"},
                "inputs": [],
                "outputs": ["timestamp"]
            },
            "page_load_trigger": {
                "type": "trigger",
                "title": "Page Load",
                "description": "Triggers when page loads",
                "icon": "📄",
                "color": "#22c55e", 
                "parameters": {"wait_for": "complete"},
                "inputs": [],
                "outputs": ["page_content", "page_title"]
            },
            
            # Action Nodes
            "extract_data": {
                "type": "action",
                "title": "Extract Data",
                "description": "Extract specific data from page",
                "icon": "📊",
                "color": "#3b82f6",
                "parameters": {"selector": "", "data_type": "text"},
                "inputs": ["page_data"],
                "outputs": ["extracted_data"]
            },
            "ai_analyze": {
                "type": "action",
                "title": "AI Analysis", 
                "description": "Analyze content with AI",
                "icon": "🤖",
                "color": "#3b82f6",
                "parameters": {"analysis_type": "summary", "model": "llama-3.3-70b"},
                "inputs": ["content"],
                "outputs": ["analysis_result"]
            },
            "web_scrape": {
                "type": "action",
                "title": "Web Scrape",
                "description": "Scrape data from websites",
                "icon": "🕷️",
                "color": "#3b82f6",
                "parameters": {"urls": [], "selectors": {}},
                "inputs": ["url_list"],
                "outputs": ["scraped_data"]
            },
            "send_notification": {
                "type": "action",
                "title": "Send Notification",
                "description": "Send notification to user",
                "icon": "🔔",
                "color": "#3b82f6",
                "parameters": {"message": "", "channel": "browser"},
                "inputs": ["message_data"],
                "outputs": ["notification_sent"]
            },
            
            # Condition Nodes
            "data_filter": {
                "type": "condition",
                "title": "Data Filter",
                "description": "Filter data based on conditions",
                "icon": "🔍",
                "color": "#f59e0b",
                "parameters": {"condition": "", "operation": "contains"},
                "inputs": ["input_data"],
                "outputs": ["filtered_data", "rejected_data"]
            },
            "content_checker": {
                "type": "condition",
                "title": "Content Checker", 
                "description": "Check if content meets criteria",
                "icon": "✅",
                "color": "#f59e0b",
                "parameters": {"criteria": "", "threshold": 0.8},
                "inputs": ["content"],
                "outputs": ["passed", "failed"]
            },
            
            # Loop Nodes  
            "for_each": {
                "type": "loop",
                "title": "For Each",
                "description": "Iterate over collection",
                "icon": "🔄",
                "color": "#8b5cf6",
                "parameters": {"max_iterations": 100},
                "inputs": ["collection"],
                "outputs": ["item", "index", "complete"]
            },
            
            # Output Nodes
            "save_to_file": {
                "type": "output",
                "title": "Save to File",
                "description": "Save data to file",
                "icon": "💾",
                "color": "#ef4444",
                "parameters": {"filename": "", "format": "json"},
                "inputs": ["data_to_save"],
                "outputs": ["file_path"]
            },
            "generate_report": {
                "type": "output",
                "title": "Generate Report",
                "description": "Generate formatted report",
                "icon": "📋",
                "color": "#ef4444", 
                "parameters": {"template": "default", "format": "html"},
                "inputs": ["report_data"],
                "outputs": ["report_url"]
            },
            "send_to_api": {
                "type": "output",
                "title": "Send to API",
                "description": "Send data to external API",
                "icon": "🚀",
                "color": "#ef4444",
                "parameters": {"endpoint": "", "method": "POST"},
                "inputs": ["api_data"],
                "outputs": ["response"]
            }
        }
    
    async def get_node_templates(self) -> Dict[str, Any]:
        """Get available node templates for drag & drop interface"""
        return {
            "categories": {
                "triggers": {
                    "title": "Triggers",
                    "description": "Start your workflow",
                    "nodes": [k for k, v in self.node_templates.items() if v["type"] == "trigger"]
                },
                "actions": {
                    "title": "Actions", 
                    "description": "Perform operations",
                    "nodes": [k for k, v in self.node_templates.items() if v["type"] == "action"]
                },
                "conditions": {
                    "title": "Conditions",
                    "description": "Add logic and filters",
                    "nodes": [k for k, v in self.node_templates.items() if v["type"] == "condition"]
                },
                "loops": {
                    "title": "Loops",
                    "description": "Iterate and repeat",
                    "nodes": [k for k, v in self.node_templates.items() if v["type"] == "loop"]
                },
                "outputs": {
                    "title": "Outputs",
                    "description": "Save and export results",
                    "nodes": [k for k, v in self.node_templates.items() if v["type"] == "output"]
                }
            },
            "templates": self.node_templates
        }
    
    async def create_visual_workflow(
        self, 
        name: str, 
        description: str, 
        created_by: str,
        canvas_settings: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create new visual workflow"""
        
        workflow_id = str(uuid.uuid4())
        
        if not canvas_settings:
            canvas_settings = {
                "zoom": 1.0,
                "pan_x": 0,
                "pan_y": 0,
                "grid_enabled": True,
                "snap_to_grid": True
            }
        
        workflow = VisualWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            created_by=created_by,
            created_at=datetime.utcnow(),
            nodes=[],
            connections=[],
            canvas_settings=canvas_settings
        )
        
        await self._store_visual_workflow(workflow)
        
        logger.info(f"🎨 Visual workflow created: {workflow_id} - '{name}'")
        
        return workflow_id
    
    async def add_node_to_workflow(
        self, 
        workflow_id: str, 
        template_key: str, 
        position: Tuple[float, float],
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add node to visual workflow (drag & drop)"""
        
        if template_key not in self.node_templates:
            raise ValueError(f"Unknown node template: {template_key}")
        
        template = self.node_templates[template_key]
        node_id = str(uuid.uuid4())
        
        # Merge custom parameters with template defaults
        parameters = template["parameters"].copy()
        if custom_parameters:
            parameters.update(custom_parameters)
        
        node = WorkflowNode(
            node_id=node_id,
            type=NodeType(template["type"]),
            title=template["title"],
            description=template["description"],
            position=position,
            parameters=parameters,
            inputs=template["inputs"].copy(),
            outputs=template["outputs"].copy(),
            icon=template["icon"],
            color=template["color"]
        )
        
        # Add node to workflow
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            workflow.nodes.append(node)
            await self._store_visual_workflow(workflow)
            
            logger.info(f"➕ Node added to workflow {workflow_id}: {template_key} at {position}")
            
            return node_id
        
        raise ValueError(f"Workflow not found: {workflow_id}")
    
    async def connect_nodes(
        self,
        workflow_id: str,
        source_node: str,
        target_node: str,
        source_output: str,
        target_input: str,
        connection_type: str = "success",
        condition: Optional[str] = None
    ) -> str:
        """Connect two nodes in visual workflow"""
        
        connection_id = str(uuid.uuid4())
        
        connection = WorkflowConnection(
            connection_id=connection_id,
            source_node=source_node,
            target_node=target_node,
            source_output=source_output,
            target_input=target_input,
            connection_type=ConnectionType(connection_type),
            condition=condition
        )
        
        # Add connection to workflow
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            workflow.connections.append(connection)
            await self._store_visual_workflow(workflow)
            
            logger.info(f"🔗 Nodes connected in workflow {workflow_id}: {source_node} → {target_node}")
            
            return connection_id
        
        raise ValueError(f"Workflow not found: {workflow_id}")
    
    async def update_node_position(
        self, 
        workflow_id: str, 
        node_id: str, 
        new_position: Tuple[float, float]
    ) -> bool:
        """Update node position (drag & drop)"""
        
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            for node in workflow.nodes:
                if node.node_id == node_id:
                    node.position = new_position
                    await self._store_visual_workflow(workflow)
                    return True
        
        return False
    
    async def update_node_parameters(
        self, 
        workflow_id: str, 
        node_id: str, 
        parameters: Dict[str, Any]
    ) -> bool:
        """Update node parameters"""
        
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            for node in workflow.nodes:
                if node.node_id == node_id:
                    node.parameters.update(parameters)
                    await self._store_visual_workflow(workflow)
                    return True
        
        return False
    
    async def delete_node(self, workflow_id: str, node_id: str) -> bool:
        """Delete node from workflow"""
        
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            # Remove node
            workflow.nodes = [n for n in workflow.nodes if n.node_id != node_id]
            
            # Remove associated connections
            workflow.connections = [
                c for c in workflow.connections 
                if c.source_node != node_id and c.target_node != node_id
            ]
            
            await self._store_visual_workflow(workflow)
            return True
        
        return False
    
    async def delete_connection(self, workflow_id: str, connection_id: str) -> bool:
        """Delete connection from workflow"""
        
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            workflow.connections = [
                c for c in workflow.connections if c.connection_id != connection_id
            ]
            await self._store_visual_workflow(workflow)
            return True
        
        return False
    
    async def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get complete workflow definition for frontend"""
        
        workflow = await self._get_visual_workflow(workflow_id)
        if workflow:
            return {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "created_by": workflow.created_by,
                "created_at": workflow.created_at.isoformat(),
                "canvas_settings": workflow.canvas_settings,
                "execution_count": workflow.execution_count,
                "nodes": [
                    {
                        "node_id": node.node_id,
                        "type": node.type.value,
                        "title": node.title,
                        "description": node.description,
                        "position": {"x": node.position[0], "y": node.position[1]},
                        "parameters": node.parameters,
                        "inputs": node.inputs,
                        "outputs": node.outputs,
                        "icon": node.icon,
                        "color": node.color
                    }
                    for node in workflow.nodes
                ],
                "connections": [
                    {
                        "connection_id": conn.connection_id,
                        "source_node": conn.source_node,
                        "target_node": conn.target_node,
                        "source_output": conn.source_output,
                        "target_input": conn.target_input,
                        "connection_type": conn.connection_type.value,
                        "condition": conn.condition
                    }
                    for conn in workflow.connections
                ]
            }
        
        return None
    
    async def list_user_workflows(self, created_by: str) -> List[Dict[str, Any]]:
        """List workflows created by user"""
        
        try:
            workflows = list(self.db.visual_workflows.find(
                {"created_by": created_by},
                {"_id": 0, "nodes": 0, "connections": 0}  # Exclude heavy data
            ).sort("created_at", -1))
            
            return workflows
        except Exception as e:
            logger.error(f"Error listing user workflows: {e}")
            return []
    
    async def duplicate_workflow(
        self, 
        workflow_id: str, 
        new_name: str, 
        created_by: str
    ) -> Optional[str]:
        """Duplicate existing workflow"""
        
        original = await self._get_visual_workflow(workflow_id)
        if original:
            new_workflow_id = str(uuid.uuid4())
            
            # Create duplicate with new IDs
            duplicate = VisualWorkflow(
                workflow_id=new_workflow_id,
                name=new_name,
                description=f"Copy of {original.description}",
                created_by=created_by,
                created_at=datetime.utcnow(),
                nodes=original.nodes.copy(),  # Deep copy needed
                connections=original.connections.copy(),  # Deep copy needed
                canvas_settings=original.canvas_settings.copy()
            )
            
            # Generate new node IDs and update connections
            old_to_new_nodes = {}
            for node in duplicate.nodes:
                old_id = node.node_id
                node.node_id = str(uuid.uuid4())
                old_to_new_nodes[old_id] = node.node_id
            
            # Update connection references
            for conn in duplicate.connections:
                conn.connection_id = str(uuid.uuid4())
                conn.source_node = old_to_new_nodes.get(conn.source_node, conn.source_node)
                conn.target_node = old_to_new_nodes.get(conn.target_node, conn.target_node)
            
            await self._store_visual_workflow(duplicate)
            
            logger.info(f"📋 Workflow duplicated: {workflow_id} → {new_workflow_id}")
            
            return new_workflow_id
        
        return None
    
    async def convert_to_executable(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Convert visual workflow to executable format"""
        
        workflow = await self._get_visual_workflow(workflow_id)
        if not workflow:
            return None
        
        # Build execution graph
        execution_graph = {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "execution_order": [],
            "node_configs": {},
            "connections": {}
        }
        
        # Analyze workflow structure
        trigger_nodes = [n for n in workflow.nodes if n.type == NodeType.TRIGGER]
        if not trigger_nodes:
            return None
        
        # Build execution order (topological sort)
        visited = set()
        execution_order = []
        
        def visit_node(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            # Add to execution order
            execution_order.append(node_id)
            
            # Visit connected nodes
            for conn in workflow.connections:
                if conn.source_node == node_id:
                    visit_node(conn.target_node)
        
        # Start from trigger nodes
        for trigger in trigger_nodes:
            visit_node(trigger.node_id)
        
        execution_graph["execution_order"] = execution_order
        
        # Build node configurations
        for node in workflow.nodes:
            execution_graph["node_configs"][node.node_id] = {
                "type": node.type.value,
                "title": node.title,
                "parameters": node.parameters,
                "inputs": node.inputs,
                "outputs": node.outputs
            }
        
        # Build connection map
        for conn in workflow.connections:
            if conn.source_node not in execution_graph["connections"]:
                execution_graph["connections"][conn.source_node] = []
            
            execution_graph["connections"][conn.source_node].append({
                "target": conn.target_node,
                "output": conn.source_output,
                "input": conn.target_input,
                "type": conn.connection_type.value,
                "condition": conn.condition
            })
        
        return execution_graph
    
    async def _get_visual_workflow(self, workflow_id: str) -> Optional[VisualWorkflow]:
        """Get visual workflow from database"""
        try:
            data = self.db.visual_workflows.find_one({"workflow_id": workflow_id}, {"_id": 0})
            if data:
                # Reconstruct objects
                data["nodes"] = [WorkflowNode(**node_data) for node_data in data["nodes"]]
                data["connections"] = [WorkflowConnection(**conn_data) for conn_data in data["connections"]]
                data["created_at"] = data["created_at"] 
                
                return VisualWorkflow(**data)
            return None
        except Exception as e:
            logger.error(f"Error getting visual workflow: {e}")
            return None
    
    async def _store_visual_workflow(self, workflow: VisualWorkflow):
        """Store visual workflow in database"""
        try:
            workflow_dict = asdict(workflow)
            workflow_dict["nodes"] = [asdict(node) for node in workflow.nodes]
            workflow_dict["connections"] = [asdict(conn) for conn in workflow.connections]
            
            # Convert enums to strings
            for node_dict in workflow_dict["nodes"]:
                node_dict["type"] = node_dict["type"].value if isinstance(node_dict["type"], NodeType) else node_dict["type"]
            
            for conn_dict in workflow_dict["connections"]:
                conn_dict["connection_type"] = conn_dict["connection_type"].value if isinstance(conn_dict["connection_type"], ConnectionType) else conn_dict["connection_type"]
            
            self.db.visual_workflows.update_one(
                {"workflow_id": workflow.workflow_id},
                {"$set": workflow_dict},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing visual workflow: {e}")

# Global visual workflow builder instance
visual_workflow_builder: Optional[VisualWorkflowBuilder] = None

def initialize_visual_workflow_builder(mongo_client: MongoClient) -> VisualWorkflowBuilder:
    """Initialize the global visual workflow builder"""
    global visual_workflow_builder
    visual_workflow_builder = VisualWorkflowBuilder(mongo_client)
    return visual_workflow_builder

def get_visual_workflow_builder() -> Optional[VisualWorkflowBuilder]:
    """Get the global visual workflow builder instance"""
    return visual_workflow_builder