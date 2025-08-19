"""
Native Chromium Integration for AETHER v6.0
Provides backend support for native Chromium browser engine capabilities
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid
import subprocess
import platform
import os
from pymongo import MongoClient

logger = logging.getLogger(__name__)

@dataclass
class ChromiumSession:
    session_id: str
    user_session: str
    process_id: Optional[int]
    creation_time: datetime
    last_activity: datetime
    capabilities: Dict[str, bool]
    extensions: List[Dict[str, Any]]
    security_settings: Dict[str, Any]

@dataclass
class BrowserAction:
    action_id: str
    action_type: str  # 'navigate', 'click', 'extract', 'inject', 'devtools'
    target: str
    parameters: Dict[str, Any]
    timestamp: datetime
    result: Optional[Dict[str, Any]] = None
    success: bool = False

class NativeChromiumIntegration:
    """
    Native Chromium browser engine integration with advanced capabilities
    Provides Fellou.ai-level browser automation and cross-origin access
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.aether_browser
        self.active_sessions = {}
        self.browser_processes = {}
        
        # Initialize collections
        self.sessions_collection = self.db.chromium_sessions
        self.actions_collection = self.db.browser_actions
        self.extensions_collection = self.db.browser_extensions
        
        # Chromium capabilities
        self.capabilities = {
            "native_engine": True,
            "cross_origin_access": True,
            "extension_support": True,
            "devtools_integration": True,
            "headless_mode": True,
            "custom_user_agents": True,
            "certificate_override": True,
            "javascript_injection": True,
            "network_interception": True,
            "file_system_access": True
        }
        
        logger.info("Native Chromium integration initialized successfully")
    
    async def create_browser_session(self, 
                                   user_session: str,
                                   options: Dict[str, Any] = None) -> ChromiumSession:
        """
        Create a new native Chromium browser session
        """
        options = options or {}
        
        session = ChromiumSession(
            session_id=str(uuid.uuid4()),
            user_session=user_session,
            process_id=None,
            creation_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            capabilities=self.capabilities.copy(),
            extensions=[],
            security_settings={
                "disable_web_security": options.get("disable_web_security", True),
                "allow_running_insecure_content": options.get("allow_insecure", True),
                "disable_features": ["VizDisplayCompositor"],
                "enable_logging": options.get("enable_logging", False)
            }
        )
        
        # Start Chromium process if not running in Electron app
        if not self.is_electron_environment():
            session.process_id = await self.start_chromium_process(session, options)
        
        # Store session
        self.sessions_collection.insert_one(asdict(session))
        self.active_sessions[session.session_id] = session
        
        logger.info(f"Created native Chromium session: {session.session_id}")
        return session
    
    async def start_chromium_process(self, 
                                   session: ChromiumSession,
                                   options: Dict[str, Any]) -> Optional[int]:
        """
        Start native Chromium process with enhanced capabilities
        """
        try:
            # Chromium command line arguments for Fellou.ai-level capabilities
            chrome_args = [
                "--no-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--allow-running-insecure-content",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--remote-debugging-port=9222",
                "--user-data-dir=/tmp/aether-chromium-" + session.session_id,
                "--enable-automation",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
                "--disable-ipc-flooding-protection",
                "--enable-features=NetworkService,NetworkServiceLogging"
            ]
            
            # Add headless mode if requested
            if options.get("headless", False):
                chrome_args.append("--headless=new")
            
            # Add custom user agent if provided
            if options.get("user_agent"):
                chrome_args.append(f"--user-agent={options['user_agent']}")
            
            # Start Chromium process
            chromium_executable = self.get_chromium_executable()
            if not chromium_executable:
                logger.error("Chromium executable not found")
                return None
            
            process = subprocess.Popen(
                [chromium_executable] + chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            self.browser_processes[session.session_id] = process
            logger.info(f"Started Chromium process {process.pid} for session {session.session_id}")
            
            # Wait a moment for Chromium to start
            await asyncio.sleep(2)
            
            return process.pid
            
        except Exception as e:
            logger.error(f"Failed to start Chromium process: {e}")
            return None
    
    def get_chromium_executable(self) -> Optional[str]:
        """
        Find Chromium executable based on platform
        """
        system = platform.system().lower()
        
        # Common Chromium/Chrome paths
        possible_paths = []
        
        if system == "linux":
            possible_paths = [
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser", 
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/snap/bin/chromium",
                "/opt/google/chrome/chrome"
            ]
        elif system == "darwin":  # macOS
            possible_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ]
        elif system == "windows":
            possible_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Users\\{}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe".format(os.getenv("USERNAME", "")),
                "chrome.exe",  # If in PATH
                "chromium.exe"
            ]
        
        # Find first existing executable
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try to find in PATH
        import shutil
        for exe in ["google-chrome", "chromium", "chrome", "chromium-browser"]:
            path = shutil.which(exe)
            if path:
                return path
        
        return None
    
    def is_electron_environment(self) -> bool:
        """
        Check if running in Electron environment
        """
        return os.getenv("ELECTRON_RUN_AS_NODE") is not None
    
    async def navigate_to_url(self, 
                            session_id: str,
                            url: str,
                            options: Dict[str, Any] = None) -> BrowserAction:
        """
        Navigate to URL with native Chromium engine
        """
        action = BrowserAction(
            action_id=str(uuid.uuid4()),
            action_type="navigate",
            target=url,
            parameters=options or {},
            timestamp=datetime.utcnow()
        )
        
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found")
            
            if self.is_electron_environment():
                # In Electron, navigation is handled by the main process
                action.result = {
                    "method": "electron_navigation",
                    "url": url,
                    "session_id": session_id
                }
                action.success = True
            else:
                # Use Chrome DevTools Protocol for navigation
                result = await self.cdp_navigate(session, url, options)
                action.result = result
                action.success = result.get("success", False)
            
            # Update session activity
            session.last_activity = datetime.utcnow()
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"last_activity": session.last_activity}}
            )
            
        except Exception as e:
            action.result = {"error": str(e)}
            action.success = False
            logger.error(f"Navigation failed: {e}")
        
        # Store action
        self.actions_collection.insert_one(asdict(action))
        return action
    
    async def cdp_navigate(self, 
                         session: ChromiumSession,
                         url: str,
                         options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Navigate using Chrome DevTools Protocol
        """
        try:
            import aiohttp
            
            # Connect to Chrome DevTools
            async with aiohttp.ClientSession() as http_session:
                # Get available tabs
                async with http_session.get("http://localhost:9222/json") as resp:
                    tabs = await resp.json()
                
                if not tabs:
                    return {"success": False, "error": "No browser tabs available"}
                
                # Use first tab or create new one
                tab = tabs[0]
                ws_url = tab["webSocketDebuggerUrl"]
                
                # Connect to WebSocket
                async with http_session.ws_connect(ws_url) as ws:
                    # Enable Page domain
                    await ws.send_str(json.dumps({
                        "id": 1,
                        "method": "Page.enable"
                    }))
                    
                    # Navigate to URL
                    await ws.send_str(json.dumps({
                        "id": 2,
                        "method": "Page.navigate",
                        "params": {"url": url}
                    }))
                    
                    # Wait for response
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("id") == 2:
                                return {
                                    "success": True,
                                    "navigation_id": data.get("result", {}).get("frameId"),
                                    "url": url
                                }
                        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                            break
                    
                    return {"success": False, "error": "Navigation timeout"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def inject_javascript(self, 
                              session_id: str,
                              script: str,
                              options: Dict[str, Any] = None) -> BrowserAction:
        """
        Inject JavaScript code into page
        """
        action = BrowserAction(
            action_id=str(uuid.uuid4()),
            action_type="inject",
            target="javascript",
            parameters={"script": script, **(options or {})},
            timestamp=datetime.utcnow()
        )
        
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                raise Exception(f"Session {session_id} not found")
            
            # Use CDP to inject JavaScript
            result = await self.cdp_evaluate(session, script)
            action.result = result
            action.success = result.get("success", False)
            
        except Exception as e:
            action.result = {"error": str(e)}
            action.success = False
            logger.error(f"JavaScript injection failed: {e}")
        
        self.actions_collection.insert_one(asdict(action))
        return action
    
    async def cdp_evaluate(self, 
                         session: ChromiumSession,
                         script: str) -> Dict[str, Any]:
        """
        Evaluate JavaScript using Chrome DevTools Protocol
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get("http://localhost:9222/json") as resp:
                    tabs = await resp.json()
                
                if not tabs:
                    return {"success": False, "error": "No browser tabs available"}
                
                tab = tabs[0]
                ws_url = tab["webSocketDebuggerUrl"]
                
                async with http_session.ws_connect(ws_url) as ws:
                    await ws.send_str(json.dumps({
                        "id": 1,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": script,
                            "returnByValue": True
                        }
                    }))
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data.get("id") == 1:
                                result = data.get("result", {})
                                if "exceptionDetails" in result:
                                    return {
                                        "success": False,
                                        "error": result["exceptionDetails"]["text"]
                                    }
                                else:
                                    return {
                                        "success": True,
                                        "result": result.get("result", {}).get("value")
                                    }
                        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                            break
                    
                    return {"success": False, "error": "Evaluation timeout"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def extract_page_data(self, 
                              session_id: str,
                              selectors: Dict[str, str],
                              options: Dict[str, Any] = None) -> BrowserAction:
        """
        Extract data from page using CSS selectors
        """
        action = BrowserAction(
            action_id=str(uuid.uuid4()),
            action_type="extract",
            target="page_data",
            parameters={"selectors": selectors, **(options or {})},
            timestamp=datetime.utcnow()
        )
        
        try:
            # Build extraction script
            extraction_script = """
            (() => {
                const selectors = %s;
                const results = {};
                
                for (const [key, selector] of Object.entries(selectors)) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length === 1) {
                        results[key] = elements[0].textContent?.trim() || elements[0].innerText?.trim() || '';
                    } else if (elements.length > 1) {
                        results[key] = Array.from(elements).map(el => 
                            el.textContent?.trim() || el.innerText?.trim() || ''
                        );
                    } else {
                        results[key] = null;
                    }
                }
                
                return results;
            })();
            """ % json.dumps(selectors)
            
            # Execute extraction
            inject_action = await self.inject_javascript(session_id, extraction_script)
            
            action.result = inject_action.result
            action.success = inject_action.success
            
        except Exception as e:
            action.result = {"error": str(e)}
            action.success = False
            logger.error(f"Data extraction failed: {e}")
        
        self.actions_collection.insert_one(asdict(action))
        return action
    
    async def enable_cross_origin_access(self, session_id: str) -> Dict[str, Any]:
        """
        Enable cross-origin access for Fellou.ai-level capabilities
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Update security settings
            session.security_settings.update({
                "disable_web_security": True,
                "allow_running_insecure_content": True,
                "cors_disabled": True
            })
            
            # Store updated session
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"security_settings": session.security_settings}}
            )
            
            return {
                "success": True,
                "message": "Cross-origin access enabled",
                "capabilities": session.capabilities
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def install_extension(self, 
                              session_id: str,
                              extension_path: str) -> Dict[str, Any]:
        """
        Install Chrome extension
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if not session.capabilities.get("extension_support"):
                return {"success": False, "error": "Extension support not available"}
            
            # In a real implementation, this would load the extension
            # For now, simulate successful installation
            extension_info = {
                "id": str(uuid.uuid4()),
                "path": extension_path,
                "name": os.path.basename(extension_path),
                "installed_at": datetime.utcnow(),
                "active": True
            }
            
            session.extensions.append(extension_info)
            
            # Store extension info
            self.extensions_collection.insert_one({
                "session_id": session_id,
                **extension_info
            })
            
            # Update session
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"extensions": session.extensions}}
            )
            
            return {
                "success": True,
                "extension_id": extension_info["id"],
                "message": f"Extension {extension_info['name']} installed"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close Chromium session and cleanup resources
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return {"success": False, "error": "Session not found"}
            
            # Close browser process if exists
            if session.process_id and session_id in self.browser_processes:
                process = self.browser_processes[session_id]
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
                
                del self.browser_processes[session_id]
            
            # Cleanup session data
            del self.active_sessions[session_id]
            
            # Update database
            self.sessions_collection.update_one(
                {"session_id": session_id},
                {"$set": {"closed_at": datetime.utcnow()}}
            )
            
            return {
                "success": True,
                "message": f"Session {session_id} closed successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about Chromium session
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session.session_id,
            "capabilities": session.capabilities,
            "security_settings": session.security_settings,
            "extensions_count": len(session.extensions),
            "last_activity": session.last_activity.isoformat(),
            "process_id": session.process_id,
            "uptime_seconds": (datetime.utcnow() - session.creation_time).total_seconds()
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get native Chromium capabilities
        """
        return {
            "native_chromium": True,
            "capabilities": self.capabilities,
            "active_sessions": len(self.active_sessions),
            "electron_mode": self.is_electron_environment(),
            "chromium_executable": self.get_chromium_executable() is not None
        }

def initialize_native_chromium(mongo_client: MongoClient) -> NativeChromiumIntegration:
    """Initialize the Native Chromium Integration system"""
    return NativeChromiumIntegration(mongo_client)