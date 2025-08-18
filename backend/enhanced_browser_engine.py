"""
AETHER Enhanced Browser Engine
Advanced browser capabilities moving beyond iframe limitations
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pymongo import MongoClient
from dataclasses import dataclass
import base64
import subprocess
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import random
import time

logger = logging.getLogger(__name__)

@dataclass
class BrowserSession:
    """Browser session management"""
    session_id: str
    user_session: str
    driver: Optional[webdriver.Chrome] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    stealth_enabled: bool = True
    fingerprint_spoofing: bool = True

class StealthBrowserManager:
    """Advanced stealth browser with fingerprint spoofing"""
    
    def __init__(self):
        self.user_agent = UserAgent()
        self.active_sessions = {}
        
    def create_stealth_options(self, custom_fingerprint: Dict[str, Any] = None) -> Options:
        """Create Chrome options with advanced stealth capabilities"""
        options = uc.ChromeOptions()
        
        # Basic stealth options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Advanced fingerprint spoofing
        if custom_fingerprint:
            # User agent spoofing
            user_agent = custom_fingerprint.get("user_agent", self.user_agent.random)
            options.add_argument(f"--user-agent={user_agent}")
            
            # Screen resolution spoofing
            resolution = custom_fingerprint.get("resolution", "1920,1080")
            options.add_argument(f"--window-size={resolution}")
            
            # Language spoofing
            language = custom_fingerprint.get("language", "en-US,en;q=0.9")
            options.add_argument(f"--lang={language}")
            
            # Timezone spoofing
            timezone = custom_fingerprint.get("timezone", "America/New_York")
            options.add_argument(f"--timezone={timezone}")
        
        # Disable automation indicators
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add custom preferences
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2,  # Disable images for speed
            "profile.default_content_setting_values.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    async def create_browser_session(self, user_session: str, stealth_config: Dict[str, Any] = None) -> str:
        """Create new browser session with advanced stealth"""
        try:
            session_id = str(uuid.uuid4())
            
            # Generate random fingerprint
            fingerprint = self._generate_fingerprint(stealth_config)
            
            # Create stealth options
            options = self.create_stealth_options(fingerprint)
            
            # Create undetected Chrome driver
            driver = uc.Chrome(options=options, version_main=None)
            
            # Execute stealth scripts
            await self._apply_stealth_scripts(driver, fingerprint)
            
            # Create session
            browser_session = BrowserSession(
                session_id=session_id,
                user_session=user_session,
                driver=driver,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                stealth_enabled=True,
                fingerprint_spoofing=True
            )
            
            self.active_sessions[session_id] = browser_session
            
            logger.info(f"Created stealth browser session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create browser session: {e}")
            return None
    
    def _generate_fingerprint(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate realistic browser fingerprint"""
        # List of realistic screen resolutions
        resolutions = [
            "1920,1080", "1366,768", "1536,864", "1440,900", 
            "1280,720", "1600,900", "2560,1440", "3840,2160"
        ]
        
        # List of realistic languages
        languages = [
            "en-US,en;q=0.9", "en-GB,en;q=0.9", "es-ES,es;q=0.9",
            "fr-FR,fr;q=0.9", "de-DE,de;q=0.9", "pt-BR,pt;q=0.9"
        ]
        
        # List of realistic timezones
        timezones = [
            "America/New_York", "America/Chicago", "America/Denver", 
            "America/Los_Angeles", "Europe/London", "Europe/Paris",
            "Asia/Tokyo", "Australia/Sydney"
        ]
        
        fingerprint = {
            "user_agent": self.user_agent.random,
            "resolution": random.choice(resolutions),
            "language": random.choice(languages),
            "timezone": random.choice(timezones),
            "webgl_vendor": random.choice(["Intel Inc.", "NVIDIA Corporation", "AMD"]),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "color_depth": random.choice([24, 32]),
            "device_memory": random.choice([4, 8, 16]),
            "hardware_concurrency": random.choice([4, 8, 12, 16])
        }
        
        # Apply custom config if provided
        if config:
            fingerprint.update(config)
        
        return fingerprint
    
    async def _apply_stealth_scripts(self, driver: webdriver.Chrome, fingerprint: Dict[str, Any]):
        """Apply JavaScript-based stealth modifications"""
        try:
            # Override navigator properties
            stealth_script = f"""
            // Override webdriver property
            Object.defineProperty(navigator, 'webdriver', {{
                get: () => undefined,
            }});
            
            // Override chrome property
            window.chrome = {{
                runtime: {{
                    onConnect: undefined,
                    onMessage: undefined,
                }},
            }};
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({{ state: Notification.permission }}) :
                    originalQuery(parameters)
            );
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {{
                get: () => [{{
                    0: {{ type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format" }},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }}],
            }});
            
            // Override webgl
            const getParameter = WebGLRenderingContext.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                if (parameter === 37445) return '{fingerprint.get("webgl_vendor", "Intel Inc.")}';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter(parameter);
            }};
            
            // Override hardwareConcurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', {{
                get: () => {fingerprint.get("hardware_concurrency", 8)},
            }});
            
            // Override deviceMemory
            Object.defineProperty(navigator, 'deviceMemory', {{
                get: () => {fingerprint.get("device_memory", 8)},
            }});
            
            // Override platform
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint.get("platform", "Win32")}',
            }});
            """
            
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": stealth_script
            })
            
        except Exception as e:
            logger.error(f"Failed to apply stealth scripts: {e}")

class AdvancedBrowserAutomation:
    """Advanced browser automation with AI-powered interactions"""
    
    def __init__(self, stealth_manager: StealthBrowserManager):
        self.stealth_manager = stealth_manager
        
    async def navigate_with_intelligence(self, session_id: str, url: str, 
                                       wait_for_element: str = None) -> Dict[str, Any]:
        """Navigate to URL with intelligent waiting"""
        try:
            session = self.stealth_manager.active_sessions.get(session_id)
            if not session or not session.driver:
                return {"error": "Invalid session"}
            
            driver = session.driver
            
            # Add random delay to mimic human behavior
            await asyncio.sleep(random.uniform(1, 3))
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for specific element if provided
            if wait_for_element:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            
            # Update session activity
            session.last_activity = datetime.utcnow()
            
            return {
                "status": "success",
                "url": driver.current_url,
                "title": driver.title,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except TimeoutException:
            return {"error": "Page load timeout"}
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return {"error": str(e)}
    
    async def extract_page_data(self, session_id: str, extraction_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract data from current page with AI enhancement"""
        try:
            session = self.stealth_manager.active_sessions.get(session_id)
            if not session or not session.driver:
                return {"error": "Invalid session"}
            
            driver = session.driver
            
            # Basic page data
            page_data = {
                "url": driver.current_url,
                "title": driver.title,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Extract text content
            if not extraction_config or extraction_config.get("extract_text", True):
                page_data["text"] = driver.find_element(By.TAG_NAME, "body").text
            
            # Extract links
            if not extraction_config or extraction_config.get("extract_links", True):
                links = []
                for link in driver.find_elements(By.TAG_NAME, "a"):
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    if href and text:
                        links.append({"url": href, "text": text})
                page_data["links"] = links[:50]  # Limit to 50 links
            
            # Extract images
            if not extraction_config or extraction_config.get("extract_images", True):
                images = []
                for img in driver.find_elements(By.TAG_NAME, "img"):
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt")
                    if src:
                        images.append({"src": src, "alt": alt or ""})
                page_data["images"] = images[:20]  # Limit to 20 images
            
            # Extract forms
            if extraction_config and extraction_config.get("extract_forms", False):
                forms = []
                for form in driver.find_elements(By.TAG_NAME, "form"):
                    form_data = {
                        "action": form.get_attribute("action"),
                        "method": form.get_attribute("method"),
                        "inputs": []
                    }
                    for input_elem in form.find_elements(By.TAG_NAME, "input"):
                        form_data["inputs"].append({
                            "type": input_elem.get_attribute("type"),
                            "name": input_elem.get_attribute("name"),
                            "placeholder": input_elem.get_attribute("placeholder")
                        })
                    forms.append(form_data)
                page_data["forms"] = forms
            
            # Custom CSS selectors
            if extraction_config and "selectors" in extraction_config:
                custom_data = {}
                for selector_name, selector in extraction_config["selectors"].items():
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        custom_data[selector_name] = [elem.text for elem in elements[:10]]
                    except Exception as e:
                        custom_data[selector_name] = f"Error: {str(e)}"
                page_data["custom_data"] = custom_data
            
            return page_data
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return {"error": str(e)}
    
    async def intelligent_form_filling(self, session_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill forms intelligently with human-like behavior"""
        try:
            session = self.stealth_manager.active_sessions.get(session_id)
            if not session or not session.driver:
                return {"error": "Invalid session"}
            
            driver = session.driver
            filled_fields = []
            
            for field_identifier, value in form_data.items():
                try:
                    # Try multiple strategies to find the field
                    element = None
                    
                    # Try by name
                    try:
                        element = driver.find_element(By.NAME, field_identifier)
                    except:
                        pass
                    
                    # Try by id
                    if not element:
                        try:
                            element = driver.find_element(By.ID, field_identifier)
                        except:
                            pass
                    
                    # Try by CSS selector
                    if not element:
                        try:
                            element = driver.find_element(By.CSS_SELECTOR, field_identifier)
                        except:
                            pass
                    
                    if element:
                        # Scroll to element
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        
                        # Human-like delay
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        
                        # Clear and fill
                        element.clear()
                        
                        # Type with human-like delays
                        for char in str(value):
                            element.send_keys(char)
                            await asyncio.sleep(random.uniform(0.05, 0.15))
                        
                        filled_fields.append({
                            "field": field_identifier,
                            "status": "success"
                        })
                    else:
                        filled_fields.append({
                            "field": field_identifier,
                            "status": "not_found"
                        })
                        
                except Exception as field_error:
                    filled_fields.append({
                        "field": field_identifier,
                        "status": "error",
                        "error": str(field_error)
                    })
            
            return {
                "status": "completed",
                "filled_fields": filled_fields,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Form filling failed: {e}")
            return {"error": str(e)}
    
    async def take_screenshot(self, session_id: str, element_selector: str = None) -> Dict[str, Any]:
        """Take screenshot of page or specific element"""
        try:
            session = self.stealth_manager.active_sessions.get(session_id)
            if not session or not session.driver:
                return {"error": "Invalid session"}
            
            driver = session.driver
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                if element_selector:
                    # Screenshot specific element
                    element = driver.find_element(By.CSS_SELECTOR, element_selector)
                    element.screenshot(tmp.name)
                else:
                    # Full page screenshot
                    driver.save_screenshot(tmp.name)
                
                # Read and encode screenshot
                with open(tmp.name, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                
                # Clean up
                os.unlink(tmp.name)
                
                return {
                    "status": "success",
                    "screenshot": img_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return {"error": str(e)}

class EnhancedBrowserEngine:
    """Main enhanced browser engine"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.browser_sessions = self.db.browser_sessions
        self.automation_logs = self.db.automation_logs
        
        # Initialize components
        self.stealth_manager = StealthBrowserManager()
        self.automation = AdvancedBrowserAutomation(self.stealth_manager)
        
        # Cleanup old sessions on startup
        asyncio.create_task(self._cleanup_old_sessions())
    
    async def create_enhanced_session(self, user_session: str, 
                                    stealth_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create enhanced browser session"""
        try:
            session_id = await self.stealth_manager.create_browser_session(user_session, stealth_config)
            
            if session_id:
                # Store session info in database
                session_data = {
                    "session_id": session_id,
                    "user_session": user_session,
                    "created_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow(),
                    "stealth_enabled": True,
                    "status": "active"
                }
                
                self.browser_sessions.insert_one(session_data)
                
                return {
                    "status": "success",
                    "session_id": session_id,
                    "capabilities": {
                        "stealth_browsing": True,
                        "fingerprint_spoofing": True,
                        "intelligent_automation": True,
                        "advanced_extraction": True
                    }
                }
            else:
                return {"error": "Failed to create browser session"}
                
        except Exception as e:
            logger.error(f"Failed to create enhanced session: {e}")
            return {"error": str(e)}
    
    async def navigate_intelligently(self, session_id: str, url: str, 
                                   options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Navigate with intelligent capabilities"""
        try:
            result = await self.automation.navigate_with_intelligence(
                session_id, url, options.get("wait_for_element") if options else None
            )
            
            # Log navigation
            await self._log_automation_activity(session_id, "navigate", {
                "url": url,
                "options": options or {},
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Intelligent navigation failed: {e}")
            return {"error": str(e)}
    
    async def extract_page_data_advanced(self, session_id: str, 
                                       extraction_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Advanced page data extraction"""
        try:
            result = await self.automation.extract_page_data(session_id, extraction_config)
            
            # Log extraction
            await self._log_automation_activity(session_id, "extract_data", {
                "config": extraction_config or {},
                "result_size": len(str(result))
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Advanced data extraction failed: {e}")
            return {"error": str(e)}
    
    async def automate_form_interaction(self, session_id: str, 
                                      form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligent form automation"""
        try:
            result = await self.automation.intelligent_form_filling(session_id, form_data)
            
            # Log form interaction
            await self._log_automation_activity(session_id, "form_filling", {
                "fields_count": len(form_data),
                "result": result
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Form automation failed: {e}")
            return {"error": str(e)}
    
    async def capture_advanced_screenshot(self, session_id: str, 
                                        options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Advanced screenshot capabilities"""
        try:
            element_selector = options.get("element_selector") if options else None
            result = await self.automation.take_screenshot(session_id, element_selector)
            
            return result
            
        except Exception as e:
            logger.error(f"Advanced screenshot failed: {e}")
            return {"error": str(e)}
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close browser session"""
        try:
            session = self.stealth_manager.active_sessions.get(session_id)
            if session and session.driver:
                session.driver.quit()
                del self.stealth_manager.active_sessions[session_id]
            
            # Update database
            self.browser_sessions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "closed", "closed_at": datetime.utcnow()}}
            )
            
            return {"status": "success", "message": "Session closed"}
            
        except Exception as e:
            logger.error(f"Failed to close session: {e}")
            return {"error": str(e)}
    
    async def get_active_sessions(self, user_session: str) -> List[Dict[str, Any]]:
        """Get user's active browser sessions"""
        try:
            sessions = list(self.browser_sessions.find(
                {"user_session": user_session, "status": "active"},
                {"_id": 0}
            ))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    async def _log_automation_activity(self, session_id: str, action: str, details: Dict[str, Any]):
        """Log automation activity"""
        try:
            log_entry = {
                "session_id": session_id,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow()
            }
            
            self.automation_logs.insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Failed to log automation activity: {e}")
    
    async def _cleanup_old_sessions(self):
        """Clean up old browser sessions"""
        try:
            # Close sessions older than 2 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            old_sessions = self.browser_sessions.find({
                "last_activity": {"$lt": cutoff_time},
                "status": "active"
            })
            
            for session_data in old_sessions:
                session_id = session_data["session_id"]
                await self.close_session(session_id)
                logger.info(f"Cleaned up old session: {session_id}")
                
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

# Initialize global instance
enhanced_browser_engine = None

def initialize_enhanced_browser_engine(mongo_client: MongoClient):
    """Initialize enhanced browser engine"""
    global enhanced_browser_engine
    enhanced_browser_engine = EnhancedBrowserEngine(mongo_client)
    return enhanced_browser_engine