"""
AETHER Native Chromium Browser API v6.0.0
Complete Native Integration - No iframe fallbacks
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import uuid
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import groq
import json
import logging
import time
import asyncio

# Native Chromium imports
from native_chromium_engine import initialize_native_chromium_engine, get_native_chromium_engine
from native_chromium_endpoints import setup_native_chromium_endpoints
from native_endpoints import add_native_endpoints

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client.aether_browser

# AI clients initialization
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Global native engine
native_chromium_engine_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Native Chromium Engine Lifespan Management"""
    global native_chromium_engine_instance
    
    # Startup
    logger.info("🔥 AETHER Native Chromium Integration - Starting...")
    try:
        # Initialize Native Chromium Engine
        native_chromium_engine_instance = await initialize_native_chromium_engine(client)
        
        if native_chromium_engine_instance:
            logger.info("✅ Native Chromium Engine initialized successfully")
            logger.info("   ✅ Playwright Browser Engine Ready")
            logger.info("   ✅ WebSocket Real-time Control Ready")
            logger.info("   ✅ Advanced DevTools Protocol Ready")
            logger.info("   ✅ Performance Monitoring Ready")
            logger.info("   ✅ Security Analysis Ready")
            logger.info("   ✅ Screenshot & Automation Ready")
            
            # Setup Native Chromium API endpoints
            setup_native_chromium_endpoints(app)
            logger.info("   ✅ Native API endpoints configured")
            logger.info("🚀 COMPLETE NATIVE CHROMIUM INTEGRATION ACTIVE")
        else:
            logger.error("❌ Native Chromium Engine initialization failed")
            
    except Exception as e:
        logger.error(f"Startup error: {e}")
    
    yield
    
    # Shutdown
    if native_chromium_engine_instance:
        await native_chromium_engine_instance.cleanup()
        logger.info("🧹 Native Chromium Engine cleaned up")

# Create FastAPI app with Native Chromium lifespan
app = FastAPI(
    title="AETHER Native Browser API",
    version="6.0.0",
    description="Complete Native Chromium Integration - No iframe fallbacks",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add native endpoints
add_native_endpoints(app)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

# Helper functions
async def get_page_content_native(url: str, session_id: str = None) -> Dict[str, Any]:
    """Get page content using Native Chromium Engine"""
    try:
        if native_chromium_engine_instance and session_id:
            # Use native engine to get content
            result = await native_chromium_engine_instance.get_page_content(session_id, include_html=False)
            if result['success']:
                return {
                    "title": result['title'],
                    "content": result['text_content'],
                    "url": result['url']
                }
        
        # Fallback to HTTP client if native engine unavailable
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 AETHER-Native/6.0'
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            title = soup.title.string if soup.title else url
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return {
                "title": title.strip(),
                "content": text[:5000],  # Limit content size
                "url": url
            }
    except Exception as e:
        return {"title": url, "content": f"Error loading page: {str(e)}", "url": url}

async def get_ai_response_native(message: str, context: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Enhanced AI response with Native Chromium context"""
    try:
        system_prompt = """You are AETHER AI, an advanced browser assistant with Native Chromium integration. 
        You can control the browser natively and provide enhanced browsing assistance."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            context_preview = context[:1500] if len(context) > 1500 else context
            context_msg = f"Current Page Context (Native Engine): {context_preview}"
            messages.append({"role": "system", "content": context_msg})
        
        messages.append({"role": "user", "content": message})
        
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1200,
            stream=False
        )
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"AI response error: {str(e)}")
        return "I apologize for the technical issue. Please try again later."

# API Routes

@app.get("/api/health")
async def health_check():
    """Native Chromium Health Check"""
    try:
        # Test database connection
        try:
            db.command("ping")
            db_status = "operational"
        except:
            db_status = "error"
        
        # Native engine status
        native_status = {
            "available": native_chromium_engine_instance is not None,
            "initialized": native_chromium_engine_instance.is_initialized if native_chromium_engine_instance else False,
            "active_sessions": len(native_chromium_engine_instance.active_sessions) if native_chromium_engine_instance else 0,
            "engine_type": "native_chromium",
            "capabilities": [
                "native_navigation",
                "screenshot_capture", 
                "javascript_execution",
                "devtools_protocol",
                "performance_monitoring",
                "security_analysis",
                "websocket_control",
                "cross_origin_access"
            ] if native_chromium_engine_instance else []
        }
        
        return {
            "status": "native_operational",
            "version": "6.0.0",
            "native_integration": native_status,
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_status,
                "ai_provider": "groq",
                "backend": "operational",
                "native_chromium": "operational" if native_status["available"] else "unavailable"
            },
            "integration_type": "complete_native_chromium",
            "iframe_fallback": False,
            "message": "AETHER Native Chromium Integration - 100% Native Browser Engine"
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.post("/api/browse")
async def browse_page_native(session: BrowsingSession):
    """Native browsing with Chromium engine"""
    try:
        # Create or get native browser session
        session_id = f"browse_{str(uuid.uuid4())[:8]}"
        
        if native_chromium_engine_instance:
            # Use native engine for browsing
            browser_session = await native_chromium_engine_instance.create_browser_session(session_id)
            
            if browser_session['success']:
                # Navigate using native engine
                nav_result = await native_chromium_engine_instance.navigate_to_url(session_id, session.url)
                
                if nav_result['success']:
                    # Get page content using native engine
                    content_result = await native_chromium_engine_instance.get_page_content(session_id)
                    
                    # Store in recent tabs
                    tab_data = {
                        "id": str(uuid.uuid4()),
                        "url": session.url,
                        "title": content_result.get('title', session.url) if content_result['success'] else session.url,
                        "content_preview": content_result.get('text_content', '')[:500] if content_result['success'] else '',
                        "timestamp": datetime.utcnow(),
                        "is_secure": session.url.startswith('https://'),
                        "domain": session.url.split('/')[2] if '://' in session.url else session.url,
                        "native_session_id": session_id,
                        "engine_type": "native_chromium"
                    }
                    
                    db.recent_tabs.insert_one(tab_data)
                    
                    return {
                        "success": True,
                        "url": nav_result['url'],
                        "page_data": {
                            "title": nav_result['title'],
                            "content": content_result.get('text_content', '') if content_result['success'] else '',
                            "security": nav_result.get('security', {}),
                            "load_time": nav_result.get('load_time', 0),
                            "native_engine": True
                        },
                        "tab_id": tab_data["id"],
                        "native_session_id": session_id
                    }
        
        # This shouldn't happen with complete native integration
        raise HTTPException(status_code=500, detail="Native Chromium Engine unavailable")
        
    except Exception as e:
        logger.error(f"Native browse error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai_native(chat_data: ChatMessage):
    """AI chat with Native Chromium integration"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Get page context using Native Chromium if URL provided
        context = None
        native_session_id = None
        
        if chat_data.current_url and native_chromium_engine_instance:
            # Create temporary native session for content analysis
            native_session_id = f"chat_{str(uuid.uuid4())[:8]}"
            browser_session = await native_chromium_engine_instance.create_browser_session(native_session_id)
            
            if browser_session['success']:
                # Navigate and get content
                nav_result = await native_chromium_engine_instance.navigate_to_url(native_session_id, chat_data.current_url)
                if nav_result['success']:
                    content_result = await native_chromium_engine_instance.get_page_content(native_session_id)
                    if content_result['success']:
                        context = f"Page: {content_result['title']}\nContent: {content_result['text_content']}"
        
        # Get AI response with native context
        ai_response = await get_ai_response_native(chat_data.message, context, session_id)
        
        # Store chat session
        chat_record = {
            "session_id": session_id,
            "user_message": chat_data.message,
            "ai_response": ai_response,
            "current_url": chat_data.current_url,
            "native_session_id": native_session_id,
            "engine_type": "native_chromium",
            "timestamp": datetime.utcnow()
        }
        
        db.chat_sessions.insert_one(chat_record)
        
        # Cleanup temporary native session
        if native_session_id and native_chromium_engine_instance:
            await native_chromium_engine_instance.close_session(native_session_id)
        
        return {
            "response": ai_response,
            "session_id": session_id,
            "native_context": context is not None
        }
        
    except Exception as e:
        logger.error(f"Native chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-tabs")
async def get_recent_tabs_native():
    """Get recent browsing tabs (Native engine)"""
    try:
        tabs = list(db.recent_tabs.find(
            {}, 
            {"_id": 0}
        ).sort("timestamp", -1).limit(4))
        
        # Mark tabs as native-powered
        for tab in tabs:
            tab["engine_type"] = "native_chromium"
            tab["native_powered"] = True
        
        return {"tabs": tabs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations_native():
    """Get AI-powered browsing recommendations (Native enhanced)"""
    try:
        recommendations = [
            {
                "id": "1",
                "title": "Native Chromium Performance",
                "description": "Experience lightning-fast browsing with native engine",
                "url": "https://www.chromium.org/developers/",
                "native_enhanced": True
            },
            {
                "id": "2", 
                "title": "Advanced Web Technologies",
                "description": "Explore cutting-edge web technologies with full native support",
                "url": "https://developer.mozilla.org/",
                "native_enhanced": True
            },
            {
                "id": "3",
                "title": "AI-Powered Development",
                "description": "Discover AI tools with enhanced native browser capabilities",
                "url": "https://www.producthunt.com/topics/artificial-intelligence",
                "native_enhanced": True
            }
        ]
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        return {"recommendations": []}

@app.delete("/api/clear-history")
async def clear_browsing_history_native():
    """Clear browsing history and chat sessions"""
    try:
        db.recent_tabs.delete_many({})
        db.chat_sessions.delete_many({})
        return {"success": True, "message": "History cleared (Native Engine)"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)