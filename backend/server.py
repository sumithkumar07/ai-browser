from fastapi import FastAPI, HTTPException, BackgroundTasks
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

load_dotenv()

app = FastAPI(title="AETHER Browser API", version="1.0.0")

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

# Groq client
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None

class BrowsingSession(BaseModel):
    url: str
    title: Optional[str] = None

class Tab(BaseModel):
    id: str
    url: str
    title: str
    timestamp: datetime

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

async def get_ai_response(message: str, context: Optional[str] = None, session_id: Optional[str] = None) -> str:
    """Get AI response using Groq API"""
    try:
        # Get conversation history
        messages = [
            {
                "role": "system", 
                "content": "You are AETHER AI Assistant, an intelligent browser companion. You help users with web browsing, answer questions, and provide helpful information. Be concise but informative."
            }
        ]
        
        if session_id:
            # Get previous messages from database
            chat_history = list(db.chat_sessions.find(
                {"session_id": session_id}
            ).sort("timestamp", -1).limit(10))
            
            for chat in reversed(chat_history):
                messages.append({"role": "user", "content": chat["user_message"]})
                messages.append({"role": "assistant", "content": chat["ai_response"]})
        
        # Add context if available (web page content)
        if context:
            context_msg = f"Current webpage context: {context[:2000]}"
            messages.append({"role": "system", "content": context_msg})
        
        messages.append({"role": "user", "content": message})
        
        # Get response from Groq
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.1-70b-versatile",  # Using latest Llama model
            temperature=0.7,
            max_tokens=1000
        )
        
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"Sorry, I'm having trouble processing your request: {str(e)}"

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "AETHER Browser API"}

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Fetch web page content and store browsing history"""
    try:
        page_data = await get_page_content(session.url)
        
        # Store in recent tabs
        tab_data = {
            "id": str(uuid.uuid4()),
            "url": session.url,
            "title": page_data["title"],
            "timestamp": datetime.utcnow(),
            "content_preview": page_data["content"][:200]
        }
        
        db.recent_tabs.insert_one(tab_data)
        
        # Keep only last 10 tabs
        all_tabs = list(db.recent_tabs.find().sort("timestamp", -1))
        if len(all_tabs) > 10:
            for tab in all_tabs[10:]:
                db.recent_tabs.delete_one({"_id": tab["_id"]})
        
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
        
        # Get page context if URL provided
        context = None
        if chat_data.current_url:
            page_data = await get_page_content(chat_data.current_url)
            context = f"Page: {page_data['title']}\nContent: {page_data['content']}"
        
        # Get AI response
        ai_response = await get_ai_response(
            chat_data.message, 
            context=context,
            session_id=session_id
        )
        
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
            # AI-powered recommendations based on browsing history
            browsing_context = "\n".join([f"- {tab['title']}: {tab.get('content_preview', '')}" for tab in recent_tabs])
            
            prompt = f"""Based on this browsing history, suggest 3 relevant websites or pages the user might be interested in:
{browsing_context}

Return only a JSON array with objects containing: id, title, description, url
Make recommendations relevant and helpful."""

            try:
                ai_response = await get_ai_response(prompt)
                # Try to parse AI response as JSON
                import re
                json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group())
                else:
                    raise Exception("No valid JSON found")
            except:
                # Fallback recommendations
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)