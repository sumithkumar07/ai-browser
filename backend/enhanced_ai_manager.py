import os
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import groq
import openai
import anthropic
import google.generativeai as genai
from langdetect import detect
import json
import time
from cachetools import TTLCache
import logging
import base64
import httpx
from PIL import Image
import io
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    GROQ = "groq"
    OPENAI = "openai" 
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class QueryType(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    CODE = "code"
    VISUAL = "visual"
    AUTOMATION = "automation"
    RESEARCH = "research"

class EnhancedAIManager:
    def __init__(self):
        # Initialize AI clients
        self.groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
        
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_key_here":
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
        if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_key_here":
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
        if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "your_google_key_here":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.google_client = genai.GenerativeModel('gemini-pro-vision')
        
        # Enhanced caching with multiple layers
        self.response_cache = TTLCache(maxsize=2000, ttl=600)  # 10 minutes cache
        self.context_cache = TTLCache(maxsize=1000, ttl=1800)  # 30 minutes context cache
        self.user_memory = TTLCache(maxsize=500, ttl=7200)     # 2 hours user memory
        
        # Enhanced model configurations
        self.model_configs = {
            AIProvider.GROQ: {
                "models": {
                    "fast": "llama-3.1-8b-instant",
                    "smart": "llama-3.3-70b-versatile",
                    "reasoning": "llama-3.3-70b-versatile"
                },
                "strengths": [QueryType.GENERAL, QueryType.TECHNICAL, QueryType.SUMMARIZATION, QueryType.AUTOMATION],
                "max_tokens": 8000
            },
            AIProvider.OPENAI: {
                "models": {
                    "fast": "gpt-4o-mini",
                    "smart": "gpt-4o",
                    "reasoning": "o1-preview",
                    "vision": "gpt-4o"
                },
                "strengths": [QueryType.CREATIVE, QueryType.CODE, QueryType.VISUAL, QueryType.RESEARCH],
                "max_tokens": 4000
            },
            AIProvider.ANTHROPIC: {
                "models": {
                    "fast": "claude-3-haiku-20240307",
                    "smart": "claude-3-5-sonnet-20241022",
                    "reasoning": "claude-3-5-sonnet-20241022"
                },
                "strengths": [QueryType.TECHNICAL, QueryType.CODE, QueryType.SUMMARIZATION, QueryType.RESEARCH],
                "max_tokens": 8000
            },
            AIProvider.GOOGLE: {
                "models": {
                    "fast": "gemini-1.5-flash",
                    "smart": "gemini-1.5-pro",
                    "vision": "gemini-1.5-pro-vision"
                },
                "strengths": [QueryType.GENERAL, QueryType.TRANSLATION, QueryType.CREATIVE, QueryType.VISUAL],
                "max_tokens": 8000
            }
        }
        
        # Response quality tracking
        self.response_quality_scores = {}
        self.model_performance_stats = {}
        
    def detect_language_enhanced(self, text: str) -> str:
        """Enhanced language detection with confidence scoring"""
        try:
            detected = detect(text)
            # Add confidence checking and fallback logic
            return detected if detected else "en"
        except:
            return "en"
    
    def classify_query_advanced(self, message: str, context: Optional[str] = None) -> QueryType:
        """Advanced query classification with context awareness"""
        message_lower = message.lower()
        
        # Visual/screenshot indicators
        if any(word in message_lower for word in ['screenshot', 'image', 'visual', 'see this page', 'what does this look like']):
            return QueryType.VISUAL
        
        # Automation indicators (enhanced)
        automation_keywords = [
            'automate', 'apply to', 'find and apply', 'save to', 'send to', 
            'schedule', 'create workflow', 'bulk action', 'mass process',
            'login to', 'navigate to', 'fill form', 'click button'
        ]
        if any(keyword in message_lower for keyword in automation_keywords):
            return QueryType.AUTOMATION
        
        # Research indicators (enhanced)
        if any(word in message_lower for word in ['research', 'compare', 'analyze trends', 'gather information', 'compile data']):
            return QueryType.RESEARCH
            
        # Code indicators
        if any(word in message_lower for word in ['code', 'programming', 'api', 'function', 'algorithm', 'debug', 'script']):
            return QueryType.CODE
        
        # Technical indicators
        if any(word in message_lower for word in ['explain', 'how does', 'technical', 'documentation', 'system']):
            return QueryType.TECHNICAL
            
        # Creative indicators  
        if any(word in message_lower for word in ['write', 'create', 'story', 'poem', 'creative', 'imagine', 'brainstorm']):
            return QueryType.CREATIVE
        
        # Summarization indicators
        if any(word in message_lower for word in ['summarize', 'summary', 'tldr', 'brief', 'overview', 'key points']):
            return QueryType.SUMMARIZATION
            
        # Translation indicators
        if any(word in message_lower for word in ['translate', 'translation', 'language', 'mean in', 'convert to']):
            return QueryType.TRANSLATION
        
        return QueryType.GENERAL
    
    def select_optimal_provider_and_model(self, query_type: QueryType, complexity: str = "medium", 
                                        available_providers: List[AIProvider] = None) -> Tuple[AIProvider, str]:
        """Select optimal provider and model based on query type and complexity"""
        
        if available_providers is None:
            available_providers = self.get_available_providers()
        
        # Complexity-based model selection
        model_tier = "fast" if complexity == "simple" else "smart" if complexity == "medium" else "reasoning"
        
        # Provider scoring based on query type and performance stats
        provider_scores = {}
        
        for provider in available_providers:
            if provider in self.model_configs:
                config = self.model_configs[provider]
                
                # Base score from strengths
                base_score = 10 if query_type in config["strengths"] else 5
                
                # Performance bonus from historical data
                perf_stats = self.model_performance_stats.get(provider.value, {})
                success_rate = perf_stats.get("success_rate", 0.9)
                avg_response_time = perf_stats.get("avg_response_time", 2.0)
                
                performance_score = (success_rate * 10) - (avg_response_time * 0.5)
                
                provider_scores[provider] = base_score + performance_score
        
        # Select best provider
        best_provider = max(provider_scores.keys(), key=lambda p: provider_scores[p]) if provider_scores else AIProvider.GROQ
        
        # Select appropriate model for complexity
        models = self.model_configs[best_provider]["models"]
        selected_model = models.get(model_tier, models.get("smart", list(models.values())[0]))
        
        return best_provider, selected_model
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available AI providers"""
        providers = [AIProvider.GROQ]
        
        if self.openai_client:
            providers.append(AIProvider.OPENAI)
        if self.anthropic_client:
            providers.append(AIProvider.ANTHROPIC)
        if self.google_client:
            providers.append(AIProvider.GOOGLE)
            
        return providers
    
    async def capture_webpage_screenshot(self, page_content: str, url: str) -> Optional[str]:
        """Capture webpage screenshot for visual understanding"""
        try:
            # This would integrate with the real browser engine
            # For now, return None - will be implemented with browser integration
            return None
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None
    
    async def analyze_webpage_visually(self, screenshot_data: str, query: str) -> str:
        """Analyze webpage screenshot using vision model"""
        if not screenshot_data or not self.openai_client:
            return "Visual analysis not available"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Analyze this webpage screenshot and answer: {query}"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{screenshot_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Visual analysis failed: {e}")
            return "Visual analysis failed"
    
    def build_enhanced_context(self, message: str, page_context: Optional[str] = None,
                             session_history: List[Dict] = None, user_id: str = None) -> List[Dict]:
        """Build enhanced context with memory and learning"""
        
        messages = []
        
        # System message with enhanced capabilities
        system_content = """You are AETHER AI Assistant, an advanced AI-powered browser companion with the following enhanced capabilities:

🧠 ENHANCED INTELLIGENCE:
- Multi-context awareness across browsing sessions
- Visual webpage understanding and analysis  
- Advanced workflow automation and task execution
- Predictive suggestions based on user patterns
- Cross-platform integration and data synthesis

🎯 RESPONSE EXCELLENCE:
- Provide contextually aware, actionable responses
- Suggest relevant automations and workflows
- Anticipate user needs based on current context
- Offer multiple solution approaches when appropriate
- Maintain conversation continuity across sessions

🛠 CAPABILITIES:
- Execute complex multi-step automations
- Analyze and interact with webpage content
- Coordinate tasks across multiple platforms
- Generate intelligent suggestions and recommendations
- Learn from user patterns and preferences

Always be helpful, accurate, and proactive in suggesting ways to enhance the user's browsing and productivity experience."""

        messages.append({"role": "system", "content": system_content})
        
        # Add user memory context if available
        if user_id:
            user_context = self.user_memory.get(user_id, {})
            if user_context:
                memory_summary = f"User Context: {json.dumps(user_context, indent=2)}"
                messages.append({"role": "system", "content": f"Previous context and preferences:\n{memory_summary}"})
        
        # Add enhanced session history (last 50 messages with intelligent pruning)
        if session_history:
            # Intelligent history pruning - keep important messages
            important_messages = []
            for msg in session_history[-50:]:
                # Keep messages with automation, important decisions, or context
                if any(keyword in msg.get("content", "").lower() for keyword in 
                      ["automate", "workflow", "remember", "important", "save", "setup"]):
                    important_messages.append(msg)
                elif len(important_messages) < 20:  # Keep recent messages
                    important_messages.append(msg)
            
            messages.extend(important_messages)
        
        # Add current page context
        if page_context:
            context_summary = f"Current webpage context:\n{page_context[:4000]}"
            messages.append({"role": "system", "content": context_summary})
        
        # Add user query
        messages.append({"role": "user", "content": message})
        
        return messages
    
    async def get_enhanced_ai_response(self, message: str, context: Optional[str] = None, 
                                     session_history: List[Dict] = None, user_id: str = None,
                                     screenshot_data: str = None) -> Dict[str, Any]:
        """Get enhanced AI response with all advanced capabilities"""
        
        start_time = time.time()
        
        # Create cache key
        cache_key = hashlib.md5(f"{message}_{context}_{user_id}".encode()).hexdigest()
        
        # Check cache first
        if cache_key in self.response_cache:
            cached_response = self.response_cache[cache_key]
            cached_response["cached"] = True
            return cached_response
        
        # Detect language and classify query
        language = self.detect_language_enhanced(message)
        query_type = self.classify_query_advanced(message, context)
        
        # Determine complexity
        complexity = "simple" if len(message) < 50 else "medium" if len(message) < 200 else "complex"
        
        # Select optimal provider and model
        provider, model = self.select_optimal_provider_and_model(query_type, complexity)
        
        # Handle visual queries
        if query_type == QueryType.VISUAL and screenshot_data:
            visual_analysis = await self.analyze_webpage_visually(screenshot_data, message)
            context = f"{context}\n\nVisual Analysis: {visual_analysis}" if context else f"Visual Analysis: {visual_analysis}"
        
        # Build enhanced context
        messages = self.build_enhanced_context(message, context, session_history, user_id)
        
        # Get AI response with fallback chain
        response = None
        used_provider = provider
        
        try:
            if provider == AIProvider.GROQ:
                response = await self._get_groq_response(messages, model, query_type)
            elif provider == AIProvider.OPENAI:
                response = await self._get_openai_response(messages, model, query_type)
            elif provider == AIProvider.ANTHROPIC:
                response = await self._get_anthropic_response(messages, model, query_type)
            elif provider == AIProvider.GOOGLE:
                response = await self._get_google_response(messages, model, query_type)
                
        except Exception as e:
            logger.error(f"Error with {provider.value}: {e}")
            
            # Intelligent fallback chain
            fallback_providers = [p for p in self.get_available_providers() if p != provider]
            for fallback_provider in fallback_providers:
                try:
                    _, fallback_model = self.select_optimal_provider_and_model(query_type, "medium", [fallback_provider])
                    
                    if fallback_provider == AIProvider.GROQ:
                        response = await self._get_groq_response(messages, fallback_model, query_type)
                    elif fallback_provider == AIProvider.OPENAI:
                        response = await self._get_openai_response(messages, fallback_model, query_type)
                    elif fallback_provider == AIProvider.ANTHROPIC:
                        response = await self._get_anthropic_response(messages, fallback_model, query_type)
                    elif fallback_provider == AIProvider.GOOGLE:
                        response = await self._get_google_response(messages, fallback_model, query_type)
                    
                    used_provider = fallback_provider
                    break
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback {fallback_provider.value} failed: {fallback_error}")
                    continue
        
        if not response:
            response = "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
        
        # Calculate metrics
        response_time = time.time() - start_time
        
        # Update performance stats
        self._update_performance_stats(used_provider.value, query_type.value, response_time, bool(response))
        
        # Update user memory
        if user_id and response:
            self._update_user_memory(user_id, message, response, query_type.value)
        
        result = {
            "response": response,
            "provider": used_provider.value,
            "model": model,
            "query_type": query_type.value,
            "language": language,
            "complexity": complexity,
            "response_time": response_time,
            "cached": False
        }
        
        # Cache successful responses
        if response:
            self.response_cache[cache_key] = result
        
        return result
    
    async def _get_groq_response(self, messages: List[Dict], model: str, query_type: QueryType) -> str:
        """Enhanced Groq API response"""
        max_tokens = self.model_configs[AIProvider.GROQ]["max_tokens"]
        temperature = 0.3 if query_type in [QueryType.TECHNICAL, QueryType.CODE] else 0.7
        
        chat_completion = self.groq_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=min(max_tokens, 4000)
        )
        return chat_completion.choices[0].message.content
    
    async def _get_openai_response(self, messages: List[Dict], model: str, query_type: QueryType) -> str:
        """Enhanced OpenAI API response"""
        if not self.openai_client:
            raise Exception("OpenAI client not available")
        
        max_tokens = self.model_configs[AIProvider.OPENAI]["max_tokens"]
        temperature = 0.3 if query_type in [QueryType.TECHNICAL, QueryType.CODE] else 0.7
        
        response = self.openai_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=min(max_tokens, 4000)
        )
        return response.choices[0].message.content
    
    async def _get_anthropic_response(self, messages: List[Dict], model: str, query_type: QueryType) -> str:
        """Enhanced Anthropic Claude API response"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not available")
        
        max_tokens = self.model_configs[AIProvider.ANTHROPIC]["max_tokens"]
        temperature = 0.3 if query_type in [QueryType.TECHNICAL, QueryType.CODE] else 0.7
        
        # Convert messages format for Claude
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message += msg["content"] + "\n"
            else:
                user_messages.append(msg)
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=min(max_tokens, 4000),
            temperature=temperature,
            system=system_message.strip(),
            messages=user_messages
        )
        return response.content[0].text
    
    async def _get_google_response(self, messages: List[Dict], model: str, query_type: QueryType) -> str:
        """Enhanced Google Gemini API response"""
        if not self.google_client:
            raise Exception("Google client not available")
        
        # Convert messages to Gemini format
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"System Instructions: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        response = self.google_client.generate_content(prompt)
        return response.text
    
    def _update_performance_stats(self, provider: str, query_type: str, response_time: float, success: bool):
        """Update provider performance statistics"""
        if provider not in self.model_performance_stats:
            self.model_performance_stats[provider] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_response_time": 0,
                "response_times": [],
                "query_types": {},
                "success_rate": 0.9
            }
        
        stats = self.model_performance_stats[provider]
        stats["total_calls"] += 1
        stats["response_times"].append(response_time)
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        # Calculate rolling averages
        stats["avg_response_time"] = sum(stats["response_times"][-100:]) / len(stats["response_times"][-100:])
        stats["success_rate"] = stats["successful_calls"] / stats["total_calls"] if stats["total_calls"] > 0 else 0.9
        
        # Track query types
        if query_type not in stats["query_types"]:
            stats["query_types"][query_type] = 0
        stats["query_types"][query_type] += 1
    
    def _update_user_memory(self, user_id: str, message: str, response: str, query_type: str):
        """Update user memory for personalization"""
        if user_id not in self.user_memory:
            self.user_memory[user_id] = {
                "preferences": {},
                "frequent_topics": {},
                "automation_patterns": {},
                "language_preference": "en"
            }
        
        user_data = self.user_memory[user_id]
        
        # Track frequent topics
        if query_type not in user_data["frequent_topics"]:
            user_data["frequent_topics"][query_type] = 0
        user_data["frequent_topics"][query_type] += 1
        
        # Detect language preference
        detected_lang = self.detect_language_enhanced(message)
        user_data["language_preference"] = detected_lang
        
        # Track automation patterns
        if "automate" in message.lower() or "workflow" in message.lower():
            automation_key = message.lower()[:50]  # First 50 chars as pattern
            if automation_key not in user_data["automation_patterns"]:
                user_data["automation_patterns"][automation_key] = 0
            user_data["automation_patterns"][automation_key] += 1
    
    async def get_personalized_suggestions(self, user_id: str, current_context: str) -> List[Dict[str, Any]]:
        """Get personalized suggestions based on user patterns"""
        
        if user_id not in self.user_memory:
            return []
        
        user_data = self.user_memory[user_id]
        suggestions = []
        
        # Suggest based on frequent topics
        frequent_topics = sorted(user_data["frequent_topics"].items(), key=lambda x: x[1], reverse=True)[:3]
        
        for topic, count in frequent_topics:
            if topic == "automation":
                suggestions.append({
                    "type": "automation",
                    "title": "Create Workflow",
                    "description": f"You frequently use automation. Want to create a workflow for this page?",
                    "confidence": min(count * 0.1, 0.9)
                })
            elif topic == "research":
                suggestions.append({
                    "type": "research",
                    "title": "Research Assistant",
                    "description": "I can help gather information from multiple sources on this topic.",
                    "confidence": min(count * 0.1, 0.9)
                })
        
        # Context-based suggestions
        if "job" in current_context.lower() or "linkedin" in current_context.lower():
            suggestions.append({
                "type": "job_automation",
                "title": "Job Application Assistant",
                "description": "I can help automate job applications based on your profile.",
                "confidence": 0.8
            })
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def start_learning_engine(self):
        """Start the learning engine for continuous improvement"""
        logger.info("Enhanced AI Manager learning engine started")
        # Background learning could be implemented here
        
    async def get_enhanced_ai_response(self, message: str, context: Optional[str] = None, 
                                     session_history: List[Dict] = None, user_id: str = None) -> Dict[str, Any]:
        """Main method to get enhanced AI response - handles all the intelligence"""
        
        # This is the main method that should be called from server.py
        # It combines all the enhanced features
        
        start_time = time.time()
        
        # Detect language and classify query
        language = self.detect_language_enhanced(message)
        query_type = self.classify_query_advanced(message, context)
        
        # Create cache key
        context_hash = hashlib.md5((context or "").encode()).hexdigest()[:8]
        cache_key = f"{message}:{query_type.value}:{context_hash}:{language}"
        
        # Check cache first
        if cache_key in self.response_cache:
            cached_result = self.response_cache[cache_key]
            cached_result["cached"] = True
            return cached_result
        
        # Determine optimal provider and model
        complexity = "medium"
        provider, model = self.select_optimal_provider_and_model(query_type, complexity)
        
        # Build messages with enhanced context
        messages = self._build_enhanced_messages(message, context, session_history, query_type, language)
        
        try:
            # Get response from selected provider
            if provider == AIProvider.GROQ:
                response = await self._get_groq_response(messages, model, query_type)
            elif provider == AIProvider.OPENAI and self.openai_client:
                response = await self._get_openai_response(messages, model, query_type)
            elif provider == AIProvider.ANTHROPIC and self.anthropic_client:
                response = await self._get_anthropic_response(messages, model, query_type)
            elif provider == AIProvider.GOOGLE and self.google_client:
                response = await self._get_google_response(messages, model, query_type)
            else:
                # Fallback to Groq
                response = await self._get_groq_response(messages, self.model_configs[AIProvider.GROQ]["models"]["smart"], query_type)
                provider = AIProvider.GROQ
                model = self.model_configs[AIProvider.GROQ]["models"]["smart"]
            
            response_time = time.time() - start_time
            
            # Update performance stats
            self._update_performance_stats(provider.value, query_type.value, response_time, True)
            
            # Update user memory
            if user_id:
                self._update_user_memory(user_id, message, response, query_type.value)
            
            result = {
                "response": response,
                "provider": provider.value,
                "model": model,
                "query_type": query_type.value,
                "language": language,
                "complexity": complexity,
                "response_time": response_time,
                "cached": False
            }
            
            # Cache successful responses
            if response:
                self.response_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Update performance stats for failure
            self._update_performance_stats(provider.value, query_type.value, response_time, False)
            
            logger.error(f"Enhanced AI response failed for {provider.value}: {e}")
            
            # Fallback response
            return {
                "response": f"I apologize, but I'm experiencing technical difficulties with the AI service. Please try again in a moment.",
                "provider": "fallback",
                "model": "fallback",
                "query_type": query_type.value,
                "language": language,
                "complexity": "simple",
                "response_time": response_time,
                "cached": False,
                "error": True
            }


# Global enhanced AI manager instance

    async def summarize_webpage(self, content: str, length: str = "medium") -> str:
        """Summarize webpage content"""
        
        try:
            query_type = QueryType.SUMMARIZATION
            complexity = "medium"
            provider, model = self.select_optimal_provider_and_model(query_type, complexity)
            
            length_instructions = {
                "short": "Provide a brief 2-3 sentence summary",
                "medium": "Provide a comprehensive paragraph summary", 
                "long": "Provide a detailed multi-paragraph summary with key points"
            }
            
            messages = [{
                "role": "user",
                "content": f"""Please summarize this webpage content:

{content[:5000]}  

{length_instructions.get(length, length_instructions['medium'])}.
Focus on the main topics, key information, and important insights."""
            }]

            # Get response from selected provider
            if provider == AIProvider.GROQ:
                response = await self._get_groq_response(messages, model, query_type)
            elif provider == AIProvider.OPENAI and self.openai_client:
                response = await self._get_openai_response(messages, model, query_type)
            elif provider == AIProvider.ANTHROPIC and self.anthropic_client:
                response = await self._get_anthropic_response(messages, model, query_type)
            elif provider == AIProvider.GOOGLE and self.google_client:
                response = await self._get_google_response(messages, model, query_type)
            else:
                response = await self._get_groq_response(messages, "llama-3.1-8b-instant", query_type)

            return response
            
        except Exception as e:
            logger.error(f"Webpage summarization error: {e}")
            return "Unable to summarize content due to an error."
    
    async def suggest_search_query(self, partial_query: str) -> List[str]:
        """Suggest search queries based on partial input"""
        
        try:
            provider, model = self.select_optimal_provider_and_model(QueryType.GENERAL, "medium")
            
            messages = [{
                "role": "user", 
                "content": f"""Based on this partial search query: "{partial_query}"
            
Suggest 5 relevant, complete search queries that the user might be looking for.
Return only the suggested queries, one per line, without numbering or bullets."""
            }]

            # Get response from selected provider
            if provider == AIProvider.GROQ:
                response = await self._get_groq_response(messages, model, QueryType.GENERAL)
            elif provider == AIProvider.OPENAI and self.openai_client:
                response = await self._get_openai_response(messages, model, QueryType.GENERAL)
            elif provider == AIProvider.ANTHROPIC and self.anthropic_client:
                response = await self._get_anthropic_response(messages, model, QueryType.GENERAL)
            elif provider == AIProvider.GOOGLE and self.google_client:
                response = await self._get_google_response(messages, model, QueryType.GENERAL)
            else:
                response = await self._get_groq_response(messages, "llama-3.1-8b-instant", QueryType.GENERAL)
            
            # Extract suggestions
            suggestions = [line.strip() for line in response.split('\n') if line.strip()]
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Search suggestion error: {e}")
            return [partial_query]  # Return original as fallback

enhanced_ai_manager = EnhancedAIManager()