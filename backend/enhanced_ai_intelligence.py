<file>
      <absolute_file_name>/app/backend/enhanced_ai_intelligence.py</absolute_file_name>
      <content>"""
Enhanced AI Intelligence Module - Phase 2 Implementation
Proactive AI with behavioral learning and predictive task automation
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging
from dataclasses import dataclass
from collections import defaultdict, deque
import re
import httpx

logger = logging.getLogger(__name__)

@dataclass
class UserBehaviorPattern:
    """User behavior pattern data structure"""
    pattern_id: str
    user_session: str
    pattern_type: str  # navigation, automation, search, workflow
    frequency: int
    last_occurrence: datetime
    context: Dict[str, Any]
    confidence_score: float
    suggested_automation: Optional[str] = None

@dataclass
class ProactiveAction:
    """Proactive action data structure"""
    action_id: str
    action_type: str  # suggestion, automation, workflow, navigation
    priority: str  # high, medium, low
    title: str
    description: str
    command: str
    context: Dict[str, Any]
    triggers: List[str]
    confidence: float

class BehavioralLearningEngine:
    """Advanced behavioral learning system"""
    
    def __init__(self, db_client):
        self.db = db_client.aether_browser
        self.patterns_collection = self.db.user_behavior_patterns
        self.actions_collection = self.db.user_actions
        self.learning_collection = self.db.learning_insights
        
        # In-memory pattern tracking
        self.active_patterns = defaultdict(list)
        self.session_history = defaultdict(lambda: deque(maxlen=50))
        
        # Pattern recognition thresholds
        self.PATTERN_MIN_FREQUENCY = 3
        self.CONFIDENCE_THRESHOLD = 0.7
        self.LEARNING_WINDOW_DAYS = 30

    async def track_user_action(self, session_id: str, action: Dict[str, Any]) -> None:
        """Track user action for pattern learning"""
        try:
            action_record = {
                "session_id": session_id,
                "action_type": action.get("type", "unknown"),
                "action_data": action,
                "timestamp": datetime.utcnow(),
                "context": action.get("context", {}),
                "url": action.get("current_url"),
                "command": action.get("command"),
                "success": action.get("success", True)
            }
            
            await self.actions_collection.insert_one(action_record)
            
            # Add to session history for immediate pattern detection
            self.session_history[session_id].append(action_record)
            
            # Trigger pattern analysis
            await self.analyze_patterns_realtime(session_id)
            
        except Exception as e:
            logger.error(f"Error tracking user action: {e}")

    async def analyze_patterns_realtime(self, session_id: str) -> List[UserBehaviorPattern]:
        """Real-time pattern analysis"""
        try:
            recent_actions = list(self.session_history[session_id])
            if len(recent_actions) < 3:
                return []
            
            patterns = []
            
            # Navigation patterns
            nav_patterns = await self._detect_navigation_patterns(session_id, recent_actions)
            patterns.extend(nav_patterns)
            
            # Automation patterns  
            auto_patterns = await self._detect_automation_patterns(session_id, recent_actions)
            patterns.extend(auto_patterns)
            
            # Workflow patterns
            workflow_patterns = await self._detect_workflow_patterns(session_id, recent_actions)
            patterns.extend(workflow_patterns)
            
            # Store significant patterns
            for pattern in patterns:
                if pattern.confidence_score >= self.CONFIDENCE_THRESHOLD:
                    await self._store_pattern(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error in real-time pattern analysis: {e}")
            return []

    async def _detect_navigation_patterns(self, session_id: str, actions: List[Dict]) -> List[UserBehaviorPattern]:
        """Detect navigation behavior patterns"""
        patterns = []
        
        # Analyze URL sequences
        nav_actions = [a for a in actions if a.get("action_type") == "navigation"]
        if len(nav_actions) < 2:
            return patterns
        
        # Detect repeated URL sequences
        url_sequence = [a.get("url") for a in nav_actions[-5:]]
        
        # Check for common patterns
        if len(set(url_sequence)) < len(url_sequence) * 0.7:  # Repeated URLs
            pattern = UserBehaviorPattern(
                pattern_id=str(uuid.uuid4()),
                user_session=session_id,
                pattern_type="navigation_repetitive",
                frequency=len(nav_actions),
                last_occurrence=datetime.utcnow(),
                context={"url_sequence": url_sequence},
                confidence_score=0.8,
                suggested_automation="Create bookmark folder for frequent sites"
            )
            patterns.append(pattern)
        
        return patterns

    async def _detect_automation_patterns(self, session_id: str, actions: List[Dict]) -> List[UserBehaviorPattern]:
        """Detect automation opportunity patterns"""
        patterns = []
        
        # Look for repetitive manual tasks
        manual_actions = [a for a in actions if a.get("action_type") in ["click", "form_fill", "data_extract"]]
        
        if len(manual_actions) >= 3:
            # Detect similar tasks
            task_similarity = await self._calculate_task_similarity(manual_actions)
            
            if task_similarity > 0.7:
                pattern = UserBehaviorPattern(
                    pattern_id=str(uuid.uuid4()),
                    user_session=session_id,
                    pattern_type="automation_opportunity",
                    frequency=len(manual_actions),
                    last_occurrence=datetime.utcnow(),
                    context={"similar_tasks": manual_actions[-3:]},
                    confidence_score=task_similarity,
                    suggested_automation="Automate repetitive task sequence"
                )
                patterns.append(pattern)
        
        return patterns

    async def _detect_workflow_patterns(self, session_id: str, actions: List[Dict]) -> List[UserBehaviorPattern]:
        """Detect workflow patterns"""
        patterns = []
        
        # Analyze action sequences for workflow patterns
        recent_sequence = actions[-10:]  # Last 10 actions
        
        # Look for research -> analyze -> create patterns
        workflow_indicators = {
            "research": ["search", "navigate", "browse"],
            "analyze": ["extract", "summarize", "compare"],
            "create": ["generate", "create", "build", "write"]
        }
        
        sequence_phases = []
        for action in recent_sequence:
            command = action.get("command", "").lower()
            for phase, keywords in workflow_indicators.items():
                if any(keyword in command for keyword in keywords):
                    sequence_phases.append(phase)
                    break
        
        # If we detect a research->analyze->create pattern
        if len(set(sequence_phases)) >= 2 and "research" in sequence_phases:
            pattern = UserBehaviorPattern(
                pattern_id=str(uuid.uuid4()),
                user_session=session_id,
                pattern_type="workflow_research_analyze_create",
                frequency=len(sequence_phases),
                last_occurrence=datetime.utcnow(),
                context={"workflow_sequence": sequence_phases},
                confidence_score=0.75,
                suggested_automation="Create workflow template for research process"
            )
            patterns.append(pattern)
        
        return patterns

    async def _calculate_task_similarity(self, tasks: List[Dict]) -> float:
        """Calculate similarity between tasks"""
        if len(tasks) < 2:
            return 0.0
        
        # Simple similarity based on action types and URLs
        action_types = [t.get("action_type") for t in tasks]
        urls = [t.get("url", "").split("/")[2] if t.get("url") else "" for t in tasks]  # Domain only
        
        # Calculate similarity scores
        type_similarity = len(set(action_types)) / len(action_types)
        url_similarity = len(set(urls)) / len(urls) if urls else 0
        
        # Return average similarity (lower is more similar)
        return 1.0 - ((type_similarity + url_similarity) / 2)

    async def _store_pattern(self, pattern: UserBehaviorPattern) -> None:
        """Store behavioral pattern in database"""
        try:
            pattern_doc = {
                "pattern_id": pattern.pattern_id,
                "user_session": pattern.user_session,
                "pattern_type": pattern.pattern_type,
                "frequency": pattern.frequency,
                "last_occurrence": pattern.last_occurrence,
                "context": pattern.context,
                "confidence_score": pattern.confidence_score,
                "suggested_automation": pattern.suggested_automation,
                "created_at": datetime.utcnow()
            }
            
            # Upsert pattern (update if exists, insert if not)
            await self.patterns_collection.update_one(
                {"user_session": pattern.user_session, "pattern_type": pattern.pattern_type},
                {"$set": pattern_doc, "$inc": {"frequency": 1}},
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error storing pattern: {e}")

    async def get_proactive_suggestions(self, session_id: str, current_context: Dict[str, Any]) -> List[ProactiveAction]:
        """Generate proactive suggestions based on learned patterns"""
        try:
            suggestions = []
            
            # Get user's behavioral patterns
            patterns = await self.patterns_collection.find({
                "user_session": session_id,
                "confidence_score": {"$gte": self.CONFIDENCE_THRESHOLD}
            }).to_list(length=20)
            
            # Generate context-aware suggestions
            for pattern in patterns:
                suggestion = await self._pattern_to_suggestion(pattern, current_context)
                if suggestion:
                    suggestions.append(suggestion)
            
            # Add contextual suggestions based on current URL/content
            contextual_suggestions = await self._generate_contextual_suggestions(current_context)
            suggestions.extend(contextual_suggestions)
            
            # Add time-based suggestions
            time_based_suggestions = await self._generate_time_based_suggestions(session_id)
            suggestions.extend(time_based_suggestions)
            
            # Sort by priority and confidence
            suggestions.sort(key=lambda x: (x.priority == "high", x.confidence), reverse=True)
            
            return suggestions[:8]  # Return top 8 suggestions
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestions: {e}")
            return []

    async def _pattern_to_suggestion(self, pattern: Dict, context: Dict[str, Any]) -> Optional[ProactiveAction]:
        """Convert behavioral pattern to actionable suggestion"""
        try:
            if pattern["pattern_type"] == "navigation_repetitive":
                return ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="automation",
                    priority="medium",
                    title="Create Navigation Shortcuts",
                    description="I noticed you visit these sites frequently. Want me to create quick shortcuts?",
                    command="create shortcuts for frequent sites",
                    context=pattern["context"],
                    triggers=["frequent_navigation"],
                    confidence=pattern["confidence_score"]
                )
            
            elif pattern["pattern_type"] == "automation_opportunity":
                return ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="workflow",
                    priority="high",
                    title="Automate Repetitive Task",
                    description="I can automate this repetitive task sequence for you.",
                    command="create automation workflow",
                    context=pattern["context"],
                    triggers=["repetitive_task"],
                    confidence=pattern["confidence_score"]
                )
            
            elif pattern["pattern_type"] == "workflow_research_analyze_create":
                return ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="workflow",
                    priority="high",
                    title="Create Research Workflow",
                    description="Build a workflow template for your research process?",
                    command="create research workflow template",
                    context=pattern["context"],
                    triggers=["workflow_pattern"],
                    confidence=pattern["confidence_score"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error converting pattern to suggestion: {e}")
            return None

    async def _generate_contextual_suggestions(self, context: Dict[str, Any]) -> List[ProactiveAction]:
        """Generate suggestions based on current context"""
        suggestions = []
        current_url = context.get("current_url", "")
        
        if not current_url:
            return suggestions
        
        try:
            # URL-based suggestions
            domain = current_url.split("//")[-1].split("/")[0]
            
            if "github.com" in domain:
                suggestions.append(ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="automation",
                    priority="medium",
                    title="GitHub Repository Analysis",
                    description="Analyze this repository structure and create documentation?",
                    command="analyze github repository",
                    context={"url": current_url},
                    triggers=["github_page"],
                    confidence=0.8
                ))
            
            elif "linkedin.com" in domain:
                suggestions.append(ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="automation",
                    priority="medium",
                    title="Professional Network Analysis",
                    description="Extract professional insights from this profile?",
                    command="analyze linkedin profile",
                    context={"url": current_url},
                    triggers=["linkedin_page"],
                    confidence=0.8
                ))
            
            elif any(ecommerce in domain for ecommerce in ["amazon.", "ebay.", "shopify"]):
                suggestions.append(ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="automation",
                    priority="high",
                    title="Price Monitoring",
                    description="Monitor price changes for this product?",
                    command="monitor product price",
                    context={"url": current_url},
                    triggers=["ecommerce_page"],
                    confidence=0.9
                ))
            
        except Exception as e:
            logger.error(f"Error generating contextual suggestions: {e}")
        
        return suggestions

    async def _generate_time_based_suggestions(self, session_id: str) -> List[ProactiveAction]:
        """Generate suggestions based on time patterns"""
        suggestions = []
        current_hour = datetime.now().hour
        
        try:
            # Morning productivity suggestions (8-11 AM)
            if 8 <= current_hour <= 11:
                suggestions.append(ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="workflow",
                    priority="medium",
                    title="Morning Productivity Setup",
                    description="Set up your productive morning workflow?",
                    command="create morning productivity workflow",
                    context={"time_period": "morning"},
                    triggers=["morning_hours"],
                    confidence=0.7
                ))
            
            # Afternoon focus suggestions (1-4 PM)  
            elif 13 <= current_hour <= 16:
                suggestions.append(ProactiveAction(
                    action_id=str(uuid.uuid4()),
                    action_type="automation",
                    priority="medium",
                    title="Focus Session",
                    description="Block distracting sites for deep work?",
                    command="enable focus mode",
                    context={"time_period": "afternoon"},
                    triggers=["afternoon_focus"],
                    confidence=0.7
                ))
            
        except Exception as e:
            logger.error(f"Error generating time-based suggestions: {e}")
        
        return suggestions


class AdvancedNLPProcessor:
    """Enhanced Natural Language Processing for complex commands"""
    
    def __init__(self, behavioral_engine: BehavioralLearningEngine):
        self.behavioral_engine = behavioral_engine
        
        # Command patterns for complex interpretation
        self.command_patterns = {
            "multi_step": [
                r"first .+ then .+",
                r".+ and then .+", 
                r"after .+ do .+",
                r".+, then .+, finally .+"
            ],
            "automation": [
                r"automate .+",
                r"set up .+ automation",
                r"create workflow for .+",
                r"monitor .+ for .+"
            ],
            "navigation": [
                r"go to .+",
                r"navigate to .+",
                r"visit .+",
                r"open .+"
            ],
            "data_extraction": [
                r"extract .+ from .+",
                r"get .+ data",
                r"find .+ information",
                r"collect .+ from .+"
            ]
        }

    async def process_complex_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process complex natural language commands"""
        try:
            result = {
                "command": command,
                "command_type": "unknown",
                "confidence": 0.0,
                "parsed_components": [],
                "suggested_actions": [],
                "automation_config": None,
                "multi_step": False
            }
            
            command_lower = command.lower()
            
            # Detect command type
            for cmd_type, patterns in self.command_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, command_lower, re.IGNORECASE):
                        result["command_type"] = cmd_type
                        result["confidence"] = 0.8
                        break
                if result["command_type"] != "unknown":
                    break
            
            # Process based on command type
            if result["command_type"] == "multi_step":
                result = await self._process_multi_step_command(command, context, result)
            elif result["command_type"] == "automation":
                result = await self._process_automation_command(command, context, result)
            elif result["command_type"] == "navigation":
                result = await self._process_navigation_command(command, context, result)
            elif result["command_type"] == "data_extraction":
                result = await self._process_data_extraction_command(command, context, result)
            
            # Add behavioral learning context
            result["behavioral_context"] = await self._get_behavioral_context(context.get("session_id"))
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing complex command: {e}")
            return {"command": command, "command_type": "error", "error": str(e)}

    async def _process_multi_step_command(self, command: str, context: Dict, result: Dict) -> Dict:
        """Process multi-step commands"""
        # Parse command into steps
        steps = []
        
        # Simple step parsing - can be enhanced with more sophisticated NLP
        if " then " in command.lower():
            step_parts = re.split(r"\s+then\s+", command.lower())
        elif " and " in command.lower():
            step_parts = re.split(r"\s+and\s+", command.lower())
        else:
            step_parts = [command]
        
        for i, step in enumerate(step_parts):
            steps.append({
                "step_id": i + 1,
                "command": step.strip(),
                "estimated_duration": "1-2 min",
                "automation_potential": "high"
            })
        
        result.update({
            "multi_step": True,
            "steps": steps,
            "sequence_id": str(uuid.uuid4()),
            "confidence": 0.9
        })
        
        return result

    async def _process_automation_command(self, command: str, context: Dict, result: Dict) -> Dict:
        """Process automation commands"""
        automation_config = {
            "type": "user_requested",
            "trigger": "manual",
            "schedule": None,
            "target_url": context.get("current_url"),
            "actions": []
        }
        
        # Extract automation intent
        if "monitor" in command.lower():
            automation_config["type"] = "monitoring"
            automation_config["schedule"] = "hourly"
        elif "daily" in command.lower():
            automation_config["schedule"] = "daily"
        elif "weekly" in command.lower():
            automation_config["schedule"] = "weekly"
        
        result.update({
            "automation_config": automation_config,
            "confidence": 0.85
        })
        
        return result

    async def _process_navigation_command(self, command: str, context: Dict, result: Dict) -> Dict:
        """Process navigation commands"""
        # Extract URL from command
        url_patterns = [
            r"https?://[^\s]+",
            r"www\.[^\s]+",
            r"[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?"
        ]
        
        extracted_url = None
        for pattern in url_patterns:
            match = re.search(pattern, command)
            if match:
                extracted_url = match.group(0)
                break
        
        # If no URL found, try common site shortcuts
        if not extracted_url:
            site_shortcuts = {
                "google": "https://google.com",
                "youtube": "https://youtube.com", 
                "github": "https://github.com",
                "stackoverflow": "https://stackoverflow.com"
            }
            
            for shortcut, url in site_shortcuts.items():
                if shortcut in command.lower():
                    extracted_url = url
                    break
        
        result.update({
            "url": extracted_url,
            "confidence": 0.9 if extracted_url else 0.3
        })
        
        return result

    async def _process_data_extraction_command(self, command: str, context: Dict, result: Dict) -> Dict:
        """Process data extraction commands"""
        extraction_config = {
            "source_url": context.get("current_url"),
            "data_types": [],
            "output_format": "json"
        }
        
        # Detect what type of data to extract
        data_keywords = {
            "links": ["link", "url", "href"],
            "text": ["text", "content", "paragraph"],
            "images": ["image", "img", "photo"],
            "tables": ["table", "data", "row"],
            "emails": ["email", "contact"],
            "phone": ["phone", "number"]
        }
        
        for data_type, keywords in data_keywords.items():
            if any(keyword in command.lower() for keyword in keywords):
                extraction_config["data_types"].append(data_type)
        
        result.update({
            "extraction_config": extraction_config,
            "confidence": 0.8 if extraction_config["data_types"] else 0.4
        })
        
        return result

    async def _get_behavioral_context(self, session_id: str) -> Dict[str, Any]:
        """Get behavioral context for command processing"""
        if not session_id:
            return {}
        
        try:
            # Get recent patterns for this user
            patterns = await self.behavioral_engine.patterns_collection.find({
                "user_session": session_id
            }).sort("last_occurrence", -1).limit(5).to_list(length=5)
            
            return {
                "recent_patterns": [p["pattern_type"] for p in patterns],
                "automation_experience": len([p for p in patterns if "automation" in p["pattern_type"]]),
                "workflow_experience": len([p for p in patterns if "workflow" in p["pattern_type"]])
            }
            
        except Exception as e:
            logger.error(f"Error getting behavioral context: {e}")
            return {}


# Initialize enhanced AI intelligence
def initialize_enhanced_ai_intelligence(db_client):
    """Initialize enhanced AI intelligence system"""
    try:
        behavioral_engine = BehavioralLearningEngine(db_client)
        nlp_processor = AdvancedNLPProcessor(behavioral_engine)
        
        logger.info("Enhanced AI Intelligence system initialized successfully")
        return {
            "behavioral_engine": behavioral_engine,
            "nlp_processor": nlp_processor
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced AI intelligence: {e}")
        return None</content>
    </file>