# Phase 5: Keyboard Shortcuts Engine
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid
from enum import Enum

logger = logging.getLogger(__name__)

class ShortcutCategory(Enum):
    NAVIGATION = "navigation"
    EDITING = "editing"
    AI_ASSISTANT = "ai_assistant"
    AUTOMATION = "automation"
    TAB_MANAGEMENT = "tab_management"
    SEARCH = "search"
    DEVELOPER = "developer"
    ACCESSIBILITY = "accessibility"

class KeyboardShortcut:
    def __init__(self, shortcut_id: str, combination: str, action: str, 
                 category: ShortcutCategory, description: str, 
                 parameters: Dict[str, Any] = None, enabled: bool = True):
        self.shortcut_id = shortcut_id
        self.combination = combination  # e.g., "Ctrl+T", "Alt+Shift+A"
        self.action = action
        self.category = category
        self.description = description
        self.parameters = parameters or {}
        self.enabled = enabled
        self.usage_count = 0
        self.last_used = None
        self.created_at = datetime.utcnow()

class KeyboardShortcutsEngine:
    """
    Phase 5: Advanced Keyboard Shortcuts Engine
    Provides comprehensive keyboard navigation and control
    """
    
    def __init__(self):
        self.shortcuts = self._initialize_default_shortcuts()
        self.custom_shortcuts = {}
        self.user_preferences = {}
        self.shortcut_history = []
        self.disabled_shortcuts = set()
        
    def _initialize_default_shortcuts(self) -> Dict[str, KeyboardShortcut]:
        """Initialize comprehensive default keyboard shortcuts"""
        
        shortcuts = {}
        
        # Navigation Shortcuts
        nav_shortcuts = [
            ("nav_back", "Alt+Left", "browser_back", "Go back to previous page"),
            ("nav_forward", "Alt+Right", "browser_forward", "Go forward to next page"),
            ("nav_refresh", "F5", "refresh_page", "Refresh current page"),
            ("nav_refresh_alt", "Ctrl+R", "refresh_page", "Refresh current page"),
            ("nav_force_refresh", "Ctrl+F5", "force_refresh", "Force refresh (bypass cache)"),
            ("nav_home", "Alt+Home", "go_home", "Go to home page"),
            ("nav_address_bar", "Ctrl+L", "focus_address_bar", "Focus address bar"),
            ("nav_address_bar_alt", "F6", "focus_address_bar", "Focus address bar"),
        ]
        
        for shortcut_id, combo, action, desc in nav_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.NAVIGATION, desc
            )
        
        # Tab Management Shortcuts
        tab_shortcuts = [
            ("tab_new", "Ctrl+T", "new_tab", "Open new tab"),
            ("tab_close", "Ctrl+W", "close_tab", "Close current tab"),
            ("tab_reopen", "Ctrl+Shift+T", "reopen_tab", "Reopen recently closed tab"),
            ("tab_duplicate", "Ctrl+Shift+K", "duplicate_tab", "Duplicate current tab"),
            ("tab_next", "Ctrl+Tab", "next_tab", "Switch to next tab"),
            ("tab_prev", "Ctrl+Shift+Tab", "previous_tab", "Switch to previous tab"),
            ("tab_first", "Ctrl+1", "go_to_tab", "Go to first tab", {"tab_index": 0}),
            ("tab_second", "Ctrl+2", "go_to_tab", "Go to second tab", {"tab_index": 1}),
            ("tab_third", "Ctrl+3", "go_to_tab", "Go to third tab", {"tab_index": 2}),
            ("tab_fourth", "Ctrl+4", "go_to_tab", "Go to fourth tab", {"tab_index": 3}),
            ("tab_fifth", "Ctrl+5", "go_to_tab", "Go to fifth tab", {"tab_index": 4}),
            ("tab_last", "Ctrl+9", "go_to_last_tab", "Go to last tab"),
        ]
        
        for shortcut_data in tab_shortcuts:
            shortcut_id, combo, action, desc = shortcut_data[:4]
            params = shortcut_data[4] if len(shortcut_data) > 4 else {}
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.TAB_MANAGEMENT, desc, params
            )
        
        # Search Shortcuts
        search_shortcuts = [
            ("search_page", "Ctrl+F", "find_in_page", "Find in current page"),
            ("search_next", "F3", "find_next", "Find next occurrence"),
            ("search_prev", "Shift+F3", "find_previous", "Find previous occurrence"),
            ("search_web", "Ctrl+K", "focus_search", "Focus web search"),
            ("search_web_alt", "Ctrl+E", "focus_search", "Focus web search"),
        ]
        
        for shortcut_id, combo, action, desc in search_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.SEARCH, desc
            )
        
        # AI Assistant Shortcuts
        ai_shortcuts = [
            ("ai_toggle", "Ctrl+Shift+A", "toggle_ai_assistant", "Toggle AI assistant panel"),
            ("ai_quick_chat", "Ctrl+Space", "quick_ai_chat", "Quick AI chat"),
            ("ai_summarize", "Ctrl+Shift+S", "ai_summarize_page", "Summarize current page"),
            ("ai_translate", "Ctrl+Shift+T", "ai_translate_page", "Translate current page"),
            ("ai_explain", "Ctrl+Shift+E", "ai_explain_selection", "Explain selected text"),
            ("ai_voice", "Ctrl+Shift+V", "toggle_voice_commands", "Toggle voice commands"),
        ]
        
        for shortcut_id, combo, action, desc in ai_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.AI_ASSISTANT, desc
            )
        
        # Automation Shortcuts
        automation_shortcuts = [
            ("auto_workflow", "Ctrl+Shift+W", "open_workflow_builder", "Open workflow builder"),
            ("auto_record", "Ctrl+Shift+R", "start_recording", "Start recording actions"),
            ("auto_stop_record", "Ctrl+Shift+X", "stop_recording", "Stop recording"),
            ("auto_quick_action", "Ctrl+Shift+Q", "quick_automation", "Quick automation menu"),
            ("auto_fill_form", "Ctrl+Shift+F", "auto_fill_form", "Auto-fill current form"),
        ]
        
        for shortcut_id, combo, action, desc in automation_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.AUTOMATION, desc
            )
        
        # Editing Shortcuts
        editing_shortcuts = [
            ("edit_select_all", "Ctrl+A", "select_all", "Select all content"),
            ("edit_copy", "Ctrl+C", "copy", "Copy selection"),
            ("edit_paste", "Ctrl+V", "paste", "Paste from clipboard"),
            ("edit_cut", "Ctrl+X", "cut", "Cut selection"),
            ("edit_undo", "Ctrl+Z", "undo", "Undo last action"),
            ("edit_redo", "Ctrl+Y", "redo", "Redo last action"),
            ("edit_redo_alt", "Ctrl+Shift+Z", "redo", "Redo last action"),
        ]
        
        for shortcut_id, combo, action, desc in editing_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.EDITING, desc
            )
        
        # Developer Shortcuts
        dev_shortcuts = [
            ("dev_tools", "F12", "toggle_dev_tools", "Toggle developer tools"),
            ("dev_tools_alt", "Ctrl+Shift+I", "toggle_dev_tools", "Toggle developer tools"),
            ("dev_console", "Ctrl+Shift+J", "open_console", "Open JavaScript console"),
            ("dev_elements", "Ctrl+Shift+C", "inspect_element", "Inspect element"),
            ("dev_network", "Ctrl+Shift+E", "open_network_tab", "Open network tab"),
            ("dev_sources", "Ctrl+Shift+O", "open_sources_tab", "Open sources tab"),
        ]
        
        for shortcut_id, combo, action, desc in dev_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.DEVELOPER, desc
            )
        
        # Accessibility Shortcuts
        accessibility_shortcuts = [
            ("acc_zoom_in", "Ctrl+Plus", "zoom_in", "Zoom in"),
            ("acc_zoom_out", "Ctrl+Minus", "zoom_out", "Zoom out"),
            ("acc_zoom_reset", "Ctrl+0", "reset_zoom", "Reset zoom level"),
            ("acc_full_screen", "F11", "toggle_fullscreen", "Toggle full screen"),
            ("acc_focus_next", "Tab", "focus_next_element", "Focus next element"),
            ("acc_focus_prev", "Shift+Tab", "focus_previous_element", "Focus previous element"),
            ("acc_high_contrast", "Ctrl+Shift+H", "toggle_high_contrast", "Toggle high contrast"),
            ("acc_read_page", "Ctrl+Shift+R", "read_page_aloud", "Read page aloud"),
        ]
        
        for shortcut_id, combo, action, desc in accessibility_shortcuts:
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.ACCESSIBILITY, desc
            )
        
        # Additional Power User Shortcuts
        power_shortcuts = [
            ("power_bookmark", "Ctrl+D", "bookmark_page", "Bookmark current page"),
            ("power_bookmarks", "Ctrl+Shift+B", "toggle_bookmarks_bar", "Toggle bookmarks bar"),
            ("power_history", "Ctrl+H", "open_history", "Open browsing history"),
            ("power_downloads", "Ctrl+J", "open_downloads", "Open downloads"),
            ("power_settings", "Ctrl+Comma", "open_settings", "Open settings"),
            ("power_incognito", "Ctrl+Shift+N", "new_incognito_tab", "Open incognito tab"),
            ("power_task_manager", "Shift+Esc", "open_task_manager", "Open task manager"),
            ("power_clear_data", "Ctrl+Shift+Delete", "clear_browsing_data", "Clear browsing data"),
        ]
        
        for shortcut_id, combo, action, desc in power_shortcuts:
            # These are general navigation, not a specific category
            shortcuts[shortcut_id] = KeyboardShortcut(
                shortcut_id, combo, action, ShortcutCategory.NAVIGATION, desc
            )
        
        return shortcuts
    
    def process_keyboard_shortcut(self, key_combination: str, user_session: str = None, 
                                 current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process keyboard shortcut and return action to execute"""
        
        try:
            # Normalize key combination
            normalized_combo = self._normalize_key_combination(key_combination)
            
            # Find matching shortcut
            matching_shortcut = self._find_matching_shortcut(normalized_combo, user_session)
            
            if not matching_shortcut:
                return {
                    "success": False,
                    "error": "Shortcut not recognized",
                    "key_combination": key_combination
                }
            
            # Check if shortcut is enabled
            if not matching_shortcut.enabled or matching_shortcut.shortcut_id in self.disabled_shortcuts:
                return {
                    "success": False,
                    "error": "Shortcut is disabled",
                    "shortcut": {
                        "id": matching_shortcut.shortcut_id,
                        "combination": matching_shortcut.combination,
                        "description": matching_shortcut.description
                    }
                }
            
            # Update usage statistics
            matching_shortcut.usage_count += 1
            matching_shortcut.last_used = datetime.utcnow()
            
            # Record in history
            self.shortcut_history.append({
                "shortcut_id": matching_shortcut.shortcut_id,
                "combination": key_combination,
                "user_session": user_session,
                "context": current_context,
                "timestamp": datetime.utcnow()
            })
            
            # Generate execution instructions
            execution_instructions = self._generate_shortcut_execution_instructions(
                matching_shortcut, current_context
            )
            
            return {
                "success": True,
                "shortcut": {
                    "id": matching_shortcut.shortcut_id,
                    "combination": matching_shortcut.combination,
                    "action": matching_shortcut.action,
                    "category": matching_shortcut.category.value,
                    "description": matching_shortcut.description,
                    "parameters": matching_shortcut.parameters
                },
                "execution_instructions": execution_instructions,
                "prevent_default": True  # Prevent browser default behavior
            }
            
        except Exception as e:
            logger.error(f"Keyboard shortcut processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "key_combination": key_combination
            }
    
    def _normalize_key_combination(self, combination: str) -> str:
        """Normalize key combination for consistent matching"""
        
        # Convert to standard format
        combo = combination.replace(" ", "").replace("+", "+")
        
        # Standardize modifier key names
        replacements = {
            "Control": "Ctrl",
            "Command": "Cmd", 
            "Shift": "Shift",
            "Alt": "Alt",
            "Meta": "Meta",
            "Option": "Alt"  # Mac
        }
        
        for old, new in replacements.items():
            combo = combo.replace(old, new)
        
        # Sort modifiers in consistent order: Ctrl, Alt, Shift, Meta
        parts = combo.split("+")
        modifiers = []
        key = ""
        
        modifier_order = ["Ctrl", "Alt", "Shift", "Meta", "Cmd"]
        
        for part in parts:
            if part in modifier_order:
                modifiers.append(part)
            else:
                key = part
        
        # Sort modifiers
        sorted_modifiers = [mod for mod in modifier_order if mod in modifiers]
        
        # Reconstruct combination
        if sorted_modifiers:
            return "+".join(sorted_modifiers) + "+" + key
        else:
            return key
    
    def _find_matching_shortcut(self, combination: str, user_session: str = None) -> Optional[KeyboardShortcut]:
        """Find shortcut matching the key combination"""
        
        # Check custom shortcuts first
        if user_session and user_session in self.custom_shortcuts:
            for shortcut in self.custom_shortcuts[user_session].values():
                if self._normalize_key_combination(shortcut.combination) == combination:
                    return shortcut
        
        # Check default shortcuts
        for shortcut in self.shortcuts.values():
            if self._normalize_key_combination(shortcut.combination) == combination:
                return shortcut
        
        return None
    
    def _generate_shortcut_execution_instructions(self, shortcut: KeyboardShortcut, 
                                               context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate execution instructions for the shortcut"""
        
        instructions = {
            "shortcut_id": shortcut.shortcut_id,
            "action_type": shortcut.action,
            "parameters": shortcut.parameters.copy(),
            "immediate_execution": True,
            "ui_feedback": False,  # Most shortcuts don't need UI feedback
            "steps": []
        }
        
        # Action-specific instructions
        if shortcut.action == "browser_back":
            instructions["steps"] = [{"action": "history_back"}]
            
        elif shortcut.action == "browser_forward":
            instructions["steps"] = [{"action": "history_forward"}]
            
        elif shortcut.action == "refresh_page":
            instructions["steps"] = [{"action": "page_reload"}]
            
        elif shortcut.action == "force_refresh":
            instructions["steps"] = [{"action": "page_reload", "bypass_cache": True}]
            
        elif shortcut.action == "new_tab":
            instructions["steps"] = [{"action": "tab_create"}]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "close_tab":
            instructions["steps"] = [{"action": "tab_close_current"}]
            
        elif shortcut.action == "focus_address_bar":
            instructions["steps"] = [{"action": "address_bar_focus", "select_all": True}]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "find_in_page":
            instructions["steps"] = [
                {"action": "show_find_bar", "animate": True},
                {"action": "focus_find_input"}
            ]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "toggle_ai_assistant":
            instructions["steps"] = [{"action": "toggle_ai_panel", "animate": True}]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "quick_ai_chat":
            instructions["steps"] = [
                {"action": "open_quick_ai_chat", "position": "center"},
                {"action": "focus_chat_input"}
            ]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "ai_summarize_page":
            instructions["steps"] = [
                {"action": "open_ai_assistant"},
                {"action": "populate_message", "message": "Please summarize this page"},
                {"action": "send_message", "auto_send": True}
            ]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "go_to_tab":
            tab_index = shortcut.parameters.get("tab_index", 0)
            instructions["steps"] = [{"action": "tab_switch", "index": tab_index}]
            
        elif shortcut.action == "zoom_in":
            instructions["steps"] = [{"action": "page_zoom", "direction": "in"}]
            
        elif shortcut.action == "zoom_out":
            instructions["steps"] = [{"action": "page_zoom", "direction": "out"}]
            
        elif shortcut.action == "reset_zoom":
            instructions["steps"] = [{"action": "page_zoom", "level": 1.0}]
            
        elif shortcut.action == "toggle_fullscreen":
            instructions["steps"] = [{"action": "browser_fullscreen_toggle"}]
            
        elif shortcut.action == "auto_fill_form":
            instructions["steps"] = [
                {"action": "detect_forms"},
                {"action": "auto_fill_detected_forms", "smart_fill": True}
            ]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "start_recording":
            instructions["steps"] = [
                {"action": "show_recording_indicator"},
                {"action": "start_automation_recording"}
            ]
            instructions["ui_feedback"] = True
            
        elif shortcut.action == "copy":
            instructions["steps"] = [{"action": "clipboard_copy"}]
            
        elif shortcut.action == "paste":
            instructions["steps"] = [{"action": "clipboard_paste"}]
            
        # Add context-aware modifications
        if context:
            current_page = context.get("current_page", {})
            
            # If on a form page, enhance form-related shortcuts
            if current_page.get("has_forms"):
                if shortcut.action == "auto_fill_form":
                    instructions["parameters"]["target_forms"] = current_page.get("form_selectors", [])
            
            # If text is selected, enhance text-related shortcuts
            if context.get("has_selection"):
                if shortcut.action == "ai_explain_selection":
                    instructions["parameters"]["selected_text"] = context.get("selected_text", "")
        
        return instructions
    
    def add_custom_shortcut(self, user_session: str, combination: str, action: str,
                          category: str, description: str, parameters: Dict[str, Any] = None) -> bool:
        """Add custom keyboard shortcut for user"""
        
        try:
            # Validate combination doesn't conflict
            if self._find_matching_shortcut(self._normalize_key_combination(combination), user_session):
                logger.warning(f"Shortcut combination {combination} already exists for user {user_session}")
                return False
            
            if user_session not in self.custom_shortcuts:
                self.custom_shortcuts[user_session] = {}
            
            shortcut_id = f"custom_{str(uuid.uuid4())[:8]}"
            
            custom_shortcut = KeyboardShortcut(
                shortcut_id=shortcut_id,
                combination=combination,
                action=action,
                category=ShortcutCategory(category),
                description=description,
                parameters=parameters or {}
            )
            
            self.custom_shortcuts[user_session][shortcut_id] = custom_shortcut
            
            logger.info(f"Custom shortcut {combination} -> {action} added for user {user_session}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom shortcut: {e}")
            return False
    
    def remove_custom_shortcut(self, user_session: str, shortcut_id: str) -> bool:
        """Remove custom shortcut"""
        
        try:
            if (user_session in self.custom_shortcuts and 
                shortcut_id in self.custom_shortcuts[user_session]):
                
                del self.custom_shortcuts[user_session][shortcut_id]
                logger.info(f"Custom shortcut {shortcut_id} removed for user {user_session}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove custom shortcut: {e}")
            return False
    
    def disable_shortcut(self, shortcut_id: str) -> bool:
        """Disable a shortcut"""
        self.disabled_shortcuts.add(shortcut_id)
        return True
    
    def enable_shortcut(self, shortcut_id: str) -> bool:
        """Enable a shortcut"""
        self.disabled_shortcuts.discard(shortcut_id)
        return True
    
    def get_shortcuts_by_category(self, category: ShortcutCategory = None, 
                                 user_session: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get shortcuts organized by category"""
        
        shortcuts_by_category = {}
        all_shortcuts = []
        
        # Add default shortcuts
        all_shortcuts.extend(self.shortcuts.values())
        
        # Add custom shortcuts for user
        if user_session and user_session in self.custom_shortcuts:
            all_shortcuts.extend(self.custom_shortcuts[user_session].values())
        
        # Filter by category if specified
        if category:
            all_shortcuts = [s for s in all_shortcuts if s.category == category]
        
        # Group by category
        for shortcut in all_shortcuts:
            cat_name = shortcut.category.value
            if cat_name not in shortcuts_by_category:
                shortcuts_by_category[cat_name] = []
            
            shortcuts_by_category[cat_name].append({
                "id": shortcut.shortcut_id,
                "combination": shortcut.combination,
                "action": shortcut.action,
                "description": shortcut.description,
                "enabled": shortcut.enabled and shortcut.shortcut_id not in self.disabled_shortcuts,
                "usage_count": shortcut.usage_count,
                "last_used": shortcut.last_used.isoformat() if shortcut.last_used else None,
                "custom": shortcut.shortcut_id.startswith("custom_")
            })
        
        return shortcuts_by_category
    
    def get_shortcut_suggestions(self, action: str) -> List[Dict[str, Any]]:
        """Get shortcut suggestions for an action"""
        
        suggestions = []
        
        for shortcut in self.shortcuts.values():
            if action.lower() in shortcut.action.lower() or action.lower() in shortcut.description.lower():
                suggestions.append({
                    "id": shortcut.shortcut_id,
                    "combination": shortcut.combination,
                    "action": shortcut.action,
                    "description": shortcut.description,
                    "category": shortcut.category.value
                })
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def get_usage_statistics(self, user_session: str = None) -> Dict[str, Any]:
        """Get keyboard shortcut usage statistics"""
        
        all_shortcuts = list(self.shortcuts.values())
        if user_session and user_session in self.custom_shortcuts:
            all_shortcuts.extend(self.custom_shortcuts[user_session].values())
        
        # Calculate statistics
        total_shortcuts = len(all_shortcuts)
        enabled_shortcuts = len([s for s in all_shortcuts if s.enabled and s.shortcut_id not in self.disabled_shortcuts])
        used_shortcuts = len([s for s in all_shortcuts if s.usage_count > 0])
        
        # Most used shortcuts
        most_used = sorted(all_shortcuts, key=lambda x: x.usage_count, reverse=True)[:10]
        
        # Category usage
        category_usage = {}
        for shortcut in all_shortcuts:
            cat = shortcut.category.value
            if cat not in category_usage:
                category_usage[cat] = {"count": 0, "usage": 0}
            category_usage[cat]["count"] += 1
            category_usage[cat]["usage"] += shortcut.usage_count
        
        return {
            "total_shortcuts": total_shortcuts,
            "enabled_shortcuts": enabled_shortcuts,
            "used_shortcuts": used_shortcuts,
            "usage_rate": used_shortcuts / total_shortcuts if total_shortcuts > 0 else 0,
            "most_used_shortcuts": [
                {
                    "id": s.shortcut_id,
                    "combination": s.combination,
                    "description": s.description,
                    "usage_count": s.usage_count,
                    "last_used": s.last_used.isoformat() if s.last_used else None
                }
                for s in most_used if s.usage_count > 0
            ],
            "category_usage": category_usage,
            "total_usage": sum(s.usage_count for s in all_shortcuts)
        }
    
    def export_shortcuts_config(self, user_session: str = None) -> Dict[str, Any]:
        """Export shortcuts configuration for backup/sync"""
        
        config = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "default_shortcuts": {},
            "custom_shortcuts": {},
            "disabled_shortcuts": list(self.disabled_shortcuts),
            "user_preferences": self.user_preferences.get(user_session, {}) if user_session else {}
        }
        
        # Export default shortcuts with modifications
        for shortcut_id, shortcut in self.shortcuts.items():
            config["default_shortcuts"][shortcut_id] = {
                "combination": shortcut.combination,
                "action": shortcut.action,
                "category": shortcut.category.value,
                "description": shortcut.description,
                "parameters": shortcut.parameters,
                "enabled": shortcut.enabled
            }
        
        # Export custom shortcuts
        if user_session and user_session in self.custom_shortcuts:
            for shortcut_id, shortcut in self.custom_shortcuts[user_session].items():
                config["custom_shortcuts"][shortcut_id] = {
                    "combination": shortcut.combination,
                    "action": shortcut.action,
                    "category": shortcut.category.value,
                    "description": shortcut.description,
                    "parameters": shortcut.parameters,
                    "enabled": shortcut.enabled
                }
        
        return config
    
    def import_shortcuts_config(self, config: Dict[str, Any], user_session: str) -> bool:
        """Import shortcuts configuration"""
        
        try:
            # Import custom shortcuts
            if "custom_shortcuts" in config:
                if user_session not in self.custom_shortcuts:
                    self.custom_shortcuts[user_session] = {}
                
                for shortcut_id, shortcut_data in config["custom_shortcuts"].items():
                    custom_shortcut = KeyboardShortcut(
                        shortcut_id=shortcut_id,
                        combination=shortcut_data["combination"],
                        action=shortcut_data["action"],
                        category=ShortcutCategory(shortcut_data["category"]),
                        description=shortcut_data["description"],
                        parameters=shortcut_data.get("parameters", {}),
                        enabled=shortcut_data.get("enabled", True)
                    )
                    self.custom_shortcuts[user_session][shortcut_id] = custom_shortcut
            
            # Import disabled shortcuts
            if "disabled_shortcuts" in config:
                self.disabled_shortcuts.update(config["disabled_shortcuts"])
            
            # Import user preferences
            if "user_preferences" in config:
                if user_session not in self.user_preferences:
                    self.user_preferences[user_session] = {}
                self.user_preferences[user_session].update(config["user_preferences"])
            
            logger.info(f"Shortcuts configuration imported for user {user_session}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import shortcuts configuration: {e}")
            return False

# Global instance
keyboard_shortcuts_engine = KeyboardShortcutsEngine()