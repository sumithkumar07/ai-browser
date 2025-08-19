# 🚀 ENHANCED AETHER SERVER - SINGLE NATURAL LANGUAGE COMMANDS
# Complete Fellou.ai-level capabilities integrated seamlessly

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
import asyncio

# Import enhanced automation engine
from enhanced_automation import nlp_processor, task_executor, Task

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced Pydantic models
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

# Enhanced AI client initialization
groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

# Database connection
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client.aether_browser

async def get_enhanced_ai_response(message: str, context: Optional[str] = None, 
                                 session_id: Optional[str] = None,
                                 enable_automation: bool = True) -> Dict[str, Any]:
    """Enhanced AI response with automation capabilities"""
    
    try:
        # Check if this is an automation command
        if enable_automation and await is_automation_command(message):
            return await handle_automation_command(message, context, session_id)
        
        # Regular AI chat response
        system_prompt = """You are AETHER AI, an advanced browser assistant with powerful automation capabilities.

You can execute complex tasks through single natural language commands, including:
- Multi-site research and data compilation
- Job applications across multiple platforms  
- Form filling and submissions
- Price monitoring and alerts
- Content extraction and analysis
- Social media automation
- Workflow chaining and conditional logic

For automation tasks, respond with enthusiasm about executing the task.
For regular questions, provide helpful, concise answers.
Always be proactive and suggest automation opportunities."""
        
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
        
        ai_response = chat_completion.choices[0].message.content
        
        return {
            "response": ai_response,
            "type": "chat",
            "automation_available": True,
            "suggestions": await get_automation_suggestions(message, context)
        }
        
    except Exception as e:
        logger.error(f"Enhanced AI response error: {str(e)}")
        return {
            "response": "I apologize for the technical issue. Please try again later.",
            "type": "error",
            "automation_available": False
        }

async def is_automation_command(message: str) -> bool:
    """Detect if message is an automation command"""
    
    automation_keywords = [
        "research", "across", "sites", "apply", "jobs", "fill", "forms",
        "monitor", "price", "extract", "data", "scrape", "compile",
        "create report", "batch", "submit", "automate", "find and",
        "search and", "then", "simultaneously", "multiple"
    ]
    
    message_lower = message.lower()
    
    # Check for automation patterns
    for keyword in automation_keywords:
        if keyword in message_lower:
            return True
    
    # Check for quantity indicators (suggesting batch operations)
    import re
    if re.search(r'\d+\s*(sites?|jobs?|forms?|pages?|applications?)', message_lower):
        return True
    
    return False

async def handle_automation_command(message: str, context: Optional[str], 
                                  session_id: Optional[str]) -> Dict[str, Any]:
    """Handle automation command and execute in background"""
    
    try:
        # Parse command into executable task
        task_context = {
            "session_id": session_id or str(uuid.uuid4()),
            "current_url": context,
            "timestamp": datetime.utcnow()
        }
        
        task = await nlp_processor.parse_command(message, task_context)
        
        # Execute task in background
        task_id = await task_executor.execute_task(task)
        
        # Generate encouraging response
        response_messages = [
            f"🚀 **Task Started!** I'm now executing your request: '{message}'\n\n",
            f"**Task ID:** {task_id}\n",
            f"**Estimated Steps:** {len(task.steps)}\n", 
            f"**Execution Mode:** Background (won't interrupt your browsing)\n\n",
            "I'll work on this intelligently while you continue browsing. ",
            "You'll get updates as I make progress, and I'll notify you when complete!\n\n",
            "💡 **What I'm doing:**\n"
        ]
        
        for i, step in enumerate(task.steps[:3]):  # Show first 3 steps
            response_messages.append(f"{i+1}. {step.get('action', 'Processing').replace('_', ' ').title()}\n")
        
        if len(task.steps) > 3:
            response_messages.append(f"... and {len(task.steps)-3} more steps\n")
            
        response_messages.append(f"\n🔄 **Status:** Running in background - continue browsing normally!")
        
        return {
            "response": "".join(response_messages),
            "type": "automation",
            "task_id": task_id,
            "background_execution": True,
            "estimated_duration": f"{len(task.steps) * 30} seconds"
        }
        
    except Exception as e:
        logger.error(f"Automation command error: {str(e)}")
        return {
            "response": f"I encountered an issue setting up that automation: {str(e)}. Let me try a different approach.",
            "type": "error"
        }

async def get_automation_suggestions(message: str, context: Optional[str]) -> List[Dict]:
    """Get contextual automation suggestions"""
    
    suggestions = []
    
    if context and "job" in context.lower():
        suggestions.append({
            "text": "Apply to similar jobs across multiple job sites",
            "command": "Apply to jobs matching my profile on LinkedIn, Indeed, and Glassdoor"
        })
    
    if "research" in message.lower():
        suggestions.append({
            "text": "Research this topic across 5 authoritative sites",
            "command": f"Research {message.split('research')[1] if 'research' in message else 'this topic'} across 5 sites and create summary"
        })
    
    if context and any(word in context.lower() for word in ["form", "contact", "apply"]):
        suggestions.append({
            "text": "Fill similar forms across multiple sites",
            "command": "Fill contact forms on related websites with my information"
        })
    
    # Always include these general suggestions
    suggestions.extend([
        {
            "text": "Monitor price changes for products",
            "command": "Monitor price changes for [product] and alert me of deals"
        },
        {
            "text": "Extract data and create report",
            "command": "Extract key information from this page and similar sites, then create comparison report"
        }
    ])
    
    return suggestions[:3]  # Limit to 3 suggestions

# Keep all existing server code and add these enhanced endpoints
# [Previous server.py content remains the same, just import and use enhanced functions]

# Enhanced endpoint that replaces the existing chat endpoint
async def enhanced_chat_with_ai(chat_data: EnhancedChatMessage):
    """Enhanced AI chat with automation capabilities"""
    try:
        session_id = chat_data.session_id or str(uuid.uuid4())
        
        # Get page context if URL provided
        context = None
        if chat_data.current_url:
            page_data = await get_page_content(chat_data.current_url)
            context = f"Page: {page_data['title']}\nContent: {page_data['content']}"
        
        # Get enhanced AI response with automation support
        ai_result = await get_enhanced_ai_response(
            chat_data.message, 
            context, 
            session_id,
            chat_data.enable_automation
        )
        
        # Store chat session with automation info
        chat_record = {
            "session_id": session_id,
            "user_message": chat_data.message,
            "ai_response": ai_result["response"],
            "current_url": chat_data.current_url,
            "timestamp": datetime.utcnow(),
            "automation_triggered": ai_result.get("type") == "automation",
            "task_id": ai_result.get("task_id")
        }
        
        db.chat_sessions.insert_one(chat_record)
        
        return {
            "response": ai_result["response"],
            "session_id": session_id,
            "automation_triggered": ai_result.get("type") == "automation",
            "task_id": ai_result.get("task_id"),
            "suggestions": ai_result.get("suggestions", [])
        }
        
    except Exception as e:
        logger.error(f"Enhanced chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper function from original server (keeping it)
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

# Export the enhanced function for use in main server
__all__ = ['enhanced_chat_with_ai', 'task_executor', 'nlp_processor']