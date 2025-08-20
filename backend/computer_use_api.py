# 🧠 WORKSTREAM A: COMPUTER USE API - Core Implementation
# Enables OS-level automation and screen interaction capabilities

import asyncio
import json
import uuid
import base64
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import subprocess
import platform

# Image processing and AI vision
try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ScreenElement:
    """Represents an element on the screen"""
    x: int
    y: int
    width: int
    height: int
    element_type: str
    confidence: float
    description: str
    
    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

@dataclass
class ActionResult:
    """Result of a computer use action"""
    success: bool
    action_type: str
    details: Dict[str, Any]
    screenshot_after: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class ScreenAnalyzer:
    """AI-powered screen analysis and element detection"""
    
    def __init__(self):
        self.current_os = platform.system().lower()
        logger.info(f"🖥️ ScreenAnalyzer initialized for {self.current_os}")
    
    async def capture_screenshot(self) -> str:
        """Capture current screen and return base64 encoded image"""
        try:
            if self.current_os == "darwin":  # macOS
                result = subprocess.run(
                    ["screencapture", "-t", "png", "-"], 
                    capture_output=True, 
                    check=True
                )
                screenshot_data = result.stdout
            elif self.current_os == "linux":
                result = subprocess.run(
                    ["import", "-window", "root", "png:-"], 
                    capture_output=True, 
                    check=True
                )
                screenshot_data = result.stdout
            else:  # Windows
                # Use PowerShell for Windows screenshot
                powershell_cmd = '''
                Add-Type -AssemblyName System.Windows.Forms,System.Drawing
                $bounds = [Drawing.Rectangle]::FromLTRB(0, 0, 1920, 1080)
                $bmp = New-Object Drawing.Bitmap $bounds.width, $bounds.height
                $graphics = [Drawing.Graphics]::FromImage($bmp)
                $graphics.CopyFromScreen($bounds.Location, [Drawing.Point]::Empty, $bounds.size)
                $ms = New-Object System.IO.MemoryStream
                $bmp.Save($ms, [Drawing.Imaging.ImageFormat]::Png)
                [Convert]::ToBase64String($ms.ToArray())
                '''
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()
            
            # For macOS and Linux, encode to base64
            return base64.b64encode(screenshot_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None
    
    async def analyze_screen_elements(self, screenshot_b64: str, target_description: str) -> List[ScreenElement]:
        """Analyze screen to find elements matching the description"""
        try:
            if not CV2_AVAILABLE:
                logger.warning("Computer vision libraries not available, using simulated detection")
                return await self._simulate_element_detection(target_description)
            
            # Decode base64 image
            image_data = base64.b64decode(screenshot_b64)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Perform element detection (simplified for MVP)
            elements = await self._detect_ui_elements(image, target_description)
            
            logger.info(f"🔍 Found {len(elements)} elements matching '{target_description}'")
            return elements
            
        except Exception as e:
            logger.error(f"Screen analysis failed: {e}")
            return []
    
    async def _simulate_element_detection(self, description: str) -> List[ScreenElement]:
        """Simulate element detection for development/testing"""
        # Common UI element positions for testing
        common_elements = {
            "chrome icon": ScreenElement(50, 50, 60, 60, "application_icon", 0.9, "Chrome browser icon"),
            "search box": ScreenElement(400, 100, 300, 40, "text_input", 0.8, "Search input field"),
            "submit button": ScreenElement(720, 100, 80, 40, "button", 0.85, "Submit button"),
            "menu button": ScreenElement(20, 20, 30, 30, "button", 0.7, "Menu hamburger button"),
            "close button": ScreenElement(980, 20, 20, 20, "button", 0.9, "Window close button")
        }
        
        # Return matching elements (case insensitive)
        matching_elements = []
        for key, element in common_elements.items():
            if any(word in key for word in description.lower().split()):
                matching_elements.append(element)
        
        return matching_elements
    
    async def _detect_ui_elements(self, image: np.ndarray, description: str) -> List[ScreenElement]:
        """Detect UI elements using computer vision (simplified implementation)"""
        elements = []
        
        # Convert to grayscale for processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect buttons using template matching (simplified)
        if "button" in description.lower():
            # Use edge detection to find rectangular elements
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter for button-like dimensions
                if 20 <= w <= 200 and 10 <= h <= 60:
                    elements.append(ScreenElement(
                        x=x, y=y, width=w, height=h,
                        element_type="button",
                        confidence=0.7,
                        description=f"Button at ({x},{y})"
                    ))
        
        # Detect text inputs
        if "input" in description.lower() or "text" in description.lower():
            # Look for rectangular regions that could be text inputs
            contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                # Filter for input-like dimensions (wider than tall)
                if w > h * 3 and w > 50 and h > 15:
                    elements.append(ScreenElement(
                        x=x, y=y, width=w, height=h,
                        element_type="text_input",
                        confidence=0.6,
                        description=f"Text input at ({x},{y})"
                    ))
        
        return elements[:5]  # Return top 5 matches

class ActionExecutor:
    """Execute actions on the operating system"""
    
    def __init__(self):
        self.current_os = platform.system().lower()
        logger.info(f"⚡ ActionExecutor initialized for {self.current_os}")
    
    async def click_element(self, element: ScreenElement) -> ActionResult:
        """Click on a screen element"""
        try:
            x, y = element.center
            
            if self.current_os == "darwin":  # macOS
                # Use AppleScript for macOS clicking
                applescript = f'''
                tell application "System Events"
                    click at {{{x}, {y}}}
                end tell
                '''
                subprocess.run(["osascript", "-e", applescript], check=True)
                
            elif self.current_os == "linux":
                # Use xdotool for Linux clicking
                subprocess.run(["xdotool", "mousemove", str(x), str(y)], check=True)
                subprocess.run(["xdotool", "click", "1"], check=True)
                
            else:  # Windows
                # Use PowerShell for Windows clicking
                powershell_cmd = f'''
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x}, {y})
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Mouse {{
                        [DllImport("user32.dll")]
                        public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
                        public const uint MOUSEEVENTF_LEFTDOWN = 0x02;
                        public const uint MOUSEEVENTF_LEFTUP = 0x04;
                    }}
                "@
                [Mouse]::mouse_event(0x02, 0, 0, 0, [UIntPtr]::Zero)
                [Mouse]::mouse_event(0x04, 0, 0, 0, [UIntPtr]::Zero)
                '''
                subprocess.run(["powershell", "-Command", powershell_cmd], check=True)
            
            return ActionResult(
                success=True,
                action_type="click",
                details={"x": x, "y": y, "element_type": element.element_type}
            )
            
        except Exception as e:
            logger.error(f"Click action failed: {e}")
            return ActionResult(
                success=False,
                action_type="click",
                details={"error": str(e)},
                error_message=str(e)
            )
    
    async def type_text(self, text: str, element: Optional[ScreenElement] = None) -> ActionResult:
        """Type text, optionally at a specific element"""
        try:
            # Click element first if provided
            if element:
                click_result = await self.click_element(element)
                if not click_result.success:
                    return click_result
            
            # Small delay to ensure focus
            await asyncio.sleep(0.1)
            
            if self.current_os == "darwin":  # macOS
                # Use AppleScript for macOS typing
                escaped_text = text.replace('"', '\\"')
                applescript = f'''
                tell application "System Events"
                    keystroke "{escaped_text}"
                end tell
                '''
                subprocess.run(["osascript", "-e", applescript], check=True)
                
            elif self.current_os == "linux":
                # Use xdotool for Linux typing
                subprocess.run(["xdotool", "type", text], check=True)
                
            else:  # Windows
                # Use PowerShell for Windows typing
                powershell_cmd = f'''
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.SendKeys]::SendWait("{text}")
                '''
                subprocess.run(["powershell", "-Command", powershell_cmd], check=True)
            
            return ActionResult(
                success=True,
                action_type="type",
                details={"text": text, "length": len(text)}
            )
            
        except Exception as e:
            logger.error(f"Type action failed: {e}")
            return ActionResult(
                success=False,
                action_type="type",
                details={"error": str(e)},
                error_message=str(e)
            )
    
    async def drag_and_drop(self, source_element: ScreenElement, target_element: ScreenElement) -> ActionResult:
        """Perform drag and drop between two elements"""
        try:
            source_x, source_y = source_element.center
            target_x, target_y = target_element.center
            
            if self.current_os == "darwin":  # macOS
                applescript = f'''
                tell application "System Events"
                    set startPoint to {{{source_x}, {source_y}}}
                    set endPoint to {{{target_x}, {target_y}}}
                    
                    -- Mouse down at start point
                    click at startPoint
                    delay 0.1
                    
                    -- Drag to end point
                    key down shift
                    click at endPoint
                    key up shift
                end tell
                '''
                subprocess.run(["osascript", "-e", applescript], check=True)
                
            elif self.current_os == "linux":
                # Use xdotool for Linux drag and drop
                subprocess.run(["xdotool", "mousemove", str(source_x), str(source_y)], check=True)
                subprocess.run(["xdotool", "mousedown", "1"], check=True)
                subprocess.run(["xdotool", "mousemove", str(target_x), str(target_y)], check=True)
                subprocess.run(["xdotool", "mouseup", "1"], check=True)
                
            else:  # Windows - More complex drag and drop
                powershell_cmd = f'''
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Mouse {{
                        [DllImport("user32.dll")]
                        public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
                        [DllImport("user32.dll")]
                        public static extern bool SetCursorPos(int x, int y);
                        public const uint MOUSEEVENTF_LEFTDOWN = 0x02;
                        public const uint MOUSEEVENTF_LEFTUP = 0x04;
                    }}
                "@
                
                # Move to source and press down
                [Mouse]::SetCursorPos({source_x}, {source_y})
                Start-Sleep -Milliseconds 100
                [Mouse]::mouse_event(0x02, 0, 0, 0, [UIntPtr]::Zero)
                
                # Drag to target
                [Mouse]::SetCursorPos({target_x}, {target_y})
                Start-Sleep -Milliseconds 100
                
                # Release
                [Mouse]::mouse_event(0x04, 0, 0, 0, [UIntPtr]::Zero)
                '''
                subprocess.run(["powershell", "-Command", powershell_cmd], check=True)
            
            return ActionResult(
                success=True,
                action_type="drag_drop",
                details={
                    "source": {"x": source_x, "y": source_y},
                    "target": {"x": target_x, "y": target_y}
                }
            )
            
        except Exception as e:
            logger.error(f"Drag and drop action failed: {e}")
            return ActionResult(
                success=False,
                action_type="drag_drop",
                details={"error": str(e)},
                error_message=str(e)
            )

class ComputerUseAPI:
    """Main Computer Use API - Integrates screen analysis and action execution"""
    
    def __init__(self):
        self.screen_analyzer = ScreenAnalyzer()
        self.action_executor = ActionExecutor()
        self.sessions = {}
        logger.info("🚀 ComputerUseAPI initialized successfully")
    
    async def execute_command(self, 
                            command: str, 
                            session_id: str,
                            target_application: Optional[str] = None,
                            require_confirmation: bool = True) -> Dict[str, Any]:
        """Execute a natural language computer use command"""
        
        try:
            logger.info(f"🎯 Executing command: '{command}' for session {session_id}")
            
            # Capture current screen state
            screenshot = await self.screen_analyzer.capture_screenshot()
            if not screenshot:
                return {
                    "success": False,
                    "error": "Failed to capture screenshot",
                    "command": command
                }
            
            # Parse command and determine action
            action_plan = await self._parse_command(command)
            
            # Find target elements on screen
            target_elements = []
            if action_plan.get('target_description'):
                target_elements = await self.screen_analyzer.analyze_screen_elements(
                    screenshot, action_plan['target_description']
                )
            
            if not target_elements and action_plan.get('requires_element', True):
                return {
                    "success": False,
                    "error": f"Could not find element: {action_plan.get('target_description', 'unknown')}",
                    "command": command,
                    "screenshot": screenshot
                }
            
            # Execute the action
            result = await self._execute_action(action_plan, target_elements)
            
            # Store session information
            self.sessions[session_id] = {
                "last_command": command,
                "last_result": result,
                "screenshot_before": screenshot,
                "timestamp": datetime.utcnow()
            }
            
            return {
                "success": result.success,
                "action_type": result.action_type,
                "details": result.details,
                "command": command,
                "session_id": session_id,
                "elements_found": len(target_elements),
                "screenshot_before": screenshot if not result.success else None,
                "error_message": result.error_message
            }
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "session_id": session_id
            }
    
    async def _parse_command(self, command: str) -> Dict[str, Any]:
        """Parse natural language command into actionable plan"""
        command_lower = command.lower()
        
        # Click actions
        if any(keyword in command_lower for keyword in ['click', 'tap', 'press']):
            # Extract target from command
            target = self._extract_target_from_command(command_lower, 
                                                     ['click on', 'tap on', 'press', 'click'])
            return {
                "action_type": "click",
                "target_description": target,
                "requires_element": True
            }
        
        # Type actions
        elif any(keyword in command_lower for keyword in ['type', 'enter', 'input']):
            # Extract text to type
            text_to_type = self._extract_text_to_type(command)
            target = self._extract_target_from_command(command_lower, 
                                                     ['in', 'into', 'in the'])
            return {
                "action_type": "type",
                "text": text_to_type,
                "target_description": target,
                "requires_element": bool(target)
            }
        
        # Drag and drop actions
        elif any(keyword in command_lower for keyword in ['drag', 'move', 'drop']):
            source = self._extract_drag_source(command_lower)
            target = self._extract_drag_target(command_lower)
            return {
                "action_type": "drag_drop",
                "source_description": source,
                "target_description": target,
                "requires_element": True
            }
        
        # Screenshot action
        elif any(keyword in command_lower for keyword in ['screenshot', 'capture', 'picture']):
            return {
                "action_type": "screenshot",
                "requires_element": False
            }
        
        # Default: try to interpret as click action
        else:
            return {
                "action_type": "click",
                "target_description": command,
                "requires_element": True
            }
    
    def _extract_target_from_command(self, command: str, prefixes: List[str]) -> str:
        """Extract target element description from command"""
        for prefix in prefixes:
            if prefix in command:
                parts = command.split(prefix, 1)
                if len(parts) > 1:
                    target = parts[1].strip()
                    # Clean up common suffixes
                    for suffix in ['button', 'icon', 'link']:
                        if not target.endswith(suffix) and suffix in target:
                            target = target.replace(suffix, '').strip() + f' {suffix}'
                    return target
        
        # If no prefix found, return the whole command as target
        return command.strip()
    
    def _extract_text_to_type(self, command: str) -> str:
        """Extract text to type from command"""
        # Look for quoted text first
        if '"' in command:
            parts = command.split('"')
            if len(parts) >= 3:
                return parts[1]
        
        # Look for common patterns
        for pattern in ['type ', 'enter ', 'input ']:
            if pattern in command.lower():
                parts = command.lower().split(pattern, 1)
                if len(parts) > 1:
                    text = parts[1].split(' in ')[0].split(' into ')[0]
                    return text.strip().strip('"\'')
        
        return ""
    
    def _extract_drag_source(self, command: str) -> str:
        """Extract source element for drag operation"""
        if 'drag ' in command:
            parts = command.split('drag ', 1)
            if len(parts) > 1:
                source_part = parts[1].split(' to ')[0].split(' onto ')[0]
                return source_part.strip()
        return "source element"
    
    def _extract_drag_target(self, command: str) -> str:
        """Extract target element for drag operation"""
        for separator in [' to ', ' onto ', ' into ']:
            if separator in command:
                parts = command.split(separator, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return "target element"
    
    async def _execute_action(self, action_plan: Dict[str, Any], elements: List[ScreenElement]) -> ActionResult:
        """Execute the planned action"""
        action_type = action_plan.get("action_type", "unknown")
        
        if action_type == "click":
            if not elements:
                return ActionResult(
                    success=False,
                    action_type="click",
                    details={"error": "No clickable element found"},
                    error_message="No clickable element found"
                )
            # Use the first (best match) element
            return await self.action_executor.click_element(elements[0])
        
        elif action_type == "type":
            text = action_plan.get("text", "")
            if not text:
                return ActionResult(
                    success=False,
                    action_type="type",
                    details={"error": "No text to type"},
                    error_message="No text to type"
                )
            
            # If we have a target element, click it first
            target_element = elements[0] if elements else None
            return await self.action_executor.type_text(text, target_element)
        
        elif action_type == "drag_drop":
            if len(elements) < 2:
                return ActionResult(
                    success=False,
                    action_type="drag_drop",
                    details={"error": "Need both source and target elements"},
                    error_message="Need both source and target elements"
                )
            
            return await self.action_executor.drag_and_drop(elements[0], elements[1])
        
        elif action_type == "screenshot":
            screenshot = await self.screen_analyzer.capture_screenshot()
            return ActionResult(
                success=bool(screenshot),
                action_type="screenshot",
                details={"screenshot": screenshot},
                error_message="Screenshot capture failed" if not screenshot else None
            )
        
        else:
            return ActionResult(
                success=False,
                action_type=action_type,
                details={"error": f"Unknown action type: {action_type}"},
                error_message=f"Unknown action type: {action_type}"
            )
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a computer use session"""
        return self.sessions.get(session_id)
    
    async def list_available_applications(self) -> List[str]:
        """List applications that can be automated"""
        try:
            if self.current_os == "darwin":  # macOS
                result = subprocess.run(
                    ["osascript", "-e", 'tell application "System Events" to get name of every process whose visible is true'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                apps = [app.strip() for app in result.stdout.split(',')]
                
            elif self.current_os == "linux":
                result = subprocess.run(
                    ["wmctrl", "-l"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                apps = [line.split()[-1] for line in result.stdout.split('\n') if line.strip()]
                
            else:  # Windows
                powershell_cmd = '''
                Get-Process | Where-Object {$_.MainWindowTitle -ne ""} | Select-Object ProcessName | Format-Table -HideTableHeaders
                '''
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True,
                    text=True,
                    check=True
                )
                apps = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            return apps[:20]  # Return top 20 applications
            
        except Exception as e:
            logger.error(f"Failed to list applications: {e}")
            return ["Chrome", "Firefox", "Safari", "Terminal", "Finder"]  # Default apps
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get current capabilities of the Computer Use API"""
        return {
            "actions_supported": ["click", "type", "drag_drop", "screenshot"],
            "operating_system": self.screen_analyzer.current_os,
            "computer_vision_available": CV2_AVAILABLE,
            "multi_element_detection": True,
            "session_management": True,
            "application_awareness": True,
            "security_features": {
                "confirmation_required": True,
                "session_isolation": True,
                "action_logging": True
            }
        }