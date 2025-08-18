import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import logging
from pymongo import MongoClient
import numpy as np
from collections import defaultdict, deque
import hashlib
import os

logger = logging.getLogger(__name__)

class UserBehaviorPattern:
    """Represents a learned user behavior pattern"""
    def __init__(self, pattern_id: str, pattern_type: str, data: Dict[str, Any]):
        self.pattern_id = pattern_id
        self.pattern_type = pattern_type  # 'browsing', 'automation', 'query', 'workflow'
        self.data = data
        self.confidence = 0.0
        self.frequency = 0
        self.last_seen = datetime.utcnow()
        self.created_at = datetime.utcnow()
        
    def update_frequency(self):
        """Update pattern frequency and confidence"""
        self.frequency += 1
        self.last_seen = datetime.utcnow()
        
        # Calculate confidence based on frequency and recency
        days_since_created = (datetime.utcnow() - self.created_at).days + 1
        self.confidence = min(0.95, (self.frequency / days_since_created) * 0.1)

class IntelligentMemorySystem:
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        
        # Collections for different types of memory
        self.user_sessions = self.db.user_sessions
        self.behavior_patterns = self.db.behavior_patterns
        self.contextual_memory = self.db.contextual_memory
        self.automation_history = self.db.automation_history
        self.preference_profiles = self.db.preference_profiles
        
        # In-memory caches for fast access
        self.session_cache = {}  # user_session -> recent data
        self.pattern_cache = {}  # user_session -> patterns
        self.context_buffer = defaultdict(lambda: deque(maxlen=100))  # Recent contexts
        
        # Learning parameters
        self.learning_threshold = 3  # Minimum occurrences to form pattern
        self.context_window_size = 50  # Number of recent interactions to consider
        self.max_patterns_per_user = 100
        
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
        """Background task for continuous learning"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._analyze_and_learn_patterns()
                await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Background learning error: {e}")
    
    async def record_user_interaction(self, user_session: str, interaction_type: str, 
                                   data: Dict[str, Any], context: Optional[Dict] = None):
        """Record user interaction for learning"""
        
        interaction_record = {
            "user_session": user_session,
            "interaction_type": interaction_type,  # 'chat', 'browse', 'automate', 'workflow'
            "data": data,
            "context": context or {},
            "timestamp": datetime.utcnow(),
            "session_id": data.get("session_id", ""),
            "page_url": data.get("current_url", "")
        }
        
        # Store in database
        self.user_sessions.insert_one(interaction_record)
        
        # Update in-memory cache
        if user_session not in self.session_cache:
            self.session_cache[user_session] = deque(maxlen=self.context_window_size)
        
        self.session_cache[user_session].append(interaction_record)
        
        # Update context buffer
        if context:
            self.context_buffer[user_session].append({
                "timestamp": datetime.utcnow(),
                "context": context,
                "interaction_type": interaction_type
            })
        
        # Trigger immediate learning for important interactions
        if interaction_type in ['automate', 'workflow'] or data.get('important', False):
            await self._learn_from_interaction(user_session, interaction_record)
    
    async def _learn_from_interaction(self, user_session: str, interaction: Dict[str, Any]):
        """Learn patterns from a single interaction"""
        
        interaction_type = interaction["interaction_type"]
        data = interaction["data"]
        
        if interaction_type == "chat":
            await self._learn_chat_patterns(user_session, data)
        elif interaction_type == "browse":
            await self._learn_browsing_patterns(user_session, data)
        elif interaction_type == "automate":
            await self._learn_automation_patterns(user_session, data)
        elif interaction_type == "workflow":
            await self._learn_workflow_patterns(user_session, data)
    
    async def _learn_chat_patterns(self, user_session: str, data: Dict[str, Any]):
        """Learn patterns from chat interactions"""
        
        message = data.get("message", "").lower()
        query_type = data.get("query_type", "general")
        
        # Extract topics and keywords
        keywords = self._extract_keywords(message)
        
        # Create pattern data
        pattern_data = {
            "keywords": keywords,
            "query_type": query_type,
            "message_length": len(message),
            "time_of_day": datetime.utcnow().hour,
            "language": data.get("language", "en")
        }
        
        await self._update_or_create_pattern(
            user_session, "chat_topic", pattern_data, 
            f"chat_{query_type}_{hash(tuple(sorted(keywords[:3])))}"
        )
    
    async def _learn_browsing_patterns(self, user_session: str, data: Dict[str, Any]):
        """Learn patterns from browsing behavior"""
        
        url = data.get("url", "")
        title = data.get("title", "")
        
        # Extract domain and categorize
        domain = self._extract_domain(url)
        category = self._categorize_website(domain, title)
        
        pattern_data = {
            "domain": domain,
            "category": category,
            "time_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday(),
            "title_keywords": self._extract_keywords(title)
        }
        
        await self._update_or_create_pattern(
            user_session, "browsing_habit", pattern_data,
            f"browse_{category}_{domain}"
        )
    
    async def _learn_automation_patterns(self, user_session: str, data: Dict[str, Any]):
        """Learn patterns from automation usage"""
        
        task_description = data.get("description", "")
        task_type = data.get("task_type", "generic")
        success = data.get("success", False)
        
        pattern_data = {
            "task_type": task_type,
            "success": success,
            "keywords": self._extract_keywords(task_description),
            "complexity": data.get("complexity", "medium"),
            "time_of_day": datetime.utcnow().hour,
            "current_url": data.get("current_url", "")
        }
        
        await self._update_or_create_pattern(
            user_session, "automation_preference", pattern_data,
            f"auto_{task_type}_{success}"
        )
    
    async def _update_or_create_pattern(self, user_session: str, pattern_type: str, 
                                      pattern_data: Dict[str, Any], pattern_key: str):
        """Update existing pattern or create new one"""
        
        pattern_id = hashlib.md5(f"{user_session}_{pattern_type}_{pattern_key}".encode()).hexdigest()
        
        # Check if pattern exists
        existing_pattern = self.behavior_patterns.find_one({
            "user_session": user_session,
            "pattern_id": pattern_id
        })
        
        if existing_pattern:
            # Update existing pattern
            self.behavior_patterns.update_one(
                {"_id": existing_pattern["_id"]},
                {
                    "$inc": {"frequency": 1},
                    "$set": {
                        "last_seen": datetime.utcnow(),
                        "data": pattern_data
                    }
                }
            )
            
            # Update confidence
            frequency = existing_pattern["frequency"] + 1
            days_since_created = (datetime.utcnow() - existing_pattern["created_at"]).days + 1
            confidence = min(0.95, (frequency / days_since_created) * 0.1)
            
            self.behavior_patterns.update_one(
                {"_id": existing_pattern["_id"]},
                {"$set": {"confidence": confidence}}
            )
            
        else:
            # Create new pattern
            new_pattern = {
                "user_session": user_session,
                "pattern_id": pattern_id,
                "pattern_type": pattern_type,
                "pattern_key": pattern_key,
                "data": pattern_data,
                "frequency": 1,
                "confidence": 0.1,
                "created_at": datetime.utcnow(),
                "last_seen": datetime.utcnow()
            }
            
            self.behavior_patterns.insert_one(new_pattern)
        
        # Update in-memory cache
        if user_session not in self.pattern_cache:
            self.pattern_cache[user_session] = {}
        
        self.pattern_cache[user_session][pattern_id] = {
            "pattern_type": pattern_type,
            "data": pattern_data,
            "frequency": existing_pattern["frequency"] + 1 if existing_pattern else 1,
            "confidence": confidence if existing_pattern else 0.1
        }
    
    async def get_user_insights(self, user_session: str) -> Dict[str, Any]:
        """Get comprehensive insights about user behavior"""
        
        # Get patterns from cache or database
        patterns = await self._get_user_patterns(user_session)
        
        # Analyze patterns
        insights = {
            "browsing_preferences": self._analyze_browsing_patterns(patterns),
            "automation_preferences": self._analyze_automation_patterns(patterns),
            "chat_preferences": self._analyze_chat_patterns(patterns),
            "temporal_patterns": self._analyze_temporal_patterns(patterns),
            "productivity_insights": self._analyze_productivity_patterns(patterns),
            "skill_level": self._assess_skill_level(patterns),
            "personality_traits": self._infer_personality_traits(patterns)
        }
        
        return insights
    
    async def _get_user_patterns(self, user_session: str) -> List[Dict[str, Any]]:
        """Get user patterns from cache or database"""
        
        # Try cache first
        if user_session in self.pattern_cache:
            return list(self.pattern_cache[user_session].values())
        
        # Load from database
        patterns = list(self.behavior_patterns.find({
            "user_session": user_session,
            "confidence": {"$gte": 0.1}
        }).sort("confidence", -1).limit(self.max_patterns_per_user))
        
        # Update cache
        self.pattern_cache[user_session] = {
            pattern["pattern_id"]: pattern for pattern in patterns
        }
        
        return patterns
    
    def _analyze_browsing_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Analyze browsing behavior patterns"""
        
        browsing_patterns = [p for p in patterns if p.get("pattern_type") == "browsing_habit"]
        
        if not browsing_patterns:
            return {"categories": [], "preferred_times": [], "domains": []}
        
        # Analyze categories
        categories = defaultdict(float)
        domains = defaultdict(float)
        times = defaultdict(float)
        
        for pattern in browsing_patterns:
            data = pattern["data"]
            confidence = pattern.get("confidence", 0.1)
            
            categories[data.get("category", "unknown")] += confidence
            domains[data.get("domain", "unknown")] += confidence
            times[data.get("time_of_day", 12)] += confidence
        
        return {
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5],
            "frequent_domains": sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10],
            "preferred_times": sorted(times.items(), key=lambda x: x[1], reverse=True)[:3],
            "total_patterns": len(browsing_patterns)
        }
    
    def _analyze_automation_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Analyze automation usage patterns"""
        
        automation_patterns = [p for p in patterns if p.get("pattern_type") == "automation_preference"]
        
        if not automation_patterns:
            return {"task_types": [], "success_rate": 0, "complexity_preference": "medium"}
        
        task_types = defaultdict(float)
        complexities = defaultdict(float)
        success_count = 0
        total_count = 0
        
        for pattern in automation_patterns:
            data = pattern["data"]
            confidence = pattern.get("confidence", 0.1)
            
            task_types[data.get("task_type", "generic")] += confidence
            complexities[data.get("complexity", "medium")] += confidence
            
            if data.get("success", False):
                success_count += 1
            total_count += 1
        
        return {
            "preferred_task_types": sorted(task_types.items(), key=lambda x: x[1], reverse=True)[:5],
            "complexity_preference": max(complexities, key=complexities.get) if complexities else "medium",
            "success_rate": (success_count / total_count) * 100 if total_count > 0 else 0,
            "automation_frequency": len(automation_patterns)
        }
    
    def _analyze_temporal_patterns(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal usage patterns"""
        
        hour_activity = defaultdict(float)
        day_activity = defaultdict(float)
        
        for pattern in patterns:
            data = pattern["data"]
            confidence = pattern.get("confidence", 0.1)
            
            hour = data.get("time_of_day")
            if hour is not None:
                hour_activity[hour] += confidence
            
            day = data.get("day_of_week")
            if day is not None:
                day_activity[day] += confidence
        
        # Determine peak hours and days
        peak_hours = sorted(hour_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_days = sorted(day_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "peak_hours": peak_hours,
            "peak_days": peak_days,
            "usage_pattern": self._classify_usage_pattern(hour_activity)
        }
    
    def _classify_usage_pattern(self, hour_activity: Dict[int, float]) -> str:
        """Classify user usage pattern"""
        
        morning_activity = sum(hour_activity.get(h, 0) for h in range(6, 12))
        afternoon_activity = sum(hour_activity.get(h, 0) for h in range(12, 18))
        evening_activity = sum(hour_activity.get(h, 0) for h in range(18, 24))
        night_activity = sum(hour_activity.get(h, 0) for h in [0, 1, 2, 3, 4, 5])
        
        max_activity = max(morning_activity, afternoon_activity, evening_activity, night_activity)
        
        if max_activity == morning_activity:
            return "morning_person"
        elif max_activity == afternoon_activity:
            return "day_worker"
        elif max_activity == evening_activity:
            return "evening_person"
        else:
            return "night_owl"
    
    def _assess_skill_level(self, patterns: List[Dict]) -> Dict[str, Any]:
        """Assess user skill level based on patterns"""
        
        automation_patterns = [p for p in patterns if p.get("pattern_type") == "automation_preference"]
        chat_patterns = [p for p in patterns if p.get("pattern_type") == "chat_topic"]
        
        skill_indicators = {
            "automation_usage": len(automation_patterns),
            "complex_tasks": sum(1 for p in automation_patterns 
                               if p["data"].get("complexity") in ["complex", "expert"]),
            "technical_queries": sum(1 for p in chat_patterns 
                                   if p["data"].get("query_type") in ["technical", "code"]),
            "success_rate": sum(p["data"].get("success", False) for p in automation_patterns) / max(len(automation_patterns), 1)
        }
        
        # Calculate skill score
        skill_score = 0
        skill_score += min(skill_indicators["automation_usage"] * 2, 20)
        skill_score += skill_indicators["complex_tasks"] * 10
        skill_score += skill_indicators["technical_queries"] * 5
        skill_score += skill_indicators["success_rate"] * 30
        
        if skill_score < 30:
            skill_level = "beginner"
        elif skill_score < 60:
            skill_level = "intermediate"
        elif skill_score < 90:
            skill_level = "advanced"
        else:
            skill_level = "expert"
        
        return {
            "level": skill_level,
            "score": skill_score,
            "indicators": skill_indicators
        }
    
    async def predict_next_action(self, user_session: str, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict likely next actions based on patterns and context"""
        
        patterns = await self._get_user_patterns(user_session)
        current_url = current_context.get("current_url", "")
        current_hour = datetime.utcnow().hour
        
        predictions = []
        
        # Context-based predictions
        if current_url:
            domain = self._extract_domain(current_url)
            
            # Find similar browsing contexts
            similar_patterns = [
                p for p in patterns 
                if p.get("pattern_type") == "browsing_habit" 
                and p["data"].get("domain") == domain
            ]
            
            for pattern in similar_patterns:
                predictions.append({
                    "action_type": "browse_similar",
                    "confidence": pattern.get("confidence", 0.1),
                    "suggestion": f"You often browse {pattern['data'].get('category', 'similar')} content",
                    "predicted_action": "continue_browsing"
                })
        
        # Time-based predictions
        time_patterns = [
            p for p in patterns 
            if abs(p["data"].get("time_of_day", 12) - current_hour) <= 1
        ]
        
        for pattern in time_patterns:
            if pattern.get("pattern_type") == "automation_preference":
                predictions.append({
                    "action_type": "automation",
                    "confidence": pattern.get("confidence", 0.1),
                    "suggestion": f"You often use automation at this time",
                    "predicted_action": "suggest_automation",
                    "task_type": pattern["data"].get("task_type", "generic")
                })
        
        # Sort by confidence and return top predictions
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        return predictions[:5]
    
    async def get_personalized_recommendations(self, user_session: str, context: str = "") -> List[Dict[str, Any]]:
        """Get personalized recommendations based on user patterns"""
        
        insights = await self.get_user_insights(user_session)
        patterns = await self._get_user_patterns(user_session)
        
        recommendations = []
        
        # Browsing recommendations
        browsing_prefs = insights.get("browsing_preferences", {})
        top_categories = browsing_prefs.get("top_categories", [])
        
        for category, confidence in top_categories[:3]:
            recommendations.append({
                "type": "content_discovery",
                "title": f"Discover More {category.title()} Content",
                "description": f"Based on your browsing history, you might enjoy more {category} content",
                "confidence": confidence,
                "action": "browse_category",
                "category": category
            })
        
        # Automation recommendations
        automation_prefs = insights.get("automation_preferences", {})
        preferred_tasks = automation_prefs.get("preferred_task_types", [])
        
        for task_type, confidence in preferred_tasks[:2]:
            recommendations.append({
                "type": "automation_suggestion",
                "title": f"Automate {task_type.title()} Tasks",
                "description": f"You frequently use {task_type} automation. Want to create a workflow?",
                "confidence": confidence,
                "action": "create_workflow",
                "task_type": task_type
            })
        
        # Skill-based recommendations
        skill_info = insights.get("skill_level", {})
        skill_level = skill_info.get("level", "beginner")
        
        if skill_level == "beginner":
            recommendations.append({
                "type": "learning",
                "title": "Learn Advanced Features",
                "description": "Discover automation and workflow capabilities to boost productivity",
                "confidence": 0.8,
                "action": "show_tutorial"
            })
        elif skill_level == "expert":
            recommendations.append({
                "type": "advanced_feature",
                "title": "Beta Features Available",
                "description": "Try advanced automation and integration features",
                "confidence": 0.9,
                "action": "enable_beta_features"
            })
        
        return sorted(recommendations, key=lambda x: x["confidence"], reverse=True)[:7]
    
    async def update_user_preference(self, user_session: str, preference_type: str, 
                                   preference_data: Dict[str, Any]):
        """Update user preferences manually"""
        
        self.preference_profiles.replace_one(
            {"user_session": user_session, "preference_type": preference_type},
            {
                "user_session": user_session,
                "preference_type": preference_type,
                "data": preference_data,
                "updated_at": datetime.utcnow()
            },
            upsert=True
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        if not text:
            return []
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = text.lower().split()
        stop_words = {"the", "a", "an", "to", "for", "of", "in", "on", "with", "by"}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return list(set(keywords))[:10]
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        
        if "://" in url:
            domain = url.split("://")[1].split("/")[0]
        else:
            domain = url.split("/")[0]
        
        return domain.replace("www.", "")
    
    def _categorize_website(self, domain: str, title: str = "") -> str:
        """Categorize website based on domain and title"""
        
        categories = {
            "social": ["linkedin", "twitter", "facebook", "instagram"],
            "tech": ["github", "stackoverflow", "techcrunch", "verge"],
            "job_search": ["indeed", "glassdoor", "monster", "ziprecruiter"],
            "news": ["cnn", "bbc", "reuters", "news"],
            "productivity": ["notion", "trello", "asana", "slack"],
            "education": ["coursera", "udemy", "edx", "khanacademy"],
            "research": ["scholar.google", "researchgate", "arxiv"]
        }
        
        domain_lower = domain.lower()
        title_lower = title.lower()
        
        for category, keywords in categories.items():
            if any(keyword in domain_lower or keyword in title_lower for keyword in keywords):
                return category
        
        return "general"
    
    async def _cleanup_old_data(self):
        """Clean up old data to maintain performance"""
        
        # Remove old interaction records (keep last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        self.user_sessions.delete_many({"timestamp": {"$lt": cutoff_date}})
        
        # Remove low-confidence patterns that haven't been seen recently
        old_pattern_cutoff = datetime.utcnow() - timedelta(days=7)
        self.behavior_patterns.delete_many({
            "confidence": {"$lt": 0.2},
            "last_seen": {"$lt": old_pattern_cutoff}
        })
        
        # Clear old cache entries
        for user_session in list(self.session_cache.keys()):
            if len(self.session_cache[user_session]) == 0:
                del self.session_cache[user_session]

# Global memory system instance
intelligent_memory_system = None  # Will be initialized in server.py