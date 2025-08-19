"""
Predictive Task Automation System for AETHER
AI system that goes beyond Fellou.ai capabilities with predictive intelligence
"""

import asyncio
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import groq
import openai

class PredictionType(Enum):
    TASK_AUTOMATION = "task_automation"
    USER_INTENT = "user_intent"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    CONTENT_GENERATION = "content_generation"
    BEHAVIOR_PATTERN = "behavior_pattern"

class ConfidenceLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class UserBehaviorPattern:
    pattern_id: str
    user_session: str
    pattern_type: str
    frequency: int
    last_occurrence: datetime
    context_data: Dict[str, Any]
    confidence: float

@dataclass
class PredictiveTask:
    task_id: str
    predicted_action: str
    user_intent: str
    confidence: ConfidenceLevel
    context: Dict[str, Any]
    suggested_automation: Optional[Dict[str, Any]] = None
    execution_time_estimate: Optional[int] = None
    success_probability: Optional[float] = None

@dataclass
class WorkflowOptimization:
    optimization_id: str
    workflow_id: str
    suggested_improvements: List[Dict[str, Any]]
    efficiency_gain: float
    time_savings: int
    complexity_reduction: float

class PredictiveAutomationEngine:
    def __init__(self, groq_client=None, openai_client=None):
        self.groq_client = groq_client
        self.openai_client = openai_client
        self.behavior_patterns: Dict[str, List[UserBehaviorPattern]] = {}
        self.ml_models: Dict[str, Any] = {}
        self.prediction_cache: Dict[str, Any] = {}
        
        # Initialize ML models
        self.initialize_ml_models()
        
    def initialize_ml_models(self):
        """Initialize machine learning models for predictions"""
        try:
            # Task classification model
            self.ml_models['task_classifier'] = RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )
            
            # Intent prediction model
            self.ml_models['intent_predictor'] = RandomForestClassifier(
                n_estimators=50,
                random_state=42
            )
            
            # Text vectorizer for NLP tasks
            self.ml_models['text_vectorizer'] = TfidfVectorizer(
                max_features=1000,
                stop_words='english'
            )
            
            # Clustering model for behavior patterns
            self.ml_models['behavior_clusterer'] = KMeans(
                n_clusters=10,
                random_state=42
            )
            
            print("✅ Predictive ML models initialized")
        except Exception as e:
            print(f"❌ ML models initialization failed: {e}")

    async def analyze_user_behavior(self, user_session: str, action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user behavior to identify patterns and predict future actions"""
        try:
            if len(action_history) < 3:
                return {
                    "success": False,
                    "error": "Insufficient data for pattern analysis"
                }
            
            # Extract behavior features
            patterns = self._extract_behavior_patterns(user_session, action_history)
            
            # Predict next likely actions
            predictions = await self._predict_next_actions(user_session, action_history)
            
            # Generate proactive automations
            proactive_automations = await self._generate_proactive_automations(patterns, predictions)
            
            # Calculate behavior insights
            insights = self._calculate_behavior_insights(action_history)
            
            return {
                "success": True,
                "user_session": user_session,
                "behavior_patterns": [asdict(p) for p in patterns],
                "predictions": [asdict(p) for p in predictions],
                "proactive_automations": proactive_automations,
                "insights": insights,
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _extract_behavior_patterns(self, user_session: str, action_history: List[Dict[str, Any]]) -> List[UserBehaviorPattern]:
        """Extract behavioral patterns from user action history"""
        patterns = []
        
        try:
            # Group actions by type
            action_groups = {}
            for action in action_history:
                action_type = action.get("type", "unknown")
                if action_type not in action_groups:
                    action_groups[action_type] = []
                action_groups[action_type].append(action)
            
            # Analyze patterns for each action type
            for action_type, actions in action_groups.items():
                if len(actions) >= 2:  # Need at least 2 occurrences to identify pattern
                    
                    # Time-based patterns
                    time_pattern = self._analyze_time_patterns(actions)
                    if time_pattern:
                        patterns.append(UserBehaviorPattern(
                            pattern_id=str(uuid.uuid4()),
                            user_session=user_session,
                            pattern_type=f"temporal_{action_type}",
                            frequency=len(actions),
                            last_occurrence=datetime.fromisoformat(actions[-1]["timestamp"]),
                            context_data=time_pattern,
                            confidence=0.8 if len(actions) > 5 else 0.6
                        ))
                    
                    # Sequence patterns
                    sequence_pattern = self._analyze_sequence_patterns(actions, action_history)
                    if sequence_pattern:
                        patterns.append(UserBehaviorPattern(
                            pattern_id=str(uuid.uuid4()),
                            user_session=user_session,
                            pattern_type=f"sequence_{action_type}",
                            frequency=sequence_pattern["frequency"],
                            last_occurrence=datetime.fromisoformat(actions[-1]["timestamp"]),
                            context_data=sequence_pattern,
                            confidence=sequence_pattern["confidence"]
                        ))
            
            # Store patterns for future analysis
            if user_session not in self.behavior_patterns:
                self.behavior_patterns[user_session] = []
            self.behavior_patterns[user_session].extend(patterns)
            
            return patterns
        except Exception as e:
            print(f"Pattern extraction error: {e}")
            return []

    def _analyze_time_patterns(self, actions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze temporal patterns in user actions"""
        try:
            timestamps = [datetime.fromisoformat(action["timestamp"]) for action in actions]
            
            # Calculate time intervals
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
            
            if not intervals:
                return None
            
            # Detect regular intervals (daily, hourly, etc.)
            avg_interval = sum(intervals) / len(intervals)
            
            # Check for daily patterns (around 24 hours = 86400 seconds)
            if 82800 <= avg_interval <= 90000:  # Allow 5% variance
                return {
                    "pattern_type": "daily",
                    "average_interval": avg_interval,
                    "regularity_score": self._calculate_regularity_score(intervals),
                    "preferred_times": [t.hour for t in timestamps]
                }
            
            # Check for hourly patterns
            elif 3300 <= avg_interval <= 3900:  # Around 1 hour with variance
                return {
                    "pattern_type": "hourly",
                    "average_interval": avg_interval,
                    "regularity_score": self._calculate_regularity_score(intervals)
                }
            
            # Check for frequent patterns (under 30 minutes)
            elif avg_interval < 1800:
                return {
                    "pattern_type": "frequent",
                    "average_interval": avg_interval,
                    "burst_activity": True
                }
            
            return None
        except Exception as e:
            print(f"Time pattern analysis error: {e}")
            return None

    def _analyze_sequence_patterns(self, target_actions: List[Dict[str, Any]], all_actions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze action sequence patterns"""
        try:
            # Find actions that commonly occur before target actions
            preceding_actions = []
            
            for target_action in target_actions:
                target_time = datetime.fromisoformat(target_action["timestamp"])
                
                # Look for actions within 5 minutes before target action
                for action in all_actions:
                    action_time = datetime.fromisoformat(action["timestamp"])
                    time_diff = (target_time - action_time).total_seconds()
                    
                    if 0 < time_diff <= 300:  # 5 minutes
                        preceding_actions.append(action["type"])
            
            if not preceding_actions:
                return None
            
            # Count frequency of preceding actions
            action_counts = {}
            for action_type in preceding_actions:
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
            
            # Find most common preceding action
            most_common = max(action_counts, key=action_counts.get)
            frequency = action_counts[most_common]
            
            if frequency >= 2:  # Need at least 2 occurrences
                confidence = min(0.9, frequency / len(target_actions))
                return {
                    "preceding_action": most_common,
                    "frequency": frequency,
                    "confidence": confidence,
                    "sequence_strength": frequency / len(target_actions)
                }
            
            return None
        except Exception as e:
            print(f"Sequence pattern analysis error: {e}")
            return None

    def _calculate_regularity_score(self, intervals: List[float]) -> float:
        """Calculate how regular the time intervals are"""
        if len(intervals) < 2:
            return 0.0
        
        # Calculate standard deviation of intervals
        mean_interval = sum(intervals) / len(intervals)
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Regularity score: lower std_dev relative to mean = higher regularity
        if mean_interval == 0:
            return 0.0
        
        coefficient_variation = std_dev / mean_interval
        regularity_score = max(0.0, 1.0 - coefficient_variation)
        
        return regularity_score

    async def _predict_next_actions(self, user_session: str, action_history: List[Dict[str, Any]]) -> List[PredictiveTask]:
        """Predict what the user is likely to do next"""
        predictions = []
        
        try:
            # Get recent patterns for this user
            user_patterns = self.behavior_patterns.get(user_session, [])
            
            # Analyze current context
            current_context = self._analyze_current_context(action_history)
            
            # Rule-based predictions
            rule_predictions = self._generate_rule_based_predictions(action_history, user_patterns)
            predictions.extend(rule_predictions)
            
            # AI-powered predictions
            ai_predictions = await self._generate_ai_predictions(action_history, current_context)
            predictions.extend(ai_predictions)
            
            # Pattern-based predictions
            pattern_predictions = self._generate_pattern_predictions(user_patterns, current_context)
            predictions.extend(pattern_predictions)
            
            # Sort by confidence and return top predictions
            predictions.sort(key=lambda x: x.confidence.value, reverse=True)
            return predictions[:5]  # Return top 5 predictions
            
        except Exception as e:
            print(f"Prediction generation error: {e}")
            return []

    def _analyze_current_context(self, action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze current user context"""
        recent_actions = action_history[-5:] if len(action_history) >= 5 else action_history
        
        context = {
            "recent_action_types": [action.get("type") for action in recent_actions],
            "current_url": recent_actions[-1].get("url", "") if recent_actions else "",
            "time_of_day": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "session_duration": self._calculate_session_duration(action_history),
            "activity_intensity": len(recent_actions) / 5.0  # Actions per recent time window
        }
        
        return context

    def _calculate_session_duration(self, action_history: List[Dict[str, Any]]) -> float:
        """Calculate current session duration in minutes"""
        if not action_history:
            return 0.0
        
        first_action = datetime.fromisoformat(action_history[0]["timestamp"])
        last_action = datetime.fromisoformat(action_history[-1]["timestamp"])
        
        duration = (last_action - first_action).total_seconds() / 60.0
        return duration

    def _generate_rule_based_predictions(self, action_history: List[Dict[str, Any]], patterns: List[UserBehaviorPattern]) -> List[PredictiveTask]:
        """Generate predictions based on predefined rules"""
        predictions = []
        
        try:
            recent_actions = action_history[-3:] if len(action_history) >= 3 else action_history
            
            # Rule 1: Form filling prediction
            if any(action.get("type") == "form_interaction" for action in recent_actions):
                predictions.append(PredictiveTask(
                    task_id=str(uuid.uuid4()),
                    predicted_action="complete_form_submission",
                    user_intent="form_completion",
                    confidence=ConfidenceLevel.HIGH,
                    context={"rule": "form_filling_sequence"},
                    suggested_automation={
                        "type": "auto_form_fill",
                        "description": "Automatically fill remaining form fields"
                    },
                    execution_time_estimate=30,
                    success_probability=0.85
                ))
            
            # Rule 2: Search behavior prediction
            search_actions = [a for a in recent_actions if a.get("type") == "search"]
            if len(search_actions) >= 2:
                predictions.append(PredictiveTask(
                    task_id=str(uuid.uuid4()),
                    predicted_action="refine_search_query",
                    user_intent="information_seeking",
                    confidence=ConfidenceLevel.MEDIUM,
                    context={"rule": "search_refinement"},
                    suggested_automation={
                        "type": "search_optimization",
                        "description": "Suggest better search terms or filters"
                    },
                    execution_time_estimate=15,
                    success_probability=0.7
                ))
            
            # Rule 3: Navigation pattern prediction
            navigation_actions = [a for a in action_history if a.get("type") == "navigation"]
            if len(navigation_actions) >= 3:
                common_domains = self._find_common_domains(navigation_actions)
                if common_domains:
                    predictions.append(PredictiveTask(
                        task_id=str(uuid.uuid4()),
                        predicted_action="visit_frequent_site",
                        user_intent="routine_browsing",
                        confidence=ConfidenceLevel.MEDIUM,
                        context={
                            "rule": "navigation_pattern",
                            "common_domains": common_domains
                        },
                        suggested_automation={
                            "type": "quick_navigation",
                            "description": f"Quick access to {common_domains[0]}"
                        },
                        execution_time_estimate=5,
                        success_probability=0.8
                    ))
            
            return predictions
        except Exception as e:
            print(f"Rule-based prediction error: {e}")
            return []

    async def _generate_ai_predictions(self, action_history: List[Dict[str, Any]], context: Dict[str, Any]) -> List[PredictiveTask]:
        """Generate predictions using AI models"""
        predictions = []
        
        try:
            # Prepare prompt for AI analysis
            action_summary = self._summarize_actions(action_history)
            
            prompt = f"""
            Analyze this user behavior and predict their next most likely actions:
            
            Recent Actions: {action_summary}
            Context: Time of day: {context['time_of_day']}, Day: {context['day_of_week']}
            Current URL: {context.get('current_url', 'N/A')}
            Session Duration: {context['session_duration']} minutes
            
            Based on this data, predict the top 3 most likely next actions the user will take.
            For each prediction, provide:
            1. The predicted action
            2. User intent
            3. Confidence level (low/medium/high/very_high)
            4. Suggested automation opportunity
            
            Respond in JSON format.
            """
            
            # Use Groq for prediction if available
            if self.groq_client:
                response = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.3,
                    max_tokens=1000
                )
                
                ai_response = response.choices[0].message.content
                
                # Parse AI response and convert to PredictiveTask objects
                try:
                    ai_predictions = json.loads(ai_response)
                    if isinstance(ai_predictions, list):
                        for pred in ai_predictions:
                            predictions.append(PredictiveTask(
                                task_id=str(uuid.uuid4()),
                                predicted_action=pred.get("predicted_action", "unknown"),
                                user_intent=pred.get("user_intent", "unknown"),
                                confidence=ConfidenceLevel(pred.get("confidence", "medium")),
                                context={"source": "ai_prediction", "model": "groq"},
                                suggested_automation=pred.get("suggested_automation"),
                                execution_time_estimate=pred.get("execution_time", 60),
                                success_probability=pred.get("success_probability", 0.6)
                            ))
                except json.JSONDecodeError:
                    print("Failed to parse AI prediction response")
            
            return predictions
        except Exception as e:
            print(f"AI prediction error: {e}")
            return []

    def _generate_pattern_predictions(self, patterns: List[UserBehaviorPattern], context: Dict[str, Any]) -> List[PredictiveTask]:
        """Generate predictions based on learned behavior patterns"""
        predictions = []
        
        try:
            current_time = datetime.now()
            
            for pattern in patterns:
                # Check if pattern is likely to repeat soon
                time_since_last = (current_time - pattern.last_occurrence).total_seconds()
                
                if pattern.pattern_type.startswith("temporal_"):
                    # Predict based on temporal patterns
                    if "daily" in pattern.context_data.get("pattern_type", ""):
                        # If daily pattern and it's been ~24 hours, predict repetition
                        if 82000 <= time_since_last <= 90000:  # Around 24 hours
                            predictions.append(PredictiveTask(
                                task_id=str(uuid.uuid4()),
                                predicted_action=pattern.pattern_type.replace("temporal_", ""),
                                user_intent="routine_behavior",
                                confidence=ConfidenceLevel.HIGH if pattern.confidence > 0.7 else ConfidenceLevel.MEDIUM,
                                context={
                                    "source": "pattern_prediction",
                                    "pattern_id": pattern.pattern_id,
                                    "pattern_frequency": pattern.frequency
                                },
                                suggested_automation={
                                    "type": "routine_automation",
                                    "description": f"Automate daily {pattern.pattern_type.replace('temporal_', '')} routine"
                                },
                                execution_time_estimate=45,
                                success_probability=pattern.confidence
                            ))
                
                elif pattern.pattern_type.startswith("sequence_"):
                    # Predict based on sequence patterns
                    sequence_data = pattern.context_data
                    preceding_action = sequence_data.get("preceding_action")
                    
                    # Check if preceding action occurred recently
                    if preceding_action in context["recent_action_types"]:
                        predictions.append(PredictiveTask(
                            task_id=str(uuid.uuid4()),
                            predicted_action=pattern.pattern_type.replace("sequence_", ""),
                            user_intent="sequential_behavior",
                            confidence=ConfidenceLevel.HIGH if sequence_data.get("confidence", 0) > 0.7 else ConfidenceLevel.MEDIUM,
                            context={
                                "source": "sequence_prediction",
                                "preceding_action": preceding_action,
                                "sequence_strength": sequence_data.get("sequence_strength", 0)
                            },
                            suggested_automation={
                                "type": "sequence_automation",
                                "description": f"Auto-trigger after {preceding_action}"
                            },
                            execution_time_estimate=20,
                            success_probability=sequence_data.get("confidence", 0.6)
                        ))
            
            return predictions
        except Exception as e:
            print(f"Pattern prediction error: {e}")
            return []

    async def _generate_proactive_automations(self, patterns: List[UserBehaviorPattern], predictions: List[PredictiveTask]) -> List[Dict[str, Any]]:
        """Generate proactive automation suggestions"""
        automations = []
        
        try:
            # High-confidence predictions become proactive automations
            for prediction in predictions:
                if prediction.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]:
                    automation = {
                        "automation_id": str(uuid.uuid4()),
                        "trigger_condition": f"predict_{prediction.predicted_action}",
                        "action_type": prediction.suggested_automation.get("type") if prediction.suggested_automation else "general",
                        "description": prediction.suggested_automation.get("description") if prediction.suggested_automation else f"Automate {prediction.predicted_action}",
                        "confidence": prediction.confidence.value,
                        "estimated_time_saving": prediction.execution_time_estimate or 30,
                        "success_probability": prediction.success_probability or 0.7,
                        "user_intent": prediction.user_intent,
                        "auto_execute": prediction.confidence == ConfidenceLevel.VERY_HIGH
                    }
                    automations.append(automation)
            
            # Pattern-based automations
            for pattern in patterns:
                if pattern.confidence > 0.8 and pattern.frequency >= 5:
                    automation = {
                        "automation_id": str(uuid.uuid4()),
                        "trigger_condition": f"pattern_{pattern.pattern_type}",
                        "action_type": "pattern_automation",
                        "description": f"Automate recurring {pattern.pattern_type} behavior",
                        "confidence": "high",
                        "estimated_time_saving": 60,
                        "success_probability": pattern.confidence,
                        "pattern_frequency": pattern.frequency,
                        "auto_execute": False  # Require user confirmation for pattern-based automations
                    }
                    automations.append(automation)
            
            return automations
        except Exception as e:
            print(f"Proactive automation generation error: {e}")
            return []

    def _summarize_actions(self, action_history: List[Dict[str, Any]]) -> str:
        """Summarize action history for AI analysis"""
        recent_actions = action_history[-10:]  # Last 10 actions
        
        summary_parts = []
        for action in recent_actions:
            action_type = action.get("type", "unknown")
            timestamp = action.get("timestamp", "")
            url = action.get("url", "")
            
            summary_parts.append(f"{action_type} at {timestamp} on {url}")
        
        return " -> ".join(summary_parts)

    def _find_common_domains(self, navigation_actions: List[Dict[str, Any]]) -> List[str]:
        """Find most commonly visited domains"""
        domain_counts = {}
        
        for action in navigation_actions:
            url = action.get("url", "")
            if url:
                try:
                    domain = url.split("://")[1].split("/")[0] if "://" in url else url.split("/")[0]
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                except:
                    continue
        
        # Sort by frequency and return top domains
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        return [domain for domain, count in sorted_domains[:3]]

    def _calculate_behavior_insights(self, action_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate behavioral insights and statistics"""
        try:
            total_actions = len(action_history)
            if total_actions == 0:
                return {"total_actions": 0}
            
            # Time-based analysis
            timestamps = [datetime.fromisoformat(action["timestamp"]) for action in action_history]
            session_duration = (timestamps[-1] - timestamps[0]).total_seconds() / 3600  # in hours
            
            # Action type distribution
            action_types = [action.get("type", "unknown") for action in action_history]
            type_distribution = {}
            for action_type in action_types:
                type_distribution[action_type] = type_distribution.get(action_type, 0) + 1
            
            # Activity intensity
            actions_per_hour = total_actions / session_duration if session_duration > 0 else 0
            
            # Most active hours
            hours = [t.hour for t in timestamps]
            hour_distribution = {}
            for hour in hours:
                hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            
            most_active_hour = max(hour_distribution, key=hour_distribution.get) if hour_distribution else 0
            
            return {
                "total_actions": total_actions,
                "session_duration_hours": round(session_duration, 2),
                "actions_per_hour": round(actions_per_hour, 2),
                "action_type_distribution": type_distribution,
                "most_active_hour": most_active_hour,
                "activity_intensity": "high" if actions_per_hour > 10 else "medium" if actions_per_hour > 5 else "low",
                "behavior_score": min(100, total_actions * 2 + actions_per_hour * 5)
            }
        except Exception as e:
            print(f"Behavior insights calculation error: {e}")
            return {"error": str(e)}

    async def optimize_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and optimize existing workflows"""
        try:
            workflow_id = workflow_data.get("workflow_id", str(uuid.uuid4()))
            steps = workflow_data.get("steps", [])
            
            if len(steps) < 2:
                return {"success": False, "error": "Workflow too short for optimization"}
            
            # Analyze workflow efficiency
            efficiency_analysis = self._analyze_workflow_efficiency(steps)
            
            # Generate optimization suggestions
            optimizations = await self._generate_workflow_optimizations(steps, efficiency_analysis)
            
            # Calculate potential improvements
            improvements = self._calculate_workflow_improvements(steps, optimizations)
            
            optimization = WorkflowOptimization(
                optimization_id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                suggested_improvements=optimizations,
                efficiency_gain=improvements["efficiency_gain"],
                time_savings=improvements["time_savings"],
                complexity_reduction=improvements["complexity_reduction"]
            )
            
            return {
                "success": True,
                "optimization": asdict(optimization),
                "analysis": efficiency_analysis
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_workflow_efficiency(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze workflow efficiency metrics"""
        try:
            total_steps = len(steps)
            
            # Count different types of steps
            step_types = {}
            wait_times = []
            
            for step in steps:
                step_type = step.get("type", "unknown")
                step_types[step_type] = step_types.get(step_type, 0) + 1
                
                if step_type == "wait":
                    wait_times.append(step.get("timeout", 0))
            
            # Calculate efficiency metrics
            total_wait_time = sum(wait_times)
            redundant_steps = self._identify_redundant_steps(steps)
            parallel_opportunities = self._identify_parallel_opportunities(steps)
            
            return {
                "total_steps": total_steps,
                "step_type_distribution": step_types,
                "total_wait_time": total_wait_time,
                "redundant_steps_count": len(redundant_steps),
                "parallel_opportunities_count": len(parallel_opportunities),
                "efficiency_score": self._calculate_efficiency_score(total_steps, total_wait_time, redundant_steps),
                "bottlenecks": self._identify_bottlenecks(steps)
            }
        except Exception as e:
            print(f"Workflow efficiency analysis error: {e}")
            return {}

    async def _generate_workflow_optimizations(self, steps: List[Dict[str, Any]], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific optimization suggestions"""
        optimizations = []
        
        try:
            # Reduce wait times
            if analysis.get("total_wait_time", 0) > 10000:  # More than 10 seconds
                optimizations.append({
                    "type": "reduce_wait_times",
                    "description": "Optimize wait conditions to reduce total wait time",
                    "impact": "high",
                    "time_saving": analysis["total_wait_time"] * 0.3,  # 30% reduction
                    "implementation": "Replace fixed timeouts with dynamic element detection"
                })
            
            # Eliminate redundant steps
            if analysis.get("redundant_steps_count", 0) > 0:
                optimizations.append({
                    "type": "remove_redundancy",
                    "description": f"Remove {analysis['redundant_steps_count']} redundant steps",
                    "impact": "medium",
                    "time_saving": analysis["redundant_steps_count"] * 2000,  # 2 seconds per step
                    "implementation": "Merge or eliminate duplicate operations"
                })
            
            # Add parallelization
            if analysis.get("parallel_opportunities_count", 0) > 0:
                optimizations.append({
                    "type": "add_parallelization",
                    "description": "Execute independent steps in parallel",
                    "impact": "high",
                    "time_saving": analysis["parallel_opportunities_count"] * 3000,  # 3 seconds per parallel group
                    "implementation": "Group independent operations for concurrent execution"
                })
            
            # Optimize step order
            if len(steps) > 5:
                optimizations.append({
                    "type": "optimize_sequence",
                    "description": "Reorder steps for better efficiency",
                    "impact": "medium",
                    "time_saving": len(steps) * 500,  # 0.5 seconds per step
                    "implementation": "Move expensive operations to background, prioritize user-visible actions"
                })
            
            # Add error handling
            error_handling_steps = len([s for s in steps if s.get("type") == "condition" or "error" in str(s)])
            if error_handling_steps < len(steps) * 0.2:  # Less than 20% error handling
                optimizations.append({
                    "type": "improve_error_handling",
                    "description": "Add comprehensive error handling and recovery",
                    "impact": "high",
                    "reliability_gain": 0.4,
                    "implementation": "Add try-catch blocks and fallback procedures"
                })
            
            return optimizations
        except Exception as e:
            print(f"Optimization generation error: {e}")
            return []

    def _identify_redundant_steps(self, steps: List[Dict[str, Any]]) -> List[int]:
        """Identify redundant steps in workflow"""
        redundant_indices = []
        
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            # Check for duplicate navigation
            if (current_step.get("type") == "navigate" and 
                next_step.get("type") == "navigate" and
                current_step.get("url") == next_step.get("url")):
                redundant_indices.append(i + 1)
            
            # Check for duplicate clicks on same element
            if (current_step.get("type") == "click" and 
                next_step.get("type") == "click" and
                current_step.get("selector") == next_step.get("selector")):
                redundant_indices.append(i + 1)
        
        return redundant_indices

    def _identify_parallel_opportunities(self, steps: List[Dict[str, Any]]) -> List[List[int]]:
        """Identify steps that can be executed in parallel"""
        parallel_groups = []
        
        # Simple heuristic: steps that don't depend on each other can be parallel
        i = 0
        while i < len(steps) - 1:
            current_group = [i]
            
            for j in range(i + 1, len(steps)):
                if self._can_execute_parallel(steps[i], steps[j]):
                    current_group.append(j)
                else:
                    break
            
            if len(current_group) > 1:
                parallel_groups.append(current_group)
                i = max(current_group) + 1
            else:
                i += 1
        
        return parallel_groups

    def _can_execute_parallel(self, step1: Dict[str, Any], step2: Dict[str, Any]) -> bool:
        """Check if two steps can be executed in parallel"""
        # Simple rules for parallel execution
        parallel_types = {"extract", "screenshot", "api_call"}
        
        type1 = step1.get("type")
        type2 = step2.get("type")
        
        # Both are parallel-safe types
        if type1 in parallel_types and type2 in parallel_types:
            return True
        
        # Different selectors for UI operations
        if (type1 in {"click", "type"} and type2 in {"click", "type"} and
            step1.get("selector") != step2.get("selector")):
            return True
        
        return False

    def _identify_bottlenecks(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify potential bottlenecks in workflow"""
        bottlenecks = []
        
        for i, step in enumerate(steps):
            step_type = step.get("type")
            
            # Long wait times
            if step_type == "wait" and step.get("timeout", 0) > 5000:
                bottlenecks.append({
                    "step_index": i,
                    "type": "long_wait",
                    "description": f"Long wait time: {step.get('timeout')}ms",
                    "severity": "medium"
                })
            
            # Navigation to external sites
            if step_type == "navigate":
                url = step.get("url", "")
                if "http" in url and not any(domain in url for domain in ["localhost", "127.0.0.1"]):
                    bottlenecks.append({
                        "step_index": i,
                        "type": "external_navigation",
                        "description": f"External site navigation: {url}",
                        "severity": "high"
                    })
        
        return bottlenecks

    def _calculate_efficiency_score(self, total_steps: int, total_wait_time: int, redundant_steps: List[int]) -> float:
        """Calculate overall workflow efficiency score (0-100)"""
        base_score = 100
        
        # Penalize for excessive steps
        if total_steps > 10:
            base_score -= (total_steps - 10) * 2
        
        # Penalize for long wait times (per second)
        base_score -= (total_wait_time / 1000) * 5
        
        # Penalize for redundant steps
        base_score -= len(redundant_steps) * 10
        
        return max(0, min(100, base_score))

    def _calculate_workflow_improvements(self, steps: List[Dict[str, Any]], optimizations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate potential improvements from optimizations"""
        total_time_saving = sum(opt.get("time_saving", 0) for opt in optimizations)
        
        # Calculate efficiency gain
        current_efficiency = 60  # Assume baseline
        efficiency_gain = min(40, len(optimizations) * 8)  # Max 40% improvement
        
        # Calculate complexity reduction
        complexity_reduction = min(0.5, len(optimizations) * 0.1)  # Max 50% reduction
        
        return {
            "efficiency_gain": efficiency_gain,
            "time_savings": int(total_time_saving),  # in milliseconds
            "complexity_reduction": complexity_reduction
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test the predictive engine connection"""
        try:
            # Test ML models
            models_ready = all(model is not None for model in self.ml_models.values())
            
            # Test AI clients
            ai_clients_ready = self.groq_client is not None or self.openai_client is not None
            
            return {
                "success": True,
                "ml_models_ready": models_ready,
                "ai_clients_ready": ai_clients_ready,
                "patterns_stored": len(self.behavior_patterns),
                "status": "operational"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}