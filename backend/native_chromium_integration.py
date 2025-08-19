"""
Native Chromium Integration - Phase 3 Implementation
Full browser engine integration with extensions and DevTools support
"""

import json
import asyncio
import subprocess
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import uuid
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)

class NativeChromiumEngine:
    """Native Chromium browser engine integration"""
    
    def __init__(self, db_client):
        self.db = db_client.aether_browser
        self.browser_sessions = {}
        self.chromium_instances = {}
        self.user_data_dir = Path("/tmp/aether_chromium_data")
        self.extensions_dir = Path("/tmp/aether_extensions")
        
        # Ensure directories exist
        self.user_data_dir.mkdir(exist_ok=True)
        self.extensions_dir.mkdir(exist_ok=True)
        
        # Browser configuration
        self.default_args = [
            "--no-first-run",
            "--no-default-browser-check", 
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-background-networking",
            "--enable-automation",
            "--disable-dev-shm-usage",
            "--disable-ipc-flooding-protection",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-sync",
            "--disable-translate",
            "--disable-web-security",  # For cross-origin access
            "--allow-running-insecure-content",
            "--disable-features=TranslateUI,BlinkGenPropertyTrees",
            "--remote-debugging-port=0",  # Let Chrome choose port
            "--enable-devtools-experiments"
        ]

    async def create_browser_session(self, session_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new native browser session"""
        try:
            session_id = str(uuid.uuid4())
            user_session = session_config.get("user_session", session_id)
            
            # Create user data directory for this session
            session_user_data = self.user_data_dir / f"session_{session_id}"
            session_user_data.mkdir(exist_ok=True)
            
            # Configure Chromium arguments
            args = self.default_args.copy()
            args.extend([
                f"--user-data-dir={session_user_data}",
                f"--profile-directory=AETHER_{user_session}"
            ])
            
            # Add extensions if requested
            extensions = session_config.get("extensions", [])
            if extensions:
                extension_paths = []
                for ext in extensions:
                    ext_path = await self._prepare_extension(ext)
                    if ext_path:
                        extension_paths.append(ext_path)
                
                if extension_paths:
                    args.append(f"--load-extension={','.join(extension_paths)}")
            
            # Enable DevTools if requested
            if session_config.get("enable_devtools", True):
                args.append("--auto-open-devtools-for-tabs")
            
            # Set window size
            width = session_config.get("width", 1920)
            height = session_config.get("height", 1080)
            args.append(f"--window-size={width},{height}")
            
            # Start Chromium process
            chromium_path = await self._get_chromium_path()
            if not chromium_path:
                raise Exception("Chromium browser not found")
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                chromium_path,
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait a moment for process to start
            await asyncio.sleep(2)
            
            # Get debugging port
            debug_port = await self._get_debug_port(process.pid)
            
            # Store session information
            session_info = {
                "session_id": session_id,
                "user_session": user_session,
                "process_id": process.pid,
                "debug_port": debug_port,
                "user_data_dir": str(session_user_data),
                "created_at": datetime.utcnow(),
                "config": session_config,
                "status": "active"
            }
            
            self.browser_sessions[session_id] = session_info
            self.chromium_instances[session_id] = process
            
            # Store in database
            await self.db.chromium_sessions.insert_one(session_info)
            
            logger.info(f"Native Chromium session created: {session_id}")
            
            return {
                "success": True,
                "session_id": session_id,
                "debug_port": debug_port,
                "process_id": process.pid,
                "devtools_url": f"http://localhost:{debug_port}",
                "capabilities": {
                    "extensions": len(extensions) > 0,
                    "devtools": session_config.get("enable_devtools", True),
                    "cross_origin": True,
                    "native_performance": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating native browser session: {e}")
            return {"success": False, "error": str(e)}

    async def navigate_session(self, session_id: str, url: str) -> Dict[str, Any]:
        """Navigate session to URL using Chrome DevTools Protocol"""
        try:
            session_info = self.browser_sessions.get(session_id)
            if not session_info:
                return {"success": False, "error": "Session not found"}
            
            debug_port = session_info["debug_port"]
            
            # Use Chrome DevTools Protocol for navigation
            import httpx
            
            # Get available targets
            async with httpx.AsyncClient() as client:
                targets_response = await client.get(f"http://localhost:{debug_port}/json")
                targets = targets_response.json()
                
                if not targets:
                    return {"success": False, "error": "No browser targets available"}
                
                # Use first target (main tab)
                target = targets[0]
                websocket_url = target["webSocketDebuggerUrl"]
                
                # Connect to WebSocket and send navigation command
                import websockets
                
                try:
                    async with websockets.connect(websocket_url) as websocket:
                        # Enable Page domain
                        await websocket.send(json.dumps({
                            "id": 1,
                            "method": "Page.enable"
                        }))
                        
                        # Navigate to URL
                        await websocket.send(json.dumps({
                            "id": 2,
                            "method": "Page.navigate",
                            "params": {"url": url}
                        }))
                        
                        # Wait for response
                        response = await websocket.recv()
                        result = json.loads(response)
                        
                        logger.info(f"Navigation result: {result}")
                        
                        return {
                            "success": True,
                            "url": url,
                            "session_id": session_id,
                            "navigation_id": result.get("result", {}).get("frameId")
                        }
                        
                except Exception as ws_error:
                    logger.error(f"WebSocket navigation error: {ws_error}")
                    return {"success": False, "error": str(ws_error)}
            
        except Exception as e:
            logger.error(f"Error navigating session: {e}")
            return {"success": False, "error": str(e)}

    async def execute_script(self, session_id: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript in browser session"""
        try:
            session_info = self.browser_sessions.get(session_id)
            if not session_info:
                return {"success": False, "error": "Session not found"}
            
            debug_port = session_info["debug_port"]
            
            import httpx
            import websockets
            
            async with httpx.AsyncClient() as client:
                targets_response = await client.get(f"http://localhost:{debug_port}/json")
                targets = targets_response.json()
                
                if targets:
                    target = targets[0]
                    websocket_url = target["webSocketDebuggerUrl"]
                    
                    async with websockets.connect(websocket_url) as websocket:
                        # Enable Runtime domain
                        await websocket.send(json.dumps({
                            "id": 1,
                            "method": "Runtime.enable"
                        }))
                        
                        # Execute script
                        await websocket.send(json.dumps({
                            "id": 2,
                            "method": "Runtime.evaluate",
                            "params": {
                                "expression": script,
                                "awaitPromise": True,
                                "returnByValue": True
                            }
                        }))
                        
                        response = await websocket.recv()
                        result = json.loads(response)
                        
                        return {
                            "success": True,
                            "result": result.get("result", {}),
                            "session_id": session_id
                        }
            
            return {"success": False, "error": "No targets available"}
            
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return {"success": False, "error": str(e)}

    async def install_extension(self, session_id: str, extension_config: Dict[str, Any]) -> Dict[str, Any]:
        """Install browser extension in session"""
        try:
            extension_id = extension_config.get("id")
            extension_url = extension_config.get("chrome_web_store_url")
            
            if not extension_id and not extension_url:
                return {"success": False, "error": "Extension ID or URL required"}
            
            # Download and install extension
            extension_path = await self._download_extension(extension_config)
            
            if extension_path:
                # Add extension to session (requires restart)
                session_info = self.browser_sessions.get(session_id)
                if session_info:
                    # Store extension info
                    extensions_list = session_info.get("extensions", [])
                    extensions_list.append({
                        "id": extension_id,
                        "path": extension_path,
                        "installed_at": datetime.utcnow()
                    })
                    session_info["extensions"] = extensions_list
                    
                    return {
                        "success": True,
                        "extension_id": extension_id,
                        "requires_restart": True,
                        "message": "Extension will be loaded on next session restart"
                    }
            
            return {"success": False, "error": "Failed to install extension"}
            
        except Exception as e:
            logger.error(f"Error installing extension: {e}")
            return {"success": False, "error": str(e)}

    async def get_page_source(self, session_id: str) -> Dict[str, Any]:
        """Get page source using DevTools"""
        try:
            result = await self.execute_script(session_id, "document.documentElement.outerHTML")
            
            if result.get("success"):
                return {
                    "success": True,
                    "source": result["result"].get("result", {}).get("value", ""),
                    "session_id": session_id
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting page source: {e}")
            return {"success": False, "error": str(e)}

    async def take_screenshot(self, session_id: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Take screenshot of current page"""
        try:
            session_info = self.browser_sessions.get(session_id)
            if not session_info:
                return {"success": False, "error": "Session not found"}
            
            debug_port = session_info["debug_port"]
            options = options or {}
            
            import httpx
            import websockets
            import base64
            
            async with httpx.AsyncClient() as client:
                targets_response = await client.get(f"http://localhost:{debug_port}/json")
                targets = targets_response.json()
                
                if targets:
                    target = targets[0]
                    websocket_url = target["webSocketDebuggerUrl"]
                    
                    async with websockets.connect(websocket_url) as websocket:
                        # Enable Page domain
                        await websocket.send(json.dumps({
                            "id": 1,
                            "method": "Page.enable"
                        }))
                        
                        # Take screenshot
                        screenshot_params = {
                            "format": options.get("format", "png"),
                            "quality": options.get("quality", 90)
                        }
                        
                        if options.get("full_page"):
                            screenshot_params["captureBeyondViewport"] = True
                        
                        await websocket.send(json.dumps({
                            "id": 2,
                            "method": "Page.captureScreenshot",
                            "params": screenshot_params
                        }))
                        
                        response = await websocket.recv()
                        result = json.loads(response)
                        
                        if result.get("result", {}).get("data"):
                            # Save screenshot
                            screenshot_data = base64.b64decode(result["result"]["data"])
                            screenshot_path = f"/tmp/screenshot_{session_id}_{int(datetime.utcnow().timestamp())}.png"
                            
                            with open(screenshot_path, "wb") as f:
                                f.write(screenshot_data)
                            
                            return {
                                "success": True,
                                "screenshot_path": screenshot_path,
                                "data": result["result"]["data"],
                                "session_id": session_id
                            }
            
            return {"success": False, "error": "Screenshot failed"}
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {"success": False, "error": str(e)}

    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close native browser session"""
        try:
            # Get session info
            session_info = self.browser_sessions.get(session_id)
            process = self.chromium_instances.get(session_id)
            
            if process:
                # Terminate process gracefully
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    # Force kill if needed
                    process.kill()
                    await process.wait()
            
            # Clean up session data
            if session_info:
                user_data_dir = Path(session_info["user_data_dir"])
                if user_data_dir.exists():
                    shutil.rmtree(user_data_dir, ignore_errors=True)
            
            # Remove from memory
            if session_id in self.browser_sessions:
                del self.browser_sessions[session_id]
            if session_id in self.chromium_instances:
                del self.chromium_instances[session_id]
            
            # Update database
            await self.db.chromium_sessions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "closed", "closed_at": datetime.utcnow()}}
            )
            
            return {"success": True, "session_id": session_id}
            
        except Exception as e:
            logger.error(f"Error closing session: {e}")
            return {"success": False, "error": str(e)}

    async def _get_chromium_path(self) -> Optional[str]:
        """Find Chromium/Chrome executable path"""
        possible_paths = [
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium", 
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/google/chrome/chrome",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find using which command
        try:
            result = subprocess.run(["which", "chromium"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            
            result = subprocess.run(["which", "google-chrome"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return None

    async def _get_debug_port(self, pid: int) -> Optional[int]:
        """Get debugging port for Chromium process"""
        try:
            # Wait a moment for process to fully start
            await asyncio.sleep(1)
            
            # Check process command line for debug port
            process = psutil.Process(pid)
            cmdline = process.cmdline()
            
            for arg in cmdline:
                if "--remote-debugging-port=" in arg:
                    return int(arg.split("=")[1])
            
            # If no specific port, Chrome usually uses 9222
            return 9222
            
        except Exception as e:
            logger.error(f"Error getting debug port: {e}")
            return 9222

    async def _prepare_extension(self, extension_config: Dict[str, Any]) -> Optional[str]:
        """Prepare extension for loading"""
        try:
            extension_id = extension_config.get("id")
            extension_path = self.extensions_dir / extension_id
            
            # Create extension directory if needed
            extension_path.mkdir(exist_ok=True)
            
            # Create basic manifest if extension is built-in
            if extension_config.get("builtin"):
                manifest = {
                    "manifest_version": 3,
                    "name": extension_config.get("name", "AETHER Extension"),
                    "version": "1.0",
                    "permissions": extension_config.get("permissions", []),
                    "content_scripts": extension_config.get("content_scripts", []),
                    "background": extension_config.get("background", {})
                }
                
                with open(extension_path / "manifest.json", "w") as f:
                    json.dump(manifest, f, indent=2)
                
                return str(extension_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Error preparing extension: {e}")
            return None

    async def _download_extension(self, extension_config: Dict[str, Any]) -> Optional[str]:
        """Download extension from Chrome Web Store"""
        # This would require Chrome Web Store API integration
        # For now, return None (extensions need to be pre-installed)
        logger.info("Extension download not implemented yet")
        return None

    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active browser sessions"""
        try:
            sessions = []
            for session_id, session_info in self.browser_sessions.items():
                sessions.append({
                    "session_id": session_id,
                    "user_session": session_info.get("user_session"),
                    "process_id": session_info.get("process_id"),
                    "debug_port": session_info.get("debug_port"),
                    "created_at": session_info.get("created_at"),
                    "status": "active"
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

# Initialize native Chromium integration
def initialize_native_chromium(db_client):
    """Initialize native Chromium browser engine"""
    try:
        chromium_engine = NativeChromiumEngine(db_client)
        
        logger.info("Native Chromium integration initialized successfully")
        return chromium_engine
        
    except Exception as e:
        logger.error(f"Failed to initialize native Chromium: {e}")
        return None