from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from pymongo import MongoClient
import uuid
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import json
import asyncio
import time
import logging

# Import our enhanced modules after loading environment
from ai_manager import ai_manager, AIProvider
from cache_manager import cache_manager
from performance_monitor import performance_monitor, monitor_performance
from automation_engine import automation_engine
from workflow_manager import workflow_manager, WorkflowManager
from integration_manager import integration_manager

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="AETHER Browser API", version="2.0.0")

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection with connection pooling
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL, maxPoolSize=50, minPoolSize=10)
db = client.aether_browser

# Initialize workflow manager
workflow_manager = WorkflowManager(client)

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

# Enhanced helper functions
async def get_page_content_with_cache(url: str) -> Dict[str, Any]:
    """Fetch and parse web page content with caching"""
    
    # Try cache first
    cached_content = await cache_manager.get_cached_page_content(url)
    if cached_content:
        return cached_content
    
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={
                'User-Agent': 'AETHER Browser/2.0 (+http://aether.browser)'
            }
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Enhanced content extraction
            # Remove script, style, and other non-content elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
                
            title = soup.title.string if soup.title else url
            
            # Extract main content more intelligently
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
                "content": text[:8000],  # Increased content size
                "meta_description": meta_description,
                "meta_keywords": meta_keywords,
                "url": url,
                "word_count": len(text.split()),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # Cache the content
            await cache_manager.cache_page_content(url, content_data)
            
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

async def get_enhanced_ai_response(message: str, context: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
    """Get AI response using enhanced AI manager"""
    
    # Get session history with extended memory (50 messages)
    session_history = []
    if session_id:
        chat_records = list(db.chat_sessions.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(50))
        
        for chat in reversed(chat_records):
            session_history.append({"role": "user", "content": chat["user_message"]})
            session_history.append({"role": "assistant", "content": chat["ai_response"]})
    
    start_time = time.time()
    
    try:
        response, provider = await ai_manager.get_smart_response(
            message=message,
            context=context,
            session_history=session_history
        )
        
        # Record performance metrics
        response_time = time.time() - start_time
        performance_monitor.record_ai_provider_usage(
            provider.value, 
            "general",  # Could enhance to detect query type
            response_time, 
            True
        )
        
        return {
            "response": response,
            "provider": provider.value,
            "response_time": response_time,
            "cached": False
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        performance_monitor.record_ai_provider_usage("unknown", "general", response_time, False)
        performance_monitor.record_error("AI_ERROR", str(e))
        
        return {
            "response": f"I apologize, but I'm experiencing technical difficulties: {str(e)}",
            "provider": "error",
            "response_time": response_time,
            "cached": False
        }

async def generate_page_summary(url: str, content: str):
    """Generate AI-powered page summary in background"""
    try:
        summary = await ai_manager.summarize_webpage(content, "medium")
        
        # Store summary in database
        summary_data = {
            "url": url,
            "summary": summary,
            "generated_at": datetime.utcnow(),
            "content_length": len(content)
        }
        
        # Update or insert summary
        db.page_summaries.replace_one(
            {"url": url}, 
            summary_data, 
            upsert=True
        )
        
    except Exception as e:
        performance_monitor.record_error("SUMMARY_ERROR", str(e))

# Enhanced API Routes
@app.get("/api/health")
async def health_check():
    """Enhanced health check with performance metrics"""
    health_status = performance_monitor.get_health_status()
    cache_stats = await cache_manager.get_cache_stats()
    
    return {
        "status": "healthy",
        "service": "AETHER Browser API v2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "health": health_status,
        "cache": cache_stats,
        "features": [
            "Multi-AI Provider Support",
            "Smart Caching",
            "Performance Monitoring",
            "Extended Memory",
            "Smart Model Selection",
            "Automation Engine",
            "Workflow Management"
        ]
    }

@app.get("/api/performance")
@monitor_performance
async def get_performance_metrics():
    """Get detailed performance metrics"""
    return performance_monitor.get_performance_summary()

@app.post("/api/browse")
@monitor_performance
async def browse_page_enhanced(session: BrowsingSession):
    """Enhanced web page fetching with caching and AI analysis"""
    try:
        # Get page content with caching
        page_data = await get_page_content_with_cache(session.url)
        
        # Store in recent tabs with enhanced metadata
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
        
        # Generate AI-powered page summary in background
        if not page_data.get("error", False):
            asyncio.create_task(generate_page_summary(session.url, page_data["content"]))
        
        return {
            "success": True,
            "page_data": page_data,
            "tab_id": tab_data["id"],
            "cached": "extracted_at" in page_data
        }
        
    except Exception as e:
        performance_monitor.record_error("BROWSE_ERROR", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
@monitor_performance
async def chat_with_enhanced_ai(chat_data: ChatMessage):
    """Enhanced chat with multi-model AI support and automation detection"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Check if this is an automation command
        automation_keywords = ["apply to", "automate", "find and", "save to", "send to", "schedule", "create workflow"]
        is_automation_command = any(keyword in chat_data.message.lower() for keyword in automation_keywords)
        
        if is_automation_command:
            # Handle as automation request
            try:
                # Create automation task
                task_id = await automation_engine.create_automation_task(
                    description=chat_data.message,
                    user_session=session_id,
                    current_url=chat_data.current_url
                )
                
                # Get task details
                task_status = await automation_engine.get_task_status(task_id)
                
                # Create automation response
                automation_response = f"""🤖 **Automation Task Created**

**Task:** {task_status['description']}
**Complexity:** {task_status['complexity'].title()}
**Estimated Time:** {task_status['estimated_duration'] // 60} minutes
**Steps:** {task_status['total_steps']}

Would you like me to start this automation? 

[**▶️ Start Automation**] [**✏️ Customize**] [**❌ Cancel**]

*Task ID: {task_id[:8]}*"""

                # Store enhanced chat session
                chat_record = {
                    "session_id": session_id,
                    "user_message": chat_data.message,
                    "ai_response": automation_response,
                    "ai_provider": "automation_engine",
                    "current_url": chat_data.current_url,
                    "response_time": 0.5,
                    "language": chat_data.language,
                    "automation_task_id": task_id,
                    "message_type": "automation_offer",
                    "timestamp": datetime.utcnow()
                }
                
                db.chat_sessions.insert_one(chat_record)
                
                return {
                    "response": automation_response,
                    "session_id": session_id,
                    "provider": "automation_engine",
                    "response_time": 0.5,
                    "automation_task_id": task_id,
                    "message_type": "automation_offer"
                }
                
            except Exception as automation_error:
                logger.error(f"Automation creation failed: {automation_error}")
                # Fall back to regular AI response
                is_automation_command = False
        
        if not is_automation_command:
            # Handle as regular AI chat
            
            # Get page context if URL provided
            context = None
            if chat_data.current_url:
                page_data = await get_page_content_with_cache(chat_data.current_url)
                if not page_data.get("error", False):
                    context = f"Page: {page_data['title']}\nDescription: {page_data.get('meta_description', '')}\nContent: {page_data['content'][:3000]}"
            
            # Get AI response with enhanced capabilities
            ai_result = await get_enhanced_ai_response(
                chat_data.message, 
                context=context,
                session_id=session_id
            )
            
            # Check if we should suggest automations
            suggestions = []
            if chat_data.current_url:
                suggestions = await automation_engine.suggest_automations(chat_data.current_url)
            
            # Add automation suggestions to response if relevant
            enhanced_response = ai_result["response"]
            if suggestions and len(suggestions) > 0:
                enhanced_response += f"\n\n💡 **Quick Actions Available:**\n"
                for i, suggestion in enumerate(suggestions[:2], 1):
                    enhanced_response += f"\n{i}. **{suggestion['title']}** - {suggestion['description']} (~{suggestion['estimated_time']})"
                enhanced_response += f"\n\n*Say something like \"{suggestions[0]['command']}\" to get started!*"
            
            # Store enhanced chat session
            chat_record = {
                "session_id": session_id,
                "user_message": chat_data.message,
                "ai_response": enhanced_response,
                "ai_provider": ai_result["provider"],
                "current_url": chat_data.current_url,
                "response_time": ai_result["response_time"],
                "language": chat_data.language,
                "automation_suggestions": suggestions,
                "message_type": "conversation",
                "timestamp": datetime.utcnow()
            }
            
            db.chat_sessions.insert_one(chat_record)
            
            return {
                "response": enhanced_response,
                "session_id": session_id,
                "provider": ai_result["provider"],
                "response_time": ai_result["response_time"],
                "automation_suggestions": suggestions,
                "message_type": "conversation"
            }
        
    except Exception as e:
        performance_monitor.record_error("CHAT_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-tabs")
@monitor_performance
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
@monitor_performance
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
                ai_result = await get_enhanced_ai_response(prompt)
                ai_response = ai_result["response"]
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

@app.post("/api/summarize")
@monitor_performance
async def summarize_page(request: SummarizationRequest):
    """Summarize webpage content"""
    try:
        # Get page content
        page_data = await get_page_content_with_cache(request.url)
        
        if page_data.get("error", False):
            raise HTTPException(status_code=400, detail="Could not fetch page content")
        
        # Generate summary
        summary = await ai_manager.summarize_webpage(page_data["content"], request.length)
        
        return {
            "url": request.url,
            "title": page_data["title"],
            "summary": summary,
            "length": request.length,
            "word_count": page_data.get("word_count", 0)
        }
        
    except Exception as e:
        performance_monitor.record_error("SUMMARIZE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-suggestions")
@monitor_performance
async def get_search_suggestions(request: SearchSuggestionRequest):
    """Get AI-powered search suggestions"""
    try:
        suggestions = await ai_manager.suggest_search_query(request.query)
        
        return {
            "original_query": request.query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        performance_monitor.record_error("SEARCH_SUGGESTIONS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/clear-history")
@monitor_performance
async def clear_browsing_history():
    """Clear browsing history and chat sessions"""
    try:
        db.recent_tabs.delete_many({})
        db.chat_sessions.delete_many({})
        db.page_summaries.delete_many({})
        
        # Clear cache
        await cache_manager.clear_pattern("*")
        
        return {"success": True, "message": "History and cache cleared"}
    except Exception as e:
        performance_monitor.record_error("CLEAR_HISTORY_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# NEW AUTOMATION & WORKFLOW ENDPOINTS
# ====================================

@app.post("/api/automate-task")
@monitor_performance
async def create_automation_task(task_data: ChatMessage):
    """Create a new automation task from natural language description"""
    try:
        # Create automation task
        task_id = await automation_engine.create_automation_task(
            description=task_data.message,
            user_session=task_data.session_id or str(uuid.uuid4()),
            current_url=task_data.current_url
        )
        
        # Get task details
        task_status = await automation_engine.get_task_status(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "task_details": task_status,
            "message": f"Automation task created: {task_status['description']}"
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTOMATION_CREATE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-automation/{task_id}")
@monitor_performance
async def execute_automation(task_id: str, background_tasks: BackgroundTasks):
    """Execute an automation task in the background"""
    try:
        # Add task execution to background
        background_tasks.add_task(automation_engine.execute_automation_task, task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "started",
            "message": "Automation task started in background"
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTOMATION_EXECUTE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation-status/{task_id}")
@monitor_performance
async def get_automation_status(task_id: str):
    """Get current status of an automation task"""
    try:
        status = await automation_engine.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "task_status": status
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTOMATION_STATUS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cancel-automation/{task_id}")
@monitor_performance
async def cancel_automation(task_id: str):
    """Cancel a running automation task"""
    try:
        cancelled = await automation_engine.cancel_task(task_id)
        
        if not cancelled:
            raise HTTPException(status_code=404, detail="Task not found or already completed")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Automation task cancelled"
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTOMATION_CANCEL_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/active-automations")
@monitor_performance
async def get_active_automations():
    """Get list of all active automation tasks"""
    try:
        active_tasks = await automation_engine.get_active_tasks()
        
        return {
            "success": True,
            "active_tasks": active_tasks,
            "count": len(active_tasks)
        }
        
    except Exception as e:
        performance_monitor.record_error("ACTIVE_AUTOMATIONS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/automation-suggestions")
@monitor_performance
async def get_automation_suggestions(current_url: str = ""):
    """Get AI-powered automation suggestions for current context"""
    try:
        suggestions = await automation_engine.suggest_automations(current_url)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "context_url": current_url
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTOMATION_SUGGESTIONS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# WORKFLOW MANAGEMENT ENDPOINTS
# ====================================

@app.get("/api/workflow-templates")
@monitor_performance
async def get_workflow_templates(category: str = None):
    """Get available workflow templates"""
    try:
        templates = await workflow_manager.get_workflow_templates(category)
        
        return {
            "success": True,
            "templates": templates,
            "category": category
        }
        
    except Exception as e:
        performance_monitor.record_error("WORKFLOW_TEMPLATES_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create-workflow")
@monitor_performance  
async def create_workflow_endpoint(workflow_data: Dict[str, Any]):
    """Create a new workflow from a template"""
    try:
        workflow_id = await workflow_manager.create_workflow(
            user_session=workflow_data.get("user_session", str(uuid.uuid4())),
            template_id=workflow_data.get("template_id"),
            parameters=workflow_data.get("parameters", {})
        )
        
        workflow_status = await workflow_manager.get_workflow_status(workflow_id)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "workflow_details": workflow_status
        }
        
    except Exception as e:
        performance_monitor.record_error("WORKFLOW_CREATE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow-status/{workflow_id}")
@monitor_performance
async def get_workflow_status(workflow_id: str):
    """Get current status of a workflow"""
    try:
        status = await workflow_manager.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow_status": status
        }
        
    except Exception as e:
        performance_monitor.record_error("WORKFLOW_STATUS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user-workflows/{user_session}")
@monitor_performance
async def get_user_workflows(user_session: str, status: str = None):
    """Get workflows for a specific user"""
    try:
        workflows = await workflow_manager.get_user_workflows(user_session, status)
        
        return {
            "success": True,
            "workflows": workflows,
            "user_session": user_session
        }
        
    except Exception as e:
        performance_monitor.record_error("USER_WORKFLOWS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/personalized-suggestions/{user_session}")
@monitor_performance
async def get_personalized_suggestions(user_session: str, current_url: str = ""):
    """Get personalized workflow suggestions"""
    try:
        suggestions = await workflow_manager.get_personalized_suggestions(user_session, current_url)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "personalized": True
        }
        
    except Exception as e:
        performance_monitor.record_error("PERSONALIZED_SUGGESTIONS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# INTEGRATION ENDPOINTS
# ====================================

@app.get("/api/integrations")
@monitor_performance
async def get_available_integrations():
    """Get list of available integrations"""
    try:
        integrations = await integration_manager.get_available_integrations()
        
        return {
            "success": True,
            "integrations": integrations
        }
        
    except Exception as e:
        performance_monitor.record_error("INTEGRATIONS_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integration-action")
@monitor_performance
async def execute_integration_action(action_data: Dict[str, Any]):
    """Execute an action using a specific integration"""
    try:
        result = await integration_manager.execute_integration_action(
            integration_id=action_data.get("integration_id"),
            action=action_data.get("action"),
            parameters=action_data.get("parameters", {})
        )
        
        return {
            "success": True,
            "integration_result": result
        }
        
    except Exception as e:
        performance_monitor.record_error("INTEGRATION_ACTION_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)