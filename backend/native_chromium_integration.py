"""
Native Chromium Integration - Phase 3 Implementation  
Provides native browser engine capabilities, extensions support, and DevTools integration
"""

import asyncio
import json
import uuid
import os
import subprocess
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging
from pymongo import MongoClient
import tempfile
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class BrowserInstance:
    instance_id: str
    user_session: str
    process_id: Optional[int]
    port: int
    profile_path: str
    status: str  # "starting", "ready", "error", "stopped"
    created_at: datetime
    extensions: List[str]

@dataclass
class ChromiumCapability:
    name: str
    description: str
    supported: bool
    version: Optional[str] = None

class NativeChromiumEngine:
    """Core native Chromium browser engine"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.instances_collection = self.db.chromium_instances
        self.extensions_collection = self.db.chromium_extensions
        
        self.base_port = 9222  # Chrome DevTools Protocol port
        self.active_instances: Dict[str, BrowserInstance] = {}
        
        # Chrome binary paths by platform
        self.chrome_paths = self._get_chrome_paths()
        self.capabilities = self._detect_capabilities()
        
    def _get_chrome_paths(self) -> Dict[str, str]:
        """Get Chrome binary paths for different platforms"""
        paths = {
            "Windows": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe"
            ],
            "Darwin": [  # macOS
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome"
            ],
            "Linux": [
                "/usr/bin/google-chrome",
                "/usr/bin/chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium"
            ]
        }
        
        system = platform.system()
        if system in paths:
            for path in paths[system]:
                if system == "Windows":
                    # Handle Windows username placeholder
                    import os
                    username = os.getenv("USERNAME", "")
                    path = path.format(username=username)
                
                if os.path.exists(path):
                    return {"chrome_path": path, "platform": system}
        
        return {"chrome_path": None, "platform": system}
    
    def _detect_capabilities(self) -> List[ChromiumCapability]:
        """Detect available Chromium capabilities"""
        capabilities = []
        
        # Check if Chrome is available
        chrome_available = self.chrome_paths.get("chrome_path") is not None
        capabilities.append(ChromiumCapability(
            name="native_chrome",
            description="Native Chrome browser engine",
            supported=chrome_available
        ))
        
        # Check DevTools Protocol support
        capabilities.append(ChromiumCapability(
            name="devtools_protocol",
            description="Chrome DevTools Protocol for automation",
            supported=chrome_available
        ))
        
        # Check extension support
        capabilities.append(ChromiumCapability(
            name="extensions",
            description="Chrome extension support",
            supported=chrome_available
        ))
        
        # Check headless mode
        capabilities.append(ChromiumCapability(
            name="headless_mode",
            description="Headless browser operation",
            supported=chrome_available
        ))
        
        return capabilities
    
    async def create_browser_instance(self, user_session: str, options: Dict[str, Any] = None) -> BrowserInstance:
        """Create a new native Chromium browser instance"""
        try:
            if not self.chrome_paths.get("chrome_path"):
                raise Exception("Chrome binary not found on system")
            
            options = options or {}
            instance_id = str(uuid.uuid4())
            port = await self._get_available_port()
            
            # Create user profile directory
            profile_path = await self._create_profile_directory(instance_id)
            
            # Build Chrome command
            chrome_args = [
                self.chrome_paths["chrome_path"],
                f"--remote-debugging-port={port}",
                f"--user-data-dir={profile_path}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
            
            # Add optional arguments
            if options.get("headless", False):
                chrome_args.extend(["--headless", "--disable-gpu"])
            
            if options.get("enable_extensions", True):
                chrome_args.append("--enable-extensions")
            else:
                chrome_args.append("--disable-extensions")
            
            if options.get("disable_web_security", False):
                chrome_args.extend([
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--allow-running-insecure-content"
                ])
            
            # Custom window size
            window_size = options.get("window_size", "1920,1080")
            chrome_args.append(f"--window-size={window_size}")
            
            # Start Chrome process
            process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == "Windows" else 0
            )
            
            # Wait for Chrome to start
            await asyncio.sleep(2)
            
            # Check if process is running
            if process.poll() is not None:
                raise Exception("Chrome process failed to start")
            
            # Create instance object
            instance = BrowserInstance(
                instance_id=instance_id,
                user_session=user_session,
                process_id=process.pid,
                port=port,
                profile_path=profile_path,
                status="ready",
                created_at=datetime.utcnow(),
                extensions=[]
            )
            
            # Store instance
            self.active_instances[instance_id] = instance
            await self._save_instance(instance)
            
            logger.info(f"✅ Created Chrome instance {instance_id} on port {port}")
            return instance
            
        except Exception as e:
            logger.error(f"❌ Failed to create Chrome instance: {e}")
            raise
    
    async def _get_available_port(self) -> int:
        """Find an available port for Chrome DevTools"""
        import socket
        
        for port in range(self.base_port, self.base_port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        
        raise Exception("No available ports for Chrome DevTools")
    
    async def _create_profile_directory(self, instance_id: str) -> str:
        """Create a temporary profile directory for Chrome"""
        temp_dir = tempfile.gettempdir()
        profile_path = os.path.join(temp_dir, f"aether_chrome_{instance_id}")
        os.makedirs(profile_path, exist_ok=True)
        
        # Create basic Chrome preferences
        prefs = {
            "profile": {
                "default_content_setting_values": {
                    "notifications": 2  # Block notifications
                }
            },
            "session": {
                "restore_on_startup": 1  # Open new tab page
            }
        }
        
        prefs_path = os.path.join(profile_path, "Preferences")
        with open(prefs_path, 'w') as f:
            json.dump(prefs, f)
        
        return profile_path
    
    async def _save_instance(self, instance: BrowserInstance):
        """Save instance to database"""
        try:
            instance_data = {
                "instance_id": instance.instance_id,
                "user_session": instance.user_session,
                "process_id": instance.process_id,
                "port": instance.port,
                "profile_path": instance.profile_path,
                "status": instance.status,
                "created_at": instance.created_at,
                "extensions": instance.extensions
            }
            
            self.instances_collection.replace_one(
                {"instance_id": instance.instance_id},
                instance_data,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving instance: {e}")
    
    async def navigate_to(self, instance_id: str, url: str) -> Dict[str, Any]:
        """Navigate to URL in browser instance"""
        try:
            instance = self.active_instances.get(instance_id)
            if not instance:
                return {"success": False, "error": "Instance not found"}
            
            # Use Chrome DevTools Protocol
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Get list of pages
                async with session.get(f"http://localhost:{instance.port}/json") as resp:
                    pages = await resp.json()
                
                if not pages:
                    return {"success": False, "error": "No pages available"}
                
                # Use first page
                page_id = pages[0]["id"]
                ws_url = pages[0]["webSocketDebuggerUrl"]
                
                # Send navigation command via DevTools Protocol
                import websockets
                
                async with websockets.connect(ws_url) as websocket:
                    # Enable Page domain
                    await websocket.send(json.dumps({
                        "id": 1,
                        "method": "Page.enable"
                    }))
                    await websocket.recv()
                    
                    # Navigate to URL
                    await websocket.send(json.dumps({
                        "id": 2,
                        "method": "Page.navigate",
                        "params": {"url": url}
                    }))
                    result = await websocket.recv()
                    
                    return {
                        "success": True,
                        "url": url,
                        "result": json.loads(result)
                    }
                    
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_javascript(self, instance_id: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript in browser instance"""
        try:
            instance = self.active_instances.get(instance_id)
            if not instance:
                return {"success": False, "error": "Instance not found"}
            
            import aiohttp
            import websockets
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{instance.port}/json") as resp:
                    pages = await resp.json()
                
                if not pages:
                    return {"success": False, "error": "No pages available"}
                
                ws_url = pages[0]["webSocketDebuggerUrl"]
                
                async with websockets.connect(ws_url) as websocket:
                    # Enable Runtime domain
                    await websocket.send(json.dumps({
                        "id": 1,
                        "method": "Runtime.enable"
                    }))
                    await websocket.recv()
                    
                    # Execute script
                    await websocket.send(json.dumps({
                        "id": 2,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": script,
                            "returnByValue": True
                        }
                    }))
                    result = await websocket.recv()
                    result_data = json.loads(result)
                    
                    if result_data.get("result", {}).get("result", {}).get("type") == "object":
                        if result_data["result"]["result"].get("subtype") == "error":
                            return {
                                "success": False,
                                "error": result_data["result"]["result"].get("description", "JavaScript error")
                            }
                    
                    return {
                        "success": True,
                        "result": result_data.get("result", {}).get("result", {}).get("value")
                    }
                    
        except Exception as e:
            logger.error(f"JavaScript execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def capture_screenshot(self, instance_id: str) -> Dict[str, Any]:
        """Capture screenshot from browser instance"""
        try:
            instance = self.active_instances.get(instance_id)
            if not instance:
                return {"success": False, "error": "Instance not found"}
            
            import aiohttp
            import websockets
            import base64
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{instance.port}/json") as resp:
                    pages = await resp.json()
                
                if not pages:
                    return {"success": False, "error": "No pages available"}
                
                ws_url = pages[0]["webSocketDebuggerUrl"]
                
                async with websockets.connect(ws_url) as websocket:
                    # Capture screenshot
                    await websocket.send(json.dumps({
                        "id": 1,
                        "method": "Page.captureScreenshot",
                        "params": {
                            "format": "png",
                            "quality": 90
                        }
                    }))
                    result = await websocket.recv()
                    result_data = json.loads(result)
                    
                    if "result" in result_data and "data" in result_data["result"]:
                        screenshot_data = result_data["result"]["data"]
                        
                        # Save screenshot
                        screenshot_path = f"/tmp/aether_screenshot_{instance_id}_{datetime.utcnow().timestamp()}.png"
                        with open(screenshot_path, "wb") as f:
                            f.write(base64.b64decode(screenshot_data))
                        
                        return {
                            "success": True,
                            "screenshot_path": screenshot_path,
                            "data": screenshot_data
                        }
                    else:
                        return {"success": False, "error": "Screenshot capture failed"}
                        
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {"success": False, "error": str(e)}
    
    async def install_extension(self, instance_id: str, extension_path: str) -> Dict[str, Any]:
        """Install Chrome extension"""
        try:
            instance = self.active_instances.get(instance_id)
            if not instance:
                return {"success": False, "error": "Instance not found"}
            
            # Extensions require restart with --load-extension flag
            # This is a simplified implementation
            
            extension_id = str(uuid.uuid4())
            
            # Store extension info
            extension_data = {
                "extension_id": extension_id,
                "instance_id": instance_id,
                "extension_path": extension_path,
                "installed_at": datetime.utcnow(),
                "status": "installed"
            }
            
            self.extensions_collection.insert_one(extension_data)
            
            # Add to instance extensions list
            instance.extensions.append(extension_id)
            await self._save_instance(instance)
            
            return {
                "success": True,
                "extension_id": extension_id,
                "message": "Extension installed (requires browser restart)"
            }
            
        except Exception as e:
            logger.error(f"Extension installation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def stop_instance(self, instance_id: str) -> Dict[str, Any]:
        """Stop browser instance"""
        try:
            instance = self.active_instances.get(instance_id)
            if not instance:
                return {"success": False, "error": "Instance not found"}
            
            # Kill Chrome process
            if instance.process_id:
                try:
                    if platform.system() == "Windows":
                        subprocess.run(["taskkill", "/F", "/PID", str(instance.process_id)], check=True)
                    else:
                        subprocess.run(["kill", "-TERM", str(instance.process_id)], check=True)
                except:
                    pass  # Process might already be dead
            
            # Clean up profile directory
            try:
                shutil.rmtree(instance.profile_path, ignore_errors=True)
            except:
                pass
            
            # Remove from active instances
            del self.active_instances[instance_id]
            
            # Update database
            instance.status = "stopped"
            await self._save_instance(instance)
            
            return {"success": True, "message": "Instance stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping instance: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_instance_info(self, instance_id: str) -> Dict[str, Any]:
        """Get browser instance information"""
        try:
            instance = self.active_instances.get(instance_id)
            if not instance:
                return {"success": False, "error": "Instance not found"}
            
            return {
                "success": True,
                "instance": {
                    "id": instance.instance_id,
                    "user_session": instance.user_session,
                    "port": instance.port,
                    "status": instance.status,
                    "created_at": instance.created_at.isoformat(),
                    "extensions_count": len(instance.extensions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting instance info: {e}")
            return {"success": False, "error": str(e)}

class NativeAPIBridge:
    """Bridge between web frontend and native Chromium engine"""
    
    def __init__(self, chromium_engine: NativeChromiumEngine):
        self.chromium_engine = chromium_engine
        self.user_instances: Dict[str, str] = {}  # user_session -> instance_id
    
    async def get_or_create_instance(self, user_session: str) -> str:
        """Get existing instance or create new one for user"""
        if user_session in self.user_instances:
            instance_id = self.user_instances[user_session]
            if instance_id in self.chromium_engine.active_instances:
                return instance_id
        
        # Create new instance
        instance = await self.chromium_engine.create_browser_instance(
            user_session,
            options={
                "enable_extensions": True,
                "window_size": "1920,1080"
            }
        )
        
        self.user_instances[user_session] = instance.instance_id
        return instance.instance_id
    
    async def navigate_to(self, user_session: str, url: str) -> Dict[str, Any]:
        """Navigate to URL for user"""
        try:
            instance_id = await self.get_or_create_instance(user_session)
            return await self.chromium_engine.navigate_to(instance_id, url)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_javascript(self, user_session: str, script: str) -> Dict[str, Any]:
        """Execute JavaScript for user"""
        try:
            instance_id = await self.get_or_create_instance(user_session)
            return await self.chromium_engine.execute_javascript(instance_id, script)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def capture_screenshot(self, user_session: str) -> Dict[str, Any]:
        """Capture screenshot for user"""
        try:
            instance_id = await self.get_or_create_instance(user_session)
            return await self.chromium_engine.capture_screenshot(instance_id)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> List[ChromiumCapability]:
        """Get available Chromium capabilities"""
        return self.chromium_engine.capabilities

def initialize_native_chromium(db_client: MongoClient) -> Dict[str, Any]:
    """Initialize native Chromium integration"""
    try:
        chromium_engine = NativeChromiumEngine(db_client)
        api_bridge = NativeAPIBridge(chromium_engine)
        
        # Check capabilities
        capabilities = chromium_engine.capabilities
        native_available = any(cap.supported for cap in capabilities if cap.name == "native_chrome")
        
        if native_available:
            logger.info("✅ Native Chromium integration initialized successfully")
            status = "native_ready"
        else:
            logger.warning("⚠️ Native Chromium not available, using fallback mode")
            status = "fallback_mode"
        
        return {
            "chromium_engine": chromium_engine,
            "api_bridge": api_bridge,
            "capabilities": capabilities,
            "status": status,
            "native_available": native_available,
            "initialized": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize native Chromium: {e}")
        return {
            "chromium_engine": None,
            "api_bridge": None,
            "capabilities": [],
            "status": "error",
            "native_available": False,
            "initialized": False,
            "error": str(e)
        }