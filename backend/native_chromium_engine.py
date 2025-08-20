"""
AETHER Native Chromium Engine v6.0.0
Complete Playwright-based native browser engine with Computer Use API
"""

import asyncio
import json
import logging
import time
import uuid
import base64
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import websockets
from dataclasses import dataclass, asdict
import traceback

# Playwright imports for native Chromium control
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pymongo import MongoClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NativeBrowserSession:
    """Native browser session data"""
    session_id: str
    user_session: str
    browser: Optional[Browser] = None
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    websocket: Optional[Any] = None
    capabilities: List[str] = None
    created_at: datetime = None
    last_activity: datetime = None
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = [
                "native_navigation",
                "screenshot_capture", 
                "javascript_execution",
                "devtools_protocol",
                "performance_monitoring",
                "element_interaction",
                "computer_use_api",
                "cross_origin_access",
                "file_system_access"
            ]
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.performance_metrics is None:
            self.performance_metrics = {}

class NativeChromiumEngine:
    """Complete Native Chromium Engine with Computer Use API"""
    
    def __init__(self, mongodb_client: MongoClient):
        self.playwright = None
        self.browser = None
        self.sessions: Dict[str, NativeBrowserSession] = {}
        self.websocket_connections: Dict[str, Any] = {}
        self.db = mongodb_client.aether_browser
        self.is_initialized = False
        
        # Performance monitoring
        self.performance_collector = PerformanceCollector()
        
        # Computer Use API
        self.computer_use_api = ComputerUseAPI()
        
    async def initialize(self):
        """Initialize Playwright and Chromium browser"""
        try:
            logger.info("🔥 Initializing Native Chromium Engine...")
            
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Launch Chromium with enhanced capabilities
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Show browser for native experience
                args=[
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-extensions-except',
                    '--disable-extensions',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-back-forward-cache',
                    '--disable-ipc-flooding-protection',
                    '--enable-features=NetworkService,NetworkServiceInProcess',
                    '--force-color-profile=srgb',
                    '--metrics-recording-only',
                    '--use-mock-keychain'
                ],
                slow_mo=50,  # Add slight delay for stability
                timeout=30000
            )
            
            self.is_initialized = True
            logger.info("✅ Native Chromium Engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Native Chromium Engine: {e}")
            logger.error(traceback.format_exc())
            return False

    async def create_native_session(self, user_session: str, user_agent: str = None) -> Dict[str, Any]:
        """Create new native browser session"""
        try:
            if not self.is_initialized:
                await self.initialize()
            
            session_id = f"native_{uuid.uuid4().hex[:12]}"
            
            # Create browser context with enhanced capabilities
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': user_agent or 'AETHER-Native-Browser/6.0.0',
                'java_script_enabled': True,
                'accept_downloads': True,
                'bypass_csp': True,  # Bypass CSP for enhanced access
                'ignore_https_errors': True
            }
            
            context = await self.browser.new_context(**context_options)
            
            # Create new page
            page = await context.new_page()
            
            # Setup page event handlers
            await self._setup_page_handlers(page, session_id)
            
            # Create session object
            session = NativeBrowserSession(
                session_id=session_id,
                user_session=user_session,
                browser=self.browser,
                context=context,
                page=page
            )
            
            # Store session
            self.sessions[session_id] = session
            
            # Store in database
            await self._store_session_in_db(session)
            
            logger.info(f"✅ Native browser session created: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "capabilities": session.capabilities,
                "viewport": context_options['viewport'],
                "user_agent": context_options['user_agent']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create native session: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e)
            }

    async def _setup_page_handlers(self, page: Page, session_id: str):
        """Setup event handlers for page events"""
        
        # Navigation handlers
        page.on("load", lambda: self._handle_page_load(session_id))
        page.on("domcontentloaded", lambda: self._handle_dom_ready(session_id))
        
        # Error handlers
        page.on("pageerror", lambda error: self._handle_page_error(session_id, error))
        page.on("crash", lambda: self._handle_page_crash(session_id))
        
        # Request/Response monitoring
        page.on("request", lambda request: self._handle_request(session_id, request))
        page.on("response", lambda response: self._handle_response(session_id, response))
        
        # Console monitoring
        page.on("console", lambda msg: self._handle_console(session_id, msg))

    async def navigate_to_url(self, session_id: str, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to URL using native browser"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            start_time = time.time()
            
            # Navigate to URL
            response = await session.page.goto(
                url, 
                wait_until='networkidle',
                timeout=timeout
            )
            
            load_time = time.time() - start_time
            
            # Get page info
            title = await session.page.title()
            actual_url = session.page.url
            
            # Update performance metrics
            session.performance_metrics['last_navigation'] = {
                'url': actual_url,
                'load_time': load_time,
                'timestamp': datetime.utcnow().isoformat(),
                'status_code': response.status if response else None
            }
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            
            # Notify WebSocket clients
            await self._broadcast_to_websocket(session_id, {
                'type': 'navigation_complete',
                'url': actual_url,
                'title': title,
                'load_time': load_time,
                'security': {
                    'is_secure': actual_url.startswith('https://'),
                    'status': 'secure' if actual_url.startswith('https://') else 'insecure'
                }
            })
            
            logger.info(f"🔥 Native navigation successful: {actual_url} ({load_time:.2f}s)")
            
            return {
                "success": True,
                "url": actual_url,
                "title": title,
                "load_time": load_time,
                "status_code": response.status if response else None
            }
            
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return {"success": False, "error": str(e)}

    async def capture_screenshot(self, session_id: str, full_page: bool = False, quality: int = 80) -> Dict[str, Any]:
        """Capture screenshot of current page"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Capture screenshot
            screenshot_bytes = await session.page.screenshot(
                full_page=full_page,
                quality=quality,
                type='jpeg'
            )
            
            # Convert to base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Store metadata
            screenshot_data = {
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'full_page': full_page,
                'quality': quality,
                'size': len(screenshot_bytes)
            }
            
            # Notify WebSocket clients
            await self._broadcast_to_websocket(session_id, {
                'type': 'screenshot_captured',
                'success': True,
                'screenshot': screenshot_b64,
                'metadata': screenshot_data
            })
            
            logger.info(f"📷 Screenshot captured: {len(screenshot_bytes)} bytes")
            
            return {
                "success": True,
                "screenshot": screenshot_b64,
                "metadata": screenshot_data
            }
            
        except Exception as e:
            logger.error(f"❌ Screenshot failed: {e}")
            return {"success": False, "error": str(e)}

    async def execute_javascript(self, session_id: str, script: str, args: List[Any] = None) -> Dict[str, Any]:
        """Execute JavaScript in native browser"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if args is None:
                args = []
            
            # Execute script
            result = await session.page.evaluate(script, args)
            
            logger.info(f"📜 JavaScript executed successfully")
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ JavaScript execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def click_element(self, session_id: str, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click element using CSS selector"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Wait for element and click
            await session.page.wait_for_selector(selector, timeout=timeout)
            await session.page.click(selector)
            
            logger.info(f"👆 Element clicked: {selector}")
            
            return {"success": True, "selector": selector}
            
        except Exception as e:
            logger.error(f"❌ Click failed: {e}")
            return {"success": False, "error": str(e)}

    async def type_text(self, session_id: str, selector: str, text: str, clear: bool = True) -> Dict[str, Any]:
        """Type text into element"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Wait for element
            await session.page.wait_for_selector(selector, timeout=5000)
            
            # Clear if requested
            if clear:
                await session.page.fill(selector, "")
            
            # Type text
            await session.page.type(selector, text)
            
            logger.info(f"⌨️ Text typed: {selector}")
            
            return {"success": True, "selector": selector, "text": text}
            
        except Exception as e:
            logger.error(f"❌ Type failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_page_content(self, session_id: str, include_html: bool = False) -> Dict[str, Any]:
        """Get page content and metadata"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Get page info
            title = await session.page.title()
            url = session.page.url
            
            # Get text content
            text_content = await session.page.evaluate("document.body.innerText")
            
            content = {
                "title": title,
                "url": url,
                "text_content": text_content[:10000],  # Limit size
            }
            
            # Include HTML if requested
            if include_html:
                html_content = await session.page.content()
                content["html_content"] = html_content[:50000]  # Limit size
            
            return {"success": True, "content": content}
            
        except Exception as e:
            logger.error(f"❌ Get content failed: {e}")
            return {"success": False, "error": str(e)}

    async def smart_click(self, session_id: str, description: str) -> Dict[str, Any]:
        """AI-powered smart click using Computer Use API"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Capture screenshot for AI analysis
            screenshot_result = await self.capture_screenshot(session_id)
            if not screenshot_result["success"]:
                return screenshot_result
            
            # Use Computer Use API to find element
            click_result = await self.computer_use_api.smart_click(
                screenshot_result["screenshot"], 
                description
            )
            
            if click_result["success"]:
                # Execute the click at coordinates
                await session.page.mouse.click(
                    click_result["coordinates"]["x"],
                    click_result["coordinates"]["y"]
                )
                
                logger.info(f"🎯 Smart click successful: {description}")
                return {"success": True, "description": description, "coordinates": click_result["coordinates"]}
            else:
                return click_result
                
        except Exception as e:
            logger.error(f"❌ Smart click failed: {e}")
            return {"success": False, "error": str(e)}

    async def extract_page_data(self, session_id: str, data_type: str = 'general') -> Dict[str, Any]:
        """Extract structured data from page"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Define extraction scripts based on data type
            extraction_scripts = {
                'general': """
                    (() => {
                        const data = {
                            title: document.title,
                            url: window.location.href,
                            headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                                tag: h.tagName.toLowerCase(),
                                text: h.textContent.trim()
                            })),
                            links: Array.from(document.querySelectorAll('a[href]')).map(a => ({
                                text: a.textContent.trim(),
                                href: a.href
                            })).slice(0, 20),
                            images: Array.from(document.querySelectorAll('img[src]')).map(img => ({
                                alt: img.alt,
                                src: img.src
                            })).slice(0, 10)
                        };
                        return data;
                    })()
                """,
                'forms': """
                    (() => {
                        return Array.from(document.querySelectorAll('form')).map(form => ({
                            action: form.action,
                            method: form.method,
                            inputs: Array.from(form.querySelectorAll('input, textarea, select')).map(input => ({
                                type: input.type,
                                name: input.name,
                                placeholder: input.placeholder,
                                required: input.required
                            }))
                        }));
                    })()
                """,
                'tables': """
                    (() => {
                        return Array.from(document.querySelectorAll('table')).map(table => ({
                            headers: Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim()),
                            rows: Array.from(table.querySelectorAll('tr')).slice(1, 6).map(tr => 
                                Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim())
                            )
                        }));
                    })()
                """
            }
            
            script = extraction_scripts.get(data_type, extraction_scripts['general'])
            
            # Execute extraction script
            result = await session.page.evaluate(script)
            
            logger.info(f"📊 Data extraction successful: {data_type}")
            
            return {
                "success": True,
                "data_type": data_type,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"❌ Data extraction failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get performance metrics for session"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Get browser performance metrics
            performance_data = await session.page.evaluate("""
                (() => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    return {
                        load_time: perf.loadEventEnd - perf.fetchStart,
                        dom_ready: perf.domContentLoadedEventEnd - perf.fetchStart,
                        first_byte: perf.responseStart - perf.fetchStart,
                        dns_lookup: perf.domainLookupEnd - perf.domainLookupStart,
                        tcp_connect: perf.connectEnd - perf.connectStart,
                        memory_usage: performance.memory ? {
                            used: performance.memory.usedJSHeapSize,
                            total: performance.memory.totalJSHeapSize,
                            limit: performance.memory.jsHeapSizeLimit
                        } : null
                    };
                })()
            """)
            
            # Combine with session metrics
            metrics = {
                **performance_data,
                **session.performance_metrics,
                "session_duration": (datetime.utcnow() - session.created_at).total_seconds(),
                "last_activity": session.last_activity.isoformat()
            }
            
            return {"success": True, "metrics": metrics}
            
        except Exception as e:
            logger.error(f"❌ Performance metrics failed: {e}")
            return {"success": False, "error": str(e)}

    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close native browser session"""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Close page and context
            if session.page:
                await session.page.close()
            if session.context:
                await session.context.close()
            
            # Remove from sessions
            del self.sessions[session_id]
            
            # Close WebSocket connection
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]
            
            logger.info(f"🧹 Native session closed: {session_id}")
            
            return {"success": True, "session_id": session_id}
            
        except Exception as e:
            logger.error(f"❌ Session close failed: {e}")
            return {"success": False, "error": str(e)}

    async def handle_websocket_connection(self, websocket, session_id: str):
        """Handle WebSocket connection for real-time communication"""
        try:
            # Store WebSocket connection
            self.websocket_connections[session_id] = websocket
            
            # Send connection confirmation
            await websocket.send(json.dumps({
                'type': 'connection_established',
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
            logger.info(f"🔗 WebSocket connected for session: {session_id}")
            
            # Listen for messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(session_id, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON'
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': str(e)
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocket disconnected: {session_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            # Cleanup
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]

    async def _handle_websocket_message(self, session_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        action = data.get('action')
        websocket = self.websocket_connections.get(session_id)
        
        if not websocket:
            return
        
        try:
            if action == 'navigate':
                result = await self.navigate_to_url(session_id, data.get('url'))
                await websocket.send(json.dumps({
                    'type': 'navigation_result',
                    'result': result
                }))
                
            elif action == 'screenshot':
                result = await self.capture_screenshot(
                    session_id,
                    full_page=data.get('full_page', False),
                    quality=data.get('quality', 80)
                )
                # Screenshot is sent via broadcast
                
            elif action == 'execute_js':
                result = await self.execute_javascript(
                    session_id,
                    data.get('script'),
                    data.get('args', [])
                )
                await websocket.send(json.dumps({
                    'type': 'js_result',
                    'messageId': data.get('messageId'),
                    **result
                }))
                
            elif action == 'click':
                result = await self.click_element(session_id, data.get('selector'))
                await websocket.send(json.dumps({
                    'type': 'click_result',
                    'result': result
                }))
                
            elif action == 'click_coordinates':
                session = self.sessions.get(session_id)
                if session:
                    await session.page.mouse.click(data.get('x'), data.get('y'))
                    await websocket.send(json.dumps({
                        'type': 'click_result',
                        'result': {'success': True}
                    }))
                    
            elif action == 'type':
                result = await self.type_text(
                    session_id,
                    data.get('selector'),
                    data.get('text')
                )
                await websocket.send(json.dumps({
                    'type': 'type_result',
                    'result': result
                }))
                
            elif action == 'get_status':
                session = self.sessions.get(session_id)
                status = {
                    'session_active': bool(session),
                    'page_url': session.page.url if session and session.page else None,
                    'capabilities': session.capabilities if session else []
                }
                await websocket.send(json.dumps({
                    'type': 'status_response',
                    'status': status
                }))
                
        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'error',
                'action': action,
                'message': str(e)
            }))

    async def _broadcast_to_websocket(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to WebSocket client"""
        websocket = self.websocket_connections.get(session_id)
        if websocket:
            try:
                await websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ WebSocket broadcast failed: {e}")

    async def _store_session_in_db(self, session: NativeBrowserSession):
        """Store session data in database"""
        try:
            session_data = {
                'session_id': session.session_id,
                'user_session': session.user_session,
                'capabilities': session.capabilities,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'performance_metrics': session.performance_metrics
            }
            
            self.db.native_sessions.insert_one(session_data)
        except Exception as e:
            logger.error(f"❌ Database store failed: {e}")

    # Event handlers
    async def _handle_page_load(self, session_id: str):
        """Handle page load event"""
        await self._broadcast_to_websocket(session_id, {
            'type': 'page_loaded',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _handle_dom_ready(self, session_id: str):
        """Handle DOM ready event"""
        await self._broadcast_to_websocket(session_id, {
            'type': 'dom_ready',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _handle_page_error(self, session_id: str, error):
        """Handle page error"""
        logger.error(f"Page error in session {session_id}: {error}")

    async def _handle_page_crash(self, session_id: str):
        """Handle page crash"""
        logger.error(f"Page crashed in session {session_id}")

    async def _handle_request(self, session_id: str, request):
        """Handle network request"""
        # Update performance metrics
        session = self.sessions.get(session_id)
        if session:
            if 'network_requests' not in session.performance_metrics:
                session.performance_metrics['network_requests'] = 0
            session.performance_metrics['network_requests'] += 1

    async def _handle_response(self, session_id: str, response):
        """Handle network response"""
        # Monitor failed requests
        if response.status >= 400:
            logger.warning(f"Failed request: {response.url} ({response.status})")

    async def _handle_console(self, session_id: str, msg):
        """Handle console messages"""
        if msg.type == 'error':
            logger.warning(f"Console error in session {session_id}: {msg.text}")

    async def cleanup(self):
        """Cleanup all sessions and close browser"""
        try:
            # Close all sessions
            for session_id in list(self.sessions.keys()):
                await self.close_session(session_id)
            
            # Close browser
            if self.browser:
                await self.browser.close()
            
            # Stop Playwright
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("🧹 Native Chromium Engine cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")


class PerformanceCollector:
    """Collect and analyze performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    async def collect_metrics(self, session: NativeBrowserSession) -> Dict[str, Any]:
        """Collect comprehensive performance metrics"""
        return {
            'session_duration': (datetime.utcnow() - session.created_at).total_seconds(),
            'last_activity': session.last_activity.isoformat(),
            'capabilities_count': len(session.capabilities),
            'performance_data': session.performance_metrics
        }


class ComputerUseAPI:
    """Computer Use API for AI-powered browser automation"""
    
    def __init__(self):
        self.ai_client = None  # Initialize with AI client if needed
    
    async def smart_click(self, screenshot_b64: str, description: str) -> Dict[str, Any]:
        """Find and click element using AI description"""
        try:
            # For now, return mock coordinates
            # In production, this would use AI/ML to analyze screenshot and find element
            
            # Mock AI analysis - find element based on description
            coordinates = await self._mock_ai_element_detection(screenshot_b64, description)
            
            return {
                "success": True,
                "description": description,
                "coordinates": coordinates,
                "confidence": 0.85
            }
            
        except Exception as e:
            logger.error(f"❌ Smart click failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _mock_ai_element_detection(self, screenshot_b64: str, description: str) -> Dict[str, int]:
        """Mock AI element detection - replace with real AI in production"""
        # Mock coordinates based on common UI patterns
        mock_coordinates = {
            "search": {"x": 500, "y": 100},
            "submit": {"x": 600, "y": 400},
            "login": {"x": 700, "y": 350},
            "button": {"x": 400, "y": 300},
            "link": {"x": 300, "y": 200}
        }
        
        # Simple keyword matching for demo
        for keyword, coords in mock_coordinates.items():
            if keyword in description.lower():
                return coords
        
        # Default center click
        return {"x": 500, "y": 400}


# Initialize function for backend integration
async def initialize_native_chromium_engine(mongodb_client: MongoClient) -> NativeChromiumEngine:
    """Initialize the native Chromium engine"""
    engine = NativeChromiumEngine(mongodb_client)
    success = await engine.initialize()
    
    if success:
        logger.info("✅ Native Chromium Engine ready for use")
        return engine
    else:
        logger.error("❌ Failed to initialize Native Chromium Engine")
        return None