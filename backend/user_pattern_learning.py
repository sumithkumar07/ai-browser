# Phase 3: User Pattern Learning System
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pymongo import MongoClient
import numpy as np
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UserPattern:
    pattern_id: str
    user_session: str
    pattern_type: str
    confidence: float
    frequency: int
    last_occurrence: datetime
    context: Dict[str, Any]
    prediction_accuracy: float

class UserPatternLearningEngine:
    """
    Phase 3: Advanced User Pattern Learning System
    Learns user behavior patterns for predictive suggestions
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.user_patterns = defaultdict(list)
        self.learning_algorithms = self._initialize_learning_algorithms()
        self.pattern_cache = {}
        
    async def record_user_interaction(self, user_session: str, interaction_type: str, data: Dict[str, Any], context: Dict[str, Any] = None) -> bool:
        """Record user interaction for pattern learning"""
        try:
            interaction_record = {
                "interaction_id": str(uuid.uuid4()),
                "user_session": user_session,
                "interaction_type": interaction_type,
                "timestamp": datetime.utcnow(),
                "data": data,
                "context": context or {},
                "processed": False,
                "sequence_number": await self._get_next_sequence_number(user_session)
            }
            
            # Store in database
            self.db.user_interactions.insert_one(interaction_record)
            
            # Process pattern learning asynchronously
            asyncio.create_task(self._process_interaction_for_learning(interaction_record))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record user interaction: {e}")
            return False
    
    async def _process_interaction_for_learning(self, interaction: Dict[str, Any]) -> None:
        """Process interaction for pattern learning"""
        try:
            user_session = interaction["user_session"]
            
            # Get recent interactions for pattern analysis
            recent_interactions = await self._get_recent_interactions(user_session, limit=50)
            
            # Detect patterns in the interaction sequence
            detected_patterns = await self._detect_patterns(recent_interactions)
            
            # Update or create patterns
            for pattern_data in detected_patterns:
                await self._update_or_create_pattern(user_session, pattern_data)
            
            # Mark interaction as processed
            self.db.user_interactions.update_one(
                {"interaction_id": interaction["interaction_id"]},
                {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
            )
            
        except Exception as e:
            logger.error(f"Pattern learning processing failed: {e}")
    
    async def _detect_patterns(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns in user interactions"""
        patterns = []
        
        if len(interactions) < 3:
            return patterns
        
        # Detect various types of patterns
        patterns.extend(await self._detect_sequence_patterns(interactions))
        patterns.extend(await self._detect_temporal_patterns(interactions))
        patterns.extend(await self._detect_contextual_patterns(interactions))
        patterns.extend(await self._detect_preference_patterns(interactions))
        
        return patterns
    
    async def _detect_sequence_patterns(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect sequential interaction patterns"""
        patterns = []
        
        # Look for repeating sequences
        interaction_types = [i["interaction_type"] for i in interactions]
        
        # Find common subsequences of length 2-5
        for seq_length in range(2, min(6, len(interactions))):
            for i in range(len(interactions) - seq_length + 1):
                sequence = interaction_types[i:i + seq_length]
                
                # Count occurrences of this sequence
                count = 0
                for j in range(len(interaction_types) - seq_length + 1):
                    if interaction_types[j:j + seq_length] == sequence:
                        count += 1
                
                # If sequence occurs multiple times, it's a pattern
                if count >= 2:
                    pattern = {
                        "pattern_type": "sequence",
                        "sequence": sequence,
                        "frequency": count,
                        "confidence": min(count / len(interactions), 1.0),
                        "context": {
                            "sequence_length": seq_length,
                            "total_interactions": len(interactions)
                        }
                    }
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_temporal_patterns(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect time-based patterns"""
        patterns = []
        
        # Analyze time intervals between similar interactions
        interaction_times = defaultdict(list)
        
        for interaction in interactions:
            interaction_type = interaction["interaction_type"]
            timestamp = interaction["timestamp"]
            interaction_times[interaction_type].append(timestamp)
        
        # Find patterns in timing
        for interaction_type, timestamps in interaction_times.items():
            if len(timestamps) >= 3:
                # Calculate intervals between interactions
                intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    intervals.append(interval)
                
                # Check for regular patterns
                if intervals:
                    avg_interval = np.mean(intervals)
                    std_interval = np.std(intervals)
                    
                    # If intervals are relatively consistent, it's a temporal pattern
                    if std_interval < avg_interval * 0.5:  # Low variation
                        pattern = {
                            "pattern_type": "temporal",
                            "interaction_type": interaction_type,
                            "average_interval": avg_interval,
                            "regularity_score": 1.0 - (std_interval / avg_interval),
                            "frequency": len(timestamps),
                            "confidence": min(len(timestamps) / 10, 1.0),
                            "context": {
                                "interval_std": std_interval,
                                "predictable_timing": True
                            }
                        }
                        patterns.append(pattern)
        
        return patterns
    
    async def _detect_contextual_patterns(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect context-based patterns"""
        patterns = []
        
        # Group interactions by context
        context_groups = defaultdict(list)
        
        for interaction in interactions:
            context = interaction.get("context", {})
            
            # Create context signatures
            context_keys = ["current_url", "page_title", "automation_type", "ai_query_type"]
            context_signature = {}
            
            for key in context_keys:
                if key in context and context[key]:
                    context_signature[key] = context[key]
            
            if context_signature:
                signature_str = json.dumps(context_signature, sort_keys=True)
                context_groups[signature_str].append(interaction)
        
        # Find patterns in contextual behavior
        for context_sig, context_interactions in context_groups.items():
            if len(context_interactions) >= 2:
                # Analyze behavior in this context
                interaction_types = [i["interaction_type"] for i in context_interactions]
                type_counts = defaultdict(int)
                
                for itype in interaction_types:
                    type_counts[itype] += 1
                
                # Find dominant behavior in this context
                most_common = max(type_counts.items(), key=lambda x: x[1])
                
                if most_common[1] >= 2:  # Appears at least twice
                    pattern = {
                        "pattern_type": "contextual",
                        "context": json.loads(context_sig),
                        "dominant_behavior": most_common[0],
                        "behavior_frequency": most_common[1],
                        "total_in_context": len(context_interactions),
                        "confidence": most_common[1] / len(context_interactions),
                        "context_specificity": len(json.loads(context_sig))
                    }
                    patterns.append(pattern)
        
        return patterns
    
    async def _detect_preference_patterns(self, interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect user preference patterns"""
        patterns = []
        
        # Analyze preferences in different categories
        preferences = {
            "websites": defaultdict(int),
            "ai_query_types": defaultdict(int),
            "automation_types": defaultdict(int),
            "time_of_day": defaultdict(int)
        }
        
        for interaction in interactions:
            # Website preferences
            if interaction["interaction_type"] == "navigation":
                url = interaction.get("data", {}).get("url", "")
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        preferences["websites"][domain] += 1
                    except:
                        pass
            
            # AI query preferences
            context = interaction.get("context", {})
            if "ai_query_type" in context:
                preferences["ai_query_types"][context["ai_query_type"]] += 1
            
            # Automation preferences
            if interaction["interaction_type"] == "automation":
                automation_type = interaction.get("data", {}).get("automation_type", "")
                if automation_type:
                    preferences["automation_types"][automation_type] += 1
            
            # Time preferences
            hour = interaction["timestamp"].hour
            time_period = self._get_time_period(hour)
            preferences["time_of_day"][time_period] += 1
        
        # Create preference patterns
        for category, prefs in preferences.items():
            if prefs:
                most_preferred = max(prefs.items(), key=lambda x: x[1])
                total_interactions = sum(prefs.values())
                
                if most_preferred[1] >= 2 and total_interactions >= 3:
                    pattern = {
                        "pattern_type": "preference",
                        "category": category,
                        "preferred_value": most_preferred[0],
                        "preference_count": most_preferred[1],
                        "total_in_category": total_interactions,
                        "preference_strength": most_preferred[1] / total_interactions,
                        "confidence": min(most_preferred[1] / 5, 1.0),
                        "context": {
                            "all_preferences": dict(prefs),
                            "diversity_score": len(prefs) / max(total_interactions, 1)
                        }
                    }
                    patterns.append(pattern)
        
        return patterns
    
    async def _update_or_create_pattern(self, user_session: str, pattern_data: Dict[str, Any]) -> None:
        """Update existing pattern or create new one"""
        
        # Check if similar pattern exists
        existing_pattern = await self._find_similar_pattern(user_session, pattern_data)
        
        if existing_pattern:
            # Update existing pattern
            await self._update_pattern(existing_pattern, pattern_data)
        else:
            # Create new pattern
            await self._create_new_pattern(user_session, pattern_data)
    
    async def _find_similar_pattern(self, user_session: str, pattern_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find similar existing pattern"""
        
        pattern_type = pattern_data["pattern_type"]
        
        # Query for similar patterns
        query = {
            "user_session": user_session,
            "pattern_type": pattern_type,
            "active": True
        }
        
        # Add type-specific similarity criteria
        if pattern_type == "sequence":
            query["data.sequence"] = pattern_data["sequence"]
        elif pattern_type == "contextual":
            query["data.context"] = pattern_data["context"]
        elif pattern_type == "preference":
            query["data.category"] = pattern_data["category"]
            query["data.preferred_value"] = pattern_data["preferred_value"]
        elif pattern_type == "temporal":
            query["data.interaction_type"] = pattern_data["interaction_type"]
        
        return self.db.user_patterns.find_one(query)
    
    async def _update_pattern(self, existing_pattern: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        """Update existing pattern with new data"""
        
        # Calculate new confidence and frequency
        old_confidence = existing_pattern["confidence"]
        old_frequency = existing_pattern["frequency"]
        new_confidence = new_data["confidence"]
        new_frequency = new_data["frequency"]
        
        # Weighted average for confidence
        total_occurrences = old_frequency + new_frequency
        updated_confidence = (old_confidence * old_frequency + new_confidence * new_frequency) / total_occurrences
        
        # Update pattern
        update_data = {
            "confidence": updated_confidence,
            "frequency": total_occurrences,
            "last_occurrence": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "data": new_data  # Update with latest data
        }
        
        self.db.user_patterns.update_one(
            {"_id": existing_pattern["_id"]},
            {"$set": update_data}
        )
    
    async def _create_new_pattern(self, user_session: str, pattern_data: Dict[str, Any]) -> None:
        """Create new pattern"""
        
        pattern_record = {
            "pattern_id": str(uuid.uuid4()),
            "user_session": user_session,
            "pattern_type": pattern_data["pattern_type"],
            "confidence": pattern_data["confidence"],
            "frequency": pattern_data.get("frequency", 1),
            "last_occurrence": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "active": True,
            "prediction_accuracy": 0.0,
            "successful_predictions": 0,
            "total_predictions": 0,
            "data": pattern_data
        }
        
        self.db.user_patterns.insert_one(pattern_record)
    
    async def predict_next_user_action(self, user_session: str, current_context: Dict[str, Any]) -> Dict[str, Any]:
        """Predict user's next likely action based on learned patterns"""
        try:
            # Get active patterns for user
            user_patterns = list(self.db.user_patterns.find({
                "user_session": user_session,
                "active": True,
                "confidence": {"$gte": 0.3}
            }).sort("confidence", -1))
            
            if not user_patterns:
                return {
                    "success": False,
                    "message": "No patterns available for prediction",
                    "predictions": []
                }
            
            # Generate predictions based on patterns
            predictions = []
            
            for pattern in user_patterns:
                prediction = await self._generate_prediction_from_pattern(pattern, current_context)
                if prediction:
                    predictions.append(prediction)
            
            # Sort by confidence and return top predictions
            predictions.sort(key=lambda x: x["confidence"], reverse=True)
            
            return {
                "success": True,
                "predictions": predictions[:5],  # Top 5 predictions
                "total_patterns_used": len(user_patterns),
                "prediction_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Next action prediction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "predictions": []
            }
    
    async def _generate_prediction_from_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate prediction from specific pattern"""
        
        pattern_type = pattern["pattern_type"]
        pattern_data = pattern["data"]
        
        try:
            if pattern_type == "sequence":
                return await self._predict_from_sequence_pattern(pattern, context)
            elif pattern_type == "contextual":
                return await self._predict_from_contextual_pattern(pattern, context)
            elif pattern_type == "temporal":
                return await self._predict_from_temporal_pattern(pattern, context)
            elif pattern_type == "preference":
                return await self._predict_from_preference_pattern(pattern, context)
            
        except Exception as e:
            logger.error(f"Prediction generation failed for pattern {pattern['pattern_id']}: {e}")
        
        return None
    
    async def _predict_from_sequence_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate prediction from sequence pattern"""
        
        sequence = pattern["data"]["sequence"]
        
        # Get recent user actions to match against sequence
        recent_interactions = await self._get_recent_interactions(
            pattern["user_session"], 
            limit=len(sequence)
        )
        
        if len(recent_interactions) < len(sequence) - 1:
            return None
        
        # Check if current sequence matches pattern (minus last element)
        recent_types = [i["interaction_type"] for i in recent_interactions]
        
        # Check if we're in the middle of this sequence
        for i in range(len(sequence) - 1):
            if recent_types[-(len(sequence)-1-i):] == sequence[:len(sequence)-1-i]:
                next_action = sequence[len(sequence)-1-i]
                
                return {
                    "type": "sequence_continuation",
                    "predicted_action": next_action,
                    "confidence": pattern["confidence"] * 0.9,
                    "reasoning": f"Sequence pattern suggests next action: {next_action}",
                    "pattern_id": pattern["pattern_id"],
                    "sequence_position": len(sequence)-1-i,
                    "full_sequence": sequence
                }
        
        return None
    
    async def _predict_from_contextual_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate prediction from contextual pattern"""
        
        pattern_context = pattern["data"]["context"]
        dominant_behavior = pattern["data"]["dominant_behavior"]
        
        # Check if current context matches pattern context
        context_match_score = self._calculate_context_similarity(pattern_context, context)
        
        if context_match_score > 0.7:
            return {
                "type": "contextual_behavior",
                "predicted_action": dominant_behavior,
                "confidence": pattern["confidence"] * context_match_score,
                "reasoning": f"In similar context, user typically performs: {dominant_behavior}",
                "pattern_id": pattern["pattern_id"],
                "context_match_score": context_match_score,
                "matching_context": pattern_context
            }
        
        return None
    
    async def _predict_from_temporal_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate prediction from temporal pattern"""
        
        interaction_type = pattern["data"]["interaction_type"]
        avg_interval = pattern["data"]["average_interval"]
        regularity_score = pattern["data"]["regularity_score"]
        
        # Get last occurrence of this interaction type
        last_interaction = self.db.user_interactions.find_one({
            "user_session": pattern["user_session"],
            "interaction_type": interaction_type
        }, sort=[("timestamp", -1)])
        
        if last_interaction:
            time_since_last = (datetime.utcnow() - last_interaction["timestamp"]).total_seconds()
            
            # Check if we're approaching the expected interval
            expected_time_range = (avg_interval * 0.8, avg_interval * 1.2)
            
            if expected_time_range[0] <= time_since_last <= expected_time_range[1]:
                return {
                    "type": "temporal_prediction",
                    "predicted_action": interaction_type,
                    "confidence": pattern["confidence"] * regularity_score,
                    "reasoning": f"User typically performs {interaction_type} every {avg_interval:.0f} seconds",
                    "pattern_id": pattern["pattern_id"],
                    "time_since_last": time_since_last,
                    "expected_interval": avg_interval
                }
        
        return None
    
    async def _predict_from_preference_pattern(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate prediction from preference pattern"""
        
        category = pattern["data"]["category"]
        preferred_value = pattern["data"]["preferred_value"]
        preference_strength = pattern["data"]["preference_strength"]
        
        # Generate contextual suggestions based on preferences
        if category == "websites" and context.get("suggesting_navigation"):
            return {
                "type": "preference_suggestion",
                "predicted_action": "navigate",
                "suggested_target": preferred_value,
                "confidence": pattern["confidence"] * preference_strength,
                "reasoning": f"User frequently visits {preferred_value}",
                "pattern_id": pattern["pattern_id"],
                "preference_category": category,
                "preference_strength": preference_strength
            }
        
        elif category == "automation_types" and context.get("suggesting_automation"):
            return {
                "type": "preference_suggestion", 
                "predicted_action": "automation",
                "suggested_automation_type": preferred_value,
                "confidence": pattern["confidence"] * preference_strength,
                "reasoning": f"User frequently uses {preferred_value} automation",
                "pattern_id": pattern["pattern_id"],
                "preference_category": category,
                "preference_strength": preference_strength
            }
        
        return None
    
    async def get_user_insights(self, user_session: str) -> Dict[str, Any]:
        """Get comprehensive insights about user behavior"""
        try:
            # Get user patterns
            patterns = list(self.db.user_patterns.find({
                "user_session": user_session,
                "active": True
            }))
            
            # Get interaction statistics
            interaction_stats = await self._calculate_interaction_statistics(user_session)
            
            # Generate behavioral insights
            behavioral_insights = await self._generate_behavioral_insights(patterns, interaction_stats)
            
            # Get prediction accuracy
            prediction_accuracy = await self._calculate_prediction_accuracy(user_session)
            
            return {
                "user_session": user_session,
                "total_patterns": len(patterns),
                "pattern_breakdown": self._analyze_pattern_breakdown(patterns),
                "interaction_statistics": interaction_stats,
                "behavioral_insights": behavioral_insights,
                "prediction_accuracy": prediction_accuracy,
                "learning_quality": self._assess_learning_quality(patterns, interaction_stats),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"User insights generation failed: {e}")
            return {"error": str(e)}
    
    async def get_personalized_recommendations(self, user_session: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on learned patterns"""
        try:
            # Get predictions for current context
            predictions = await self.predict_next_user_action(user_session, context or {})
            
            if not predictions["success"]:
                return []
            
            # Convert predictions to recommendations
            recommendations = []
            
            for prediction in predictions["predictions"]:
                recommendation = await self._convert_prediction_to_recommendation(prediction, context)
                if recommendation:
                    recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Personalized recommendations failed: {e}")
            return []
    
    # Helper methods
    async def _get_recent_interactions(self, user_session: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent user interactions"""
        return list(self.db.user_interactions.find({
            "user_session": user_session
        }).sort("timestamp", -1).limit(limit))
    
    async def _get_next_sequence_number(self, user_session: str) -> int:
        """Get next sequence number for user interactions"""
        last_interaction = self.db.user_interactions.find_one({
            "user_session": user_session
        }, sort=[("sequence_number", -1)])
        
        return (last_interaction["sequence_number"] + 1) if last_interaction else 1
    
    def _get_time_period(self, hour: int) -> str:
        """Convert hour to time period"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0
        
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if context1[key] == context2[key]:
                matches += 1
        
        return matches / len(common_keys)
    
    async def _calculate_interaction_statistics(self, user_session: str) -> Dict[str, Any]:
        """Calculate interaction statistics for user"""
        interactions = await self._get_recent_interactions(user_session, limit=1000)
        
        if not interactions:
            return {"total_interactions": 0}
        
        # Basic statistics
        stats = {
            "total_interactions": len(interactions),
            "interaction_types": defaultdict(int),
            "daily_activity": defaultdict(int),
            "hourly_activity": defaultdict(int),
            "avg_session_length": 0,
            "most_active_day": "",
            "most_active_hour": 0
        }
        
        # Analyze interactions
        session_lengths = []
        
        for interaction in interactions:
            itype = interaction["interaction_type"]
            timestamp = interaction["timestamp"]
            
            stats["interaction_types"][itype] += 1
            stats["daily_activity"][timestamp.strftime("%A")] += 1
            stats["hourly_activity"][timestamp.hour] += 1
        
        # Find most active periods
        if stats["daily_activity"]:
            stats["most_active_day"] = max(stats["daily_activity"].items(), key=lambda x: x[1])[0]
        
        if stats["hourly_activity"]:
            stats["most_active_hour"] = max(stats["hourly_activity"].items(), key=lambda x: x[1])[0]
        
        # Convert defaultdicts to regular dicts
        stats["interaction_types"] = dict(stats["interaction_types"])
        stats["daily_activity"] = dict(stats["daily_activity"])
        stats["hourly_activity"] = dict(stats["hourly_activity"])
        
        return stats
    
    async def _generate_behavioral_insights(self, patterns: List[Dict[str, Any]], stats: Dict[str, Any]) -> List[str]:
        """Generate behavioral insights from patterns and statistics"""
        insights = []
        
        # Pattern-based insights
        if patterns:
            high_confidence_patterns = [p for p in patterns if p["confidence"] > 0.8]
            if high_confidence_patterns:
                insights.append(f"User has {len(high_confidence_patterns)} highly predictable behavior patterns")
        
        # Activity-based insights
        total_interactions = stats.get("total_interactions", 0)
        if total_interactions > 100:
            insights.append("User is highly engaged with frequent interactions")
        elif total_interactions > 20:
            insights.append("User shows moderate engagement levels")
        
        # Time-based insights
        most_active_day = stats.get("most_active_day", "")
        if most_active_day:
            insights.append(f"Most active on {most_active_day}")
        
        most_active_hour = stats.get("most_active_hour", 0)
        if most_active_hour:
            time_period = self._get_time_period(most_active_hour)
            insights.append(f"Most active during {time_period} hours")
        
        return insights
    
    async def _calculate_prediction_accuracy(self, user_session: str) -> Dict[str, float]:
        """Calculate prediction accuracy for user patterns"""
        patterns = list(self.db.user_patterns.find({
            "user_session": user_session,
            "total_predictions": {"$gt": 0}
        }))
        
        if not patterns:
            return {"overall_accuracy": 0.0, "total_predictions": 0}
        
        total_predictions = sum(p["total_predictions"] for p in patterns)
        successful_predictions = sum(p["successful_predictions"] for p in patterns)
        
        overall_accuracy = successful_predictions / total_predictions if total_predictions > 0 else 0.0
        
        return {
            "overall_accuracy": overall_accuracy,
            "total_predictions": total_predictions,
            "successful_predictions": successful_predictions
        }
    
    def _analyze_pattern_breakdown(self, patterns: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze breakdown of pattern types"""
        breakdown = defaultdict(int)
        
        for pattern in patterns:
            breakdown[pattern["pattern_type"]] += 1
        
        return dict(breakdown)
    
    def _assess_learning_quality(self, patterns: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Assess quality of learning based on patterns and statistics"""
        
        total_interactions = stats.get("total_interactions", 0)
        pattern_count = len(patterns)
        
        if total_interactions < 10:
            return "insufficient_data"
        elif pattern_count == 0:
            return "no_patterns_detected"
        elif pattern_count < 3:
            return "basic_learning"
        elif pattern_count < 10:
            return "good_learning"
        else:
            return "excellent_learning"
    
    async def _convert_prediction_to_recommendation(self, prediction: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert prediction to actionable recommendation"""
        
        prediction_type = prediction["type"]
        predicted_action = prediction["predicted_action"]
        confidence = prediction["confidence"]
        
        if confidence < 0.5:
            return None
        
        recommendation = {
            "id": str(uuid.uuid4()),
            "title": "",
            "description": "",
            "action": predicted_action,
            "confidence": confidence,
            "reasoning": prediction["reasoning"],
            "type": "personalized",
            "created_at": datetime.utcnow().isoformat()
        }
        
        if prediction_type == "sequence_continuation":
            recommendation["title"] = f"Continue with {predicted_action}"
            recommendation["description"] = f"Based on your usage pattern, you typically {predicted_action} next"
        
        elif prediction_type == "contextual_behavior":
            recommendation["title"] = f"Try {predicted_action}"
            recommendation["description"] = f"In similar situations, you usually {predicted_action}"
        
        elif prediction_type == "preference_suggestion":
            if "suggested_target" in prediction:
                recommendation["title"] = f"Visit {prediction['suggested_target']}"
                recommendation["description"] = f"You frequently visit this site"
            elif "suggested_automation_type" in prediction:
                recommendation["title"] = f"Use {prediction['suggested_automation_type']} automation"
                recommendation["description"] = f"This is your preferred automation type"
        
        elif prediction_type == "temporal_prediction":
            recommendation["title"] = f"Time for {predicted_action}"
            recommendation["description"] = f"You typically {predicted_action} around this time"
        
        return recommendation
    
    def _initialize_learning_algorithms(self) -> Dict[str, Any]:
        """Initialize learning algorithms configuration"""
        return {
            "sequence_learning": {
                "min_sequence_length": 2,
                "max_sequence_length": 5,
                "min_occurrences": 2,
                "confidence_threshold": 0.3
            },
            "temporal_learning": {
                "min_interactions": 3,
                "regularity_threshold": 0.5,
                "time_window_hours": 24
            },
            "contextual_learning": {
                "min_context_interactions": 2,
                "context_similarity_threshold": 0.7
            },
            "preference_learning": {
                "min_preference_count": 2,
                "preference_strength_threshold": 0.4
            }
        }

# Global instance
user_pattern_learning_engine = None

def initialize_user_pattern_learning(mongo_client: MongoClient):
    global user_pattern_learning_engine
    user_pattern_learning_engine = UserPatternLearningEngine(mongo_client)
    return user_pattern_learning_engine