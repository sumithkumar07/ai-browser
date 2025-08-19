# Split View Engine - Multi-Webpage Viewing System
# Critical Gap #3: Fellou.ai-style multiple webpage viewing in single interface

import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)

class SplitLayout(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    GRID_2X2 = "grid_2x2"
    GRID_3X3 = "grid_3x3"
    CUSTOM = "custom"

class PaneStatus(Enum):
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    NAVIGATING = "navigating"
    READY = "ready"

@dataclass
class SplitPane:
    pane_id: str
    url: str
    title: str = "Loading..."
    position: Tuple[int, int] = (0, 0)  # Grid position (row, col)
    size: Tuple[float, float] = (1.0, 1.0)  # Size as fraction of container
    status: PaneStatus = PaneStatus.LOADING
    load_time: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    navigation_history: List[str] = field(default_factory=list)
    is_synchronized: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SplitViewSession:
    session_id: str
    user_session: str
    layout: SplitLayout
    panes: Dict[str, SplitPane] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    sync_navigation: bool = False
    custom_layout_config: Dict[str, Any] = field(default_factory=dict)

class SplitViewEngine:
    """
    Split View Engine provides multi-webpage viewing capabilities within a single browser interface.
    This addresses Fellou.ai's ability to view and interact with multiple websites simultaneously.
    """
    
    def __init__(self, mongo_client):
        self.db = mongo_client.aether_browser
        self.active_sessions: Dict[str, SplitViewSession] = {}
        self.max_panes_per_session = 9  # 3x3 grid max
        
        # Predefined layout configurations
        self.layout_configs = {
            SplitLayout.HORIZONTAL: {
                "max_panes": 2,
                "pane_positions": [(0, 0), (0, 1)],
                "pane_sizes": [(1.0, 0.5), (1.0, 0.5)]
            },
            SplitLayout.VERTICAL: {
                "max_panes": 2,
                "pane_positions": [(0, 0), (1, 0)],
                "pane_sizes": [(0.5, 1.0), (0.5, 1.0)]
            },
            SplitLayout.GRID_2X2: {
                "max_panes": 4,
                "pane_positions": [(0, 0), (0, 1), (1, 0), (1, 1)],
                "pane_sizes": [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5), (0.5, 0.5)]
            },
            SplitLayout.GRID_3X3: {
                "max_panes": 9,
                "pane_positions": [(i, j) for i in range(3) for j in range(3)],
                "pane_sizes": [(1/3, 1/3)] * 9
            }
        }
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_inactive_sessions())
        
        logger.info("🔲 Split View Engine initialized")
    
    async def create_split_view_session(
        self, 
        user_session: str,
        layout: str = "horizontal",
        initial_urls: Optional[List[str]] = None
    ) -> str:
        """Create a new split view session"""
        try:
            session_id = f"split_{uuid.uuid4()}"
            layout_enum = SplitLayout(layout)
            
            split_session = SplitViewSession(
                session_id=session_id,
                user_session=user_session,
                layout=layout_enum
            )
            
            # Add initial panes if URLs provided
            if initial_urls:
                layout_config = self.layout_configs.get(layout_enum, {})
                max_panes = layout_config.get("max_panes", 2)
                positions = layout_config.get("pane_positions", [(0, 0), (0, 1)])
                sizes = layout_config.get("pane_sizes", [(1.0, 0.5), (1.0, 0.5)])
                
                for i, url in enumerate(initial_urls[:max_panes]):
                    pane_id = await self._create_pane(
                        session_id=session_id,
                        url=url,
                        position=positions[i] if i < len(positions) else (0, 0),
                        size=sizes[i] if i < len(sizes) else (1.0, 1.0)
                    )
                    
                    pane = SplitPane(
                        pane_id=pane_id,
                        url=url,
                        position=positions[i] if i < len(positions) else (0, 0),
                        size=sizes[i] if i < len(sizes) else (1.0, 1.0),
                        navigation_history=[url]
                    )
                    
                    split_session.panes[pane_id] = pane
            
            # Store session
            self.active_sessions[session_id] = split_session
            await self._store_split_session(split_session)
            
            logger.info(f"🔲 Split view session created: {layout} with {len(initial_urls or [])} panes")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating split view session: {e}")
            raise
    
    async def add_pane_to_session(
        self, 
        session_id: str, 
        url: str,
        position: Optional[Tuple[int, int]] = None
    ) -> Optional[str]:
        """Add a new pane to existing split view session"""
        try:
            if session_id not in self.active_sessions:
                # Try to load from database
                await self._load_split_session(session_id)
                if session_id not in self.active_sessions:
                    return None
            
            session = self.active_sessions[session_id]
            
            # Check if we can add more panes
            max_panes = self.layout_configs.get(session.layout, {}).get("max_panes", 2)
            if len(session.panes) >= max_panes:
                logger.warning(f"Cannot add more panes to session {session_id}: limit reached")
                return None
            
            # Determine position
            if position is None:
                position = self._find_next_available_position(session)
            
            # Create pane
            pane_id = f"pane_{uuid.uuid4()}"
            pane = SplitPane(
                pane_id=pane_id,
                url=url,
                position=position,
                navigation_history=[url]
            )
            
            # Add to session
            session.panes[pane_id] = pane
            session.last_accessed = datetime.utcnow()
            
            # Update database
            await self._update_split_session(session)
            
            # Simulate pane loading
            asyncio.create_task(self._simulate_pane_loading(session_id, pane_id))
            
            logger.info(f"➕ Pane added to split view {session_id}: {url}")
            return pane_id
            
        except Exception as e:
            logger.error(f"Error adding pane to session: {e}")
            return None
    
    async def navigate_pane(
        self, 
        session_id: str, 
        pane_id: str, 
        url: str,
        sync_all: bool = False
    ) -> bool:
        """Navigate a specific pane to new URL"""
        try:
            if session_id not in self.active_sessions:
                await self._load_split_session(session_id)
                if session_id not in self.active_sessions:
                    return False
            
            session = self.active_sessions[session_id]
            
            if pane_id not in session.panes:
                logger.warning(f"Pane {pane_id} not found in session {session_id}")
                return False
            
            pane = session.panes[pane_id]
            
            # Update pane
            pane.url = url
            pane.status = PaneStatus.NAVIGATING
            pane.title = "Loading..."
            pane.navigation_history.append(url)
            pane.last_updated = datetime.utcnow()
            
            # Keep only last 20 history entries
            if len(pane.navigation_history) > 20:
                pane.navigation_history = pane.navigation_history[-20:]
            
            # Sync all panes if requested
            if sync_all:
                for other_pane in session.panes.values():
                    if other_pane.pane_id != pane_id:
                        other_pane.url = url
                        other_pane.status = PaneStatus.NAVIGATING
                        other_pane.title = "Loading..."
                        other_pane.navigation_history.append(url)
                        other_pane.last_updated = datetime.utcnow()
                        other_pane.is_synchronized = True
            
            session.last_accessed = datetime.utcnow()
            
            # Update database
            await self._update_split_session(session)
            
            # Simulate navigation
            asyncio.create_task(self._simulate_pane_navigation(session_id, pane_id, sync_all))
            
            logger.info(f"🌐 Pane navigation: {session_id}/{pane_id} -> {url} (sync: {sync_all})")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating pane: {e}")
            return False
    
    async def remove_pane(self, session_id: str, pane_id: str) -> bool:
        """Remove a pane from split view session"""
        try:
            if session_id not in self.active_sessions:
                await self._load_split_session(session_id)
                if session_id not in self.active_sessions:
                    return False
            
            session = self.active_sessions[session_id]
            
            if pane_id in session.panes:
                del session.panes[pane_id]
                session.last_accessed = datetime.utcnow()
                
                # Update database
                await self._update_split_session(session)
                
                logger.info(f"➖ Pane removed from split view {session_id}: {pane_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing pane: {e}")
            return False
    
    async def change_layout(self, session_id: str, new_layout: str) -> bool:
        """Change the layout of a split view session"""
        try:
            if session_id not in self.active_sessions:
                await self._load_split_session(session_id)
                if session_id not in self.active_sessions:
                    return False
            
            session = self.active_sessions[session_id]
            new_layout_enum = SplitLayout(new_layout)
            
            # Get new layout configuration
            new_config = self.layout_configs.get(new_layout_enum, {})
            max_panes = new_config.get("max_panes", 2)
            positions = new_config.get("pane_positions", [(0, 0)])
            sizes = new_config.get("pane_sizes", [(1.0, 1.0)])
            
            # Adjust existing panes to new layout
            panes_list = list(session.panes.values())
            
            # Remove excess panes if new layout has fewer slots
            if len(panes_list) > max_panes:
                for i in range(max_panes, len(panes_list)):
                    pane_to_remove = panes_list[i]
                    del session.panes[pane_to_remove.pane_id]
            
            # Update positions and sizes of remaining panes
            remaining_panes = list(session.panes.values())
            for i, pane in enumerate(remaining_panes):
                if i < len(positions):
                    pane.position = positions[i]
                    pane.size = sizes[i] if i < len(sizes) else (1.0, 1.0)
            
            session.layout = new_layout_enum
            session.last_accessed = datetime.utcnow()
            
            # Update database
            await self._update_split_session(session)
            
            logger.info(f"🔄 Split view layout changed: {session_id} -> {new_layout}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing layout: {e}")
            return False
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of split view session"""
        try:
            if session_id not in self.active_sessions:
                await self._load_split_session(session_id)
                if session_id not in self.active_sessions:
                    return None
            
            session = self.active_sessions[session_id]
            
            # Format panes data
            panes_data = []
            for pane in session.panes.values():
                panes_data.append({
                    "pane_id": pane.pane_id,
                    "url": pane.url,
                    "title": pane.title,
                    "position": {"row": pane.position[0], "col": pane.position[1]},
                    "size": {"width": pane.size[0], "height": pane.size[1]},
                    "status": pane.status.value,
                    "load_time": pane.load_time,
                    "last_updated": pane.last_updated.isoformat(),
                    "is_synchronized": pane.is_synchronized,
                    "navigation_history": pane.navigation_history[-5:]  # Last 5 entries
                })
            
            return {
                "session_id": session.session_id,
                "user_session": session.user_session,
                "layout": session.layout.value,
                "panes": panes_data,
                "created_at": session.created_at.isoformat(),
                "last_accessed": session.last_accessed.isoformat(),
                "is_active": session.is_active,
                "sync_navigation": session.sync_navigation,
                "pane_count": len(panes_data),
                "layout_info": self.layout_configs.get(session.layout, {})
            }
            
        except Exception as e:
            logger.error(f"Error getting session state: {e}")
            return None
    
    async def toggle_sync_navigation(self, session_id: str, enabled: bool) -> bool:
        """Toggle synchronized navigation for all panes"""
        try:
            if session_id not in self.active_sessions:
                await self._load_split_session(session_id)
                if session_id not in self.active_sessions:
                    return False
            
            session = self.active_sessions[session_id]
            session.sync_navigation = enabled
            session.last_accessed = datetime.utcnow()
            
            # Update all panes sync status
            for pane in session.panes.values():
                pane.is_synchronized = enabled
            
            await self._update_split_session(session)
            
            logger.info(f"🔄 Sync navigation {'enabled' if enabled else 'disabled'} for {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error toggling sync navigation: {e}")
            return False
    
    async def get_user_sessions(self, user_session: str) -> List[Dict[str, Any]]:
        """Get all split view sessions for a user"""
        try:
            user_sessions = []
            
            # From active sessions
            for session in self.active_sessions.values():
                if session.user_session == user_session:
                    user_sessions.append({
                        "session_id": session.session_id,
                        "layout": session.layout.value,
                        "pane_count": len(session.panes),
                        "created_at": session.created_at.isoformat(),
                        "last_accessed": session.last_accessed.isoformat(),
                        "is_active": session.is_active
                    })
            
            # From database (recent sessions)
            db_sessions = list(self.db.split_view_sessions.find(
                {
                    "user_session": user_session,
                    "is_active": True,
                    "last_accessed": {"$gte": datetime.utcnow() - timedelta(days=7)}
                },
                {"_id": 0, "panes_data": 0}  # Exclude large pane data
            ).sort("last_accessed", -1))
            
            # Merge and deduplicate
            session_ids = {s["session_id"] for s in user_sessions}
            for db_session in db_sessions:
                if db_session["session_id"] not in session_ids:
                    user_sessions.append({
                        "session_id": db_session["session_id"],
                        "layout": db_session["layout"],
                        "pane_count": len(db_session.get("panes_data", [])),
                        "created_at": db_session["created_at"].isoformat() if isinstance(db_session["created_at"], datetime) else db_session["created_at"],
                        "last_accessed": db_session["last_accessed"].isoformat() if isinstance(db_session["last_accessed"], datetime) else db_session["last_accessed"],
                        "is_active": db_session["is_active"]
                    })
            
            return user_sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    def _find_next_available_position(self, session: SplitViewSession) -> Tuple[int, int]:
        """Find next available position in the layout grid"""
        config = self.layout_configs.get(session.layout, {})
        available_positions = config.get("pane_positions", [(0, 0), (0, 1)])
        used_positions = {pane.position for pane in session.panes.values()}
        
        for pos in available_positions:
            if pos not in used_positions:
                return pos
        
        # If all positions used, return first one (shouldn't happen due to max_panes check)
        return available_positions[0] if available_positions else (0, 0)
    
    async def _create_pane(
        self, 
        session_id: str, 
        url: str,
        position: Tuple[int, int],
        size: Tuple[float, float]
    ) -> str:
        """Create a new pane ID"""
        return f"pane_{uuid.uuid4()}"
    
    async def _simulate_pane_loading(self, session_id: str, pane_id: str):
        """Simulate pane loading process"""
        try:
            await asyncio.sleep(2)  # Simulate loading time
            
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if pane_id in session.panes:
                    pane = session.panes[pane_id]
                    pane.status = PaneStatus.LOADED
                    pane.load_time = 2.0
                    pane.title = f"Page {pane_id[-8:]}"  # Use last 8 chars of ID as title
                    pane.last_updated = datetime.utcnow()
                    
                    await self._update_split_session(session)
                    
        except Exception as e:
            logger.error(f"Error simulating pane loading: {e}")
    
    async def _simulate_pane_navigation(self, session_id: str, pane_id: str, sync_all: bool):
        """Simulate pane navigation process"""
        try:
            await asyncio.sleep(1.5)  # Simulate navigation time
            
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                panes_to_update = [pane_id]
                if sync_all:
                    panes_to_update = list(session.panes.keys())
                
                for pid in panes_to_update:
                    if pid in session.panes:
                        pane = session.panes[pid]
                        pane.status = PaneStatus.READY
                        pane.load_time = 1.5
                        domain = pane.url.split('/')[2] if '://' in pane.url else pane.url
                        pane.title = f"{domain} - Page"
                        pane.last_updated = datetime.utcnow()
                
                await self._update_split_session(session)
                
        except Exception as e:
            logger.error(f"Error simulating pane navigation: {e}")
    
    async def _store_split_session(self, session: SplitViewSession):
        """Store split view session in database"""
        try:
            doc = {
                "session_id": session.session_id,
                "user_session": session.user_session,
                "layout": session.layout.value,
                "created_at": session.created_at,
                "last_accessed": session.last_accessed,
                "is_active": session.is_active,
                "sync_navigation": session.sync_navigation,
                "panes_data": []
            }
            
            # Store panes
            for pane in session.panes.values():
                doc["panes_data"].append({
                    "pane_id": pane.pane_id,
                    "url": pane.url,
                    "title": pane.title,
                    "position": list(pane.position),
                    "size": list(pane.size),
                    "status": pane.status.value,
                    "load_time": pane.load_time,
                    "last_updated": pane.last_updated,
                    "navigation_history": pane.navigation_history,
                    "is_synchronized": pane.is_synchronized,
                    "metadata": pane.metadata
                })
            
            self.db.split_view_sessions.insert_one(doc)
            
        except Exception as e:
            logger.error(f"Error storing split session: {e}")
    
    async def _update_split_session(self, session: SplitViewSession):
        """Update split view session in database"""
        try:
            session.last_accessed = datetime.utcnow()
            
            update_doc = {
                "last_accessed": session.last_accessed,
                "is_active": session.is_active,
                "sync_navigation": session.sync_navigation,
                "panes_data": []
            }
            
            # Update panes
            for pane in session.panes.values():
                update_doc["panes_data"].append({
                    "pane_id": pane.pane_id,
                    "url": pane.url,
                    "title": pane.title,
                    "position": list(pane.position),
                    "size": list(pane.size),
                    "status": pane.status.value,
                    "load_time": pane.load_time,
                    "last_updated": pane.last_updated,
                    "navigation_history": pane.navigation_history,
                    "is_synchronized": pane.is_synchronized,
                    "metadata": pane.metadata
                })
            
            self.db.split_view_sessions.update_one(
                {"session_id": session.session_id},
                {"$set": update_doc}
            )
            
        except Exception as e:
            logger.error(f"Error updating split session: {e}")
    
    async def _load_split_session(self, session_id: str):
        """Load split view session from database"""
        try:
            doc = self.db.split_view_sessions.find_one({"session_id": session_id})
            if not doc:
                return
            
            session = SplitViewSession(
                session_id=doc["session_id"],
                user_session=doc["user_session"],
                layout=SplitLayout(doc["layout"]),
                created_at=doc.get("created_at", datetime.utcnow()),
                last_accessed=doc.get("last_accessed", datetime.utcnow()),
                is_active=doc.get("is_active", True),
                sync_navigation=doc.get("sync_navigation", False)
            )
            
            # Load panes
            for pane_data in doc.get("panes_data", []):
                pane = SplitPane(
                    pane_id=pane_data["pane_id"],
                    url=pane_data["url"],
                    title=pane_data.get("title", "Loading..."),
                    position=tuple(pane_data["position"]),
                    size=tuple(pane_data["size"]),
                    status=PaneStatus(pane_data.get("status", "ready")),
                    load_time=pane_data.get("load_time", 0.0),
                    last_updated=pane_data.get("last_updated", datetime.utcnow()),
                    navigation_history=pane_data.get("navigation_history", []),
                    is_synchronized=pane_data.get("is_synchronized", False),
                    metadata=pane_data.get("metadata", {})
                )
                session.panes[pane.pane_id] = pane
            
            self.active_sessions[session_id] = session
            
        except Exception as e:
            logger.error(f"Error loading split session: {e}")
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive sessions periodically"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                inactive_sessions = []
                
                # Find inactive sessions
                for session_id, session in list(self.active_sessions.items()):
                    if session.last_accessed < cutoff_time:
                        inactive_sessions.append(session_id)
                
                # Remove from memory
                for session_id in inactive_sessions:
                    del self.active_sessions[session_id]
                
                # Mark as inactive in database
                if inactive_sessions:
                    self.db.split_view_sessions.update_many(
                        {"session_id": {"$in": inactive_sessions}},
                        {"$set": {"is_active": False}}
                    )
                
                logger.info(f"🧹 Cleaned up {len(inactive_sessions)} inactive split view sessions")
                
            except Exception as e:
                logger.error(f"Error in split view cleanup: {e}")

# Global split view engine instance
split_view_engine = None

def initialize_split_view_engine(mongo_client) -> SplitViewEngine:
    """Initialize the global split view engine"""
    global split_view_engine
    split_view_engine = SplitViewEngine(mongo_client)
    return split_view_engine

def get_split_view_engine() -> Optional[SplitViewEngine]:
    """Get the global split view engine instance"""
    return split_view_engine