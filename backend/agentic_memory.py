# 🧠 WORKSTREAM A: AGENTIC MEMORY SYSTEM - Cross-Session Learning & Behavioral Analysis
# Implements sophisticated memory and learning capabilities similar to Fellou.ai's Agentic Memory

import asyncio
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import math
from collections import defaultdict, Counter

# Machine learning imports
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memories in the agentic system"""
    EPISODIC = "episodic"  # What happened (specific events)
    SEMANTIC = "semantic"  # What it means (patterns and knowledge)
    PROCEDURAL = "procedural"  # How to do things (learned procedures)
    WORKING = "working"  # Current context (temporary memory)

class InteractionType(Enum):
    """Types of user interactions"""
    CHAT = "chat"
    COMMAND = "command"
    AUTOMATION = "automation"
    BROWSE = "browse"
    WORKFLOW = "workflow"

@dataclass
class Memory:
    """Base memory structure"""
    memory_id: str
    session_id: str
    memory_type: MemoryType
    content: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime
    importance_score: float = 0.0
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.memory_type, str):
            self.memory_type = MemoryType(self.memory_type)
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

@dataclass
class BehavioralPattern:
    """Represents a learned behavioral pattern"""
    pattern_id: str
    pattern_type: str
    frequency: int
    confidence: float
    contexts: List[Dict[str, Any]]
    learned_actions: List[str]
    success_rate: float
    last_occurrence: datetime

@dataclass
class PredictiveInsight:
    """Represents a prediction about user needs"""
    prediction: str
    confidence: float
    insight_type: str
    reasoning: str
    suggested_actions: List[str]
    expires_at: datetime

class EpisodicMemory:
    """Manages episodic memories - specific events and interactions"""
    
    def __init__(self, db_collection):
        self.db = db_collection
        self.memory_cache = {}
        logger.info("📚 EpisodicMemory initialized")
    
    async def store_episode(self, memory: Memory) -> str:
        """Store an episodic memory"""
        try:
            memory_data = asdict(memory)
            memory_data['memory_type'] = memory.memory_type.value
            memory_data['timestamp'] = memory.timestamp.isoformat()
            
            # Calculate importance score based on content
            importance = await self._calculate_importance(memory)
            memory_data['importance_score'] = importance
            
            # Store in database
            self.db.insert_one(memory_data)
            
            # Cache important memories
            if importance > 0.7:
                self.memory_cache[memory.memory_id] = memory
            
            logger.debug(f"📝 Stored episodic memory {memory.memory_id} with importance {importance:.2f}")
            return memory.memory_id
            
        except Exception as e:
            logger.error(f"Failed to store episodic memory: {e}")
            return None
    
    async def retrieve_episodes(self, session_id: str, limit: int = 20) -> List[Memory]:
        """Retrieve episodic memories for a session"""
        try:
            episodes = list(self.db.find(
                {
                    "session_id": session_id,
                    "memory_type": MemoryType.EPISODIC.value
                },
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit))
            
            memories = []
            for episode_data in episodes:
                memory = Memory(**episode_data)
                memories.append(memory)
                
                # Update access tracking
                await self._update_access(memory.memory_id)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve episodic memories: {e}")
            return []
    
    async def find_similar_episodes(self, current_context: Dict[str, Any], limit: int = 5) -> List[Memory]:
        """Find similar past episodes based on context"""
        try:
            if not ML_AVAILABLE:
                return await self._simple_similarity_search(current_context, limit)
            
            # Get recent memories for analysis
            recent_memories = list(self.db.find(
                {"memory_type": MemoryType.EPISODIC.value},
                {"_id": 0}
            ).sort("timestamp", -1).limit(1000))
            
            if not recent_memories:
                return []
            
            # Create text representations for similarity comparison
            current_text = self._context_to_text(current_context)
            memory_texts = [self._memory_to_text(mem) for mem in recent_memories]
            
            # Use TF-IDF for similarity
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            all_texts = [current_text] + memory_texts
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Get top similar memories
            similar_indices = similarities.argsort()[-limit:][::-1]
            similar_memories = []
            
            for idx in similar_indices:
                if similarities[idx] > 0.1:  # Minimum similarity threshold
                    memory_data = recent_memories[idx]
                    memory = Memory(**memory_data)
                    memory.importance_score = similarities[idx]  # Use similarity as importance
                    similar_memories.append(memory)
            
            return similar_memories
            
        except Exception as e:
            logger.error(f"Failed to find similar episodes: {e}")
            return []
    
    async def _calculate_importance(self, memory: Memory) -> float:
        """Calculate importance score for a memory"""
        importance = 0.0
        content = memory.content
        
        # Base importance factors
        if memory.memory_type == MemoryType.EPISODIC:
            importance += 0.3
        
        # Content-based importance
        if 'error' in content or 'success' in content:
            importance += 0.4 if content.get('success', True) else 0.6
        
        # Interaction complexity
        if 'automation' in str(content).lower():
            importance += 0.3
        if 'workflow' in str(content).lower():
            importance += 0.2
        
        # Recency factor (more recent = more important)
        hours_old = (datetime.utcnow() - memory.timestamp).total_seconds() / 3600
        recency_factor = max(0, 1 - (hours_old / 168))  # Decay over 1 week
        importance += recency_factor * 0.2
        
        return min(1.0, importance)
    
    async def _update_access(self, memory_id: str):
        """Update access tracking for a memory"""
        try:
            self.db.update_one(
                {"memory_id": memory_id},
                {
                    "$inc": {"access_count": 1},
                    "$set": {"last_accessed": datetime.utcnow().isoformat()}
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update access for memory {memory_id}: {e}")
    
    def _context_to_text(self, context: Dict[str, Any]) -> str:
        """Convert context dictionary to text for similarity analysis"""
        text_parts = []
        for key, value in context.items():
            if isinstance(value, str):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, (int, float, bool)):
                text_parts.append(f"{key}: {value}")
        return " ".join(text_parts)
    
    def _memory_to_text(self, memory_data: Dict[str, Any]) -> str:
        """Convert memory to text representation"""
        content = memory_data.get('content', {})
        context = memory_data.get('context', {})
        
        text_parts = []
        text_parts.append(self._context_to_text(content))
        text_parts.append(self._context_to_text(context))
        
        return " ".join(text_parts)
    
    async def _simple_similarity_search(self, current_context: Dict[str, Any], limit: int) -> List[Memory]:
        """Fallback similarity search when ML libraries not available"""
        try:
            # Simple keyword-based search
            keywords = []
            for value in current_context.values():
                if isinstance(value, str):
                    keywords.extend(value.lower().split())
            
            if not keywords:
                return []
            
            # Find memories containing similar keywords
            query = {
                "$or": [
                    {"content": {"$regex": "|".join(keywords), "$options": "i"}},
                    {"context": {"$regex": "|".join(keywords), "$options": "i"}}
                ],
                "memory_type": MemoryType.EPISODIC.value
            }
            
            similar_data = list(self.db.find(query, {"_id": 0}).limit(limit))
            
            return [Memory(**data) for data in similar_data]
            
        except Exception as e:
            logger.error(f"Simple similarity search failed: {e}")
            return []

class SemanticMemory:
    """Manages semantic memories - patterns, concepts, and learned knowledge"""
    
    def __init__(self, db_collection):
        self.db = db_collection
        self.patterns_cache = {}
        logger.info("🧠 SemanticMemory initialized")
    
    async def extract_patterns(self, episodes: List[Memory]) -> List[BehavioralPattern]:
        """Extract behavioral patterns from episodic memories"""
        try:
            if not episodes:
                return []
            
            # Group episodes by similarity
            pattern_groups = await self._group_similar_episodes(episodes)
            
            patterns = []
            for group_id, group_episodes in pattern_groups.items():
                if len(group_episodes) >= 2:  # Minimum frequency for pattern
                    pattern = await self._create_behavioral_pattern(group_episodes)
                    if pattern:
                        patterns.append(pattern)
            
            # Store patterns in database
            for pattern in patterns:
                await self._store_pattern(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Pattern extraction failed: {e}")
            return []
    
    async def get_user_patterns(self, session_id: str) -> List[BehavioralPattern]:
        """Get learned patterns for a user session"""
        try:
            pattern_data = list(self.db.find(
                {"session_id": session_id, "type": "behavioral_pattern"},
                {"_id": 0}
            ))
            
            patterns = []
            for data in pattern_data:
                pattern = BehavioralPattern(**data['pattern'])
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to get user patterns: {e}")
            return []
    
    async def update_pattern_success(self, pattern_id: str, success: bool):
        """Update success rate of a behavioral pattern"""
        try:
            pattern = await self._get_pattern_by_id(pattern_id)
            if pattern:
                # Update success rate using running average
                total_attempts = pattern.frequency
                current_successes = pattern.success_rate * total_attempts
                
                if success:
                    current_successes += 1
                
                new_success_rate = current_successes / (total_attempts + 1)
                
                self.db.update_one(
                    {"pattern.pattern_id": pattern_id},
                    {
                        "$set": {
                            "pattern.success_rate": new_success_rate,
                            "pattern.frequency": total_attempts + 1,
                            "pattern.last_occurrence": datetime.utcnow()
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to update pattern success: {e}")
    
    async def _group_similar_episodes(self, episodes: List[Memory]) -> Dict[str, List[Memory]]:
        """Group similar episodes together for pattern detection"""
        groups = defaultdict(list)
        
        for episode in episodes:
            # Create a signature for the episode
            signature = await self._create_episode_signature(episode)
            groups[signature].append(episode)
        
        return dict(groups)
    
    async def _create_episode_signature(self, episode: Memory) -> str:
        """Create a signature for episode grouping"""
        content = episode.content
        context = episode.context
        
        # Extract key features for grouping
        features = []
        
        # Action type
        if 'action_type' in content:
            features.append(f"action:{content['action_type']}")
        
        # URL pattern
        if 'current_url' in context:
            url = context['current_url']
            if url:
                domain = url.split('/')[2] if '//' in url else url
                features.append(f"domain:{domain}")
        
        # Time of day pattern
        hour = episode.timestamp.hour
        time_period = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        features.append(f"time:{time_period}")
        
        # Interaction type
        if 'type' in content:
            features.append(f"type:{content['type']}")
        
        return "|".join(sorted(features))
    
    async def _create_behavioral_pattern(self, episodes: List[Memory]) -> Optional[BehavioralPattern]:
        """Create a behavioral pattern from grouped episodes"""
        try:
            if len(episodes) < 2:
                return None
            
            # Analyze the episodes to extract pattern
            pattern_type = await self._identify_pattern_type(episodes)
            
            # Calculate pattern statistics
            frequency = len(episodes)
            confidence = min(1.0, frequency / 10.0)  # Confidence increases with frequency
            
            # Extract contexts
            contexts = [episode.context for episode in episodes]
            
            # Extract common actions
            actions = []
            for episode in episodes:
                if 'action_type' in episode.content:
                    actions.append(episode.content['action_type'])
            
            # Calculate success rate
            successes = sum(1 for episode in episodes if episode.content.get('success', True))
            success_rate = successes / len(episodes)
            
            # Get most recent occurrence
            last_occurrence = max(episode.timestamp for episode in episodes)
            
            pattern = BehavioralPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type=pattern_type,
                frequency=frequency,
                confidence=confidence,
                contexts=contexts,
                learned_actions=list(set(actions)),
                success_rate=success_rate,
                last_occurrence=last_occurrence
            )
            
            return pattern
            
        except Exception as e:
            logger.error(f"Failed to create behavioral pattern: {e}")
            return None
    
    async def _identify_pattern_type(self, episodes: List[Memory]) -> str:
        """Identify the type of pattern from episodes"""
        # Analyze common elements across episodes
        action_types = [ep.content.get('action_type', 'unknown') for ep in episodes]
        most_common_action = Counter(action_types).most_common(1)[0][0]
        
        # Identify temporal patterns
        hours = [ep.timestamp.hour for ep in episodes]
        hour_variance = np.var(hours) if ML_AVAILABLE else 0
        
        # Identify contextual patterns
        domains = []
        for ep in episodes:
            url = ep.context.get('current_url', '')
            if url and '//' in url:
                domain = url.split('/')[2]
                domains.append(domain)
        
        common_domain = Counter(domains).most_common(1)[0][0] if domains else None
        
        # Classify pattern type
        if hour_variance < 4 and len(set(hours)) <= 3:
            return f"temporal_{most_common_action}"
        elif common_domain and len(set(domains)) == 1:
            return f"site_specific_{most_common_action}"
        elif most_common_action != 'unknown':
            return f"action_pattern_{most_common_action}"
        else:
            return "general_behavior"
    
    async def _store_pattern(self, pattern: BehavioralPattern):
        """Store a behavioral pattern in the database"""
        try:
            pattern_data = {
                "type": "behavioral_pattern",
                "pattern": asdict(pattern),
                "created_at": datetime.utcnow().isoformat(),
                "session_id": pattern.contexts[0].get('session_id', 'unknown') if pattern.contexts else 'unknown'
            }
            
            # Convert datetime to string for storage
            pattern_data['pattern']['last_occurrence'] = pattern.last_occurrence.isoformat()
            
            self.db.insert_one(pattern_data)
            
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
    
    async def _get_pattern_by_id(self, pattern_id: str) -> Optional[BehavioralPattern]:
        """Retrieve a pattern by ID"""
        try:
            data = self.db.find_one({"pattern.pattern_id": pattern_id, "type": "behavioral_pattern"})
            if data:
                pattern_data = data['pattern']
                pattern_data['last_occurrence'] = datetime.fromisoformat(pattern_data['last_occurrence'])
                return BehavioralPattern(**pattern_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get pattern by ID: {e}")
            return None

class ProceduralMemory:
    """Manages procedural memories - learned procedures and workflows"""
    
    def __init__(self, db_collection):
        self.db = db_collection
        logger.info("⚙️ ProceduralMemory initialized")
    
    async def learn_procedure(self, episodes: List[Memory], procedure_name: str) -> str:
        """Learn a new procedure from a sequence of episodes"""
        try:
            # Extract steps from episodes
            steps = []
            for episode in episodes:
                step = {
                    "action": episode.content.get('action_type', 'unknown'),
                    "parameters": episode.content,
                    "context": episode.context,
                    "timestamp": episode.timestamp.isoformat()
                }
                steps.append(step)
            
            # Create procedure
            procedure = {
                "procedure_id": str(uuid.uuid4()),
                "name": procedure_name,
                "steps": steps,
                "success_rate": 1.0,  # Start optimistic
                "usage_count": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_used": None
            }
            
            # Store procedure
            self.db.insert_one({
                "type": "procedure",
                "procedure": procedure
            })
            
            return procedure["procedure_id"]
            
        except Exception as e:
            logger.error(f"Failed to learn procedure: {e}")
            return None

class WorkingMemory:
    """Manages working memory - current context and active information"""
    
    def __init__(self):
        self.active_contexts = {}
        self.context_timeout = timedelta(hours=1)
        logger.info("🔄 WorkingMemory initialized")
    
    async def set_context(self, session_id: str, context: Dict[str, Any]):
        """Set current context for a session"""
        self.active_contexts[session_id] = {
            "context": context,
            "timestamp": datetime.utcnow(),
            "access_count": 0
        }
    
    async def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current context for a session"""
        if session_id in self.active_contexts:
            ctx = self.active_contexts[session_id]
            
            # Check if context is still valid
            if datetime.utcnow() - ctx["timestamp"] > self.context_timeout:
                del self.active_contexts[session_id]
                return None
            
            # Update access
            ctx["access_count"] += 1
            ctx["last_accessed"] = datetime.utcnow()
            
            return ctx["context"]
        
        return None
    
    async def update_context(self, session_id: str, updates: Dict[str, Any]):
        """Update current context with new information"""
        if session_id in self.active_contexts:
            self.active_contexts[session_id]["context"].update(updates)
            self.active_contexts[session_id]["timestamp"] = datetime.utcnow()

class AgenticMemorySystem:
    """Main Agentic Memory System - orchestrates all memory types"""
    
    def __init__(self, db):
        # Initialize memory subsystems
        self.episodic_memory = EpisodicMemory(db.user_memories)
        self.semantic_memory = SemanticMemory(db.user_memories)
        self.procedural_memory = ProceduralMemory(db.user_memories)
        self.working_memory = WorkingMemory()
        
        # Analytics
        self.interaction_count = 0
        self.learning_sessions = {}
        
        logger.info("🧠 AgenticMemorySystem fully initialized")
    
    async def record_interaction(self, 
                               session_id: str, 
                               interaction_type: str, 
                               content: Dict[str, Any], 
                               context: Dict[str, Any]):
        """Record a new interaction in the memory system"""
        try:
            # Create episodic memory
            memory = Memory(
                memory_id=str(uuid.uuid4()),
                session_id=session_id,
                memory_type=MemoryType.EPISODIC,
                content=content,
                context=context,
                timestamp=datetime.utcnow()
            )
            
            # Store in episodic memory
            await self.episodic_memory.store_episode(memory)
            
            # Update working memory context
            await self.working_memory.set_context(session_id, context)
            
            # Trigger learning if we have enough interactions
            self.interaction_count += 1
            if self.interaction_count % 10 == 0:  # Learn patterns every 10 interactions
                await self._trigger_learning(session_id)
            
            logger.debug(f"🔄 Recorded interaction for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to record interaction: {e}")
    
    async def get_contextual_memory(self, 
                                  session_id: str, 
                                  current_context: Dict[str, Any],
                                  limit: int = 5) -> List[Memory]:
        """Get relevant memories based on current context"""
        try:
            # Get similar episodes
            similar_episodes = await self.episodic_memory.find_similar_episodes(
                current_context, limit
            )
            
            # Sort by relevance (importance score)
            similar_episodes.sort(key=lambda m: m.importance_score, reverse=True)
            
            return similar_episodes
            
        except Exception as e:
            logger.error(f"Failed to get contextual memory: {e}")
            return []
    
    async def predict_user_needs(self, 
                               session_id: str, 
                               current_context: Dict[str, Any]) -> List[PredictiveInsight]:
        """Generate predictive insights about user needs"""
        try:
            insights = []
            
            # Get user's behavioral patterns
            patterns = await self.semantic_memory.get_user_patterns(session_id)
            
            # Get similar past episodes
            similar_episodes = await self.episodic_memory.find_similar_episodes(
                current_context, limit=10
            )
            
            # Generate predictions based on patterns
            for pattern in patterns:
                if pattern.confidence > 0.6 and pattern.success_rate > 0.7:
                    insight = await self._generate_pattern_insight(pattern, current_context)
                    if insight:
                        insights.append(insight)
            
            # Generate predictions based on similar episodes
            if similar_episodes:
                episode_insight = await self._generate_episode_insight(
                    similar_episodes, current_context
                )
                if episode_insight:
                    insights.append(episode_insight)
            
            # Sort by confidence
            insights.sort(key=lambda i: i.confidence, reverse=True)
            
            return insights[:3]  # Return top 3 insights
            
        except Exception as e:
            logger.error(f"Failed to predict user needs: {e}")
            return []
    
    async def _trigger_learning(self, session_id: str):
        """Trigger pattern learning for a session"""
        try:
            # Get recent episodes for pattern learning
            recent_episodes = await self.episodic_memory.retrieve_episodes(
                session_id, limit=50
            )
            
            if len(recent_episodes) >= 5:
                # Extract new patterns
                patterns = await self.semantic_memory.extract_patterns(recent_episodes)
                
                if patterns:
                    logger.info(f"🎯 Learned {len(patterns)} new patterns for session {session_id}")
            
        except Exception as e:
            logger.error(f"Learning trigger failed: {e}")
    
    async def _generate_pattern_insight(self, 
                                      pattern: BehavioralPattern, 
                                      current_context: Dict[str, Any]) -> Optional[PredictiveInsight]:
        """Generate insight based on behavioral pattern"""
        try:
            # Check if current context matches pattern contexts
            context_match = await self._calculate_context_match(pattern.contexts, current_context)
            
            if context_match > 0.5:
                confidence = min(0.95, pattern.confidence * context_match)
                
                # Generate prediction based on pattern
                if pattern.pattern_type.startswith("temporal_"):
                    prediction = f"Based on your pattern, you usually {pattern.learned_actions[0]} around this time"
                elif pattern.pattern_type.startswith("site_specific_"):
                    prediction = f"You typically {pattern.learned_actions[0]} on this site"
                else:
                    prediction = f"You might want to {pattern.learned_actions[0]} next"
                
                return PredictiveInsight(
                    prediction=prediction,
                    confidence=confidence,
                    insight_type="behavioral_pattern",
                    reasoning=f"Based on {pattern.frequency} similar interactions with {pattern.success_rate:.1%} success rate",
                    suggested_actions=pattern.learned_actions,
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate pattern insight: {e}")
            return None
    
    async def _generate_episode_insight(self, 
                                      episodes: List[Memory], 
                                      current_context: Dict[str, Any]) -> Optional[PredictiveInsight]:
        """Generate insight based on similar episodes"""
        try:
            if not episodes:
                return None
            
            # Analyze common outcomes from similar episodes
            successful_actions = []
            for episode in episodes:
                if episode.content.get('success', True):
                    action = episode.content.get('action_type', 'unknown')
                    if action != 'unknown':
                        successful_actions.append(action)
            
            if successful_actions:
                most_common_action = Counter(successful_actions).most_common(1)[0][0]
                success_rate = len(successful_actions) / len(episodes)
                
                confidence = min(0.8, episodes[0].importance_score * success_rate)
                
                return PredictiveInsight(
                    prediction=f"In similar situations, you successfully used '{most_common_action}'",
                    confidence=confidence,
                    insight_type="episode_similarity",
                    reasoning=f"Based on {len(episodes)} similar past interactions",
                    suggested_actions=[most_common_action],
                    expires_at=datetime.utcnow() + timedelta(minutes=30)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate episode insight: {e}")
            return None
    
    async def _calculate_context_match(self, 
                                     pattern_contexts: List[Dict[str, Any]], 
                                     current_context: Dict[str, Any]) -> float:
        """Calculate how well current context matches pattern contexts"""
        try:
            if not pattern_contexts:
                return 0.0
            
            matches = []
            for ctx in pattern_contexts:
                match_score = 0.0
                total_keys = 0
                
                # Compare common keys
                for key in set(ctx.keys()) & set(current_context.keys()):
                    total_keys += 1
                    if ctx[key] == current_context[key]:
                        match_score += 1.0
                    elif isinstance(ctx[key], str) and isinstance(current_context[key], str):
                        # Partial string match
                        if ctx[key].lower() in current_context[key].lower():
                            match_score += 0.5
                
                if total_keys > 0:
                    matches.append(match_score / total_keys)
            
            return max(matches) if matches else 0.0
            
        except Exception as e:
            logger.error(f"Context match calculation failed: {e}")
            return 0.0
    
    async def get_memory_stats(self, session_id: str) -> Dict[str, Any]:
        """Get memory system statistics for a session"""
        try:
            # Count memories by type
            episodic_count = len(await self.episodic_memory.retrieve_episodes(session_id, limit=1000))
            patterns = await self.semantic_memory.get_user_patterns(session_id)
            pattern_count = len(patterns)
            
            # Calculate learning metrics
            total_interactions = self.interaction_count
            avg_pattern_confidence = sum(p.confidence for p in patterns) / len(patterns) if patterns else 0
            
            return {
                "session_id": session_id,
                "episodic_memories": episodic_count,
                "behavioral_patterns": pattern_count,
                "total_interactions": total_interactions,
                "avg_pattern_confidence": round(avg_pattern_confidence, 3),
                "learning_active": True,
                "memory_quality": "high" if avg_pattern_confidence > 0.7 else "medium" if avg_pattern_confidence > 0.4 else "building"
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of the agentic memory system"""
        return {
            "memory_types": ["episodic", "semantic", "procedural", "working"],
            "learning_enabled": True,
            "pattern_recognition": True,
            "predictive_insights": True,
            "cross_session_learning": True,
            "behavioral_analysis": True,
            "context_awareness": True,
            "similarity_matching": ML_AVAILABLE,
            "ml_enhanced": ML_AVAILABLE
        }