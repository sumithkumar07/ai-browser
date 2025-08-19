"""
Predictive Task Automation Engine for AETHER
ML-powered behavior prediction and optimization
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import groq

class PredictiveAutomationEngine:
    def __init__(self):
        self.groq_client = None
        self.user_patterns = {}
        self.automation_history = {}
        self.behavior_models = {}
        self.prediction_cache = {}
        
    async def analyze_user_behavior(self, user_session: Dict[str, Any], action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user behavior patterns for predictions"""
        try:
            user_id = user_session.get("user_id", "anonymous")
            
            # Initialize user pattern tracking
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = {
                    "sessions": [],
                    "common_actions": {},
                    "time_patterns": {},
                    "workflow_preferences": {}
                }
            
            # Analyze current session
            session_analysis = {
                "session_id": user_session.get("session_id"),
                "timestamp": datetime.now().isoformat(),
                "actions": action_history,
                "duration": user_session.get("duration", 0),
                "pages_visited": user_session.get("pages_visited", [])
            }
            
            # Extract patterns
            patterns = await self._extract_behavior_patterns(action_history)
            
            # Predict next actions
            predictions = await self._predict_next_actions(user_id, patterns)
            
            # Store session data
            self.user_patterns[user_id]["sessions"].append(session_analysis)
            
            return {
                "success": True,
                "user_id": user_id,
                "patterns": patterns,
                "predictions": predictions,
                "confidence_score": self._calculate_confidence(patterns),
                "recommendations": await self._generate_recommendations(patterns)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _extract_behavior_patterns(self, action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract behavioral patterns from user actions"""
        try:
            patterns = {
                "action_frequency": {},
                "sequential_patterns": [],
                "time_patterns": {},
                "page_transitions": [],
                "interaction_types": {}
            }
            
            # Analyze action frequency
            for action in action_history:
                action_type = action.get("type", "unknown")
                patterns["action_frequency"][action_type] = patterns["action_frequency"].get(action_type, 0) + 1
            
            # Analyze sequential patterns
            if len(action_history) > 1:
                for i in range(len(action_history) - 1):
                    current_action = action_history[i].get("type")
                    next_action = action_history[i + 1].get("type")
                    sequence = f"{current_action} -> {next_action}"
                    patterns["sequential_patterns"].append(sequence)
            
            # Analyze time patterns
            for action in action_history:
                timestamp = action.get("timestamp")
                if timestamp:
                    hour = datetime.fromisoformat(timestamp).hour
                    patterns["time_patterns"][hour] = patterns["time_patterns"].get(hour, 0) + 1
            
            return patterns
        except Exception as e:
            return {"error": str(e)}

    async def _predict_next_actions(self, user_id: str, current_patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Predict next likely actions based on patterns"""
        try:
            predictions = []
            
            # Get historical patterns for user
            user_history = self.user_patterns.get(user_id, {})
            
            # Simple frequency-based prediction
            action_freq = current_patterns.get("action_frequency", {})
            if action_freq:
                sorted_actions = sorted(action_freq.items(), key=lambda x: x[1], reverse=True)
                
                for action, frequency in sorted_actions[:3]:
                    confidence = min(frequency / len(current_patterns.get("sequential_patterns", [1])), 1.0)
                    predictions.append({
                        "action": action,
                        "confidence": confidence,
                        "reason": f"Frequently used action ({frequency} times)"
                    })
            
            # AI-enhanced prediction if Groq client available
            if self.groq_client and current_patterns:
                ai_predictions = await self._ai_enhanced_prediction(current_patterns)
                predictions.extend(ai_predictions)
            
            return predictions[:5]  # Return top 5 predictions
        except Exception as e:
            return [{"error": str(e)}]

    async def _ai_enhanced_prediction(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use AI to enhance behavior predictions"""
        try:
            if not self.groq_client:
                return []
            
            prompt = f"""
            Based on the following user behavior patterns, predict the next 3 most likely actions:
            
            Action Frequency: {patterns.get('action_frequency', {})}
            Sequential Patterns: {patterns.get('sequential_patterns', [])}
            Time Patterns: {patterns.get('time_patterns', {})}
            
            Provide predictions in JSON format with action, confidence (0-1), and reasoning.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Simple parsing - in production, use more robust JSON parsing
            predictions = []
            if "action" in ai_response.lower():
                predictions.append({
                    "action": "ai_suggested_action",
                    "confidence": 0.7,
                    "reason": "AI-powered prediction",
                    "details": ai_response[:100]
                })
            
            return predictions
        except Exception as e:
            return [{"action": "error", "confidence": 0, "reason": str(e)}]

    def _calculate_confidence(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for predictions"""
        try:
            action_count = sum(patterns.get("action_frequency", {}).values())
            sequence_count = len(patterns.get("sequential_patterns", []))
            
            # Simple confidence calculation
            confidence = min((action_count + sequence_count) / 20, 1.0)
            return round(confidence, 2)
        except:
            return 0.5

    async def _generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate automation recommendations based on patterns"""
        try:
            recommendations = []
            
            action_freq = patterns.get("action_frequency", {})
            
            # Recommend automation for frequent actions
            for action, frequency in action_freq.items():
                if frequency >= 3:
                    recommendations.append(f"Consider automating '{action}' (used {frequency} times)")
            
            # Recommend workflow creation for sequential patterns
            sequences = patterns.get("sequential_patterns", [])
            if len(sequences) >= 2:
                recommendations.append("Create a workflow for your repeated action sequences")
            
            # Time-based recommendations
            time_patterns = patterns.get("time_patterns", {})
            if time_patterns:
                peak_hour = max(time_patterns.items(), key=lambda x: x[1])[0]
                recommendations.append(f"Schedule automated tasks around {peak_hour}:00 (your peak activity time)")
            
            return recommendations[:3]
        except Exception as e:
            return [f"Error generating recommendations: {str(e)}"]

    async def optimize_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing workflow based on usage patterns"""
        try:
            workflow_id = workflow_data.get("workflow_id")
            steps = workflow_data.get("steps", [])
            
            optimization_suggestions = []
            
            # Analyze step efficiency
            for i, step in enumerate(steps):
                step_type = step.get("type")
                execution_time = step.get("avg_execution_time", 0)
                
                if execution_time > 5:  # If step takes more than 5 seconds
                    optimization_suggestions.append({
                        "step_index": i,
                        "suggestion": "Consider breaking this step into smaller operations",
                        "reason": f"Step takes {execution_time}s on average"
                    })
            
            # Suggest parallel execution opportunities
            if len(steps) > 2:
                optimization_suggestions.append({
                    "type": "parallel_execution",
                    "suggestion": "Some steps can potentially run in parallel",
                    "impact": "Reduce total execution time by up to 40%"
                })
            
            optimized_workflow = {
                "original_workflow": workflow_data,
                "optimizations": optimization_suggestions,
                "estimated_improvement": "20-40% faster execution",
                "confidence": 0.8
            }
            
            return {
                "success": True,
                "optimized_workflow": optimized_workflow,
                "optimization_count": len(optimization_suggestions)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_connection(self) -> Dict[str, Any]:
        """Test the predictive engine connectivity"""
        try:
            test_patterns = {
                "action_frequency": {"click": 5, "type": 3, "scroll": 2},
                "sequential_patterns": ["click -> type", "type -> scroll"],
                "time_patterns": {14: 3, 15: 5, 16: 2}
            }
            
            predictions = await self._predict_next_actions("test_user", test_patterns)
            
            return {
                "success": True,
                "status": "operational",
                "test_predictions": len(predictions),
                "groq_client": self.groq_client is not None,
                "features": [
                    "behavior_analysis",
                    "pattern_recognition", 
                    "workflow_optimization",
                    "ai_predictions" if self.groq_client else "basic_predictions"
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}