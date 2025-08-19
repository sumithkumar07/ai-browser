# Split View Engine - Multi-Website Viewing System
# Critical Gap #3: Implement native split view browsing capabilities

import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pymongo import MongoClient
import asyncio

logger = logging.getLogger(__name__)

class SplitLayout(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    GRID_2X2 = "grid_2x2"
    GRID_3X1 = "grid_3x1"
    GRID_1X3 = "grid_1x3"
    PICTURE_IN_PICTURE = "pip"

class PaneStatus(Enum):
    ACTIVE = "active"
    LOADING = "loading"
    ERROR = "error"
    IDLE = "idle"

@dataclass
class SplitPane:
    """Individual pane in split view"""
    pane_id: str
    url: str
    title: str
    position: Tuple[int, int]  # Grid position (row, col)
    size: Tuple[float, float]  # Width/height as percentages
    status: PaneStatus
    last_updated: datetime
    security_status: str
    loading_time: float
    favicon: Optional[str] = None
    is_focused: bool = False

@dataclass
class SplitViewSession:
    """Complete split view session"""
    session_id: str
    user_session: str
    layout: SplitLayout
    panes: List[SplitPane]
    created_at: datetime
    last_activity: datetime
    total_panes: int
    active_pane: Optional[str]
    sync_navigation: bool = False  # Fellou.ai-style synchronized browsing

class SplitViewEngine:
    """Advanced split view engine for multi-website viewing (Fellou.ai capability)"""
    
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.aether_browser
        self.active_sessions: Dict[str, SplitViewSession] = {}
        
        # Layout configurations
        self.layout_configs = {
            SplitLayout.HORIZONTAL: {
                "max_panes": 2,
                "default_sizes": [(50, 100), (50, 100)],
                "positions": [(0, 0), (0, 1)]
            },
            SplitLayout.VERTICAL: {
                "max_panes": 2, 
                "default_sizes": [(100, 50), (100, 50)],
                "positions": [(0, 0), (1, 0)]
            },
            SplitLayout.GRID_2X2: {
                "max_panes": 4,
                "default_sizes": [(50, 50), (50, 50), (50, 50), (50, 50)],
                "positions": [(0, 0), (0, 1), (1, 0), (1, 1)]
            },
            SplitLayout.GRID_3X1: {
                "max_panes": 3,
                "default_sizes": [(33.33, 100), (33.33, 100), (33.33, 100)],
                "positions": [(0, 0), (0, 1), (0, 2)]
            },
            SplitLayout.GRID_1X3: {
                "max_panes": 3,
                "default_sizes": [(100, 33.33), (100, 33.33), (100, 33.33)],
                "positions": [(0, 0), (1, 0), (2, 0)]
            },
            SplitLayout.PICTURE_IN_PICTURE: {
                "max_panes": 2,
                "default_sizes": [(70, 70), (25, 25)],
                "positions": [(0, 0), (0, 1)]  # Main + floating overlay
            }
        }
    
    async def create_split_view_session(
        self, 
        user_session: str, 
        layout: str = "horizontal",
        initial_urls: Optional[List[str]] = None
    ) -> str:
        """Create new split view session"""
        
        session_id = str(uuid.uuid4())
        layout_enum = SplitLayout(layout)
        
        # Create initial panes
        panes = []
        if initial_urls:
            config = self.layout_configs[layout_enum]
            for i, url in enumerate(initial_urls[:config["max_panes"]]):
                pane = await self._create_pane(
                    url=url,
                    position=config["positions"][i],
                    size=config["default_sizes"][i]
                )
                panes.append(pane)
        
        session = SplitViewSession(
            session_id=session_id,
            user_session=user_session,
            layout=layout_enum,
            panes=panes,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            total_panes=len(panes),
            active_pane=panes[0].pane_id if panes else None,
            sync_navigation=False
        )
        
        # Store session
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        logger.info(f"🔲 Split view session created: {session_id} ({layout}) with {len(panes)} panes")
        
        return session_id
    
    async def add_pane_to_session(
        self, 
        session_id: str, 
        url: str,
        position: Optional[Tuple[int, int]] = None
    ) -> Optional[str]:
        """Add new pane to split view session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return None
        
        config = self.layout_configs[session.layout]
        
        # Check if we can add more panes
        if len(session.panes) >= config["max_panes"]:
            logger.warning(f"Cannot add pane: Maximum {config['max_panes']} panes for {session.layout.value}")
            return None
        
        # Determine position and size
        if not position:
            next_index = len(session.panes)
            position = config["positions"][next_index]
            size = config["default_sizes"][next_index]
        else:
            # Calculate size based on layout
            size = (50.0, 50.0)  # Default fallback
        
        # Create new pane
        pane = await self._create_pane(url, position, size)
        session.panes.append(pane)
        session.total_panes = len(session.panes)
        session.last_activity = datetime.utcnow()
        
        # Update active sessions and database
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        logger.info(f"➕ Pane added to split session {session_id}: {url}")
        
        return pane.pane_id
    
    async def navigate_pane(
        self, 
        session_id: str, 
        pane_id: str, 
        url: str,
        sync_all: bool = False
    ) -> bool:
        """Navigate specific pane to URL"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return False
        
        # Find and update pane
        pane_updated = False
        for pane in session.panes:
            if pane.pane_id == pane_id:
                pane.url = url
                pane.title = self._extract_domain_from_url(url)
                pane.status = PaneStatus.LOADING
                pane.last_updated = datetime.utcnow()
                pane.security_status = "secure" if url.startswith("https://") else "warning"
                pane_updated = True
                break
        
        if not pane_updated:
            return False
        
        # Fellou.ai-style synchronized navigation
        if sync_all or session.sync_navigation:
            for pane in session.panes:
                if pane.pane_id != pane_id:
                    pane.url = url
                    pane.title = self._extract_domain_from_url(url)
                    pane.status = PaneStatus.LOADING
                    pane.last_updated = datetime.utcnow()
        
        session.last_activity = datetime.utcnow()
        
        # Update sessions
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        logger.info(f"🌐 Pane navigation: {session_id}/{pane_id} → {url} (sync: {sync_all})")
        
        return True
    
    async def resize_pane(
        self, 
        session_id: str, 
        pane_id: str, 
        new_size: Tuple[float, float]
    ) -> bool:
        """Resize specific pane (drag to resize)"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return False
        
        # Update pane size
        for pane in session.panes:
            if pane.pane_id == pane_id:
                pane.size = new_size
                pane.last_updated = datetime.utcnow()
                break
        else:
            return False
        
        session.last_activity = datetime.utcnow()
        
        # Update sessions
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        return True
    
    async def change_layout(
        self, 
        session_id: str, 
        new_layout: str
    ) -> bool:
        """Change split view layout"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return False
        
        new_layout_enum = SplitLayout(new_layout)
        config = self.layout_configs[new_layout_enum]
        
        # Adjust panes to fit new layout
        if len(session.panes) > config["max_panes"]:
            # Remove excess panes
            session.panes = session.panes[:config["max_panes"]]
        
        # Update positions and sizes for new layout
        for i, pane in enumerate(session.panes):
            if i < len(config["positions"]):
                pane.position = config["positions"][i]
                pane.size = config["default_sizes"][i]
                pane.last_updated = datetime.utcnow()
        
        session.layout = new_layout_enum
        session.last_activity = datetime.utcnow()
        session.total_panes = len(session.panes)
        
        # Update sessions
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        logger.info(f"🔄 Layout changed for session {session_id}: {new_layout}")
        
        return True
    
    async def focus_pane(self, session_id: str, pane_id: str) -> bool:
        """Set focus on specific pane"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return False
        
        # Update focus states
        for pane in session.panes:
            pane.is_focused = (pane.pane_id == pane_id)
            if pane.is_focused:
                pane.last_updated = datetime.utcnow()
        
        session.active_pane = pane_id
        session.last_activity = datetime.utcnow()
        
        # Update sessions
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        return True
    
    async def close_pane(self, session_id: str, pane_id: str) -> bool:
        """Close specific pane"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return False
        
        # Don't close if it's the only pane
        if len(session.panes) <= 1:
            return False
        
        # Remove pane
        session.panes = [p for p in session.panes if p.pane_id != pane_id]
        session.total_panes = len(session.panes)
        
        # Update active pane if needed
        if session.active_pane == pane_id:
            session.active_pane = session.panes[0].pane_id if session.panes else None
        
        session.last_activity = datetime.utcnow()
        
        # Update sessions
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        logger.info(f"❌ Pane closed: {session_id}/{pane_id}")
        
        return True
    
    async def toggle_sync_navigation(self, session_id: str) -> bool:
        """Toggle synchronized navigation (Fellou.ai feature)"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return False
        
        session.sync_navigation = not session.sync_navigation
        session.last_activity = datetime.utcnow()
        
        # Update sessions
        self.active_sessions[session_id] = session
        await self._store_split_session(session)
        
        logger.info(f"🔗 Sync navigation toggled for {session_id}: {session.sync_navigation}")
        
        return session.sync_navigation
    
    async def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete session state for frontend"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            session = await self._load_split_session(session_id)
            if not session:
                return None
        
        return {
            "session_id": session.session_id,
            "layout": session.layout.value,
            "total_panes": session.total_panes,
            "active_pane": session.active_pane,
            "sync_navigation": session.sync_navigation,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "panes": [
                {
                    "pane_id": pane.pane_id,
                    "url": pane.url,
                    "title": pane.title,
                    "position": {"row": pane.position[0], "col": pane.position[1]},
                    "size": {"width": pane.size[0], "height": pane.size[1]},
                    "status": pane.status.value,
                    "security_status": pane.security_status,
                    "is_focused": pane.is_focused,
                    "favicon": pane.favicon,
                    "last_updated": pane.last_updated.isoformat()
                }
                for pane in session.panes
            ],
            "layout_config": {
                "max_panes": self.layout_configs[session.layout]["max_panes"],
                "available_layouts": [layout.value for layout in SplitLayout]
            }
        }
    
    async def list_user_sessions(self, user_session: str) -> List[Dict[str, Any]]:
        """List split view sessions for user"""
        
        try:
            sessions = list(self.db.split_view_sessions.find(
                {"user_session": user_session},
                {"_id": 0, "panes": 0}  # Exclude heavy pane data
            ).sort("last_activity", -1).limit(10))
            
            return sessions
        except Exception as e:
            logger.error(f"Error listing user split sessions: {e}")
            return []
    
    async def close_session(self, session_id: str) -> bool:
        """Close split view session"""
        
        try:
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Mark as closed in database
            self.db.split_view_sessions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "closed", "closed_at": datetime.utcnow()}}
            )
            
            logger.info(f"🔒 Split view session closed: {session_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error closing split session: {e}")
            return False
    
    async def _create_pane(
        self, 
        url: str, 
        position: Tuple[int, int], 
        size: Tuple[float, float]
    ) -> SplitPane:
        """Create new split pane"""
        
        pane_id = str(uuid.uuid4())
        
        return SplitPane(
            pane_id=pane_id,
            url=url,
            title=self._extract_domain_from_url(url),
            position=position,
            size=size,
            status=PaneStatus.LOADING,
            last_updated=datetime.utcnow(),
            security_status="secure" if url.startswith("https://") else "warning",
            loading_time=0.0,
            favicon=None,
            is_focused=False
        )
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain name from URL for title"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain if domain else 'New Tab'
        except:
            return 'New Tab'
    
    async def _load_split_session(self, session_id: str) -> Optional[SplitViewSession]:
        """Load split session from database"""
        try:
            data = self.db.split_view_sessions.find_one(
                {"session_id": session_id, "status": {"$ne": "closed"}}, 
                {"_id": 0}
            )
            if data:
                # Reconstruct pane objects
                data["panes"] = [SplitPane(**pane_data) for pane_data in data["panes"]]
                data["layout"] = SplitLayout(data["layout"])
                
                session = SplitViewSession(**data)
                self.active_sessions[session_id] = session
                return session
            return None
        except Exception as e:
            logger.error(f"Error loading split session: {e}")
            return None
    
    async def _store_split_session(self, session: SplitViewSession):
        """Store split session in database"""
        try:
            session_dict = asdict(session)
            session_dict["layout"] = session.layout.value
            session_dict["panes"] = [asdict(pane) for pane in session.panes]
            
            # Convert enums to strings for panes
            for pane_dict in session_dict["panes"]:
                pane_dict["status"] = pane_dict["status"].value if isinstance(pane_dict["status"], PaneStatus) else pane_dict["status"]
            
            self.db.split_view_sessions.update_one(
                {"session_id": session.session_id},
                {"$set": session_dict},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing split session: {e}")

# Global split view engine instance
split_view_engine: Optional[SplitViewEngine] = None

def initialize_split_view_engine(mongo_client: MongoClient) -> SplitViewEngine:
    """Initialize the global split view engine"""
    global split_view_engine
    split_view_engine = SplitViewEngine(mongo_client)
    return split_view_engine

def get_split_view_engine() -> Optional[SplitViewEngine]:
    """Get the global split view engine instance"""
    return split_view_engine