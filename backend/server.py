from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AETHER Browser API", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None
    language: Optional[str] = None

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

# In-memory storage
storage = {
    "recent_tabs": [],
    "chat_sessions": [],
    "recommendations": [
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
}

# Helper functions
async def fetch_page_content(url: str) -> Dict[str, Any]:
    """Fetch and parse web page content"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers={
                'User-Agent': 'AETHER Browser/3.0'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()
                
            title = soup.title.string if soup.title else url
            text_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text_content.splitlines())
            text = ' '.join(line for line in lines if line)[:5000]
            
            return {
                "title": title.strip(),
                "content": text,
                "url": url,
                "word_count": len(text.split()),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        return {
            "title": url,
            "content": f"Error loading page: {str(e)}",
            "url": url,
            "error": True,
            "extracted_at": datetime.utcnow().isoformat()
        }

def get_ai_response(message: str, context: str = None) -> str:
    """Generate AI response (fallback version)"""
    if "automate" in message.lower() or "task" in message.lower():
        return f"I understand you want to automate something: '{message}'. I'm currently in basic mode, but I can help you navigate and browse websites. Advanced automation features are being initialized."
    elif context:
        return f"I can see you're on a webpage about '{context[:100]}...'. How can I help you with this page? I can assist with navigation, searching, or explaining the content."
    else:
        return f"I understand your question: '{message}'. I'm running in basic mode right now. I can help you browse websites, navigate pages, and provide basic assistance. What would you like to do?"

# API Routes
@app.get("/")
async def root():
    return {
        "message": "AETHER Browser API",
        "version": "3.0.0",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AETHER Browser API v3.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Web Browsing & Navigation",
            "AI Chat Assistant (Basic Mode)",
            "Browsing History Tracking",
            "Content Analysis",
            "Recommendations Engine"
        ]
    }

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Browse to a web page"""
    try:
        page_data = await fetch_page_content(session.url)
        
        # Store in recent tabs
        tab_data = {
            "id": str(uuid.uuid4()),
            "url": session.url,
            "title": page_data["title"],
            "timestamp": datetime.utcnow(),
            "content_preview": page_data["content"][:300]
        }
        
        # Add to beginning and keep only last 10
        storage["recent_tabs"].insert(0, tab_data)
        storage["recent_tabs"] = storage["recent_tabs"][:10]
        
        return {
            "success": True,
            "page_data": page_data,
            "tab_id": tab_data["id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """Chat with AI assistant"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Get page context if available
        context = None
        if chat_data.current_url:
            try:
                page_data = await fetch_page_content(chat_data.current_url)
                context = page_data.get("title", "")
            except:
                context = chat_data.current_url
        
        # Generate AI response
        response = get_ai_response(chat_data.message, context)
        
        # Store chat session
        chat_record = {
            "session_id": session_id,
            "user_message": chat_data.message,
            "ai_response": response,
            "current_url": chat_data.current_url,
            "timestamp": datetime.utcnow()
        }
        
        storage["chat_sessions"].append(chat_record)
        
        return {
            "response": response,
            "session_id": session_id,
            "provider": "basic",
            "response_time": 0.1,
            "message_type": "conversation"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-tabs")
async def get_recent_tabs():
    """Get recent browsing tabs"""
    return {"tabs": storage["recent_tabs"][:4]}

@app.get("/api/recommendations")
async def get_recommendations():
    """Get browsing recommendations"""
    return {"recommendations": storage["recommendations"]}

@app.delete("/api/clear-history")
async def clear_history():
    """Clear browsing history"""
    storage["recent_tabs"] = []
    storage["chat_sessions"] = []
    return {"success": True, "message": "History cleared"}

# Basic automation endpoints
@app.post("/api/automate-task")
async def create_automation_task(task_data: ChatMessage):
    """Create automation task"""
    return {
        "success": True,
        "message": f"Automation task received: {task_data.message}",
        "task_id": str(uuid.uuid4()),
        "status": "basic_mode"
    }

@app.get("/api/active-automations")
async def get_active_automations():
    """Get active automations"""
    return {
        "success": True,
        "active_tasks": [],
        "message": "No active automations in basic mode"
    }

@app.post("/api/voice-command")
async def process_voice_command(request: Dict[str, Any]):
    """Process voice command"""
    return {
        "success": True,
        "message": "Voice command received (basic mode)"
    }

@app.post("/api/keyboard-shortcut")
async def keyboard_shortcut(request: Dict[str, Any]):
    """Handle keyboard shortcut"""
    return {
        "success": True,
        "message": "Keyboard shortcut handled (basic mode)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)