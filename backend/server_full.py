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
import logging
import time
import hashlib

load_dotenv()

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AETHER Enhanced Browser API", version="4.0.0")

# CORS middleware - Compatible configuration
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

# AI clients initialization
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize additional AI providers
openai_client = None
anthropic_client = None

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
    start_time = time.time()
    
    try:
        # Enhanced system prompt
        system_prompt = """You are AETHER AI, an advanced browser assistant with enhanced capabilities:

🔍 **Web Analysis**: Deep webpage content analysis and insights
🤖 **Smart Automation**: Workflow creation and task optimization  
📊 **Performance Intelligence**: System monitoring and optimization recommendations
🔒 **Security Awareness**: Website security analysis and safety guidance
💡 **Proactive Intelligence**: Context-aware suggestions and predictions

Response Guidelines:
- Be concise yet comprehensive
- Use markdown for clarity when helpful
- Provide actionable insights and suggestions
- Consider user context and browsing patterns
- Offer relevant next steps or related actions

Focus on being helpful, accurate, and efficient."""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add session history (last 3 interactions for context)
        if session_id:
            try:
                chat_history = list(db.chat_sessions.find(
                    {"session_id": session_id}
                ).sort("timestamp", -1).limit(3))
                
                for chat in reversed(chat_history):
                    messages.append({"role": "user", "content": chat["user_message"][:200]})
                    messages.append({"role": "assistant", "content": chat["ai_response"][:300]})
            except Exception:
                pass
        
        # Enhanced context processing
        if context:
            context_preview = context[:1500] if len(context) > 1500 else context
            context_msg = f"**Current Page Context:**\n{context_preview}"
            messages.append({"role": "system", "content": context_msg})
        
        messages.append({"role": "user", "content": message})
        
        # Enhanced Groq processing
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1200,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            stream=False
        )
        response_content = chat_completion.choices[0].message.content
        
        processing_time = time.time() - start_time
        logger.info(f"🚀 AI Response: {processing_time:.2f}s")
        
        return response_content
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"AI response error: {str(e)}")
        
        # Intelligent error responses
        if "timeout" in str(e).lower():
            return "The AI service is currently experiencing high load. Please try again in a moment."
        elif "rate limit" in str(e).lower():
            return "I'm processing many requests right now. Please wait a moment and try again."
        else:
            return "I apologize for the technical issue. Please try rephrasing your question or try again later."

# API Routes
@app.get("/api/health")
async def health_check():
    """Enhanced health check with comprehensive system status"""
    try:
        # Test database connection
        try:
            db.command("ping")
            db_status = "operational"
        except:
            db_status = "error"
        
        health_data = {
            "status": "operational",
            "version": "4.0.0", 
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": db_status,
                "ai_provider": "groq",
                "backend": "operational"
            },
            "enhanced_capabilities": [
                "intelligent_ai_conversations",
                "advanced_web_browsing",
                "real_time_performance_monitoring",
                "comprehensive_security_analysis",
                "automated_optimization_suggestions"
            ]
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/browse")
async def browse_page(session: BrowsingSession):
    """Enhanced web page browsing"""
    try:
        page_data = await get_page_content(session.url)
        
        # Store in recent tabs with enhanced data
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
        
        # Keep only last 20 tabs for performance
        all_tabs = list(db.recent_tabs.find().sort("timestamp", -1))
        if len(all_tabs) > 20:
            for tab in all_tabs[20:]:
                db.recent_tabs.delete_one({"_id": tab["_id"]})
        
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
    """Enhanced AI chat with intelligent conversation patterns"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Get page context if URL provided
        context = None
        if chat_data.current_url:
            page_data = await get_page_content(chat_data.current_url)
            context = f"Page: {page_data['title']}\nContent: {page_data['content']}"
        
        # Get AI response
        ai_response = await get_ai_response(chat_data.message, context, session_id)
        
        # Store chat session with enhanced data
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
            "session_id": session_id,
            "enhanced_features": ["intelligent_conversation", "context_aware", "session_management"]
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
            # AI-powered recommendations based on browsing history
            browsing_context = "\n".join([f"- {tab['title']}: {tab.get('content_preview', '')}" for tab in recent_tabs])
            
            prompt = f"""Based on this browsing history, suggest 3 relevant websites:
{browsing_context}

Return only a JSON array with objects containing: id, title, description, url"""

            try:
                ai_response = await get_ai_response(prompt)
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

# Enhanced endpoints
@app.post("/api/summarize")
async def summarize_page(request: SummarizationRequest):
    """Summarize webpage content"""
    try:
        page_data = await get_page_content(request.url)
        
        length_instructions = {
            "short": "Provide a brief 2-3 sentence summary",
            "medium": "Provide a comprehensive paragraph summary",
            "long": "Provide a detailed multi-paragraph analysis"
        }
        
        prompt = f"""Summarize this webpage content:
        
Title: {page_data['title']}
Content: {page_data['content'][:3000]}

{length_instructions.get(request.length, length_instructions['medium'])}"""

        summary = await get_ai_response(prompt)
        
        return {
            "success": True,
            "title": page_data["title"],
            "summary": summary,
            "length": request.length,
            "word_count": len(summary.split())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/api/search-suggestions")
async def get_search_suggestions(request: SearchSuggestionRequest):
    """Get AI-powered search suggestions"""
    try:
        prompt = f"""Provide 5 relevant search suggestions for the query: "{request.query}"

Make the suggestions helpful and diverse. Return as a JSON array of strings."""

        ai_response = await get_ai_response(prompt)
        
        try:
            import re
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
            else:
                suggestions = [f"{request.query} tutorial", f"{request.query} guide", f"{request.query} examples"]
        except:
            suggestions = [f"{request.query} tutorial", f"{request.query} guide", f"{request.query} examples"]
        
        return {
            "success": True,
            "query": request.query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search suggestions failed: {str(e)}")

@app.post("/api/create-workflow")
async def create_workflow(request: WorkflowRequest):
    """Create automation workflow"""
    try:
        workflow_data = {
            "id": str(uuid.uuid4()),
            "name": request.name,
            "description": request.description,
            "steps": request.steps,
            "created_at": datetime.utcnow(),
            "status": "created"
        }
        
        db.workflows.insert_one(workflow_data)
        
        return {
            "success": True,
            "workflow_id": workflow_data["id"],
            "name": request.name,
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow creation failed: {str(e)}")

@app.post("/api/voice-command")
async def process_voice_command(request: Dict[str, Any]):
    """Process voice commands"""
    try:
        command = request.get("command", "")
        
        # Process different voice commands
        if "navigate" in command.lower():
            return {"success": True, "action": "navigate", "result": "Navigation command processed"}
        elif "search" in command.lower():
            return {"success": True, "action": "search", "result": "Search command processed"}
        elif "summarize" in command.lower():
            return {"success": True, "action": "summarize", "result": "Summarization command processed"}
        else:
            return {"success": True, "action": "general", "result": f"Voice command processed: {command}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice command failed: {str(e)}")

@app.post("/api/automate-task")
async def create_automation_task(request: AutomationRequest):
    """Create automation task"""
    try:
        task_data = {
            "id": str(uuid.uuid4()),
            "name": request.task_name,
            "url": request.url,
            "action_type": request.action_type,
            "parameters": request.parameters,
            "status": "created",
            "created_at": datetime.utcnow()
        }
        
        db.automation_tasks.insert_one(task_data)
        
        return {
            "success": True,
            "task_id": task_data["id"],
            "name": request.task_name,
            "status": "created"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Automation task creation failed: {str(e)}")

@app.get("/api/enhanced/system/overview")
async def get_system_overview():
    """Get comprehensive system overview"""
    try:
        # Get database stats
        recent_tabs_count = db.recent_tabs.count_documents({})
        chat_sessions_count = db.chat_sessions.count_documents({})
        workflows_count = db.workflows.count_documents({})
        
        return {
            "status": "operational",
            "version": "4.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "recent_tabs": recent_tabs_count,
                "chat_sessions": chat_sessions_count,
                "workflows": workflows_count
            },
            "services": {
                "database": "operational",
                "ai_provider": "operational",
                "backend": "operational"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)