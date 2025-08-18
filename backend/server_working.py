from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
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
import json
import asyncio
import time
import logging

# Load environment variables first
load_dotenv()

# Only import basic essential modules to start
try:
    from database import get_database, get_client
    database_available = True
except ImportError:
    database_available = False
    
try:
    from ai_manager import get_ai_manager
    ai_manager = get_ai_manager()
    ai_available = True
except ImportError:
    ai_available = False

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="AETHER Browser API - Working", version="3.0.0")

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
if database_available:
    try:
        client = get_client()
        db = get_database()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        database_available = False

if not database_available:
    # Fallback to direct connection
    try:
        MONGO_URL = os.getenv("MONGO_URL")
        client = MongoClient(MONGO_URL, maxPoolSize=50, minPoolSize=10)
        db = client.aether_browser
        database_available = True
        logger.info("Direct database connection established")
    except Exception as e:
        logger.error(f"Direct database connection failed: {e}")
        database_available = False

# Enhanced Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None
    language: Optional[str] = None

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

class Tab(BaseModel):
    id: str
    url: str
    title: str
    timestamp: datetime

class SummarizationRequest(BaseModel):
    url: str
    length: str = "medium"  # short, medium, long

class SearchSuggestionRequest(BaseModel):
    query: str

class BookmarkRequest(BaseModel):
    url: str
    title: str
    tags: Optional[List[str]] = []

# In-memory fallback storage
fallback_storage = {
    "recent_tabs": [],
    "chat_sessions": [],
    "recommendations": []
}

# Helper functions
async def get_page_content_basic(url: str) -> Dict[str, Any]:
    """Basic web page content fetching without advanced caching"""
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={
                'User-Agent': 'AETHER Browser/3.0 (+http://aether.browser)'
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
                
            title = soup.title.string if soup.title else url
            
            # Extract main content
            main_content = soup.find(['main', 'article', '[role="main"]'])
            if main_content:
                text_content = main_content.get_text()
            else:
                text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Extract metadata
            meta_description = ""
            meta_keywords = ""
            
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag and desc_tag.get('content'):
                meta_description = desc_tag['content']
            
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag and keywords_tag.get('content'):
                meta_keywords = keywords_tag['content']
            
            content_data = {
                "title": title.strip(),
                "content": text[:8000],
                "meta_description": meta_description,
                "meta_keywords": meta_keywords,
                "url": url,
                "word_count": len(text.split()),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            return content_data
            
    except Exception as e:
        error_content = {
            "title": url,
            "content": f"Error loading page: {str(e)}",
            "url": url,
            "error": True,
            "extracted_at": datetime.utcnow().isoformat()
        }
        return error_content

async def get_basic_ai_response(message: str, context: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get AI response with fallback if advanced system not available"""
    
    if ai_available:
        try:
            # Try with AI manager
            response = await ai_manager.get_response(message, context)
            return {
                "response": response,
                "provider": "groq",
                "response_time": 1.0,
                "cached": False
            }
        except Exception as e:
            logger.error(f"AI manager failed: {e}")
    
    # Fallback response
    fallback_responses = [
        f"I understand you're asking about: '{message}'. I'm currently running in basic mode, but I can still help you browse and navigate websites.",
        f"Thanks for your question about '{message}'. While my advanced AI features are initializing, I can still assist with web browsing and basic tasks.",
        f"I received your message: '{message}'. I'm operating in compatibility mode right now, but I can help you with browsing, navigation, and basic web tasks."
    ]
    
    response_text = fallback_responses[hash(message) % len(fallback_responses)]
    
    if context:
        response_text += f"\n\nI can see you're currently on a webpage. Would you like me to help you navigate or find something specific on this page?"
    
    return {
        "response": response_text,
        "provider": "fallback",
        "response_time": 0.1,
        "cached": False,
        "mode": "basic"
    }

# API Routes
@app.get("/")
async def root():
    return {
        "message": "AETHER Browser API - Working Version",
        "version": "3.0.0",
        "status": "operational",
        "database": "available" if database_available else "fallback",
        "ai": "available" if ai_available else "fallback"
    }

@app.get("/api/health")
async def health_check():
    """Enhanced health check"""
    return {
        "status": "healthy",
        "service": "AETHER Browser API v3.0 - Working",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "connected" if database_available else "fallback",
            "ai_system": "operational" if ai_available else "fallback",
            "web_scraping": "operational",
            "api_endpoints": "operational"
        },
        "features": [
            "Web Browsing & Navigation",
            "AI Chat Assistant (Basic Mode)" if not ai_available else "AI Chat Assistant (Enhanced)",
            "Browsing History Tracking", 
            "Content Analysis",
            "Recommendations Engine"
        ]
    }

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Enhanced web page fetching"""
    try:
        # Get page content
        page_data = await get_page_content_basic(session.url)
        
        # Store in recent tabs
        tab_data = {
            "id": str(uuid.uuid4()),
            "url": session.url,
            "title": page_data["title"],
            "timestamp": datetime.utcnow(),
            "content_preview": page_data["content"][:300],
            "meta_description": page_data.get("meta_description", ""),
            "word_count": page_data.get("word_count", 0),
            "visit_count": 1
        }
        
        if database_available:
            # Check if URL already exists and increment visit count
            existing_tab = db.recent_tabs.find_one({"url": session.url})
            if existing_tab:
                tab_data["visit_count"] = existing_tab.get("visit_count", 0) + 1
                db.recent_tabs.replace_one({"url": session.url}, tab_data)
            else:
                db.recent_tabs.insert_one(tab_data)
            
            # Keep only last 20 tabs
            all_tabs = list(db.recent_tabs.find().sort("timestamp", -1))
            if len(all_tabs) > 20:
                for tab in all_tabs[20:]:
                    db.recent_tabs.delete_one({"_id": tab["_id"]})
        else:
            # Use fallback storage
            fallback_storage["recent_tabs"].insert(0, tab_data)
            if len(fallback_storage["recent_tabs"]) > 20:
                fallback_storage["recent_tabs"] = fallback_storage["recent_tabs"][:20]
        
        return {
            "success": True,
            "page_data": page_data,
            "tab_id": tab_data["id"],
            "cached": False
        }
        
    except Exception as e:
        logger.error(f"Browse error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """Enhanced chat with AI support"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Get page context if URL provided
        context = None
        if chat_data.current_url:
            try:
                page_data = await get_page_content_basic(chat_data.current_url)
                if not page_data.get("error", False):
                    title = page_data.get('title', 'Unknown Page')
                    description = page_data.get('meta_description', '')
                    content = page_data.get('content', '')[:3000]
                    context = f"Page: {title}\nDescription: {description}\nContent: {content}"
            except Exception as e:
                logger.error(f"Failed to get page context: {e}")
                context = f"Page URL: {chat_data.current_url}"
        
        # Get AI response
        ai_result = await get_basic_ai_response(
            chat_data.message, 
            context=context,
            session_id=session_id
        )
        
        # Store chat session
        chat_record = {
            "session_id": session_id,
            "user_message": chat_data.message,
            "ai_response": ai_result["response"],
            "ai_provider": ai_result["provider"],
            "current_url": chat_data.current_url,
            "response_time": ai_result["response_time"],
            "language": chat_data.language,
            "message_type": "conversation",
            "timestamp": datetime.utcnow()
        }
        
        if database_available:
            db.chat_sessions.insert_one(chat_record)
        else:
            fallback_storage["chat_sessions"].append(chat_record)
        
        return {
            "response": ai_result["response"],
            "session_id": session_id,
            "provider": ai_result["provider"],
            "response_time": ai_result["response_time"],
            "message_type": "conversation",
            "mode": ai_result.get("mode", "enhanced")
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-tabs")
async def get_recent_tabs():
    """Get recent browsing tabs"""
    try:
        if database_available:
            tabs = list(db.recent_tabs.find(
                {}, 
                {"_id": 0}
            ).sort("timestamp", -1).limit(4))
        else:
            tabs = fallback_storage["recent_tabs"][:4]
        
        return {"tabs": tabs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations")
async def get_recommendations():
    """Get AI-powered browsing recommendations"""
    try:
        # Get recent browsing history
        if database_available:
            recent_tabs = list(db.recent_tabs.find().sort("timestamp", -1).limit(5))
        else:
            recent_tabs = fallback_storage["recent_tabs"][:5]
        
        if not recent_tabs:
            # Default recommendations
            recommendations = [
                {
                    "id": "1",
                    "title": "Discover AI Tools",
                    "description": "Explore the latest AI-powered tools and services",
                    "url": "https://www.producthunt.com/topics/artificial-intelligence"
                },
                {
                    "id": "2", 
                    "title": "Tech News",
                    "description": "Stay updated with technology trends",
                    "url": "https://news.ycombinator.com"
                },
                {
                    "id": "3",
                    "title": "Learn Something New",
                    "description": "Educational content and tutorials",
                    "url": "https://www.coursera.org"
                }
            ]
        else:
            # Simple recommendations based on browsing history
            recommendations = [
                {
                    "id": "1",
                    "title": "Continue Reading",
                    "description": "Based on your recent browsing",
                    "url": recent_tabs[0]["url"] if recent_tabs else "https://google.com"
                },
                {
                    "id": "2",
                    "title": "Related Topics",
                    "description": "Discover similar content",
                    "url": "https://www.google.com/search?q=" + recent_tabs[0]["title"].replace(" ", "+") if recent_tabs else "https://google.com"
                },
                {
                    "id": "3",
                    "title": "Trending Now",
                    "description": "Popular content today",
                    "url": "https://trends.google.com"
                }
            ]
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        return {"recommendations": []}

@app.delete("/api/clear-history")
async def clear_browsing_history():
    """Clear browsing history and chat sessions"""
    try:
        if database_available:
            db.recent_tabs.delete_many({})
            db.chat_sessions.delete_many({})
        else:
            fallback_storage["recent_tabs"] = []
            fallback_storage["chat_sessions"] = []
        
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Basic automation endpoints (placeholder)
@app.post("/api/automate-task")
async def create_automation_task(task_data: ChatMessage):
    """Create automation task (basic version)"""
    return {
        "success": True,
        "message": f"Automation task noted: {task_data.message}. Advanced automation features are being initialized.",
        "task_id": str(uuid.uuid4()),
        "status": "pending_advanced_features"
    }

@app.get("/api/active-automations")
async def get_active_automations():
    """Get active automation tasks (basic version)"""
    return {
        "success": True,
        "active_tasks": [],
        "message": "Automation engine initializing"
    }

# Voice commands placeholder
@app.post("/api/voice-command")
async def process_voice_command(request: Dict[str, Any]):
    """Process voice command (basic version)"""
    return {
        "success": True,
        "message": "Voice command received. Advanced voice features initializing.",
        "command_processed": False
    }

# Keyboard shortcuts placeholder
@app.post("/api/keyboard-shortcut")
async def execute_keyboard_shortcut(request: Dict[str, Any]):
    """Execute keyboard shortcut (basic version)"""
    return {
        "success": True,
        "message": "Keyboard shortcut noted. Advanced shortcuts system initializing."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)