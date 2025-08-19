import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
import hashlib
from collections import defaultdict, deque
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import openai
import anthropic
import groq
import google.generativeai as genai
import os
from dataclasses import dataclass
import aiofiles
import base64
from io import BytesIO
from PIL import Image
import cv2
import time

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    session_id: str
    user_intent: str
    conversation_type: str
    context_score: float
    previous_topics: List[str]
    user_preferences: Dict[str, Any]
    timestamp: datetime

@dataclass
class IntelligentResponse:
    content: str
    confidence_score: float
    response_type: str
    suggested_actions: List[str]
    context_used: Dict[str, Any]
    processing_time: float

class AdvancedAIIntelligenceEngine:
    """
    Advanced AI Intelligence Engine with multi-modal processing, predictive analytics,
    intelligent conversation patterns, and enhanced user behavior analysis.
    """
    
    def __init__(self):
        # AI Clients
        self.groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.openai_client = None
        self.anthropic_client = None
        self.genai_model = None
        
        # Initialize AI providers
        self._initialize_ai_providers()
        
        # Intelligent conversation management
        self.conversation_memory = defaultdict(deque)
        self.user_profiles = defaultdict(dict)
        self.conversation_patterns = {}
        self.intent_classifier = None
        
        # Advanced analytics
        self.conversation_analytics = {
            'total_conversations': 0,
            'average_session_length': 0,
            'common_intents': defaultdict(int),
            'user_satisfaction_scores': deque(maxlen=1000),
            'response_quality_metrics': deque(maxlen=1000)
        }
        
        # Multi-modal processing
        self.image_analysis_cache = {}
        self.content_analysis_cache = {}
        
        # Predictive user behavior
        self.user_behavior_patterns = defaultdict(list)
        self.prediction_models = {}
        
        # Enhanced context management
        self.context_memory = defaultdict(lambda: deque(maxlen=50))
        self.global_context = {
            'trending_topics': deque(maxlen=100),
            'common_questions': defaultdict(int),
            'system_insights': []
        }
        
        # Intelligent response templates
        self.response_templates = self._initialize_response_templates()
        
        # Quality assessment
        self.response_quality_assessor = ResponseQualityAssessor()
        
        logger.info("🧠 Advanced AI Intelligence Engine initialized")
    
    def _initialize_ai_providers(self):
        """Initialize all available AI providers with enhanced configurations"""
        
        # OpenAI
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_key_here":
            self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ OpenAI client initialized")
            
        # Anthropic
        if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_key_here":
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            logger.info("✅ Anthropic client initialized")
        
        # Google Gemini
        if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "your_google_key_here":
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            self.genai_model = genai.GenerativeModel('gemini-pro')
            logger.info("✅ Google Gemini initialized")
    
    def _initialize_response_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize intelligent response templates for different scenarios"""
        return {
            'research': {
                'system_prompt': "You are a research specialist. Provide comprehensive, well-sourced, and analytical responses. Include multiple perspectives and suggest further research directions.",
                'temperature': 0.3,
                'max_tokens': 2000,
                'response_style': 'analytical'
            },
            'creative': {
                'system_prompt': "You are a creative assistant. Be imaginative, innovative, and inspiring. Think outside the box and provide unique solutions and ideas.",
                'temperature': 0.8,
                'max_tokens': 1500,
                'response_style': 'creative'
            },
            'technical': {
                'system_prompt': "You are a technical expert. Provide precise, accurate, and detailed technical information. Include code examples and best practices when relevant.",
                'temperature': 0.2,
                'max_tokens': 2000,
                'response_style': 'technical'
            },
            'conversational': {
                'system_prompt': "You are a helpful conversational assistant. Be friendly, engaging, and personable while providing useful information.",
                'temperature': 0.6,
                'max_tokens': 1000,
                'response_style': 'conversational'
            },
            'problem_solving': {
                'system_prompt': "You are a problem-solving specialist. Break down complex problems, provide step-by-step solutions, and suggest multiple approaches.",
                'temperature': 0.4,
                'max_tokens': 1800,
                'response_style': 'analytical'
            }
        }
    
    async def process_intelligent_conversation(self, message: str, session_id: str,
                                            context: Optional[str] = None,
                                            image_data: Optional[str] = None,
                                            url_context: Optional[str] = None,
                                            user_preferences: Optional[Dict[str, Any]] = None) -> IntelligentResponse:
        """
        Process conversation with advanced intelligence, multi-modal support,
        and predictive user behavior analysis
        """
        start_time = time.time()
        
        try:
            # 1. Analyze user intent and conversation type
            intent_analysis = await self._analyze_conversation_intent(message, session_id)
            
            # 2. Build comprehensive conversation context
            conversation_context = await self._build_conversation_context(
                message, session_id, context, url_context, user_preferences, intent_analysis
            )
            
            # 3. Multi-modal content analysis
            multi_modal_context = await self._process_multi_modal_content(
                message, image_data, url_context
            )
            
            # 4. Predictive user behavior analysis
            behavioral_insights = await self._analyze_user_behavior(session_id, message)
            
            # 5. Generate intelligent response
            response_content = await self._generate_intelligent_response(
                message, conversation_context, multi_modal_context, behavioral_insights, intent_analysis
            )
            
            # 6. Assess response quality
            quality_score = await self.response_quality_assessor.assess_response_quality(
                message, response_content, conversation_context
            )
            
            # 7. Generate suggested actions
            suggested_actions = await self._generate_suggested_actions(
                intent_analysis, conversation_context, response_content
            )
            
            # 8. Update conversation memory and analytics
            await self._update_conversation_memory(
                session_id, message, response_content, intent_analysis, quality_score
            )
            
            processing_time = time.time() - start_time
            
            # Create intelligent response
            intelligent_response = IntelligentResponse(
                content=response_content,
                confidence_score=quality_score,
                response_type=intent_analysis['primary_intent'],
                suggested_actions=suggested_actions,
                context_used={
                    'conversation_context': conversation_context.__dict__,
                    'multi_modal_context': multi_modal_context,
                    'behavioral_insights': behavioral_insights
                },
                processing_time=processing_time
            )
            
            return intelligent_response
            
        except Exception as e:
            logger.error(f"Intelligent conversation processing error: {str(e)}")
            
            # Fallback response
            return IntelligentResponse(
                content="I apologize, but I'm experiencing technical difficulties. Please try rephrasing your question or try again in a moment.",
                confidence_score=0.3,
                response_type="error_fallback",
                suggested_actions=["Try rephrasing your question", "Check your internet connection", "Try again in a few moments"],
                context_used={},
                processing_time=time.time() - start_time
            )
    
    async def _analyze_conversation_intent(self, message: str, session_id: str) -> Dict[str, Any]:
        """Advanced conversation intent analysis with context awareness"""
        
        # Define intent patterns with enhanced matching
        intent_patterns = {
            'question': r'\b(what|when|where|who|how|why|can you|could you|do you|is it|are there)\b',
            'request': r'\b(please|can you|could you|would you|help me|i need|i want)\b',
            'information_seeking': r'\b(tell me|explain|describe|define|what is|how does)\b',
            'problem_solving': r'\b(solve|fix|resolve|issue|problem|error|trouble)\b',
            'creative': r'\b(create|generate|design|make|build|write|compose)\b',
            'analysis': r'\b(analyze|compare|evaluate|assess|review|examine)\b',
            'learning': r'\b(learn|teach|understand|study|tutorial|guide)\b',
            'planning': r'\b(plan|schedule|organize|strategy|approach|method)\b',
            'summarization': r'\b(summarize|summary|brief|overview|tldr|key points)\b'
        }
        
        message_lower = message.lower()
        intent_scores = {}
        
        # Pattern matching with scoring
        for intent, pattern in intent_patterns.items():
            matches = len(re.findall(pattern, message_lower))
            if matches > 0:
                intent_scores[intent] = matches
        
        # Context-based intent enhancement
        if session_id in self.conversation_memory:
            recent_intents = [conv.get('intent', '') for conv in list(self.conversation_memory[session_id])[-5:]]
            for intent in intent_scores:
                if intent in recent_intents:
                    intent_scores[intent] += 0.5  # Boost based on recent context
        
        # Determine primary intent
        primary_intent = 'general'
        intent_confidence = 0.5
        
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            total_score = sum(intent_scores.values())
            intent_confidence = intent_scores[primary_intent] / max(total_score, 1)
        
        return {
            'primary_intent': primary_intent,
            'intent_confidence': min(1.0, intent_confidence),
            'all_intents': intent_scores,
            'conversation_complexity': len(message.split()),
            'question_words': len(re.findall(r'\b(what|when|where|who|how|why)\b', message_lower))
        }
    
    async def _build_conversation_context(self, message: str, session_id: str, 
                                        context: Optional[str], url_context: Optional[str],
                                        user_preferences: Optional[Dict[str, Any]],
                                        intent_analysis: Dict[str, Any]) -> ConversationContext:
        """Build comprehensive conversation context with intelligent analysis"""
        
        # Get conversation history
        conversation_history = list(self.conversation_memory[session_id]) if session_id in self.conversation_memory else []
        
        # Extract previous topics
        previous_topics = []
        if conversation_history:
            for conv in conversation_history[-10:]:  # Last 10 conversations
                if 'topics' in conv:
                    previous_topics.extend(conv['topics'])
        
        # Remove duplicates and limit
        previous_topics = list(dict.fromkeys(previous_topics))[:20]
        
        # User preferences (learning from past interactions)
        if session_id not in self.user_profiles:
            self.user_profiles[session_id] = {
                'preferred_response_length': 'medium',
                'preferred_complexity': 'moderate',
                'common_topics': defaultdict(int),
                'interaction_style': 'conversational',
                'expertise_level': 'intermediate'
            }
        
        # Update user profile based on current interaction
        profile = self.user_profiles[session_id]
        if user_preferences:
            profile.update(user_preferences)
        
        # Determine conversation type based on intent and history
        conversation_type = self._determine_conversation_type(intent_analysis, conversation_history)
        
        # Calculate context score (relevance of available context)
        context_score = self._calculate_context_relevance(message, context, url_context, conversation_history)
        
        return ConversationContext(
            session_id=session_id,
            user_intent=intent_analysis['primary_intent'],
            conversation_type=conversation_type,
            context_score=context_score,
            previous_topics=previous_topics,
            user_preferences=profile,
            timestamp=datetime.utcnow()
        )
    
    def _determine_conversation_type(self, intent_analysis: Dict[str, Any], 
                                   conversation_history: List[Dict[str, Any]]) -> str:
        """Determine the type of conversation for optimal response strategy"""
        
        primary_intent = intent_analysis['primary_intent']
        
        # Single-turn conversation types
        if primary_intent in ['summarization', 'information_seeking']:
            return 'informational'
        elif primary_intent in ['creative', 'problem_solving']:
            return 'collaborative'
        
        # Multi-turn conversation analysis
        if len(conversation_history) > 5:
            recent_intents = [conv.get('intent', '') for conv in conversation_history[-5:]]
            
            if len(set(recent_intents)) == 1:  # Consistent intent
                return 'focused_deep_dive'
            elif 'problem_solving' in recent_intents:
                return 'troubleshooting_session'
            elif 'learning' in recent_intents:
                return 'educational_session'
            else:
                return 'exploratory_conversation'
        
        return 'standard_conversation'
    
    def _calculate_context_relevance(self, message: str, context: Optional[str],
                                   url_context: Optional[str], 
                                   conversation_history: List[Dict[str, Any]]) -> float:
        """Calculate how relevant the available context is to the current message"""
        
        relevance_score = 0.0
        
        # Context from current page/URL
        if context and len(context) > 50:
            # Simple keyword overlap calculation
            message_words = set(message.lower().split())
            context_words = set(context.lower().split())
            overlap = len(message_words.intersection(context_words))
            relevance_score += min(0.4, overlap / max(len(message_words), 1))
        
        # URL context relevance
        if url_context:
            relevance_score += 0.2
        
        # Conversation history relevance
        if conversation_history:
            recent_content = ' '.join([conv.get('message', '') + ' ' + conv.get('response', '') 
                                     for conv in conversation_history[-3:]])
            if recent_content:
                message_words = set(message.lower().split())
                history_words = set(recent_content.lower().split())
                overlap = len(message_words.intersection(history_words))
                relevance_score += min(0.4, overlap / max(len(message_words), 1))
        
        return min(1.0, relevance_score)
    
    async def _process_multi_modal_content(self, message: str, image_data: Optional[str],
                                         url_context: Optional[str]) -> Dict[str, Any]:
        """Process multi-modal content including images and web context"""
        
        multi_modal_context = {
            'has_image': bool(image_data),
            'has_url_context': bool(url_context),
            'image_analysis': None,
            'url_analysis': None,
            'content_type': 'text_only'
        }
        
        # Image analysis
        if image_data:
            try:
                image_analysis = await self._analyze_image_content(image_data)
                multi_modal_context['image_analysis'] = image_analysis
                multi_modal_context['content_type'] = 'text_and_image'
                
            except Exception as e:
                logger.error(f"Image analysis error: {str(e)}")
                multi_modal_context['image_analysis'] = {"error": "Image analysis failed"}
        
        # URL/Web context analysis
        if url_context:
            try:
                url_analysis = await self._analyze_web_content(url_context)
                multi_modal_context['url_analysis'] = url_analysis
                multi_modal_context['content_type'] = 'text_and_web' if not image_data else 'multi_modal'
                
            except Exception as e:
                logger.error(f"URL analysis error: {str(e)}")
                multi_modal_context['url_analysis'] = {"error": "URL analysis failed"}
        
        return multi_modal_context
    
    async def _analyze_image_content(self, image_data: str) -> Dict[str, Any]:
        """Advanced image content analysis"""
        
        # Check cache first
        image_hash = hashlib.md5(image_data.encode()).hexdigest()
        if image_hash in self.image_analysis_cache:
            return self.image_analysis_cache[image_hash]
        
        try:
            # Decode base64 image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            # Basic image properties
            height, width = img_array.shape[:2]
            channels = len(img_array.shape)
            
            # Advanced image analysis using OpenCV
            analysis_result = {
                'dimensions': {'width': width, 'height': height},
                'channels': channels,
                'file_size_estimate': len(image_bytes),
                'analysis_features': {}
            }
            
            # Convert to grayscale for analysis
            if channels == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Calculate image properties
            brightness = np.mean(gray)
            contrast = np.std(gray)
            
            # Edge detection for complexity analysis
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / (height * width)
            
            # Color analysis (if color image)
            if channels == 3:
                # Dominant colors (simplified)
                pixels = img_array.reshape(-1, 3)
                # Simple color dominance
                avg_color = np.mean(pixels, axis=0)
                analysis_result['dominant_color'] = {
                    'r': int(avg_color[0]),
                    'g': int(avg_color[1]),
                    'b': int(avg_color[2])
                }
            
            analysis_result['analysis_features'] = {
                'brightness': float(brightness),
                'contrast': float(contrast),
                'edge_density': float(edge_density),
                'complexity_score': float(edge_density * contrast / 100),
                'image_type': 'photograph' if edge_density > 0.1 else 'graphic'
            }
            
            # Cache the result
            self.image_analysis_cache[image_hash] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            return {'error': f'Image analysis failed: {str(e)}'}
    
    async def _analyze_web_content(self, url_context: str) -> Dict[str, Any]:
        """Advanced web content analysis"""
        
        try:
            # Simple content analysis (can be expanded)
            analysis = {
                'content_length': len(url_context),
                'word_count': len(url_context.split()),
                'sentence_count': len(re.findall(r'[.!?]+', url_context)),
                'paragraph_estimate': url_context.count('\n') + 1,
                'key_topics': []
            }
            
            # Extract key topics using simple keyword frequency
            words = re.findall(r'\b[a-zA-Z]{3,}\b', url_context.lower())
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should'}
            
            word_freq = {}
            for word in words:
                if word not in stop_words and len(word) > 3:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            analysis['key_topics'] = [word for word, freq in top_keywords if freq > 1]
            
            # Content quality assessment
            if analysis['word_count'] > 100:
                analysis['content_quality'] = 'substantial'
            elif analysis['word_count'] > 50:
                analysis['content_quality'] = 'moderate'
            else:
                analysis['content_quality'] = 'brief'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Web content analysis error: {str(e)}")
            return {'error': f'Web content analysis failed: {str(e)}'}
    
    async def _analyze_user_behavior(self, session_id: str, message: str) -> Dict[str, Any]:
        """Analyze user behavior patterns for predictive insights"""
        
        # Record current interaction
        current_time = datetime.utcnow()
        interaction = {
            'timestamp': current_time,
            'message': message,
            'message_length': len(message),
            'complexity': len(message.split()),
            'question_count': len(re.findall(r'\?', message))
        }
        
        self.user_behavior_patterns[session_id].append(interaction)
        
        # Analyze patterns (keep last 50 interactions)
        if len(self.user_behavior_patterns[session_id]) > 50:
            self.user_behavior_patterns[session_id] = self.user_behavior_patterns[session_id][-50:]
        
        # Behavioral analysis
        interactions = self.user_behavior_patterns[session_id]
        
        if len(interactions) < 2:
            return {'pattern_analysis': 'insufficient_data', 'predictions': []}
        
        # Calculate behavioral metrics
        avg_message_length = np.mean([i['message_length'] for i in interactions])
        avg_complexity = np.mean([i['complexity'] for i in interactions])
        total_questions = sum([i['question_count'] for i in interactions])
        
        # Interaction frequency analysis
        if len(interactions) > 1:
            time_diffs = []
            for i in range(1, len(interactions)):
                diff = (interactions[i]['timestamp'] - interactions[i-1]['timestamp']).total_seconds()
                time_diffs.append(diff)
            
            avg_response_time = np.mean(time_diffs) if time_diffs else 0
        else:
            avg_response_time = 0
        
        # Classify user type
        user_type = 'explorer'  # default
        if total_questions > len(interactions) * 0.7:
            user_type = 'questioner'
        elif avg_complexity > 15:
            user_type = 'detailed_communicator'
        elif avg_response_time < 30:
            user_type = 'quick_interactor'
        elif avg_message_length > 200:
            user_type = 'thorough_communicator'
        
        # Generate behavioral predictions
        predictions = []
        if user_type == 'questioner':
            predictions.append('Likely to ask follow-up questions')
        if avg_complexity > 20:
            predictions.append('Prefers detailed explanations')
        if avg_response_time < 60:
            predictions.append('Expects quick responses')
        
        return {
            'user_type': user_type,
            'avg_message_length': avg_message_length,
            'avg_complexity': avg_complexity,
            'interaction_frequency': 1 / max(avg_response_time, 1) * 60,  # interactions per minute
            'question_ratio': total_questions / len(interactions),
            'predictions': predictions,
            'engagement_level': 'high' if len(interactions) > 10 else 'medium' if len(interactions) > 3 else 'low'
        }
    
    async def _generate_intelligent_response(self, message: str, 
                                           conversation_context: ConversationContext,
                                           multi_modal_context: Dict[str, Any],
                                           behavioral_insights: Dict[str, Any],
                                           intent_analysis: Dict[str, Any]) -> str:
        """Generate intelligent response using advanced AI with context awareness"""
        
        # Select response template based on intent
        template_key = intent_analysis['primary_intent']
        if template_key not in self.response_templates:
            template_key = 'conversational'
        
        template = self.response_templates[template_key]
        
        # Build enhanced system prompt
        system_prompt = self._build_enhanced_system_prompt(
            template, conversation_context, behavioral_insights, intent_analysis
        )
        
        # Build context-aware user message
        enhanced_message = self._build_enhanced_user_message(
            message, conversation_context, multi_modal_context
        )
        
        # Generate response using best available AI provider
        response = await self._generate_ai_response(
            system_prompt, enhanced_message, template, conversation_context.session_id
        )
        
        return response
    
    def _build_enhanced_system_prompt(self, template: Dict[str, Any],
                                    conversation_context: ConversationContext,
                                    behavioral_insights: Dict[str, Any],
                                    intent_analysis: Dict[str, Any]) -> str:
        """Build enhanced system prompt with context and behavioral insights"""
        
        base_prompt = template['system_prompt']
        
        # Add behavioral adaptations
        user_type = behavioral_insights.get('user_type', 'explorer')
        engagement_level = behavioral_insights.get('engagement_level', 'medium')
        
        behavioral_adaptations = {
            'questioner': "The user tends to ask many questions. Provide comprehensive answers that anticipate follow-up questions.",
            'detailed_communicator': "The user prefers detailed explanations. Provide thorough, well-structured responses.",
            'quick_interactor': "The user prefers concise, quick responses. Be direct and to-the-point.",
            'thorough_communicator': "The user provides detailed context. Match their communication style with comprehensive responses.",
            'explorer': "The user is exploring topics. Provide informative responses that encourage further exploration."
        }
        
        # Add conversation context
        context_additions = []
        
        if conversation_context.previous_topics:
            context_additions.append(f"Previous topics discussed: {', '.join(conversation_context.previous_topics[:5])}")
        
        if conversation_context.context_score > 0.5:
            context_additions.append("High-quality context is available. Use it to provide relevant, specific answers.")
        
        # Build enhanced prompt
        enhanced_prompt = f"{base_prompt}\n\n"
        
        if user_type in behavioral_adaptations:
            enhanced_prompt += f"User behavior insight: {behavioral_adaptations[user_type]}\n"
        
        if context_additions:
            enhanced_prompt += f"Context information: {' '.join(context_additions)}\n"
        
        enhanced_prompt += f"\nConversation type: {conversation_context.conversation_type}"
        enhanced_prompt += f"\nUser engagement level: {engagement_level}"
        enhanced_prompt += f"\nPrimary intent: {intent_analysis['primary_intent']}"
        
        return enhanced_prompt
    
    def _build_enhanced_user_message(self, message: str,
                                   conversation_context: ConversationContext,
                                   multi_modal_context: Dict[str, Any]) -> str:
        """Build enhanced user message with context integration"""
        
        enhanced_parts = [f"User message: {message}"]
        
        # Add conversation context
        if conversation_context.previous_topics:
            enhanced_parts.append(f"Related topics from conversation: {', '.join(conversation_context.previous_topics[:3])}")
        
        # Add multi-modal context
        if multi_modal_context['has_image'] and multi_modal_context['image_analysis']:
            img_analysis = multi_modal_context['image_analysis']
            if 'analysis_features' in img_analysis:
                features = img_analysis['analysis_features']
                enhanced_parts.append(f"Image context: {img_analysis['dimensions']['width']}x{img_analysis['dimensions']['height']} image with {features.get('image_type', 'unknown')} characteristics")
        
        if multi_modal_context['has_url_context'] and multi_modal_context['url_analysis']:
            url_analysis = multi_modal_context['url_analysis']
            if 'key_topics' in url_analysis and url_analysis['key_topics']:
                enhanced_parts.append(f"Webpage topics: {', '.join(url_analysis['key_topics'][:5])}")
        
        return "\n\n".join(enhanced_parts)
    
    async def _generate_ai_response(self, system_prompt: str, user_message: str,
                                  template: Dict[str, Any], session_id: str) -> str:
        """Generate AI response using the best available provider"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        temperature = template.get('temperature', 0.7)
        max_tokens = template.get('max_tokens', 1500)
        
        # Try providers in order of preference
        providers = ['groq', 'openai', 'anthropic', 'google']
        
        for provider in providers:
            try:
                if provider == 'groq' and self.groq_client:
                    response = self.groq_client.chat.completions.create(
                        messages=messages,
                        model="llama-3.3-70b-versatile",
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
                
                elif provider == 'openai' and self.openai_client:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
                
                elif provider == 'anthropic' and self.anthropic_client:
                    response = self.anthropic_client.messages.create(
                        model="claude-3-haiku-20240307",
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_message}],
                        max_tokens=max_tokens
                    )
                    return response.content[0].text
                
                elif provider == 'google' and self.genai_model:
                    full_prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"
                    response = self.genai_model.generate_content(full_prompt)
                    return response.text
                    
            except Exception as e:
                logger.error(f"AI provider {provider} failed: {str(e)}")
                continue
        
        # Fallback response
        return "I apologize, but I'm experiencing technical difficulties with my AI systems. Please try again in a moment."
    
    async def _generate_suggested_actions(self, intent_analysis: Dict[str, Any],
                                        conversation_context: ConversationContext,
                                        response_content: str) -> List[str]:
        """Generate intelligent suggested actions based on conversation context"""
        
        suggestions = []
        primary_intent = intent_analysis['primary_intent']
        
        # Intent-based suggestions
        if primary_intent == 'question':
            suggestions.extend([
                "Ask a follow-up question",
                "Request more details",
                "Explore related topics"
            ])
        elif primary_intent == 'problem_solving':
            suggestions.extend([
                "Try the suggested solution",
                "Ask for alternative approaches",
                "Request step-by-step guidance"
            ])
        elif primary_intent == 'learning':
            suggestions.extend([
                "Ask for examples",
                "Request practice exercises",
                "Explore advanced concepts"
            ])
        elif primary_intent == 'creative':
            suggestions.extend([
                "Refine the creative output",
                "Generate variations",
                "Explore different approaches"
            ])
        
        # Context-based suggestions
        if conversation_context.previous_topics:
            suggestions.append(f"Revisit previous topic: {conversation_context.previous_topics[0]}")
        
        # Response-based suggestions (simple keyword analysis)
        if 'example' in response_content.lower():
            suggestions.append("Ask for more examples")
        
        if 'step' in response_content.lower():
            suggestions.append("Request detailed steps")
        
        if any(word in response_content.lower() for word in ['however', 'but', 'although']):
            suggestions.append("Explore the alternative perspective")
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    async def _update_conversation_memory(self, session_id: str, message: str,
                                        response_content: str, intent_analysis: Dict[str, Any],
                                        quality_score: float):
        """Update conversation memory and analytics"""
        
        # Update conversation memory
        conversation_record = {
            'message': message,
            'response': response_content,
            'intent': intent_analysis['primary_intent'],
            'quality_score': quality_score,
            'timestamp': datetime.utcnow(),
            'topics': self._extract_topics_from_text(message + ' ' + response_content)
        }
        
        self.conversation_memory[session_id].append(conversation_record)
        
        # Update analytics
        self.conversation_analytics['total_conversations'] += 1
        self.conversation_analytics['common_intents'][intent_analysis['primary_intent']] += 1
        self.conversation_analytics['response_quality_metrics'].append(quality_score)
        
        # Update global context
        topics = conversation_record['topics']
        for topic in topics[:3]:  # Add top 3 topics to trending
            self.global_context['trending_topics'].append(topic)
        
        # Update user profile
        if session_id in self.user_profiles:
            profile = self.user_profiles[session_id]
            for topic in topics:
                profile['common_topics'][topic] += 1
    
    def _extract_topics_from_text(self, text: str) -> List[str]:
        """Extract key topics from text using simple keyword analysis"""
        
        # Simple topic extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stop_words = {'this', 'that', 'these', 'those', 'will', 'would', 'could', 'should', 'might', 'must', 'have', 'been', 'were', 'was', 'are', 'is', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 4]
        
        # Count frequency and return top topics
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top 5 topics
        top_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        return [word for word, freq in top_topics if freq > 1]
    
    def get_intelligence_analytics(self) -> Dict[str, Any]:
        """Get comprehensive intelligence analytics"""
        
        # Calculate average session length
        session_lengths = []
        for session_memory in self.conversation_memory.values():
            session_lengths.append(len(session_memory))
        
        avg_session_length = np.mean(session_lengths) if session_lengths else 0
        
        # Quality metrics
        quality_scores = list(self.conversation_analytics['response_quality_metrics'])
        avg_quality = np.mean(quality_scores) if quality_scores else 0
        
        # Top intents
        top_intents = dict(sorted(self.conversation_analytics['common_intents'].items(), 
                                key=lambda x: x[1], reverse=True)[:10])
        
        # User behavior insights
        user_behavior_summary = {}
        for session_id, behaviors in self.user_behavior_patterns.items():
            if behaviors:
                user_behavior_summary[session_id] = {
                    'interaction_count': len(behaviors),
                    'avg_message_length': np.mean([b['message_length'] for b in behaviors]),
                    'last_interaction': behaviors[-1]['timestamp'].isoformat()
                }
        
        return {
            'total_conversations': self.conversation_analytics['total_conversations'],
            'average_session_length': avg_session_length,
            'average_quality_score': avg_quality,
            'top_intents': top_intents,
            'active_sessions': len(self.conversation_memory),
            'user_behavior_insights': user_behavior_summary,
            'trending_topics': list(self.global_context['trending_topics'])[-20:],  # Last 20 topics
            'cache_performance': {
                'image_cache_size': len(self.image_analysis_cache),
                'content_cache_size': len(self.content_analysis_cache)
            }
        }

class ResponseQualityAssessor:
    """Assess the quality of AI responses using various metrics"""
    
    def __init__(self):
        self.quality_metrics = {
            'relevance': 0.3,
            'completeness': 0.25,
            'clarity': 0.2,
            'accuracy': 0.15,
            'helpfulness': 0.1
        }
    
    async def assess_response_quality(self, user_message: str, response: str,
                                    context: ConversationContext) -> float:
        """Assess response quality using multiple metrics"""
        
        try:
            scores = {}
            
            # Relevance score (keyword overlap)
            scores['relevance'] = self._calculate_relevance(user_message, response)
            
            # Completeness score (response length and structure)
            scores['completeness'] = self._calculate_completeness(response, context.user_intent)
            
            # Clarity score (readability and structure)
            scores['clarity'] = self._calculate_clarity(response)
            
            # Accuracy score (placeholder - would need fact-checking)
            scores['accuracy'] = 0.8  # Assume good accuracy
            
            # Helpfulness score (actionable content)
            scores['helpfulness'] = self._calculate_helpfulness(response, context.user_intent)
            
            # Calculate weighted score
            total_score = sum(scores[metric] * weight 
                            for metric, weight in self.quality_metrics.items())
            
            return min(1.0, total_score)
            
        except Exception as e:
            logger.error(f"Quality assessment error: {str(e)}")
            return 0.7  # Default score
    
    def _calculate_relevance(self, user_message: str, response: str) -> float:
        """Calculate relevance based on keyword overlap"""
        
        user_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', user_message.lower()))
        response_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', response.lower()))
        
        if not user_words:
            return 0.5
        
        overlap = len(user_words.intersection(response_words))
        relevance = overlap / len(user_words)
        
        return min(1.0, relevance * 2)  # Scale up to max 1.0
    
    def _calculate_completeness(self, response: str, intent: str) -> float:
        """Calculate completeness based on response length and structure"""
        
        word_count = len(response.split())
        sentence_count = len(re.findall(r'[.!?]+', response))
        
        # Intent-based expectations
        expected_lengths = {
            'question': 100,
            'problem_solving': 200,
            'learning': 150,
            'creative': 120,
            'analysis': 180
        }
        
        expected_length = expected_lengths.get(intent, 100)
        
        # Score based on meeting expected length
        length_score = min(1.0, word_count / expected_length)
        
        # Bonus for good structure (multiple sentences)
        structure_bonus = min(0.2, sentence_count / 5)
        
        return min(1.0, length_score + structure_bonus)
    
    def _calculate_clarity(self, response: str) -> float:
        """Calculate clarity based on readability and structure"""
        
        words = response.split()
        sentences = len(re.findall(r'[.!?]+', response))
        
        if sentences == 0:
            return 0.3
        
        # Average words per sentence (readability indicator)
        avg_words_per_sentence = len(words) / sentences
        
        # Ideal range: 15-20 words per sentence
        if 15 <= avg_words_per_sentence <= 20:
            readability_score = 1.0
        elif 10 <= avg_words_per_sentence <= 25:
            readability_score = 0.8
        else:
            readability_score = 0.6
        
        # Check for good structure indicators
        structure_indicators = ['first', 'second', 'however', 'therefore', 'finally', 'in conclusion']
        structure_score = min(0.3, sum(0.1 for indicator in structure_indicators if indicator in response.lower()))
        
        return min(1.0, readability_score + structure_score)
    
    def _calculate_helpfulness(self, response: str, intent: str) -> float:
        """Calculate helpfulness based on actionable content"""
        
        # Look for actionable elements
        actionable_indicators = [
            'you can', 'try', 'consider', 'step', 'first', 'next', 'then',
            'example', 'for instance', 'such as', 'here\'s how', 'to do this'
        ]
        
        response_lower = response.lower()
        actionable_count = sum(1 for indicator in actionable_indicators if indicator in response_lower)
        
        # Intent-specific helpfulness
        intent_bonuses = {
            'problem_solving': 0.3 if 'solution' in response_lower or 'solve' in response_lower else 0,
            'learning': 0.3 if 'example' in response_lower or 'learn' in response_lower else 0,
            'question': 0.3 if 'answer' in response_lower or '?' in response else 0
        }
        
        base_score = min(0.7, actionable_count * 0.1)
        intent_bonus = intent_bonuses.get(intent, 0)
        
        return min(1.0, base_score + intent_bonus)

# Global AI intelligence engine instance
ai_intelligence_engine = AdvancedAIIntelligenceEngine()