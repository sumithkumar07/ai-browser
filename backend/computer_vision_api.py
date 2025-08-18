# Phase 1: Computer Vision API Integration
import asyncio
import json
import logging
import base64
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class ComputerVisionAPI:
    """
    Phase 1: Advanced Computer Vision API integration
    Provides visual webpage understanding and screenshot analysis
    """
    
    def __init__(self):
        self.api_providers = {
            "openai": {
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "headers": {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', '')}"}
            },
            "anthropic": {
                "endpoint": "https://api.anthropic.com/v1/messages",
                "headers": {"x-api-key": os.getenv('ANTHROPIC_API_KEY', '')}
            },
            "google": {
                "endpoint": "https://generativelanguage.googleapis.com/v1/models/gemini-pro-vision:generateContent",
                "headers": {"Authorization": f"Bearer {os.getenv('GOOGLE_API_KEY', '')}"}
            }
        }
        
    async def analyze_webpage_screenshot(self, screenshot_data: bytes, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze webpage screenshot using computer vision"""
        try:
            # Convert screenshot to base64
            screenshot_b64 = base64.b64encode(screenshot_data).decode('utf-8')
            
            # Choose analysis prompt based on type
            prompts = {
                "comprehensive": "Analyze this webpage screenshot comprehensively. Describe the layout, key elements, navigation structure, content areas, and any interactive elements you can identify.",
                "ui_elements": "Identify and list all UI elements in this webpage screenshot: buttons, forms, links, navigation menus, input fields, etc.",
                "content_structure": "Analyze the content structure of this webpage: headers, paragraphs, lists, images, and how the information is organized.",
                "accessibility": "Evaluate this webpage for accessibility: identify potential issues with contrast, text size, navigation, and suggest improvements.",
                "automation_targets": "Identify elements in this webpage that could be automated: forms to fill, buttons to click, data to extract, etc."
            }
            
            prompt = prompts.get(analysis_type, prompts["comprehensive"])
            
            # Try multiple providers for redundancy
            for provider in ["openai", "anthropic"]:
                try:
                    result = await self._analyze_with_provider(provider, screenshot_b64, prompt)
                    if result["success"]:
                        return result
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue
            
            # Fallback result
            return {
                "success": False,
                "error": "All vision providers failed",
                "analysis": "Unable to analyze screenshot",
                "provider": "fallback"
            }
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": "Analysis failed",
                "provider": "error"
            }
    
    async def _analyze_with_provider(self, provider: str, screenshot_b64: str, prompt: str) -> Dict[str, Any]:
        """Analyze screenshot with specific provider"""
        
        if provider == "openai":
            return await self._analyze_with_openai(screenshot_b64, prompt)
        elif provider == "anthropic":
            return await self._analyze_with_anthropic(screenshot_b64, prompt)
        elif provider == "google":
            return await self._analyze_with_google(screenshot_b64, prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _analyze_with_openai(self, screenshot_b64: str, prompt: str) -> Dict[str, Any]:
        """Analyze with OpenAI Vision API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": "gpt-4-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{screenshot_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
                
                response = await client.post(
                    self.api_providers["openai"]["endpoint"],
                    json=payload,
                    headers=self.api_providers["openai"]["headers"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result["choices"][0]["message"]["content"]
                    
                    return {
                        "success": True,
                        "analysis": analysis,
                        "provider": "openai",
                        "model": "gpt-4-vision-preview",
                        "confidence": 0.9,
                        "elements_detected": self._extract_ui_elements(analysis)
                    }
                else:
                    raise Exception(f"OpenAI API error: {response.status_code}")
                    
        except Exception as e:
            raise Exception(f"OpenAI vision analysis failed: {e}")
    
    async def _analyze_with_anthropic(self, screenshot_b64: str, prompt: str) -> Dict[str, Any]:
        """Analyze with Anthropic Vision API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": screenshot_b64
                                    }
                                }
                            ]
                        }
                    ]
                }
                
                response = await client.post(
                    self.api_providers["anthropic"]["endpoint"],
                    json=payload,
                    headers=self.api_providers["anthropic"]["headers"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result["content"][0]["text"]
                    
                    return {
                        "success": True,
                        "analysis": analysis,
                        "provider": "anthropic",
                        "model": "claude-3-sonnet",
                        "confidence": 0.9,
                        "elements_detected": self._extract_ui_elements(analysis)
                    }
                else:
                    raise Exception(f"Anthropic API error: {response.status_code}")
                    
        except Exception as e:
            raise Exception(f"Anthropic vision analysis failed: {e}")
    
    async def _analyze_with_google(self, screenshot_b64: str, prompt: str) -> Dict[str, Any]:
        """Analyze with Google Vision API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": "image/jpeg",
                                        "data": screenshot_b64
                                    }
                                }
                            ]
                        }
                    ]
                }
                
                response = await client.post(
                    f"{self.api_providers['google']['endpoint']}?key={os.getenv('GOOGLE_API_KEY', '')}",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    return {
                        "success": True,
                        "analysis": analysis,
                        "provider": "google",
                        "model": "gemini-pro-vision",
                        "confidence": 0.8,
                        "elements_detected": self._extract_ui_elements(analysis)
                    }
                else:
                    raise Exception(f"Google API error: {response.status_code}")
                    
        except Exception as e:
            raise Exception(f"Google vision analysis failed: {e}")
    
    def _extract_ui_elements(self, analysis_text: str) -> List[Dict[str, Any]]:
        """Extract UI elements from analysis text"""
        elements = []
        
        # Common UI element keywords
        element_keywords = {
            "button": ["button", "btn", "click", "submit"],
            "input": ["input", "field", "textbox", "search box"],
            "link": ["link", "href", "anchor", "navigation"],
            "image": ["image", "img", "picture", "photo"],
            "form": ["form", "login", "signup", "contact"],
            "menu": ["menu", "navigation", "nav", "dropdown"],
            "header": ["header", "title", "heading", "h1", "h2"],
            "content": ["paragraph", "text", "content", "article"]
        }
        
        analysis_lower = analysis_text.lower()
        
        for element_type, keywords in element_keywords.items():
            for keyword in keywords:
                if keyword in analysis_lower:
                    elements.append({
                        "type": element_type,
                        "keyword": keyword,
                        "confidence": 0.7,
                        "detected_at": datetime.utcnow().isoformat()
                    })
                    break  # Avoid duplicates for same type
        
        return elements
    
    async def identify_automation_opportunities(self, screenshot_data: bytes, current_url: str = "") -> Dict[str, Any]:
        """Identify automation opportunities in webpage"""
        try:
            analysis_result = await self.analyze_webpage_screenshot(
                screenshot_data, 
                "automation_targets"
            )
            
            if not analysis_result["success"]:
                return analysis_result
            
            # Extract automation suggestions from analysis
            automation_opportunities = self._parse_automation_opportunities(
                analysis_result["analysis"], 
                current_url
            )
            
            return {
                "success": True,
                "url": current_url,
                "opportunities": automation_opportunities,
                "analysis": analysis_result["analysis"],
                "provider": analysis_result["provider"],
                "confidence": analysis_result.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Automation opportunity identification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "opportunities": []
            }
    
    def _parse_automation_opportunities(self, analysis: str, url: str) -> List[Dict[str, Any]]:
        """Parse automation opportunities from analysis text"""
        opportunities = []
        
        # Common automation patterns
        patterns = {
            "form_filling": {
                "triggers": ["form", "input", "signup", "login", "contact"],
                "description": "Automated form filling with user data",
                "complexity": "medium",
                "estimated_time": "2-5 minutes"
            },
            "data_extraction": {
                "triggers": ["table", "list", "data", "information", "content"],
                "description": "Extract structured data from page",
                "complexity": "low",
                "estimated_time": "1-3 minutes"
            },
            "navigation": {
                "triggers": ["menu", "navigation", "links", "pages"],
                "description": "Automated navigation through site sections",
                "complexity": "low",
                "estimated_time": "1-2 minutes"
            },
            "social_interaction": {
                "triggers": ["social", "share", "like", "comment", "follow"],
                "description": "Social media interactions and sharing",
                "complexity": "medium",
                "estimated_time": "2-4 minutes"
            },
            "ecommerce": {
                "triggers": ["cart", "buy", "purchase", "checkout", "product"],
                "description": "E-commerce actions like adding to cart",
                "complexity": "high",
                "estimated_time": "5-10 minutes"
            }
        }
        
        analysis_lower = analysis.lower()
        
        for pattern_type, config in patterns.items():
            for trigger in config["triggers"]:
                if trigger in analysis_lower:
                    opportunity = {
                        "id": f"auto_{pattern_type}_{len(opportunities)}",
                        "type": pattern_type,
                        "title": f"Automate {pattern_type.replace('_', ' ').title()}",
                        "description": config["description"],
                        "complexity": config["complexity"],
                        "estimated_time": config["estimated_time"],
                        "url": url,
                        "confidence": 0.8,
                        "trigger_keyword": trigger,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    opportunities.append(opportunity)
                    break  # Avoid duplicates
        
        return opportunities[:5]  # Limit to top 5 opportunities
    
    async def extract_page_elements(self, screenshot_data: bytes) -> Dict[str, Any]:
        """Extract structured information about page elements"""
        try:
            analysis_result = await self.analyze_webpage_screenshot(
                screenshot_data, 
                "ui_elements"
            )
            
            if not analysis_result["success"]:
                return analysis_result
            
            # Structure the element information
            structured_elements = self._structure_elements(analysis_result["analysis"])
            
            return {
                "success": True,
                "elements": structured_elements,
                "raw_analysis": analysis_result["analysis"],
                "provider": analysis_result["provider"],
                "total_elements": len(structured_elements)
            }
            
        except Exception as e:
            logger.error(f"Page element extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "elements": []
            }
    
    def _structure_elements(self, analysis: str) -> List[Dict[str, Any]]:
        """Structure element information from analysis"""
        elements = []
        
        # Parse analysis for structured elements
        lines = analysis.split('\n')
        current_element = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect element mentions
            for element_type in ["button", "input", "link", "image", "form", "menu", "header"]:
                if element_type in line.lower():
                    element = {
                        "type": element_type,
                        "description": line,
                        "confidence": 0.8,
                        "line": line,
                        "automatable": element_type in ["button", "input", "form", "link"],
                        "identified_at": datetime.utcnow().isoformat()
                    }
                    elements.append(element)
                    break
        
        return elements
    
    async def generate_automation_script(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate automation script from identified opportunities"""
        try:
            if not opportunities:
                return {
                    "success": False,
                    "error": "No opportunities provided",
                    "script": ""
                }
            
            # Generate script based on opportunities
            script_parts = []
            script_parts.append("# Auto-generated automation script")
            script_parts.append(f"# Generated at: {datetime.utcnow().isoformat()}")
            script_parts.append("")
            
            for i, opp in enumerate(opportunities):
                script_parts.append(f"# Step {i+1}: {opp['title']}")
                script_parts.append(f"# {opp['description']}")
                script_parts.append(f"# Estimated time: {opp['estimated_time']}")
                
                if opp["type"] == "form_filling":
                    script_parts.append("await fill_form_fields(page, user_data)")
                elif opp["type"] == "data_extraction":
                    script_parts.append("data = await extract_page_data(page)")
                elif opp["type"] == "navigation":
                    script_parts.append("await navigate_site_sections(page)")
                elif opp["type"] == "social_interaction":
                    script_parts.append("await perform_social_actions(page)")
                elif opp["type"] == "ecommerce":
                    script_parts.append("await handle_ecommerce_actions(page)")
                
                script_parts.append("")
            
            script = "\n".join(script_parts)
            
            return {
                "success": True,
                "script": script,
                "opportunities_count": len(opportunities),
                "estimated_total_time": self._calculate_total_time(opportunities)
            }
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": ""
            }
    
    def _calculate_total_time(self, opportunities: List[Dict[str, Any]]) -> str:
        """Calculate total estimated time for all opportunities"""
        total_minutes = 0
        
        for opp in opportunities:
            time_str = opp.get("estimated_time", "1-2 minutes")
            # Extract average time in minutes
            if "minute" in time_str:
                numbers = [int(x) for x in time_str.split() if x.isdigit()]
                if numbers:
                    if len(numbers) == 2:
                        total_minutes += (numbers[0] + numbers[1]) / 2
                    else:
                        total_minutes += numbers[0]
        
        return f"{int(total_minutes)}-{int(total_minutes * 1.2)} minutes"

# Global instance
computer_vision_api = ComputerVisionAPI()