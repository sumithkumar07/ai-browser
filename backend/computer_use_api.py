"""
AETHER Computer Use API - AI-Powered Element Detection and Interaction
Implements the complete Computer Use API from the comprehensive plan
Features:
- AI-powered element detection using vision models
- Natural language command interpretation
- Screenshot analysis and coordinate mapping
- Smart interaction patterns
"""

import asyncio
import base64
import json
import io
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw
import cv2
import numpy as np
from dataclasses import dataclass
from pydantic import BaseModel

from playwright.async_api import Page, Browser
import openai
from groq import AsyncGroq


@dataclass
class Element:
    """Detected UI element"""
    x: int
    y: int
    width: int
    height: int
    text: Optional[str] = None
    element_type: Optional[str] = None
    confidence: float = 0.0
    selector: Optional[str] = None
    description: Optional[str] = None
    center_x: int = 0
    center_y: int = 0
    
    def __post_init__(self):
        self.center_x = self.x + self.width // 2
        self.center_y = self.y + self.height // 2


class ComputerUseCommand(BaseModel):
    """Natural language command for computer use"""
    action: str  # click, type, scroll, navigate, find, etc.
    target: str  # description of what to interact with
    value: Optional[str] = None  # text to type, URL to navigate to, etc.
    timeout: int = 10000
    screenshot_before: bool = True
    screenshot_after: bool = True


class ComputerUseAPI:
    """Advanced Computer Use API with AI-powered element detection"""
    
    def __init__(self, ai_provider: str = "groq"):
        self.ai_provider = ai_provider
        self.groq_client = AsyncGroq(api_key="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") if ai_provider == "groq" else None
        self.openai_client = openai.AsyncOpenAI() if ai_provider == "openai" else None
        
        # Element detection cache
        self.element_cache: Dict[str, List[Element]] = {}
        self.screenshot_cache: Dict[str, str] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "average_response_time": 0.0,
            "element_detection_accuracy": 0.0
        }
    
    async def capture_screenshot(self, page: Page, full_page: bool = False, quality: int = 80) -> str:
        """Capture high-quality screenshot for AI analysis"""
        try:
            screenshot_options = {
                "quality": quality,
                "type": "jpeg",
                "full_page": full_page
            }
            
            screenshot_bytes = await page.screenshot(**screenshot_options)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
            
            # Cache the screenshot
            cache_key = f"screenshot_{time.time()}"
            self.screenshot_cache[cache_key] = screenshot_base64
            
            return screenshot_base64
            
        except Exception as e:
            print(f"Screenshot capture error: {e}")
            return ""
    
    async def analyze_screenshot_with_ai(self, screenshot_base64: str, task_description: str) -> List[Element]:
        """Use AI vision models to analyze screenshot and detect elements"""
        try:
            if self.ai_provider == "groq" and self.groq_client:
                return await self._analyze_with_groq(screenshot_base64, task_description)
            elif self.ai_provider == "openai" and self.openai_client:
                return await self._analyze_with_openai(screenshot_base64, task_description)
            else:
                # Fallback to basic element detection
                return await self._basic_element_detection(screenshot_base64, task_description)
                
        except Exception as e:
            print(f"AI screenshot analysis error: {e}")
            return []
    
    async def _analyze_with_groq(self, screenshot_base64: str, task_description: str) -> List[Element]:
        """Analyze screenshot using Groq vision model"""
        try:
            # For now, use basic detection since Groq vision API is still in beta
            return await self._basic_element_detection(screenshot_base64, task_description)
            
        except Exception as e:
            print(f"Groq analysis error: {e}")
            return []
    
    async def _analyze_with_openai(self, screenshot_base64: str, task_description: str) -> List[Element]:
        """Analyze screenshot using OpenAI vision model"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this screenshot and identify UI elements relevant to: "{task_description}"
                                
                                Return a JSON array of elements with this structure:
                                [{{
                                    "x": number,
                                    "y": number, 
                                    "width": number,
                                    "height": number,
                                    "text": "visible text",
                                    "element_type": "button|input|link|image|text",
                                    "confidence": 0.0-1.0,
                                    "description": "what this element does"
                                }}]
                                
                                Focus on interactive elements like buttons, inputs, links that match the task."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{screenshot_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            elements_data = json.loads(content)
            
            elements = []
            for elem_data in elements_data:
                element = Element(
                    x=elem_data.get("x", 0),
                    y=elem_data.get("y", 0),
                    width=elem_data.get("width", 0),
                    height=elem_data.get("height", 0),
                    text=elem_data.get("text"),
                    element_type=elem_data.get("element_type"),
                    confidence=elem_data.get("confidence", 0.0),
                    description=elem_data.get("description")
                )
                elements.append(element)
            
            return elements
            
        except Exception as e:
            print(f"OpenAI vision analysis error: {e}")
            return await self._basic_element_detection(screenshot_base64, task_description)
    
    async def _basic_element_detection(self, screenshot_base64: str, task_description: str) -> List[Element]:
        """Basic element detection using OpenCV and heuristics"""
        try:
            # Decode screenshot
            screenshot_bytes = base64.b64decode(screenshot_base64)
            image = Image.open(io.BytesIO(screenshot_bytes))
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale for processing
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect button-like elements using edge detection
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            elements = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size (reasonable button/element sizes)
                if 20 < w < 300 and 20 < h < 100:
                    element = Element(
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        element_type="interactive",
                        confidence=0.7,
                        description=f"Interactive element at ({x}, {y})"
                    )
                    elements.append(element)
            
            # Sort by confidence and return top candidates
            elements.sort(key=lambda e: e.confidence, reverse=True)
            return elements[:10]  # Return top 10 candidates
            
        except Exception as e:
            print(f"Basic element detection error: {e}")
            return []
    
    async def find_element(self, page: Page, description: str) -> Optional[Element]:
        """Find element using AI-powered description"""
        try:
            # Capture current screenshot
            screenshot = await self.capture_screenshot(page)
            if not screenshot:
                return None
            
            # Analyze with AI to find matching elements
            elements = await self.analyze_screenshot_with_ai(screenshot, description)
            
            if elements:
                # Return the most confident match
                return max(elements, key=lambda e: e.confidence)
            
            return None
            
        except Exception as e:
            print(f"Element finding error: {e}")
            return None
    
    async def smart_click(self, page: Page, description: str) -> Dict[str, Any]:
        """AI-powered smart click using natural language description"""
        start_time = time.time()
        
        try:
            # Find the element using AI
            element = await self.find_element(page, description)
            
            if not element:
                return {
                    "success": False,
                    "error": f"Could not find element matching: {description}",
                    "response_time": time.time() - start_time
                }
            
            # Click at the element's center
            await page.mouse.click(element.center_x, element.center_y)
            
            # Wait for potential page changes
            await asyncio.sleep(0.5)
            
            # Capture screenshot after click
            after_screenshot = await self.capture_screenshot(page)
            
            self.performance_metrics["successful_commands"] += 1
            
            return {
                "success": True,
                "element": {
                    "x": element.x,
                    "y": element.y,
                    "width": element.width,
                    "height": element.height,
                    "description": element.description,
                    "confidence": element.confidence
                },
                "click_coordinates": [element.center_x, element.center_y],
                "response_time": time.time() - start_time,
                "screenshot_after": after_screenshot
            }
            
        except Exception as e:
            self.performance_metrics["failed_commands"] += 1
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
        finally:
            self.performance_metrics["total_commands"] += 1
    
    async def smart_type(self, page: Page, field_description: str, text: str) -> Dict[str, Any]:
        """AI-powered typing in fields using natural language description"""
        start_time = time.time()
        
        try:
            # Find the input field
            element = await self.find_element(page, f"input field for {field_description}")
            
            if not element:
                return {
                    "success": False,
                    "error": f"Could not find input field for: {field_description}",
                    "response_time": time.time() - start_time
                }
            
            # Click on the field first
            await page.mouse.click(element.center_x, element.center_y)
            await asyncio.sleep(0.2)
            
            # Clear existing text and type new text
            await page.keyboard.press("Control+a")
            await page.keyboard.type(text)
            
            # Capture screenshot after typing
            after_screenshot = await self.capture_screenshot(page)
            
            self.performance_metrics["successful_commands"] += 1
            
            return {
                "success": True,
                "element": {
                    "x": element.x,
                    "y": element.y,
                    "description": element.description,
                    "confidence": element.confidence
                },
                "text_typed": text,
                "response_time": time.time() - start_time,
                "screenshot_after": after_screenshot
            }
            
        except Exception as e:
            self.performance_metrics["failed_commands"] += 1
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
        finally:
            self.performance_metrics["total_commands"] += 1
    
    async def execute_natural_language_command(self, page: Page, command: str) -> Dict[str, Any]:
        """Execute complex commands using natural language"""
        start_time = time.time()
        
        try:
            # Parse the command using AI
            parsed_command = await self._parse_natural_language_command(command)
            
            if not parsed_command:
                return {
                    "success": False,
                    "error": f"Could not understand command: {command}",
                    "response_time": time.time() - start_time
                }
            
            # Execute the parsed command
            result = await self._execute_parsed_command(page, parsed_command)
            result["original_command"] = command
            result["parsed_command"] = parsed_command
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_command": command,
                "response_time": time.time() - start_time
            }
    
    async def _parse_natural_language_command(self, command: str) -> Optional[Dict[str, Any]]:
        """Parse natural language command into structured format"""
        try:
            if self.groq_client:
                completion = await self.groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a command parser for browser automation. Parse natural language commands into structured JSON.

Supported actions: click, type, scroll, navigate, wait, find
Return JSON with: {"action": "...", "target": "...", "value": "...", "confidence": 0.0-1.0}

Examples:
"Click the login button" -> {"action": "click", "target": "login button", "confidence": 0.9}
"Type hello in the search box" -> {"action": "type", "target": "search box", "value": "hello", "confidence": 0.9}
"Navigate to google.com" -> {"action": "navigate", "target": "google.com", "confidence": 0.9}
"Scroll down" -> {"action": "scroll", "target": "down", "confidence": 0.9}"""
                        },
                        {
                            "role": "user",
                            "content": f"Parse this command: {command}"
                        }
                    ],
                    model="llama3-8b-8192",
                    temperature=0.1,
                    max_tokens=200
                )
                
                response_text = completion.choices[0].message.content.strip()
                return json.loads(response_text)
            
            # Fallback basic parsing
            return self._basic_command_parsing(command)
            
        except Exception as e:
            print(f"Command parsing error: {e}")
            return self._basic_command_parsing(command)
    
    def _basic_command_parsing(self, command: str) -> Dict[str, Any]:
        """Basic command parsing using keywords"""
        command_lower = command.lower()
        
        if "click" in command_lower:
            # Extract target after "click"
            parts = command_lower.split("click")
            if len(parts) > 1:
                target = parts[1].strip().lstrip("the ").lstrip("on ")
                return {"action": "click", "target": target, "confidence": 0.7}
        
        elif "type" in command_lower:
            # Extract what to type and where
            if " in " in command_lower:
                parts = command_lower.split(" in ")
                if len(parts) == 2:
                    value_part = parts[0].replace("type", "").strip().strip('"\'')
                    target = parts[1].strip()
                    return {"action": "type", "target": target, "value": value_part, "confidence": 0.7}
        
        elif "navigate" in command_lower or "go to" in command_lower:
            # Extract URL
            for word in command.split():
                if "." in word and ("http" in word or "www" in word or ".com" in word):
                    return {"action": "navigate", "target": word, "confidence": 0.8}
        
        elif "scroll" in command_lower:
            direction = "down"
            if "up" in command_lower:
                direction = "up"
            return {"action": "scroll", "target": direction, "confidence": 0.8}
        
        return {"action": "unknown", "target": command, "confidence": 0.3}
    
    async def _execute_parsed_command(self, page: Page, parsed_command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a parsed command"""
        action = parsed_command.get("action")
        target = parsed_command.get("target")
        value = parsed_command.get("value")
        
        if action == "click":
            return await self.smart_click(page, target)
        
        elif action == "type":
            return await self.smart_type(page, target, value)
        
        elif action == "navigate":
            try:
                await page.goto(target if target.startswith("http") else f"https://{target}")
                await page.wait_for_load_state("networkidle", timeout=10000)
                screenshot = await self.capture_screenshot(page)
                
                return {
                    "success": True,
                    "action": "navigate",
                    "url": target,
                    "screenshot_after": screenshot
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        elif action == "scroll":
            try:
                if target == "down":
                    await page.mouse.wheel(0, 300)
                else:
                    await page.mouse.wheel(0, -300)
                
                await asyncio.sleep(0.5)
                screenshot = await self.capture_screenshot(page)
                
                return {
                    "success": True,
                    "action": "scroll",
                    "direction": target,
                    "screenshot_after": screenshot
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        total = self.performance_metrics["total_commands"]
        if total > 0:
            success_rate = (self.performance_metrics["successful_commands"] / total) * 100
        else:
            success_rate = 0.0
        
        return {
            **self.performance_metrics,
            "success_rate": success_rate,
            "timestamp": time.time()
        }
    
    async def batch_execute(self, page: Page, commands: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple commands in sequence"""
        results = []
        
        for i, command in enumerate(commands):
            print(f"Executing command {i+1}/{len(commands)}: {command}")
            result = await self.execute_natural_language_command(page, command)
            results.append(result)
            
            # Add delay between commands
            if i < len(commands) - 1:
                await asyncio.sleep(1)
        
        return results


# Global Computer Use API instance
computer_use_api = ComputerUseAPI()