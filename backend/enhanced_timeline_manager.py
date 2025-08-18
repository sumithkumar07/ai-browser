import asyncio
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class TimelineEventType(Enum):
    BROWSING = "browsing"
    CHAT = "chat"
    AUTOMATION = "automation"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    SEARCH = "search"
    BOOKMARK = "bookmark"
    DOWNLOAD = "download"
    FORM_FILL = "form_fill"

class TimelineEventPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TimelineEvent:
    """Represents a single event in the user's activity timeline"""
    id: str
    user_session: str
    event_type: TimelineEventType
    title: str
    description: str
    url: Optional[str] = None
    metadata: Dict[str, Any] = None
    priority: TimelineEventPriority = TimelineEventPriority.MEDIUM
    duration_ms: int = 0
    tags: List[str] = None
    related_events: List[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []
        if self.related_events is None:
            self.related_events = []

class EnhancedTimelineManager:
    """Advanced timeline management for tracking and visualizing user activities"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        
        # Collections
        self.timeline_events = self.db.timeline_events
        self.timeline_sessions = self.db.timeline_sessions
        self.timeline_analytics = self.db.timeline_analytics
        
        # In-memory event buffer for real-time updates
        self.event_buffer = []
        self.buffer_size = 100
        
        # Background tasks
        self._analytics_task = None
        
    def start_timeline_manager(self):
        """Start background timeline management tasks"""
        if self._analytics_task is None:
            try:
                self._analytics_task = asyncio.create_task(self._background_analytics())
            except RuntimeError:
                pass
    
    async def record_event(self, user_session: str, event_type: TimelineEventType, 
                          title: str, description: str, **kwargs) -> str:
        """Record a new timeline event"""
        
        event_id = str(uuid.uuid4())
        
        event = TimelineEvent(
            id=event_id,
            user_session=user_session,
            event_type=event_type,
            title=title,
            description=description,
            url=kwargs.get('url'),
            metadata=kwargs.get('metadata', {}),
            priority=kwargs.get('priority', TimelineEventPriority.MEDIUM),
            duration_ms=kwargs.get('duration_ms', 0),
            tags=kwargs.get('tags', []),
            related_events=kwargs.get('related_events', [])
        )
        
        # Store in database
        event_doc = asdict(event)
        event_doc['timestamp'] = event.timestamp
        event_doc['event_type'] = event.event_type.value
        event_doc['priority'] = event.priority.value
        
        self.timeline_events.insert_one(event_doc)
        
        # Add to buffer for real-time updates
        self.event_buffer.append(event_doc)
        if len(self.event_buffer) > self.buffer_size:
            self.event_buffer.pop(0)
        
        logger.info(f"Recorded timeline event {event_id}: {title}")
        return event_id
    
    async def get_timeline(self, user_session: str, start_time: datetime = None, 
                          end_time: datetime = None, event_types: List[str] = None, 
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Get timeline events for a user session"""
        
        # Build query
        query = {"user_session": user_session}
        
        if start_time or end_time:
            time_query = {}
            if start_time:
                time_query["$gte"] = start_time
            if end_time:
                time_query["$lte"] = end_time
            query["timestamp"] = time_query
        
        if event_types:
            query["event_type"] = {"$in": event_types}
        
        # Get events
        events = list(self.timeline_events.find(
            query, {"_id": 0}
        ).sort("timestamp", -1).limit(limit))
        
        # Convert timestamps to ISO format
        for event in events:
            if event.get("timestamp"):
                event["timestamp"] = event["timestamp"].isoformat()
        
        return events
    
    async def get_timeline_summary(self, user_session: str, 
                                  period: str = "today") -> Dict[str, Any]:
        """Get timeline summary for different time periods"""
        
        # Calculate time range
        now = datetime.utcnow()
        if period == "today":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_time = now - timedelta(days=7)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)
        
        # Get events in period
        events = await self.get_timeline(user_session, start_time=start_time, limit=1000)
        
        # Analyze events
        summary = {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "total_events": len(events),
            "event_breakdown": {},
            "activity_pattern": {},
            "top_websites": {},
            "productivity_score": 0,
            "highlights": []
        }
        
        # Event type breakdown
        for event in events:
            event_type = event.get("event_type", "unknown")
            summary["event_breakdown"][event_type] = summary["event_breakdown"].get(event_type, 0) + 1
        
        # Activity pattern (events per hour)
        activity_hours = {}
        for event in events:
            if event.get("timestamp"):
                try:
                    event_time = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
                    hour = event_time.hour
                    activity_hours[hour] = activity_hours.get(hour, 0) + 1
                except:
                    pass
        
        summary["activity_pattern"] = activity_hours
        
        # Top websites
        website_counts = {}
        for event in events:
            url = event.get("url")
            if url:
                domain = self._extract_domain(url)
                website_counts[domain] = website_counts.get(domain, 0) + 1
        
        summary["top_websites"] = dict(sorted(website_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Productivity score (simplified calculation)
        productive_events = sum(1 for event in events if event.get("event_type") in ["automation", "workflow", "integration"])
        total_browsing = sum(1 for event in events if event.get("event_type") == "browsing")
        
        if total_browsing > 0:
            summary["productivity_score"] = min((productive_events / total_browsing) * 100, 100)
        
        # Highlights (significant events)
        highlights = []
        for event in events:
            if event.get("priority") == "high" or event.get("duration_ms", 0) > 300000:  # 5+ minutes
                highlights.append({
                    "id": event["id"],
                    "title": event["title"],
                    "timestamp": event["timestamp"],
                    "type": event["event_type"]
                })
        
        summary["highlights"] = highlights[:5]  # Top 5 highlights
        
        return summary
    
    async def search_timeline(self, user_session: str, query: str, 
                             event_types: List[str] = None) -> List[Dict[str, Any]]:
        """Search timeline events"""
        
        # Build search query
        search_conditions = [
            {"user_session": user_session}
        ]
        
        # Text search in title and description
        text_search = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"url": {"$regex": query, "$options": "i"}}
            ]
        }
        search_conditions.append(text_search)
        
        # Event type filter
        if event_types:
            search_conditions.append({"event_type": {"$in": event_types}})
        
        final_query = {"$and": search_conditions}
        
        # Execute search
        results = list(self.timeline_events.find(
            final_query, {"_id": 0}
        ).sort("timestamp", -1).limit(100))
        
        # Convert timestamps
        for result in results:
            if result.get("timestamp"):
                result["timestamp"] = result["timestamp"].isoformat()
        
        return results
    
    async def get_related_events(self, event_id: str, user_session: str) -> List[Dict[str, Any]]:
        """Get events related to a specific event"""
        
        # Get the target event
        target_event = self.timeline_events.find_one({"id": event_id, "user_session": user_session})
        if not target_event:
            return []
        
        related_events = []
        
        # Find explicitly related events
        if target_event.get("related_events"):
            explicit_related = list(self.timeline_events.find(
                {"id": {"$in": target_event["related_events"]}, "user_session": user_session},
                {"_id": 0}
            ))
            related_events.extend(explicit_related)
        
        # Find events with same URL
        if target_event.get("url"):
            url_related = list(self.timeline_events.find(
                {
                    "url": target_event["url"],
                    "user_session": user_session,
                    "id": {"$ne": event_id}
                },
                {"_id": 0}
            ).limit(5))
            related_events.extend(url_related)
        
        # Find events with similar tags
        if target_event.get("tags"):
            tag_related = list(self.timeline_events.find(
                {
                    "tags": {"$in": target_event["tags"]},
                    "user_session": user_session,
                    "id": {"$ne": event_id}
                },
                {"_id": 0}
            ).limit(5))
            related_events.extend(tag_related)
        
        # Remove duplicates and convert timestamps
        seen_ids = set()
        unique_related = []
        for event in related_events:
            if event["id"] not in seen_ids:
                seen_ids.add(event["id"])
                if event.get("timestamp"):
                    event["timestamp"] = event["timestamp"].isoformat()
                unique_related.append(event)
        
        return unique_related[:10]  # Return top 10 related events
    
    async def create_timeline_session(self, user_session: str, session_name: str) -> str:
        """Create a new timeline session for grouping activities"""
        
        session_id = str(uuid.uuid4())
        
        session_doc = {
            "session_id": session_id,
            "user_session": user_session,
            "session_name": session_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "event_count": 0,
            "duration_ms": 0,
            "status": "active",
            "tags": [],
            "metadata": {}
        }
        
        self.timeline_sessions.insert_one(session_doc)
        
        logger.info(f"Created timeline session {session_id}: {session_name}")
        return session_id
    
    async def get_timeline_sessions(self, user_session: str) -> List[Dict[str, Any]]:
        """Get all timeline sessions for a user"""
        
        sessions = list(self.timeline_sessions.find(
            {"user_session": user_session},
            {"_id": 0}
        ).sort("updated_at", -1))
        
        # Convert timestamps
        for session in sessions:
            for time_field in ["created_at", "updated_at"]:
                if session.get(time_field):
                    session[time_field] = session[time_field].isoformat()
        
        return sessions
    
    async def export_timeline(self, user_session: str, format: str = "json", 
                             start_time: datetime = None, end_time: datetime = None) -> Dict[str, Any]:
        """Export timeline data in different formats"""
        
        events = await self.get_timeline(user_session, start_time, end_time, limit=10000)
        summary = await self.get_timeline_summary(user_session)
        
        export_data = {
            "user_session": user_session,
            "exported_at": datetime.utcnow().isoformat(),
            "format": format,
            "summary": summary,
            "events": events,
            "total_events": len(events)
        }
        
        if format == "json":
            return export_data
        elif format == "csv":
            # Convert to CSV-friendly format
            csv_events = []
            for event in events:
                csv_events.append({
                    "timestamp": event.get("timestamp", ""),
                    "type": event.get("event_type", ""),
                    "title": event.get("title", ""),
                    "description": event.get("description", ""),
                    "url": event.get("url", ""),
                    "duration": event.get("duration_ms", 0)
                })
            export_data["csv_events"] = csv_events
            return export_data
        
        return export_data
    
    async def _background_analytics(self):
        """Background analytics processing"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Process analytics for active users
                await self._process_user_analytics()
                
                # Clean up old events (keep last 90 days)
                await self._cleanup_old_events()
                
            except Exception as e:
                logger.error(f"Timeline analytics error: {e}")
    
    async def _process_user_analytics(self):
        """Process analytics for all users"""
        
        # Get unique user sessions from recent events
        recent_time = datetime.utcnow() - timedelta(hours=24)
        
        pipeline = [
            {"$match": {"timestamp": {"$gte": recent_time}}},
            {"$group": {"_id": "$user_session", "event_count": {"$sum": 1}}}
        ]
        
        active_users = list(self.timeline_events.aggregate(pipeline))
        
        for user_data in active_users:
            user_session = user_data["_id"]
            
            # Generate analytics
            analytics = {
                "user_session": user_session,
                "generated_at": datetime.utcnow(),
                "daily_summary": await self.get_timeline_summary(user_session, "today"),
                "weekly_summary": await self.get_timeline_summary(user_session, "week"),
                "patterns": await self._analyze_user_patterns(user_session)
            }
            
            # Store analytics
            self.timeline_analytics.replace_one(
                {"user_session": user_session},
                analytics,
                upsert=True
            )
    
    async def _analyze_user_patterns(self, user_session: str) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        
        # Get recent events for pattern analysis
        recent_events = await self.get_timeline(user_session, limit=500)
        
        patterns = {
            "most_active_hours": [],
            "favorite_websites": [],
            "common_workflows": [],
            "productivity_trends": {}
        }
        
        if not recent_events:
            return patterns
        
        # Most active hours
        hour_activity = {}
        for event in recent_events:
            if event.get("timestamp"):
                try:
                    event_time = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
                    hour = event_time.hour
                    hour_activity[hour] = hour_activity.get(hour, 0) + 1
                except:
                    pass
        
        if hour_activity:
            sorted_hours = sorted(hour_activity.items(), key=lambda x: x[1], reverse=True)
            patterns["most_active_hours"] = [f"{hour}:00" for hour, _ in sorted_hours[:3]]
        
        # Favorite websites
        website_counts = {}
        for event in recent_events:
            url = event.get("url")
            if url:
                domain = self._extract_domain(url)
                website_counts[domain] = website_counts.get(domain, 0) + 1
        
        if website_counts:
            sorted_sites = sorted(website_counts.items(), key=lambda x: x[1], reverse=True)
            patterns["favorite_websites"] = [site for site, _ in sorted_sites[:5]]
        
        return patterns
    
    async def _cleanup_old_events(self):
        """Clean up events older than 90 days"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        result = self.timeline_events.delete_many({"timestamp": {"$lt": cutoff_date}})
        
        if result.deleted_count > 0:
            logger.info(f"Cleaned up {result.deleted_count} old timeline events")
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or parsed.path.split('/')[0]
        except:
            return url
    
    # Real-time event methods for WebSocket support
    
    def get_recent_events(self, user_session: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent events from buffer"""
        
        user_events = [
            event for event in self.event_buffer 
            if event.get("user_session") == user_session
        ]
        
        return sorted(user_events, key=lambda x: x.get("timestamp", datetime.min), reverse=True)[:limit]
    
    def clear_event_buffer(self, user_session: str):
        """Clear event buffer for a specific user"""
        
        self.event_buffer = [
            event for event in self.event_buffer 
            if event.get("user_session") != user_session
        ]

# Global timeline manager instance
enhanced_timeline_manager = None  # Will be initialized in server.py