<file>
      <absolute_file_name>/app/backend/enhanced_ai_intelligence.py</absolute_file_name>
      <content>"""
Enhanced AI Intelligence Engine - Phase 2 Implementation
Provides behavioral learning, proactive suggestions, and advanced NLP processing
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from pymongo import MongoClient
import groq
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class UserPattern:
    pattern_id: str
    user_session: str
    pattern_type: str  # "navigation", "command", "automation", "time_based"
    strength: float  # 0.0 to 1.0
    frequency: int
    last_occurrence: datetime
    pattern_data: Dict[str, Any]

@dataclass
class ProactiveSuggestion:
    suggestion_id: str
    title: str
    description: str
    confidence: float
    suggested_action: str
    category: str
    trigger_patterns: List[str]

class BehavioralLearningEngine:
    """Learns from user behavior and creates patterns"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.patterns_collection = self.db.user_patterns
        self.interactions_collection = self.db.user_interactions
        
    async def record_interaction(self, user_session: str, interaction_data: Dict[str, Any]):
        """Record user interaction for pattern learning"""
        try:
            interaction = {
                "interaction_id": str(uuid.uuid4()),
                "user_session": user_session,
                "timestamp": datetime.utcnow(),
                "interaction_type": interaction_data.get("type", "unknown"),
                "data": interaction_data,
                "context": {
                    "url": interaction_data.get("current_url"),
                    "time_of_day": datetime.utcnow().hour,
                    "day_of_week": datetime.utcnow().weekday()
                }
            }
            
            self.interactions_collection.insert_one(interaction)
            
            # Analyze for patterns
            await self._analyze_patterns(user_session)
            
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
    
    async def _analyze_patterns(self, user_session: str):
        """Analyze user interactions to identify patterns"""
        try:
            # Get recent interactions (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_interactions = list(
                self.interactions_collection.find({
                    "user_session": user_session,
                    "timestamp": {"$gte": thirty_days_ago}
                })
            )
            
            if len(recent_interactions) < 3:
                return
            
            # Analyze different pattern types
            await self._analyze_navigation_patterns(user_session, recent_interactions)
            await self._analyze_command_patterns(user_session, recent_interactions)
            await self._analyze_time_patterns(user_session, recent_interactions)
            await self._analyze_automation_patterns(user_session, recent_interactions)
            
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
    
    async def _analyze_navigation_patterns(self, user_session: str, interactions: List[Dict]):
        """Analyze navigation patterns"""
        try:
            navigation_interactions = [
                i for i in interactions 
                if i.get("interaction_type") == "navigation"
            ]
            
            if len(navigation_interactions) < 3:
                return
            
            # Find frequently visited domains
            domain_counts = {}
            for interaction in navigation_interactions:
                url = interaction.get("data", {}).get("url", "")
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    except:
                        continue
            
            # Create patterns for frequently visited domains (>= 3 times)
            for domain, count in domain_counts.items():
                if count >= 3:
                    pattern_id = f"nav_{user_session}_{domain}"
                    strength = min(count / 10.0, 1.0)  # Max strength at 10+ visits
                    
                    pattern_data = {
                        "domain": domain,
                        "visit_count": count,
                        "common_times": self._get_common_times(navigation_interactions, domain)
                    }
                    
                    await self._save_pattern(
                        user_session, "navigation", pattern_id, 
                        strength, count, pattern_data
                    )
                    
        except Exception as e:
            logger.error(f"Error analyzing navigation patterns: {e}")
    
    async def _analyze_command_patterns(self, user_session: str, interactions: List[Dict]):
        """Analyze command usage patterns"""
        try:
            command_interactions = [
                i for i in interactions 
                if i.get("interaction_type") in ["chat", "voice_command", "automation"]
            ]
            
            command_counts = {}
            for interaction in command_interactions:
                command = interaction.get("data", {}).get("command", "")
                if command:
                    # Normalize command for pattern recognition
                    normalized = self._normalize_command(command)
                    command_counts[normalized] = command_counts.get(normalized, 0) + 1
            
            # Create patterns for frequent commands
            for command, count in command_counts.items():
                if count >= 2:  # Lower threshold for commands
                    pattern_id = f"cmd_{user_session}_{hash(command) % 10000}"
                    strength = min(count / 5.0, 1.0)
                    
                    pattern_data = {
                        "command_type": command,
                        "usage_count": count,
                        "success_rate": 0.9  # Default high success rate
                    }
                    
                    await self._save_pattern(
                        user_session, "command", pattern_id,
                        strength, count, pattern_data
                    )
                    
        except Exception as e:
            logger.error(f"Error analyzing command patterns: {e}")
    
    async def _analyze_time_patterns(self, user_session: str, interactions: List[Dict]):
        """Analyze time-based usage patterns"""
        try:
            time_usage = {}
            for interaction in interactions:
                hour = interaction.get("context", {}).get("time_of_day", 0)
                time_usage[hour] = time_usage.get(hour, 0) + 1
            
            # Find peak usage hours
            if time_usage:
                max_usage = max(time_usage.values())
                peak_hours = [hour for hour, count in time_usage.items() if count >= max_usage * 0.7]
                
                if peak_hours:
                    pattern_id = f"time_{user_session}_peak"
                    strength = len(peak_hours) / 24.0  # More focused = higher strength
                    
                    pattern_data = {
                        "peak_hours": peak_hours,
                        "total_interactions": sum(time_usage.values()),
                        "usage_distribution": time_usage
                    }
                    
                    await self._save_pattern(
                        user_session, "time_based", pattern_id,
                        strength, len(peak_hours), pattern_data
                    )
                    
        except Exception as e:
            logger.error(f"Error analyzing time patterns: {e}")
    
    async def _analyze_automation_patterns(self, user_session: str, interactions: List[Dict]):
        """Analyze automation usage patterns"""
        try:
            automation_interactions = [
                i for i in interactions 
                if i.get("interaction_type") == "automation"
            ]
            
            if len(automation_interactions) >= 2:
                pattern_id = f"auto_{user_session}_usage"
                strength = min(len(automation_interactions) / 10.0, 1.0)
                
                automation_types = {}
                for interaction in automation_interactions:
                    auto_type = interaction.get("data", {}).get("automation_type", "general")
                    automation_types[auto_type] = automation_types.get(auto_type, 0) + 1
                
                pattern_data = {
                    "automation_usage": len(automation_interactions),
                    "preferred_types": automation_types,
                    "skill_level": "advanced" if len(automation_interactions) > 5 else "intermediate"
                }
                
                await self._save_pattern(
                    user_session, "automation", pattern_id,
                    strength, len(automation_interactions), pattern_data
                )
                
        except Exception as e:
            logger.error(f"Error analyzing automation patterns: {e}")
    
    def _normalize_command(self, command: str) -> str:
        """Normalize command for pattern recognition"""
        command = command.lower().strip()
        
        # Group similar commands
        if any(word in command for word in ["navigate", "go to", "open"]):
            return "navigation"
        elif any(word in command for word in ["summarize", "summary"]):
            return "summarization"
        elif any(word in command for word in ["create", "make", "build"]):
            return "creation"
        elif any(word in command for word in ["search", "find", "look for"]):
            return "search"
        elif any(word in command for word in ["automate", "automation"]):
            return "automation"
        else:
            return "general"
    
    def _get_common_times(self, interactions: List[Dict], domain: str) -> List[int]:
        """Get common times for domain visits"""
        times = []
        for interaction in interactions:
            url = interaction.get("data", {}).get("url", "")
            if domain in url:
                times.append(interaction.get("context", {}).get("time_of_day", 0))
        
        # Return most common times
        time_counts = {}
        for time in times:
            time_counts[time] = time_counts.get(time, 0) + 1
        
        return sorted(time_counts.keys(), key=lambda x: time_counts[x], reverse=True)[:3]
    
    async def _save_pattern(self, user_session: str, pattern_type: str, pattern_id: str, 
                           strength: float, frequency: int, pattern_data: Dict):
        """Save or update a user pattern"""
        try:
            pattern = {
                "pattern_id": pattern_id,
                "user_session": user_session,
                "pattern_type": pattern_type,
                "strength": strength,
                "frequency": frequency,
                "last_occurrence": datetime.utcnow(),
                "pattern_data": pattern_data,
                "updated_at": datetime.utcnow()
            }
            
            self.patterns_collection.replace_one(
                {"pattern_id": pattern_id},
                pattern,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error saving pattern: {e}")
    
    async def get_user_patterns(self, user_session: str) -> List[UserPattern]:
        """Get all patterns for a user"""
        try:
            patterns = list(
                self.patterns_collection.find({
                    "user_session": user_session
                })
            )
            
            return [
                UserPattern(
                    pattern_id=p["pattern_id"],
                    user_session=p["user_session"],
                    pattern_type=p["pattern_type"],
                    strength=p["strength"],
                    frequency=p["frequency"],
                    last_occurrence=p["last_occurrence"],
                    pattern_data=p["pattern_data"]
                )
                for p in patterns
            ]
            
        except Exception as e:
            logger.error(f"Error getting user patterns: {e}")
            return []

class ProactiveAIEngine:
    """Generates proactive suggestions based on patterns"""
    
    def __init__(self, db_client: MongoClient, groq_client):
        self.db = db_client.aether_browser
        self.groq_client = groq_client
        self.learning_engine = BehavioralLearningEngine(db_client)
        self.suggestions_collection = self.db.proactive_suggestions
        
    async def generate_proactive_suggestions(self, user_session: str, context: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Generate context-aware proactive suggestions"""
        try:
            patterns = await self.learning_engine.get_user_patterns(user_session)
            current_url = context.get("current_url")
            current_time = datetime.utcnow().hour
            
            suggestions = []
            
            # Time-based suggestions
            suggestions.extend(await self._generate_time_based_suggestions(patterns, current_time))
            
            # Navigation-based suggestions
            if current_url:
                suggestions.extend(await self._generate_navigation_suggestions(patterns, current_url))
            
            # Pattern-based suggestions
            suggestions.extend(await self._generate_pattern_suggestions(patterns, context))
            
            # AI-generated contextual suggestions
            ai_suggestions = await self._generate_ai_suggestions(user_session, context, patterns)
            suggestions.extend(ai_suggestions)
            
            # Rank and filter suggestions
            ranked_suggestions = self._rank_suggestions(suggestions, patterns)
            
            return ranked_suggestions[:5]  # Top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestions: {e}")
            return []
    
    async def _generate_time_based_suggestions(self, patterns: List[UserPattern], current_time: int) -> List[ProactiveSuggestion]:
        """Generate suggestions based on time patterns"""
        suggestions = []
        
        time_patterns = [p for p in patterns if p.pattern_type == "time_based"]
        for pattern in time_patterns:
            peak_hours = pattern.pattern_data.get("peak_hours", [])
            
            if current_time in peak_hours:
                if 9 <= current_time <= 11:  # Morning
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        title="Morning Productivity Boost",
                        description="Based on your patterns, you're most productive now. Ready to tackle some tasks?",
                        confidence=pattern.strength,
                        suggested_action="show_productivity_tools",
                        category="time_optimization",
                        trigger_patterns=[pattern.pattern_id]
                    ))
                elif 14 <= current_time <= 16:  # Afternoon
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        title="Afternoon Focus Session",
                        description="Perfect time for deep work based on your usage patterns.",
                        confidence=pattern.strength,
                        suggested_action="create_focus_environment",
                        category="time_optimization",
                        trigger_patterns=[pattern.pattern_id]
                    ))
        
        return suggestions
    
    async def _generate_navigation_suggestions(self, patterns: List[UserPattern], current_url: str) -> List[ProactiveSuggestion]:
        """Generate suggestions based on navigation patterns"""
        suggestions = []
        
        try:
            from urllib.parse import urlparse
            current_domain = urlparse(current_url).netloc
            
            nav_patterns = [p for p in patterns if p.pattern_type == "navigation"]
            for pattern in nav_patterns:
                pattern_domain = pattern.pattern_data.get("domain", "")
                
                if pattern_domain == current_domain and pattern.strength > 0.3:
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        title="Optimize Your Workflow",
                        description=f"You visit {pattern_domain} frequently. Want me to create shortcuts?",
                        confidence=pattern.strength,
                        suggested_action=f"create_shortcuts_{pattern_domain}",
                        category="workflow_optimization",
                        trigger_patterns=[pattern.pattern_id]
                    ))
        except:
            pass
        
        return suggestions
    
    async def _generate_pattern_suggestions(self, patterns: List[UserPattern], context: Dict[str, Any]) -> List[ProactiveSuggestion]:
        """Generate suggestions based on user patterns"""
        suggestions = []
        
        # Automation patterns
        automation_patterns = [p for p in patterns if p.pattern_type == "automation"]
        for pattern in automation_patterns:
            if pattern.strength > 0.4:
                skill_level = pattern.pattern_data.get("skill_level", "intermediate")
                
                if skill_level == "advanced":
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        title="Advanced Automation Available",
                        description="Ready for complex multi-step automations?",
                        confidence=pattern.strength,
                        suggested_action="show_advanced_automation",
                        category="automation_enhancement",
                        trigger_patterns=[pattern.pattern_id]
                    ))
        
        # Command patterns
        command_patterns = [p for p in patterns if p.pattern_type == "command"]
        for pattern in command_patterns:
            if pattern.strength > 0.5:
                suggestions.append(ProactiveSuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    title="Smart Command Shortcuts",
                    description="I can create voice shortcuts for your frequent commands.",
                    confidence=pattern.strength,
                    suggested_action="create_voice_shortcuts",
                    category="efficiency_enhancement",
                    trigger_patterns=[pattern.pattern_id]
                ))
        
        return suggestions
    
    async def _generate_ai_suggestions(self, user_session: str, context: Dict[str, Any], patterns: List[UserPattern]) -> List[ProactiveSuggestion]:
        """Generate AI-powered contextual suggestions"""
        suggestions = []
        
        try:
            current_url = context.get("current_url", "")
            if not current_url:
                return suggestions
            
            # Create context for AI
            pattern_summary = {
                "navigation_patterns": len([p for p in patterns if p.pattern_type == "navigation"]),
                "automation_usage": len([p for p in patterns if p.pattern_type == "automation"]),
                "command_patterns": len([p for p in patterns if p.pattern_type == "command"]),
                "peak_usage_identified": len([p for p in patterns if p.pattern_type == "time_based"]) > 0
            }
            
            prompt = f"""
            Based on the user's browsing patterns and current context, generate 2 proactive suggestions.
            
            Current URL: {current_url}
            User Patterns: {json.dumps(pattern_summary, indent=2)}
            
            Provide suggestions in JSON format:
            [
                {{
                    "title": "Brief title",
                    "description": "Helpful description",
                    "action": "suggested_action_code",
                    "confidence": 0.8
                }}
            ]
            
            Focus on practical, actionable suggestions that help with productivity, automation, or efficiency.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response
            try:
                ai_suggestions_data = json.loads(ai_response)
                for suggestion_data in ai_suggestions_data[:2]:  # Max 2 AI suggestions
                    suggestions.append(ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        title=suggestion_data.get("title", "AI Suggestion"),
                        description=suggestion_data.get("description", "AI-generated suggestion"),
                        confidence=suggestion_data.get("confidence", 0.7),
                        suggested_action=suggestion_data.get("action", "ai_suggestion"),
                        category="ai_generated",
                        trigger_patterns=["ai_context"]
                    ))
            except json.JSONDecodeError:
                pass
                
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
        
        return suggestions
    
    def _rank_suggestions(self, suggestions: List[ProactiveSuggestion], patterns: List[UserPattern]) -> List[ProactiveSuggestion]:
        """Rank suggestions by relevance and confidence"""
        def calculate_score(suggestion: ProactiveSuggestion) -> float:
            base_score = suggestion.confidence
            
            # Boost score based on pattern strength
            pattern_boost = 0
            for pattern_id in suggestion.trigger_patterns:
                pattern = next((p for p in patterns if p.pattern_id == pattern_id), None)
                if pattern:
                    pattern_boost += pattern.strength * 0.2
            
            return base_score + pattern_boost
        
        # Sort by score descending
        ranked = sorted(suggestions, key=calculate_score, reverse=True)
        
        # Remove duplicates by category (keep highest scoring)
        seen_categories = set()
        unique_suggestions = []
        
        for suggestion in ranked:
            if suggestion.category not in seen_categories:
                unique_suggestions.append(suggestion)
                seen_categories.add(suggestion.category)
        
        return unique_suggestions

class AdvancedNLPProcessor:
    """Advanced natural language processing for complex commands"""
    
    def __init__(self, groq_client):
        self.groq_client = groq_client
        
    async def parse_complex_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse complex multi-step commands"""
        try:
            prompt = f"""
            Parse this command into actionable steps:
            
            Command: "{command}"
            Context: {json.dumps(context, default=str, indent=2)}
            
            Provide a detailed breakdown in JSON format:
            {{
                "intent": "primary_intent",
                "complexity": "simple|medium|complex",
                "steps": [
                    {{
                        "step": 1,
                        "action": "action_type",
                        "description": "what to do",
                        "parameters": {{"key": "value"}},
                        "estimated_time": "time_estimate"
                    }}
                ],
                "requires_confirmation": true|false,
                "background_suitable": true|false,
                "success_probability": 0.0-1.0
            }}
            
            Focus on practical, executable steps.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=800
            )
            
            parsed_response = response.choices[0].message.content.strip()
            
            try:
                return json.loads(parsed_response)
            except json.JSONDecodeError:
                return {
                    "intent": "general",
                    "complexity": "simple",
                    "steps": [{"step": 1, "action": "chat_response", "description": command}],
                    "requires_confirmation": False,
                    "background_suitable": True,
                    "success_probability": 0.8
                }
                
        except Exception as e:
            logger.error(f"Error parsing complex command: {e}")
            return {
                "intent": "error",
                "complexity": "simple",
                "steps": [],
                "requires_confirmation": False,
                "background_suitable": False,
                "success_probability": 0.0
            }
    
    async def generate_follow_up_suggestions(self, command: str, result: Dict[str, Any]) -> List[str]:
        """Generate follow-up suggestions based on command results"""
        try:
            prompt = f"""
            Based on this command and its result, suggest 3 helpful follow-up actions:
            
            Original Command: "{command}"
            Result Success: {result.get('success', False)}
            
            Provide 3 short, actionable follow-up suggestions as a JSON array:
            ["suggestion 1", "suggestion 2", "suggestion 3"]
            
            Focus on logical next steps that add value.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=300
            )
            
            suggestions_text = response.choices[0].message.content.strip()
            
            try:
                return json.loads(suggestions_text)
            except json.JSONDecodeError:
                return ["Continue with related tasks", "Save this result", "Share or export data"]
                
        except Exception as e:
            logger.error(f"Error generating follow-up suggestions: {e}")
            return []

def initialize_enhanced_ai_intelligence(db_client: MongoClient) -> Dict[str, Any]:
    """Initialize the enhanced AI intelligence system"""
    try:
        groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        learning_engine = BehavioralLearningEngine(db_client)
        proactive_engine = ProactiveAIEngine(db_client, groq_client)
        nlp_processor = AdvancedNLPProcessor(groq_client)
        
        logger.info("✅ Enhanced AI Intelligence initialized successfully")
        
        return {
            "learning_engine": learning_engine,
            "proactive_engine": proactive_engine,
            "nlp_processor": nlp_processor,
            "initialized": True
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced AI intelligence: {e}")
        return {
            "learning_engine": None,
            "proactive_engine": None,
            "nlp_processor": None,
            "initialized": False,
            "error": str(e)
        }
</content>
    </file>