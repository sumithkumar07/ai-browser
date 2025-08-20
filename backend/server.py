"""
AETHER Native Chromium Browser API v6.0.0 - Complete Native Integration
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import uuid
from datetime import datetime
import logging
import asyncio
import json
import threading

# Import native components
from native_chromium_engine import NativeChromiumEngine, initialize_native_chromium_engine
from websocket_server import AETHERWebSocketServer, integrate_websocket_with_native_engine
# from enhanced_native_api import enhanced_router  # Temporarily disabled until components are ready

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AETHER Native Chromium Browser API",
    version="6.0.0",
    description="Complete Native Chromium Integration with Computer Use API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Database connection
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client.aether_browser

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None
    enable_automation: Optional[bool] = False
    background_execution: Optional[bool] = False

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

class NativeSessionRequest(BaseModel):
    user_session: str
    user_agent: Optional[str] = None

class NavigationRequest(BaseModel):
    session_id: str
    url: str
    timeout: Optional[int] = 30000

class JavaScriptRequest(BaseModel):
    session_id: str
    script: str
    args: Optional[List[Any]] = []

class ClickRequest(BaseModel):
    session_id: str
    selector: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    timeout: Optional[int] = 5000

class TypeRequest(BaseModel):
    session_id: str
    selector: str
    text: str
    clear: Optional[bool] = True

class ScreenshotRequest(BaseModel):
    session_id: str
    full_page: Optional[bool] = False
    quality: Optional[int] = 80

class SmartClickRequest(BaseModel):
    session_id: str
    description: str

class ExtractDataRequest(BaseModel):
    session_id: str
    data_type: Optional[str] = 'general'

class ContentRequest(BaseModel):
    session_id: str
    include_html: Optional[bool] = False

# Global state for native engine
native_engine: Optional[NativeChromiumEngine] = None
websocket_server: Optional[AETHERWebSocketServer] = None
native_engine_ready = False

@app.on_event("startup")
async def startup_event():
    """Initialize Native Chromium Engine and WebSocket server on startup"""
    global native_engine, websocket_server, native_engine_ready
    
    try:
        logger.info("🔥 AETHER Native Chromium Integration - Starting...")
        
        # Initialize Native Chromium Engine
        native_engine = await initialize_native_chromium_engine(client)
        
        if native_engine:
            native_engine_ready = True
            logger.info("✅ Native Chromium Engine initialized successfully")
            
            # Initialize WebSocket Server
            websocket_server = AETHERWebSocketServer(native_engine)
            
            # Integrate WebSocket with Native Engine
            integrate_websocket_with_native_engine(native_engine)
            
            # Start WebSocket server in background
            asyncio.create_task(websocket_server.start_server())
            
            logger.info("✅ WebSocket Server started successfully")
        else:
            logger.error("❌ Failed to initialize Native Chromium Engine")
            native_engine_ready = False
        
        logger.info("🚀 AETHER Backend startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        native_engine_ready = False

async def initialize_native_engine():
    """Initialize native engine in background - DEPRECATED"""
    # This method is now handled in startup_event
    pass

@app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Test database connection
        try:
            db.command("ping")
            db_status = "operational"
        except:
            db_status = "error"
        
        # Get native engine status
        engine_status = "not_initialized"
        session_count = 0
        websocket_stats = {}
        
        if native_engine:
            engine_status = "operational" if native_engine_ready else "initializing"
            session_count = len(native_engine.sessions)
        
        if websocket_server:
            websocket_stats = await websocket_server.get_connection_stats()
        
        return {
            "status": "operational",
            "version": "6.0.0",
            "database": db_status,
            "native_chromium_ready": native_engine_ready,
            "native_engine_status": engine_status,
            "active_sessions": session_count,
            "websocket_server": websocket_stats,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "AETHER Native Chromium Integration - Full Stack Operational",
            "capabilities": [
                "native_chromium_browsing",
                "websocket_real_time_communication",
                "computer_use_api",
                "ai_powered_automation",
                "performance_monitoring",
                "cross_origin_access",
                "file_system_access"
            ] if native_engine_ready else []
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/api/native/status")
async def native_status():
    """Get comprehensive native engine status"""
    try:
        status = {
            "native_available": native_engine_ready,
            "engine_type": "playwright_chromium",
            "version": "6.0.0"
        }
        
        if native_engine:
            status.update({
                "active_sessions": len(native_engine.sessions),
                "capabilities": [
                    "native_navigation",
                    "screenshot_capture", 
                    "javascript_execution",
                    "devtools_protocol",
                    "performance_monitoring",
                    "element_interaction",
                    "computer_use_api",
                    "smart_click",
                    "data_extraction"
                ],
                "browser_ready": native_engine.is_initialized,
                "sessions": {
                    session_id: {
                        "user_session": session.user_session,
                        "created_at": session.created_at.isoformat(),
                        "last_activity": session.last_activity.isoformat(),
                        "current_url": session.page.url if session.page else None
                    }
                    for session_id, session in native_engine.sessions.items()
                }
            })
        
        if websocket_server:
            ws_stats = await websocket_server.get_connection_stats()
            status["websocket_server"] = ws_stats
        
        return status
        
    except Exception as e:
        logger.error(f"Native status error: {str(e)}")
        return {
            "native_available": False,
            "error": str(e)
        }

# ============================================================================
# NATIVE BROWSER API ENDPOINTS - Complete Implementation
# ============================================================================

@app.post("/api/native/create-session")
async def create_native_session(request: NativeSessionRequest):
    """Create new native browser session"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.create_native_session(
            request.user_session,
            request.user_agent
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/navigate")
async def native_navigate(request: NavigationRequest):
    """Navigate using native browser"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.navigate_to_url(
            request.session_id,
            request.url,
            request.timeout
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Native navigation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/screenshot")
async def native_screenshot(request: ScreenshotRequest):
    """Capture screenshot using native browser"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.capture_screenshot(
            request.session_id,
            request.full_page,
            request.quality
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/execute-js")
async def native_execute_js(request: JavaScriptRequest):
    """Execute JavaScript using native browser"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.execute_javascript(
            request.session_id,
            request.script,
            request.args
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute JS error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/click")
async def native_click(request: ClickRequest):
    """Click element using native browser"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        if request.selector:
            # CSS selector click
            result = await native_engine.click_element(
                request.session_id,
                request.selector,
                request.timeout
            )
        elif request.x is not None and request.y is not None:
            # Coordinate click
            session = native_engine.sessions.get(request.session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            await session.page.mouse.click(request.x, request.y)
            result = {
                "success": True,
                "coordinates": {"x": request.x, "y": request.y}
            }
        else:
            raise HTTPException(status_code=400, detail="Either selector or coordinates required")
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Click error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/type")
async def native_type(request: TypeRequest):
    """Type text using native browser"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.type_text(
            request.session_id,
            request.selector,
            request.text,
            request.clear
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Type error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/get-content")
async def native_get_content(request: ContentRequest):
    """Get page content using native browser"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.get_page_content(
            request.session_id,
            request.include_html
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get content error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/native/performance/{session_id}")
async def native_performance(session_id: str):
    """Get performance metrics for native browser session"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.get_performance_metrics(session_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Performance metrics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/native/session/{session_id}")
async def close_native_session(session_id: str):
    """Close native browser session"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.close_session(session_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Close session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# COMPUTER USE API ENDPOINTS - AI-Powered Automation
# ============================================================================

@app.post("/api/native/automation/smart-click")
async def native_smart_click(request: SmartClickRequest):
    """AI-powered smart click using Computer Use API"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.smart_click(
            request.session_id,
            request.description
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart click error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/native/automation/extract-data")
async def native_extract_data(request: ExtractDataRequest):
    """Extract structured data from page using AI"""
    try:
        if not native_engine_ready or not native_engine:
            raise HTTPException(status_code=503, detail="Native engine not available")
        
        result = await native_engine.extract_page_data(
            request.session_id,
            request.data_type
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract data error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# WEBSOCKET ENDPOINT - Real-time Communication
# ============================================================================

@app.websocket("/ws/native/{session_id}")
async def websocket_native_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time native browser communication"""
    try:
        await websocket.accept()
        
        if not native_engine_ready or not native_engine:
            await websocket.close(code=4503, reason="Native engine not available")
            return
        
        # Handle WebSocket connection
        await native_engine.handle_websocket_connection(websocket, session_id)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass

# ============================================================================
# ENHANCED EXISTING ENDPOINTS - Backward Compatibility
# ============================================================================

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Enhanced browse page endpoint with native integration"""
    try:
        # Store in recent tabs
        tab_data = {
            "id": str(uuid.uuid4()),
            "url": session.url,
            "title": session.title or session.url,
            "timestamp": datetime.utcnow(),
            "is_secure": session.url.startswith('https://'),
            "domain": session.url.split('/')[2] if '://' in session.url else session.url,
            "engine_type": "native_chromium" if native_engine_ready else "fallback"
        }
        
        db.recent_tabs.insert_one(tab_data)
        
        return {
            "success": True,
            "url": session.url,
            "tab_id": tab_data["id"],
            "native_engine": native_engine_ready,
            "engine_type": tab_data["engine_type"]
        }
        
    except Exception as e:
        logger.error(f"Browse error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """Enhanced AI chat endpoint with native browser integration"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Enhanced AI response with native capabilities info
        native_info = ""
        if native_engine_ready and native_engine:
            active_sessions = len(native_engine.sessions)
            native_info = f" I'm running with Native Chromium Engine (v6.0.0) with {active_sessions} active browser sessions."
        
        ai_response = f"I'm AETHER AI with complete Native Chromium integration.{native_info} You said: {chat_data.message}"
        
        # Add automation capabilities if requested
        response_data = {
            "response": ai_response,
            "session_id": session_id,
            "native_engine_available": native_engine_ready
        }
        
        # Handle automation requests
        if chat_data.enable_automation and native_engine_ready:
            response_data["automation_capabilities"] = [
                "smart_click",
                "data_extraction", 
                "screenshot_capture",
                "javascript_execution",
                "performance_monitoring"
            ]
        
        # Store chat session
        chat_record = {
            "session_id": session_id,
            "user_message": chat_data.message,
            "ai_response": ai_response,
            "current_url": chat_data.current_url,
            "automation_enabled": chat_data.enable_automation,
            "background_execution": chat_data.background_execution,
            "native_engine_used": native_engine_ready,
            "timestamp": datetime.utcnow()
        }
        
        db.chat_sessions.insert_one(chat_record)
        
        return response_data
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-tabs")
async def get_recent_tabs():
    """Enhanced recent tabs with native engine info"""
    try:
        tabs = list(db.recent_tabs.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(8))
        
        # Add native engine status to each tab
        for tab in tabs:
            tab["native_engine_available"] = native_engine_ready
            if not tab.get("engine_type"):
                tab["engine_type"] = "native_chromium" if native_engine_ready else "fallback"
        
        return {"tabs": tabs, "native_engine_ready": native_engine_ready}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations():
    """Enhanced AI-powered browsing recommendations"""
    try:
        recommendations = [
            {
                "id": "1",
                "title": "🔥 Native Chromium Test",
                "description": "Test the new Native Chromium integration with full browser capabilities",
                "url": "https://www.google.com",
                "category": "native_features",
                "requires_native": True
            },
            {
                "id": "2", 
                "title": "🚀 GitHub Integration",
                "description": "Explore repositories with native browser automation",
                "url": "https://github.com",
                "category": "development",
                "requires_native": False
            },
            {
                "id": "3",
                "title": "🎯 Computer Use API Demo",
                "description": "Experience AI-powered smart clicking and automation",
                "url": "https://example.com",
                "category": "ai_automation",
                "requires_native": True
            },
            {
                "id": "4",
                "title": "📊 Performance Monitoring",
                "description": "Real-time browser performance analytics",
                "url": "https://web.dev/measure",
                "category": "performance",
                "requires_native": True
            }
        ]
        
        # Filter recommendations based on native engine availability
        if not native_engine_ready:
            recommendations = [r for r in recommendations if not r.get("requires_native")]
        
        return {
            "recommendations": recommendations,
            "native_engine_ready": native_engine_ready,
            "total_capabilities": len(recommendations) if native_engine_ready else 2
        }
        
    except Exception as e:
        return {"recommendations": [], "error": str(e)}

@app.delete("/api/clear-history")
async def clear_browsing_history():
    """Enhanced clear history with native session cleanup"""
    try:
        # Clear database records
        tabs_deleted = db.recent_tabs.delete_many({}).deleted_count
        chat_deleted = db.chat_sessions.delete_many({}).deleted_count
        
        # Clear native sessions if available
        native_sessions_closed = 0
        if native_engine_ready and native_engine:
            sessions_to_close = list(native_engine.sessions.keys())
            for session_id in sessions_to_close:
                result = await native_engine.close_session(session_id)
                if result["success"]:
                    native_sessions_closed += 1
        
        return {
            "success": True,
            "message": "Complete history cleared",
            "details": {
                "tabs_deleted": tabs_deleted,
                "chat_sessions_deleted": chat_deleted,
                "native_sessions_closed": native_sessions_closed,
                "native_engine_available": native_engine_ready
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENHANCED NATIVE API INTEGRATION
# ============================================================================

# Include the enhanced API router
# app.include_router(enhanced_router)  # Temporarily disabled until components are ready

# ============================================================================
# CLEANUP AND SHUTDOWN
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global native_engine, websocket_server
    
    try:
        logger.info("🛑 AETHER shutting down...")
        
        # Cleanup native engine
        if native_engine:
            await native_engine.cleanup()
            logger.info("✅ Native engine cleaned up")
        
        # Stop WebSocket server
        if websocket_server:
            await websocket_server.stop_server()
            logger.info("✅ WebSocket server stopped")
        
        logger.info("🛑 AETHER shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)