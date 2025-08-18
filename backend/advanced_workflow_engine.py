import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor

# Import database
from database import get_database

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowNodeType(Enum):
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    WEBHOOK = "webhook"
    AI_TASK = "ai_task"
    INTEGRATION = "integration"

@dataclass
class WorkflowNode:
    id: str
    type: WorkflowNodeType
    name: str
    description: str
    parameters: Dict[str, Any]
    position: Dict[str, int]  # x, y coordinates for visual builder
    connections: List[str]  # Connected node IDs
    conditions: Optional[Dict[str, Any]] = None
    retry_settings: Optional[Dict[str, Any]] = None
    timeout: int = 300  # 5 minutes default

@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    category: str
    nodes: List[WorkflowNode]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_public: bool = False
    tags: List[str] = None

class WorkflowInstance:
    def __init__(self, instance_id: str, template_id: str, user_session: str, parameters: Dict[str, Any]):
        self.instance_id = instance_id
        self.template_id = template_id
        self.user_session = user_session
        self.parameters = parameters
        self.status = WorkflowStatus.DRAFT
        self.current_nodes = []
        self.completed_nodes = []
        self.failed_nodes = []
        self.results = {}
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.execution_context = {}

class AdvancedWorkflowEngine:
    def __init__(self):
        self.db = get_database()
        self.templates_collection = self.db.workflow_templates
        self.instances_collection = self.db.workflow_instances
        self.executions_collection = self.db.workflow_executions
        
        # Runtime management
        self.active_instances: Dict[str, WorkflowInstance] = {}
        self.execution_queue = asyncio.Queue()
        self.max_concurrent_workflows = 10
        self.running_workflows = set()
        
        # Visual builder components
        self.node_templates = self._initialize_node_templates()
        self.visual_components = self._initialize_visual_components()
        
        # Background processor
        self._background_processor_task = None
        
        # Performance tracking
        self.execution_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "avg_execution_time": 0,
            "node_performance": {}
        }
    
    def start_background_processor(self):
        """Start background workflow processor"""
        if self._background_processor_task is None:
            try:
                self._background_processor_task = asyncio.create_task(self._background_workflow_processor())
            except RuntimeError:
                pass  # No event loop running yet
    
    async def _background_workflow_processor(self):
        """Process workflows in background"""
        while True:
            try:
                await asyncio.sleep(3)
                
                # Get ready workflows
                ready_workflows = [
                    instance for instance in self.active_instances.values()
                    if instance.status == WorkflowStatus.ACTIVE 
                    and instance.instance_id not in self.running_workflows
                ]
                
                # Execute workflows up to concurrent limit
                for workflow in ready_workflows[:self.max_concurrent_workflows - len(self.running_workflows)]:
                    if len(self.running_workflows) < self.max_concurrent_workflows:
                        asyncio.create_task(self._execute_workflow_instance(workflow.instance_id))
                        
            except Exception as e:
                logger.error(f"Background workflow processor error: {e}")
    
    def _initialize_node_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pre-built node templates"""
        return {
            "web_navigation": {
                "type": WorkflowNodeType.ACTION,
                "name": "Navigate to URL",
                "description": "Navigate to a specific URL",
                "parameters": {
                    "url": {"type": "string", "required": True},
                    "wait_for_load": {"type": "boolean", "default": True},
                    "timeout": {"type": "number", "default": 30}
                },
                "icon": "🌐",
                "category": "Browser"
            },
            "form_fill": {
                "type": WorkflowNodeType.ACTION,
                "name": "Fill Form",
                "description": "Fill out a form on the current page",
                "parameters": {
                    "form_fields": {"type": "object", "required": True},
                    "submit_form": {"type": "boolean", "default": True}
                },
                "icon": "📝",
                "category": "Browser"
            },
            "data_extraction": {
                "type": WorkflowNodeType.ACTION,
                "name": "Extract Data",
                "description": "Extract data from the current page",
                "parameters": {
                    "selectors": {"type": "array", "required": True},
                    "output_format": {"type": "string", "default": "json"}
                },
                "icon": "📊",
                "category": "Data"
            },
            "ai_analysis": {
                "type": WorkflowNodeType.AI_TASK,
                "name": "AI Analysis",
                "description": "Analyze content using AI",
                "parameters": {
                    "content": {"type": "string", "required": True},
                    "analysis_type": {"type": "string", "required": True},
                    "model": {"type": "string", "default": "groq"}
                },
                "icon": "🤖",
                "category": "AI"
            },
            "condition_check": {
                "type": WorkflowNodeType.CONDITION,
                "name": "Condition Check",
                "description": "Check condition and branch workflow",
                "parameters": {
                    "condition": {"type": "string", "required": True},
                    "true_path": {"type": "array", "required": True},
                    "false_path": {"type": "array", "required": True}
                },
                "icon": "🔀",
                "category": "Logic"
            },
            "loop_iteration": {
                "type": WorkflowNodeType.LOOP,
                "name": "Loop",
                "description": "Repeat actions for a set of items",
                "parameters": {
                    "items": {"type": "array", "required": True},
                    "loop_body": {"type": "array", "required": True},
                    "max_iterations": {"type": "number", "default": 100}
                },
                "icon": "🔄",
                "category": "Logic"
            },
            "integration_action": {
                "type": WorkflowNodeType.INTEGRATION,
                "name": "Integration Action",
                "description": "Execute action via third-party integration",
                "parameters": {
                    "integration_id": {"type": "string", "required": True},
                    "action": {"type": "string", "required": True},
                    "action_parameters": {"type": "object", "required": True}
                },
                "icon": "🔗",
                "category": "Integration"
            },
            "webhook_trigger": {
                "type": WorkflowNodeType.WEBHOOK,
                "name": "Webhook",
                "description": "Send data to webhook endpoint",
                "parameters": {
                    "url": {"type": "string", "required": True},
                    "method": {"type": "string", "default": "POST"},
                    "headers": {"type": "object", "default": {}},
                    "payload": {"type": "object", "required": True}
                },
                "icon": "📡",
                "category": "Integration"
            }
        }
    
    def _initialize_visual_components(self) -> Dict[str, Any]:
        """Initialize visual builder components"""
        return {
            "node_styles": {
                "action": {"color": "#4CAF50", "icon": "⚡"},
                "condition": {"color": "#FF9800", "icon": "🔀"},
                "loop": {"color": "#2196F3", "icon": "🔄"},
                "parallel": {"color": "#9C27B0", "icon": "⚡"},
                "webhook": {"color": "#607D8B", "icon": "📡"},
                "ai_task": {"color": "#E91E63", "icon": "🤖"},
                "integration": {"color": "#009688", "icon": "🔗"}
            },
            "connection_styles": {
                "success": {"color": "#4CAF50", "style": "solid"},
                "error": {"color": "#F44336", "style": "dashed"},
                "condition_true": {"color": "#2196F3", "style": "solid"},
                "condition_false": {"color": "#FF5722", "style": "solid"}
            },
            "grid_settings": {
                "snap_to_grid": True,
                "grid_size": 20,
                "show_grid": True
            }
        }
    
    async def create_workflow_template(self, template_data: Dict[str, Any], user_session: str) -> str:
        """Create a new workflow template with visual builder support"""
        
        template_id = str(uuid.uuid4())
        
        # Parse nodes from template data
        nodes = []
        if "nodes" in template_data:
            for node_data in template_data["nodes"]:
                node = WorkflowNode(
                    id=node_data.get("id", str(uuid.uuid4())),
                    type=WorkflowNodeType(node_data.get("type", "action")),
                    name=node_data.get("name", ""),
                    description=node_data.get("description", ""),
                    parameters=node_data.get("parameters", {}),
                    position=node_data.get("position", {"x": 0, "y": 0}),
                    connections=node_data.get("connections", []),
                    conditions=node_data.get("conditions"),
                    retry_settings=node_data.get("retry_settings"),
                    timeout=node_data.get("timeout", 300)
                )
                nodes.append(node)
        
        # Create template
        template = WorkflowTemplate(
            id=template_id,
            name=template_data.get("name", "Untitled Workflow"),
            description=template_data.get("description", ""),
            category=template_data.get("category", "general"),
            nodes=nodes,
            metadata={
                "created_by": user_session,
                "version": "1.0",
                "visual_layout": template_data.get("visual_layout", {}),
                "estimated_duration": self._estimate_workflow_duration(nodes),
                "complexity": self._calculate_workflow_complexity(nodes)
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_public=template_data.get("is_public", False),
            tags=template_data.get("tags", [])
        )
        
        # Store in database
        template_doc = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "nodes": [asdict(node) for node in template.nodes],
            "metadata": template.metadata,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
            "is_public": template.is_public,
            "tags": template.tags
        }
        
        self.templates_collection.insert_one(template_doc)
        
        logger.info(f"Created workflow template {template_id}: {template.name}")
        return template_id
    
    async def create_workflow_instance(self, template_id: str, user_session: str, parameters: Dict[str, Any]) -> str:
        """Create workflow instance from template"""
        
        # Get template
        template_doc = self.templates_collection.find_one({"id": template_id})
        if not template_doc:
            raise ValueError(f"Template {template_id} not found")
        
        # Create instance
        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            instance_id=instance_id,
            template_id=template_id,
            user_session=user_session,
            parameters=parameters
        )
        
        # Store instance
        self.active_instances[instance_id] = instance
        
        # Store in database
        instance_doc = {
            "instance_id": instance.instance_id,
            "template_id": instance.template_id,
            "user_session": instance.user_session,
            "parameters": instance.parameters,
            "status": instance.status.value,
            "created_at": instance.created_at,
            "results": instance.results
        }
        
        self.instances_collection.insert_one(instance_doc)
        
        logger.info(f"Created workflow instance {instance_id} from template {template_id}")
        return instance_id
    
    async def start_workflow_instance(self, instance_id: str) -> bool:
        """Start executing a workflow instance"""
        
        if instance_id not in self.active_instances:
            return False
        
        instance = self.active_instances[instance_id]
        instance.status = WorkflowStatus.ACTIVE
        instance.started_at = datetime.utcnow()
        
        # Update database
        self.instances_collection.update_one(
            {"instance_id": instance_id},
            {"$set": {
                "status": instance.status.value,
                "started_at": instance.started_at
            }}
        )
        
        logger.info(f"Started workflow instance {instance_id}")
        return True
    
    async def _execute_workflow_instance(self, instance_id: str) -> bool:
        """Execute workflow instance"""
        
        if instance_id not in self.active_instances:
            return False
        
        instance = self.active_instances[instance_id]
        self.running_workflows.add(instance_id)
        
        try:
            instance.status = WorkflowStatus.RUNNING
            
            # Get template
            template_doc = self.templates_collection.find_one({"id": instance.template_id})
            if not template_doc:
                raise Exception(f"Template {instance.template_id} not found")
            
            # Execute nodes
            success = await self._execute_workflow_nodes(instance, template_doc["nodes"])
            
            # Update final status
            if success:
                instance.status = WorkflowStatus.COMPLETED
                instance.completed_at = datetime.utcnow()
                self.execution_stats["successful_workflows"] += 1
            else:
                instance.status = WorkflowStatus.FAILED
                instance.completed_at = datetime.utcnow()
                self.execution_stats["failed_workflows"] += 1
            
            # Update database
            self.instances_collection.update_one(
                {"instance_id": instance_id},
                {"$set": {
                    "status": instance.status.value,
                    "completed_at": instance.completed_at,
                    "results": instance.results,
                    "completed_nodes": instance.completed_nodes,
                    "failed_nodes": instance.failed_nodes,
                    "error_message": instance.error_message
                }}
            )
            
            self.execution_stats["total_workflows"] += 1
            logger.info(f"Workflow instance {instance_id} completed with status: {instance.status.value}")
            return success
            
        except Exception as e:
            instance.status = WorkflowStatus.FAILED
            instance.error_message = str(e)
            instance.completed_at = datetime.utcnow()
            logger.error(f"Workflow instance {instance_id} failed: {e}")
            return False
        
        finally:
            self.running_workflows.discard(instance_id)
    
    async def _execute_workflow_nodes(self, instance: WorkflowInstance, node_docs: List[Dict]) -> bool:
        """Execute workflow nodes in proper order"""
        
        # Convert to WorkflowNode objects
        nodes = []
        for node_doc in node_docs:
            node = WorkflowNode(
                id=node_doc["id"],
                type=WorkflowNodeType(node_doc["type"]),
                name=node_doc["name"],
                description=node_doc["description"],
                parameters=node_doc["parameters"],
                position=node_doc["position"],
                connections=node_doc["connections"],
                conditions=node_doc.get("conditions"),
                retry_settings=node_doc.get("retry_settings"),
                timeout=node_doc.get("timeout", 300)
            )
            nodes.append(node)
        
        # Find entry nodes (nodes with no incoming connections)
        entry_nodes = self._find_entry_nodes(nodes)
        
        # Execute starting from entry nodes
        for entry_node in entry_nodes:
            success = await self._execute_node_chain(instance, entry_node, nodes)
            if not success:
                return False
        
        return True
    
    def _find_entry_nodes(self, nodes: List[WorkflowNode]) -> List[WorkflowNode]:
        """Find nodes that don't have incoming connections"""
        all_node_ids = {node.id for node in nodes}
        connected_node_ids = set()
        
        for node in nodes:
            connected_node_ids.update(node.connections)
        
        entry_node_ids = all_node_ids - connected_node_ids
        return [node for node in nodes if node.id in entry_node_ids]
    
    async def _execute_node_chain(self, instance: WorkflowInstance, node: WorkflowNode, all_nodes: List[WorkflowNode]) -> bool:
        """Execute a chain of connected nodes"""
        
        try:
            # Execute current node
            result = await self._execute_single_node(instance, node)
            
            if result["success"]:
                instance.completed_nodes.append(node.id)
                instance.results[node.id] = result["data"]
                
                # Execute connected nodes
                for connected_id in node.connections:
                    connected_node = next((n for n in all_nodes if n.id == connected_id), None)
                    if connected_node:
                        # Check conditions if applicable
                        if await self._should_execute_node(instance, connected_node, result):
                            success = await self._execute_node_chain(instance, connected_node, all_nodes)
                            if not success:
                                return False
                
                return True
            else:
                instance.failed_nodes.append(node.id)
                instance.error_message = result.get("error", "Node execution failed")
                return False
                
        except Exception as e:
            instance.failed_nodes.append(node.id)
            instance.error_message = str(e)
            logger.error(f"Node {node.id} execution failed: {e}")
            return False
    
    async def _execute_single_node(self, instance: WorkflowInstance, node: WorkflowNode) -> Dict[str, Any]:
        """Execute a single workflow node"""
        
        try:
            if node.type == WorkflowNodeType.ACTION:
                return await self._execute_action_node(instance, node)
            elif node.type == WorkflowNodeType.CONDITION:
                return await self._execute_condition_node(instance, node)
            elif node.type == WorkflowNodeType.LOOP:
                return await self._execute_loop_node(instance, node)
            elif node.type == WorkflowNodeType.AI_TASK:
                return await self._execute_ai_task_node(instance, node)
            elif node.type == WorkflowNodeType.INTEGRATION:
                return await self._execute_integration_node(instance, node)
            elif node.type == WorkflowNodeType.WEBHOOK:
                return await self._execute_webhook_node(instance, node)
            else:
                return {"success": False, "error": f"Unsupported node type: {node.type}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_action_node(self, instance: WorkflowInstance, node: WorkflowNode) -> Dict[str, Any]:
        """Execute action node"""
        # This would integrate with browser engine or other action systems
        await asyncio.sleep(1)  # Simulate work
        return {
            "success": True,
            "data": {
                "node_id": node.id,
                "action": node.name,
                "parameters": node.parameters,
                "execution_time": 1.0
            }
        }
    
    async def _execute_condition_node(self, instance: WorkflowInstance, node: WorkflowNode) -> Dict[str, Any]:
        """Execute condition node"""
        condition = node.parameters.get("condition", "true")
        # Simple condition evaluation - could be enhanced with expression parser
        result = eval(condition.replace("true", "True").replace("false", "False"))
        
        return {
            "success": True,
            "data": {
                "condition_result": result,
                "condition": condition
            }
        }
    
    async def _execute_ai_task_node(self, instance: WorkflowInstance, node: WorkflowNode) -> Dict[str, Any]:
        """Execute AI task node"""
        # This would integrate with AI manager
        return {
            "success": True,
            "data": {
                "ai_result": "AI task completed",
                "model_used": node.parameters.get("model", "groq"),
                "analysis_type": node.parameters.get("analysis_type", "general")
            }
        }
    
    async def _should_execute_node(self, instance: WorkflowInstance, node: WorkflowNode, previous_result: Dict[str, Any]) -> bool:
        """Determine if node should be executed based on conditions"""
        if not node.conditions:
            return True
        
        # Simple condition checking - could be enhanced
        if "requires_success" in node.conditions:
            return previous_result.get("success", False)
        
        return True
    
    def _estimate_workflow_duration(self, nodes: List[WorkflowNode]) -> int:
        """Estimate workflow execution duration in seconds"""
        total_duration = 0
        for node in nodes:
            total_duration += node.timeout
        return total_duration
    
    def _calculate_workflow_complexity(self, nodes: List[WorkflowNode]) -> str:
        """Calculate workflow complexity level"""
        complexity_score = len(nodes)
        
        # Add complexity for different node types
        for node in nodes:
            if node.type in [WorkflowNodeType.CONDITION, WorkflowNodeType.LOOP]:
                complexity_score += 2
            elif node.type == WorkflowNodeType.AI_TASK:
                complexity_score += 3
        
        if complexity_score < 5:
            return "simple"
        elif complexity_score < 15:
            return "medium"
        elif complexity_score < 30:
            return "complex"
        else:
            return "expert"
    
    # Public API methods
    
    async def get_workflow_templates(self, category: str = None, user_session: str = None) -> List[Dict[str, Any]]:
        """Get available workflow templates"""
        
        query = {}
        if category:
            query["category"] = category
        if user_session:
            query["$or"] = [
                {"is_public": True},
                {"metadata.created_by": user_session}
            ]
        else:
            query["is_public"] = True
        
        templates = list(self.templates_collection.find(query, {"_id": 0}))
        return templates
    
    async def get_workflow_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow instance status"""
        
        instance = self.active_instances.get(instance_id)
        if not instance:
            # Check database
            instance_doc = self.instances_collection.find_one({"instance_id": instance_id}, {"_id": 0})
            if instance_doc:
                return instance_doc
            return None
        
        return {
            "instance_id": instance.instance_id,
            "template_id": instance.template_id,
            "status": instance.status.value,
            "current_nodes": instance.current_nodes,
            "completed_nodes": instance.completed_nodes,
            "failed_nodes": instance.failed_nodes,
            "results": instance.results,
            "created_at": instance.created_at.isoformat(),
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
            "error_message": instance.error_message
        }
    
    async def get_node_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available node templates for visual builder"""
        return self.node_templates
    
    async def get_visual_components(self) -> Dict[str, Any]:
        """Get visual builder components configuration"""
        return self.visual_components

# Global advanced workflow engine instance
advanced_workflow_engine = AdvancedWorkflowEngine()

# Alias for backward compatibility
VisualWorkflowEngine = AdvancedWorkflowEngine