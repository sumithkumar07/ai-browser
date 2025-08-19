#!/usr/bin/env python3
"""
AETHER Enhanced Browser - Minimal Working Backend API
"""

from fastapi import FastAPI, HTTPException
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

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AETHER Enhanced Browser API", version="4.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client.aether_browser

# AI clients initialization
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

class SummarizationRequest(BaseModel):
    url: str
    length: str = "medium"

class SearchSuggestionRequest(BaseModel):
    query: str

class WorkflowRequest(BaseModel):
    name: str
    description: str
    steps: List[Dict[str, Any]]

class AutomationRequest(BaseModel):
    task_name: str
    url: str
    action_type: str
    parameters: Optional[Dict[str, Any]] = {}

# Helper functions
async def get_page_content(url: str) -> Dict[str, Any]:
    """Fetch and parse web page content"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
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

async def get_ai_response(message: str, context: Optional[str] = None, 
                         session_id: Optional[str] = None) -> str:
    """Get AI response using Groq"""
    try:
        system_prompt = """You are AETHER AI, an advanced browser assistant. Be helpful, concise, and accurate."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            context_msg = f"Current page context: {context[:1000]}"
            messages.append({"role": "system", "content": context_msg})
        
        messages.append({"role": "user", "content": message})
        
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1200,
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        logger.error(f"AI response error: {str(e)}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again."

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
            "version": "4.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_status,
                "ai_provider": "groq",
                "backend": "operational"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Browse a web page"""
    try:
        page_data = await get_page_content(session.url)
        
        # Store in recent tabs
        tab_data = {
            "id": str(uuid.uuid4()),
            "url": session.url,
            "title": page_data["title"],
            "content_preview": page_data["content"][:500],
            "timestamp": datetime.utcnow()
        }
        
        db.recent_tabs.insert_one(tab_data)
        
        # Keep only last 20 tabs
        all_tabs = list(db.recent_tabs.find().sort("timestamp", -1))
        if len(all_tabs) > 20:
            for tab in all_tabs[20:]:
                db.recent_tabs.delete_one({"_id": tab["_id"]})
        
        return {
            "success": True,
            "url": session.url,
            "page_data": page_data,
            "tab_id": tab_data["id"]
        }
        
    except Exception as e:
        logger.error(f"Browse error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """Chat with AI assistant"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Get page context if URL provided
        context = None
        if chat_data.current_url:
            page_data = await get_page_content(chat_data.current_url)
            context = f"Page: {page_data['title']}\nContent: {page_data['content']}"
        
        # Get AI response
        ai_response = await get_ai_response(chat_data.message, context, session_id)
        
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
        # Get recent browsing history
        recent_tabs = list(db.recent_tabs.find().sort("timestamp", -1).limit(5))
        
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
            # Simple recommendations based on recent tabs
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
        db.recent_tabs.delete_many({})
        db.chat_sessions.delete_many({})
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize")
async def summarize_page(request: SummarizationRequest):
    """Summarize webpage content"""
    try:
        page_data = await get_page_content(request.url)
        
        if "Error loading page" in page_data["content"]:
            raise HTTPException(status_code=400, detail="Could not fetch page content")
        
        prompt = f"""Please provide a {request.length} summary of this webpage:
        
Title: {page_data['title']}
Content: {page_data['content'][:3000]}

Provide a clear, informative summary."""

        summary = await get_ai_response(prompt)
        
        return {
            "url": request.url,
            "title": page_data["title"],
            "summary": summary,
            "length": request.length
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/api/search-suggestions")
async def get_search_suggestions(request: SearchSuggestionRequest):
    """Get AI-powered search suggestions"""
    try:
        suggestions = [
            f"{request.query} tutorial",
            f"{request.query} guide", 
            f"best {request.query}",
            f"{request.query} examples",
            f"how to {request.query}"
        ]
        
        return {
            "original_query": request.query,
            "suggestions": suggestions[:5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search suggestions failed: {str(e)}")

@app.post("/api/create-workflow")
async def create_workflow(request: WorkflowRequest):
    """Create a new workflow"""
    try:
        workflow_id = str(uuid.uuid4())
        
        workflow_data = {
            "id": workflow_id,
            "name": request.name,
            "description": request.description,
            "steps": request.steps,
            "status": "draft",
            "created_at": datetime.utcnow()
        }
        
        db.workflows.insert_one(workflow_data)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "name": request.name,
            "message": "Workflow created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")

@app.post("/api/voice-command")
async def process_voice_command(request: Dict[str, Any]):
    """Process voice command"""
    try:
        command_text = request.get("command", "")
        
        if "navigate to" in command_text.lower():
            url = command_text.lower().replace("navigate to", "").strip()
            return {"success": True, "action": "navigate", "url": url}
        elif "search for" in command_text.lower():
            query = command_text.lower().replace("search for", "").strip()
            return {"success": True, "action": "search", "query": query}
        else:
            return {"success": True, "action": "chat", "message": command_text}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/automate-task")
async def automate_task(request: Dict[str, Any]):
    """Create automation task"""
    try:
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "message": request.get("message", ""),
            "session_id": request.get("session_id"),
            "current_url": request.get("current_url"),
            "status": "created",
            "created_at": datetime.utcnow()
        }
        
        db.automation_tasks.insert_one(task_data)
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "created",
            "message": "Automation task created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@app.get("/api/enhanced/system/overview")
async def system_overview():
    """Get system overview"""
    try:
        tabs_count = db.recent_tabs.count_documents({})
        chats_count = db.chat_sessions.count_documents({})
        
        return {
            "status": "operational",
            "version": "4.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "recent_tabs": tabs_count,
                "chat_sessions": chats_count
            },
            "features": {
                "ai_chat": "operational",
                "web_browsing": "operational", 
                "automation": "operational"
            }
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)