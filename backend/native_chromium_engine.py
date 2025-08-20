"""
Native Chromium Engine - Advanced Browser Automation
Implements Workstream D: Native Browser Engine with full Chromium integration
"""

import asyncio
import json
import base64
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import websockets
from fastapi import WebSocket
import uuid

logger = logging.getLogger(__name__)

class NativeChromiumEngine:
    def __init__(self, db_client):
        self.db = db_client.aether_browser
        self.browser: Optional[Browser] = None
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.playwright_instance = None
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.is_initialized = False

    async def initialize(self):
        """Initialize the native Chromium engine"""
        try:
            self.playwright_instance = await async_playwright().start()
            self.browser = await self.playwright_instance.chromium.launch(
                headless=True,  # Set to False for debugging
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--enable-automation',
                    '--remote-debugging-port=9222'
                ]
            )
            self.is_initialized = True
            logger.info("🔥 Native Chromium Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Native Chromium Engine: {e}")
            return False

    async def create_browser_session(self, session_id: str, user_agent: str = None) -> Dict[str, Any]:
        """Create a new browser session with isolated context"""
        try:
            if not self.is_initialized:
                await self.initialize()

            # Create new browser context (isolated session)
            context = await self.browser.new_context(
                user_agent=user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AETHER/6.0",
                viewport={'width': 1920, 'height': 1080}
            )

            # Create new page
            page = await context.new_page()
            
            # Store references
            self.contexts[session_id] = context
            self.pages[session_id] = page
            
            # Initialize session tracking
            self.active_sessions[session_id] = {
                'created_at': datetime.utcnow(),
                'current_url': '',
                'navigation_history': [],
                'performance_metrics': {},
                'security_info': {}
            }

            # Set up page event handlers
            await self._setup_page_handlers(session_id, page)

            logger.info(f"✅ Native browser session created: {session_id}")
            return {
                'success': True,
                'session_id': session_id,
                'status': 'created',
                'capabilities': [
                    'native_navigation',
                    'javascript_execution', 
                    'screenshot_capture',
                    'devtools_protocol',
                    'performance_monitoring',
                    'security_analysis'
                ]
            }

        except Exception as e:
            logger.error(f"Failed to create browser session: {e}")
            return {'success': False, 'error': str(e)}

    async def _setup_page_handlers(self, session_id: str, page: Page):
        """Set up event handlers for page events"""
        
        async def on_request(request):
            """Track network requests"""
            self.active_sessions[session_id]['performance_metrics']['last_request'] = {
                'url': request.url,
                'method': request.method,
                'timestamp': datetime.utcnow().isoformat()
            }

        async def on_response(response):
            """Track network responses"""
            self.active_sessions[session_id]['performance_metrics']['last_response'] = {
                'url': response.url,
                'status': response.status,
                'timestamp': datetime.utcnow().isoformat()
            }

        async def on_load(page):
            """Track page loads"""
            self.active_sessions[session_id]['performance_metrics']['page_loaded'] = datetime.utcnow().isoformat()
            
            # Send update to connected WebSocket
            if session_id in self.websocket_connections:
                await self._send_websocket_update(session_id, {
                    'type': 'page_loaded',
                    'url': page.url,
                    'title': await page.title()
                })

        page.on('request', on_request)
        page.on('response', on_response)
        page.on('load', lambda: asyncio.create_task(on_load(page)))

    async def navigate_to_url(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigate to a specific URL"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Start performance tracking
            start_time = datetime.utcnow()
            
            # Navigate
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Calculate load time
            load_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get page info
            title = await page.title()
            current_url = page.url
            
            # Update session info
            self.active_sessions[session_id]['current_url'] = current_url
            self.active_sessions[session_id]['navigation_history'].append({
                'url': url,
                'final_url': current_url,
                'title': title,
                'load_time': load_time,
                'timestamp': datetime.utcnow(),
                'status_code': response.status if response else None
            })

            # Security analysis
            security_info = await self._analyze_page_security(page, current_url)
            self.active_sessions[session_id]['security_info'] = security_info

            result = {
                'success': True,
                'url': current_url,
                'title': title,
                'load_time': load_time,
                'status_code': response.status if response else None,
                'security': security_info,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Send WebSocket update
            if session_id in self.websocket_connections:
                await self._send_websocket_update(session_id, {
                    'type': 'navigation_complete',
                    **result
                })

            return result

        except Exception as e:
            logger.error(f"Navigation failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def execute_javascript(self, session_id: str, script: str, args: List = None) -> Dict[str, Any]:
        """Execute JavaScript in the browser context"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Execute JavaScript
            result = await page.evaluate(script, args or [])
            
            return {
                'success': True,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"JavaScript execution failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def take_screenshot(self, session_id: str, full_page: bool = False, quality: int = 80) -> Dict[str, Any]:
        """Take a screenshot of the current page"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(
                full_page=full_page,
                quality=quality,
                type='jpeg'
            )
            
            # Convert to base64 for transmission
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return {
                'success': True,
                'screenshot': screenshot_b64,
                'format': 'jpeg',
                'full_page': full_page,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Screenshot failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def get_page_content(self, session_id: str, include_html: bool = False) -> Dict[str, Any]:
        """Get page content and metadata"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Get page data
            title = await page.title()
            url = page.url
            
            # Get text content
            text_content = await page.evaluate('''() => {
                return document.body.innerText;
            }''')
            
            result = {
                'success': True,
                'url': url,
                'title': title,
                'text_content': text_content[:5000],  # Limit size
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Optionally include HTML
            if include_html:
                html_content = await page.content()
                result['html_content'] = html_content[:10000]  # Limit size
            
            return result

        except Exception as e:
            logger.error(f"Get page content failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def click_element(self, session_id: str, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click an element on the page"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Wait for element and click
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
            
            return {
                'success': True,
                'action': 'click',
                'selector': selector,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Click element failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def type_text(self, session_id: str, selector: str, text: str, clear: bool = True) -> Dict[str, Any]:
        """Type text into an input element"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Wait for element
            await page.wait_for_selector(selector, timeout=5000)
            
            if clear:
                await page.fill(selector, text)
            else:
                await page.type(selector, text)
            
            return {
                'success': True,
                'action': 'type',
                'selector': selector,
                'text': text,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Type text failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            if session_id not in self.pages:
                return {'success': False, 'error': 'Session not found'}

            page = self.pages[session_id]
            
            # Get performance metrics using CDP
            performance_metrics = await page.evaluate('''() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                return {
                    load_time: navigation ? navigation.loadEventEnd - navigation.fetchStart : 0,
                    dom_content_loaded: navigation ? navigation.domContentLoadedEventEnd - navigation.fetchStart : 0,
                    first_paint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    first_contentful_paint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    memory_used: performance.memory ? performance.memory.usedJSHeapSize : 0
                };
            }''')
            
            return {
                'success': True,
                'metrics': performance_metrics,
                'session_info': self.active_sessions.get(session_id, {}),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Get performance metrics failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def _analyze_page_security(self, page: Page, url: str) -> Dict[str, Any]:
        """Analyze page security"""
        try:
            security_info = {
                'is_https': url.startswith('https://'),
                'domain': url.split('/')[2] if '://' in url else url,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Check for mixed content
            mixed_content = await page.evaluate('''() => {
                const images = Array.from(document.images);
                const scripts = Array.from(document.scripts);
                const links = Array.from(document.links);
                
                const httpResources = [
                    ...images.filter(img => img.src.startsWith('http:')),
                    ...scripts.filter(script => script.src.startsWith('http:')),
                    ...links.filter(link => link.href.startsWith('http:'))
                ];
                
                return httpResources.length;
            }''')
            
            security_info['mixed_content_count'] = mixed_content
            security_info['security_level'] = 'secure' if security_info['is_https'] and mixed_content == 0 else 'warning' if security_info['is_https'] else 'insecure'
            
            return security_info

        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {'error': str(e)}

    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket connection for real-time browser control"""
        try:
            await websocket.accept()
            self.websocket_connections[session_id] = websocket
            
            logger.info(f"WebSocket connection established for session {session_id}")
            
            # Send initial status
            await self._send_websocket_update(session_id, {
                'type': 'connection_established',
                'session_id': session_id,
                'status': 'ready'
            })
            
            while True:
                # Receive message from client
                message = await websocket.receive_text()
                command = json.loads(message)
                
                # Process command
                response = await self._process_websocket_command(session_id, command)
                
                # Send response
                await websocket.send_text(json.dumps(response))
                
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
        finally:
            # Clean up
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]

    async def _process_websocket_command(self, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process WebSocket command"""
        try:
            action = command.get('action')
            
            if action == 'navigate':
                return await self.navigate_to_url(session_id, command.get('url'))
            
            elif action == 'screenshot':
                return await self.take_screenshot(session_id, command.get('full_page', False))
            
            elif action == 'execute_js':
                return await self.execute_javascript(session_id, command.get('script'), command.get('args'))
            
            elif action == 'click':
                return await self.click_element(session_id, command.get('selector'))
            
            elif action == 'type':
                return await self.type_text(session_id, command.get('selector'), command.get('text'))
            
            elif action == 'get_content':
                return await self.get_page_content(session_id, command.get('include_html', False))
            
            elif action == 'performance':
                return await self.get_performance_metrics(session_id)
            
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _send_websocket_update(self, session_id: str, data: Dict[str, Any]):
        """Send update to WebSocket connection"""
        try:
            if session_id in self.websocket_connections:
                websocket = self.websocket_connections[session_id]
                await websocket.send_text(json.dumps(data))
        except Exception as e:
            logger.error(f"Failed to send WebSocket update: {e}")

    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a browser session"""
        try:
            # Close page and context
            if session_id in self.pages:
                await self.pages[session_id].close()
                del self.pages[session_id]
            
            if session_id in self.contexts:
                await self.contexts[session_id].close()
                del self.contexts[session_id]
            
            # Clean up session data
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]
            
            logger.info(f"✅ Browser session closed: {session_id}")
            return {'success': True, 'message': 'Session closed'}

        except Exception as e:
            logger.error(f"Failed to close session {session_id}: {e}")
            return {'success': False, 'error': str(e)}

    async def cleanup(self):
        """Clean up all resources"""
        try:
            # Close all sessions
            for session_id in list(self.pages.keys()):
                await self.close_session(session_id)
            
            # Close browser
            if self.browser:
                await self.browser.close()
            
            # Stop playwright
            if self.playwright_instance:
                await self.playwright_instance.stop()
            
            logger.info("🔥 Native Chromium Engine cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Global instance
native_chromium_engine = None

async def initialize_native_chromium_engine(db_client):
    """Initialize the native chromium engine"""
    global native_chromium_engine
    try:
        native_chromium_engine = NativeChromiumEngine(db_client)
        success = await native_chromium_engine.initialize()
        if success:
            logger.info("🔥 Native Chromium Engine initialized and ready")
            return native_chromium_engine
        else:
            logger.error("Failed to initialize Native Chromium Engine")
            return None
    except Exception as e:
        logger.error(f"Native Chromium Engine initialization error: {e}")
        return None

def get_native_chromium_engine():
    """Get the global native chromium engine instance"""
    return native_chromium_engine