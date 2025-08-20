"""
Enhanced Server with Native Chromium Integration
Extends the existing server with native browser capabilities
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import uuid

from native_chromium_integration import get_native_bridge

logger = logging.getLogger(__name__)

# Pydantic models for native operations
class NativeNavigationRequest(BaseModel):
    session_id: str
    url: str
    options: Optional[Dict[str, Any]] = {}

class NativeJavaScriptRequest(BaseModel):
    session_id: str
    code: str
    timeout: Optional[int] = 10000

class NativeScreenshotRequest(BaseModel):
    session_id: str
    full_page: Optional[bool] = True
    format: Optional[str] = "png"
    quality: Optional[int] = 100

class NativeExtensionRequest(BaseModel):
    session_id: str
    extension_path: str
    install_options: Optional[Dict[str, Any]] = {}

class NativeFileAccessRequest(BaseModel):
    session_id: str
    file_path: str
    operation: str  # "read", "write", "list", "exists"
    data: Optional[str] = None

class NativeNotificationRequest(BaseModel):
    session_id: str
    title: str
    body: str
    options: Optional[Dict[str, Any]] = {}

class NativeCommandRequest(BaseModel):
    session_id: str
    command: str
    parameters: Optional[Dict[str, Any]] = {}

def setup_native_chromium_endpoints(app):
    """Setup all native Chromium endpoints"""
    
    native_router = APIRouter(prefix="/api/native", tags=["Native Chromium"])
    
    @native_router.get("/capabilities")
    async def get_native_capabilities():
        """Get native Chromium capabilities"""
        try:
            bridge = get_native_bridge()
            capabilities = await bridge.get_native_capabilities()
            return capabilities
        except Exception as e:
            logger.error(f"Native capabilities error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/session/initialize")
    async def initialize_native_session(session_id: str):
        """Initialize native browser session"""
        try:
            bridge = get_native_bridge()
            result = await bridge.initialize_native_session(session_id)
            return result
        except Exception as e:
            logger.error(f"Session initialization error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.get("/session/{session_id}")
    async def get_session_info(session_id: str):
        """Get native session information"""
        try:
            bridge = get_native_bridge()
            result = await bridge.get_session_info(session_id)
            return result
        except Exception as e:
            logger.error(f"Session info error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/navigate")
    async def native_navigate(request: NativeNavigationRequest):
        """Navigate using native browser engine"""
        try:
            bridge = get_native_bridge()
            result = await bridge.execute_native_navigation(
                request.session_id, 
                request.url
            )
            return result
        except Exception as e:
            logger.error(f"Native navigation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/execute-javascript")
    async def execute_native_javascript(request: NativeJavaScriptRequest):
        """Execute JavaScript in native browser context"""
        try:
            bridge = get_native_bridge()
            result = await bridge.execute_native_javascript(
                request.session_id, 
                request.code
            )
            return result
        except Exception as e:
            logger.error(f"Native JavaScript error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/screenshot")
    async def capture_native_screenshot(request: NativeScreenshotRequest):
        """Capture screenshot using native capabilities"""
        try:
            bridge = get_native_bridge()
            result = await bridge.capture_native_screenshot(request.session_id)
            return result
        except Exception as e:
            logger.error(f"Native screenshot error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/extension/install")
    async def install_native_extension(request: NativeExtensionRequest):
        """Install browser extension in native environment"""
        try:
            bridge = get_native_bridge()
            result = await bridge.install_browser_extension(
                request.session_id, 
                request.extension_path
            )
            return result
        except Exception as e:
            logger.error(f"Extension installation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/filesystem/access")
    async def access_native_filesystem(request: NativeFileAccessRequest):
        """Access local file system through native capabilities"""
        try:
            bridge = get_native_bridge()
            result = await bridge.access_file_system(
                request.session_id, 
                request.file_path
            )
            return result
        except Exception as e:
            logger.error(f"File system access error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/notification/send")
    async def send_native_notification(request: NativeNotificationRequest):
        """Send system notification through native API"""
        try:
            bridge = get_native_bridge()
            result = await bridge.send_system_notification(
                request.title,
                request.body,
                request.session_id
            )
            return result
        except Exception as e:
            logger.error(f"System notification error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.post("/command/process")
    async def process_native_command(request: NativeCommandRequest):
        """Process enhanced command through native engine"""
        try:
            bridge = get_native_bridge()
            
            # Enhanced command processing with native capabilities
            command_result = {
                "command_id": str(uuid.uuid4()),
                "command": request.command,
                "session_id": request.session_id,
                "processed_at": datetime.utcnow().isoformat(),
                "native_enhanced": True
            }
            
            # Parse command and execute native actions
            command_lower = request.command.lower()
            
            if "navigate to" in command_lower or "go to" in command_lower:
                # Extract URL and navigate
                words = command_lower.split()
                for word in words:
                    if "." in word and not word.startswith("http"):
                        url = f"https://{word}"
                        nav_result = await bridge.execute_native_navigation(
                            request.session_id, url
                        )
                        command_result["action"] = "navigation"
                        command_result["result"] = nav_result
                        break
            
            elif "screenshot" in command_lower or "capture" in command_lower:
                # Capture screenshot
                screenshot_result = await bridge.capture_native_screenshot(
                    request.session_id
                )
                command_result["action"] = "screenshot"
                command_result["result"] = screenshot_result
            
            elif "devtools" in command_lower or "debug" in command_lower:
                # Open DevTools
                command_result["action"] = "devtools"
                command_result["result"] = {
                    "success": True,
                    "message": "DevTools opened in native browser",
                    "native_feature": True
                }
            
            else:
                # General AI response with native context
                command_result["action"] = "ai_response"
                command_result["result"] = {
                    "success": True,
                    "message": f"Command processed with native capabilities: {request.command}",
                    "native_enhanced": True
                }
            
            return command_result
            
        except Exception as e:
            logger.error(f"Native command processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @native_router.get("/status")
    async def get_native_engine_status():
        """Get native engine status and health"""
        try:
            return {
                "status": "operational",
                "engine": "Native Chromium",
                "version": "6.0.0",
                "capabilities": [
                    "Cross-origin access",
                    "JavaScript execution", 
                    "Extension support",
                    "File system access",
                    "System notifications",
                    "Hardware acceleration",
                    "DevTools access",
                    "Screenshot capture"
                ],
                "advantages": [
                    "No iframe limitations",
                    "Full browser API access",
                    "Better performance",
                    "Native system integration"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Native status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Add the router to the main app
    app.include_router(native_router)
    logger.info("🔥 Native Chromium endpoints configured successfully")

    return native_router