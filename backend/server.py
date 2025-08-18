from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="AETHER Browser API - Minimal", version="1.0.0")

# CORS middleware
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

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

# In-memory storage for testing
recent_tabs = []
chat_sessions = {}
active_automations = []

@app.get("/")
async def root():
    return {"message": "AETHER Browser API - Minimal Version", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/recent-tabs")
async def get_recent_tabs():
    """Get recent browsing tabs"""
    return {
        "tabs": recent_tabs if recent_tabs else [
            {"id": "1", "title": "Example Site", "url": "https://example.com", "timestamp": datetime.now().isoformat()},
            {"id": "2", "title": "GitHub", "url": "https://github.com", "timestamp": datetime.now().isoformat()},
        ]
    }

@app.get("/api/recommendations")
async def get_recommendations():
    """Get AI-powered recommendations"""
    return {
        "recommendations": [
            {
                "id": "1",
                "title": "Discover AI Tools",
                "description": "Explore the latest AI-powered tools and services to enhance your productivity and creativity.",
                "url": "https://example.com/ai-tools"
            },
            {
                "id": "2", 
                "title": "Tech News & Updates",
                "description": "Stay informed with the latest technology trends, product launches, and industry insights.",
                "url": "https://news.ycombinator.com"
            },
            {
                "id": "3",
                "title": "Learning Resources", 
                "description": "Find educational content, tutorials, and courses to expand your knowledge and skills.",
                "url": "https://example.com/learning"
            }
        ]
    }

@app.get("/api/active-automations")
async def get_active_automations():
    """Get active automation tasks"""
    return {"active_tasks": active_automations}

@app.post("/api/browse")
async def browse_url(session: BrowsingSession):
    """Handle URL browsing"""
    try:
        # Add to recent tabs
        tab_data = {
            "id": str(len(recent_tabs) + 1),
            "title": session.title or "Web Page",
            "url": session.url,
            "timestamp": datetime.now().isoformat()
        }
        recent_tabs.insert(0, tab_data)
        
        # Keep only last 10 tabs
        if len(recent_tabs) > 10:
            recent_tabs.pop()
        
        return {
            "success": True,
            "page_data": {
                "title": session.title or "Web Page",
                "url": session.url
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(message: ChatMessage):
    """Handle AI chat messages"""
    try:
        # Simple mock response for testing
        response_text = f"I understand you said: '{message.message}'. This is a test response from the minimal backend. The AI integration is not fully implemented in this minimal version."
        
        # Store in session
        session_id = message.session_id or "default"
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        chat_sessions[session_id].append({
            "user_message": message.message,
            "ai_response": response_text,
            "timestamp": datetime.now().isoformat(),
            "current_url": message.current_url
        })
        
        return {
            "response": response_text,
            "session_id": session_id,
            "message_type": "chat_response"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation-suggestions")
async def get_automation_suggestions(current_url: Optional[str] = None):
    """Get automation suggestions for current page"""
    return {
        "suggestions": [
            {
                "title": "Extract Page Content",
                "command": "extract all text from this page",
                "estimated_time": "30 seconds"
            },
            {
                "title": "Monitor Page Changes",
                "command": "monitor this page for changes",
                "estimated_time": "ongoing"
            }
        ]
    }

@app.delete("/api/clear-history")
async def clear_history():
    """Clear browsing history"""
    global recent_tabs
    recent_tabs = []
    return {"success": True, "message": "History cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)