"""
Enhanced API Endpoints for Native Chromium and Agentic Memory
Seamless integration with existing frontend without disrupting current functionality
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from .enhanced_native_chromium import get_enhanced_native_chromium
from .agentic_memory_system import get_agentic_memory_system

logger = logging.getLogger(__name__)

# Enhanced API Models
class NativeNavigationRequest(BaseModel):
    url: str
    session_id: str
    options: Optional[Dict[str, Any]] = {}

class NativeAutomationRequest(BaseModel):
    session_id: str
    automation_script: Dict[str, Any]

class ScreenshotRequest(BaseModel):
    session_id: str
    options: Optional[Dict[str, Any]] = {}

class ExtensionRequest(BaseModel):
    session_id: str
    action: str
    extension_data: Optional[Dict[str, Any]] = {}

class DevToolsRequest(BaseModel):
    session_id: str
    action: str
    options: Optional[Dict[str, Any]] = {}

class MemoryContextRequest(BaseModel):
    user_id: str
    current_context: Dict[str, Any]
    limit: Optional[int] = 10

class InteractionRecordRequest(BaseModel):
    user_id: str
    interaction_data: Dict[str, Any]

def setup_enhanced_endpoints(app, mongodb_client):
    """Setup enhanced API endpoints without disrupting existing functionality"""
    
    router = APIRouter(prefix="/api/enhanced", tags=["Enhanced Features"])
    
    # Native Chromium Endpoints
    @router.post("/native/session/initialize")
    async def initialize_native_session(request: Dict[str, Any]):
        """Initialize native Chromium session"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            session_id = request.get("session_id", "")
            config = request.get("config", {})
            
            result = await native_chromium.initialize_enhanced_session(session_id, config)
            return result
            
        except Exception as e:
            logger.error(f"Native session initialization error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/native/navigate")
    async def native_navigate(request: NativeNavigationRequest):
        """Enhanced native navigation"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.enhanced_navigation(
                request.session_id, 
                request.url, 
                request.options
            )
            return result
            
        except Exception as e:
            logger.error(f"Native navigation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/native/automate")
    async def native_automate(request: NativeAutomationRequest):
        """Enhanced native automation"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.enhanced_automation(
                request.session_id,
                request.automation_script
            )
            return result
            
        except Exception as e:
            logger.error(f"Native automation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/native/screenshot")
    async def native_screenshot(request: ScreenshotRequest):
        """Enhanced native screenshot"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.capture_enhanced_screenshot(
                request.session_id,
                request.options
            )
            return result
            
        except Exception as e:
            logger.error(f"Native screenshot error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/native/extensions")
    async def manage_native_extensions(request: ExtensionRequest):
        """Enhanced extension management"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.manage_extensions(
                request.session_id,
                request.action,
                request.extension_data
            )
            return result
            
        except Exception as e:
            logger.error(f"Extension management error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/native/devtools")
    async def native_devtools(request: DevToolsRequest):
        """Enhanced DevTools control"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.devtools_control(
                request.session_id,
                request.action,
                request.options
            )
            return result
            
        except Exception as e:
            logger.error(f"DevTools control error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/native/performance/{session_id}")
    async def get_native_performance(session_id: str):
        """Get native performance metrics"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.get_performance_metrics(session_id)
            return result
            
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.delete("/native/session/{session_id}")
    async def cleanup_native_session(session_id: str):
        """Cleanup native session"""
        try:
            native_chromium = get_enhanced_native_chromium()
            if not native_chromium:
                return {"success": False, "error": "Native Chromium not available"}
            
            result = await native_chromium.cleanup_session(session_id)
            return result
            
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Agentic Memory Endpoints
    @router.post("/memory/record")
    async def record_interaction(request: InteractionRecordRequest, background_tasks: BackgroundTasks):
        """Record interaction for agentic memory"""
        try:
            memory_system = get_agentic_memory_system()
            if not memory_system:
                return {"success": False, "error": "Agentic memory system not available"}
            
            # Record interaction in background to avoid blocking
            background_tasks.add_task(
                memory_system.record_interaction,
                request.user_id,
                request.interaction_data
            )
            
            return {
                "success": True,
                "message": "Interaction recorded for agentic learning"
            }
            
        except Exception as e:
            logger.error(f"Memory recording error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/memory/context")
    async def get_memory_context(request: MemoryContextRequest):
        """Get contextual memory for enhanced AI responses"""
        try:
            memory_system = get_agentic_memory_system()
            if not memory_system:
                return {"memories": [], "success": False, "error": "Memory system not available"}
            
            memories = await memory_system.get_contextual_memory(
                request.user_id,
                request.current_context,
                request.limit
            )
            
            return {
                "success": True,
                "memories": memories,
                "count": len(memories)
            }
            
        except Exception as e:
            logger.error(f"Memory context error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/memory/predictions/{user_id}")
    async def get_predictive_insights(user_id: str, request: Dict[str, Any]):
        """Get predictive insights from agentic memory"""
        try:
            memory_system = get_agentic_memory_system()
            if not memory_system:
                return {"predictions": [], "success": False, "error": "Memory system not available"}
            
            predictions = await memory_system.predict_user_needs(
                user_id,
                request.get("current_context", {})
            )
            
            # Convert predictions to serializable format
            serializable_predictions = []
            for pred in predictions:
                serializable_predictions.append({
                    "insight_id": pred.insight_id,
                    "insight_type": pred.insight_type,
                    "prediction": pred.prediction,
                    "confidence": pred.confidence,
                    "evidence": pred.evidence,
                    "actionable_suggestions": pred.actionable_suggestions,
                    "expiry_date": pred.expiry_date.isoformat(),
                    "generated_at": pred.generated_at.isoformat()
                })
            
            return {
                "success": True,
                "predictions": serializable_predictions,
                "count": len(serializable_predictions)
            }
            
        except Exception as e:
            logger.error(f"Predictive insights error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/memory/insights/{user_id}")
    async def get_user_insights(user_id: str):
        """Get comprehensive user insights and analytics"""
        try:
            memory_system = get_agentic_memory_system()
            if not memory_system:
                return {"insights": {}, "success": False, "error": "Memory system not available"}
            
            insights = await memory_system.get_user_insights(user_id)
            
            return {
                "success": True,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"User insights error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Detection endpoint for frontend to check enhanced capabilities
    @router.get("/capabilities")
    async def get_enhanced_capabilities():
        """Get available enhanced capabilities"""
        try:
            native_chromium = get_enhanced_native_chromium()
            memory_system = get_agentic_memory_system()
            
            capabilities = {
                "native_chromium": {
                    "available": native_chromium is not None,
                    "capabilities": native_chromium.enhanced_capabilities if native_chromium else {}
                },
                "agentic_memory": {
                    "available": memory_system is not None,
                    "features": [
                        "cross_session_learning",
                        "behavioral_analysis", 
                        "predictive_insights",
                        "contextual_memory",
                        "user_modeling"
                    ] if memory_system else []
                },
                "enhanced_features": {
                    "split_view_native": native_chromium is not None,
                    "advanced_automation": native_chromium is not None,
                    "performance_monitoring": native_chromium is not None,
                    "predictive_ai": memory_system is not None,
                    "behavioral_learning": memory_system is not None
                }
            }
            
            return {
                "success": True,
                "capabilities": capabilities,
                "version": "6.0.0-enhanced"
            }
            
        except Exception as e:
            logger.error(f"Capabilities check error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Integration endpoint for existing AI chat
    @router.post("/ai/enhanced-chat")
    async def enhanced_ai_chat(request: Dict[str, Any]):
        """Enhanced AI chat with agentic memory integration"""
        try:
            message = request.get("message", "")
            session_id = request.get("session_id", "")
            current_url = request.get("current_url", "")
            
            # Get contextual memory
            memory_system = get_agentic_memory_system()
            contextual_memories = []
            
            if memory_system and session_id:
                contextual_memories = await memory_system.get_contextual_memory(
                    session_id,
                    {
                        "message": message,
                        "current_url": current_url,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    limit=5
                )
            
            # Get predictive insights
            predictions = []
            if memory_system and session_id:
                predictions = await memory_system.predict_user_needs(
                    session_id,
                    {
                        "message": message,
                        "current_url": current_url
                    }
                )
            
            # Return enhanced context for AI processing
            return {
                "success": True,
                "enhanced_context": {
                    "contextual_memories": contextual_memories,
                    "predictions": [
                        {
                            "prediction": pred.prediction,
                            "confidence": pred.confidence,
                            "suggestions": pred.actionable_suggestions
                        }
                        for pred in predictions
                    ],
                    "memory_available": len(contextual_memories) > 0,
                    "learning_active": memory_system is not None
                },
                "message": "Enhanced context prepared for AI processing"
            }
            
        except Exception as e:
            logger.error(f"Enhanced AI chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Add the router to the main app
    app.include_router(router)
    
    logger.info("🚀 Enhanced API endpoints configured successfully")
    return router