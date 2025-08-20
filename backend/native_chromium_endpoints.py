"""
Native Chromium API Endpoints
FastAPI endpoints for native browser control
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import logging
from datetime import datetime

from native_chromium_engine import get_native_chromium_engine

logger = logging.getLogger(__name__)

# Pydantic models for native chromium
class CreateBrowserSessionRequest(BaseModel):
    user_session: str
    user_agent: Optional[str] = None

class NavigateRequest(BaseModel):
    session_id: str
    url: str

class ExecuteJavaScriptRequest(BaseModel):
    session_id: str
    script: str
    args: Optional[List[Any]] = []

class ScreenshotRequest(BaseModel):
    session_id: str
    full_page: Optional[bool] = False
    quality: Optional[int] = 80

class ClickElementRequest(BaseModel):
    session_id: str
    selector: str
    timeout: Optional[int] = 5000

class TypeTextRequest(BaseModel):
    session_id: str
    selector: str
    text: str
    clear: Optional[bool] = True

class GetContentRequest(BaseModel):
    session_id: str
    include_html: Optional[bool] = False

def setup_native_chromium_endpoints(app: FastAPI):
    """Setup all native chromium endpoints"""
    
    @app.post("/api/native/create-session")
    async def create_browser_session(request: CreateBrowserSessionRequest):
        """Create a new native browser session"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            # Generate session ID
            session_id = f"native_{request.user_session}_{str(uuid.uuid4())[:8]}"
            
            result = await engine.create_browser_session(session_id, request.user_agent)
            
            if result['success']:
                return {
                    "success": True,
                    "session_id": session_id,
                    "capabilities": result['capabilities'],
                    "message": "Native browser session created"
                }
            else:
                raise HTTPException(status_code=500, detail=result.get('error', 'Failed to create session'))
                
        except Exception as e:
            logger.error(f"Create session error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/navigate")
    async def navigate_to_url(request: NavigateRequest):
        """Navigate to a specific URL using native browser"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.navigate_to_url(request.session_id, request.url)
            
            if result['success']:
                return {
                    "success": True,
                    "url": result['url'],
                    "title": result['title'],
                    "load_time": result['load_time'],
                    "security": result['security'],
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Navigation failed'))
                
        except Exception as e:
            logger.error(f"Navigate error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/execute-js")
    async def execute_javascript(request: ExecuteJavaScriptRequest):
        """Execute JavaScript in native browser context"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.execute_javascript(request.session_id, request.script, request.args)
            
            if result['success']:
                return {
                    "success": True,
                    "result": result['result'],
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'JavaScript execution failed'))
                
        except Exception as e:
            logger.error(f"Execute JS error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/screenshot")
    async def take_screenshot(request: ScreenshotRequest):
        """Take a screenshot using native browser"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.take_screenshot(request.session_id, request.full_page, request.quality)
            
            if result['success']:
                return {
                    "success": True,
                    "screenshot": result['screenshot'],
                    "format": result['format'],
                    "full_page": result['full_page'],
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Screenshot failed'))
                
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/click")
    async def click_element(request: ClickElementRequest):
        """Click an element using native browser"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.click_element(request.session_id, request.selector, request.timeout)
            
            if result['success']:
                return {
                    "success": True,
                    "action": result['action'],
                    "selector": result['selector'],
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Click failed'))
                
        except Exception as e:
            logger.error(f"Click error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/type")
    async def type_text(request: TypeTextRequest):
        """Type text using native browser"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.type_text(request.session_id, request.selector, request.text, request.clear)
            
            if result['success']:
                return {
                    "success": True,
                    "action": result['action'],
                    "selector": result['selector'],
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Type failed'))
                
        except Exception as e:
            logger.error(f"Type error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/get-content")
    async def get_page_content(request: GetContentRequest):
        """Get page content using native browser"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.get_page_content(request.session_id, request.include_html)
            
            if result['success']:
                return {
                    "success": True,
                    "url": result['url'],
                    "title": result['title'],
                    "text_content": result['text_content'],
                    "html_content": result.get('html_content'),
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Get content failed'))
                
        except Exception as e:
            logger.error(f"Get content error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/native/performance/{session_id}")
    async def get_performance_metrics(session_id: str):
        """Get performance metrics for a session"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.get_performance_metrics(session_id)
            
            if result['success']:
                return {
                    "success": True,
                    "metrics": result['metrics'],
                    "session_info": result['session_info'],
                    "timestamp": result['timestamp']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Get performance failed'))
                
        except Exception as e:
            logger.error(f"Get performance error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/native/session/{session_id}")
    async def close_browser_session(session_id: str):
        """Close a native browser session"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            result = await engine.close_session(session_id)
            
            if result['success']:
                return {
                    "success": True,
                    "message": result['message']
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Close session failed'))
                
        except Exception as e:
            logger.error(f"Close session error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.websocket("/ws/native/{session_id}")
    async def websocket_browser_control(websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time browser control"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                await websocket.close(code=1000, reason="Native Chromium Engine not available")
                return
            
            await engine.handle_websocket(websocket, session_id)
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.close(code=1000, reason=str(e))
            except:
                pass

    @app.get("/api/native/status")
    async def get_native_browser_status():
        """Get native browser engine status"""
        try:
            engine = get_native_chromium_engine()
            
            if not engine:
                return {
                    "available": False,
                    "status": "not_initialized",
                    "message": "Native Chromium Engine not available"
                }
            
            return {
                "available": True,
                "status": "operational",
                "initialized": engine.is_initialized,
                "active_sessions": len(engine.active_sessions),
                "capabilities": [
                    "native_navigation",
                    "javascript_execution", 
                    "screenshot_capture",
                    "devtools_protocol",
                    "performance_monitoring",
                    "security_analysis",
                    "websocket_control"
                ],
                "message": "Native Chromium Engine operational"
            }
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {
                "available": False,
                "status": "error",
                "error": str(e)
            }

    # Enhanced browser automation endpoints
    @app.post("/api/native/automation/smart-click")
    async def smart_click_element(request: dict):
        """Smart click with AI element detection"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            session_id = request.get('session_id')
            description = request.get('description', '')  # Natural language description
            
            # Use AI to find element by description
            smart_selector_script = f"""
            (() => {{
                // Find elements that match the description: {description}
                const elements = Array.from(document.querySelectorAll('*')).filter(el => {{
                    const text = el.textContent?.toLowerCase() || '';
                    const placeholder = el.placeholder?.toLowerCase() || '';
                    const title = el.title?.toLowerCase() || '';
                    const description_lower = '{description}'.toLowerCase();
                    
                    return text.includes(description_lower) || 
                           placeholder.includes(description_lower) || 
                           title.includes(description_lower);
                }});
                
                if (elements.length > 0) {{
                    return elements[0];
                }} else {{
                    return null;
                }}
            }})()
            """
            
            # Execute the smart selector
            element_result = await engine.execute_javascript(session_id, smart_selector_script)
            
            if element_result['success'] and element_result['result']:
                # Click the found element
                click_result = await engine.execute_javascript(session_id, "arguments[0].click()", [element_result['result']])
                return {
                    "success": True,
                    "action": "smart_click",
                    "description": description,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Could not find element matching description"
                }
                
        except Exception as e:
            logger.error(f"Smart click error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/native/automation/extract-data")
    async def extract_page_data(request: dict):
        """Extract structured data from page"""
        try:
            engine = get_native_chromium_engine()
            if not engine:
                raise HTTPException(status_code=500, detail="Native Chromium Engine not available")
            
            session_id = request.get('session_id')
            data_type = request.get('data_type', 'general')  # links, images, text, forms, etc.
            
            extraction_scripts = {
                'links': '''
                    Array.from(document.links).map(link => ({
                        text: link.textContent.trim(),
                        url: link.href,
                        target: link.target
                    }))
                ''',
                'images': '''
                    Array.from(document.images).map(img => ({
                        src: img.src,
                        alt: img.alt,
                        width: img.width,
                        height: img.height
                    }))
                ''',
                'forms': '''
                    Array.from(document.forms).map(form => ({
                        action: form.action,
                        method: form.method,
                        inputs: Array.from(form.elements).map(el => ({
                            name: el.name,
                            type: el.type,
                            placeholder: el.placeholder
                        }))
                    }))
                ''',
                'general': '''
                    ({
                        title: document.title,
                        url: location.href,
                        headings: Array.from(document.querySelectorAll('h1,h2,h3')).map(h => ({
                            level: h.tagName,
                            text: h.textContent.trim()
                        })),
                        paragraphs: Array.from(document.querySelectorAll('p')).slice(0, 10).map(p => p.textContent.trim()),
                        links_count: document.links.length,
                        images_count: document.images.length
                    })
                '''
            }
            
            script = extraction_scripts.get(data_type, extraction_scripts['general'])
            result = await engine.execute_javascript(session_id, script)
            
            if result['success']:
                return {
                    "success": True,
                    "data_type": data_type,
                    "extracted_data": result['result'],
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(status_code=400, detail=result.get('error', 'Data extraction failed'))
                
        except Exception as e:
            logger.error(f"Extract data error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("🔥 Native Chromium API endpoints configured")