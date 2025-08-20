"""
AETHER WebSocket Server v6.0.0
Real-time communication server for Native Chromium Engine
"""

import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from typing import Dict, Set, Any
import uuid
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AETHERWebSocketServer:
    """WebSocket server for real-time browser communication"""
    
    def __init__(self, native_engine):
        self.native_engine = native_engine
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
        self.server = None
        self.host = '0.0.0.0'
        self.port = 8002
        
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            logger.info(f"🔗 Starting AETHER WebSocket Server on {self.host}:{self.port}")
            
            self.server = await websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
                max_size=2**20,  # 1MB max message size
                compression=None
            )
            
            logger.info(f"✅ WebSocket Server started successfully on ws://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start WebSocket server: {e}")
            return False
    
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        connection_id = str(uuid.uuid4())
        
        try:
            # Extract session ID from path
            session_id = self._extract_session_id(path)
            
            if not session_id:
                await websocket.close(code=4000, reason="No session ID provided")
                return
            
            # Store connection
            self.connections[connection_id] = websocket
            self.session_connections[session_id] = connection_id
            
            logger.info(f"🔗 WebSocket connected: {connection_id} (session: {session_id})")
            
            # Send connection confirmation
            await self.send_message(websocket, {
                'type': 'connection_established',
                'connection_id': connection_id,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'server_version': '6.0.0'
            })
            
            # Handle messages from this connection
            await self._handle_connection_messages(websocket, session_id, connection_id)
            
        except ConnectionClosed:
            logger.info(f"🔌 WebSocket connection closed: {connection_id}")
        except WebSocketException as e:
            logger.error(f"❌ WebSocket exception: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error handling connection: {e}")
        finally:
            # Cleanup
            await self._cleanup_connection(connection_id, session_id)
    
    async def _handle_connection_messages(self, websocket, session_id: str, connection_id: str):
        """Handle messages from WebSocket connection"""
        try:
            async for message in websocket:
                try:
                    # Parse message
                    if isinstance(message, bytes):
                        message = message.decode('utf-8')
                    
                    data = json.loads(message)
                    
                    # Add connection context
                    data['connection_id'] = connection_id
                    data['session_id'] = session_id
                    
                    # Handle the message
                    await self._process_message(websocket, data)
                    
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Invalid JSON format")
                except Exception as e:
                    await self.send_error(websocket, f"Message processing error: {str(e)}")
                    
        except ConnectionClosed:
            pass  # Connection closed normally
        except Exception as e:
            logger.error(f"❌ Error handling messages: {e}")
    
    async def _process_message(self, websocket, data: Dict[str, Any]):
        """Process incoming message and route to native engine"""
        action = data.get('action')
        session_id = data.get('session_id')
        
        logger.debug(f"📨 Processing message: {action} (session: {session_id})")
        
        try:
            if action == 'navigate':
                result = await self.native_engine.navigate_to_url(
                    session_id, 
                    data.get('url'),
                    timeout=data.get('timeout', 30000)
                )
                await self.send_message(websocket, {
                    'type': 'navigation_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'screenshot':
                result = await self.native_engine.capture_screenshot(
                    session_id,
                    full_page=data.get('full_page', False),
                    quality=data.get('quality', 80)
                )
                # Screenshot result is broadcasted by native engine
                
            elif action == 'execute_js':
                result = await self.native_engine.execute_javascript(
                    session_id,
                    data.get('script'),
                    data.get('args', [])
                )
                await self.send_message(websocket, {
                    'type': 'js_result',
                    'messageId': data.get('messageId'),
                    **result
                })
            
            elif action == 'click':
                if 'selector' in data:
                    # CSS selector click
                    result = await self.native_engine.click_element(
                        session_id, 
                        data.get('selector'),
                        timeout=data.get('timeout', 5000)
                    )
                elif 'x' in data and 'y' in data:
                    # Coordinate click
                    session = self.native_engine.sessions.get(session_id)
                    if session and session.page:
                        await session.page.mouse.click(data.get('x'), data.get('y'))
                        result = {'success': True, 'coordinates': {'x': data.get('x'), 'y': data.get('y')}}
                    else:
                        result = {'success': False, 'error': 'Session not found'}
                else:
                    result = {'success': False, 'error': 'No selector or coordinates provided'}
                
                await self.send_message(websocket, {
                    'type': 'click_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'type':
                result = await self.native_engine.type_text(
                    session_id,
                    data.get('selector'),
                    data.get('text'),
                    clear=data.get('clear', True)
                )
                await self.send_message(websocket, {
                    'type': 'type_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'get_content':
                result = await self.native_engine.get_page_content(
                    session_id,
                    include_html=data.get('include_html', False)
                )
                await self.send_message(websocket, {
                    'type': 'content_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'smart_click':
                result = await self.native_engine.smart_click(
                    session_id,
                    data.get('description')
                )
                await self.send_message(websocket, {
                    'type': 'smart_click_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'extract_data':
                result = await self.native_engine.extract_page_data(
                    session_id,
                    data_type=data.get('data_type', 'general')
                )
                await self.send_message(websocket, {
                    'type': 'extract_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'get_performance':
                result = await self.native_engine.get_performance_metrics(session_id)
                await self.send_message(websocket, {
                    'type': 'performance_result',
                    'messageId': data.get('messageId'),
                    'result': result
                })
            
            elif action == 'get_status':
                session = self.native_engine.sessions.get(session_id)
                status = {
                    'session_active': bool(session),
                    'page_url': session.page.url if session and session.page else None,
                    'page_title': await session.page.title() if session and session.page else None,
                    'capabilities': session.capabilities if session else [],
                    'connection_id': data.get('connection_id'),
                    'server_time': datetime.utcnow().isoformat()
                }
                await self.send_message(websocket, {
                    'type': 'status_response',
                    'messageId': data.get('messageId'),
                    'status': status
                })
            
            elif action == 'ping':
                await self.send_message(websocket, {
                    'type': 'pong',
                    'messageId': data.get('messageId'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            else:
                await self.send_error(websocket, f"Unknown action: {action}")
            
        except Exception as e:
            logger.error(f"❌ Error processing {action}: {e}")
            await self.send_error(websocket, f"Action failed: {str(e)}", messageId=data.get('messageId'))
    
    async def send_message(self, websocket, message: Dict[str, Any]):
        """Send message to WebSocket client"""
        try:
            await websocket.send(json.dumps(message, default=str))
        except ConnectionClosed:
            pass  # Client disconnected
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    async def send_error(self, websocket, error_message: str, messageId: str = None):
        """Send error message to WebSocket client"""
        error_data = {
            'type': 'error',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if messageId:
            error_data['messageId'] = messageId
        
        await self.send_message(websocket, error_data)
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to specific session"""
        connection_id = self.session_connections.get(session_id)
        if connection_id and connection_id in self.connections:
            websocket = self.connections[connection_id]
            await self.send_message(websocket, message)
        else:
            logger.debug(f"No WebSocket connection found for session: {session_id}")
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.connections:
            return
        
        # Send to all connections
        disconnected = []
        for connection_id, websocket in self.connections.items():
            try:
                await self.send_message(websocket, message)
            except:
                disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            await self._cleanup_connection(connection_id, None)
    
    def _extract_session_id(self, path: str) -> str:
        """Extract session ID from WebSocket path"""
        # Expected format: /ws/native/{session_id}
        parts = path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'ws' and parts[1] == 'native':
            return parts[2]
        return None
    
    async def _cleanup_connection(self, connection_id: str, session_id: str = None):
        """Cleanup connection references"""
        try:
            # Remove from connections
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            # Remove from session connections
            if session_id and session_id in self.session_connections:
                if self.session_connections[session_id] == connection_id:
                    del self.session_connections[session_id]
            else:
                # Find and remove by connection_id
                to_remove = []
                for sid, cid in self.session_connections.items():
                    if cid == connection_id:
                        to_remove.append(sid)
                
                for sid in to_remove:
                    del self.session_connections[sid]
            
            logger.debug(f"🧹 Cleaned up connection: {connection_id}")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up connection: {e}")
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket server statistics"""
        return {
            'total_connections': len(self.connections),
            'active_sessions': len(self.session_connections),
            'server_status': 'running' if self.server else 'stopped',
            'server_address': f"ws://{self.host}:{self.port}",
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        try:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                logger.info("🛑 WebSocket server stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping server: {e}")


# Integration with Native Engine
def integrate_websocket_with_native_engine(native_engine):
    """Integrate WebSocket server with native engine for broadcasts"""
    
    # Override native engine broadcast method
    original_broadcast = native_engine._broadcast_to_websocket
    websocket_server = None
    
    async def enhanced_broadcast(session_id: str, message: Dict[str, Any]):
        """Enhanced broadcast that uses WebSocket server"""
        try:
            # Use original method first (for backwards compatibility)
            await original_broadcast(session_id, message)
            
            # Also use WebSocket server if available
            if websocket_server:
                await websocket_server.broadcast_to_session(session_id, message)
                
        except Exception as e:
            logger.error(f"❌ Enhanced broadcast failed: {e}")
    
    # Replace broadcast method
    native_engine._broadcast_to_websocket = enhanced_broadcast
    
    return lambda ws_server: setattr(websocket_server, 'value', ws_server) or ws_server