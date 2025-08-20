"""
Enhanced Native API Routes - Complete Integration
Integrates all advanced features:
- Computer Use API with AI vision
- Agentic Memory System
- Natural Language Programming
- Ultimate Simplicity Interface
- Performance Engine
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# Import system components - will be initialized at startup
computer_use_api = None
memory_system = None  
aether_programming = None
native_chromium_engine = None


# Enhanced API Models
class UltimateCommandRequest(BaseModel):
    """Single natural language command for ultimate simplicity"""
    command: str
    session_id: str
    user_id: str = "anonymous"
    context: Optional[Dict[str, Any]] = None
    auto_remember: bool = True
    performance_mode: str = "balanced"  # fast, balanced, thorough


class WorkflowRequest(BaseModel):
    """Natural language workflow creation request"""
    instruction: str
    user_id: str = "anonymous"
    session_id: str
    auto_execute: bool = False
    context: Optional[Dict[str, Any]] = None


class SmartInteractionRequest(BaseModel):
    """AI-powered interaction request"""
    session_id: str
    action_type: str  # smart_click, smart_type, smart_extract
    description: str
    value: Optional[str] = None
    timeout: int = 10000
    user_id: str = "anonymous"


class MemoryQueryRequest(BaseModel):
    """Memory system query request"""
    user_id: str
    query_type: str  # patterns, predictions, insights, stats
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


# Initialize router
enhanced_router = APIRouter(prefix="/api/enhanced", tags=["Enhanced Native API"])


@enhanced_router.post("/ultimate-command")
async def execute_ultimate_command(request: UltimateCommandRequest):
    """
    🚀 ULTIMATE SIMPLICITY INTERFACE
    Single natural language input that can do anything
    """
    try:
        start_time = time.time()
        
        # Get native browser session
        session = await native_chromium_engine.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Browser session not found")
        
        page = session["page"]
        
        # Record interaction start in memory
        if request.auto_remember:
            await memory_system.record_interaction(request.session_id, {
                "user_id": request.user_id,
                "action_type": "ultimate_command",
                "target": request.command,
                "context": request.context or {},
                "success": False,  # Will update after execution
                "duration": 0.0,
                "metadata": {"performance_mode": request.performance_mode}
            })
        
        # Get memory predictions for context
        predictions = await memory_system.predict_user_needs(request.session_id, {
            "user_id": request.user_id,
            "current_command": request.command,
            **(request.context or {})
        })
        
        # Determine execution strategy based on command complexity
        execution_strategy = await _determine_execution_strategy(request.command, request.performance_mode)
        
        result = {"success": False, "error": "Unknown execution path"}
        
        if execution_strategy == "direct_computer_use":
            # Direct computer use for simple commands
            result = await computer_use_api.execute_natural_language_command(page, request.command)
            
        elif execution_strategy == "workflow_generation":
            # Generate and execute workflow for complex commands
            workflow = await aether_programming.generate(request.command, request.user_id)
            result = await aether_programming.execute(workflow, page, request.context)
            result["workflow_id"] = workflow.workflow_id
            result["workflow_name"] = workflow.name
            
        elif execution_strategy == "smart_interaction":
            # Use AI-powered smart interactions
            if "click" in request.command.lower():
                target = request.command.lower().replace("click", "").strip()
                result = await computer_use_api.smart_click(page, target)
            elif "type" in request.command.lower():
                parts = request.command.split(" in ")
                if len(parts) == 2:
                    text = parts[0].replace("type", "").strip().strip('"\'')
                    field = parts[1].strip()
                    result = await computer_use_api.smart_type(page, field, text)
                else:
                    result = await computer_use_api.execute_natural_language_command(page, request.command)
            else:
                result = await computer_use_api.execute_natural_language_command(page, request.command)
        
        # Update memory with final result
        if request.auto_remember:
            await memory_system.record_interaction(request.session_id, {
                "user_id": request.user_id,
                "action_type": "ultimate_command",
                "target": request.command,
                "context": request.context or {},
                "success": result.get("success", False),
                "duration": (time.time() - start_time) * 1000,
                "metadata": {
                    "performance_mode": request.performance_mode,
                    "execution_strategy": execution_strategy,
                    "result": result
                }
            })
        
        # Add enhanced response data
        response = {
            **result,
            "execution_strategy": execution_strategy,
            "response_time": (time.time() - start_time) * 1000,
            "predictions": predictions.get("predictions", []),
            "session_id": request.session_id,
            "command": request.command,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return response
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": request.command,
            "response_time": (time.time() - start_time) * 1000 if 'start_time' in locals() else 0,
            "timestamp": datetime.utcnow().isoformat()
        }


@enhanced_router.post("/create-workflow")
async def create_natural_language_workflow(request: WorkflowRequest):
    """
    🧠 NATURAL LANGUAGE PROGRAMMING
    Create workflows from natural language instructions
    """
    try:
        # Generate workflow from instruction
        workflow = await aether_programming.generate(request.instruction, request.user_id)
        
        # Auto-execute if requested
        execution_result = None
        if request.auto_execute:
            session = await native_chromium_engine.get_session(request.session_id)
            if session:
                page = session["page"]
                execution_result = await aether_programming.execute(workflow, page, request.context)
        
        # Record in memory
        await memory_system.record_interaction(request.session_id, {
            "user_id": request.user_id,
            "action_type": "workflow_creation",
            "target": request.instruction,
            "context": request.context or {},
            "success": True,
            "duration": 0.0,
            "metadata": {
                "workflow_id": workflow.workflow_id,
                "auto_executed": request.auto_execute
            }
        })
        
        return {
            "success": True,
            "workflow": {
                "id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "type": step.step_type.value,
                        "description": step.description,
                        "parameters": step.parameters
                    }
                    for step in workflow.steps
                ],
                "tags": workflow.tags,
                "created_at": workflow.created_at.isoformat()
            },
            "execution_result": execution_result,
            "instruction": request.instruction
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "instruction": request.instruction
        }


@enhanced_router.post("/smart-interaction")
async def smart_ai_interaction(request: SmartInteractionRequest):
    """
    🎯 AI-POWERED SMART INTERACTIONS
    Use AI vision and element detection for precise interactions
    """
    try:
        start_time = time.time()
        
        # Get browser session
        session = await native_chromium_engine.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Browser session not found")
        
        page = session["page"]
        
        # Execute based on action type
        if request.action_type == "smart_click":
            result = await computer_use_api.smart_click(page, request.description)
            
        elif request.action_type == "smart_type":
            if not request.value:
                raise HTTPException(status_code=400, detail="Value required for smart_type")
            result = await computer_use_api.smart_type(page, request.description, request.value)
            
        elif request.action_type == "smart_extract":
            # Get page content and analyze
            screenshot = await computer_use_api.capture_screenshot(page)
            elements = await computer_use_api.analyze_screenshot_with_ai(screenshot, request.description)
            
            result = {
                "success": True,
                "extracted_elements": [
                    {
                        "x": elem.x,
                        "y": elem.y,
                        "width": elem.width,
                        "height": elem.height,
                        "text": elem.text,
                        "type": elem.element_type,
                        "confidence": elem.confidence,
                        "description": elem.description
                    }
                    for elem in elements
                ],
                "screenshot": screenshot
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action type: {request.action_type}")
        
        # Record interaction
        await memory_system.record_interaction(request.session_id, {
            "user_id": request.user_id,
            "action_type": f"smart_{request.action_type}",
            "target": request.description,
            "context": {"value": request.value} if request.value else {},
            "success": result.get("success", False),
            "duration": (time.time() - start_time) * 1000,
            "metadata": {"ai_powered": True}
        })
        
        return {
            **result,
            "action_type": request.action_type,
            "response_time": (time.time() - start_time) * 1000,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action_type": request.action_type,
            "timestamp": datetime.utcnow().isoformat()
        }


@enhanced_router.post("/memory-query")
async def query_agentic_memory(request: MemoryQueryRequest):
    """
    🧠 AGENTIC MEMORY SYSTEM
    Query the comprehensive memory system for patterns, predictions, and insights
    """
    try:
        if request.query_type == "patterns":
            patterns = await memory_system.semantic.get_user_patterns(request.user_id)
            return {
                "success": True,
                "patterns": [
                    {
                        "id": pattern.pattern_id,
                        "type": pattern.pattern_type,
                        "description": pattern.description,
                        "confidence": pattern.confidence,
                        "frequency": pattern.frequency,
                        "last_seen": pattern.last_seen.isoformat(),
                        "success_rate": pattern.success_rate
                    }
                    for pattern in patterns
                ]
            }
            
        elif request.query_type == "predictions":
            predictions = await memory_system.predict_user_needs(
                request.session_id or str(uuid.uuid4()),
                {
                    "user_id": request.user_id,
                    **(request.context or {})
                }
            )
            return {
                "success": True,
                "predictions": predictions
            }
            
        elif request.query_type == "insights":
            patterns = await memory_system.semantic.get_user_patterns(request.user_id)
            insights = await memory_system.semantic.generate_insights(request.user_id, patterns)
            return {
                "success": True,
                "insights": insights
            }
            
        elif request.query_type == "stats":
            stats = await memory_system.get_memory_stats(request.user_id)
            return {
                "success": True,
                "stats": stats
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {request.query_type}")
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query_type": request.query_type
        }


@enhanced_router.get("/performance-metrics")
async def get_performance_metrics():
    """
    📊 PERFORMANCE ENGINE
    Get comprehensive performance metrics across all systems
    """
    try:
        # Computer Use API metrics
        computer_use_metrics = computer_use_api.get_performance_metrics()
        
        # Natural Language Programming metrics
        programming_stats = aether_programming.get_execution_stats()
        
        # Native browser metrics
        browser_metrics = await native_chromium_engine.get_performance_metrics()
        
        return {
            "success": True,
            "metrics": {
                "computer_use_api": computer_use_metrics,
                "natural_language_programming": programming_stats,
                "native_browser": browser_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@enhanced_router.get("/workflows")
async def list_workflows(user_id: Optional[str] = None):
    """List all workflows, optionally filtered by user"""
    try:
        workflows = aether_programming.list_workflows(user_id)
        
        return {
            "success": True,
            "workflows": [
                {
                    "id": workflow.workflow_id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "created_by": workflow.created_by,
                    "created_at": workflow.created_at.isoformat(),
                    "tags": workflow.tags,
                    "success_rate": workflow.success_rate,
                    "execution_count": workflow.execution_count,
                    "average_duration": workflow.average_duration,
                    "steps_count": len(workflow.steps)
                }
                for workflow in workflows
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@enhanced_router.post("/workflow/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, session_id: str, context: Optional[Dict[str, Any]] = None):
    """Execute an existing workflow"""
    try:
        # Get workflow
        workflow = aether_programming.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get browser session
        session = await native_chromium_engine.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Browser session not found")
        
        # Execute workflow
        page = session["page"]
        result = await aether_programming.execute(workflow, page, context)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "execution_result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow_id": workflow_id
        }


@enhanced_router.post("/workflow/{workflow_id}/modify")
async def modify_workflow(workflow_id: str, modification: str):
    """Modify an existing workflow using natural language"""
    try:
        updated_workflow = await aether_programming.modify_workflow(workflow_id, modification)
        
        if not updated_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow": {
                "id": updated_workflow.workflow_id,
                "name": updated_workflow.name,
                "description": updated_workflow.description,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "type": step.step_type.value,
                        "description": step.description,
                        "parameters": step.parameters
                    }
                    for step in updated_workflow.steps
                ],
                "modification_applied": modification
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow_id": workflow_id
        }


@enhanced_router.get("/workflow/{workflow_id}/suggestions")
async def get_workflow_improvements(workflow_id: str):
    """Get AI-powered suggestions for workflow improvements"""
    try:
        suggestions = await aether_programming.suggest_workflow_improvements(workflow_id)
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "suggestions": suggestions
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "workflow_id": workflow_id
        }


async def _determine_execution_strategy(command: str, performance_mode: str = "balanced") -> str:
    """Determine the best execution strategy for a command"""
    command_lower = command.lower()
    
    # Fast mode - prefer direct execution
    if performance_mode == "fast":
        return "direct_computer_use"
    
    # Complex workflow indicators
    workflow_indicators = [
        "and then", "after that", "followed by", "next", "step by step",
        "first", "second", "then", "finally", "workflow", "automation",
        "process", "sequence", "multiple", "several"
    ]
    
    if any(indicator in command_lower for indicator in workflow_indicators):
        return "workflow_generation"
    
    # Smart interaction indicators
    smart_indicators = [
        "find", "locate", "identify", "detect", "search for",
        "click on", "type in", "fill", "extract", "get data"
    ]
    
    if any(indicator in command_lower for indicator in smart_indicators):
        return "smart_interaction"
    
    # Default to direct computer use for simple commands
    return "direct_computer_use"


# Background task for memory system initialization
@enhanced_router.on_event("startup")
async def initialize_enhanced_systems():
    """Initialize all enhanced systems on startup"""
    try:
        await memory_system.initialize()
        print("🚀 Enhanced Native API systems initialized")
    except Exception as e:
        print(f"❌ Error initializing enhanced systems: {e}")