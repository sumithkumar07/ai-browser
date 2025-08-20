"""
Enhanced Server Native Chromium Endpoints
Provides API endpoints for native Chromium functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Native Chromium Request Models
class NativeNavigationRequest(BaseModel):
    url: str
    user_session: str
    options: Optional[Dict[str, Any]] = {}

class NativeScreenshotRequest(BaseModel):
    user_session: str
    format: Optional[str] = "png"
    quality: Optional[int] = 90
    full_page: Optional[bool] = False
    clip: Optional[Dict[str, int]] = None

class NativeExtensionRequest(BaseModel):
    user_session: str
    action: str  # "load", "unload", "list"
    extension_path: Optional[str] = ""
    extension_id: Optional[str] = ""

class NativeDevToolsRequest(BaseModel):
    user_session: str
    action: str  # "open", "close", "execute"
    command: Optional[str] = ""
    params: Optional[Dict[str, Any]] = {}

class NativeAutomationRequest(BaseModel):
    user_session: str
    actions: List[Dict[str, Any]]
    name: Optional[str] = "Native Automation"
    background: Optional[bool] = True

def setup_native_chromium_endpoints(app, enhanced_ai_intelligence=None, native_chromium=None):
    """Setup native Chromium API endpoints"""
    
    if not native_chromium or not native_chromium.get("native_available"):
        logger.warning("Native Chromium not available - endpoints will return fallback responses")
        native_bridge = None
    else:
        native_bridge = native_chromium.get("api_bridge")
    
    @app.post("/api/native/navigate")
    async def native_navigate(request: NativeNavigationRequest):
        """Navigate using native Chromium engine"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native Chromium engine not available",
                    "fallback_message": "Use enhanced iframe browser instead"
                }
            
            result = await native_bridge.navigate_native(request.user_session, request.url)
            return result
            
        except Exception as e:
            logger.error(f"Native navigation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/native/screenshot")
    async def native_screenshot(request: NativeScreenshotRequest):
        """Capture screenshot using native engine"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native screenshot not available",
                    "fallback_message": "Native Chromium engine required"
                }
            
            options = {
                "format": request.format,
                "quality": request.quality,
                "full_page": request.full_page,
                "clip": request.clip
            }
            
            result = await native_bridge.capture_native_screenshot(request.user_session, options)
            return result
            
        except Exception as e:
            logger.error(f"Native screenshot error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/native/extensions")
    async def native_extensions(request: NativeExtensionRequest):
        """Manage Chrome extensions in native engine"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native extension support not available",
                    "fallback_message": "Extensions require native Chromium engine"
                }
            
            extension_data = {
                "path": request.extension_path,
                "extension_id": request.extension_id
            }
            
            result = await native_bridge.manage_native_extensions(
                request.user_session, 
                request.action, 
                extension_data
            )
            return result
            
        except Exception as e:
            logger.error(f"Native extensions error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/native/devtools")
    async def native_devtools(request: NativeDevToolsRequest):
        """Control native Chrome DevTools"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native DevTools not available",
                    "fallback_message": "DevTools require native Chromium engine"
                }
            
            options = {
                "command": request.command,
                "params": request.params
            }
            
            result = await native_bridge.native_devtools_control(
                request.user_session,
                request.action,
                options
            )
            return result
            
        except Exception as e:
            logger.error(f"Native DevTools error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/native/automate")
    async def native_automation(request: NativeAutomationRequest):
        """Execute automation using native engine"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native automation not available",
                    "fallback_message": "Advanced automation requires native Chromium engine"
                }
            
            automation_data = {
                "actions": request.actions,
                "name": request.name,
                "background": request.background
            }
            
            result = await native_bridge.native_automation(request.user_session, automation_data)
            return result
            
        except Exception as e:
            logger.error(f"Native automation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/native/capabilities")
    async def native_capabilities():
        """Get native Chromium capabilities"""
        try:
            if not native_bridge:
                return {
                    "success": True,
                    "native_available": False,
                    "message": "Native Chromium engine not available",
                    "fallback_capabilities": [
                        "Enhanced iframe browser",
                        "Web-based automation",
                        "Standard screenshot capture"
                    ]
                }
            
            result = await native_bridge.get_native_capabilities()
            return result
            
        except Exception as e:
            logger.error(f"Native capabilities error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/native/session/{user_session}")
    async def native_session_state(user_session: str):
        """Get native session state"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native session tracking not available"
                }
            
            result = await native_bridge.get_session_state(user_session)
            return result
            
        except Exception as e:
            logger.error(f"Native session state error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/native/initialize/{user_session}")
    async def initialize_native_session(user_session: str):
        """Initialize a new native browsing session"""
        try:
            if not native_bridge:
                return {
                    "success": False,
                    "error": "Native session initialization not available",
                    "fallback_message": "Using enhanced web browser mode"
                }
            
            result = await native_bridge.initialize_native_session(user_session)
            return result
            
        except Exception as e:
            logger.error(f"Native session initialization error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Enhanced endpoints that work with both native and web modes
    @app.get("/api/browser/engine-status")
    async def browser_engine_status():
        """Get current browser engine status"""
        try:
            return {
                "success": True,
                "native_available": native_bridge is not None,
                "engine_type": "native_chromium" if native_bridge else "enhanced_iframe",
                "capabilities": {
                    "cross_origin": native_bridge is not None,
                    "file_access": native_bridge is not None,
                    "extensions": native_bridge is not None,
                    "devtools": native_bridge is not None,
                    "advanced_automation": native_bridge is not None,
                    "native_screenshot": native_bridge is not None
                },
                "version": "6.0.0",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Engine status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    logger.info("🔥 Native Chromium endpoints setup complete")
    return True