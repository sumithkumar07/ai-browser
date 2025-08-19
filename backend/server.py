from fastapi import FastAPI, HTTPException
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

# Create FastAPI app - Clean initialization
app = FastAPI(
    title="AETHER Enhanced Browser API", 
    version="4.0.0",
    middleware=[]  # Explicitly empty middleware list
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

# Helper functions
async def get_page_content(url: str) -> Dict[str, Any]:
    """Fetch and parse web page content"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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

async def get_ai_response(message: str, context: Optional[str] = None, 
                         session_id: Optional[str] = None) -> str:
    """Enhanced AI response with Groq"""
    try:
        system_prompt = """You are AETHER AI, an advanced browser assistant. Be helpful, concise, and accurate."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            context_preview = context[:1500] if len(context) > 1500 else context
            context_msg = f"Current Page Context: {context_preview}"
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
    """Enhanced health check"""
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
    """Enhanced web page browsing"""
    try:
        page_data = await get_page_content(session.url)
        
        # Store in recent tabs
        tab_data = {
            "id": str(uuid.uuid4()),
            "url": session.url,
            "title": page_data["title"],
            "content_preview": page_data["content"][:500],
            "timestamp": datetime.utcnow(),
            "is_secure": session.url.startswith('https://'),
            "domain": session.url.split('/')[2] if '://' in session.url else session.url
        }
        
        db.recent_tabs.insert_one(tab_data)
        
        return {
            "success": True,
            "url": session.url,
            "page_data": {
                "title": page_data["title"],
                "content": page_data["content"],
                "security": {"is_https": session.url.startswith('https://')},
                "meta": {"description": ""}
            },
            "tab_id": tab_data["id"]
        }
        
    except Exception as e:
        logger.error(f"Browse error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat_with_ai(chat_data: ChatMessage):
    """Enhanced AI chat"""
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