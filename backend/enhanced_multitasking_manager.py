import asyncio
import uuid
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class WorkspaceType(Enum):
    PERSONAL = "personal"
    WORK = "work"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    PRODUCTIVITY = "productivity"
    ENTERTAINMENT = "entertainment"
    CUSTOM = "custom"

class TabGroupType(Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SMART = "smart"
    TEMPORARY = "temporary"

class LayoutType(Enum):
    SINGLE = "single"
    SPLIT_HORIZONTAL = "split_horizontal"
    SPLIT_VERTICAL = "split_vertical"
    GRID_2X2 = "grid_2x2"
    PICTURE_IN_PICTURE = "picture_in_picture"
    TABS = "tabs"

@dataclass
class BrowserTab:
    """Enhanced browser tab with workspace capabilities"""
    id: str
    url: str
    title: str
    user_session: str
    workspace_id: Optional[str] = None
    group_id: Optional[str] = None
    position: int = 0
    is_active: bool = False
    is_pinned: bool = False
    is_muted: bool = False
    favicon_url: Optional[str] = None
    last_accessed: datetime = None
    created_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TabGroup:
    """Group of related tabs"""
    id: str
    name: str
    user_session: str
    workspace_id: str
    group_type: TabGroupType
    color: str = "#4F46E5"
    description: str = ""
    tab_ids: List[str] = None
    auto_rules: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.tab_ids is None:
            self.tab_ids = []
        if self.auto_rules is None:
            self.auto_rules = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class Workspace:
    """Enhanced workspace for organizing browsing activities"""
    id: str
    name: str
    user_session: str
    workspace_type: WorkspaceType
    description: str = ""
    color: str = "#4F46E5"
    icon: str = "🌐"
    is_active: bool = False
    layout: LayoutType = LayoutType.TABS
    settings: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

class EnhancedMultitaskingManager:
    """Advanced multitasking management for workspaces, tab groups, and split views"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        
        # Collections
        self.workspaces = self.db.workspaces
        self.tabs = self.db.enhanced_tabs
        self.tab_groups = self.db.tab_groups
        self.layouts = self.db.workspace_layouts
        self.sessions = self.db.multitasking_sessions
        
        # In-memory state for real-time updates
        self.active_sessions = {}  # user_session -> workspace_state
        
        # Smart grouping rules
        self.grouping_rules = self._initialize_grouping_rules()
        
        # Background tasks
        self._optimization_task = None
    
    def start_multitasking_manager(self):
        """Start background multitasking optimization tasks"""
        if self._optimization_task is None:
            try:
                self._optimization_task = asyncio.create_task(self._background_optimization())
            except RuntimeError:
                pass
    
    def _initialize_grouping_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize smart tab grouping rules"""
        return {
            "domain_based": {
                "enabled": True,
                "weight": 0.8,
                "rules": {
                    "google.com": {"name": "Google Services", "color": "#4285F4"},
                    "github.com": {"name": "Development", "color": "#24292E"},
                    "stackoverflow.com": {"name": "Development", "color": "#F48024"},
                    "linkedin.com": {"name": "Professional", "color": "#0077B5"},
                    "youtube.com": {"name": "Media", "color": "#FF0000"},
                    "twitter.com": {"name": "Social", "color": "#1DA1F2"},
                    "facebook.com": {"name": "Social", "color": "#1877F2"}
                }
            },
            "content_type": {
                "enabled": True,
                "weight": 0.6,
                "patterns": {
                    "documentation": ["docs", "documentation", "guide", "tutorial"],
                    "social": ["social", "community", "forum", "chat"],
                    "productivity": ["dashboard", "admin", "manage", "settings"],
                    "development": ["api", "code", "repository", "pull", "commit"],
                    "research": ["research", "study", "analysis", "data", "report"]
                }
            },
            "temporal_based": {
                "enabled": True,
                "weight": 0.4,
                "time_window_minutes": 15
            }
        }
    
    # Workspace Management
    
    async def create_workspace(self, user_session: str, name: str, workspace_type: WorkspaceType, 
                              **kwargs) -> str:
        """Create a new workspace"""
        
        workspace_id = str(uuid.uuid4())
        
        workspace = Workspace(
            id=workspace_id,
            name=name,
            user_session=user_session,
            workspace_type=workspace_type,
            description=kwargs.get('description', ''),
            color=kwargs.get('color', self._get_workspace_default_color(workspace_type)),
            icon=kwargs.get('icon', self._get_workspace_default_icon(workspace_type)),
            layout=kwargs.get('layout', LayoutType.TABS),
            settings=kwargs.get('settings', {})
        )
        
        # Store in database
        workspace_doc = asdict(workspace)
        workspace_doc['workspace_type'] = workspace.workspace_type.value
        workspace_doc['layout'] = workspace.layout.value
        
        self.workspaces.insert_one(workspace_doc)
        
        logger.info(f"Created workspace {workspace_id}: {name}")
        return workspace_id
    
    async def get_workspaces(self, user_session: str) -> List[Dict[str, Any]]:
        """Get all workspaces for a user"""
        
        workspaces = list(self.workspaces.find(
            {"user_session": user_session},
            {"_id": 0}
        ).sort("updated_at", -1))
        
        # Convert timestamps and add tab counts
        for workspace in workspaces:
            workspace_id = workspace["id"]
            
            # Convert timestamps
            for time_field in ["created_at", "updated_at"]:
                if workspace.get(time_field):
                    workspace[time_field] = workspace[time_field].isoformat()
            
            # Add tab count
            tab_count = self.tabs.count_documents({
                "user_session": user_session,
                "workspace_id": workspace_id
            })
            workspace["tab_count"] = tab_count
            
            # Add group count
            group_count = self.tab_groups.count_documents({
                "user_session": user_session,
                "workspace_id": workspace_id
            })
            workspace["group_count"] = group_count
        
        return workspaces
    
    async def switch_workspace(self, user_session: str, workspace_id: str) -> Dict[str, Any]:
        """Switch to a different workspace"""
        
        # Deactivate current workspace
        self.workspaces.update_many(
            {"user_session": user_session, "is_active": True},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        # Activate new workspace
        result = self.workspaces.update_one(
            {"id": workspace_id, "user_session": user_session},
            {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Workspace {workspace_id} not found")
        
        # Get workspace details with tabs and groups
        workspace_details = await self.get_workspace_details(user_session, workspace_id)
        
        logger.info(f"Switched to workspace {workspace_id}")
        return workspace_details
    
    async def get_workspace_details(self, user_session: str, workspace_id: str) -> Dict[str, Any]:
        """Get detailed workspace information"""
        
        workspace = self.workspaces.find_one(
            {"id": workspace_id, "user_session": user_session},
            {"_id": 0}
        )
        
        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")
        
        # Convert timestamps
        for time_field in ["created_at", "updated_at"]:
            if workspace.get(time_field):
                workspace[time_field] = workspace[time_field].isoformat()
        
        # Get tabs in workspace
        tabs = await self.get_workspace_tabs(user_session, workspace_id)
        
        # Get tab groups in workspace
        groups = await self.get_workspace_tab_groups(user_session, workspace_id)
        
        # Get layout information
        layout_info = await self.get_workspace_layout(user_session, workspace_id)
        
        return {
            **workspace,
            "tabs": tabs,
            "groups": groups,
            "layout_info": layout_info
        }
    
    # Tab Management
    
    async def create_tab(self, user_session: str, url: str, title: str, 
                        workspace_id: str = None, **kwargs) -> str:
        """Create a new enhanced tab"""
        
        tab_id = str(uuid.uuid4())
        
        # Get or create default workspace if not specified
        if not workspace_id:
            workspace_id = await self._get_or_create_default_workspace(user_session)
        
        tab = BrowserTab(
            id=tab_id,
            url=url,
            title=title,
            user_session=user_session,
            workspace_id=workspace_id,
            group_id=kwargs.get('group_id'),
            position=kwargs.get('position', 0),
            is_pinned=kwargs.get('is_pinned', False),
            favicon_url=kwargs.get('favicon_url'),
            metadata=kwargs.get('metadata', {})
        )
        
        # Store in database
        tab_doc = asdict(tab)
        
        self.tabs.insert_one(tab_doc)
        
        # Auto-group tab if smart grouping is enabled
        await self._auto_group_tab(user_session, tab_id, url, title)
        
        # Update workspace
        self.workspaces.update_one(
            {"id": workspace_id, "user_session": user_session},
            {"$set": {"updated_at": datetime.utcnow()}}
        )
        
        logger.info(f"Created tab {tab_id} in workspace {workspace_id}")
        return tab_id
    
    async def get_workspace_tabs(self, user_session: str, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all tabs in a workspace"""
        
        tabs = list(self.tabs.find(
            {"user_session": user_session, "workspace_id": workspace_id},
            {"_id": 0}
        ).sort("position", 1))
        
        # Convert timestamps
        for tab in tabs:
            for time_field in ["last_accessed", "created_at"]:
                if tab.get(time_field):
                    tab[time_field] = tab[time_field].isoformat()
        
        return tabs
    
    async def move_tab_to_workspace(self, user_session: str, tab_id: str, 
                                   target_workspace_id: str) -> bool:
        """Move a tab to a different workspace"""
        
        result = self.tabs.update_one(
            {"id": tab_id, "user_session": user_session},
            {
                "$set": {
                    "workspace_id": target_workspace_id,
                    "group_id": None,  # Remove from current group
                    "last_accessed": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count > 0:
            # Update workspace timestamps
            self.workspaces.update_one(
                {"id": target_workspace_id, "user_session": user_session},
                {"$set": {"updated_at": datetime.utcnow()}}
            )
            
            logger.info(f"Moved tab {tab_id} to workspace {target_workspace_id}")
            return True
        
        return False
    
    # Tab Group Management
    
    async def create_tab_group(self, user_session: str, workspace_id: str, name: str, 
                              tab_ids: List[str] = None, **kwargs) -> str:
        """Create a new tab group"""
        
        group_id = str(uuid.uuid4())
        
        group = TabGroup(
            id=group_id,
            name=name,
            user_session=user_session,
            workspace_id=workspace_id,
            group_type=kwargs.get('group_type', TabGroupType.MANUAL),
            color=kwargs.get('color', '#4F46E5'),
            description=kwargs.get('description', ''),
            tab_ids=tab_ids or [],
            auto_rules=kwargs.get('auto_rules', {})
        )
        
        # Store in database
        group_doc = asdict(group)
        group_doc['group_type'] = group.group_type.value
        
        self.tab_groups.insert_one(group_doc)
        
        # Update tabs to belong to this group
        if tab_ids:
            self.tabs.update_many(
                {"id": {"$in": tab_ids}, "user_session": user_session},
                {"$set": {"group_id": group_id}}
            )
        
        logger.info(f"Created tab group {group_id}: {name} with {len(tab_ids or [])} tabs")
        return group_id
    
    async def get_workspace_tab_groups(self, user_session: str, workspace_id: str) -> List[Dict[str, Any]]:
        """Get all tab groups in a workspace"""
        
        groups = list(self.tab_groups.find(
            {"user_session": user_session, "workspace_id": workspace_id},
            {"_id": 0}
        ).sort("updated_at", -1))
        
        # Convert timestamps and add tab details
        for group in groups:
            for time_field in ["created_at", "updated_at"]:
                if group.get(time_field):
                    group[time_field] = group[time_field].isoformat()
            
            # Get tab count and preview
            tab_count = len(group.get("tab_ids", []))
            group["tab_count"] = tab_count
            
            if group.get("tab_ids"):
                # Get preview of first few tabs
                preview_tabs = list(self.tabs.find(
                    {"id": {"$in": group["tab_ids"][:3]}, "user_session": user_session},
                    {"title": 1, "url": 1, "favicon_url": 1, "_id": 0}
                ))
                group["tab_preview"] = preview_tabs
        
        return groups
    
    async def add_tabs_to_group(self, user_session: str, group_id: str, tab_ids: List[str]) -> bool:
        """Add tabs to an existing group"""
        
        # Update group with new tab IDs
        result = self.tab_groups.update_one(
            {"id": group_id, "user_session": user_session},
            {
                "$addToSet": {"tab_ids": {"$each": tab_ids}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        if result.matched_count > 0:
            # Update tabs to belong to this group
            self.tabs.update_many(
                {"id": {"$in": tab_ids}, "user_session": user_session},
                {"$set": {"group_id": group_id}}
            )
            
            logger.info(f"Added {len(tab_ids)} tabs to group {group_id}")
            return True
        
        return False
    
    # Layout Management
    
    async def set_workspace_layout(self, user_session: str, workspace_id: str, 
                                  layout_type: LayoutType, layout_config: Dict[str, Any] = None) -> bool:
        """Set workspace layout"""
        
        # Update workspace layout
        result = self.workspaces.update_one(
            {"id": workspace_id, "user_session": user_session},
            {
                "$set": {
                    "layout": layout_type.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count > 0:
            # Store detailed layout configuration
            layout_doc = {
                "workspace_id": workspace_id,
                "user_session": user_session,
                "layout_type": layout_type.value,
                "config": layout_config or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            self.layouts.replace_one(
                {"workspace_id": workspace_id, "user_session": user_session},
                layout_doc,
                upsert=True
            )
            
            logger.info(f"Set workspace {workspace_id} layout to {layout_type.value}")
            return True
        
        return False
    
    async def get_workspace_layout(self, user_session: str, workspace_id: str) -> Dict[str, Any]:
        """Get workspace layout configuration"""
        
        layout = self.layouts.find_one(
            {"workspace_id": workspace_id, "user_session": user_session},
            {"_id": 0}
        )
        
        if layout:
            # Convert timestamps
            for time_field in ["created_at", "updated_at"]:
                if layout.get(time_field):
                    layout[time_field] = layout[time_field].isoformat()
        
        return layout or {
            "layout_type": "tabs",
            "config": {}
        }
    
    # Smart Automation Features
    
    async def _auto_group_tab(self, user_session: str, tab_id: str, url: str, title: str):
        """Automatically group tab based on smart rules"""
        
        try:
            # Get tab details
            tab = self.tabs.find_one({"id": tab_id, "user_session": user_session})
            if not tab or tab.get("group_id"):
                return  # Already grouped
            
            workspace_id = tab["workspace_id"]
            
            # Try domain-based grouping
            domain = self._extract_domain(url)
            domain_rules = self.grouping_rules["domain_based"]["rules"]
            
            if domain in domain_rules:
                rule = domain_rules[domain]
                group_name = rule["name"]
                
                # Find existing group or create new one
                existing_group = self.tab_groups.find_one({
                    "user_session": user_session,
                    "workspace_id": workspace_id,
                    "name": group_name,
                    "group_type": TabGroupType.AUTOMATIC.value
                })
                
                if existing_group:
                    group_id = existing_group["id"]
                else:
                    group_id = await self.create_tab_group(
                        user_session=user_session,
                        workspace_id=workspace_id,
                        name=group_name,
                        tab_ids=[],
                        group_type=TabGroupType.AUTOMATIC,
                        color=rule["color"],
                        auto_rules={"domain": domain}
                    )
                
                # Add tab to group
                await self.add_tabs_to_group(user_session, group_id, [tab_id])
                
                logger.info(f"Auto-grouped tab {tab_id} into {group_name}")
                return
            
            # Try content-type grouping
            content_patterns = self.grouping_rules["content_type"]["patterns"]
            
            for category, keywords in content_patterns.items():
                if any(keyword in url.lower() or keyword in title.lower() for keyword in keywords):
                    group_name = category.title()
                    
                    existing_group = self.tab_groups.find_one({
                        "user_session": user_session,
                        "workspace_id": workspace_id,
                        "name": group_name,
                        "group_type": TabGroupType.AUTOMATIC.value
                    })
                    
                    if existing_group:
                        group_id = existing_group["id"]
                    else:
                        group_id = await self.create_tab_group(
                            user_session=user_session,
                            workspace_id=workspace_id,
                            name=group_name,
                            tab_ids=[],
                            group_type=TabGroupType.AUTOMATIC,
                            auto_rules={"content_type": category}
                        )
                    
                    await self.add_tabs_to_group(user_session, group_id, [tab_id])
                    logger.info(f"Auto-grouped tab {tab_id} into {group_name} (content-based)")
                    return
        
        except Exception as e:
            logger.error(f"Auto-grouping error for tab {tab_id}: {e}")
    
    async def suggest_workspace_optimization(self, user_session: str, workspace_id: str) -> Dict[str, Any]:
        """Suggest workspace optimizations"""
        
        suggestions = {
            "grouping_suggestions": [],
            "layout_suggestions": [],
            "cleanup_suggestions": [],
            "productivity_tips": []
        }
        
        # Get workspace tabs
        tabs = await self.get_workspace_tabs(user_session, workspace_id)
        
        if len(tabs) == 0:
            return suggestions
        
        # Grouping suggestions
        ungrouped_tabs = [tab for tab in tabs if not tab.get("group_id")]
        if len(ungrouped_tabs) > 3:
            domain_clusters = {}
            for tab in ungrouped_tabs:
                domain = self._extract_domain(tab["url"])
                if domain not in domain_clusters:
                    domain_clusters[domain] = []
                domain_clusters[domain].append(tab)
            
            for domain, domain_tabs in domain_clusters.items():
                if len(domain_tabs) > 1:
                    suggestions["grouping_suggestions"].append({
                        "type": "domain_grouping",
                        "domain": domain,
                        "tab_count": len(domain_tabs),
                        "suggestion": f"Group {len(domain_tabs)} tabs from {domain}",
                        "tab_ids": [tab["id"] for tab in domain_tabs]
                    })
        
        # Layout suggestions
        if len(tabs) > 6:
            suggestions["layout_suggestions"].append({
                "type": "split_view",
                "suggestion": "Consider using split view for better multitasking",
                "reason": f"You have {len(tabs)} tabs open"
            })
        
        # Cleanup suggestions
        old_tabs = [
            tab for tab in tabs 
            if tab.get("last_accessed") and 
            datetime.fromisoformat(tab["last_accessed"].replace('Z', '+00:00')) < datetime.utcnow() - timedelta(days=7)
        ]
        
        if len(old_tabs) > 0:
            suggestions["cleanup_suggestions"].append({
                "type": "old_tabs",
                "tab_count": len(old_tabs),
                "suggestion": f"Consider closing {len(old_tabs)} tabs not accessed in 7+ days",
                "tab_ids": [tab["id"] for tab in old_tabs]
            })
        
        return suggestions
    
    async def _background_optimization(self):
        """Background optimization and maintenance"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                
                # Clean up old temporary groups
                await self._cleanup_temporary_groups()
                
                # Update smart group memberships
                await self._update_smart_groups()
                
                # Generate workspace analytics
                await self._generate_workspace_analytics()
                
            except Exception as e:
                logger.error(f"Multitasking optimization error: {e}")
    
    async def _cleanup_temporary_groups(self):
        """Clean up temporary and empty groups"""
        
        # Remove temporary groups older than 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        temp_groups = list(self.tab_groups.find({
            "group_type": TabGroupType.TEMPORARY.value,
            "created_at": {"$lt": cutoff_time}
        }))
        
        for group in temp_groups:
            # Remove group reference from tabs
            self.tabs.update_many(
                {"group_id": group["id"]},
                {"$unset": {"group_id": ""}}
            )
            
            # Delete group
            self.tab_groups.delete_one({"_id": group["_id"]})
        
        # Remove empty groups
        empty_groups = list(self.tab_groups.find())
        
        for group in empty_groups:
            tab_count = self.tabs.count_documents({"group_id": group["id"]})
            if tab_count == 0:
                self.tab_groups.delete_one({"_id": group["_id"]})
                logger.info(f"Cleaned up empty group: {group['name']}")
    
    async def _update_smart_groups(self):
        """Update smart group memberships based on rules"""
        
        smart_groups = list(self.tab_groups.find({
            "group_type": TabGroupType.AUTOMATIC.value,
            "auto_rules": {"$exists": True}
        }))
        
        for group in smart_groups:
            auto_rules = group.get("auto_rules", {})
            
            if "domain" in auto_rules:
                domain = auto_rules["domain"]
                
                # Find tabs matching the domain
                matching_tabs = list(self.tabs.find({
                    "user_session": group["user_session"],
                    "workspace_id": group["workspace_id"],
                    "url": {"$regex": domain, "$options": "i"},
                    "group_id": {"$ne": group["id"]}
                }))
                
                # Add matching tabs to group
                if matching_tabs:
                    tab_ids = [tab["id"] for tab in matching_tabs]
                    await self.add_tabs_to_group(group["user_session"], group["id"], tab_ids)
    
    async def _generate_workspace_analytics(self):
        """Generate analytics for workspace usage"""
        
        # Get unique users with recent activity
        recent_time = datetime.utcnow() - timedelta(days=1)
        
        active_users = self.tabs.distinct("user_session", {
            "last_accessed": {"$gte": recent_time}
        })
        
        for user_session in active_users:
            user_workspaces = list(self.workspaces.find({"user_session": user_session}))
            
            analytics = {
                "user_session": user_session,
                "generated_at": datetime.utcnow(),
                "workspace_count": len(user_workspaces),
                "total_tabs": 0,
                "total_groups": 0,
                "most_used_workspace": None,
                "productivity_metrics": {}
            }
            
            workspace_usage = {}
            
            for workspace in user_workspaces:
                workspace_id = workspace["id"]
                tab_count = self.tabs.count_documents({
                    "user_session": user_session,
                    "workspace_id": workspace_id
                })
                
                group_count = self.tab_groups.count_documents({
                    "user_session": user_session,
                    "workspace_id": workspace_id
                })
                
                analytics["total_tabs"] += tab_count
                analytics["total_groups"] += group_count
                
                workspace_usage[workspace_id] = {
                    "name": workspace["name"],
                    "tab_count": tab_count,
                    "group_count": group_count
                }
            
            # Find most used workspace
            if workspace_usage:
                most_used = max(workspace_usage.items(), key=lambda x: x[1]["tab_count"])
                analytics["most_used_workspace"] = {
                    "id": most_used[0],
                    "name": most_used[1]["name"],
                    "tab_count": most_used[1]["tab_count"]
                }
            
            # Store analytics
            self.sessions.replace_one(
                {"user_session": user_session},
                analytics,
                upsert=True
            )
    
    # Helper methods
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or parsed.path.split('/')[0]
        except:
            return url
    
    def _get_workspace_default_color(self, workspace_type: WorkspaceType) -> str:
        """Get default color for workspace type"""
        color_map = {
            WorkspaceType.PERSONAL: "#6B7280",
            WorkspaceType.WORK: "#3B82F6",
            WorkspaceType.RESEARCH: "#8B5CF6",
            WorkspaceType.DEVELOPMENT: "#10B981",
            WorkspaceType.PRODUCTIVITY: "#F59E0B",
            WorkspaceType.ENTERTAINMENT: "#EF4444",
            WorkspaceType.CUSTOM: "#4F46E5"
        }
        return color_map.get(workspace_type, "#4F46E5")
    
    def _get_workspace_default_icon(self, workspace_type: WorkspaceType) -> str:
        """Get default icon for workspace type"""
        icon_map = {
            WorkspaceType.PERSONAL: "🏠",
            WorkspaceType.WORK: "💼",
            WorkspaceType.RESEARCH: "🔬",
            WorkspaceType.DEVELOPMENT: "💻",
            WorkspaceType.PRODUCTIVITY: "📊",
            WorkspaceType.ENTERTAINMENT: "🎮",
            WorkspaceType.CUSTOM: "⭐"
        }
        return icon_map.get(workspace_type, "🌐")
    
    async def _get_or_create_default_workspace(self, user_session: str) -> str:
        """Get or create default workspace for user"""
        
        default_workspace = self.workspaces.find_one({
            "user_session": user_session,
            "name": "Default"
        })
        
        if default_workspace:
            return default_workspace["id"]
        
        # Create default workspace
        return await self.create_workspace(
            user_session=user_session,
            name="Default",
            workspace_type=WorkspaceType.PERSONAL,
            description="Default workspace for general browsing",
            is_active=True
        )

# Global multitasking manager instance
enhanced_multitasking_manager = None  # Will be initialized in server.py