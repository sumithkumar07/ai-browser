"""
Enhanced AI Intelligence System for AETHER v6.0
Implements Fellou.ai-level proactive AI, behavioral learning, and advanced NLP
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid
from collections import defaultdict, Counter
import re
import numpy as np
from pymongo import MongoClient

logger = logging.getLogger(__name__)

@dataclass
class BehavioralPattern:
    pattern_id: str
    pattern_type: str  # 'command', 'navigation', 'workflow', 'temporal'
    frequency: int
    confidence: float
    last_seen: datetime
    context: Dict[str, Any]
    suggested_automation: Optional[str] = None

@dataclass
class ProactiveSuggestion:
    suggestion_id: str
    suggestion_type: str  # 'automation', 'navigation', 'optimization', 'learning'
    title: str
    description: str
    command: str
    priority: int  # 1-10, 10 being highest
    confidence: float
    context_match: Dict[str, Any]
    expires_at: datetime

@dataclass
class UserContext:
    session_id: str
    current_url: Optional[str]
    recent_commands: List[Dict[str, Any]]
    active_patterns: List[BehavioralPattern]
    user_preferences: Dict[str, Any]
    skill_level: str  # 'beginner', 'intermediate', 'advanced'
    interaction_history: List[Dict[str, Any]]

class EnhancedAIIntelligence:
    """
    Advanced AI system with behavioral learning and proactive capabilities
    Implements Fellou.ai-style intelligence patterns
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.aether_browser
        self.behavioral_patterns = {}
        self.user_contexts = {}
        self.active_learning = True
        
        # Initialize collections
        self.patterns_collection = self.db.behavioral_patterns
        self.suggestions_collection = self.db.proactive_suggestions  
        self.user_contexts_collection = self.db.user_contexts
        self.interaction_logs = self.db.interaction_logs
        
        # Learning parameters
        self.min_pattern_frequency = 3
        self.confidence_threshold = 0.7
        self.suggestion_ttl_hours = 24
        
        logger.info("Enhanced AI Intelligence system initialized successfully")
    
    async def process_user_interaction(self, 
                                    user_session: str,
                                    interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user interaction and update behavioral learning
        """
        try:
            # Update user context
            context = await self.update_user_context(user_session, interaction_data)
            
            # Detect behavioral patterns
            patterns = await self.detect_patterns(context)
            
            # Generate proactive suggestions
            suggestions = await self.generate_proactive_suggestions(context, patterns)
            
            # Log interaction for learning
            await self.log_interaction(user_session, interaction_data)
            
            return {
                "success": True,
                "patterns_detected": len(patterns),
                "suggestions_generated": len(suggestions),
                "context_updated": True,
                "proactive_suggestions": [asdict(s) for s in suggestions[:3]]
            }
            
        except Exception as e:
            logger.error(f"Error processing user interaction: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_user_context(self, 
                                user_session: str, 
                                interaction_data: Dict[str, Any]) -> UserContext:
        """
        Update user context with new interaction data
        """
        # Get existing context or create new
        existing = self.user_contexts_collection.find_one({"session_id": user_session})
        
        if existing:
            context = UserContext(**existing)
        else:
            context = UserContext(
                session_id=user_session,
                current_url=None,
                recent_commands=[],
                active_patterns=[],
                user_preferences={},
                skill_level="intermediate",
                interaction_history=[]
            )
        
        # Update with new data
        if "command" in interaction_data:
            context.recent_commands.append({
                "command": interaction_data["command"],
                "timestamp": datetime.utcnow(),
                "url": interaction_data.get("context", {}).get("url"),
                "success": interaction_data.get("success", True)
            })
            
            # Keep only last 20 commands for pattern detection
            context.recent_commands = context.recent_commands[-20:]
        
        if "url" in interaction_data.get("context", {}):
            context.current_url = interaction_data["context"]["url"]
        
        # Add to interaction history
        context.interaction_history.append({
            "timestamp": datetime.utcnow(),
            "data": interaction_data
        })
        
        # Keep last 100 interactions
        context.interaction_history = context.interaction_history[-100:]
        
        # Update skill level based on command complexity
        await self.update_skill_level(context, interaction_data)
        
        # Store updated context
        self.user_contexts_collection.replace_one(
            {"session_id": user_session},
            asdict(context),
            upsert=True
        )
        
        self.user_contexts[user_session] = context
        return context
    
    async def detect_patterns(self, context: UserContext) -> List[BehavioralPattern]:
        """
        Detect behavioral patterns using advanced analysis
        """
        patterns = []
        
        # Command sequence patterns
        command_patterns = await self.detect_command_patterns(context)
        patterns.extend(command_patterns)
        
        # Temporal patterns (time-based behaviors)
        temporal_patterns = await self.detect_temporal_patterns(context)
        patterns.extend(temporal_patterns)
        
        # Navigation patterns
        navigation_patterns = await self.detect_navigation_patterns(context)
        patterns.extend(navigation_patterns)
        
        # Workflow patterns
        workflow_patterns = await self.detect_workflow_patterns(context)
        patterns.extend(workflow_patterns)
        
        # Store significant patterns
        for pattern in patterns:
            if pattern.confidence >= self.confidence_threshold:
                self.patterns_collection.replace_one(
                    {"pattern_id": pattern.pattern_id},
                    asdict(pattern),
                    upsert=True
                )
        
        return patterns
    
    async def detect_command_patterns(self, context: UserContext) -> List[BehavioralPattern]:
        """
        Detect patterns in command usage
        """
        patterns = []
        commands = [cmd["command"].lower() for cmd in context.recent_commands]
        
        if len(commands) < 3:
            return patterns
        
        # Command frequency analysis
        command_counts = Counter(commands)
        
        for command, frequency in command_counts.items():
            if frequency >= self.min_pattern_frequency:
                confidence = min(frequency / len(commands), 1.0)
                
                pattern = BehavioralPattern(
                    pattern_id=f"cmd_{hash(command)}_{context.session_id}",
                    pattern_type="command",
                    frequency=frequency,
                    confidence=confidence,
                    last_seen=datetime.utcnow(),
                    context={
                        "command": command,
                        "usage_frequency": frequency,
                        "success_rate": self.calculate_command_success_rate(context, command)
                    },
                    suggested_automation=f"Create automation template for '{command}'"
                )
                patterns.append(pattern)
        
        # Command sequence patterns
        sequences = self.extract_command_sequences(commands)
        for sequence, frequency in sequences.items():
            if frequency >= 2:
                confidence = frequency / (len(commands) - len(sequence.split()) + 1)
                
                pattern = BehavioralPattern(
                    pattern_id=f"seq_{hash(sequence)}_{context.session_id}",
                    pattern_type="command_sequence",
                    frequency=frequency,
                    confidence=confidence,
                    last_seen=datetime.utcnow(),
                    context={
                        "sequence": sequence,
                        "frequency": frequency
                    },
                    suggested_automation=f"Create workflow for sequence: {sequence}"
                )
                patterns.append(pattern)
        
        return patterns
    
    async def detect_temporal_patterns(self, context: UserContext) -> List[BehavioralPattern]:
        """
        Detect time-based usage patterns
        """
        patterns = []
        
        # Group interactions by hour of day
        hour_activity = defaultdict(int)
        for interaction in context.interaction_history:
            if isinstance(interaction["timestamp"], datetime):
                hour = interaction["timestamp"].hour
                hour_activity[hour] += 1
        
        # Find peak activity hours
        if hour_activity:
            total_interactions = sum(hour_activity.values())
            for hour, count in hour_activity.items():
                usage_ratio = count / total_interactions
                
                if usage_ratio > 0.2:  # More than 20% of activity in this hour
                    pattern = BehavioralPattern(
                        pattern_id=f"temporal_{hour}_{context.session_id}",
                        pattern_type="temporal",
                        frequency=count,
                        confidence=usage_ratio,
                        last_seen=datetime.utcnow(),
                        context={
                            "peak_hour": hour,
                            "usage_ratio": usage_ratio,
                            "activity_count": count
                        },
                        suggested_automation=f"Schedule automated tasks for {hour}:00"
                    )
                    patterns.append(pattern)
        
        return patterns
    
    async def detect_navigation_patterns(self, context: UserContext) -> List[BehavioralPattern]:
        """
        Detect website navigation patterns
        """
        patterns = []
        
        # Extract domains from recent commands and URLs
        domains = []
        for cmd in context.recent_commands:
            if cmd.get("url"):
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(cmd["url"]).netloc
                    domains.append(domain)
                except:
                    continue
        
        if len(domains) < 2:
            return patterns
        
        domain_counts = Counter(domains)
        
        for domain, frequency in domain_counts.items():
            if frequency >= 2:
                confidence = frequency / len(domains)
                
                pattern = BehavioralPattern(
                    pattern_id=f"nav_{hash(domain)}_{context.session_id}",
                    pattern_type="navigation", 
                    frequency=frequency,
                    confidence=confidence,
                    last_seen=datetime.utcnow(),
                    context={
                        "domain": domain,
                        "visit_frequency": frequency,
                        "domain_type": self.classify_domain(domain)
                    },
                    suggested_automation=f"Create bookmark automation for {domain}"
                )
                patterns.append(pattern)
        
        return patterns
    
    async def detect_workflow_patterns(self, context: UserContext) -> List[BehavioralPattern]:
        """
        Detect complex workflow patterns
        """
        patterns = []
        
        # Analyze command combinations that appear together
        recent_commands = [cmd["command"].lower() for cmd in context.recent_commands[-10:]]
        
        # Look for extract -> process -> export patterns
        workflow_keywords = {
            "data_extraction": ["extract", "scrape", "get data", "collect"],
            "data_processing": ["analyze", "process", "transform", "filter"],
            "data_export": ["export", "save", "download", "send"]
        }
        
        workflow_presence = {}
        for workflow_type, keywords in workflow_keywords.items():
            presence = any(
                any(keyword in cmd for keyword in keywords)
                for cmd in recent_commands
            )
            workflow_presence[workflow_type] = presence
        
        # If multiple workflow stages detected, suggest automation
        active_workflows = [wf for wf, present in workflow_presence.items() if present]
        
        if len(active_workflows) >= 2:
            confidence = len(active_workflows) / len(workflow_keywords)
            
            pattern = BehavioralPattern(
                pattern_id=f"workflow_{hash('_'.join(active_workflows))}_{context.session_id}",
                pattern_type="workflow",
                frequency=len(active_workflows),
                confidence=confidence,
                last_seen=datetime.utcnow(),
                context={
                    "workflow_stages": active_workflows,
                    "complexity": len(active_workflows)
                },
                suggested_automation=f"Create end-to-end automation for {' -> '.join(active_workflows)}"
            )
            patterns.append(pattern)
        
        return patterns
    
    async def generate_proactive_suggestions(self, 
                                          context: UserContext, 
                                          patterns: List[BehavioralPattern]) -> List[ProactiveSuggestion]:
        """
        Generate proactive suggestions based on context and patterns
        """
        suggestions = []
        
        # Context-aware suggestions
        if context.current_url:
            context_suggestions = await self.generate_context_suggestions(context)
            suggestions.extend(context_suggestions)
        
        # Pattern-based suggestions
        for pattern in patterns:
            if pattern.confidence >= self.confidence_threshold:
                pattern_suggestion = await self.generate_pattern_suggestion(pattern, context)
                if pattern_suggestion:
                    suggestions.append(pattern_suggestion)
        
        # Skill-level appropriate suggestions
        skill_suggestions = await self.generate_skill_based_suggestions(context)
        suggestions.extend(skill_suggestions)
        
        # Remove duplicates and sort by priority
        unique_suggestions = {s.suggestion_id: s for s in suggestions}
        sorted_suggestions = sorted(
            unique_suggestions.values(), 
            key=lambda x: (x.priority, x.confidence), 
            reverse=True
        )
        
        # Store suggestions
        for suggestion in sorted_suggestions[:5]:  # Keep top 5
            self.suggestions_collection.replace_one(
                {"suggestion_id": suggestion.suggestion_id},
                asdict(suggestion),
                upsert=True
            )
        
        return sorted_suggestions[:3]  # Return top 3
    
    async def generate_context_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """
        Generate suggestions based on current page context
        """
        suggestions = []
        
        if not context.current_url:
            return suggestions
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(context.current_url)
            domain = parsed.netloc.lower()
            
            # Domain-specific suggestions
            if "linkedin" in domain:
                suggestions.extend([
                    ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        suggestion_type="automation",
                        title="Extract LinkedIn Contacts",
                        description="Extract professional contacts from this LinkedIn page",
                        command="extract linkedin contacts from this page and save to spreadsheet",
                        priority=8,
                        confidence=0.9,
                        context_match={"domain": domain, "type": "professional"},
                        expires_at=datetime.utcnow() + timedelta(hours=2)
                    ),
                    ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        suggestion_type="monitoring",
                        title="Monitor Profile Updates",
                        description="Set up monitoring for profile changes and job updates",
                        command="monitor this linkedin profile for updates and notify me",
                        priority=6,
                        confidence=0.8,
                        context_match={"domain": domain, "type": "monitoring"},
                        expires_at=datetime.utcnow() + timedelta(hours=4)
                    )
                ])
            
            elif "github" in domain:
                suggestions.append(
                    ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        suggestion_type="automation",
                        title="Track Repository Updates",
                        description="Monitor this repository for new releases and issues",
                        command="monitor this github repository for updates and new releases",
                        priority=7,
                        confidence=0.85,
                        context_match={"domain": domain, "type": "development"},
                        expires_at=datetime.utcnow() + timedelta(hours=6)
                    )
                )
            
            elif any(shop in domain for shop in ["amazon", "ebay", "shop", "store"]):
                suggestions.append(
                    ProactiveSuggestion(
                        suggestion_id=str(uuid.uuid4()),
                        suggestion_type="monitoring",
                        title="Price Monitoring",
                        description="Monitor this product for price changes and deals",
                        command="monitor this product for price changes and notify when price drops",
                        priority=9,
                        confidence=0.95,
                        context_match={"domain": domain, "type": "shopping"},
                        expires_at=datetime.utcnow() + timedelta(hours=12)
                    )
                )
        
        except Exception as e:
            logger.error(f"Error generating context suggestions: {e}")
        
        return suggestions
    
    async def generate_pattern_suggestion(self, 
                                        pattern: BehavioralPattern, 
                                        context: UserContext) -> Optional[ProactiveSuggestion]:
        """
        Generate suggestion based on detected pattern
        """
        if not pattern.suggested_automation:
            return None
        
        priority = min(int(pattern.confidence * 10), 10)
        
        return ProactiveSuggestion(
            suggestion_id=str(uuid.uuid4()),
            suggestion_type="optimization",
            title=f"Optimize {pattern.pattern_type.replace('_', ' ').title()}",
            description=pattern.suggested_automation,
            command=pattern.suggested_automation.lower(),
            priority=priority,
            confidence=pattern.confidence,
            context_match={"pattern_type": pattern.pattern_type},
            expires_at=datetime.utcnow() + timedelta(hours=self.suggestion_ttl_hours)
        )
    
    async def generate_skill_based_suggestions(self, context: UserContext) -> List[ProactiveSuggestion]:
        """
        Generate suggestions appropriate for user skill level
        """
        suggestions = []
        
        if context.skill_level == "beginner":
            suggestions.append(
                ProactiveSuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    suggestion_type="learning",
                    title="Learn Voice Commands",
                    description="Try voice commands to speed up your workflow",
                    command="show me voice command tutorial",
                    priority=4,
                    confidence=0.7,
                    context_match={"skill_level": "beginner"},
                    expires_at=datetime.utcnow() + timedelta(days=1)
                )
            )
        
        elif context.skill_level == "advanced":
            suggestions.append(
                ProactiveSuggestion(
                    suggestion_id=str(uuid.uuid4()),
                    suggestion_type="automation",
                    title="Create Custom Workflow",
                    description="Build advanced automation workflows for complex tasks",
                    command="open workflow builder for advanced automation",
                    priority=7,
                    confidence=0.9,
                    context_match={"skill_level": "advanced"},
                    expires_at=datetime.utcnow() + timedelta(hours=6)
                )
            )
        
        return suggestions
    
    # Helper methods
    
    def calculate_command_success_rate(self, context: UserContext, command: str) -> float:
        """Calculate success rate for a specific command"""
        matching_commands = [
            cmd for cmd in context.recent_commands 
            if cmd["command"].lower() == command.lower()
        ]
        
        if not matching_commands:
            return 0.0
        
        successful = sum(1 for cmd in matching_commands if cmd.get("success", True))
        return successful / len(matching_commands)
    
    def extract_command_sequences(self, commands: List[str]) -> Dict[str, int]:
        """Extract common command sequences"""
        sequences = {}
        
        for i in range(len(commands) - 1):
            for j in range(i + 2, min(i + 4, len(commands) + 1)):  # Sequences of 2-3 commands
                sequence = " -> ".join(commands[i:j])
                sequences[sequence] = sequences.get(sequence, 0) + 1
        
        return {seq: count for seq, count in sequences.items() if count >= 2}
    
    def classify_domain(self, domain: str) -> str:
        """Classify domain type for better suggestions"""
        domain = domain.lower()
        
        if any(social in domain for social in ["linkedin", "twitter", "facebook", "instagram"]):
            return "social"
        elif any(dev in domain for dev in ["github", "stackoverflow", "gitlab"]):
            return "development" 
        elif any(shop in domain for shop in ["amazon", "ebay", "shop", "store"]):
            return "shopping"
        elif any(news in domain for news in ["news", "cnn", "bbc", "reuters"]):
            return "news"
        else:
            return "general"
    
    async def update_skill_level(self, context: UserContext, interaction_data: Dict[str, Any]):
        """Update user skill level based on command complexity"""
        command = interaction_data.get("command", "").lower()
        
        # Advanced command indicators
        advanced_keywords = [
            "workflow", "automation", "script", "api", "regex", 
            "xpath", "css selector", "headless", "parallel"
        ]
        
        # Beginner command indicators  
        beginner_keywords = [
            "navigate", "click", "scroll", "basic", "simple", "help"
        ]
        
        if any(keyword in command for keyword in advanced_keywords):
            if context.skill_level != "advanced":
                context.skill_level = "advanced"
        elif any(keyword in command for keyword in beginner_keywords):
            if context.skill_level == "intermediate":
                # Only downgrade if consistently using basic commands
                recent_basic = sum(
                    1 for cmd in context.recent_commands[-5:]
                    if any(kw in cmd["command"].lower() for kw in beginner_keywords)
                )
                if recent_basic >= 4:
                    context.skill_level = "beginner"
    
    async def log_interaction(self, user_session: str, interaction_data: Dict[str, Any]):
        """Log interaction for learning purposes"""
        log_entry = {
            "session_id": user_session,
            "timestamp": datetime.utcnow(),
            "interaction_data": interaction_data,
            "processed_at": datetime.utcnow()
        }
        
        self.interaction_logs.insert_one(log_entry)
    
    async def get_user_insights(self, user_session: str) -> Dict[str, Any]:
        """Get behavioral insights for a user"""
        context = self.user_contexts.get(user_session)
        if not context:
            return {"insights": "No behavioral data available"}
        
        patterns = list(self.patterns_collection.find({"context.session_id": user_session}))
        suggestions = list(self.suggestions_collection.find({"context_match.session_id": user_session}))
        
        return {
            "skill_level": context.skill_level,
            "active_patterns": len(patterns),
            "command_frequency": len(context.recent_commands),
            "suggested_optimizations": len(suggestions),
            "behavioral_insights": {
                "most_used_commands": Counter([cmd["command"] for cmd in context.recent_commands]).most_common(3),
                "peak_activity_pattern": "Analysis in progress...",
                "automation_potential": len([p for p in patterns if p.get("confidence", 0) > 0.8])
            }
        }

def initialize_enhanced_ai_intelligence(mongo_client: MongoClient) -> EnhancedAIIntelligence:
    """Initialize the Enhanced AI Intelligence system"""
    return EnhancedAIIntelligence(mongo_client)