"""
AETHER Agentic Memory System - Advanced Multi-Dimensional Memory Architecture
Implements comprehensive memory system from the plan:
- Episodic Memory: What happened (user interactions, workflows)
- Semantic Memory: What it means (patterns, insights, knowledge)
- Procedural Memory: How to do things (learned automation patterns)
- Working Memory: Current context and active information

Features:
- Cross-session learning and pattern recognition
- Predictive user needs analysis
- Adaptive personalization
- Behavioral pattern recognition
- Memory-based workflow optimization
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import hashlib

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING, DESCENDING
import openai
from groq import AsyncGroq


class MemoryType(Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


@dataclass
class UserInteraction:
    """Individual user interaction record"""
    interaction_id: str
    session_id: str
    user_id: str
    timestamp: datetime
    action_type: str  # click, type, navigate, automation, etc.
    target: str  # what was interacted with
    context: Dict[str, Any]  # page URL, element info, etc.
    success: bool
    duration: float  # milliseconds
    metadata: Dict[str, Any]


@dataclass
class BehaviorPattern:
    """Identified behavioral pattern"""
    pattern_id: str
    user_id: str
    pattern_type: str  # workflow, preference, habit, etc.
    description: str
    confidence: float
    frequency: int
    last_seen: datetime
    triggers: List[str]  # what triggers this pattern
    actions: List[str]  # sequence of actions
    success_rate: float
    metadata: Dict[str, Any]


@dataclass
class UserModel:
    """Comprehensive user model"""
    user_id: str
    preferences: Dict[str, Any]
    skill_level: str  # beginner, intermediate, advanced
    common_tasks: List[str]
    behavior_patterns: List[BehaviorPattern]
    efficiency_metrics: Dict[str, float]
    last_updated: datetime
    personalization_data: Dict[str, Any]


@dataclass
class WorkingMemoryItem:
    """Current context item"""
    item_id: str
    content: Any
    relevance_score: float
    last_accessed: datetime
    decay_factor: float = 0.1


class EpisodicMemory:
    """Stores and retrieves what happened - user interactions and events"""
    
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.aether_memory
        self.interactions = self.db.episodic_interactions
        self.sessions = self.db.episodic_sessions
    
    async def initialize(self):
        """Initialize indexes for episodic memory"""
        await self.interactions.create_indexes([
            IndexModel([("user_id", ASCENDING), ("timestamp", DESCENDING)]),
            IndexModel([("session_id", ASCENDING)]),
            IndexModel([("action_type", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)])
        ])
        
        await self.sessions.create_indexes([
            IndexModel([("user_id", ASCENDING), ("start_time", DESCENDING)]),
            IndexModel([("session_id", ASCENDING)])
        ])
    
    async def record_interaction(self, interaction: UserInteraction):
        """Store a user interaction"""
        interaction_data = asdict(interaction)
        interaction_data["timestamp"] = interaction.timestamp.isoformat()
        
        await self.interactions.insert_one(interaction_data)
        
        # Update session summary
        await self._update_session_summary(interaction.session_id, interaction.user_id)
    
    async def get_user_history(self, user_id: str, limit: int = 100, 
                              start_date: Optional[datetime] = None) -> List[UserInteraction]:
        """Get user's interaction history"""
        query = {"user_id": user_id}
        if start_date:
            query["timestamp"] = {"$gte": start_date.isoformat()}
        
        cursor = self.interactions.find(query).sort("timestamp", -1).limit(limit)
        interactions = []
        
        async for doc in cursor:
            doc["timestamp"] = datetime.fromisoformat(doc["timestamp"])
            interactions.append(UserInteraction(**doc))
        
        return interactions
    
    async def get_session_interactions(self, session_id: str) -> List[UserInteraction]:
        """Get all interactions for a specific session"""
        cursor = self.interactions.find({"session_id": session_id}).sort("timestamp", 1)
        interactions = []
        
        async for doc in cursor:
            doc["timestamp"] = datetime.fromisoformat(doc["timestamp"])
            interactions.append(UserInteraction(**doc))
        
        return interactions
    
    async def _update_session_summary(self, session_id: str, user_id: str):
        """Update session summary statistics"""
        session_interactions = await self.get_session_interactions(session_id)
        
        if not session_interactions:
            return
        
        summary = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": session_interactions[0].timestamp.isoformat(),
            "end_time": session_interactions[-1].timestamp.isoformat(),
            "total_interactions": len(session_interactions),
            "success_rate": sum(1 for i in session_interactions if i.success) / len(session_interactions),
            "action_types": list(set(i.action_type for i in session_interactions)),
            "total_duration": sum(i.duration for i in session_interactions),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await self.sessions.update_one(
            {"session_id": session_id},
            {"$set": summary},
            upsert=True
        )


class SemanticMemory:
    """Stores and retrieves what things mean - patterns, insights, knowledge"""
    
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.aether_memory
        self.patterns = self.db.semantic_patterns
        self.insights = self.db.semantic_insights
        self.knowledge = self.db.semantic_knowledge
        
        # AI clients for semantic analysis
        self.groq_client = AsyncGroq(api_key="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")
    
    async def initialize(self):
        """Initialize indexes for semantic memory"""
        await self.patterns.create_indexes([
            IndexModel([("user_id", ASCENDING), ("confidence", DESCENDING)]),
            IndexModel([("pattern_type", ASCENDING)]),
            IndexModel([("last_seen", DESCENDING)])
        ])
        
        await self.insights.create_indexes([
            IndexModel([("user_id", ASCENDING), ("relevance", DESCENDING)]),
            IndexModel([("category", ASCENDING)])
        ])
    
    async def analyze_interaction_patterns(self, user_id: str, interactions: List[UserInteraction]) -> List[BehaviorPattern]:
        """Analyze interactions to identify behavioral patterns"""
        if len(interactions) < 5:  # Need minimum interactions
            return []
        
        patterns = []
        
        # Identify sequential patterns
        sequential_patterns = await self._find_sequential_patterns(interactions)
        patterns.extend(sequential_patterns)
        
        # Identify time-based patterns
        temporal_patterns = await self._find_temporal_patterns(interactions)
        patterns.extend(temporal_patterns)
        
        # Identify context-based patterns
        contextual_patterns = await self._find_contextual_patterns(interactions)
        patterns.extend(contextual_patterns)
        
        # Store patterns in database
        for pattern in patterns:
            await self.store_pattern(pattern)
        
        return patterns
    
    async def _find_sequential_patterns(self, interactions: List[UserInteraction]) -> List[BehaviorPattern]:
        """Find patterns in sequences of actions"""
        patterns = []
        
        # Group interactions by session
        sessions = defaultdict(list)
        for interaction in interactions:
            sessions[interaction.session_id].append(interaction)
        
        # Look for common sequences across sessions
        sequence_counts = defaultdict(int)
        
        for session_interactions in sessions.values():
            if len(session_interactions) < 3:
                continue
            
            # Extract action sequences
            for i in range(len(session_interactions) - 2):
                sequence = tuple(
                    f"{interaction.action_type}:{interaction.target}"
                    for interaction in session_interactions[i:i+3]
                )
                sequence_counts[sequence] += 1
        
        # Create patterns for frequent sequences
        for sequence, count in sequence_counts.items():
            if count >= 3:  # Appeared at least 3 times
                pattern = BehaviorPattern(
                    pattern_id=str(uuid.uuid4()),
                    user_id=interactions[0].user_id,
                    pattern_type="sequential_workflow",
                    description=f"Common sequence: {' → '.join(sequence)}",
                    confidence=min(count / len(sessions), 1.0),
                    frequency=count,
                    last_seen=max(interaction.timestamp for interaction in interactions),
                    triggers=[sequence[0]],
                    actions=list(sequence),
                    success_rate=0.8,  # Will be calculated more precisely later
                    metadata={"sequence_length": len(sequence)}
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _find_temporal_patterns(self, interactions: List[UserInteraction]) -> List[BehaviorPattern]:
        """Find patterns in timing and frequency"""
        patterns = []
        
        # Group by hour of day
        hourly_activity = defaultdict(int)
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hourly_activity[hour] += 1
        
        # Find peak activity hours
        if hourly_activity:
            max_activity = max(hourly_activity.values())
            peak_hours = [hour for hour, count in hourly_activity.items() 
                         if count >= max_activity * 0.7]
            
            if peak_hours:
                pattern = BehaviorPattern(
                    pattern_id=str(uuid.uuid4()),
                    user_id=interactions[0].user_id,
                    pattern_type="temporal_preference",
                    description=f"Most active during hours: {peak_hours}",
                    confidence=0.8,
                    frequency=sum(hourly_activity[h] for h in peak_hours),
                    last_seen=max(interaction.timestamp for interaction in interactions),
                    triggers=["time_based"],
                    actions=["optimize_for_peak_hours"],
                    success_rate=0.9,
                    metadata={"peak_hours": peak_hours, "activity_distribution": dict(hourly_activity)}
                )
                patterns.append(pattern)
        
        return patterns
    
    async def _find_contextual_patterns(self, interactions: List[UserInteraction]) -> List[BehaviorPattern]:
        """Find patterns based on context (URLs, elements, etc.)"""
        patterns = []
        
        # Group by context similarity
        context_patterns = defaultdict(list)
        for interaction in interactions:
            context_key = interaction.context.get("url", "unknown")
            context_patterns[context_key].append(interaction)
        
        # Identify frequently used sites/contexts
        for context, context_interactions in context_patterns.items():
            if len(context_interactions) >= 5:  # Used at least 5 times
                success_rate = sum(1 for i in context_interactions if i.success) / len(context_interactions)
                
                pattern = BehaviorPattern(
                    pattern_id=str(uuid.uuid4()),
                    user_id=interactions[0].user_id,
                    pattern_type="contextual_preference",
                    description=f"Frequent use of: {context}",
                    confidence=min(len(context_interactions) / len(interactions), 1.0),
                    frequency=len(context_interactions),
                    last_seen=max(i.timestamp for i in context_interactions),
                    triggers=[context],
                    actions=["optimize_for_context"],
                    success_rate=success_rate,
                    metadata={"context": context, "interaction_count": len(context_interactions)}
                )
                patterns.append(pattern)
        
        return patterns
    
    async def store_pattern(self, pattern: BehaviorPattern):
        """Store a behavioral pattern"""
        pattern_data = asdict(pattern)
        pattern_data["last_seen"] = pattern.last_seen.isoformat()
        
        await self.patterns.update_one(
            {"pattern_id": pattern.pattern_id},
            {"$set": pattern_data},
            upsert=True
        )
    
    async def get_user_patterns(self, user_id: str, pattern_type: Optional[str] = None) -> List[BehaviorPattern]:
        """Get user's behavioral patterns"""
        query = {"user_id": user_id}
        if pattern_type:
            query["pattern_type"] = pattern_type
        
        cursor = self.patterns.find(query).sort("confidence", -1)
        patterns = []
        
        async for doc in cursor:
            doc["last_seen"] = datetime.fromisoformat(doc["last_seen"])
            patterns.append(BehaviorPattern(**doc))
        
        return patterns
    
    async def generate_insights(self, user_id: str, patterns: List[BehaviorPattern]) -> List[Dict[str, Any]]:
        """Generate AI-powered insights from patterns"""
        if not patterns:
            return []
        
        try:
            # Prepare pattern data for AI analysis
            pattern_descriptions = [
                f"Pattern: {p.description} (Confidence: {p.confidence:.2f}, Frequency: {p.frequency})"
                for p in patterns[:10]  # Top 10 patterns
            ]
            
            completion = await self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI assistant that analyzes user behavior patterns and generates insights for improving productivity and user experience.

Generate actionable insights based on the patterns. Return a JSON array of insights with this structure:
[{
    "insight_id": "unique_id",
    "category": "productivity|efficiency|preferences|habits",
    "title": "Brief insight title",
    "description": "Detailed insight description",
    "actionable_recommendations": ["recommendation1", "recommendation2"],
    "relevance": 0.0-1.0,
    "impact": "high|medium|low"
}]"""
                    },
                    {
                        "role": "user",
                        "content": f"Analyze these user behavior patterns and generate insights:\n\n{chr(10).join(pattern_descriptions)}"
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=1000
            )
            
            insights_text = completion.choices[0].message.content.strip()
            insights = json.loads(insights_text)
            
            # Store insights in database
            for insight in insights:
                insight["user_id"] = user_id
                insight["generated_at"] = datetime.utcnow().isoformat()
                
                await self.insights.update_one(
                    {"insight_id": insight["insight_id"], "user_id": user_id},
                    {"$set": insight},
                    upsert=True
                )
            
            return insights
            
        except Exception as e:
            print(f"Insight generation error: {e}")
            return []


class ProceduralMemory:
    """Stores and retrieves how to do things - learned automation patterns"""
    
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.aether_memory
        self.procedures = self.db.procedural_workflows
        self.automations = self.db.procedural_automations
    
    async def initialize(self):
        """Initialize indexes for procedural memory"""
        await self.procedures.create_indexes([
            IndexModel([("user_id", ASCENDING), ("success_rate", DESCENDING)]),
            IndexModel([("category", ASCENDING)]),
            IndexModel([("last_used", DESCENDING)])
        ])
    
    async def learn_procedure(self, user_id: str, interactions: List[UserInteraction], 
                             procedure_name: str) -> Dict[str, Any]:
        """Learn a new procedure from a sequence of interactions"""
        if len(interactions) < 2:
            return {"success": False, "error": "Need at least 2 interactions"}
        
        # Extract the procedure steps
        steps = []
        for i, interaction in enumerate(interactions):
            step = {
                "step_number": i + 1,
                "action": interaction.action_type,
                "target": interaction.target,
                "context": interaction.context,
                "expected_duration": interaction.duration
            }
            steps.append(step)
        
        # Calculate success rate
        success_rate = sum(1 for i in interactions if i.success) / len(interactions)
        
        procedure = {
            "procedure_id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": procedure_name,
            "category": "learned_workflow",
            "steps": steps,
            "success_rate": success_rate,
            "times_used": 1,
            "last_used": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "total_duration": sum(i.duration for i in interactions),
                "complexity": len(steps)
            }
        }
        
        await self.procedures.insert_one(procedure)
        
        return {
            "success": True,
            "procedure_id": procedure["procedure_id"],
            "steps": len(steps),
            "success_rate": success_rate
        }
    
    async def get_procedures(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user's learned procedures"""
        query = {"user_id": user_id}
        if category:
            query["category"] = category
        
        cursor = self.procedures.find(query).sort("success_rate", -1)
        procedures = []
        async for doc in cursor:
            procedures.append(doc)
        
        return procedures
    
    async def suggest_automation(self, user_id: str, current_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Suggest automation based on current context and learned procedures"""
        # Get user's procedures
        procedures = await self.get_procedures(user_id)
        
        if not procedures:
            return None
        
        # Find procedures that match current context
        relevant_procedures = []
        for procedure in procedures:
            if procedure["success_rate"] > 0.7 and procedure["times_used"] >= 3:
                # Check context similarity
                first_step = procedure["steps"][0] if procedure["steps"] else {}
                if self._context_similarity(current_context, first_step.get("context", {})) > 0.6:
                    relevant_procedures.append(procedure)
        
        if relevant_procedures:
            # Return the most successful and frequently used procedure
            best_procedure = max(relevant_procedures, 
                               key=lambda p: p["success_rate"] * p["times_used"])
            return {
                "suggestion_type": "automation",
                "procedure": best_procedure,
                "confidence": best_procedure["success_rate"],
                "reasoning": f"You've successfully completed this workflow {best_procedure['times_used']} times"
            }
        
        return None
    
    def _context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0
        
        # Simple similarity based on URL and common keys
        url1 = context1.get("url", "")
        url2 = context2.get("url", "")
        
        if url1 and url2:
            # Domain similarity
            try:
                from urllib.parse import urlparse
                domain1 = urlparse(url1).netloc
                domain2 = urlparse(url2).netloc
                if domain1 == domain2:
                    return 1.0
                elif domain1 in domain2 or domain2 in domain1:
                    return 0.8
            except:
                pass
        
        # Check other common keys
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matches = sum(1 for key in common_keys 
                     if str(context1[key]) == str(context2[key]))
        
        return matches / len(common_keys)


class WorkingMemory:
    """Manages current context and active information"""
    
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.items: Dict[str, WorkingMemoryItem] = {}
        self.access_history = deque(maxlen=max_items)
    
    def add_item(self, item_id: str, content: Any, relevance_score: float = 1.0):
        """Add item to working memory"""
        item = WorkingMemoryItem(
            item_id=item_id,
            content=content,
            relevance_score=relevance_score,
            last_accessed=datetime.utcnow()
        )
        
        self.items[item_id] = item
        self.access_history.append(item_id)
        
        # Decay older items and remove if necessary
        self._decay_items()
        self._cleanup_items()
    
    def get_item(self, item_id: str) -> Optional[WorkingMemoryItem]:
        """Get item from working memory"""
        if item_id in self.items:
            item = self.items[item_id]
            item.last_accessed = datetime.utcnow()
            self.access_history.append(item_id)
            return item
        return None
    
    def get_relevant_items(self, context: Dict[str, Any], limit: int = 10) -> List[WorkingMemoryItem]:
        """Get most relevant items for current context"""
        relevant_items = []
        
        for item in self.items.values():
            # Calculate relevance based on recency and initial relevance
            recency_factor = self._calculate_recency_factor(item.last_accessed)
            total_relevance = item.relevance_score * recency_factor
            
            if total_relevance > 0.1:  # Threshold for relevance
                relevant_items.append((item, total_relevance))
        
        # Sort by relevance and return top items
        relevant_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in relevant_items[:limit]]
    
    def _decay_items(self):
        """Apply decay to item relevance scores"""
        current_time = datetime.utcnow()
        
        for item in self.items.values():
            time_diff = (current_time - item.last_accessed).total_seconds()
            decay = item.decay_factor * (time_diff / 3600)  # Decay per hour
            item.relevance_score = max(0.0, item.relevance_score - decay)
    
    def _cleanup_items(self):
        """Remove least relevant items if over capacity"""
        if len(self.items) <= self.max_items:
            return
        
        # Sort by relevance and last access
        items_by_relevance = sorted(
            self.items.items(),
            key=lambda x: (x[1].relevance_score, x[1].last_accessed),
            reverse=True
        )
        
        # Keep only the top items
        keep_items = dict(items_by_relevance[:self.max_items])
        self.items = keep_items
    
    def _calculate_recency_factor(self, last_accessed: datetime) -> float:
        """Calculate recency factor (more recent = higher factor)"""
        time_diff = (datetime.utcnow() - last_accessed).total_seconds()
        # Exponential decay with half-life of 1 hour
        return np.exp(-time_diff / 3600)


class AgenticMemorySystem:
    """Main Agentic Memory System - coordinates all memory types"""
    
    def __init__(self, mongo_url: str = "mongodb://localhost:27017"):
        self.client = AsyncIOMotorClient(mongo_url)
        
        # Initialize memory subsystems
        self.episodic = EpisodicMemory(self.client)
        self.semantic = SemanticMemory(self.client)
        self.procedural = ProceduralMemory(self.client)
        self.working = WorkingMemory()
        
        # User models cache
        self.user_models: Dict[str, UserModel] = {}
    
    async def initialize(self):
        """Initialize all memory subsystems"""
        await self.episodic.initialize()
        await self.semantic.initialize()
        await self.procedural.initialize()
        print("🧠 Agentic Memory System initialized")
    
    async def record_interaction(self, session_id: str, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Record a user interaction across all memory systems"""
        try:
            # Create interaction object
            user_interaction = UserInteraction(
                interaction_id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=interaction.get("user_id", "anonymous"),
                timestamp=datetime.utcnow(),
                action_type=interaction.get("action_type", "unknown"),
                target=interaction.get("target", ""),
                context=interaction.get("context", {}),
                success=interaction.get("success", True),
                duration=interaction.get("duration", 0.0),
                metadata=interaction.get("metadata", {})
            )
            
            # Store in episodic memory
            await self.episodic.record_interaction(user_interaction)
            
            # Add to working memory
            self.working.add_item(
                user_interaction.interaction_id,
                user_interaction,
                relevance_score=1.0
            )
            
            # Trigger pattern analysis if enough interactions
            await self._maybe_analyze_patterns(user_interaction.user_id)
            
            return {
                "success": True,
                "interaction_id": user_interaction.interaction_id,
                "timestamp": user_interaction.timestamp.isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def predict_user_needs(self, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict user needs based on memory and context"""
        try:
            user_id = context.get("user_id", "anonymous")
            
            # Get user patterns
            patterns = await self.semantic.get_user_patterns(user_id)
            
            # Get relevant working memory items
            relevant_items = self.working.get_relevant_items(context, limit=5)
            
            # Get procedural suggestions
            automation_suggestion = await self.procedural.suggest_automation(user_id, context)
            
            predictions = {
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "predictions": []
            }
            
            # Pattern-based predictions
            for pattern in patterns[:3]:  # Top 3 patterns
                if pattern.confidence > 0.7:
                    predictions["predictions"].append({
                        "type": "pattern_based",
                        "description": pattern.description,
                        "confidence": pattern.confidence,
                        "suggested_actions": pattern.actions,
                        "reasoning": f"Based on {pattern.frequency} previous occurrences"
                    })
            
            # Automation suggestion
            if automation_suggestion:
                predictions["predictions"].append({
                    "type": "automation",
                    "description": f"Auto-complete: {automation_suggestion['procedure']['name']}",
                    "confidence": automation_suggestion["confidence"],
                    "procedure": automation_suggestion["procedure"],
                    "reasoning": automation_suggestion["reasoning"]
                })
            
            # Context-based predictions from working memory
            if relevant_items:
                context_predictions = self._generate_context_predictions(relevant_items, context)
                predictions["predictions"].extend(context_predictions)
            
            return predictions
            
        except Exception as e:
            return {
                "session_id": session_id,
                "error": str(e),
                "predictions": []
            }
    
    async def get_user_model(self, user_id: str) -> UserModel:
        """Get or create comprehensive user model"""
        if user_id in self.user_models:
            return self.user_models[user_id]
        
        # Get patterns and interactions
        patterns = await self.semantic.get_user_patterns(user_id)
        recent_interactions = await self.episodic.get_user_history(user_id, limit=100)
        
        # Calculate user metrics
        if recent_interactions:
            success_rate = sum(1 for i in recent_interactions if i.success) / len(recent_interactions)
            avg_duration = sum(i.duration for i in recent_interactions) / len(recent_interactions)
            
            # Determine skill level
            skill_level = "beginner"
            if success_rate > 0.8 and len(recent_interactions) > 50:
                skill_level = "advanced"
            elif success_rate > 0.6 and len(recent_interactions) > 20:
                skill_level = "intermediate"
        else:
            success_rate = 0.0
            avg_duration = 0.0
            skill_level = "beginner"
        
        # Extract common tasks
        common_tasks = []
        if recent_interactions:
            task_counts = defaultdict(int)
            for interaction in recent_interactions:
                task_counts[interaction.action_type] += 1
            
            common_tasks = [task for task, count in 
                          sorted(task_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        user_model = UserModel(
            user_id=user_id,
            preferences={
                "success_rate": success_rate,
                "avg_response_time": avg_duration
            },
            skill_level=skill_level,
            common_tasks=common_tasks,
            behavior_patterns=patterns,
            efficiency_metrics={
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "pattern_count": len(patterns)
            },
            last_updated=datetime.utcnow(),
            personalization_data={}
        )
        
        # Cache the model
        self.user_models[user_id] = user_model
        
        return user_model
    
    async def _maybe_analyze_patterns(self, user_id: str):
        """Analyze patterns if enough new interactions"""
        # Get recent interactions
        recent_interactions = await self.episodic.get_user_history(user_id, limit=50)
        
        # Analyze patterns every 20 interactions
        if len(recent_interactions) % 20 == 0:
            await self.semantic.analyze_interaction_patterns(user_id, recent_interactions)
    
    def _generate_context_predictions(self, relevant_items: List[WorkingMemoryItem], 
                                    context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate predictions based on working memory context"""
        predictions = []
        
        # Analyze recent similar contexts
        for item in relevant_items[:3]:
            if isinstance(item.content, UserInteraction):
                interaction = item.content
                if interaction.success and item.relevance_score > 0.5:
                    predictions.append({
                        "type": "context_based",
                        "description": f"Similar to previous: {interaction.action_type} on {interaction.target}",
                        "confidence": item.relevance_score,
                        "suggested_action": interaction.action_type,
                        "reasoning": f"Based on similar context from {interaction.timestamp.strftime('%Y-%m-%d %H:%M')}"
                    })
        
        return predictions
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        # Episodic stats
        recent_interactions = await self.episodic.get_user_history(user_id, limit=100)
        
        # Semantic stats
        patterns = await self.semantic.get_user_patterns(user_id)
        
        # Procedural stats
        procedures = await self.procedural.get_procedures(user_id)
        
        # Working memory stats
        working_items = len(self.working.items)
        
        return {
            "user_id": user_id,
            "episodic_memory": {
                "total_interactions": len(recent_interactions),
                "success_rate": sum(1 for i in recent_interactions if i.success) / len(recent_interactions) if recent_interactions else 0,
                "avg_duration": sum(i.duration for i in recent_interactions) / len(recent_interactions) if recent_interactions else 0
            },
            "semantic_memory": {
                "identified_patterns": len(patterns),
                "high_confidence_patterns": len([p for p in patterns if p.confidence > 0.8])
            },
            "procedural_memory": {
                "learned_procedures": len(procedures),
                "successful_procedures": len([p for p in procedures if p["success_rate"] > 0.7])
            },
            "working_memory": {
                "active_items": working_items,
                "capacity_used": f"{(working_items / self.working.max_items) * 100:.1f}%"
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global memory system instance
memory_system = AgenticMemorySystem()