"""
AETHER Timeline Navigation System
Advanced timeline navigation with session history and temporal browsing
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pymongo import MongoClient
from dataclasses import dataclass, asdict
from collections import defaultdict
import base64

logger = logging.getLogger(__name__)

@dataclass
class TimelineEvent:
    """Single timeline event"""
    event_id: str
    user_session: str
    event_type: str  # 'navigation', 'chat', 'automation', 'search', 'interaction'
    timestamp: datetime
    title: str
    description: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None

@dataclass
class TimelinePeriod:
    """Timeline period grouping"""
    period_id: str
    start_time: datetime
    end_time: datetime
    period_type: str  # 'hour', 'day', 'week', 'month'
    event_count: int
    events: List[TimelineEvent]

class TimelineNavigationSystem:
    """Advanced timeline navigation with session tracking"""
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.timeline_events = self.db.timeline_events
        self.timeline_snapshots = self.db.timeline_snapshots
        self.user_sessions = self.db.user_sessions_timeline
        
        # Create indexes for performance
        self._create_indexes()
        
        # In-memory cache for recent events
        self.recent_events_cache = defaultdict(list)  # user_session -> events list
        
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Timeline events indexes
            self.timeline_events.create_index([("user_session", 1), ("timestamp", -1)])
            self.timeline_events.create_index([("event_type", 1), ("timestamp", -1)])
            self.timeline_events.create_index([("timestamp", -1)])
            
            # Timeline snapshots indexes
            self.timeline_snapshots.create_index([("user_session", 1), ("captured_at", -1)])
            
            logger.info("Timeline indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create timeline indexes: {e}")
    
    async def record_event(self, user_session: str, event_type: str, title: str, 
                          description: str, url: str = None, 
                          metadata: Dict[str, Any] = None) -> str:
        """Record timeline event"""
        try:
            event_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            event = TimelineEvent(
                event_id=event_id,
                user_session=user_session,
                event_type=event_type,
                timestamp=timestamp,
                title=title,
                description=description,
                url=url,
                metadata=metadata or {}
            )
            
            # Store in database
            event_doc = asdict(event)
            self.timeline_events.insert_one(event_doc)
            
            # Update cache
            self.recent_events_cache[user_session].append(event)
            
            # Keep only last 100 events in cache per user
            if len(self.recent_events_cache[user_session]) > 100:
                self.recent_events_cache[user_session] = self.recent_events_cache[user_session][-100:]
            
            # Update user session activity
            await self._update_session_activity(user_session, timestamp)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to record timeline event: {e}")
            return None
    
    async def record_navigation_event(self, user_session: str, url: str, 
                                    title: str = None, screenshot: str = None) -> str:
        """Record navigation-specific event"""
        try:
            title = title or f"Visited {url}"
            description = f"Navigated to {url}"
            
            metadata = {
                "page_title": title,
                "domain": self._extract_domain(url),
                "has_screenshot": bool(screenshot)
            }
            
            event_id = await self.record_event(
                user_session=user_session,
                event_type="navigation",
                title=title,
                description=description,
                url=url,
                metadata=metadata
            )
            
            # Store screenshot if provided
            if screenshot and event_id:
                await self._store_screenshot(event_id, screenshot)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to record navigation event: {e}")
            return None
    
    async def record_chat_event(self, user_session: str, message: str, 
                               ai_response: str, url: str = None) -> str:
        """Record chat interaction event"""
        try:
            title = f"Chat: {message[:50]}{'...' if len(message) > 50 else ''}"
            description = f"Asked: {message}"
            
            metadata = {
                "user_message": message,
                "ai_response": ai_response,
                "message_length": len(message),
                "response_length": len(ai_response),
                "current_url": url
            }
            
            return await self.record_event(
                user_session=user_session,
                event_type="chat",
                title=title,
                description=description,
                url=url,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to record chat event: {e}")
            return None
    
    async def record_automation_event(self, user_session: str, automation_type: str, 
                                    description: str, status: str = "started") -> str:
        """Record automation event"""
        try:
            title = f"Automation: {automation_type}"
            
            metadata = {
                "automation_type": automation_type,
                "status": status,
                "automation_category": self._categorize_automation(automation_type)
            }
            
            return await self.record_event(
                user_session=user_session,
                event_type="automation",
                title=title,
                description=description,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to record automation event: {e}")
            return None
    
    async def record_search_event(self, user_session: str, query: str, 
                                 results_count: int = 0, url: str = None) -> str:
        """Record search event"""
        try:
            title = f"Search: {query}"
            description = f"Searched for '{query}'"
            
            metadata = {
                "query": query,
                "results_count": results_count,
                "query_length": len(query),
                "search_context": url
            }
            
            return await self.record_event(
                user_session=user_session,
                event_type="search",
                title=title,
                description=description,
                url=url,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to record search event: {e}")
            return None
    
    async def get_timeline(self, user_session: str, hours: int = 24, 
                          event_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get user timeline for specified period"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Build query
            query = {
                "user_session": user_session,
                "timestamp": {"$gte": start_time}
            }
            
            if event_types:
                query["event_type"] = {"$in": event_types}
            
            # Get events from database
            events = list(self.timeline_events.find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1))
            
            # Add screenshots if available
            for event in events:
                if event.get("metadata", {}).get("has_screenshot"):
                    screenshot = await self._get_screenshot(event["event_id"])
                    if screenshot:
                        event["screenshot"] = screenshot
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get timeline: {e}")
            return []
    
    async def get_grouped_timeline(self, user_session: str, hours: int = 24, 
                                 group_by: str = "hour") -> List[Dict[str, Any]]:
        """Get timeline grouped by time periods"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Define grouping pipeline based on group_by parameter
            if group_by == "hour":
                group_stage = {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"},
                            "hour": {"$hour": "$timestamp"}
                        },
                        "events": {"$push": "$$ROOT"},
                        "count": {"$sum": 1},
                        "start_time": {"$min": "$timestamp"},
                        "end_time": {"$max": "$timestamp"}
                    }
                }
            elif group_by == "day":
                group_stage = {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"}
                        },
                        "events": {"$push": "$$ROOT"},
                        "count": {"$sum": 1},
                        "start_time": {"$min": "$timestamp"},
                        "end_time": {"$max": "$timestamp"}
                    }
                }
            else:  # Default to hour
                group_stage = {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"},
                            "hour": {"$hour": "$timestamp"}
                        },
                        "events": {"$push": "$$ROOT"},
                        "count": {"$sum": 1},
                        "start_time": {"$min": "$timestamp"},
                        "end_time": {"$max": "$timestamp"}
                    }
                }
            
            pipeline = [
                {
                    "$match": {
                        "user_session": user_session,
                        "timestamp": {"$gte": start_time}
                    }
                },
                group_stage,
                {
                    "$sort": {"start_time": -1}
                }
            ]
            
            grouped_data = list(self.timeline_events.aggregate(pipeline))
            
            # Format response
            periods = []
            for group in grouped_data:
                period = {
                    "period_id": f"{group['_id']['year']}-{group['_id']['month']}-{group['_id']['day']}",
                    "start_time": group["start_time"].isoformat(),
                    "end_time": group["end_time"].isoformat(),
                    "period_type": group_by,
                    "event_count": group["count"],
                    "events": group["events"]
                }
                
                if group_by == "hour":
                    period["period_id"] += f"-{group['_id']['hour']}"
                
                periods.append(period)
            
            return periods
            
        except Exception as e:
            logger.error(f"Failed to get grouped timeline: {e}")
            return []
    
    async def search_timeline(self, user_session: str, query: str, 
                            hours: int = 168) -> List[Dict[str, Any]]:  # Default 7 days
        """Search timeline events"""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Build search pipeline
            pipeline = [
                {
                    "$match": {
                        "user_session": user_session,
                        "timestamp": {"$gte": start_time},
                        "$or": [
                            {"title": {"$regex": query, "$options": "i"}},
                            {"description": {"$regex": query, "$options": "i"}},
                            {"url": {"$regex": query, "$options": "i"}},
                            {"metadata.user_message": {"$regex": query, "$options": "i"}},
                            {"metadata.page_title": {"$regex": query, "$options": "i"}}
                        ]
                    }
                },
                {
                    "$addFields": {
                        "relevance_score": {
                            "$add": [
                                {"$cond": [{"$regexMatch": {"input": "$title", "regex": query, "options": "i"}}, 3, 0]},
                                {"$cond": [{"$regexMatch": {"input": "$description", "regex": query, "options": "i"}}, 2, 0]},
                                {"$cond": [{"$regexMatch": {"input": "$url", "regex": query, "options": "i"}}, 1, 0]}
                            ]
                        }
                    }
                },
                {
                    "$sort": {"relevance_score": -1, "timestamp": -1}
                },
                {
                    "$limit": 50
                },
                {
                    "$project": {"_id": 0}
                }
            ]
            
            search_results = list(self.timeline_events.aggregate(pipeline))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Timeline search failed: {e}")
            return []
    
    async def get_timeline_statistics(self, user_session: str, 
                                    days: int = 7) -> Dict[str, Any]:
        """Get timeline usage statistics"""
        try:
            start_time = datetime.utcnow() - timedelta(days=days)
            
            # Event type distribution
            type_pipeline = [
                {
                    "$match": {
                        "user_session": user_session,
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": "$event_type",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            event_type_counts = {
                item["_id"]: item["count"] 
                for item in self.timeline_events.aggregate(type_pipeline)
            }
            
            # Daily activity
            daily_pipeline = [
                {
                    "$match": {
                        "user_session": user_session,
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$timestamp"},
                            "month": {"$month": "$timestamp"},
                            "day": {"$dayOfMonth": "$timestamp"}
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            daily_activity = [
                {
                    "date": f"{item['_id']['year']}-{item['_id']['month']:02d}-{item['_id']['day']:02d}",
                    "events": item["count"]
                }
                for item in self.timeline_events.aggregate(daily_pipeline)
            ]
            
            # Total events
            total_events = sum(event_type_counts.values())
            
            # Most active hour
            hour_pipeline = [
                {
                    "$match": {
                        "user_session": user_session,
                        "timestamp": {"$gte": start_time}
                    }
                },
                {
                    "$group": {
                        "_id": {"$hour": "$timestamp"},
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"count": -1}
                },
                {
                    "$limit": 1
                }
            ]
            
            most_active_hour_result = list(self.timeline_events.aggregate(hour_pipeline))
            most_active_hour = most_active_hour_result[0]["_id"] if most_active_hour_result else None
            
            return {
                "period_days": days,
                "total_events": total_events,
                "event_type_distribution": event_type_counts,
                "daily_activity": daily_activity,
                "most_active_hour": most_active_hour,
                "average_events_per_day": round(total_events / days, 2) if days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Timeline statistics failed: {e}")
            return {}
    
    async def get_related_events(self, event_id: str, 
                               time_window_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get events related to a specific event"""
        try:
            # Get the target event
            target_event = self.timeline_events.find_one({"event_id": event_id})
            if not target_event:
                return []
            
            # Find events within time window
            start_time = target_event["timestamp"] - timedelta(minutes=time_window_minutes)
            end_time = target_event["timestamp"] + timedelta(minutes=time_window_minutes)
            
            related_events = list(self.timeline_events.find(
                {
                    "user_session": target_event["user_session"],
                    "event_id": {"$ne": event_id},
                    "timestamp": {"$gte": start_time, "$lte": end_time}
                },
                {"_id": 0}
            ).sort("timestamp", 1))
            
            # Add relationship score based on proximity and context
            for event in related_events:
                time_diff = abs((event["timestamp"] - target_event["timestamp"]).total_seconds())
                proximity_score = max(0, 1 - (time_diff / (time_window_minutes * 60)))
                
                # Context similarity (simplified)
                context_score = 0
                if event.get("url") == target_event.get("url"):
                    context_score += 0.5
                if event.get("event_type") == target_event.get("event_type"):
                    context_score += 0.3
                
                event["relationship_score"] = round((proximity_score + context_score) / 1.8, 3)
            
            # Sort by relationship score
            related_events.sort(key=lambda x: x["relationship_score"], reverse=True)
            
            return related_events[:10]  # Return top 10 related events
            
        except Exception as e:
            logger.error(f"Failed to get related events: {e}")
            return []
    
    async def create_timeline_snapshot(self, user_session: str, 
                                     title: str, description: str = "") -> str:
        """Create timeline snapshot/bookmark"""
        try:
            snapshot_id = str(uuid.uuid4())
            
            # Get recent timeline
            recent_events = await self.get_timeline(user_session, hours=1)
            
            snapshot = {
                "snapshot_id": snapshot_id,
                "user_session": user_session,
                "title": title,
                "description": description,
                "captured_at": datetime.utcnow(),
                "event_count": len(recent_events),
                "events_summary": self._create_events_summary(recent_events)
            }
            
            self.timeline_snapshots.insert_one(snapshot)
            
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Failed to create timeline snapshot: {e}")
            return None
    
    async def get_timeline_snapshots(self, user_session: str) -> List[Dict[str, Any]]:
        """Get user's timeline snapshots"""
        try:
            snapshots = list(self.timeline_snapshots.find(
                {"user_session": user_session},
                {"_id": 0}
            ).sort("captured_at", -1))
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to get timeline snapshots: {e}")
            return []
    
    async def _update_session_activity(self, user_session: str, timestamp: datetime):
        """Update user session activity tracking"""
        try:
            self.user_sessions.update_one(
                {"user_session": user_session},
                {
                    "$set": {"last_activity": timestamp},
                    "$inc": {"total_events": 1},
                    "$setOnInsert": {"first_activity": timestamp, "created_at": timestamp}
                },
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")
    
    async def _store_screenshot(self, event_id: str, screenshot: str):
        """Store screenshot for event"""
        try:
            screenshot_doc = {
                "event_id": event_id,
                "screenshot_data": screenshot,
                "stored_at": datetime.utcnow()
            }
            
            self.db.timeline_screenshots.insert_one(screenshot_doc)
            
        except Exception as e:
            logger.error(f"Failed to store screenshot: {e}")
    
    async def _get_screenshot(self, event_id: str) -> Optional[str]:
        """Get screenshot for event"""
        try:
            screenshot_doc = self.db.timeline_screenshots.find_one({"event_id": event_id})
            return screenshot_doc.get("screenshot_data") if screenshot_doc else None
            
        except Exception as e:
            logger.error(f"Failed to get screenshot: {e}")
            return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url
    
    def _categorize_automation(self, automation_type: str) -> str:
        """Categorize automation type"""
        automation_categories = {
            "web_scraping": "data_collection",
            "form_filling": "interaction",
            "email": "communication",
            "social_media": "content",
            "file_processing": "data_processing",
            "api_integration": "integration"
        }
        
        return automation_categories.get(automation_type.lower(), "general")
    
    def _create_events_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of events for snapshot"""
        try:
            if not events:
                return {"event_types": {}, "total": 0}
            
            event_types = defaultdict(int)
            urls = set()
            
            for event in events:
                event_types[event["event_type"]] += 1
                if event.get("url"):
                    urls.add(event["url"])
            
            return {
                "event_types": dict(event_types),
                "unique_urls": len(urls),
                "total": len(events),
                "time_span": {
                    "start": events[-1]["timestamp"] if events else None,
                    "end": events[0]["timestamp"] if events else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create events summary: {e}")
            return {"event_types": {}, "total": 0}

# Initialize global instance
timeline_navigation_system = None

def initialize_timeline_navigation_system(mongo_client: MongoClient):
    """Initialize timeline navigation system"""
    global timeline_navigation_system
    timeline_navigation_system = TimelineNavigationSystem(mongo_client)
    return timeline_navigation_system