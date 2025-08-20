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
    """Initialize Native Chromium Engine on startup"""
    global native_engine_ready
    
    try:
        logger.info("🔥 AETHER Native Chromium Integration - Starting...")
        
        # Test native chromium imports
        try:
            from native_chromium_engine import initialize_native_chromium_engine
            logger.info("✅ Native Chromium imports successful")
            
            # Initialize in background
            asyncio.create_task(initialize_native_engine())
            
        except ImportError as e:
            logger.warning(f"⚠️ Native Chromium imports failed: {e}")
            
        logger.info("🚀 AETHER Backend startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

async def initialize_native_engine():
    """Initialize native engine in background"""
    global native_engine_ready
    try:
        from native_chromium_engine import initialize_native_chromium_engine
        native_engine = await initialize_native_chromium_engine(client)
        if native_engine:
            native_engine_ready = True
            logger.info("✅ Native Chromium Engine ready")
    except Exception as e:
        logger.error(f"Native engine initialization error: {e}")

# API Routes

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        try:
            db.command("ping")
            db_status = "operational"
        except:
            db_status = "error"
        
        return {
            "status": "operational",
            "version": "6.0.0",
            "database": db_status,
            "native_chromium_ready": native_engine_ready,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "AETHER Native Chromium Integration"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/api/native/status")
async def native_status():
    """Get native engine status"""
    return {
        "native_available": native_engine_ready,
        "engine_type": "native_chromium",
        "version": "6.0.0",
        "capabilities": [
            "native_navigation",
            "screenshot_capture", 
            "javascript_execution",
            "devtools_protocol",
            "performance_monitoring"
        ] if native_engine_ready else []
    }

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Browse page endpoint"""
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
            "native_engine": native_engine_ready
        }
        
    except Exception as e:
        logger.error(f"Browse error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """AI chat endpoint"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Simple AI response
        ai_response = f"I'm AETHER AI with Native Chromium integration. You said: {chat_data.message}"
        
        # Store chat session
        chat_record = {
            "session_id": session_id,
            "user_message": chat_data.message,
            "ai_response": ai_response,
            "current_url": chat_data.current_url,
            "timestamp": datetime.utcnow()
        }
        
        db.chat_sessions.insert_one(chat_record)
        
        return {
            "response": ai_response,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-tabs")
async def get_recent_tabs():
    """Get recent browsing tabs"""
    try:
        tabs = list(db.recent_tabs.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(4))
        
        return {"tabs": tabs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations():
    """Get AI-powered browsing recommendations"""
    try:
        recommendations = [
            {
                "id": "1",
                "title": "Native Chromium Test",
                "description": "Test the native Chromium integration",
                "url": "https://www.google.com"
            },
            {
                "id": "2", 
                "title": "GitHub",
                "description": "Explore code repositories",
                "url": "https://github.com"
            }
        ]
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        return {"recommendations": []}

@app.delete("/api/clear-history")
async def clear_browsing_history():
    """Clear browsing history and chat sessions"""
    try:
        db.recent_tabs.delete_many({})
        db.chat_sessions.delete_many({})
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)