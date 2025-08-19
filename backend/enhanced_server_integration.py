# Enhanced Server Integration - All Critical Gaps Implementation
# Integrates Shadow Workspace, Visual Workflow Builder, Split View, Platform Integrations

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from pydantic import BaseModel

# Import all new systems
from shadow_workspace import (
    initialize_shadow_workspace, get_shadow_workspace, 
    ShadowWorkspace, TaskPriority
)
from visual_workflow_builder import (
    initialize_visual_workflow_builder, get_visual_workflow_builder,
    VisualWorkflowBuilder
)
from split_view_engine import (
    initialize_split_view_engine, get_split_view_engine,
    SplitViewEngine
)
from platform_integration_engine import (
    initialize_platform_integration_engine, get_platform_integration_engine,
    PlatformIntegrationEngine
)

logger = logging.getLogger(__name__)

# Enhanced Pydantic Models for new features
class ShadowTaskRequest(BaseModel):
    command: str
    user_session: str
    current_url: Optional[str] = None
    priority: str = "normal"
    background_mode: bool = True

class VisualWorkflowCreateRequest(BaseModel):
    name: str
    description: str
    created_by: str

class WorkflowNodeRequest(BaseModel):
    workflow_id: str
    template_key: str
    position_x: float
    position_y: float
    parameters: Optional[Dict[str, Any]] = None

class NodeConnectionRequest(BaseModel):
    workflow_id: str
    source_node: str
    target_node: str
    source_output: str
    target_input: str
    connection_type: str = "success"

class SplitViewCreateRequest(BaseModel):
    user_session: str
    layout: str = "horizontal"
    initial_urls: Optional[List[str]] = None

class SplitViewNavigateRequest(BaseModel):
    session_id: str
    pane_id: str
    url: str
    sync_all: bool = False

class PlatformConnectionRequest(BaseModel):
    user_session: str
    platform_id: str
    auth_data: Dict[str, Any]

class PlatformActionRequest(BaseModel):
    user_session: str
    platform_id: str
    capability_id: str
    parameters: Dict[str, Any]

class BatchActionRequest(BaseModel):
    user_session: str
    actions: List[Dict[str, Any]]

class EnhancedServerIntegration:
    """Enhanced server integration for all new capabilities"""
    
    def __init__(self, mongo_client):
        self.mongo_client = mongo_client
        
        # Initialize all systems
        self.shadow_workspace = initialize_shadow_workspace(mongo_client)
        self.workflow_builder = initialize_visual_workflow_builder(mongo_client)
        self.split_view_engine = initialize_split_view_engine(mongo_client)
        self.platform_engine = initialize_platform_integration_engine(mongo_client)
        
        # Start shadow workspace
        asyncio.create_task(self._start_enhanced_systems())
    
    async def _start_enhanced_systems(self):
        """Start all enhanced systems"""
        try:
            await self.shadow_workspace.start_shadow_workspace()
            logger.info("🚀 All enhanced systems started successfully")
        except Exception as e:
            logger.error(f"Error starting enhanced systems: {e}")
    
    # ==================== SHADOW WORKSPACE API METHODS ====================
    
    async def create_shadow_task(self, request: ShadowTaskRequest) -> Dict[str, Any]:
        """Create shadow task for background execution"""
        try:
            priority_map = {
                "low": TaskPriority.LOW,
                "normal": TaskPriority.NORMAL,
                "high": TaskPriority.HIGH,
                "urgent": TaskPriority.URGENT
            }
            
            task_id = await self.shadow_workspace.create_shadow_task(
                command=request.command,
                user_session=request.user_session,
                current_url=request.current_url,
                priority=priority_map.get(request.priority, TaskPriority.NORMAL),
                background_mode=request.background_mode
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "message": f"🌟 Shadow task created: {request.command}",
                "background_mode": request.background_mode,
                "estimated_completion": "2-5 minutes"
            }
            
        except Exception as e:
            logger.error(f"Shadow task creation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_shadow_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get shadow task status"""
        try:
            status = await self.shadow_workspace.get_shadow_task_status(task_id)
            if status:
                return {"success": True, "task_status": status}
            else:
                return {"success": False, "error": "Task not found"}
        except Exception as e:
            logger.error(f"Shadow task status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_active_shadow_tasks(self, user_session: str) -> Dict[str, Any]:
        """Get active shadow tasks for user"""
        try:
            tasks = await self.shadow_workspace.get_active_shadow_tasks(user_session)
            return {"success": True, "active_tasks": tasks}
        except Exception as e:
            logger.error(f"Active shadow tasks error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def control_shadow_task(self, task_id: str, action: str) -> Dict[str, Any]:
        """Control shadow task (pause/resume/cancel)"""
        try:
            if action == "pause":
                result = await self.shadow_workspace.pause_shadow_task(task_id)
            elif action == "resume":
                result = await self.shadow_workspace.resume_shadow_task(task_id)
            elif action == "cancel":
                result = await self.shadow_workspace.cancel_shadow_task(task_id)
            else:
                return {"success": False, "error": "Invalid action"}
            
            return {
                "success": result,
                "task_id": task_id,
                "action": action,
                "message": f"Task {action}{'d' if action.endswith('e') else 'ed'} successfully"
            }
        except Exception as e:
            logger.error(f"Shadow task control error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== VISUAL WORKFLOW BUILDER API METHODS ====================
    
    async def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow node templates"""
        try:
            templates = await self.workflow_builder.get_node_templates()
            return {"success": True, "templates": templates}
        except Exception as e:
            logger.error(f"Workflow templates error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_visual_workflow(self, request: VisualWorkflowCreateRequest) -> Dict[str, Any]:
        """Create new visual workflow"""
        try:
            workflow_id = await self.workflow_builder.create_visual_workflow(
                name=request.name,
                description=request.description,
                created_by=request.created_by
            )
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "name": request.name,
                "message": f"🎨 Visual workflow created: {request.name}"
            }
        except Exception as e:
            logger.error(f"Visual workflow creation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def add_workflow_node(self, request: WorkflowNodeRequest) -> Dict[str, Any]:
        """Add node to visual workflow"""
        try:
            node_id = await self.workflow_builder.add_node_to_workflow(
                workflow_id=request.workflow_id,
                template_key=request.template_key,
                position=(request.position_x, request.position_y),
                custom_parameters=request.parameters
            )
            
            return {
                "success": True,
                "node_id": node_id,
                "workflow_id": request.workflow_id,
                "message": f"➕ Node added to workflow"
            }
        except Exception as e:
            logger.error(f"Workflow node addition error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def connect_workflow_nodes(self, request: NodeConnectionRequest) -> Dict[str, Any]:
        """Connect nodes in visual workflow"""
        try:
            connection_id = await self.workflow_builder.connect_nodes(
                workflow_id=request.workflow_id,
                source_node=request.source_node,
                target_node=request.target_node,
                source_output=request.source_output,
                target_input=request.target_input,
                connection_type=request.connection_type
            )
            
            return {
                "success": True,
                "connection_id": connection_id,
                "message": "🔗 Nodes connected successfully"
            }
        except Exception as e:
            logger.error(f"Node connection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_workflow_definition(self, workflow_id: str) -> Dict[str, Any]:
        """Get complete workflow definition"""
        try:
            workflow = await self.workflow_builder.get_workflow_definition(workflow_id)
            if workflow:
                return {"success": True, "workflow": workflow}
            else:
                return {"success": False, "error": "Workflow not found"}
        except Exception as e:
            logger.error(f"Workflow definition error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def list_user_workflows(self, created_by: str) -> Dict[str, Any]:
        """List user's workflows"""
        try:
            workflows = await self.workflow_builder.list_user_workflows(created_by)
            return {"success": True, "workflows": workflows}
        except Exception as e:
            logger.error(f"User workflows error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== SPLIT VIEW ENGINE API METHODS ====================
    
    async def create_split_view_session(self, request: SplitViewCreateRequest) -> Dict[str, Any]:
        """Create split view session"""
        try:
            session_id = await self.split_view_engine.create_split_view_session(
                user_session=request.user_session,
                layout=request.layout,
                initial_urls=request.initial_urls
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "layout": request.layout,
                "panes_count": len(request.initial_urls) if request.initial_urls else 0,
                "message": f"🔲 Split view session created ({request.layout})"
            }
        except Exception as e:
            logger.error(f"Split view creation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def add_split_pane(
        self, 
        session_id: str, 
        url: str, 
        position_row: Optional[int] = None,
        position_col: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add pane to split view"""
        try:
            position = (position_row, position_col) if position_row is not None and position_col is not None else None
            
            pane_id = await self.split_view_engine.add_pane_to_session(
                session_id=session_id,
                url=url,
                position=position
            )
            
            if pane_id:
                return {
                    "success": True,
                    "pane_id": pane_id,
                    "session_id": session_id,
                    "message": f"➕ Pane added to split view: {url}"
                }
            else:
                return {"success": False, "error": "Could not add pane (maximum reached?)"}
        except Exception as e:
            logger.error(f"Split pane addition error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def navigate_split_pane(self, request: SplitViewNavigateRequest) -> Dict[str, Any]:
        """Navigate split view pane"""
        try:
            result = await self.split_view_engine.navigate_pane(
                session_id=request.session_id,
                pane_id=request.pane_id,
                url=request.url,
                sync_all=request.sync_all
            )
            
            return {
                "success": result,
                "session_id": request.session_id,
                "pane_id": request.pane_id,
                "url": request.url,
                "synchronized": request.sync_all,
                "message": f"🌐 Pane navigated to {request.url}"
            }
        except Exception as e:
            logger.error(f"Split pane navigation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_split_view_state(self, session_id: str) -> Dict[str, Any]:
        """Get split view session state"""
        try:
            state = await self.split_view_engine.get_session_state(session_id)
            if state:
                return {"success": True, "split_view": state}
            else:
                return {"success": False, "error": "Session not found"}
        except Exception as e:
            logger.error(f"Split view state error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def change_split_layout(self, session_id: str, layout: str) -> Dict[str, Any]:
        """Change split view layout"""
        try:
            result = await self.split_view_engine.change_layout(session_id, layout)
            return {
                "success": result,
                "session_id": session_id,
                "new_layout": layout,
                "message": f"🔄 Layout changed to {layout}"
            }
        except Exception as e:
            logger.error(f"Split layout change error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # ==================== PLATFORM INTEGRATIONS API METHODS ====================
    
    async def get_available_integrations(self, integration_type: Optional[str] = None) -> Dict[str, Any]:
        """Get available platform integrations"""
        try:
            integrations = await self.platform_engine.get_available_integrations(integration_type)
            return {
                "success": True,
                "integrations": integrations,
                "total_platforms": len(integrations)
            }
        except Exception as e:
            logger.error(f"Available integrations error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def connect_platform(self, request: PlatformConnectionRequest) -> Dict[str, Any]:
        """Connect user to platform"""
        try:
            connection_id = await self.platform_engine.connect_user_to_platform(
                user_session=request.user_session,
                platform_id=request.platform_id,
                auth_data=request.auth_data
            )
            
            return {
                "success": True,
                "connection_id": connection_id,
                "platform_id": request.platform_id,
                "message": f"🔗 Connected to {request.platform_id}"
            }
        except Exception as e:
            logger.error(f"Platform connection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def execute_platform_action(self, request: PlatformActionRequest) -> Dict[str, Any]:
        """Execute action on connected platform"""
        try:
            result = await self.platform_engine.execute_platform_action(
                user_session=request.user_session,
                platform_id=request.platform_id,
                capability_id=request.capability_id,
                parameters=request.parameters
            )
            
            return result
        except Exception as e:
            logger.error(f"Platform action error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def batch_execute_platform_actions(self, request: BatchActionRequest) -> Dict[str, Any]:
        """Execute multiple platform actions (Fellou.ai-style)"""
        try:
            results = await self.platform_engine.batch_execute_actions(
                user_session=request.user_session,
                actions=request.actions
            )
            
            return {
                "success": True,
                "batch_results": results,
                "total_actions": len(results),
                "message": f"🚀 Executed {len(results)} platform actions"
            }
        except Exception as e:
            logger.error(f"Batch platform actions error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_user_integrations(self, user_session: str) -> Dict[str, Any]:
        """Get user's connected integrations"""
        try:
            integrations = await self.platform_engine.get_user_integrations(user_session)
            return {
                "success": True,
                "connected_integrations": integrations,
                "total_connected": len(integrations)
            }
        except Exception as e:
            logger.error(f"User integrations error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def disconnect_platform(self, user_session: str, platform_id: str) -> Dict[str, Any]:
        """Disconnect user from platform"""
        try:
            result = await self.platform_engine.disconnect_user_from_platform(
                user_session=user_session,
                platform_id=platform_id
            )
            
            return {
                "success": result,
                "platform_id": platform_id,
                "message": f"🔌 Disconnected from {platform_id}" if result else "Disconnection failed"
            }
        except Exception as e:
            logger.error(f"Platform disconnection error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Global enhanced server integration instance
enhanced_server_integration: Optional[EnhancedServerIntegration] = None

def initialize_enhanced_server_integration(mongo_client) -> EnhancedServerIntegration:
    """Initialize the global enhanced server integration"""
    global enhanced_server_integration
    enhanced_server_integration = EnhancedServerIntegration(mongo_client)
    return enhanced_server_integration

def get_enhanced_server_integration() -> Optional[EnhancedServerIntegration]:
    """Get the global enhanced server integration instance"""
    return enhanced_server_integration