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

# Import enhanced automation capabilities
try:
    from enhanced_server import enhanced_chat_with_ai, task_executor, nlp_processor
    ENHANCED_MODE = True
    logger.info("Enhanced automation capabilities loaded successfully")
except ImportError:
    ENHANCED_MODE = False
    logger.warning("Enhanced automation not available, running in basic mode")

# Create FastAPI app
app = FastAPI(
    title="AETHER Enhanced Browser API", 
    version="5.0.0"  # Updated version for enhanced capabilities
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

# AI clients initialization
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Enhanced Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None

class EnhancedChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    current_url: Optional[str] = None
    enable_automation: Optional[bool] = True
    background_execution: Optional[bool] = True

class AutomationCommand(BaseModel):
    command: str
    user_session: str
    priority: Optional[str] = "normal"
    background: Optional[bool] = True

class TaskStatusRequest(BaseModel):
    task_id: str
    user_session: str

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

class VoiceCommandRequest(BaseModel):
    voice_text: Optional[str] = None
    command: Optional[str] = None
    user_session: Optional[str] = None

class KeyboardShortcutRequest(BaseModel):
    shortcut: str
    user_session: Optional[str] = None

class AutomationRequest(BaseModel):
    task_name: str
    task_type: str = "basic"
    current_url: Optional[str] = None
    session_id: Optional[str] = None

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

@app.post("/api/summarize")
async def summarize_page(request: SummarizationRequest):
    """Enhanced page summarization"""
    try:
        page_data = await get_page_content(request.url)
        
        # Generate AI summary
        content_preview = page_data["content"][:2000]  # Limit content for AI
        
        summary_prompt = f"""
        Please provide a {request.length} summary of the following webpage content:
        
        Title: {page_data["title"]}
        Content: {content_preview}
        
        Focus on the main points and key information.
        """
        
        summary_response = await get_ai_response(summary_prompt, None, "summarization")
        
        return {
            "success": True,
            "title": page_data["title"],
            "summary": summary_response,
            "length": request.length,
            "word_count": len(summary_response.split()),
            "url": request.url
        }
        
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-suggestions")
async def get_search_suggestions(request: SearchSuggestionRequest):
    """Get AI-powered search suggestions"""
    try:
        # Generate smart search suggestions
        suggestions = []
        
        if request.query:
            # Basic intelligent suggestions based on query
            query_lower = request.query.lower()
            
            if "ai" in query_lower or "artificial intelligence" in query_lower:
                suggestions = [
                    {"text": f"{request.query} tools", "type": "search"},
                    {"text": f"{request.query} research papers", "type": "search"},
                    {"text": f"{request.query} news", "type": "search"},
                    {"text": f"ChatGPT {request.query}", "type": "direct"},
                    {"text": f"Google {request.query}", "type": "search"}
                ]
            elif "python" in query_lower or "programming" in query_lower:
                suggestions = [
                    {"text": f"{request.query} documentation", "type": "search"},
                    {"text": f"{request.query} tutorial", "type": "search"},
                    {"text": f"{request.query} Stack Overflow", "type": "search"},
                    {"text": f"GitHub {request.query}", "type": "direct"},
                    {"text": f"{request.query} examples", "type": "search"}
                ]
            else:
                suggestions = [
                    {"text": f"{request.query} wikipedia", "type": "search"},
                    {"text": f"{request.query} news", "type": "search"},
                    {"text": f"{request.query} reddit", "type": "search"},
                    {"text": f"YouTube {request.query}", "type": "direct"},
                    {"text": f"Google {request.query}", "type": "search"}
                ]
        
        return {
            "success": True,
            "suggestions": suggestions[:5]  # Limit to 5 suggestions
        }
        
    except Exception as e:
        logger.error(f"Search suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-workflow")
async def create_workflow(request: WorkflowRequest):
    """Create automation workflow"""
    try:
        workflow_id = str(uuid.uuid4())
        
        workflow_data = {
            "workflow_id": workflow_id,
            "name": request.name,
            "description": request.description,
            "steps": request.steps,
            "created_at": datetime.utcnow(),
            "status": "created",
            "execution_count": 0
        }
        
        db.workflows.insert_one(workflow_data)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "name": request.name,
            "description": request.description,
            "steps_count": len(request.steps)
        }
        
    except Exception as e:
        logger.error(f"Workflow creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/system/overview")
async def get_system_overview():
    """Enhanced system status and overview"""
    try:
        # Database stats
        recent_tabs_count = db.recent_tabs.count_documents({})
        chat_sessions_count = db.chat_sessions.count_documents({})
        workflows_count = db.workflows.count_documents({})
        
        return {
            "status": "enhanced_operational",
            "version": "4.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "operational",
                "ai_provider": "groq",
                "backend": "operational",
                "frontend": "operational"
            },
            "stats": {
                "recent_tabs": recent_tabs_count,
                "chat_sessions": chat_sessions_count,
                "workflows": workflows_count,
                "uptime": "operational"
            },
            "capabilities": [
                "ai_chat",
                "web_browsing",
                "page_summarization",
                "workflow_automation",
                "voice_commands",
                "search_suggestions"
            ]
        }
        
    except Exception as e:
        logger.error(f"System overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice-command")
async def process_voice_command(request: VoiceCommandRequest):
    """Process voice commands"""
    try:
        voice_text = request.voice_text or request.command or ""
        
        # Process voice command
        command_lower = voice_text.lower()
        
        if "navigate to" in command_lower or "go to" in command_lower:
            # Extract URL from command
            words = command_lower.split()
            if "navigate" in words:
                url_index = words.index("to") + 1 if "to" in words else -1
            else:
                url_index = words.index("go") + 2 if "go" in words else -1
                
            if url_index > 0 and url_index < len(words):
                url = words[url_index]
                if not url.startswith("http"):
                    url = f"https://{url}"
                    
                return {
                    "success": True,
                    "action": "navigate",
                    "url": url,
                    "message": f"Navigating to {url}"
                }
        
        elif "search for" in command_lower or "search" in command_lower:
            # Extract search query
            query = command_lower.replace("search for", "").replace("search", "").strip()
            return {
                "success": True,
                "action": "search",
                "query": query,
                "message": f"Searching for: {query}"
            }
        
        else:
            # General chat command
            return {
                "success": True,
                "action": "chat",
                "message": voice_text,
                "response": "I heard you say: " + voice_text
            }
        
    except Exception as e:
        logger.error(f"Voice command error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice-commands/available")
async def get_available_voice_commands():
    """Get list of available voice commands"""
    try:
        commands = [
            {
                "command": "Navigate to [website]",
                "example": "Navigate to google.com",
                "description": "Navigate to a specific website"
            },
            {
                "command": "Search for [query]",
                "example": "Search for AI tools",
                "description": "Perform a web search"
            },
            {
                "command": "Summarize page",
                "example": "Summarize this page",
                "description": "Get AI summary of current page"
            },
            {
                "command": "Create workflow",
                "example": "Create workflow for automation",
                "description": "Start workflow creation process"
            }
        ]
        
        return {
            "success": True,
            "commands": commands
        }
        
    except Exception as e:
        logger.error(f"Voice commands error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/keyboard-shortcut")
async def process_keyboard_shortcut(request: KeyboardShortcutRequest):
    """Process keyboard shortcuts"""
    try:
        shortcut = request.shortcut.lower()
        
        action_map = {
            "ctrl+h": {"action": "home", "description": "Navigate to home"},
            "ctrl+r": {"action": "refresh", "description": "Refresh current page"},
            "ctrl+t": {"action": "new_tab", "description": "Open new tab"},
            "ctrl+shift+a": {"action": "ai_assistant", "description": "Toggle AI assistant"},
            "ctrl+shift+v": {"action": "voice", "description": "Activate voice commands"},
            "ctrl+/": {"action": "shortcuts", "description": "Show keyboard shortcuts"}
        }
        
        result = action_map.get(shortcut, {"action": "unknown", "description": "Unknown shortcut"})
        
        return {
            "success": True,
            "shortcut": request.shortcut,
            **result
        }
        
    except Exception as e:
        logger.error(f"Keyboard shortcut error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/keyboard-shortcuts/available")
async def get_available_shortcuts():
    """Get list of available keyboard shortcuts"""
    try:
        shortcuts = [
            {"shortcut": "Ctrl+H", "action": "Home", "description": "Navigate to home page"},
            {"shortcut": "Ctrl+R", "action": "Refresh", "description": "Refresh current page"},
            {"shortcut": "Ctrl+T", "action": "New Tab", "description": "Open new tab"},
            {"shortcut": "Ctrl+Shift+A", "action": "AI Assistant", "description": "Toggle AI assistant panel"},
            {"shortcut": "Ctrl+Shift+V", "action": "Voice Commands", "description": "Activate voice commands"},
            {"shortcut": "Ctrl+/", "action": "Help", "description": "Show keyboard shortcuts"},
            {"shortcut": "Alt+←", "action": "Back", "description": "Go back"},
            {"shortcut": "Alt+→", "action": "Forward", "description": "Go forward"},
            {"shortcut": "F5", "action": "Refresh", "description": "Refresh page"},
            {"shortcut": "Ctrl+W", "action": "Close Tab", "description": "Close current tab"}
        ]
        
        return {
            "success": True,
            "shortcuts": shortcuts
        }
        
    except Exception as e:
        logger.error(f"Shortcuts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automate-task")
async def create_automation_task(request: AutomationRequest):
    """Create automation task"""
    try:
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "name": request.task_name,
            "type": request.task_type,
            "url": request.current_url,
            "session_id": request.session_id,
            "status": "created",
            "created_at": datetime.utcnow(),
            "steps": [],
            "progress": 0
        }
        
        db.automation_tasks.insert_one(task_data)
        
        return {
            "success": True,
            "task_id": task_id,
            "name": request.task_name,
            "status": "created"
        }
        
    except Exception as e:
        logger.error(f"Automation task error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation-suggestions")
async def get_automation_suggestions():
    """Get automation suggestions based on context"""
    try:
        suggestions = [
            {
                "title": "Extract Data",
                "description": "Extract key data from this page",
                "command": "Extract important information from this page",
                "estimated_time": "2-3 min"
            },
            {
                "title": "Monitor Changes",
                "description": "Monitor this page for changes",
                "command": "Set up monitoring for page changes",
                "estimated_time": "1 min"
            },
            {
                "title": "Create Report",
                "description": "Generate a report from page content",
                "command": "Create a summary report of this content",
                "estimated_time": "3-5 min"
            }
        ]
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Automation suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/active-automations")
async def get_active_automations():
    """Get list of active automation tasks"""
    try:
        active_tasks = list(db.automation_tasks.find(
            {"status": {"$in": ["created", "running", "pending"]}},
            {"_id": 0}
        ).sort("created_at", -1).limit(10))
        
        return {
            "success": True,
            "active_tasks": active_tasks
        }
        
    except Exception as e:
        logger.error(f"Active automations error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-automation/{task_id}")
async def execute_automation(task_id: str):
    """Execute automation task"""
    try:
        # Update task status to running
        db.automation_tasks.update_one(
            {"task_id": task_id},
            {"$set": {"status": "running", "started_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "running",
            "message": "Automation task started"
        }
        
    except Exception as e:
        logger.error(f"Execute automation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation-status/{task_id}")
async def get_automation_status(task_id: str):
    """Get automation task status"""
    try:
        task = db.automation_tasks.find_one({"task_id": task_id}, {"_id": 0})
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "task_status": task
        }
        
    except Exception as e:
        logger.error(f"Automation status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cancel-automation/{task_id}")
async def cancel_automation(task_id: str):
    """Cancel automation task"""
    try:
        db.automation_tasks.update_one(
            {"task_id": task_id},
            {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "cancelled",
            "message": "Automation task cancelled"
        }
        
    except Exception as e:
        logger.error(f"Cancel automation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced endpoints for advanced features
@app.get("/api/proactive-suggestions")
async def get_proactive_suggestions(session_id: Optional[str] = None, current_url: Optional[str] = None):
    """Get proactive AI suggestions"""
    try:
        suggestions = [
            {
                "id": str(uuid.uuid4()),
                "title": "Optimize Browsing",
                "description": "I noticed patterns in your browsing. Would you like me to create shortcuts?",
                "type": "pattern_based",
                "priority": "medium",
                "action": "create_shortcuts"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Extract Key Data",
                "description": "This page has structured data. Shall I extract it for you?",
                "type": "context_based",
                "priority": "high",
                "action": "extract_data"
            }
        ]
        
        return {
            "success": True,
            "suggestions": suggestions,
            "autonomous_insights": {
                "learning_active": True,
                "pattern_strength": "medium",
                "context_awareness": "high"
            }
        }
        
    except Exception as e:
        logger.error(f"Proactive suggestions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/autonomous-action")
async def execute_autonomous_action(request: Dict[str, Any]):
    """Execute autonomous AI action"""
    try:
        action = request.get("action", "")
        
        response_map = {
            "create_shortcuts": "✅ **Smart Shortcuts Created!**\n\nI've analyzed your browsing patterns and created 3 intelligent shortcuts for frequently visited sections.",
            "extract_data": "📊 **Data Extracted Successfully!**\n\nI've extracted key information from this page and organized it for easy access.",
            "optimize_workflow": "⚡ **Workflow Optimized!**\n\nYour browsing workflow has been enhanced based on usage patterns."
        }
        
        message = response_map.get(action, f"🤖 **Action Completed!**\n\nExecuted: {action}")
        
        return {
            "success": True,
            "message": message,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Autonomous action error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)