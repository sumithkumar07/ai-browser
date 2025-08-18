# Phase 5: Voice Commands Engine
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid
from enum import Enum
import re

logger = logging.getLogger(__name__)

class VoiceCommandType(Enum):
    NAVIGATION = "navigation"
    SEARCH = "search"
    AUTOMATION = "automation"
    CHAT = "chat"
    CONTROL = "control"
    QUICK_ACTION = "quick_action"

class VoiceCommand:
    def __init__(self, command_id: str, command_text: str, command_type: VoiceCommandType, 
                 action: str, parameters: Dict[str, Any] = None, confidence: float = 1.0):
        self.command_id = command_id
        self.command_text = command_text
        self.command_type = command_type
        self.action = action
        self.parameters = parameters or {}
        self.confidence = confidence
        self.created_at = datetime.utcnow()

class VoiceCommandsEngine:
    """
    Phase 5: Advanced Voice Commands Engine
    Enables hands-free browser control and AI interaction
    """
    
    def __init__(self):
        self.command_patterns = self._initialize_command_patterns()
        self.custom_commands = {}
        self.user_voice_preferences = {}
        self.command_history = []
        
    def _initialize_command_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize built-in voice command patterns"""
        return {
            # Navigation Commands
            "navigate_to": {
                "patterns": [
                    r"go to (.+)",
                    r"navigate to (.+)",
                    r"open (.+)",
                    r"visit (.+)"
                ],
                "command_type": VoiceCommandType.NAVIGATION,
                "action": "navigate",
                "parameter_extraction": lambda match: {"url": match.group(1)}
            },
            
            "go_back": {
                "patterns": [r"go back", r"back", r"previous page"],
                "command_type": VoiceCommandType.NAVIGATION,
                "action": "back"
            },
            
            "go_forward": {
                "patterns": [r"go forward", r"forward", r"next page"],
                "command_type": VoiceCommandType.NAVIGATION,
                "action": "forward"
            },
            
            "refresh_page": {
                "patterns": [r"refresh", r"reload", r"refresh page"],
                "command_type": VoiceCommandType.CONTROL,
                "action": "refresh"
            },
            
            # Search Commands
            "search": {
                "patterns": [
                    r"search for (.+)",
                    r"find (.+)",
                    r"look up (.+)"
                ],
                "command_type": VoiceCommandType.SEARCH,
                "action": "search",
                "parameter_extraction": lambda match: {"query": match.group(1)}
            },
            
            # AI Chat Commands
            "ask_ai": {
                "patterns": [
                    r"ask (.+)",
                    r"aether (.+)",
                    r"hey aether (.+)",
                    r"ai (.+)"
                ],
                "command_type": VoiceCommandType.CHAT,
                "action": "chat",
                "parameter_extraction": lambda match: {"message": match.group(1)}
            },
            
            "summarize_page": {
                "patterns": [
                    r"summarize this page",
                    r"summarize",
                    r"what is this page about",
                    r"explain this page"
                ],
                "command_type": VoiceCommandType.CHAT,
                "action": "summarize",
                "parameter_extraction": lambda match: {"request": "summarize"}
            },
            
            # Automation Commands
            "automate_task": {
                "patterns": [
                    r"automate (.+)",
                    r"create workflow for (.+)",
                    r"help me (.+) automatically"
                ],
                "command_type": VoiceCommandType.AUTOMATION,
                "action": "automate",
                "parameter_extraction": lambda match: {"task_description": match.group(1)}
            },
            
            "fill_form": {
                "patterns": [
                    r"fill the form",
                    r"auto fill",
                    r"complete the form"
                ],
                "command_type": VoiceCommandType.AUTOMATION,
                "action": "fill_form"
            },
            
            # Control Commands  
            "toggle_ai_assistant": {
                "patterns": [
                    r"toggle ai",
                    r"show ai",
                    r"hide ai",
                    r"open assistant",
                    r"close assistant"
                ],
                "command_type": VoiceCommandType.CONTROL,
                "action": "toggle_assistant"
            },
            
            "new_tab": {
                "patterns": [r"new tab", r"open new tab"],
                "command_type": VoiceCommandType.CONTROL,
                "action": "new_tab"
            },
            
            "close_tab": {
                "patterns": [r"close tab", r"close this tab"],
                "command_type": VoiceCommandType.CONTROL,
                "action": "close_tab"
            },
            
            # Quick Actions
            "scroll_down": {
                "patterns": [r"scroll down", r"go down"],
                "command_type": VoiceCommandType.QUICK_ACTION,
                "action": "scroll",
                "parameter_extraction": lambda match: {"direction": "down"}
            },
            
            "scroll_up": {
                "patterns": [r"scroll up", r"go up"],
                "command_type": VoiceCommandType.QUICK_ACTION,
                "action": "scroll",
                "parameter_extraction": lambda match: {"direction": "up"}
            },
            
            "click_link": {
                "patterns": [
                    r"click (.+)",
                    r"click on (.+)",
                    r"select (.+)"
                ],
                "command_type": VoiceCommandType.QUICK_ACTION,
                "action": "click",
                "parameter_extraction": lambda match: {"target": match.group(1)}
            },
            
            # System Commands
            "help": {
                "patterns": [
                    r"help",
                    r"what can you do",
                    r"voice commands",
                    r"show commands"
                ],
                "command_type": VoiceCommandType.CONTROL,
                "action": "help"
            },
            
            "stop_listening": {
                "patterns": [
                    r"stop listening",
                    r"stop voice",
                    r"turn off voice"
                ],
                "command_type": VoiceCommandType.CONTROL,
                "action": "stop_listening"
            },
            
            "start_listening": {
                "patterns": [
                    r"start listening",
                    r"voice on",
                    r"wake up aether"
                ],
                "command_type": VoiceCommandType.CONTROL,
                "action": "start_listening"
            }
        }
    
    async def process_voice_command(self, voice_text: str, user_session: str = None, 
                                  current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process voice command and return action to execute"""
        
        try:
            # Clean and normalize voice text
            normalized_text = self._normalize_voice_text(voice_text)
            
            # Parse voice command
            parsed_command = await self._parse_voice_command(normalized_text, user_session)
            
            if not parsed_command:
                return {
                    "success": False,
                    "error": "Command not recognized",
                    "suggestions": await self._get_command_suggestions(normalized_text),
                    "original_text": voice_text
                }
            
            # Add context to command
            if current_context:
                parsed_command.parameters.update({"context": current_context})
            
            # Record command in history
            self.command_history.append({
                "command": parsed_command,
                "voice_text": voice_text,
                "user_session": user_session,
                "timestamp": datetime.utcnow(),
                "context": current_context
            })
            
            # Generate execution instructions
            execution_instructions = await self._generate_execution_instructions(parsed_command, current_context)
            
            return {
                "success": True,
                "command": {
                    "id": parsed_command.command_id,
                    "type": parsed_command.command_type.value,
                    "action": parsed_command.action,
                    "parameters": parsed_command.parameters,
                    "confidence": parsed_command.confidence,
                    "original_text": voice_text
                },
                "execution_instructions": execution_instructions,
                "response_message": self._generate_response_message(parsed_command)
            }
            
        except Exception as e:
            logger.error(f"Voice command processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_text": voice_text
            }
    
    def _normalize_voice_text(self, text: str) -> str:
        """Normalize voice text for better pattern matching"""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove common speech artifacts
        text = re.sub(r'\buh\b|\bum\b|\ber\b', '', text)
        
        # Handle common speech-to-text corrections
        corrections = {
            "goe to": "go to",
            "navegate to": "navigate to",
            "opn": "open",
            "serch": "search",
            "refres": "refresh",
            "bak": "back",
            "foward": "forward"
        }
        
        for incorrect, correct in corrections.items():
            text = text.replace(incorrect, correct)
        
        # Clean extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def _parse_voice_command(self, text: str, user_session: str = None) -> Optional[VoiceCommand]:
        """Parse voice text into structured command"""
        
        # Check custom commands first (user-specific)
        if user_session and user_session in self.custom_commands:
            for command_name, command_config in self.custom_commands[user_session].items():
                for pattern in command_config["patterns"]:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        parameters = {}
                        if "parameter_extraction" in command_config:
                            parameters = command_config["parameter_extraction"](match)
                        
                        return VoiceCommand(
                            command_id=str(uuid.uuid4()),
                            command_text=text,
                            command_type=VoiceCommandType(command_config["command_type"]),
                            action=command_config["action"],
                            parameters=parameters,
                            confidence=0.95  # Higher confidence for custom commands
                        )
        
        # Check built-in commands
        for command_name, command_config in self.command_patterns.items():
            for pattern in command_config["patterns"]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parameters = {}
                    if "parameter_extraction" in command_config:
                        parameters = command_config["parameter_extraction"](match)
                    
                    return VoiceCommand(
                        command_id=str(uuid.uuid4()),
                        command_text=text,
                        command_type=command_config["command_type"],
                        action=command_config["action"],
                        parameters=parameters,
                        confidence=0.9
                    )
        
        # Fuzzy matching for partial commands
        fuzzy_match = await self._fuzzy_match_command(text)
        if fuzzy_match:
            return fuzzy_match
        
        return None
    
    async def _fuzzy_match_command(self, text: str) -> Optional[VoiceCommand]:
        """Attempt fuzzy matching for partial or unclear commands"""
        
        # Simple keyword-based fuzzy matching
        keywords = {
            "navigation": ["go", "open", "visit", "navigate"],
            "search": ["search", "find", "look"],
            "chat": ["ask", "tell", "aether", "ai"],
            "control": ["close", "refresh", "back", "forward"],
            "help": ["help", "commands", "what"]
        }
        
        text_words = set(text.split())
        
        best_match = None
        best_score = 0
        
        for category, category_keywords in keywords.items():
            overlap = len(text_words.intersection(set(category_keywords)))
            score = overlap / len(category_keywords)
            
            if score > best_score and score >= 0.5:  # At least 50% keyword match
                best_score = score
                best_match = category
        
        if best_match:
            # Create a generic command for the matched category
            if best_match == "navigation":
                # Extract potential URL or site name
                remaining_words = text_words - set(keywords["navigation"])
                if remaining_words:
                    target = " ".join(remaining_words)
                    return VoiceCommand(
                        command_id=str(uuid.uuid4()),
                        command_text=text,
                        command_type=VoiceCommandType.NAVIGATION,
                        action="navigate",
                        parameters={"url": target},
                        confidence=0.6
                    )
            
            elif best_match == "search":
                remaining_words = text_words - set(keywords["search"])
                if remaining_words:
                    query = " ".join(remaining_words)
                    return VoiceCommand(
                        command_id=str(uuid.uuid4()),
                        command_text=text,
                        command_type=VoiceCommandType.SEARCH,
                        action="search",
                        parameters={"query": query},
                        confidence=0.6
                    )
            
            elif best_match == "chat":
                remaining_words = text_words - set(keywords["chat"])
                if remaining_words:
                    message = " ".join(remaining_words)
                    return VoiceCommand(
                        command_id=str(uuid.uuid4()),
                        command_text=text,
                        command_type=VoiceCommandType.CHAT,
                        action="chat",
                        parameters={"message": message},
                        confidence=0.6
                    )
        
        return None
    
    async def _generate_execution_instructions(self, command: VoiceCommand, 
                                            context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate detailed execution instructions for the frontend"""
        
        instructions = {
            "command_id": command.command_id,
            "action_type": command.action,
            "parameters": command.parameters,
            "ui_feedback": True,
            "confirm_execution": command.confidence < 0.8,  # Confirm low-confidence commands
            "steps": []
        }
        
        if command.action == "navigate":
            url = command.parameters.get("url", "")
            # Smart URL processing
            if not url.startswith(("http://", "https://")):
                if "." not in url:
                    # Treat as search query
                    instructions["action_type"] = "search"
                    instructions["parameters"]["query"] = url
                    instructions["steps"] = [
                        {"action": "show_search_bar", "animate": True},
                        {"action": "fill_search", "value": url},
                        {"action": "execute_search"}
                    ]
                else:
                    # Add https prefix
                    instructions["parameters"]["url"] = f"https://{url}"
                    instructions["steps"] = [
                        {"action": "show_navigation_start"},
                        {"action": "update_url_bar", "url": f"https://{url}"},
                        {"action": "navigate", "url": f"https://{url}"},
                        {"action": "show_navigation_complete"}
                    ]
        
        elif command.action == "search":
            query = command.parameters.get("query", "")
            instructions["steps"] = [
                {"action": "show_search_interface"},
                {"action": "populate_search", "query": query},
                {"action": "execute_search", "engine": "google"}
            ]
        
        elif command.action == "chat":
            message = command.parameters.get("message", "")
            instructions["steps"] = [
                {"action": "open_ai_assistant", "animate": True},
                {"action": "populate_message", "message": message},
                {"action": "send_message", "auto_send": True}
            ]
        
        elif command.action == "back":
            instructions["steps"] = [
                {"action": "browser_back", "animate": True}
            ]
        
        elif command.action == "forward":
            instructions["steps"] = [
                {"action": "browser_forward", "animate": True}
            ]
        
        elif command.action == "refresh":
            instructions["steps"] = [
                {"action": "show_refresh_animation"},
                {"action": "browser_refresh"}
            ]
        
        elif command.action == "toggle_assistant":
            instructions["steps"] = [
                {"action": "toggle_ai_panel", "animate": True}
            ]
        
        elif command.action == "scroll":
            direction = command.parameters.get("direction", "down")
            instructions["steps"] = [
                {"action": "scroll_page", "direction": direction, "smooth": True}
            ]
        
        elif command.action == "automate":
            task_description = command.parameters.get("task_description", "")
            instructions["steps"] = [
                {"action": "open_ai_assistant"},
                {"action": "populate_message", "message": f"Please help me automate: {task_description}"},
                {"action": "send_message", "auto_send": True}
            ]
        
        elif command.action == "help":
            instructions["steps"] = [
                {"action": "show_voice_help_modal"},
                {"action": "display_available_commands"}
            ]
        
        return instructions
    
    def _generate_response_message(self, command: VoiceCommand) -> str:
        """Generate a response message for the user"""
        
        responses = {
            "navigate": "Navigating to {url}",
            "search": "Searching for '{query}'",
            "chat": "Asking AI: {message}",
            "back": "Going back",
            "forward": "Going forward",
            "refresh": "Refreshing page",
            "toggle_assistant": "Toggling AI assistant",
            "scroll": "Scrolling {direction}",
            "automate": "Creating automation for: {task_description}",
            "help": "Here are the available voice commands",
            "summarize": "Let me summarize this page for you"
        }
        
        base_message = responses.get(command.action, "Executing command")
        
        try:
            return base_message.format(**command.parameters)
        except KeyError:
            return base_message
    
    async def _get_command_suggestions(self, text: str) -> List[str]:
        """Get command suggestions for unrecognized voice input"""
        
        suggestions = []
        
        # Analyze the input for potential intentions
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["go", "open", "visit"]):
            suggestions.extend([
                "Try: 'Go to example.com'",
                "Try: 'Open Google'",
                "Try: 'Navigate to GitHub'"
            ])
        
        elif any(word in text_lower for word in ["find", "search", "look"]):
            suggestions.extend([
                "Try: 'Search for Python tutorials'",
                "Try: 'Find restaurants near me'",
                "Try: 'Look up weather'"
            ])
        
        elif any(word in text_lower for word in ["ask", "tell", "help"]):
            suggestions.extend([
                "Try: 'Ask what is machine learning'",
                "Try: 'Aether, help me with this page'",
                "Try: 'AI, explain this concept'"
            ])
        
        else:
            # General suggestions
            suggestions.extend([
                "Try: 'Go to [website name]'",
                "Try: 'Search for [topic]'",
                "Try: 'Ask [question]'",
                "Try: 'Help' to see all commands"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    async def add_custom_command(self, user_session: str, command_name: str, 
                                patterns: List[str], action: str, command_type: str,
                                parameters: Dict[str, Any] = None) -> bool:
        """Add custom voice command for user"""
        
        try:
            if user_session not in self.custom_commands:
                self.custom_commands[user_session] = {}
            
            self.custom_commands[user_session][command_name] = {
                "patterns": patterns,
                "action": action,
                "command_type": command_type,
                "parameters": parameters or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Custom command '{command_name}' added for user {user_session}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom command: {e}")
            return False
    
    async def get_user_voice_preferences(self, user_session: str) -> Dict[str, Any]:
        """Get voice preferences for user"""
        
        return self.user_voice_preferences.get(user_session, {
            "wake_word": "aether",
            "confirmation_required": False,
            "voice_feedback": True,
            "language": "en",
            "sensitivity": "medium",
            "custom_commands_enabled": True
        })
    
    async def update_voice_preferences(self, user_session: str, preferences: Dict[str, Any]) -> bool:
        """Update voice preferences for user"""
        
        try:
            if user_session not in self.user_voice_preferences:
                self.user_voice_preferences[user_session] = {}
            
            self.user_voice_preferences[user_session].update(preferences)
            logger.info(f"Voice preferences updated for user {user_session}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update voice preferences: {e}")
            return False
    
    async def get_command_history(self, user_session: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get command history for user"""
        
        user_history = [
            cmd for cmd in self.command_history 
            if cmd.get("user_session") == user_session
        ]
        
        # Sort by timestamp, most recent first
        user_history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return user_history[:limit]
    
    async def get_available_commands(self, user_session: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available voice commands"""
        
        commands_by_type = {}
        
        # Built-in commands
        for command_name, config in self.command_patterns.items():
            command_type = config["command_type"].value
            
            if command_type not in commands_by_type:
                commands_by_type[command_type] = []
            
            commands_by_type[command_type].append({
                "name": command_name,
                "patterns": config["patterns"],
                "action": config["action"],
                "description": self._get_command_description(command_name),
                "examples": config["patterns"][:2],  # First 2 patterns as examples
                "custom": False
            })
        
        # Custom commands for user
        if user_session and user_session in self.custom_commands:
            for command_name, config in self.custom_commands[user_session].items():
                command_type = config["command_type"]
                
                if command_type not in commands_by_type:
                    commands_by_type[command_type] = []
                
                commands_by_type[command_type].append({
                    "name": command_name,
                    "patterns": config["patterns"],
                    "action": config["action"],
                    "description": f"Custom command: {command_name}",
                    "examples": config["patterns"][:2],
                    "custom": True
                })
        
        return commands_by_type
    
    def _get_command_description(self, command_name: str) -> str:
        """Get human-readable description for command"""
        
        descriptions = {
            "navigate_to": "Navigate to a website or URL",
            "go_back": "Go back to the previous page",
            "go_forward": "Go forward to the next page", 
            "refresh_page": "Refresh the current page",
            "search": "Search for something on the web",
            "ask_ai": "Ask the AI assistant a question",
            "summarize_page": "Get a summary of the current page",
            "automate_task": "Create an automation for a task",
            "fill_form": "Auto-fill forms on the current page",
            "toggle_ai_assistant": "Show or hide the AI assistant",
            "new_tab": "Open a new browser tab",
            "close_tab": "Close the current tab",
            "scroll_down": "Scroll down on the page",
            "scroll_up": "Scroll up on the page",
            "click_link": "Click on a link or button",
            "help": "Show available voice commands",
            "stop_listening": "Stop voice recognition",
            "start_listening": "Start voice recognition"
        }
        
        return descriptions.get(command_name, "Execute voice command")

# Global instance
voice_commands_engine = VoiceCommandsEngine()