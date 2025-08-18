import os
import asyncio
from typing import Dict, List, Optional, Tuple
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

class AIManager:
    def __init__(self):
        self.groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Initialize other AI clients (will use if API keys provided)
        self.openai_client = None
        self.anthropic_client = None
        self.google_client = None
        
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_key_here":
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
        if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_key_here":
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
        if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "your_google_key_here":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.google_client = genai.GenerativeModel('gemini-pro')
        
        # Response cache
        self.response_cache = TTLCache(maxsize=1000, ttl=300)  # 5 minutes cache
        
        # Model configurations
        self.model_configs = {
            AIProvider.GROQ: {
                "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
                "strengths": [QueryType.GENERAL, QueryType.TECHNICAL, QueryType.SUMMARIZATION]
            },
            AIProvider.OPENAI: {
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "strengths": [QueryType.CREATIVE, QueryType.CODE, QueryType.GENERAL]
            },
            AIProvider.ANTHROPIC: {
                "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
                "strengths": [QueryType.TECHNICAL, QueryType.CODE, QueryType.SUMMARIZATION]
            },
            AIProvider.GOOGLE: {
                "models": ["gemini-pro", "gemini-pro-vision"],
                "strengths": [QueryType.GENERAL, QueryType.TRANSLATION, QueryType.CREATIVE]
            }
        }
    
    def detect_language(self, text: str) -> str:
        """Detect the language of input text"""
        try:
            return detect(text)
        except:
            return "en"  # Default to English
    
    def classify_query_type(self, message: str) -> QueryType:
        """Classify the type of query to select best model"""
        message_lower = message.lower()
        
        # Technical indicators
        if any(word in message_lower for word in ['code', 'programming', 'api', 'function', 'algorithm', 'debug']):
            return QueryType.CODE
        
        # Summarization indicators
        if any(word in message_lower for word in ['summarize', 'summary', 'tldr', 'brief', 'overview']):
            return QueryType.SUMMARIZATION
            
        # Translation indicators
        if any(word in message_lower for word in ['translate', 'translation', 'language', 'mean in']):
            return QueryType.TRANSLATION
            
        # Creative indicators
        if any(word in message_lower for word in ['write', 'create', 'story', 'poem', 'creative', 'imagine']):
            return QueryType.CREATIVE
            
        # Technical indicators
        if any(word in message_lower for word in ['explain', 'how does', 'technical', 'documentation', 'analyze']):
            return QueryType.TECHNICAL
            
        return QueryType.GENERAL
    
    def select_best_provider(self, query_type: QueryType, available_providers: List[AIProvider]) -> AIProvider:
        """Select the best AI provider based on query type"""
        # Score providers based on their strengths
        scores = {}
        
        for provider in available_providers:
            if provider in self.model_configs:
                config = self.model_configs[provider]
                if query_type in config["strengths"]:
                    scores[provider] = len(config["strengths"]) - config["strengths"].index(query_type)
                else:
                    scores[provider] = 0
        
        # Return provider with highest score, fallback to GROQ
        if scores:
            return max(scores, key=scores.get)
        return AIProvider.GROQ
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available AI providers"""
        providers = [AIProvider.GROQ]  # Always available
        
        if self.openai_client:
            providers.append(AIProvider.OPENAI)
        if self.anthropic_client:
            providers.append(AIProvider.ANTHROPIC)
        if self.google_client:
            providers.append(AIProvider.GOOGLE)
            
        return providers
    
    async def get_ai_response_groq(self, messages: List[Dict], query_type: QueryType) -> str:
        """Get response from Groq API"""
        model = "llama-3.3-70b-versatile"
        if query_type == QueryType.GENERAL:
            model = "llama-3.1-8b-instant"  # Faster for simple queries
            
        chat_completion = self.groq_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7,
            max_tokens=1500
        )
        return chat_completion.choices[0].message.content
    
    async def get_ai_response_openai(self, messages: List[Dict], query_type: QueryType) -> str:
        """Get response from OpenAI API"""
        if not self.openai_client:
            raise Exception("OpenAI client not available")
            
        model = "gpt-4o-mini"
        if query_type in [QueryType.CREATIVE, QueryType.CODE]:
            model = "gpt-4o"
            
        response = self.openai_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    
    async def get_ai_response_anthropic(self, messages: List[Dict], query_type: QueryType) -> str:
        """Get response from Anthropic Claude API"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not available")
            
        model = "claude-3-haiku-20240307"
        if query_type in [QueryType.TECHNICAL, QueryType.CODE]:
            model = "claude-3-5-sonnet-20241022"
        
        # Convert messages format for Claude
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        response = self.anthropic_client.messages.create(
            model=model,
            max_tokens=1500,
            temperature=0.7,
            system=system_message,
            messages=user_messages
        )
        return response.content[0].text
    
    async def get_ai_response_google(self, messages: List[Dict], query_type: QueryType) -> str:
        """Get response from Google Gemini API"""
        if not self.google_client:
            raise Exception("Google client not available")
        
        # Convert messages to Gemini format
        prompt = ""
        for msg in messages:
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n"
            elif msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n"
        
        response = self.google_client.generate_content(prompt)
        return response.text
    
    async def get_smart_response(self, message: str, context: Optional[str] = None, 
                                session_history: List[Dict] = None) -> Tuple[str, AIProvider]:
        """Get AI response using smart model selection"""
        
        # Create cache key
        cache_key = f"{message}_{context}_{len(session_history or [])}"
        if cache_key in self.response_cache:
            logger.info(f"Cache hit for query: {message[:50]}...")
            return self.response_cache[cache_key]
        
        # Detect language and query type
        language = self.detect_language(message)
        query_type = self.classify_query_type(message)
        
        logger.info(f"Query type: {query_type.value}, Language: {language}")
        
        # Get available providers and select best one
        available_providers = self.get_available_providers()
        selected_provider = self.select_best_provider(query_type, available_providers)
        
        logger.info(f"Selected provider: {selected_provider.value}")
        
        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": f"""You are AETHER AI Assistant, an intelligent browser companion. 
                Language detected: {language}
                Query type: {query_type.value}
                
                Provide helpful, accurate, and concise responses. If the user is not using English, 
                respond in their detected language ({language}) unless they specifically ask for English.
                
                For technical queries, be precise and detailed.
                For creative queries, be imaginative and engaging.
                For summarization, be concise and structured.
                """
            }
        ]
        
        # Add session history (last 25 messages for extended memory)
        if session_history:
            messages.extend(session_history[-25:])
        
        # Add context if available
        if context:
            messages.append({
                "role": "system",
                "content": f"Current webpage context: {context[:3000]}"
            })
        
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Try to get response with fallback
        response = None
        used_provider = selected_provider
        
        try:
            if selected_provider == AIProvider.GROQ:
                response = await self.get_ai_response_groq(messages, query_type)
            elif selected_provider == AIProvider.OPENAI:
                response = await self.get_ai_response_openai(messages, query_type)
            elif selected_provider == AIProvider.ANTHROPIC:
                response = await self.get_ai_response_anthropic(messages, query_type)
            elif selected_provider == AIProvider.GOOGLE:
                response = await self.get_ai_response_google(messages, query_type)
                
        except Exception as e:
            logger.error(f"Error with {selected_provider.value}: {e}")
            
            # Fallback to Groq if other providers fail
            if selected_provider != AIProvider.GROQ:
                try:
                    response = await self.get_ai_response_groq(messages, query_type)
                    used_provider = AIProvider.GROQ
                except Exception as groq_error:
                    logger.error(f"Groq fallback failed: {groq_error}")
                    response = f"I'm experiencing technical difficulties. Please try again in a moment."
                    used_provider = AIProvider.GROQ
        
        if not response:
            response = "I apologize, but I'm unable to process your request right now. Please try again."
        
        # Cache the response
        result = (response, used_provider)
        self.response_cache[cache_key] = result
        
        return result
    
    async def summarize_webpage(self, content: str, length: str = "medium") -> str:
        """Summarize webpage content in different lengths"""
        
        length_configs = {
            "short": {"max_tokens": 100, "instruction": "in 2-3 sentences"},
            "medium": {"max_tokens": 300, "instruction": "in 1-2 paragraphs"},
            "long": {"max_tokens": 600, "instruction": "in detail with key points"}
        }
        
        config = length_configs.get(length, length_configs["medium"])
        
        messages = [
            {
                "role": "system",
                "content": f"Summarize the following webpage content {config['instruction']}. Focus on the main topics and key information."
            },
            {
                "role": "user",
                "content": f"Please summarize this webpage: {content[:4000]}"
            }
        ]
        
        try:
            response = await self.get_ai_response_groq(messages, QueryType.SUMMARIZATION)
            return response
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Unable to summarize content at this time."
    
    async def suggest_search_query(self, user_intent: str) -> List[str]:
        """Suggest better search queries based on user intent"""
        
        messages = [
            {
                "role": "system",
                "content": "You are a search query optimization expert. Given a user's search intent, suggest 3-5 better, more specific search queries that would yield better results. Return only the queries, one per line."
            },
            {
                "role": "user",
                "content": f"Improve this search query: {user_intent}"
            }
        ]
        
        try:
            response = await self.get_ai_response_groq(messages, QueryType.GENERAL)
            queries = [q.strip() for q in response.split('\n') if q.strip()]
            return queries[:5]  # Return max 5 suggestions
        except Exception as e:
            logger.error(f"Search suggestion error: {e}")
            return [user_intent]  # Return original query as fallback

# Global AI manager instance
ai_manager = AIManager()