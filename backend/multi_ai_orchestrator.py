"""
PHASE 1: Multi-AI Provider Excellence System
Advanced AI orchestration with intelligent routing and performance optimization
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from datetime import datetime, timedelta

import openai
import anthropic
from groq import Groq
import google.generativeai as genai

# Configure logging
logger = logging.getLogger(__name__)

class AIProvider(Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    EMERGENT = "emergent"

class QueryType(Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"
    CODE_GENERATION = "code_generation"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"

@dataclass
class AIResponse:
    content: str
    provider: AIProvider
    model: str
    response_time: float
    quality_score: float
    cost: float
    cached: bool = False
    metadata: Dict[str, Any] = None

@dataclass
class ProviderMetrics:
    provider: AIProvider
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    avg_quality_score: float = 0.0
    total_cost: float = 0.0
    last_updated: datetime = None

class MultiAIOrchestrator:
    """
    Advanced AI orchestration system that intelligently routes queries
    to the best AI provider based on performance metrics and query characteristics
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.providers = {}
        self.metrics = {}
        self.response_cache = {}
        self.quality_analyzer = AIQualityAnalyzer()
        self.cost_tracker = CostTracker()
        
        # Initialize providers
        self._initialize_providers()
        
        # Performance tracking
        self._initialize_metrics()
        
        # Cost and performance thresholds
        self.max_cost_per_query = self.config.get('max_cost_per_query', 0.50)
        self.min_quality_threshold = self.config.get('min_quality_threshold', 0.7)
        self.max_response_time = self.config.get('max_response_time', 10.0)
    
    def _initialize_providers(self):
        """Initialize AI providers with their configurations"""
        # Groq (Ultra-fast inference)
        if groq_key := self.config.get('groq_api_key'):
            self.providers[AIProvider.GROQ] = {
                'client': Groq(api_key=groq_key),
                'models': ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'],
                'strengths': ['speed', 'general_conversation', 'real_time'],
                'cost_per_token': 0.00001,
                'max_tokens': 8192
            }
        
        # OpenAI (General intelligence)
        if openai_key := self.config.get('openai_api_key'):
            openai.api_key = openai_key
            self.providers[AIProvider.OPENAI] = {
                'client': openai,
                'models': ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
                'strengths': ['general_intelligence', 'code_generation', 'problem_solving'],
                'cost_per_token': 0.00003,
                'max_tokens': 128000
            }
        
        # Anthropic (Reasoning and analysis)
        if anthropic_key := self.config.get('anthropic_api_key'):
            self.providers[AIProvider.ANTHROPIC] = {
                'client': anthropic.Anthropic(api_key=anthropic_key),
                'models': ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307'],
                'strengths': ['reasoning', 'analysis', 'safety', 'long_context'],
                'cost_per_token': 0.000015,
                'max_tokens': 200000
            }
        
        # Google (Search and knowledge)
        if google_key := self.config.get('google_api_key'):
            genai.configure(api_key=google_key)
            self.providers[AIProvider.GOOGLE] = {
                'client': genai,
                'models': ['gemini-pro', 'gemini-pro-vision'],
                'strengths': ['knowledge', 'factual_accuracy', 'multilingual'],
                'cost_per_token': 0.0000125,
                'max_tokens': 32000
            }
        
        # Emergent (Specialized tasks)
        if emergent_key := self.config.get('emergent_llm_key'):
            self.providers[AIProvider.EMERGENT] = {
                'api_key': emergent_key,
                'models': ['universal-model'],
                'strengths': ['specialized_tasks', 'workflow_automation'],
                'cost_per_token': 0.00002,
                'max_tokens': 16000
            }
    
    def _initialize_metrics(self):
        """Initialize performance metrics for all providers"""
        for provider in AIProvider:
            self.metrics[provider] = ProviderMetrics(
                provider=provider,
                last_updated=datetime.now()
            )
    
    async def get_optimal_response(
        self,
        query: str,
        context: Optional[str] = None,
        query_type: QueryType = QueryType.GENERAL,
        preferences: Dict[str, Any] = None
    ) -> AIResponse:
        """
        Get the optimal AI response by selecting the best provider
        """
        preferences = preferences or {}
        
        # Check cache first
        cache_key = self._generate_cache_key(query, context, query_type)
        if cached_response := self.response_cache.get(cache_key):
            if self._is_cache_valid(cached_response):
                cached_response.cached = True
                return cached_response
        
        # Select optimal provider
        optimal_provider = await self._select_optimal_provider(
            query, query_type, preferences
        )
        
        # Get response from selected provider
        try:
            response = await self._get_provider_response(
                optimal_provider, query, context, query_type
            )
            
            # Analyze quality and update metrics
            quality_score = await self.quality_analyzer.analyze_response(
                response.content, query, context
            )
            response.quality_score = quality_score
            
            # Update provider metrics
            await self._update_provider_metrics(optimal_provider, response, True)
            
            # Cache response
            self.response_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            logger.error(f"Provider {optimal_provider} failed: {e}")
            
            # Update failure metrics
            await self._update_provider_metrics(optimal_provider, None, False)
            
            # Try fallback provider
            fallback_provider = await self._get_fallback_provider(optimal_provider)
            if fallback_provider:
                return await self._get_provider_response(
                    fallback_provider, query, context, query_type
                )
            
            raise Exception(f"All AI providers failed for query: {query[:50]}...")
    
    async def _select_optimal_provider(
        self,
        query: str,
        query_type: QueryType,
        preferences: Dict[str, Any]
    ) -> AIProvider:
        """
        Select the optimal AI provider based on query characteristics and performance
        """
        # Analyze query characteristics
        query_analysis = await self._analyze_query(query, query_type)
        
        # Calculate scores for each available provider
        provider_scores = {}
        
        for provider, config in self.providers.items():
            score = await self._calculate_provider_score(
                provider, config, query_analysis, preferences
            )
            provider_scores[provider] = score
        
        # Select provider with highest score
        if not provider_scores:
            raise Exception("No AI providers available")
        
        optimal_provider = max(provider_scores.keys(), key=lambda p: provider_scores[p])
        
        logger.info(f"Selected {optimal_provider.value} for query type {query_type.value}")
        return optimal_provider
    
    async def _calculate_provider_score(
        self,
        provider: AIProvider,
        config: Dict[str, Any],
        query_analysis: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> float:
        """
        Calculate a comprehensive score for provider selection
        """
        score = 0.0
        metrics = self.metrics[provider]
        
        # Performance metrics (40% of score)
        if metrics.successful_requests > 0:
            success_rate = metrics.successful_requests / max(metrics.total_requests, 1)
            avg_response_time = min(metrics.avg_response_time / self.max_response_time, 1.0)
            quality_score = metrics.avg_quality_score
            
            performance_score = (
                success_rate * 0.4 +
                (1.0 - avg_response_time) * 0.3 +
                quality_score * 0.3
            )
            score += performance_score * 0.4
        else:
            # Default score for untested providers
            score += 0.3
        
        # Provider strengths alignment (30% of score)
        strengths = config.get('strengths', [])
        query_requirements = query_analysis.get('requirements', [])
        
        strength_alignment = len(set(strengths) & set(query_requirements)) / max(len(query_requirements), 1)
        score += strength_alignment * 0.3
        
        # Cost efficiency (20% of score)
        cost_per_token = config.get('cost_per_token', 0.0001)
        estimated_tokens = query_analysis.get('estimated_tokens', 1000)
        estimated_cost = cost_per_token * estimated_tokens
        
        if estimated_cost <= self.max_cost_per_query:
            cost_efficiency = 1.0 - (estimated_cost / self.max_cost_per_query)
            score += cost_efficiency * 0.2
        
        # User preferences (10% of score)
        preferred_provider = preferences.get('provider')
        if preferred_provider == provider:
            score += 0.1
        
        return score
    
    async def _get_provider_response(
        self,
        provider: AIProvider,
        query: str,
        context: Optional[str],
        query_type: QueryType
    ) -> AIResponse:
        """
        Get response from specific AI provider
        """
        start_time = time.time()
        
        # Prepare messages
        messages = self._prepare_messages(query, context, query_type)
        
        # Route to appropriate provider
        if provider == AIProvider.GROQ:
            response = await self._get_groq_response(messages)
        elif provider == AIProvider.OPENAI:
            response = await self._get_openai_response(messages)
        elif provider == AIProvider.ANTHROPIC:
            response = await self._get_anthropic_response(messages)
        elif provider == AIProvider.GOOGLE:
            response = await self._get_google_response(messages)
        elif provider == AIProvider.EMERGENT:
            response = await self._get_emergent_response(messages)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        response_time = time.time() - start_time
        
        return AIResponse(
            content=response['content'],
            provider=provider,
            model=response['model'],
            response_time=response_time,
            quality_score=0.0,  # Will be calculated later
            cost=response.get('cost', 0.0),
            metadata=response.get('metadata', {})
        )
    
    async def _get_groq_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Get response from Groq"""
        client = self.providers[AIProvider.GROQ]['client']
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=2048,
            temperature=0.7
        )
        
        return {
            'content': response.choices[0].message.content,
            'model': 'llama-3.3-70b-versatile',
            'cost': self._calculate_cost(response.usage.total_tokens, AIProvider.GROQ)
        }
    
    async def _get_openai_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Get response from OpenAI"""
        client = openai
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=2048,
            temperature=0.7
        )
        
        return {
            'content': response.choices[0].message.content,
            'model': 'gpt-4-turbo',
            'cost': self._calculate_cost(response.usage.total_tokens, AIProvider.OPENAI)
        }
    
    async def _get_anthropic_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Get response from Anthropic"""
        client = self.providers[AIProvider.ANTHROPIC]['client']
        
        # Convert messages format for Anthropic
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                user_messages.append(msg)
        
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-3-5-sonnet-20241022",
            system=system_message,
            messages=user_messages,
            max_tokens=2048
        )
        
        return {
            'content': response.content[0].text,
            'model': 'claude-3-5-sonnet-20241022',
            'cost': self._calculate_cost(response.usage.input_tokens + response.usage.output_tokens, AIProvider.ANTHROPIC)
        }
    
    async def _get_google_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Get response from Google"""
        model = genai.GenerativeModel('gemini-pro')
        
        # Convert messages to prompt
        prompt = self._convert_messages_to_prompt(messages)
        
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2048,
                temperature=0.7
            )
        )
        
        return {
            'content': response.text,
            'model': 'gemini-pro',
            'cost': self._calculate_cost(1000, AIProvider.GOOGLE)  # Estimated
        }
    
    async def _get_emergent_response(self, messages: List[Dict]) -> Dict[str, Any]:
        """Get response from Emergent LLM"""
        # Implementation for Emergent LLM integration
        # This would use the emergent integrations library
        
        prompt = self._convert_messages_to_prompt(messages)
        
        # Placeholder implementation
        return {
            'content': f"Emergent LLM Response for: {prompt[:100]}...",
            'model': 'universal-model',
            'cost': self._calculate_cost(1000, AIProvider.EMERGENT)
        }
    
    def _prepare_messages(
        self,
        query: str,
        context: Optional[str],
        query_type: QueryType
    ) -> List[Dict[str, str]]:
        """Prepare messages for AI providers"""
        messages = []
        
        # System message based on query type
        system_prompts = {
            QueryType.GENERAL: "You are a helpful AI assistant.",
            QueryType.TECHNICAL: "You are a technical expert assistant specializing in providing accurate, detailed technical information.",
            QueryType.CREATIVE: "You are a creative AI assistant that helps with imaginative and artistic tasks.",
            QueryType.ANALYTICAL: "You are an analytical AI assistant that excels at data analysis, reasoning, and logical problem-solving.",
            QueryType.CODE_GENERATION: "You are a programming expert that writes clean, efficient, and well-documented code.",
            QueryType.SUMMARIZATION: "You are a summarization expert that creates concise, accurate summaries.",
            QueryType.TRANSLATION: "You are a translation expert fluent in multiple languages."
        }
        
        messages.append({
            'role': 'system',
            'content': system_prompts.get(query_type, system_prompts[QueryType.GENERAL])
        })
        
        # Add context if provided
        if context:
            messages.append({
                'role': 'user',
                'content': f"Context: {context}\n\nQuery: {query}"
            })
        else:
            messages.append({
                'role': 'user',
                'content': query
            })
        
        return messages
    
    def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert messages to a single prompt string"""
        prompt_parts = []
        for msg in messages:
            if msg['role'] == 'system':
                prompt_parts.append(f"System: {msg['content']}")
            elif msg['role'] == 'user':
                prompt_parts.append(f"User: {msg['content']}")
            elif msg['role'] == 'assistant':
                prompt_parts.append(f"Assistant: {msg['content']}")
        
        return "\n\n".join(prompt_parts)
    
    async def _analyze_query(self, query: str, query_type: QueryType) -> Dict[str, Any]:
        """Analyze query characteristics"""
        return {
            'length': len(query),
            'complexity': 'high' if len(query.split()) > 50 else 'medium' if len(query.split()) > 20 else 'low',
            'estimated_tokens': len(query.split()) * 1.3,  # Rough estimate
            'requirements': self._get_query_requirements(query, query_type),
            'language': 'en',  # Default, could use language detection
            'urgency': 'normal'  # Could be determined by keywords
        }
    
    def _get_query_requirements(self, query: str, query_type: QueryType) -> List[str]:
        """Determine query requirements based on content and type"""
        requirements = []
        
        # Type-based requirements
        if query_type == QueryType.CODE_GENERATION:
            requirements.extend(['code_generation', 'technical'])
        elif query_type == QueryType.ANALYTICAL:
            requirements.extend(['reasoning', 'analysis'])
        elif query_type == QueryType.CREATIVE:
            requirements.extend(['creativity', 'imagination'])
        
        # Content-based requirements
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['fast', 'quick', 'immediately', 'urgent']):
            requirements.append('speed')
        
        if any(word in query_lower for word in ['analyze', 'compare', 'evaluate']):
            requirements.append('analysis')
        
        if any(word in query_lower for word in ['code', 'program', 'function', 'algorithm']):
            requirements.append('code_generation')
        
        if len(query.split()) > 100:
            requirements.append('long_context')
        
        return requirements
    
    def _calculate_cost(self, tokens: int, provider: AIProvider) -> float:
        """Calculate cost for token usage"""
        cost_per_token = self.providers[provider].get('cost_per_token', 0.0001)
        return tokens * cost_per_token
    
    async def _update_provider_metrics(
        self,
        provider: AIProvider,
        response: Optional[AIResponse],
        success: bool
    ):
        """Update performance metrics for a provider"""
        metrics = self.metrics[provider]
        metrics.total_requests += 1
        metrics.last_updated = datetime.now()
        
        if success and response:
            metrics.successful_requests += 1
            
            # Update averages
            if metrics.successful_requests == 1:
                metrics.avg_response_time = response.response_time
                metrics.avg_quality_score = response.quality_score
                metrics.total_cost = response.cost
            else:
                # Running average
                n = metrics.successful_requests
                metrics.avg_response_time = ((n - 1) * metrics.avg_response_time + response.response_time) / n
                metrics.avg_quality_score = ((n - 1) * metrics.avg_quality_score + response.quality_score) / n
                metrics.total_cost += response.cost
        else:
            metrics.failed_requests += 1
    
    def _generate_cache_key(self, query: str, context: Optional[str], query_type: QueryType) -> str:
        """Generate cache key for response"""
        import hashlib
        content = f"{query}|{context or ''}|{query_type.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_response: AIResponse, ttl_minutes: int = 60) -> bool:
        """Check if cached response is still valid"""
        if not hasattr(cached_response, 'timestamp'):
            return False
        
        cache_age = datetime.now() - cached_response.timestamp
        return cache_age < timedelta(minutes=ttl_minutes)
    
    async def _get_fallback_provider(self, failed_provider: AIProvider) -> Optional[AIProvider]:
        """Get fallback provider when primary fails"""
        # Fallback hierarchy
        fallback_map = {
            AIProvider.GROQ: AIProvider.OPENAI,
            AIProvider.OPENAI: AIProvider.ANTHROPIC,
            AIProvider.ANTHROPIC: AIProvider.GOOGLE,
            AIProvider.GOOGLE: AIProvider.GROQ,
            AIProvider.EMERGENT: AIProvider.GROQ
        }
        
        fallback = fallback_map.get(failed_provider)
        if fallback and fallback in self.providers:
            return fallback
        
        # Return any available provider
        available_providers = [p for p in self.providers.keys() if p != failed_provider]
        return available_providers[0] if available_providers else None
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'providers': {},
            'summary': {
                'total_requests': 0,
                'total_successful': 0,
                'total_cost': 0.0,
                'avg_response_time': 0.0
            }
        }
        
        all_response_times = []
        
        for provider, metrics in self.metrics.items():
            if provider in self.providers:  # Only include active providers
                provider_data = {
                    'total_requests': metrics.total_requests,
                    'successful_requests': metrics.successful_requests,
                    'failed_requests': metrics.failed_requests,
                    'success_rate': metrics.successful_requests / max(metrics.total_requests, 1),
                    'avg_response_time': metrics.avg_response_time,
                    'avg_quality_score': metrics.avg_quality_score,
                    'total_cost': metrics.total_cost,
                    'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None
                }
                
                report['providers'][provider.value] = provider_data
                report['summary']['total_requests'] += metrics.total_requests
                report['summary']['total_successful'] += metrics.successful_requests
                report['summary']['total_cost'] += metrics.total_cost
                
                if metrics.successful_requests > 0:
                    all_response_times.append(metrics.avg_response_time)
        
        if all_response_times:
            report['summary']['avg_response_time'] = statistics.mean(all_response_times)
        
        return report


class AIQualityAnalyzer:
    """Analyze AI response quality"""
    
    async def analyze_response(
        self,
        response: str,
        query: str,
        context: Optional[str] = None
    ) -> float:
        """
        Analyze response quality and return score 0.0-1.0
        """
        score = 0.0
        
        # Length appropriateness (20%)
        query_length = len(query.split())
        response_length = len(response.split())
        
        if query_length < 10:  # Short query
            ideal_length = 50
        elif query_length < 50:  # Medium query
            ideal_length = 200
        else:  # Long query
            ideal_length = 500
        
        length_ratio = min(response_length / ideal_length, 1.0)
        score += length_ratio * 0.2
        
        # Relevance keywords (30%)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        relevance = len(query_words & response_words) / max(len(query_words), 1)
        score += relevance * 0.3
        
        # Completeness (25%)
        if '...' not in response and not response.endswith('.'):
            completeness = 0.8
        elif response.endswith('.') or response.endswith('!') or response.endswith('?'):
            completeness = 1.0
        else:
            completeness = 0.6
        
        score += completeness * 0.25
        
        # Structure and clarity (25%)
        sentences = response.split('.')
        if len(sentences) > 1:  # Multiple sentences
            structure_score = 1.0
        elif len(response) > 50:  # Single substantial sentence
            structure_score = 0.8
        else:  # Very short response
            structure_score = 0.5
        
        score += structure_score * 0.25
        
        return min(score, 1.0)


class CostTracker:
    """Track AI usage costs"""
    
    def __init__(self):
        self.daily_costs = {}
        self.monthly_costs = {}
        self.provider_costs = {}
    
    def track_cost(self, provider: AIProvider, cost: float):
        """Track cost for a provider"""
        today = datetime.now().date()
        month = today.replace(day=1)
        
        # Daily costs
        if today not in self.daily_costs:
            self.daily_costs[today] = {}
        if provider not in self.daily_costs[today]:
            self.daily_costs[today][provider] = 0.0
        self.daily_costs[today][provider] += cost
        
        # Monthly costs
        if month not in self.monthly_costs:
            self.monthly_costs[month] = {}
        if provider not in self.monthly_costs[month]:
            self.monthly_costs[month][provider] = 0.0
        self.monthly_costs[month][provider] += cost
        
        # Provider totals
        if provider not in self.provider_costs:
            self.provider_costs[provider] = 0.0
        self.provider_costs[provider] += cost
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        today = datetime.now().date()
        month = today.replace(day=1)
        
        return {
            'today_total': sum(self.daily_costs.get(today, {}).values()),
            'month_total': sum(self.monthly_costs.get(month, {}).values()),
            'provider_totals': {p.value: cost for p, cost in self.provider_costs.items()},
            'daily_costs': {
                str(date): {p.value: cost for p, cost in costs.items()}
                for date, costs in self.daily_costs.items()
            }
        }


# Global instance
multi_ai_orchestrator = None

def get_orchestrator() -> MultiAIOrchestrator:
    """Get global orchestrator instance"""
    global multi_ai_orchestrator
    if multi_ai_orchestrator is None:
        import os
        config = {
            'groq_api_key': os.getenv('GROQ_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
            'google_api_key': os.getenv('GOOGLE_API_KEY'),
            'emergent_llm_key': os.getenv('EMERGENT_LLM_KEY')
        }
        multi_ai_orchestrator = MultiAIOrchestrator(config)
    
    return multi_ai_orchestrator