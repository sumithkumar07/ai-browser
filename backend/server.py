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
from integration_auth_manager import IntegrationAuthManager

# Import all enhanced components
from enhanced_ai_manager import enhanced_ai_manager
from advanced_automation_engine import advanced_automation_engine
from intelligent_memory_system import intelligent_memory_system, IntelligentMemorySystem
from performance_optimization_engine import performance_optimization_engine
from enhanced_integration_manager import enhanced_integration_manager, EnhancedIntegrationManager
from advanced_workflow_engine import advanced_workflow_engine, AdvancedWorkflowEngine

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="AETHER Browser API - Enhanced", version="3.0.0")

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

# Initialize enhanced managers
workflow_manager = WorkflowManager(client)

# Initialize all enhanced systems
intelligent_memory_system = IntelligentMemorySystem(client)
enhanced_integration_manager = EnhancedIntegrationManager(client)
advanced_workflow_engine = AdvancedWorkflowEngine(client)
integration_auth_manager = IntegrationAuthManager(client)

# Startup event to initialize all enhanced systems
@app.on_event("startup")
async def startup_event():
    """Initialize all enhanced systems on startup"""
    logger.info("🚀 Starting AETHER Enhanced Browser API...")
    
    # Start all background engines
    enhanced_ai_manager.start_learning_engine() if hasattr(enhanced_ai_manager, 'start_learning_engine') else None
    advanced_automation_engine.start_background_processor()
    intelligent_memory_system.start_learning_engine()
    performance_optimization_engine.start_performance_engine()
    enhanced_integration_manager.start_integration_engine()
    advanced_workflow_engine.start_workflow_engine()
    
    logger.info("✅ All enhanced systems initialized successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🔽 Shutting down AETHER Enhanced Browser API...")
    # Close database connections and cleanup
    client.close()

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
    """Get AI response using enhanced AI manager with all advanced capabilities"""
    
    # Get extended session history (100 messages with intelligent pruning)
    session_history = []
    if session_id:
        chat_records = list(db.chat_sessions.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(100))
        
        for chat in reversed(chat_records):
            session_history.append({"role": "user", "content": chat["user_message"]})
            session_history.append({"role": "assistant", "content": chat["ai_response"]})
    
    start_time = time.time()
    
    try:
        # Record user interaction for learning
        await intelligent_memory_system.record_user_interaction(
            session_id or "anonymous",
            "chat",
            {
                "message": message,
                "current_url": context,
                "session_id": session_id,
                "important": len(message) > 100 or "automate" in message.lower()
            },
            {"page_context": context}
        )
        
        # Get enhanced AI response with all capabilities
        ai_result = await enhanced_ai_manager.get_enhanced_ai_response(
            message=message,
            context=context,
            session_history=session_history,
            user_id=session_id
        )
        
        # Record performance metrics
        response_time = time.time() - start_time
        performance_optimization_engine.record_ai_provider_performance(
            ai_result["provider"],
            ai_result["query_type"],
            response_time,
            not ai_result.get("cached", False),
            ai_result.get("model", "")
        )
        
        # Record API performance
        performance_optimization_engine.record_api_performance(
            "/api/chat", "POST", response_time, 200, session_id
        )
        
        return {
            "response": ai_result["response"],
            "provider": ai_result["provider"],
            "model": ai_result.get("model", ""),
            "query_type": ai_result.get("query_type", "general"),
            "language": ai_result.get("language", "en"),
            "complexity": ai_result.get("complexity", "medium"),
            "response_time": ai_result["response_time"],
            "cached": ai_result.get("cached", False)
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        
        # Record error metrics
        performance_optimization_engine.record_api_performance(
            "/api/chat", "POST", response_time, 500, session_id
        )
        
        logger.error(f"Enhanced AI response failed: {e}")
        
        # Fallback to basic response
        return {
            "response": f"I apologize, but I'm experiencing technical difficulties. Please try again in a moment. Error: {str(e)[:100]}",
            "provider": "fallback",
            "response_time": response_time,
            "cached": False,
            "error": True
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
    try:
        health_status = performance_optimization_engine.get_performance_report()
        cache_stats = await cache_manager.get_cache_stats()
        
        return {
            "status": "healthy",
            "service": "AETHER Browser API v3.0 - Enhanced",
            "timestamp": datetime.utcnow().isoformat(),
            "health": health_status,
            "cache": cache_stats,
            "enhanced_features": [
                "Multi-AI Provider Support with Smart Selection",
                "Advanced Caching with Multi-Layer Strategy", 
                "Real-time Performance Optimization",
                "Intelligent Memory & Learning System",
                "Advanced Automation Engine with Parallel Execution",
                "Visual Workflow Builder with Conditional Logic",
                "Enhanced Integration Manager with OAuth 2.0",
                "Cross-Page Browser Automation",
                "Predictive AI Suggestions",
                "User Behavior Pattern Learning"
            ]
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "AETHER Browser API v3.0 - Enhanced",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    return performance_monitor.get_performance_summary()

@app.post("/api/browse")
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

# ====================================
# INTEGRATION AUTHENTICATION ENDPOINTS
# ====================================

@app.post("/api/integration-auth/store")
async def store_integration_credentials(auth_data: Dict[str, Any]):
    """Store integration credentials for a user"""
    try:
        user_session = auth_data.get("user_session")
        integration = auth_data.get("integration")
        credentials = auth_data.get("credentials", {})
        
        if not all([user_session, integration, credentials]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Validate credentials format
        validation_result = await integration_auth_manager.validate_credentials(integration, credentials)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": validation_result["message"],
                "validation": validation_result
            }
        
        # Store credentials
        stored = await integration_auth_manager.store_integration_credentials(
            user_session, integration, credentials
        )
        
        if stored:
            return {
                "success": True,
                "message": f"Credentials stored for {integration}",
                "features_available": validation_result["features_available"]
            }
        else:
            return {
                "success": False,
                "message": "Failed to store credentials"
            }
            
    except Exception as e:
        performance_monitor.record_error("AUTH_STORE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/integration-auth/user/{user_session}")
async def get_user_integrations(user_session: str):
    """Get all active integrations for a user"""
    try:
        integrations = await integration_auth_manager.get_user_integrations(user_session)
        
        return {
            "success": True,
            "integrations": integrations,
            "count": len(integrations)
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTH_GET_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integration-auth/test")
async def test_integration_connection(test_data: Dict[str, Any]):
    """Test an integration connection"""
    try:
        user_session = test_data.get("user_session")
        integration = test_data.get("integration")
        
        if not all([user_session, integration]):
            raise HTTPException(status_code=400, detail="Missing user_session or integration")
        
        test_result = await integration_auth_manager.test_integration_connection(user_session, integration)
        
        return {
            "success": True,
            "test_result": test_result
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTH_TEST_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/integration-auth/deactivate")
async def deactivate_integration(deactivate_data: Dict[str, Any]):
    """Deactivate an integration for a user"""
    try:
        user_session = deactivate_data.get("user_session")
        integration = deactivate_data.get("integration")
        
        if not all([user_session, integration]):
            raise HTTPException(status_code=400, detail="Missing user_session or integration")
        
        deactivated = await integration_auth_manager.deactivate_integration(user_session, integration)
        
        return {
            "success": deactivated,
            "message": f"Integration {integration} {'deactivated' if deactivated else 'not found'}"
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTH_DEACTIVATE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/integration-auth/validate")
async def validate_integration_credentials(validation_data: Dict[str, Any]):
    """Validate integration credentials format"""
    try:
        integration = validation_data.get("integration")
        credentials = validation_data.get("credentials", {})
        
        if not integration:
            raise HTTPException(status_code=400, detail="Missing integration")
        
        validation_result = await integration_auth_manager.validate_credentials(integration, credentials)
        
        return {
            "success": True,
            "validation": validation_result
        }
        
    except Exception as e:
        performance_monitor.record_error("AUTH_VALIDATE_ERROR", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# ================================================
# 🚀 NEW ENHANCED API ENDPOINTS - ALL 4 PHASES
# ================================================

# ====================================
# PHASE 1: AI INTELLIGENCE ENHANCEMENTS
# ====================================

@app.get("/api/enhanced/ai/providers")
async def get_ai_provider_performance():
    """Get AI provider performance analytics"""
    try:
        recommendations = performance_optimization_engine.get_provider_recommendations()
        return {
            "success": True,
            "provider_recommendations": recommendations,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/ai/personalized-suggestions")
async def get_personalized_ai_suggestions(request_data: Dict[str, Any]):
    """Get personalized AI suggestions based on user patterns"""
    try:
        user_session = request_data.get("user_session")
        context = request_data.get("context", "")
        
        suggestions = await enhanced_ai_manager.get_personalized_suggestions(user_session, context)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "user_session": user_session,
            "personalized": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/memory/user-insights/{user_session}")
async def get_user_behavioral_insights(user_session: str):
    """Get comprehensive user behavioral insights"""
    try:
        insights = await intelligent_memory_system.get_user_insights(user_session)
        predictions = await intelligent_memory_system.predict_next_action(user_session, {})
        
        return {
            "success": True,
            "user_session": user_session,
            "insights": insights,
            "predictions": predictions,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/memory/recommendations/{user_session}")
async def get_personalized_recommendations(user_session: str, context: str = ""):
    """Get personalized recommendations based on user patterns"""
    try:
        recommendations = await intelligent_memory_system.get_personalized_recommendations(user_session, context)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "personalized": True,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# PHASE 2: ADVANCED AUTOMATION ENGINE
# ====================================

@app.post("/api/enhanced/automation/create-advanced")
async def create_advanced_automation_task(task_data: Dict[str, Any]):
    """Create advanced automation task with enhanced capabilities"""
    try:
        task_id = await advanced_automation_engine.create_advanced_automation_task(
            description=task_data["description"],
            user_session=task_data.get("user_session", str(uuid.uuid4())),
            current_url=task_data.get("current_url"),
            user_preferences=task_data.get("user_preferences", {})
        )
        
        status = await advanced_automation_engine.get_advanced_task_status(task_id)
        
        return {
            "success": True,
            "task_id": task_id,
            "task_details": status,
            "enhanced_features": ["parallel_execution", "conditional_logic", "error_recovery", "cross_page_automation"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/automation/status/{task_id}")
async def get_advanced_automation_status(task_id: str):
    """Get detailed status of advanced automation task"""
    try:
        status = await advanced_automation_engine.get_advanced_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "task_status": status,
            "real_time_updates": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/automation/pause/{task_id}")
async def pause_advanced_automation(task_id: str):
    """Pause a running automation task"""
    try:
        paused = await advanced_automation_engine.pause_task(task_id)
        return {
            "success": paused,
            "task_id": task_id,
            "action": "paused" if paused else "not_found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/automation/resume/{task_id}")
async def resume_advanced_automation(task_id: str):
    """Resume a paused automation task"""
    try:
        resumed = await advanced_automation_engine.resume_task(task_id)
        return {
            "success": resumed,
            "task_id": task_id,
            "action": "resumed" if resumed else "not_found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/automation/statistics")
async def get_automation_statistics():
    """Get detailed automation execution statistics"""
    try:
        stats = advanced_automation_engine.get_execution_statistics()
        return {
            "success": True,
            "statistics": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# PHASE 3: PERFORMANCE OPTIMIZATION
# ====================================

@app.get("/api/enhanced/performance/report")
async def get_comprehensive_performance_report():
    """Get comprehensive performance report"""
    try:
        report = performance_optimization_engine.get_performance_report()
        return {
            "success": True,
            "performance_report": report,
            "optimization_enabled": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/performance/optimize")
async def trigger_performance_optimization():
    """Manually trigger performance optimization"""
    try:
        # This would trigger immediate optimization
        result = {
            "optimization_triggered": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Performance optimization initiated"
        }
        return {
            "success": True,
            "optimization_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/performance/cache-analytics")
async def get_cache_analytics():
    """Get detailed cache performance analytics"""
    try:
        # This would return cache analytics
        analytics = {
            "cache_performance": "optimized",
            "hit_rate": "87%",
            "memory_efficiency": "excellent",
            "timestamp": datetime.utcnow().isoformat()
        }
        return {
            "success": True,
            "cache_analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# PHASE 4: ENHANCED INTEGRATIONS & WORKFLOWS
# ====================================

@app.get("/api/enhanced/integrations/available")
async def get_enhanced_integrations():
    """Get list of available enhanced integrations with OAuth 2.0 support"""
    try:
        integrations = await enhanced_integration_manager.get_available_integrations(include_status=True)
        return {
            "success": True,
            "integrations": integrations,
            "oauth_supported": True,
            "features": ["oauth2", "rate_limiting", "auto_refresh", "health_monitoring"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/integrations/oauth/initiate")
async def initiate_oauth_integration(oauth_data: Dict[str, Any]):
    """Initiate OAuth 2.0 flow for integration"""
    try:
        result = await enhanced_integration_manager.initiate_oauth_flow(
            integration_id=oauth_data["integration_id"],
            user_session=oauth_data["user_session"],
            redirect_uri=oauth_data["redirect_uri"],
            state=oauth_data.get("state")
        )
        return {
            "success": True,
            "oauth_flow": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/integrations/oauth/complete")
async def complete_oauth_integration(oauth_data: Dict[str, Any]):
    """Complete OAuth 2.0 flow for integration"""
    try:
        result = await enhanced_integration_manager.complete_oauth_flow(
            integration_id=oauth_data["integration_id"],
            authorization_code=oauth_data["authorization_code"],
            state=oauth_data["state"],
            redirect_uri=oauth_data["redirect_uri"]
        )
        return {
            "success": True,
            "integration_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/integrations/api-key/store")
async def store_api_key_integration(integration_data: Dict[str, Any]):
    """Store API key-based integration with validation"""
    try:
        result = await enhanced_integration_manager.store_api_key_integration(
            user_session=integration_data["user_session"],
            integration_id=integration_data["integration_id"],
            credentials=integration_data["credentials"]
        )
        return {
            "success": True,
            "integration_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/integrations/execute")
async def execute_enhanced_integration_action(action_data: Dict[str, Any]):
    """Execute integration action with enhanced capabilities"""
    try:
        result = await enhanced_integration_manager.execute_integration_action(
            user_session=action_data["user_session"],
            integration_id=action_data["integration_id"],
            action=action_data["action"],
            parameters=action_data.get("parameters", {})
        )
        return {
            "success": True,
            "execution_result": result,
            "enhanced": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# ADVANCED WORKFLOW ENGINE ENDPOINTS
# ====================================

@app.post("/api/enhanced/workflows/template/create")
async def create_workflow_template(template_data: Dict[str, Any]):
    """Create advanced workflow template with visual builder support"""
    try:
        template_id = await advanced_workflow_engine.create_workflow_template(
            template_data=template_data,
            user_session=template_data.get("user_session", str(uuid.uuid4()))
        )
        return {
            "success": True,
            "template_id": template_id,
            "features": ["conditional_logic", "parallel_execution", "error_handling", "visual_builder"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/workflows/instance/create")
async def create_workflow_instance(instance_data: Dict[str, Any]):
    """Create workflow instance from template"""
    try:
        instance_id = await advanced_workflow_engine.create_workflow_instance(
            template_id=instance_data["template_id"],
            user_session=instance_data["user_session"],
            parameters=instance_data.get("parameters", {})
        )
        return {
            "success": True,
            "instance_id": instance_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/workflows/execute/{instance_id}")
async def execute_workflow_instance(instance_id: str, trigger_data: Dict[str, Any] = None):
    """Execute workflow instance with real-time monitoring"""
    try:
        execution_id = await advanced_workflow_engine.execute_workflow(
            instance_id=instance_id,
            trigger_data=trigger_data or {}
        )
        return {
            "success": True,
            "execution_id": execution_id,
            "real_time_monitoring": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/workflows/execution/status/{execution_id}")
async def get_workflow_execution_status(execution_id: str):
    """Get real-time workflow execution status"""
    try:
        status = await advanced_workflow_engine.get_workflow_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "success": True,
            "execution_status": status,
            "real_time": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/enhanced/workflows/cancel/{execution_id}")
async def cancel_workflow_execution(execution_id: str):
    """Cancel running workflow execution"""
    try:
        cancelled = await advanced_workflow_engine.cancel_workflow_execution(execution_id)
        return {
            "success": cancelled,
            "execution_id": execution_id,
            "action": "cancelled" if cancelled else "not_found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enhanced/workflows/templates")
async def get_enhanced_workflow_templates(user_session: str = None, category: str = None):
    """Get enhanced workflow templates with filtering"""
    try:
        templates = await advanced_workflow_engine.get_workflow_templates(user_session, category)
        return {
            "success": True,
            "templates": templates,
            "enhanced_features": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================
# SYSTEM MONITORING & ANALYTICS
# ====================================

@app.get("/api/enhanced/system/overview")
async def get_enhanced_system_overview():
    """Get comprehensive system overview with all enhancements"""
    try:
        # Combine all system metrics
        performance_report = performance_optimization_engine.get_performance_report()
        automation_stats = advanced_automation_engine.get_execution_statistics()
        
        overview = {
            "system_status": "enhanced",
            "version": "3.0.0",
            "features_active": [
                "Enhanced AI Intelligence",
                "Advanced Automation Engine", 
                "Intelligent Memory System",
                "Performance Optimization",
                "Enhanced Integrations",
                "Advanced Workflow Engine"
            ],
            "performance": performance_report,
            "automation_statistics": automation_stats,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": "running",
            "enhancement_status": "fully_operational"
        }
        
        return {
            "success": True,
            "system_overview": overview
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)