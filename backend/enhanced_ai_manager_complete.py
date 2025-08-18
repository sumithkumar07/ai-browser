import asyncio
import json
import logging
import time
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import httpx
import os
from PIL import Image
import io
import hashlib
from collections import defaultdict
import random

logger = logging.getLogger(__name__)

class QueryType(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    CODE = "code"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    SUMMARIZATION = "summarization"
    WORKFLOW_PARSING = "workflow_parsing"
    VISUAL_ANALYSIS = "visual_analysis"
    MULTI_STEP_REASONING = "multi_step_reasoning"

class AIProvider(Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    FALLBACK = "fallback"

class EnhancedAIManager:
    """Advanced AI management system with computer vision and multi-step reasoning"""
    
    def __init__(self):
        # API configurations
        self.api_keys = {
            AIProvider.GROQ: os.getenv("GROQ_API_KEY"),
            AIProvider.OPENAI: os.getenv("OPENAI_API_KEY"),
            AIProvider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY"),
            AIProvider.GOOGLE: os.getenv("GOOGLE_API_KEY")
        }
        
        # Provider capabilities and preferences
        self.provider_capabilities = {
            AIProvider.GROQ: {
                "text_generation": True,
                "code_generation": True,
                "analysis": True,
                "speed": "very_fast",
                "cost": "low",
                "max_tokens": 8000,
                "models": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
            },
            AIProvider.OPENAI: {
                "text_generation": True,
                "code_generation": True,
                "analysis": True,
                "vision": True,
                "multi_modal": True,
                "speed": "fast",
                "cost": "medium",
                "max_tokens": 4000,
                "models": ["gpt-4", "gpt-4-vision-preview", "gpt-3.5-turbo"]
            },
            AIProvider.ANTHROPIC: {
                "text_generation": True,
                "code_generation": True,
                "analysis": True,
                "reasoning": True,
                "speed": "medium",
                "cost": "medium",
                "max_tokens": 8000,
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
            },
            AIProvider.GOOGLE: {
                "text_generation": True,
                "code_generation": True,
                "analysis": True,
                "vision": True,
                "multi_modal": True,
                "speed": "fast",
                "cost": "low",
                "max_tokens": 8000,
                "models": ["gemini-pro", "gemini-pro-vision"]
            }
        }
        
        # Smart routing configuration
        self.routing_rules = {
            QueryType.VISUAL_ANALYSIS: [AIProvider.OPENAI, AIProvider.GOOGLE],
            QueryType.CODE: [AIProvider.GROQ, AIProvider.OPENAI, AIProvider.ANTHROPIC],
            QueryType.TECHNICAL: [AIProvider.ANTHROPIC, AIProvider.GROQ, AIProvider.OPENAI],
            QueryType.CREATIVE: [AIProvider.OPENAI, AIProvider.ANTHROPIC, AIProvider.GOOGLE],
            QueryType.ANALYSIS: [AIProvider.ANTHROPIC, AIProvider.OPENAI, AIProvider.GROQ],
            QueryType.WORKFLOW_PARSING: [AIProvider.ANTHROPIC, AIProvider.GROQ],
            QueryType.MULTI_STEP_REASONING: [AIProvider.ANTHROPIC, AIProvider.OPENAI],
            QueryType.GENERAL: [AIProvider.GROQ, AIProvider.OPENAI, AIProvider.GOOGLE]
        }
        
        # Performance tracking
        self.provider_performance = defaultdict(lambda: {
            "response_times": [],
            "success_rate": 1.0,
            "last_used": datetime.utcnow(),
            "failures": 0
        })
        
        # Caching system
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Learning system
        self.learning_data = {
            "query_patterns": defaultdict(int),
            "successful_routings": defaultdict(int),
            "user_preferences": defaultdict(dict)
        }
        
        # Background learning task
        self._learning_task = None
        
    def start_learning_engine(self):
        """Start background learning engine"""
        if self._learning_task is None:
            try:
                self._learning_task = asyncio.create_task(self._background_learning_loop())
            except RuntimeError:
                pass
    
    async def _background_learning_loop(self):
        """Background learning and optimization"""
        while True:
            try:
                await asyncio.sleep(600)  # Run every 10 minutes
                await self._optimize_provider_rankings()
                await self._clean_cache()
                await self._update_learning_patterns()
                
            except Exception as e:
                logger.error(f"AI learning engine error: {e}")
    
    def _classify_query_type(self, message: str, context: Optional[str] = None) -> QueryType:
        """Classify query type using enhanced heuristics"""
        message_lower = message.lower()
        
        # Computer vision keywords
        vision_keywords = ["image", "picture", "screenshot", "visual", "analyze photo", "what do you see", 
                          "describe image", "extract text from", "ocr", "diagram", "chart"]
        if any(keyword in message_lower for keyword in vision_keywords):
            return QueryType.VISUAL_ANALYSIS
        
        # Multi-step reasoning keywords
        reasoning_keywords = ["step by step", "break down", "analyze", "compare", "evaluate", 
                             "pros and cons", "reasoning", "logic", "deduce", "infer"]
        if any(keyword in message_lower for keyword in reasoning_keywords):
            return QueryType.MULTI_STEP_REASONING
        
        # Workflow parsing keywords
        workflow_keywords = ["automate", "workflow", "create task", "sequence", "steps to", 
                           "process", "procedure", "how to do"]
        if any(keyword in message_lower for keyword in workflow_keywords):
            return QueryType.WORKFLOW_PARSING
        
        # Code-related keywords
        code_keywords = ["code", "function", "programming", "script", "debug", "algorithm", 
                        "syntax", "variable", "class", "import", "def ", "return ", "if ", "for "]
        if any(keyword in message_lower for keyword in code_keywords):
            return QueryType.CODE
        
        # Technical keywords
        tech_keywords = ["api", "database", "server", "configuration", "technical", "architecture", 
                        "implementation", "optimization", "performance", "integration"]
        if any(keyword in message_lower for keyword in tech_keywords):
            return QueryType.TECHNICAL
        
        # Analysis keywords
        analysis_keywords = ["analyze", "examine", "evaluate", "assess", "review", "study", 
                           "investigate", "research", "findings", "insights"]
        if any(keyword in message_lower for keyword in analysis_keywords):
            return QueryType.ANALYSIS
        
        # Summarization keywords
        summary_keywords = ["summarize", "summary", "brief", "overview", "key points", 
                          "main ideas", "tldr", "conclude", "wrap up"]
        if any(keyword in message_lower for keyword in summary_keywords):
            return QueryType.SUMMARIZATION
        
        # Creative keywords
        creative_keywords = ["creative", "story", "write", "poem", "brainstorm", "ideas", 
                           "imagine", "design", "art", "creative writing"]
        if any(keyword in message_lower for keyword in creative_keywords):
            return QueryType.CREATIVE
        
        return QueryType.GENERAL
    
    def _select_optimal_provider(self, query_type: QueryType, message_length: int = 0, 
                                has_context: bool = False) -> Tuple[AIProvider, str]:
        """Select optimal AI provider using smart routing"""
        
        # Get preferred providers for query type
        preferred_providers = self.routing_rules.get(query_type, [AIProvider.GROQ])
        
        # Filter available providers (with API keys)
        available_providers = [p for p in preferred_providers if self.api_keys.get(p)]
        
        if not available_providers:
            available_providers = [AIProvider.GROQ]  # Fallback to Groq
        
        # Score providers based on performance and suitability
        provider_scores = {}
        
        for provider in available_providers:
            score = 100  # Base score
            
            # Performance scoring
            perf_data = self.provider_performance[provider]
            if perf_data["response_times"]:
                avg_response_time = sum(perf_data["response_times"][-10:]) / len(perf_data["response_times"][-10:])
                score += max(0, 50 - avg_response_time * 10)  # Penalty for slow responses
            
            score *= perf_data["success_rate"]  # Factor in success rate
            
            # Capability scoring
            capabilities = self.provider_capabilities.get(provider, {})
            
            if query_type == QueryType.VISUAL_ANALYSIS and capabilities.get("vision"):
                score += 50
            elif query_type == QueryType.CODE and capabilities.get("code_generation"):
                score += 30
            elif query_type == QueryType.MULTI_STEP_REASONING and capabilities.get("reasoning"):
                score += 40
            
            # Message length considerations
            max_tokens = capabilities.get("max_tokens", 4000)
            if message_length > max_tokens * 0.8:
                score -= 30  # Penalty for long messages
            
            # Context considerations
            if has_context and capabilities.get("max_tokens", 4000) > 6000:
                score += 20
            
            # Speed preference (for real-time interactions)
            if capabilities.get("speed") == "very_fast":
                score += 15
            elif capabilities.get("speed") == "fast":
                score += 10
            
            # Recent failures penalty
            if perf_data["failures"] > 2:
                score -= perf_data["failures"] * 10
            
            provider_scores[provider] = score
        
        # Select best provider
        best_provider = max(provider_scores, key=provider_scores.get)
        
        # Select appropriate model
        model = self._select_model(best_provider, query_type)
        
        logger.info(f"Selected provider: {best_provider.value} with model: {model} for query type: {query_type.value}")
        
        return best_provider, model
    
    def _select_model(self, provider: AIProvider, query_type: QueryType) -> str:
        """Select appropriate model for provider and query type"""
        
        capabilities = self.provider_capabilities.get(provider, {})
        models = capabilities.get("models", [])
        
        if not models:
            return "default"
        
        # Model selection logic
        if provider == AIProvider.GROQ:
            if query_type in [QueryType.CODE, QueryType.TECHNICAL]:
                return "llama3-70b-8192"
            elif query_type == QueryType.CREATIVE:
                return "mixtral-8x7b-32768"
            else:
                return "llama3-70b-8192"
        
        elif provider == AIProvider.OPENAI:
            if query_type == QueryType.VISUAL_ANALYSIS:
                return "gpt-4-vision-preview"
            elif query_type in [QueryType.CODE, QueryType.TECHNICAL, QueryType.MULTI_STEP_REASONING]:
                return "gpt-4"
            else:
                return "gpt-3.5-turbo"
        
        elif provider == AIProvider.ANTHROPIC:
            if query_type in [QueryType.MULTI_STEP_REASONING, QueryType.ANALYSIS]:
                return "claude-3-opus"
            elif query_type in [QueryType.CODE, QueryType.TECHNICAL]:
                return "claude-3-sonnet"
            else:
                return "claude-3-haiku"
        
        elif provider == AIProvider.GOOGLE:
            if query_type == QueryType.VISUAL_ANALYSIS:
                return "gemini-pro-vision"
            else:
                return "gemini-pro"
        
        return models[0]  # Default to first model
    
    def _generate_cache_key(self, message: str, context: Optional[str], query_type: QueryType) -> str:
        """Generate cache key for response caching"""
        content = f"{message}_{context or ''}_{query_type.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available and not expired"""
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if datetime.utcnow() - cached_data["timestamp"] < timedelta(seconds=self.cache_ttl):
                return cached_data["response"]
        return None
    
    def _cache_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache AI response"""
        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.utcnow()
        }
    
    async def get_enhanced_ai_response(self, message: str, context: Optional[str] = None, 
                                     session_history: List[Dict] = None, 
                                     query_type: Optional[str] = None, user_id: str = None) -> Dict[str, Any]:
        """Get enhanced AI response with smart routing and advanced capabilities"""
        
        start_time = time.time()
        
        try:
            # Classify query type if not provided
            if query_type:
                try:
                    classified_type = QueryType(query_type)
                except ValueError:
                    classified_type = self._classify_query_type(message, context)
            else:
                classified_type = self._classify_query_type(message, context)
            
            # Check cache first
            cache_key = self._generate_cache_key(message, context, classified_type)
            cached_response = self._get_cached_response(cache_key)
            
            if cached_response:
                cached_response["cached"] = True
                cached_response["response_time"] = time.time() - start_time
                return cached_response
            
            # Select optimal provider and model
            provider, model = self._select_optimal_provider(
                classified_type, 
                len(message), 
                bool(context)
            )
            
            # Handle different query types with specialized processing
            if classified_type == QueryType.VISUAL_ANALYSIS:
                response = await self._handle_visual_analysis(message, context, provider, model)
            elif classified_type == QueryType.MULTI_STEP_REASONING:
                response = await self._handle_multi_step_reasoning(message, context, provider, model)
            elif classified_type == QueryType.WORKFLOW_PARSING:
                response = await self._handle_workflow_parsing(message, context, provider, model)
            else:
                response = await self._handle_standard_query(message, context, session_history, 
                                                           provider, model, classified_type)
            
            # Add metadata to response
            response.update({
                "provider": provider.value,
                "model": model,
                "query_type": classified_type.value,
                "response_time": time.time() - start_time,
                "cached": False
            })
            
            # Update performance tracking
            self._update_provider_performance(provider, time.time() - start_time, True)
            
            # Cache successful response
            self._cache_response(cache_key, response)
            
            # Update learning data
            self._update_learning_data(classified_type, provider, user_id, True)
            
            return response
            
        except Exception as e:
            logger.error(f"Enhanced AI response error: {e}")
            
            # Update failure tracking
            if 'provider' in locals():
                self._update_provider_performance(provider, time.time() - start_time, False)
                self._update_learning_data(classified_type, provider, user_id, False)
            
            # Fallback response
            return {
                "response": f"I apologize, but I encountered an error processing your request. Error: {str(e)[:100]}",
                "provider": "fallback",
                "model": "error_handler",
                "query_type": classified_type.value if 'classified_type' in locals() else "unknown",
                "response_time": time.time() - start_time,
                "cached": False,
                "error": True
            }
    
    async def _handle_visual_analysis(self, message: str, context: Optional[str], 
                                    provider: AIProvider, model: str) -> Dict[str, Any]:
        """Handle visual analysis queries with computer vision"""
        
        try:
            # Extract image data from context or message
            image_data = await self._extract_image_data(message, context)
            
            if not image_data:
                return {
                    "response": "I'd be happy to help with visual analysis, but I don't see any image data in your request. Please provide an image URL, upload an image, or include image data.",
                    "analysis_type": "no_image_found"
                }
            
            # Analyze image with selected provider
            if provider == AIProvider.OPENAI:
                analysis = await self._analyze_with_openai_vision(image_data, message, model)
            elif provider == AIProvider.GOOGLE:
                analysis = await self._analyze_with_google_vision(image_data, message, model)
            else:
                # Fallback to description-based analysis
                analysis = await self._analyze_image_fallback(image_data, message)
            
            return {
                "response": analysis["description"],
                "visual_analysis": analysis,
                "analysis_type": "computer_vision"
            }
            
        except Exception as e:
            logger.error(f"Visual analysis error: {e}")
            return {
                "response": "I encountered an error while analyzing the visual content. Please try again or provide the image in a different format.",
                "analysis_type": "vision_error",
                "error": str(e)
            }
    
    async def _extract_image_data(self, message: str, context: Optional[str]) -> Optional[Dict[str, Any]]:
        """Extract image data from message or context"""
        
        # Check for image URLs in message
        import re
        url_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|bmp|webp)'
        urls = re.findall(url_pattern, message + (context or ""))
        
        if urls:
            # Download and process image
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(urls[0])
                    if response.status_code == 200:
                        image_bytes = response.content
                        
                        # Convert to base64
                        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        # Get image info
                        img = Image.open(io.BytesIO(image_bytes))
                        
                        return {
                            "data": image_b64,
                            "format": img.format.lower(),
                            "size": img.size,
                            "url": urls[0]
                        }
            except Exception as e:
                logger.error(f"Image download error: {e}")
        
        # Check for base64 image data
        if "base64" in message.lower() or "data:image" in message.lower():
            # Extract base64 data
            b64_pattern = r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)'
            matches = re.findall(b64_pattern, message + (context or ""))
            
            if matches:
                return {
                    "data": matches[0],
                    "format": "unknown",
                    "source": "base64"
                }
        
        return None
    
    async def _analyze_with_openai_vision(self, image_data: Dict[str, Any], 
                                        message: str, model: str) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision API"""
        
        try:
            if not self.api_keys.get(AIProvider.OPENAI):
                raise ValueError("OpenAI API key not available")
            
            # Prepare the request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_keys[AIProvider.OPENAI]}"
            }
            
            # Create vision prompt
            vision_prompt = f"""Please analyze this image and provide a detailed description. 
            Focus on: {message}
            
            Provide your analysis in the following format:
            1. Overall description
            2. Key elements and objects
            3. Colors and composition
            4. Any text or symbols
            5. Context and purpose
            """
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_data.get('format', 'jpeg')};base64,{image_data['data']}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    return {
                        "description": content,
                        "provider": "openai_vision",
                        "model": model,
                        "confidence": 0.9,
                        "features_detected": self._extract_features_from_description(content)
                    }
                else:
                    raise Exception(f"OpenAI Vision API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"OpenAI vision analysis error: {e}")
            raise e
    
    async def _analyze_with_google_vision(self, image_data: Dict[str, Any], 
                                        message: str, model: str) -> Dict[str, Any]:
        """Analyze image using Google Vision API"""
        
        try:
            if not self.api_keys.get(AIProvider.GOOGLE):
                raise ValueError("Google API key not available")
            
            # Use Google Generative AI
            headers = {
                "Content-Type": "application/json"
            }
            
            vision_prompt = f"""Analyze this image in detail. Focus on: {message}
            
            Provide comprehensive analysis including:
            - Visual elements and objects
            - Colors, lighting, and composition
            - Any text or symbols present
            - Context and potential purpose
            - Overall impression and insights
            """
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": vision_prompt},
                        {
                            "inline_data": {
                                "mime_type": f"image/{image_data.get('format', 'jpeg')}",
                                "data": image_data["data"]
                            }
                        }
                    ]
                }]
            }
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_keys[AIProvider.GOOGLE]}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    return {
                        "description": content,
                        "provider": "google_vision",
                        "model": model,
                        "confidence": 0.85,
                        "features_detected": self._extract_features_from_description(content)
                    }
                else:
                    raise Exception(f"Google Vision API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Google vision analysis error: {e}")
            raise e
    
    async def _analyze_image_fallback(self, image_data: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Fallback image analysis without vision API"""
        
        try:
            # Basic image analysis using PIL
            if image_data.get("data"):
                img_bytes = base64.b64decode(image_data["data"])
                img = Image.open(io.BytesIO(img_bytes))
                
                # Basic image properties
                width, height = img.size
                mode = img.mode
                format_type = img.format or "Unknown"
                
                # Color analysis
                colors = img.getcolors(maxcolors=256*256*256)
                dominant_color = "Unknown"
                if colors:
                    dominant_color = max(colors, key=lambda x: x[0])[1]
                
                description = f"""I can see this is a {format_type} image with dimensions {width}x{height} pixels.
                The image is in {mode} color mode. While I cannot fully analyze the visual content without vision capabilities,
                I can tell you about the technical properties of the image.
                
                To get detailed visual analysis, please use an AI service with vision capabilities or describe what you see in the image,
                and I can help you analyze or work with that information."""
                
                return {
                    "description": description,
                    "provider": "basic_analysis",
                    "model": "image_properties",
                    "confidence": 0.3,
                    "technical_info": {
                        "width": width,
                        "height": height,
                        "mode": mode,
                        "format": format_type,
                        "dominant_color": str(dominant_color)
                    }
                }
        except Exception as e:
            logger.error(f"Fallback image analysis error: {e}")
        
        return {
            "description": "I'm unable to analyze visual content directly. Please describe the image, and I'll help you work with that information.",
            "provider": "text_only",
            "model": "fallback",
            "confidence": 0.1
        }
    
    def _extract_features_from_description(self, description: str) -> List[str]:
        """Extract key features from vision description"""
        
        # Common visual features to look for
        feature_keywords = {
            "objects": ["person", "car", "building", "tree", "animal", "furniture", "device"],
            "colors": ["red", "blue", "green", "yellow", "black", "white", "orange", "purple"],
            "actions": ["walking", "running", "sitting", "standing", "driving", "flying"],
            "settings": ["indoor", "outdoor", "office", "home", "street", "nature", "city"],
            "text": ["text", "sign", "label", "writing", "words", "numbers"],
            "emotions": ["happy", "sad", "excited", "calm", "surprised", "focused"]
        }
        
        detected_features = []
        description_lower = description.lower()
        
        for category, keywords in feature_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    detected_features.append(f"{category}:{keyword}")
        
        return detected_features[:10]  # Return top 10 features
    
    async def _handle_multi_step_reasoning(self, message: str, context: Optional[str], 
                                         provider: AIProvider, model: str) -> Dict[str, Any]:
        """Handle multi-step reasoning queries"""
        
        try:
            # Enhanced reasoning prompt
            reasoning_prompt = f"""I need you to break down this problem using multi-step reasoning.

Query: {message}
Context: {context or 'No additional context provided'}

Please follow this structured reasoning approach:

1. **Problem Analysis**: What is being asked and what are the key components?
2. **Information Gathering**: What information do we have and what might be missing?
3. **Step-by-Step Breakdown**: Break the problem into logical steps
4. **Analysis & Evaluation**: Analyze each step and consider alternatives
5. **Synthesis**: Combine insights to reach a conclusion
6. **Final Answer**: Provide a clear, actionable response

Please be thorough in your reasoning and explain your thought process at each step."""

            response_text = await self._call_ai_provider(provider, model, reasoning_prompt, context)
            
            # Extract reasoning steps
            reasoning_steps = self._extract_reasoning_steps(response_text)
            
            return {
                "response": response_text,
                "reasoning_type": "multi_step",
                "reasoning_steps": reasoning_steps,
                "complexity": "high"
            }
            
        except Exception as e:
            logger.error(f"Multi-step reasoning error: {e}")
            return {
                "response": "I encountered an error while processing your multi-step reasoning request. Let me provide a simpler analysis instead.",
                "reasoning_type": "fallback",
                "error": str(e)
            }
    
    def _extract_reasoning_steps(self, response_text: str) -> List[Dict[str, str]]:
        """Extract structured reasoning steps from AI response"""
        
        steps = []
        current_step = {"title": "", "content": ""}
        
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for numbered steps or section headers
            if any(pattern in line.lower() for pattern in ["step", "analysis", "breakdown", "conclusion"]):
                if current_step["title"] or current_step["content"]:
                    steps.append(current_step.copy())
                
                current_step = {"title": line, "content": ""}
            elif line and current_step["title"]:
                current_step["content"] += line + " "
        
        # Add the last step
        if current_step["title"] or current_step["content"]:
            steps.append(current_step)
        
        return steps[:10]  # Return up to 10 reasoning steps
    
    async def _handle_workflow_parsing(self, message: str, context: Optional[str], 
                                     provider: AIProvider, model: str) -> Dict[str, Any]:
        """Handle workflow parsing queries"""
        
        try:
            workflow_prompt = f"""Please analyze this automation request and create a structured workflow:

Request: {message}
Context: {context or 'No additional context'}

Create a detailed workflow with these components:

1. **Workflow Summary**: Brief description of what will be accomplished
2. **Prerequisites**: What needs to be in place before starting
3. **Detailed Steps**: Break down into specific, actionable steps
4. **Decision Points**: Any conditional logic or branching
5. **Error Handling**: What to do if steps fail
6. **Success Criteria**: How to know the workflow completed successfully

Format your response as a structured workflow that could be implemented by an automation system."""

            response_text = await self._call_ai_provider(provider, model, workflow_prompt, context)
            
            # Extract workflow components
            workflow_structure = self._parse_workflow_structure(response_text)
            
            return {
                "response": response_text,
                "workflow_structure": workflow_structure,
                "parsing_type": "automation_workflow",
                "complexity": self._assess_workflow_complexity(workflow_structure)
            }
            
        except Exception as e:
            logger.error(f"Workflow parsing error: {e}")
            return {
                "response": "I encountered an error while parsing your workflow request. Please try describing the automation in simpler terms.",
                "parsing_type": "fallback",
                "error": str(e)
            }
    
    def _parse_workflow_structure(self, response_text: str) -> Dict[str, Any]:
        """Parse workflow structure from AI response"""
        
        structure = {
            "summary": "",
            "prerequisites": [],
            "steps": [],
            "decision_points": [],
            "error_handling": [],
            "success_criteria": []
        }
        
        current_section = None
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Identify sections
            if "summary" in line.lower() and ("workflow" in line.lower() or "description" in line.lower()):
                current_section = "summary"
            elif "prerequisite" in line.lower() or "requirement" in line.lower():
                current_section = "prerequisites"
            elif "step" in line.lower() and "detailed" in line.lower():
                current_section = "steps"
            elif "decision" in line.lower() or "conditional" in line.lower():
                current_section = "decision_points"
            elif "error" in line.lower() or "failure" in line.lower():
                current_section = "error_handling"
            elif "success" in line.lower() or "completion" in line.lower():
                current_section = "success_criteria"
            elif line and current_section:
                # Add content to current section
                if current_section == "summary":
                    structure[current_section] += line + " "
                elif line.startswith(('-', '•', '*', str(len(structure[current_section])+1))):
                    structure[current_section].append(line.lstrip('-•* ').lstrip('0123456789. '))
                elif structure[current_section]:
                    structure[current_section][-1] += " " + line
        
        # Clean up
        structure["summary"] = structure["summary"].strip()
        
        return structure
    
    def _assess_workflow_complexity(self, workflow_structure: Dict[str, Any]) -> str:
        """Assess workflow complexity"""
        
        step_count = len(workflow_structure.get("steps", []))
        decision_count = len(workflow_structure.get("decision_points", []))
        error_handling_count = len(workflow_structure.get("error_handling", []))
        
        total_complexity = step_count + (decision_count * 2) + error_handling_count
        
        if total_complexity > 15:
            return "expert"
        elif total_complexity > 10:
            return "complex"
        elif total_complexity > 5:
            return "medium"
        else:
            return "simple"
    
    async def _handle_standard_query(self, message: str, context: Optional[str], 
                                   session_history: List[Dict], provider: AIProvider, 
                                   model: str, query_type: QueryType) -> Dict[str, Any]:
        """Handle standard AI queries"""
        
        try:
            # Build context-aware prompt
            full_prompt = self._build_context_prompt(message, context, session_history, query_type)
            
            response_text = await self._call_ai_provider(provider, model, full_prompt, context)
            
            # Assess response quality
            quality_score = self._assess_response_quality(response_text, message, query_type)
            
            return {
                "response": response_text,
                "quality_score": quality_score,
                "language": self._detect_language(response_text),
                "complexity": self._assess_response_complexity(response_text)
            }
            
        except Exception as e:
            logger.error(f"Standard query error: {e}")
            raise e
    
    def _build_context_prompt(self, message: str, context: Optional[str], 
                            session_history: List[Dict], query_type: QueryType) -> str:
        """Build context-aware prompt"""
        
        prompt_parts = []
        
        # Add system context based on query type
        if query_type == QueryType.TECHNICAL:
            prompt_parts.append("You are a technical expert providing detailed, accurate technical guidance.")
        elif query_type == QueryType.CODE:
            prompt_parts.append("You are a programming expert. Provide clear, working code examples with explanations.")
        elif query_type == QueryType.CREATIVE:
            prompt_parts.append("You are a creative assistant. Be imaginative and engaging while being helpful.")
        elif query_type == QueryType.ANALYSIS:
            prompt_parts.append("You are an analytical expert. Provide thorough analysis with evidence and reasoning.")
        else:
            prompt_parts.append("You are a helpful AI assistant providing clear, accurate, and useful responses.")
        
        # Add relevant context
        if context:
            prompt_parts.append(f"\nContext: {context}")
        
        # Add relevant session history (last 3 exchanges)
        if session_history and len(session_history) > 0:
            prompt_parts.append("\nRecent conversation:")
            for exchange in session_history[-6:]:  # Last 3 exchanges (user + assistant pairs)
                role = exchange.get("role", "user")
                content = exchange.get("content", "")
                if content and len(content) < 200:  # Only include short exchanges
                    prompt_parts.append(f"{role}: {content}")
        
        # Add main query
        prompt_parts.append(f"\nUser Query: {message}")
        
        # Add specific instructions
        prompt_parts.append("\nPlease provide a helpful, accurate, and well-structured response.")
        
        return "\n".join(prompt_parts)
    
    async def _call_ai_provider(self, provider: AIProvider, model: str, 
                              prompt: str, context: Optional[str] = None) -> str:
        """Call the specified AI provider"""
        
        if provider == AIProvider.GROQ:
            return await self._call_groq(model, prompt)
        elif provider == AIProvider.OPENAI:
            return await self._call_openai(model, prompt)
        elif provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(model, prompt)
        elif provider == AIProvider.GOOGLE:
            return await self._call_google(model, prompt)
        else:
            return await self._call_groq("llama3-70b-8192", prompt)  # Fallback
    
    async def _call_groq(self, model: str, prompt: str) -> str:
        """Call Groq API"""
        
        try:
            from groq import AsyncGroq
            
            client = AsyncGroq(api_key=self.api_keys[AIProvider.GROQ])
            
            chat_completion = await client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                max_tokens=4000,
                temperature=0.7
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise e
    
    async def _call_openai(self, model: str, prompt: str) -> str:
        """Call OpenAI API"""
        
        try:
            if not self.api_keys.get(AIProvider.OPENAI):
                raise ValueError("OpenAI API key not available")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_keys[AIProvider.OPENAI]}"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"OpenAI API call error: {e}")
            raise e
    
    async def _call_anthropic(self, model: str, prompt: str) -> str:
        """Call Anthropic API"""
        
        try:
            if not self.api_keys.get(AIProvider.ANTHROPIC):
                raise ValueError("Anthropic API key not available")
            
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_keys[AIProvider.ANTHROPIC],
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": model,
                "max_tokens": 3000,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Anthropic API call error: {e}")
            raise e
    
    async def _call_google(self, model: str, prompt: str) -> str:
        """Call Google AI API"""
        
        try:
            if not self.api_keys.get(AIProvider.GOOGLE):
                raise ValueError("Google API key not available")
            
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_keys[AIProvider.GOOGLE]}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    raise Exception(f"Google API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Google API call error: {e}")
            raise e
    
    def _assess_response_quality(self, response: str, original_query: str, query_type: QueryType) -> float:
        """Assess the quality of AI response"""
        
        quality_score = 0.5  # Base score
        
        # Length check
        if 50 <= len(response) <= 2000:
            quality_score += 0.1
        elif len(response) > 2000:
            quality_score += 0.05
        
        # Relevance check (simple keyword matching)
        query_words = set(original_query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words.intersection(response_words))
        relevance_ratio = overlap / len(query_words) if query_words else 0
        quality_score += relevance_ratio * 0.2
        
        # Structure check
        if any(indicator in response for indicator in ['\n', '1.', '2.', '•', '-', '*']):
            quality_score += 0.1
        
        # Query type specific checks
        if query_type == QueryType.CODE and any(indicator in response for indicator in ['```', 'def ', 'function', 'class ']):
            quality_score += 0.1
        
        if query_type == QueryType.TECHNICAL and any(indicator in response for indicator in ['API', 'configuration', 'implementation']):
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _detect_language(self, text: str) -> str:
        """Detect language of the response"""
        
        try:
            from langdetect import detect
            return detect(text)
        except:
            return "en"  # Default to English
    
    def _assess_response_complexity(self, response: str) -> str:
        """Assess complexity of the response"""
        
        word_count = len(response.split())
        sentence_count = len([s for s in response.split('.') if s.strip()])
        
        if word_count > 500 or sentence_count > 20:
            return "high"
        elif word_count > 200 or sentence_count > 10:
            return "medium"
        else:
            return "low"
    
    def _update_provider_performance(self, provider: AIProvider, response_time: float, success: bool):
        """Update provider performance tracking"""
        
        perf_data = self.provider_performance[provider]
        
        # Update response times (keep last 20)
        perf_data["response_times"].append(response_time)
        if len(perf_data["response_times"]) > 20:
            perf_data["response_times"].pop(0)
        
        # Update success rate (exponential moving average)
        current_success = 1.0 if success else 0.0
        perf_data["success_rate"] = (perf_data["success_rate"] * 0.9) + (current_success * 0.1)
        
        # Update failure count
        if success:
            perf_data["failures"] = max(0, perf_data["failures"] - 1)
        else:
            perf_data["failures"] += 1
        
        perf_data["last_used"] = datetime.utcnow()
    
    def _update_learning_data(self, query_type: QueryType, provider: AIProvider, 
                            user_id: Optional[str], success: bool):
        """Update learning data"""
        
        # Update query patterns
        self.learning_data["query_patterns"][query_type.value] += 1
        
        # Update successful routings
        if success:
            routing_key = f"{query_type.value}:{provider.value}"
            self.learning_data["successful_routings"][routing_key] += 1
        
        # Update user preferences
        if user_id and success:
            if user_id not in self.learning_data["user_preferences"]:
                self.learning_data["user_preferences"][user_id] = {}
            
            user_prefs = self.learning_data["user_preferences"][user_id]
            if provider.value not in user_prefs:
                user_prefs[provider.value] = 0
            user_prefs[provider.value] += 1
    
    async def _optimize_provider_rankings(self):
        """Optimize provider rankings based on performance"""
        
        try:
            # Analyze performance data
            for query_type in QueryType:
                preferred_providers = self.routing_rules.get(query_type, [])
                
                # Score providers based on recent performance
                provider_scores = {}
                for provider in preferred_providers:
                    if provider in self.provider_performance:
                        perf_data = self.provider_performance[provider]
                        
                        # Calculate composite score
                        avg_response_time = (sum(perf_data["response_times"][-10:]) / 
                                           len(perf_data["response_times"][-10:])) if perf_data["response_times"] else 5.0
                        
                        speed_score = max(0, 10 - avg_response_time)  # Lower time = higher score
                        success_score = perf_data["success_rate"] * 10
                        
                        composite_score = (speed_score + success_score) / 2
                        provider_scores[provider] = composite_score
                
                # Re-rank providers
                if provider_scores:
                    sorted_providers = sorted(provider_scores.keys(), 
                                            key=lambda p: provider_scores[p], reverse=True)
                    self.routing_rules[query_type] = sorted_providers
                    
                    logger.info(f"Updated routing for {query_type.value}: {[p.value for p in sorted_providers]}")
            
        except Exception as e:
            logger.error(f"Provider ranking optimization error: {e}")
    
    async def _clean_cache(self):
        """Clean expired cache entries"""
        
        current_time = datetime.utcnow()
        expired_keys = []
        
        for cache_key, cache_data in self.response_cache.items():
            if current_time - cache_data["timestamp"] > timedelta(seconds=self.cache_ttl):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.response_cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
    
    async def _update_learning_patterns(self):
        """Update learning patterns and preferences"""
        
        try:
            # Analyze query patterns to improve classification
            most_common_queries = sorted(self.learning_data["query_patterns"].items(), 
                                       key=lambda x: x[1], reverse=True)
            
            # Analyze successful routings to improve provider selection
            successful_routings = sorted(self.learning_data["successful_routings"].items(), 
                                       key=lambda x: x[1], reverse=True)
            
            # Log insights
            if most_common_queries:
                logger.info(f"Most common query types: {most_common_queries[:3]}")
            
            if successful_routings:
                logger.info(f"Most successful routings: {successful_routings[:3]}")
            
        except Exception as e:
            logger.error(f"Learning pattern update error: {e}")
    
    # Additional utility methods
    
    async def summarize_webpage(self, content: str, length: str = "medium") -> str:
        """Summarize webpage content"""
        
        try:
            query_type = QueryType.SUMMARIZATION
            provider, model = self._select_optimal_provider(query_type, len(content))
            
            length_instructions = {
                "short": "Provide a brief 2-3 sentence summary",
                "medium": "Provide a comprehensive paragraph summary",
                "long": "Provide a detailed multi-paragraph summary with key points"
            }
            
            prompt = f"""Please summarize this webpage content:

{content[:5000]}  

{length_instructions.get(length, length_instructions['medium'])}.
Focus on the main topics, key information, and important insights."""

            return await self._call_ai_provider(provider, model, prompt)
            
        except Exception as e:
            logger.error(f"Webpage summarization error: {e}")
            return "Unable to summarize content due to an error."
    
    async def suggest_search_query(self, partial_query: str) -> List[str]:
        """Suggest search queries based on partial input"""
        
        try:
            provider, model = self._select_optimal_provider(QueryType.GENERAL, len(partial_query))
            
            prompt = f"""Based on this partial search query: "{partial_query}"
            
Suggest 5 relevant, complete search queries that the user might be looking for.
Return only the suggested queries, one per line, without numbering or bullets."""

            response = await self._call_ai_provider(provider, model, prompt)
            
            # Extract suggestions
            suggestions = [line.strip() for line in response.split('\n') if line.strip()]
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Search suggestion error: {e}")
            return [partial_query]  # Return original as fallback

# Global enhanced AI manager instance
enhanced_ai_manager = EnhancedAIManager()