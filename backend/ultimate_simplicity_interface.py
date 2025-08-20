# ⚡ ULTIMATE SIMPLICITY INTERFACE - Single-Input Philosophy
# Workstream B1: Zero Learning Curve & Invisible Complexity

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class InterfaceMode(Enum):
    """Interface complexity modes"""
    MINIMAL = "minimal"          # Single input only
    SIMPLIFIED = "simplified"    # Essential controls only
    STANDARD = "standard"        # Traditional interface
    ADVANCED = "advanced"        # Full feature access

class InputType(Enum):
    """Types of user input"""
    NATURAL_LANGUAGE = "natural_language"
    VOICE = "voice"
    GESTURE = "gesture"
    DIRECT_MANIPULATION = "direct_manipulation"

@dataclass
class UserIntent:
    """Parsed user intention"""
    intent_id: str
    primary_action: str
    secondary_actions: List[str]
    parameters: Dict[str, Any]
    confidence: float
    complexity: str
    estimated_steps: int

@dataclass
class InterfaceState:
    """Current interface state and context"""
    mode: InterfaceMode
    user_expertise: str  # novice, intermediate, expert
    current_context: Dict[str, Any]
    active_workflows: List[str]
    predicted_next_actions: List[str]

@dataclass
class PredictedAction:
    """AI-predicted next user action"""
    action: str
    description: str
    confidence: float
    shortcut: Optional[str]
    visual_hint: str

class UltimateSimplicityInterface:
    """Single-input philosophy with invisible complexity"""
    
    def __init__(self, db_client):
        self.db = db_client.aether_browser
        self.interface_states = {}  # session_id -> InterfaceState
        self.user_patterns = {}     # user_id -> behavioral patterns
        
        # Natural Language Processing for intent recognition
        self.intent_patterns = self._initialize_intent_patterns()
        
        # Interface adaptation engine
        self.adaptation_engine = InterfaceAdaptationEngine()
        
        logger.info("⚡ Ultimate Simplicity Interface initialized")

    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for intent recognition"""
        return {
            "navigate": [
                "go to", "visit", "open", "navigate to", "load", "browse to",
                "take me to", "show me", "find"
            ],
            "search": [
                "search for", "find", "look for", "query", "explore",
                "discover", "research", "investigate"
            ],
            "automate": [
                "automate", "create workflow", "set up automation", "schedule",
                "repeat", "do this regularly", "make this automatic"
            ],
            "analyze": [
                "analyze", "summarize", "extract", "review", "examine",
                "understand", "explain", "break down"
            ],
            "create": [
                "create", "make", "build", "generate", "produce",
                "design", "construct", "develop"
            ],
            "organize": [
                "organize", "sort", "categorize", "group", "arrange",
                "structure", "clean up", "manage"
            ]
        }

    async def process_single_input(self, session_id: str, user_input: str, 
                                 input_type: InputType = InputType.NATURAL_LANGUAGE,
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process single user input and determine complete action plan"""
        try:
            # Get or create interface state
            interface_state = self._get_interface_state(session_id)
            
            # Parse user intent from input
            user_intent = await self._parse_user_intent(user_input, context or {})
            
            # Adapt interface based on user expertise and context
            adapted_interface = await self.adaptation_engine.adapt_interface(
                interface_state, user_intent, self.user_patterns.get(session_id, {})
            )
            
            # Generate action plan
            action_plan = await self._generate_action_plan(user_intent, adapted_interface)
            
            # Predict next likely actions
            predicted_actions = await self._predict_next_actions(session_id, user_intent, context or {})
            
            # Update interface state
            interface_state.current_context.update(context or {})
            interface_state.predicted_next_actions = [p.action for p in predicted_actions]
            self.interface_states[session_id] = interface_state
            
            return {
                "success": True,
                "user_intent": {
                    "intent_id": user_intent.intent_id,
                    "primary_action": user_intent.primary_action,
                    "confidence": user_intent.confidence,
                    "complexity": user_intent.complexity
                },
                "action_plan": action_plan,
                "interface_adaptation": {
                    "recommended_mode": adapted_interface["mode"].value,
                    "hidden_complexity": adapted_interface["hidden_features"],
                    "exposed_controls": adapted_interface["visible_controls"]
                },
                "predicted_actions": [
                    {
                        "action": p.action,
                        "description": p.description,
                        "confidence": p.confidence,
                        "shortcut": p.shortcut
                    }
                    for p in predicted_actions[:3]  # Top 3 predictions
                ],
                "execution_ready": True
            }
            
        except Exception as e:
            logger.error(f"❌ Single input processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_message": "I understand you want to do something. Can you be more specific?"
            }

    async def _parse_user_intent(self, user_input: str, context: Dict[str, Any]) -> UserIntent:
        """Parse natural language input to determine user intent"""
        try:
            user_input_lower = user_input.lower().strip()
            
            # Intent classification
            detected_intents = []
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if pattern in user_input_lower:
                        detected_intents.append(intent)
                        break
            
            # Determine primary intent
            primary_intent = detected_intents[0] if detected_intents else "general"
            secondary_intents = detected_intents[1:] if len(detected_intents) > 1 else []
            
            # Extract parameters from input
            parameters = self._extract_parameters(user_input, primary_intent, context)
            
            # Calculate confidence based on pattern matches and context
            confidence = self._calculate_intent_confidence(user_input, detected_intents, context)
            
            # Determine complexity level
            complexity = self._assess_complexity(user_input, parameters, context)
            
            # Estimate steps required
            estimated_steps = self._estimate_execution_steps(primary_intent, parameters)
            
            return UserIntent(
                intent_id=str(uuid.uuid4()),
                primary_action=primary_intent,
                secondary_actions=secondary_intents,
                parameters=parameters,
                confidence=confidence,
                complexity=complexity,
                estimated_steps=estimated_steps
            )
            
        except Exception as e:
            logger.error(f"Intent parsing error: {e}")
            # Return default intent
            return UserIntent(
                intent_id=str(uuid.uuid4()),
                primary_action="general",
                secondary_actions=[],
                parameters={"original_input": user_input},
                confidence=0.3,
                complexity="simple",
                estimated_steps=1
            )

    def _extract_parameters(self, user_input: str, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant parameters from user input"""
        parameters = {"original_input": user_input}
        
        # URL extraction
        import re
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, user_input)
        if urls:
            parameters["urls"] = urls
            parameters["target_url"] = urls[0]
        
        # Extract quoted strings (specific terms)
        quoted_pattern = r'"([^"]*)"'
        quoted_terms = re.findall(quoted_pattern, user_input)
        if quoted_terms:
            parameters["specific_terms"] = quoted_terms
        
        # Extract action targets based on intent
        if intent == "navigate":
            # Look for website names, domains
            website_keywords = ["google", "github", "youtube", "facebook", "twitter", "linkedin"]
            for keyword in website_keywords:
                if keyword in user_input.lower():
                    parameters["target_site"] = keyword
                    parameters["inferred_url"] = f"https://{keyword}.com"
                    break
        
        elif intent == "search":
            # Extract search query
            search_triggers = ["search for", "find", "look for"]
            for trigger in search_triggers:
                if trigger in user_input.lower():
                    query_start = user_input.lower().find(trigger) + len(trigger)
                    search_query = user_input[query_start:].strip()
                    parameters["search_query"] = search_query
                    break
        
        # Add context parameters
        if context.get("current_url"):
            parameters["context_url"] = context["current_url"]
        
        return parameters

    def _calculate_intent_confidence(self, user_input: str, detected_intents: List[str], context: Dict[str, Any]) -> float:
        """Calculate confidence score for intent recognition"""
        base_confidence = 0.5
        
        # Boost confidence for clear intent patterns
        if detected_intents:
            base_confidence += 0.3
        
        # Boost for specific parameters
        if any(param in user_input.lower() for param in ["http", "www", ".com", ".org"]):
            base_confidence += 0.1
        
        # Boost for context alignment
        if context.get("current_url") and "this page" in user_input.lower():
            base_confidence += 0.1
        
        return min(max(base_confidence, 0.1), 0.95)

    def _assess_complexity(self, user_input: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Assess complexity of the requested action"""
        complexity_indicators = {
            "simple": ["go to", "open", "show", "find", "search"],
            "moderate": ["create", "automate", "analyze", "summarize", "extract"],
            "complex": ["workflow", "integration", "schedule", "multiple", "batch", "advanced"]
        }
        
        user_input_lower = user_input.lower()
        
        # Check for complexity keywords
        for level, keywords in complexity_indicators.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return level
        
        return "simple"

    def _estimate_execution_steps(self, intent: str, parameters: Dict[str, Any]) -> int:
        """Estimate number of steps required for execution"""
        step_estimates = {
            "navigate": 1,
            "search": 2,
            "automate": 4,
            "analyze": 3,
            "create": 5,
            "organize": 3
        }
        
        base_steps = step_estimates.get(intent, 2)
        return min(base_steps, 10)  # Cap at 10 steps

    async def _generate_action_plan(self, intent: UserIntent, adapted_interface: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed execution plan for the user intent"""
        try:
            action_plan = {
                "plan_id": str(uuid.uuid4()),
                "intent_id": intent.intent_id,
                "execution_mode": "automatic" if intent.confidence > 0.7 else "guided",
                "steps": [],
                "estimated_duration": intent.estimated_steps * 2,  # seconds
                "requires_confirmation": intent.complexity in ["moderate", "complex"]
            }
            
            # Generate steps based on primary action
            if intent.primary_action == "navigate":
                if intent.parameters.get("target_url"):
                    action_plan["steps"] = [
                        {
                            "step": 1,
                            "action": "navigate_to_url",
                            "parameters": {"url": intent.parameters["target_url"]},
                            "description": f"Navigate to {intent.parameters['target_url']}"
                        }
                    ]
                elif intent.parameters.get("inferred_url"):
                    action_plan["steps"] = [
                        {
                            "step": 1,
                            "action": "navigate_to_url", 
                            "parameters": {"url": intent.parameters["inferred_url"]},
                            "description": f"Navigate to {intent.parameters['target_site']}"
                        }
                    ]
            
            elif intent.primary_action == "search":
                search_query = intent.parameters.get("search_query", intent.parameters["original_input"])
                action_plan["steps"] = [
                    {
                        "step": 1,
                        "action": "navigate_to_search",
                        "parameters": {"search_engine": "google"},
                        "description": "Open search engine"
                    },
                    {
                        "step": 2,
                        "action": "perform_search",
                        "parameters": {"query": search_query},
                        "description": f"Search for: {search_query}"
                    }
                ]
            
            return action_plan
            
        except Exception as e:
            logger.error(f"Action plan generation error: {e}")
            return {
                "plan_id": str(uuid.uuid4()),
                "error": "Could not generate action plan"
            }

    async def _predict_next_actions(self, session_id: str, current_intent: UserIntent, 
                                  context: Dict[str, Any]) -> List[PredictedAction]:
        """Predict likely next user actions"""
        try:
            predictions = []
            
            # Context-based predictions
            if current_intent.primary_action == "navigate":
                predictions.extend([
                    PredictedAction(
                        action="analyze_page",
                        description="Analyze this page content",
                        confidence=0.7,
                        shortcut="Ctrl+A",
                        visual_hint="📊 Auto-analyze"
                    ),
                    PredictedAction(
                        action="create_automation",
                        description="Create automation for this page",
                        confidence=0.6,
                        shortcut="Ctrl+W",
                        visual_hint="🔧 Automate"
                    )
                ])
            
            # Sort by confidence
            predictions.sort(key=lambda x: x.confidence, reverse=True)
            return predictions[:5]  # Top 5 predictions
            
        except Exception as e:
            logger.error(f"Next action prediction error: {e}")
            return []

    def _get_interface_state(self, session_id: str) -> InterfaceState:
        """Get or create interface state for session"""
        if session_id not in self.interface_states:
            self.interface_states[session_id] = InterfaceState(
                mode=InterfaceMode.MINIMAL,
                user_expertise="novice",  # Start with novice assumption
                current_context={},
                active_workflows=[],
                predicted_next_actions=[]
            )
        return self.interface_states[session_id]


class InterfaceAdaptationEngine:
    """Engine for adapting interface based on user patterns"""
    
    async def adapt_interface(self, interface_state: InterfaceState, 
                            user_intent: UserIntent, user_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt interface based on current context and user patterns"""
        try:
            # Determine optimal interface mode
            optimal_mode = self._determine_optimal_mode(interface_state, user_intent, user_patterns)
            
            # Calculate what features to hide/show
            feature_visibility = self._calculate_feature_visibility(optimal_mode, user_intent)
            
            return {
                "mode": optimal_mode,
                "hidden_features": feature_visibility["hidden"],
                "visible_controls": feature_visibility["visible"]
            }
            
        except Exception as e:
            logger.error(f"Interface adaptation error: {e}")
            return {
                "mode": InterfaceMode.MINIMAL,
                "hidden_features": [],
                "visible_controls": ["single_input"]
            }

    def _determine_optimal_mode(self, interface_state: InterfaceState, 
                              user_intent: UserIntent, user_patterns: Dict[str, Any]) -> InterfaceMode:
        """Determine optimal interface mode"""
        
        # Simple intent -> minimal interface
        if user_intent.complexity == "simple" and user_intent.confidence > 0.8:
            return InterfaceMode.MINIMAL
        
        # Complex intent -> more controls
        if user_intent.complexity == "complex":
            if interface_state.user_expertise == "expert":
                return InterfaceMode.ADVANCED
            else:
                return InterfaceMode.STANDARD
        
        # Moderate complexity -> simplified interface
        if user_intent.complexity == "moderate":
            return InterfaceMode.SIMPLIFIED
        
        # Default to current mode or minimal
        return interface_state.mode if interface_state.mode else InterfaceMode.MINIMAL

    def _calculate_feature_visibility(self, mode: InterfaceMode, 
                                    user_intent: UserIntent) -> Dict[str, Any]:
        """Calculate which features to show/hide"""
        
        all_features = [
            "toolbar", "tabs", "bookmarks", "menu", "developer_tools", 
            "advanced_settings", "sidebar", "status_bar", "extensions"
        ]
        
        if mode == InterfaceMode.MINIMAL:
            visible = ["single_input", "voice_button"]
            hidden = all_features
            
        elif mode == InterfaceMode.SIMPLIFIED:
            visible = ["single_input", "voice_button", "back_forward", "essential_tools"]
            hidden = ["developer_tools", "advanced_settings", "extensions"]
            
        elif mode == InterfaceMode.STANDARD:
            visible = ["toolbar", "tabs", "bookmarks", "menu", "single_input"]
            hidden = ["developer_tools", "advanced_settings"]
            
        else:  # ADVANCED
            visible = all_features + ["single_input", "voice_button"]
            hidden = []
        
        return {
            "visible": visible,
            "hidden": hidden
        }


# Initialize functions for integration
def initialize_ultimate_simplicity_interface(db_client) -> UltimateSimplicityInterface:
    """Initialize and return ultimate simplicity interface"""
    return UltimateSimplicityInterface(db_client)

def get_ultimate_simplicity_interface() -> Optional[UltimateSimplicityInterface]:
    """Get the global ultimate simplicity interface instance"""
    return getattr(get_ultimate_simplicity_interface, '_instance', None)

def set_ultimate_simplicity_instance(instance: UltimateSimplicityInterface):
    """Set the global ultimate simplicity interface instance"""
    get_ultimate_simplicity_interface._instance = instance