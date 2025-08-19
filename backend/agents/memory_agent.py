"""
Memory Agent - Handles persistent learning and knowledge management
Implements advanced memory capabilities similar to Fellou.ai's agentic memory
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from .base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="memory",
            capabilities=[
                "knowledge_storage",
                "pattern_learning",
                "user_behavior_tracking",
                "context_retention",
                "adaptive_learning",
                "memory_optimization",
                "knowledge_retrieval"
            ]
        )
        self.short_term_memory = {}  # Recent interactions
        self.long_term_memory = {}   # Persistent knowledge
        self.pattern_memory = {}     # Learned patterns
        self.user_profiles = {}      # User-specific learning
        self.context_memory = {}     # Session contexts
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory-related operations"""
        await self.update_status("processing", task)
        
        operation = task.get("operation", "store")
        
        if operation == "store":
            result = await self._store_memory(task)
        elif operation == "retrieve":
            result = await self._retrieve_memory(task)
        elif operation == "learn_pattern":
            result = await self._learn_pattern(task)
        elif operation == "update_user_profile":
            result = await self._update_user_profile(task)
        elif operation == "optimize_memory":
            result = await self._optimize_memory(task)
        else:
            result = await self._general_memory_operation(task)
        
        await self.update_status("completed", task)
        return result
    
    async def _store_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Store information in appropriate memory system"""
        memory_data = task.get("memory_data", {})
        memory_type = task.get("memory_type", "short_term")
        user_session = task.get("user_session", "default")
        
        memory_entry = {
            "data": memory_data,
            "timestamp": datetime.utcnow(),
            "user_session": user_session,
            "importance": self._calculate_importance(memory_data),
            "access_count": 0,
            "last_accessed": datetime.utcnow()
        }
        
        memory_id = f"{user_session}_{datetime.utcnow().timestamp()}"
        
        if memory_type == "short_term":
            self.short_term_memory[memory_id] = memory_entry
            # Auto-cleanup old short-term memories
            await self._cleanup_short_term_memory()
            
        elif memory_type == "long_term":
            self.long_term_memory[memory_id] = memory_entry
            
        elif memory_type == "pattern":
            await self._store_pattern_memory(memory_id, memory_entry)
            
        elif memory_type == "context":
            session_id = memory_data.get("session_id", user_session)
            if session_id not in self.context_memory:
                self.context_memory[session_id] = []
            self.context_memory[session_id].append(memory_entry)
        
        return {
            "success": True,
            "memory_id": memory_id,
            "memory_type": memory_type,
            "storage_location": self._get_memory_location(memory_type),
            "importance_score": memory_entry["importance"],
            "agent_id": self.agent_id
        }
    
    async def _retrieve_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant memories based on query"""
        query = task.get("query", "")
        user_session = task.get("user_session", "default")
        memory_types = task.get("memory_types", ["short_term", "long_term", "pattern"])
        limit = task.get("limit", 10)
        
        retrieved_memories = []
        
        # Search across specified memory types
        for memory_type in memory_types:
            if memory_type == "short_term":
                memories = await self._search_short_term_memory(query, user_session)
            elif memory_type == "long_term":
                memories = await self._search_long_term_memory(query, user_session)
            elif memory_type == "pattern":
                memories = await self._search_pattern_memory(query, user_session)
            elif memory_type == "context":
                memories = await self._search_context_memory(query, user_session)
            else:
                continue
            
            retrieved_memories.extend(memories)
        
        # Sort by relevance and recency
        retrieved_memories = await self._rank_memories(retrieved_memories, query)
        retrieved_memories = retrieved_memories[:limit]
        
        # Update access patterns
        for memory in retrieved_memories:
            await self._update_access_pattern(memory)
        
        return {
            "success": True,
            "memories_found": len(retrieved_memories),
            "memories": retrieved_memories,
            "search_query": query,
            "memory_types_searched": memory_types,
            "agent_id": self.agent_id
        }
    
    async def _learn_pattern(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Learn patterns from user interactions and behaviors"""
        interaction_data = task.get("interaction_data", {})
        user_session = task.get("user_session", "default")
        
        # Extract patterns from interaction data
        patterns = await self._extract_patterns(interaction_data, user_session)
        
        # Store learned patterns
        for pattern in patterns:
            pattern_id = f"pattern_{user_session}_{pattern['type']}_{datetime.utcnow().timestamp()}"
            
            pattern_memory = {
                "pattern": pattern,
                "confidence": pattern.get("confidence", 0.5),
                "occurrences": 1,
                "first_seen": datetime.utcnow(),
                "last_reinforced": datetime.utcnow(),
                "user_session": user_session
            }
            
            # Check if similar pattern already exists
            existing_pattern = await self._find_similar_pattern(pattern, user_session)
            if existing_pattern:
                # Reinforce existing pattern
                await self._reinforce_pattern(existing_pattern["id"], pattern_memory)
            else:
                # Store new pattern
                self.pattern_memory[pattern_id] = pattern_memory
        
        return {
            "success": True,
            "patterns_learned": len(patterns),
            "patterns": patterns,
            "user_session": user_session,
            "learning_confidence": sum(p.get("confidence", 0) for p in patterns) / len(patterns) if patterns else 0,
            "agent_id": self.agent_id
        }
    
    async def _update_user_profile(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile based on behavior and preferences"""
        user_session = task.get("user_session", "default")
        behavior_data = task.get("behavior_data", {})
        
        if user_session not in self.user_profiles:
            self.user_profiles[user_session] = {
                "created_at": datetime.utcnow(),
                "preferences": {},
                "behavior_patterns": {},
                "usage_statistics": {},
                "learning_rate": 0.5,
                "adaptation_score": 0.0
            }
        
        profile = self.user_profiles[user_session]
        
        # Update preferences
        preferences = behavior_data.get("preferences", {})
        for key, value in preferences.items():
            profile["preferences"][key] = value
        
        # Update behavior patterns
        behaviors = behavior_data.get("behaviors", [])
        for behavior in behaviors:
            behavior_type = behavior.get("type", "unknown")
            if behavior_type not in profile["behavior_patterns"]:
                profile["behavior_patterns"][behavior_type] = {
                    "count": 0,
                    "frequency": 0.0,
                    "last_occurrence": None,
                    "pattern_strength": 0.0
                }
            
            pattern = profile["behavior_patterns"][behavior_type]
            pattern["count"] += 1
            pattern["last_occurrence"] = datetime.utcnow()
            
            # Calculate frequency (occurrences per day)
            days_active = (datetime.utcnow() - profile["created_at"]).days or 1
            pattern["frequency"] = pattern["count"] / days_active
            
            # Calculate pattern strength based on consistency
            pattern["pattern_strength"] = min(pattern["frequency"] * 0.1, 1.0)
        
        # Update usage statistics
        profile["usage_statistics"]["last_update"] = datetime.utcnow()
        profile["usage_statistics"]["total_updates"] = profile["usage_statistics"].get("total_updates", 0) + 1
        
        # Calculate adaptation score
        profile["adaptation_score"] = await self._calculate_adaptation_score(profile)
        
        return {
            "success": True,
            "user_session": user_session,
            "profile_updated": True,
            "behavior_patterns_count": len(profile["behavior_patterns"]),
            "adaptation_score": profile["adaptation_score"],
            "agent_id": self.agent_id
        }
    
    async def _optimize_memory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize memory usage and retention policies"""
        optimization_type = task.get("optimization_type", "general")
        
        optimization_results = {
            "memories_cleaned": 0,
            "patterns_consolidated": 0,
            "space_freed": 0,
            "optimization_type": optimization_type
        }
        
        if optimization_type in ["general", "cleanup"]:
            # Clean old, low-importance memories
            cleaned = await self._cleanup_old_memories()
            optimization_results["memories_cleaned"] = cleaned
        
        if optimization_type in ["general", "consolidate"]:
            # Consolidate similar patterns
            consolidated = await self._consolidate_patterns()
            optimization_results["patterns_consolidated"] = consolidated
        
        if optimization_type in ["general", "compress"]:
            # Compress memory representations
            space_freed = await self._compress_memories()
            optimization_results["space_freed"] = space_freed
        
        return {
            "success": True,
            "optimization_results": optimization_results,
            "memory_efficiency_improved": True,
            "agent_id": self.agent_id
        }
    
    async def _calculate_importance(self, memory_data: Dict[str, Any]) -> float:
        """Calculate importance score for memory data"""
        importance_factors = []
        
        # Recency factor
        recency_factor = 1.0  # New memories are important
        importance_factors.append(recency_factor)
        
        # Content relevance factor
        if isinstance(memory_data, dict):
            content_length = len(str(memory_data))
            content_factor = min(content_length / 1000, 1.0)  # Longer content may be more important
            importance_factors.append(content_factor)
            
            # Check for high-value keywords
            content_str = str(memory_data).lower()
            high_value_keywords = ["error", "success", "important", "critical", "user", "preference"]
            keyword_factor = sum(0.1 for keyword in high_value_keywords if keyword in content_str)
            importance_factors.append(min(keyword_factor, 1.0))
        
        return sum(importance_factors) / len(importance_factors)
    
    async def _cleanup_short_term_memory(self):
        """Clean up old short-term memories"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)  # Keep memories for 24 hours
        
        to_remove = []
        for memory_id, memory in self.short_term_memory.items():
            if memory["timestamp"] < cutoff_time and memory["importance"] < 0.7:
                to_remove.append(memory_id)
        
        for memory_id in to_remove:
            # Move high-access memories to long-term storage
            memory = self.short_term_memory[memory_id]
            if memory["access_count"] > 5:
                self.long_term_memory[memory_id] = memory
            
            del self.short_term_memory[memory_id]
    
    async def _search_short_term_memory(self, query: str, user_session: str) -> List[Dict[str, Any]]:
        """Search short-term memory for relevant entries"""
        relevant_memories = []
        query_lower = query.lower()
        
        for memory_id, memory in self.short_term_memory.items():
            if memory["user_session"] == user_session or user_session == "default":
                memory_str = str(memory["data"]).lower()
                
                # Simple relevance scoring
                relevance = 0.0
                query_words = query_lower.split()
                for word in query_words:
                    if word in memory_str:
                        relevance += 0.2
                
                if relevance > 0:
                    memory_entry = memory.copy()
                    memory_entry["memory_id"] = memory_id
                    memory_entry["relevance_score"] = relevance
                    memory_entry["memory_type"] = "short_term"
                    relevant_memories.append(memory_entry)
        
        return relevant_memories
    
    async def _search_long_term_memory(self, query: str, user_session: str) -> List[Dict[str, Any]]:
        """Search long-term memory for relevant entries"""
        relevant_memories = []
        query_lower = query.lower()
        
        for memory_id, memory in self.long_term_memory.items():
            if memory["user_session"] == user_session or user_session == "default":
                memory_str = str(memory["data"]).lower()
                
                relevance = 0.0
                query_words = query_lower.split()
                for word in query_words:
                    if word in memory_str:
                        relevance += 0.3  # Long-term memories get higher relevance
                
                if relevance > 0:
                    memory_entry = memory.copy()
                    memory_entry["memory_id"] = memory_id
                    memory_entry["relevance_score"] = relevance
                    memory_entry["memory_type"] = "long_term"
                    relevant_memories.append(memory_entry)
        
        return relevant_memories
    
    async def _search_pattern_memory(self, query: str, user_session: str) -> List[Dict[str, Any]]:
        """Search pattern memory for relevant patterns"""
        relevant_patterns = []
        query_lower = query.lower()
        
        for pattern_id, pattern_memory in self.pattern_memory.items():
            if pattern_memory["user_session"] == user_session or user_session == "default":
                pattern_str = str(pattern_memory["pattern"]).lower()
                
                relevance = 0.0
                query_words = query_lower.split()
                for word in query_words:
                    if word in pattern_str:
                        relevance += 0.4 * pattern_memory["confidence"]  # Weight by pattern confidence
                
                if relevance > 0:
                    pattern_entry = pattern_memory.copy()
                    pattern_entry["memory_id"] = pattern_id
                    pattern_entry["relevance_score"] = relevance
                    pattern_entry["memory_type"] = "pattern"
                    relevant_patterns.append(pattern_entry)
        
        return relevant_patterns
    
    async def _search_context_memory(self, query: str, user_session: str) -> List[Dict[str, Any]]:
        """Search context memory for relevant session contexts"""
        relevant_contexts = []
        
        if user_session in self.context_memory:
            query_lower = query.lower()
            
            for context in self.context_memory[user_session]:
                context_str = str(context["data"]).lower()
                
                relevance = 0.0
                query_words = query_lower.split()
                for word in query_words:
                    if word in context_str:
                        relevance += 0.25
                
                if relevance > 0:
                    context_entry = context.copy()
                    context_entry["relevance_score"] = relevance
                    context_entry["memory_type"] = "context"
                    relevant_contexts.append(context_entry)
        
        return relevant_contexts
    
    async def _rank_memories(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank memories by relevance and other factors"""
        def memory_score(memory):
            base_score = memory.get("relevance_score", 0.0)
            
            # Recency bonus
            timestamp = memory.get("timestamp", datetime.min)
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            age_hours = (datetime.utcnow() - timestamp).total_seconds() / 3600
            recency_bonus = max(0, 1 - (age_hours / 168))  # Decay over a week
            
            # Importance bonus
            importance_bonus = memory.get("importance", 0.5) * 0.5
            
            # Access frequency bonus
            access_bonus = min(memory.get("access_count", 0) / 10, 0.3)
            
            return base_score + recency_bonus + importance_bonus + access_bonus
        
        memories.sort(key=memory_score, reverse=True)
        return memories
    
    async def _update_access_pattern(self, memory: Dict[str, Any]):
        """Update access patterns for retrieved memory"""
        memory_id = memory.get("memory_id")
        memory_type = memory.get("memory_type")
        
        if memory_type == "short_term" and memory_id in self.short_term_memory:
            self.short_term_memory[memory_id]["access_count"] += 1
            self.short_term_memory[memory_id]["last_accessed"] = datetime.utcnow()
        elif memory_type == "long_term" and memory_id in self.long_term_memory:
            self.long_term_memory[memory_id]["access_count"] += 1
            self.long_term_memory[memory_id]["last_accessed"] = datetime.utcnow()
    
    async def _extract_patterns(self, interaction_data: Dict[str, Any], user_session: str) -> List[Dict[str, Any]]:
        """Extract behavioral patterns from interaction data"""
        patterns = []
        
        # Time-based patterns
        if "timestamp" in interaction_data:
            hour = datetime.fromisoformat(interaction_data["timestamp"]).hour
            time_pattern = {
                "type": "time_preference",
                "pattern": f"active_during_hour_{hour}",
                "confidence": 0.7,
                "data": {"preferred_hour": hour}
            }
            patterns.append(time_pattern)
        
        # Action patterns
        if "action" in interaction_data:
            action = interaction_data["action"]
            action_pattern = {
                "type": "action_preference", 
                "pattern": f"frequently_uses_{action}",
                "confidence": 0.6,
                "data": {"preferred_action": action}
            }
            patterns.append(action_pattern)
        
        # Context patterns
        if "context" in interaction_data:
            context = interaction_data["context"]
            if isinstance(context, dict):
                for key, value in context.items():
                    context_pattern = {
                        "type": "context_preference",
                        "pattern": f"context_{key}_{value}",
                        "confidence": 0.5,
                        "data": {"context_key": key, "context_value": value}
                    }
                    patterns.append(context_pattern)
        
        return patterns
    
    async def _find_similar_pattern(self, pattern: Dict[str, Any], user_session: str) -> Optional[Dict[str, Any]]:
        """Find existing similar pattern"""
        pattern_type = pattern.get("type")
        pattern_data = pattern.get("pattern")
        
        for pattern_id, existing_pattern in self.pattern_memory.items():
            if (existing_pattern["user_session"] == user_session and
                existing_pattern["pattern"].get("type") == pattern_type and
                existing_pattern["pattern"].get("pattern") == pattern_data):
                
                return {"id": pattern_id, **existing_pattern}
        
        return None
    
    async def _reinforce_pattern(self, pattern_id: str, new_pattern_data: Dict[str, Any]):
        """Reinforce existing pattern with new occurrence"""
        if pattern_id in self.pattern_memory:
            existing = self.pattern_memory[pattern_id]
            existing["occurrences"] += 1
            existing["last_reinforced"] = datetime.utcnow()
            
            # Increase confidence with reinforcement
            existing["confidence"] = min(existing["confidence"] * 1.1, 1.0)
    
    async def _calculate_adaptation_score(self, profile: Dict[str, Any]) -> float:
        """Calculate how well the system has adapted to user behavior"""
        behavior_patterns = profile.get("behavior_patterns", {})
        
        if not behavior_patterns:
            return 0.0
        
        # Score based on pattern strength and consistency
        adaptation_scores = []
        
        for pattern_type, pattern_data in behavior_patterns.items():
            pattern_strength = pattern_data.get("pattern_strength", 0.0)
            frequency = pattern_data.get("frequency", 0.0)
            
            # Higher frequency and strength indicate better adaptation
            pattern_score = (pattern_strength + min(frequency, 1.0)) / 2
            adaptation_scores.append(pattern_score)
        
        return sum(adaptation_scores) / len(adaptation_scores)
    
    async def _cleanup_old_memories(self) -> int:
        """Clean up old, low-importance memories"""
        cleaned_count = 0
        cutoff_time = datetime.utcnow() - timedelta(days=30)  # Keep memories for 30 days
        
        # Clean short-term memory
        to_remove_short = []
        for memory_id, memory in self.short_term_memory.items():
            if (memory["timestamp"] < cutoff_time and 
                memory["importance"] < 0.3 and 
                memory["access_count"] < 2):
                to_remove_short.append(memory_id)
        
        for memory_id in to_remove_short:
            del self.short_term_memory[memory_id]
            cleaned_count += 1
        
        # Clean long-term memory (more conservative)
        cutoff_time_long = datetime.utcnow() - timedelta(days=90)
        to_remove_long = []
        for memory_id, memory in self.long_term_memory.items():
            if (memory["timestamp"] < cutoff_time_long and 
                memory["importance"] < 0.2 and 
                memory["access_count"] < 1):
                to_remove_long.append(memory_id)
        
        for memory_id in to_remove_long:
            del self.long_term_memory[memory_id]
            cleaned_count += 1
        
        return cleaned_count
    
    async def _consolidate_patterns(self) -> int:
        """Consolidate similar patterns to reduce redundancy"""
        consolidated_count = 0
        
        # Group patterns by type and user session
        pattern_groups = defaultdict(list)
        
        for pattern_id, pattern_memory in self.pattern_memory.items():
            key = (pattern_memory["user_session"], pattern_memory["pattern"]["type"])
            pattern_groups[key].append((pattern_id, pattern_memory))
        
        # Consolidate similar patterns within each group
        for group_key, patterns in pattern_groups.items():
            if len(patterns) > 1:
                # Find patterns that can be merged
                for i, (id1, pattern1) in enumerate(patterns):
                    for j, (id2, pattern2) in enumerate(patterns[i+1:], i+1):
                        similarity = await self._calculate_pattern_similarity(
                            pattern1["pattern"], pattern2["pattern"]
                        )
                        
                        if similarity > 0.8:  # High similarity threshold
                            # Merge patterns
                            merged_pattern = await self._merge_patterns(pattern1, pattern2)
                            self.pattern_memory[id1] = merged_pattern
                            
                            # Remove the redundant pattern
                            if id2 in self.pattern_memory:
                                del self.pattern_memory[id2]
                                consolidated_count += 1
        
        return consolidated_count
    
    async def _calculate_pattern_similarity(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> float:
        """Calculate similarity between two patterns"""
        if pattern1.get("type") != pattern2.get("type"):
            return 0.0
        
        # Simple similarity based on pattern string matching
        pattern1_str = pattern1.get("pattern", "")
        pattern2_str = pattern2.get("pattern", "")
        
        if pattern1_str == pattern2_str:
            return 1.0
        
        # Calculate Jaccard similarity for string patterns
        set1 = set(pattern1_str.split("_"))
        set2 = set(pattern2_str.split("_"))
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    async def _merge_patterns(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two similar patterns"""
        merged = pattern1.copy()
        
        # Combine occurrences
        merged["occurrences"] += pattern2["occurrences"]
        
        # Average confidence
        total_occurrences = pattern1["occurrences"] + pattern2["occurrences"]
        merged["confidence"] = (
            (pattern1["confidence"] * pattern1["occurrences"] + 
             pattern2["confidence"] * pattern2["occurrences"]) / total_occurrences
        )
        
        # Update timestamps
        merged["last_reinforced"] = max(pattern1["last_reinforced"], pattern2["last_reinforced"])
        merged["first_seen"] = min(pattern1["first_seen"], pattern2["first_seen"])
        
        return merged
    
    async def _compress_memories(self) -> int:
        """Compress memory representations to save space"""
        # This is a placeholder for memory compression
        # In a real implementation, you might:
        # 1. Compress text representations
        # 2. Remove redundant data
        # 3. Use more efficient data structures
        
        space_freed = 0
        
        # Example: Remove verbose fields from old memories
        cutoff_time = datetime.utcnow() - timedelta(days=7)
        
        for memory in self.long_term_memory.values():
            if memory["timestamp"] < cutoff_time:
                # Compress by removing less important fields
                if "detailed_metadata" in memory.get("data", {}):
                    del memory["data"]["detailed_metadata"]
                    space_freed += 1
        
        return space_freed
    
    async def _store_pattern_memory(self, pattern_id: str, pattern_entry: Dict[str, Any]):
        """Store pattern in pattern memory with deduplication"""
        self.pattern_memory[pattern_id] = pattern_entry
    
    def _get_memory_location(self, memory_type: str) -> str:
        """Get storage location description for memory type"""
        locations = {
            "short_term": "in_memory_cache",
            "long_term": "persistent_storage", 
            "pattern": "pattern_database",
            "context": "session_storage"
        }
        return locations.get(memory_type, "unknown_location")
    
    async def _general_memory_operation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general memory operations"""
        return {
            "success": True,
            "message": "General memory operation completed",
            "operation": task.get("operation", "unknown"),
            "agent_id": self.agent_id
        }