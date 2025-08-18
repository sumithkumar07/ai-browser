import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
import uuid

logger = logging.getLogger(__name__)

class TimelineManager:
    """
    Phase 3: Timeline and Session Management System
    Advanced timeline tracking for enhanced user experience
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.active_sessions = {}
        self.timeline_cache = {}
    
    async def create_timeline_entry(self, session_id: str, entry_type: str, data: Dict[str, Any]) -> str:
        """Create a new timeline entry"""
        try:
            entry_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            timeline_entry = {
                "entry_id": entry_id,
                "session_id": session_id,
                "type": entry_type,
                "timestamp": timestamp,
                "data": data,
                "metadata": {
                    "user_agent": data.get("user_agent", ""),
                    "ip_address": data.get("ip_address", ""),
                    "duration": data.get("duration", 0),
                    "interaction_count": data.get("interaction_count", 0)
                },
                "search_metadata": self._generate_search_metadata(entry_type, data),
                "ai_summary": await self._generate_ai_summary(entry_type, data)
            }
            
            # Store in database
            self.db.timeline_entries.insert_one(timeline_entry)
            
            # Update session cache
            if session_id not in self.timeline_cache:
                self.timeline_cache[session_id] = []
            
            self.timeline_cache[session_id].append({
                "entry_id": entry_id,
                "type": entry_type,
                "timestamp": timestamp.isoformat(),
                "summary": timeline_entry["ai_summary"]
            })
            
            # Keep cache limited
            if len(self.timeline_cache[session_id]) > 50:
                self.timeline_cache[session_id] = self.timeline_cache[session_id][-50:]
            
            logger.info(f"Timeline entry created: {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Timeline entry creation failed: {e}")
            raise
    
    async def get_timeline(self, session_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, entry_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get timeline entries for a session"""
        try:
            # Build query
            query = {"session_id": session_id}
            
            # Add time range filter
            if start_time or end_time:
                time_filter = {}
                if start_time:
                    time_filter["$gte"] = start_time
                if end_time:
                    time_filter["$lte"] = end_time
                query["timestamp"] = time_filter
            
            # Add type filter
            if entry_types:
                query["type"] = {"$in": entry_types}
            
            # Get entries from database
            entries = list(self.db.timeline_entries.find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1).limit(100))
            
            # Process entries for frontend
            processed_entries = []
            for entry in entries:
                processed_entry = {
                    "entry_id": entry["entry_id"],
                    "type": entry["type"],
                    "timestamp": entry["timestamp"].isoformat(),
                    "summary": entry.get("ai_summary", ""),
                    "data": self._sanitize_data_for_frontend(entry["data"]),
                    "metadata": entry.get("metadata", {}),
                    "search_metadata": entry.get("search_metadata", {}),
                    "category": self._categorize_entry(entry["type"], entry["data"]),
                    "importance_score": self._calculate_importance_score(entry)
                }
                processed_entries.append(processed_entry)
            
            return processed_entries
            
        except Exception as e:
            logger.error(f"Timeline retrieval failed: {e}")
            return []
    
    async def search_timeline(self, session_id: str, search_query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search timeline entries using text search and filters"""
        try:
            # Build search query
            query = {"session_id": session_id}
            
            # Text search
            if search_query:
                # Search in multiple fields
                text_conditions = []
                
                # Search in AI summary
                text_conditions.append({"ai_summary": {"$regex": search_query, "$options": "i"}})
                
                # Search in data fields
                text_conditions.append({"data.title": {"$regex": search_query, "$options": "i"}})
                text_conditions.append({"data.url": {"$regex": search_query, "$options": "i"}})
                text_conditions.append({"data.content": {"$regex": search_query, "$options": "i"}})
                
                # Search in search metadata
                text_conditions.append({"search_metadata.keywords": {"$regex": search_query, "$options": "i"}})
                
                query["$or"] = text_conditions
            
            # Apply filters
            if filters:
                if "entry_types" in filters:
                    query["type"] = {"$in": filters["entry_types"]}
                
                if "date_range" in filters:
                    date_range = filters["date_range"]
                    if "start" in date_range or "end" in date_range:
                        time_filter = {}
                        if "start" in date_range:
                            time_filter["$gte"] = datetime.fromisoformat(date_range["start"])
                        if "end" in date_range:
                            time_filter["$lte"] = datetime.fromisoformat(date_range["end"])
                        query["timestamp"] = time_filter
                
                if "importance_threshold" in filters:
                    # This would require a more complex query or post-processing
                    pass
            
            # Execute search
            entries = list(self.db.timeline_entries.find(
                query,
                {"_id": 0}
            ).sort("timestamp", -1).limit(50))
            
            # Process and rank results
            processed_results = []
            for entry in entries:
                relevance_score = self._calculate_search_relevance(entry, search_query)
                
                result = {
                    "entry_id": entry["entry_id"],
                    "type": entry["type"],
                    "timestamp": entry["timestamp"].isoformat(),
                    "summary": entry.get("ai_summary", ""),
                    "data": self._sanitize_data_for_frontend(entry["data"]),
                    "metadata": entry.get("metadata", {}),
                    "relevance_score": relevance_score,
                    "matched_fields": self._identify_matched_fields(entry, search_query)
                }
                processed_results.append(result)
            
            # Sort by relevance
            processed_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Timeline search failed: {e}")
            return []
    
    async def get_timeline_analytics(self, session_id: str, time_range: str = "week") -> Dict[str, Any]:
        """Get analytics for timeline activity"""
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_range == "day":
                start_time = end_time - timedelta(days=1)
            elif time_range == "week":
                start_time = end_time - timedelta(weeks=1)
            elif time_range == "month":
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(weeks=1)
            
            # Get entries in time range
            entries = list(self.db.timeline_entries.find({
                "session_id": session_id,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }))
            
            # Calculate analytics
            analytics = {
                "total_entries": len(entries),
                "time_range": time_range,
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
                "entry_breakdown": self._calculate_entry_breakdown(entries),
                "activity_patterns": self._analyze_activity_patterns(entries),
                "top_websites": self._analyze_top_websites(entries),
                "productivity_insights": self._calculate_productivity_insights(entries),
                "ai_interaction_stats": self._analyze_ai_interactions(entries),
                "automation_usage": self._analyze_automation_usage(entries)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Timeline analytics failed: {e}")
            return {}
    
    async def create_timeline_bookmark(self, session_id: str, entry_id: str, bookmark_data: Dict[str, Any]) -> str:
        """Create a bookmark for a timeline entry"""
        try:
            bookmark_id = str(uuid.uuid4())
            
            bookmark = {
                "bookmark_id": bookmark_id,
                "session_id": session_id,
                "entry_id": entry_id,
                "title": bookmark_data.get("title", ""),
                "notes": bookmark_data.get("notes", ""),
                "tags": bookmark_data.get("tags", []),
                "created_at": datetime.utcnow(),
                "is_favorite": bookmark_data.get("is_favorite", False),
                "category": bookmark_data.get("category", "general")
            }
            
            self.db.timeline_bookmarks.insert_one(bookmark)
            
            return bookmark_id
            
        except Exception as e:
            logger.error(f"Timeline bookmark creation failed: {e}")
            raise
    
    async def get_timeline_bookmarks(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all bookmarks for a session"""
        try:
            bookmarks = list(self.db.timeline_bookmarks.find(
                {"session_id": session_id},
                {"_id": 0}
            ).sort("created_at", -1))
            
            # Enrich bookmarks with entry data
            enriched_bookmarks = []
            for bookmark in bookmarks:
                entry = self.db.timeline_entries.find_one(
                    {"entry_id": bookmark["entry_id"]},
                    {"_id": 0, "data": 1, "type": 1, "timestamp": 1, "ai_summary": 1}
                )
                
                if entry:
                    enriched_bookmark = {
                        **bookmark,
                        "entry_data": {
                            "type": entry["type"],
                            "timestamp": entry["timestamp"].isoformat(),
                            "summary": entry.get("ai_summary", ""),
                            "title": entry["data"].get("title", ""),
                            "url": entry["data"].get("url", "")
                        }
                    }
                    enriched_bookmarks.append(enriched_bookmark)
            
            return enriched_bookmarks
            
        except Exception as e:
            logger.error(f"Timeline bookmarks retrieval failed: {e}")
            return []
    
    async def delete_timeline_entry(self, session_id: str, entry_id: str) -> bool:
        """Delete a timeline entry"""
        try:
            result = self.db.timeline_entries.delete_one({
                "session_id": session_id,
                "entry_id": entry_id
            })
            
            # Also delete related bookmarks
            self.db.timeline_bookmarks.delete_many({
                "session_id": session_id,
                "entry_id": entry_id
            })
            
            # Update cache
            if session_id in self.timeline_cache:
                self.timeline_cache[session_id] = [
                    entry for entry in self.timeline_cache[session_id] 
                    if entry["entry_id"] != entry_id
                ]
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Timeline entry deletion failed: {e}")
            return False
    
    async def export_timeline(self, session_id: str, export_format: str = "json", filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Export timeline data in various formats"""
        try:
            # Get filtered timeline entries
            entries = await self.get_timeline(session_id, **filters if filters else {})
            
            # Get bookmarks
            bookmarks = await self.get_timeline_bookmarks(session_id)
            
            # Get analytics
            analytics = await self.get_timeline_analytics(session_id)
            
            export_data = {
                "session_id": session_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "export_format": export_format,
                "total_entries": len(entries),
                "entries": entries,
                "bookmarks": bookmarks,
                "analytics": analytics,
                "metadata": {
                    "exported_by": "AETHER Timeline Manager",
                    "version": "3.0",
                    "filters_applied": filters or {}
                }
            }
            
            if export_format == "json":
                return {
                    "success": True,
                    "data": export_data,
                    "content_type": "application/json"
                }
            elif export_format == "csv":
                csv_content = self._convert_to_csv(entries)
                return {
                    "success": True,
                    "data": csv_content,
                    "content_type": "text/csv"
                }
            else:
                return {
                    "success": True,
                    "data": export_data,
                    "content_type": "application/json"
                }
            
        except Exception as e:
            logger.error(f"Timeline export failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_search_metadata(self, entry_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate search metadata for timeline entry"""
        metadata = {
            "keywords": [],
            "searchable_text": "",
            "category_tags": [],
            "importance_indicators": []
        }
        
        # Extract keywords based on entry type
        if entry_type == "navigation":
            url = data.get("url", "")
            title = data.get("title", "")
            
            # Extract domain
            if url:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    metadata["keywords"].extend([domain, url])
                except:
                    pass
            
            if title:
                # Simple keyword extraction from title
                words = title.lower().split()
                keywords = [word.strip('.,!?";()') for word in words if len(word) > 3]
                metadata["keywords"].extend(keywords[:10])
            
            metadata["searchable_text"] = f"{title} {url}"
            metadata["category_tags"] = ["browsing", "navigation"]
            
        elif entry_type == "chat":
            message = data.get("message", "")
            response = data.get("response", "")
            
            # Extract keywords from chat
            combined_text = f"{message} {response}".lower()
            words = combined_text.split()
            keywords = [word.strip('.,!?";()') for word in words if len(word) > 4]
            metadata["keywords"] = list(set(keywords))[:20]
            
            metadata["searchable_text"] = combined_text
            metadata["category_tags"] = ["ai_chat", "conversation"]
            
            # Check for automation keywords
            if any(keyword in combined_text for keyword in ["automate", "workflow", "task"]):
                metadata["importance_indicators"].append("automation_related")
        
        elif entry_type == "automation":
            task_description = data.get("description", "")
            task_type = data.get("task_type", "")
            
            metadata["keywords"] = [task_type, "automation", "workflow"]
            metadata["searchable_text"] = task_description
            metadata["category_tags"] = ["automation", "productivity"]
            metadata["importance_indicators"] = ["user_workflow"]
        
        return metadata
    
    async def _generate_ai_summary(self, entry_type: str, data: Dict[str, Any]) -> str:
        """Generate AI summary for timeline entry"""
        try:
            # Create summary based on entry type
            if entry_type == "navigation":
                url = data.get("url", "")
                title = data.get("title", "")
                timestamp = data.get("timestamp", "")
                
                if title and url:
                    return f"Visited {title} at {url}"
                elif url:
                    return f"Navigated to {url}"
                else:
                    return "Web navigation activity"
            
            elif entry_type == "chat":
                message = data.get("message", "")
                if len(message) > 100:
                    return f"AI conversation: {message[:100]}..."
                else:
                    return f"AI conversation: {message}"
            
            elif entry_type == "automation":
                description = data.get("description", "")
                status = data.get("status", "")
                return f"Automation task: {description} ({status})"
            
            elif entry_type == "search":
                query = data.get("query", "")
                results_count = data.get("results_count", 0)
                return f"Searched for '{query}' ({results_count} results)"
            
            elif entry_type == "file_operation":
                operation = data.get("operation", "")
                file_name = data.get("file_name", "")
                return f"File operation: {operation} on {file_name}"
            
            else:
                return f"Activity: {entry_type}"
                
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return f"Activity recorded: {entry_type}"
    
    def _sanitize_data_for_frontend(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for frontend consumption"""
        sanitized = {}
        
        # Only include safe fields
        safe_fields = [
            "url", "title", "description", "message", "response", 
            "status", "progress", "result", "file_name", "operation",
            "query", "results_count", "automation_type", "duration"
        ]
        
        for field in safe_fields:
            if field in data:
                value = data[field]
                # Truncate long strings
                if isinstance(value, str) and len(value) > 500:
                    sanitized[field] = value[:500] + "..."
                else:
                    sanitized[field] = value
        
        return sanitized
    
    def _categorize_entry(self, entry_type: str, data: Dict[str, Any]) -> str:
        """Categorize timeline entry for better organization"""
        if entry_type == "navigation":
            url = data.get("url", "").lower()
            if any(social in url for social in ["twitter.com", "linkedin.com", "facebook.com", "instagram.com"]):
                return "social_media"
            elif any(work in url for work in ["github.com", "stackoverflow.com", "docs.google.com"]):
                return "work"
            elif any(news in url for news in ["news.", "bbc.com", "cnn.com", "reuters.com"]):
                return "news"
            else:
                return "browsing"
        
        elif entry_type == "chat":
            message = data.get("message", "").lower()
            if any(keyword in message for keyword in ["automate", "workflow", "task"]):
                return "automation_planning"
            elif any(keyword in message for keyword in ["help", "how", "what", "explain"]):
                return "learning"
            else:
                return "general_chat"
        
        elif entry_type == "automation":
            return "productivity"
        
        else:
            return "general"
    
    def _calculate_importance_score(self, entry: Dict[str, Any]) -> float:
        """Calculate importance score for timeline entry"""
        score = 50.0  # Base score
        
        entry_type = entry.get("type", "")
        data = entry.get("data", {})
        metadata = entry.get("metadata", {})
        
        # Type-based scoring
        type_scores = {
            "automation": 20,
            "chat": 10,
            "navigation": 5,
            "search": 8,
            "file_operation": 15
        }
        score += type_scores.get(entry_type, 0)
        
        # Duration-based scoring (longer interactions are more important)
        duration = metadata.get("duration", 0)
        if duration > 300:  # 5 minutes
            score += 15
        elif duration > 60:  # 1 minute
            score += 10
        
        # Interaction-based scoring
        interaction_count = metadata.get("interaction_count", 0)
        score += min(interaction_count * 2, 20)
        
        # Content-based scoring
        if entry_type == "chat":
            message = data.get("message", "")
            if len(message) > 100:
                score += 10
            
            # Check for important keywords
            important_keywords = ["important", "urgent", "automate", "workflow", "task", "help"]
            if any(keyword in message.lower() for keyword in important_keywords):
                score += 15
        
        elif entry_type == "automation":
            # Automation tasks are generally important
            score += 20
            
            status = data.get("status", "")
            if status == "completed":
                score += 10
            elif status == "failed":
                score += 5
        
        # Bookmark indicator
        search_metadata = entry.get("search_metadata", {})
        if "user_workflow" in search_metadata.get("importance_indicators", []):
            score += 25
        
        return min(score, 100.0)  # Cap at 100
    
    def _calculate_search_relevance(self, entry: Dict[str, Any], search_query: str) -> float:
        """Calculate search relevance score"""
        score = 0.0
        query_lower = search_query.lower()
        
        # Check AI summary (highest weight)
        ai_summary = entry.get("ai_summary", "").lower()
        if query_lower in ai_summary:
            score += 50
        
        # Check data fields
        data = entry.get("data", {})
        
        # Title match (high weight)
        title = data.get("title", "").lower()
        if query_lower in title:
            score += 30
        
        # URL match (medium weight)
        url = data.get("url", "").lower()
        if query_lower in url:
            score += 20
        
        # Content match (lower weight due to noise)
        content = data.get("content", "").lower()
        if query_lower in content:
            score += 10
        
        # Message/response match (for chat entries)
        message = data.get("message", "").lower()
        response = data.get("response", "").lower()
        if query_lower in message:
            score += 25
        if query_lower in response:
            score += 20
        
        # Keyword match
        search_metadata = entry.get("search_metadata", {})
        keywords = search_metadata.get("keywords", [])
        keyword_matches = sum(1 for keyword in keywords if query_lower in keyword.lower())
        score += keyword_matches * 5
        
        # Partial word matches
        query_words = query_lower.split()
        searchable_text = search_metadata.get("searchable_text", "").lower()
        
        for word in query_words:
            if len(word) > 2 and word in searchable_text:
                score += 3
        
        return min(score, 100.0)  # Cap at 100
    
    def _identify_matched_fields(self, entry: Dict[str, Any], search_query: str) -> List[str]:
        """Identify which fields matched the search query"""
        matched_fields = []
        query_lower = search_query.lower()
        
        # Check various fields
        if query_lower in entry.get("ai_summary", "").lower():
            matched_fields.append("summary")
        
        data = entry.get("data", {})
        
        if query_lower in data.get("title", "").lower():
            matched_fields.append("title")
        
        if query_lower in data.get("url", "").lower():
            matched_fields.append("url")
        
        if query_lower in data.get("message", "").lower():
            matched_fields.append("message")
        
        if query_lower in data.get("response", "").lower():
            matched_fields.append("response")
        
        return matched_fields
    
    def _calculate_entry_breakdown(self, entries: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate breakdown of entry types"""
        breakdown = {}
        
        for entry in entries:
            entry_type = entry.get("type", "unknown")
            breakdown[entry_type] = breakdown.get(entry_type, 0) + 1
        
        return breakdown
    
    def _analyze_activity_patterns(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze activity patterns"""
        if not entries:
            return {}
        
        # Group by hour of day
        hourly_activity = {}
        daily_activity = {}
        
        for entry in entries:
            timestamp = entry.get("timestamp")
            if timestamp:
                hour = timestamp.hour
                day = timestamp.strftime("%A")
                
                hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
                daily_activity[day] = daily_activity.get(day, 0) + 1
        
        # Find peak hours
        peak_hour = max(hourly_activity.items(), key=lambda x: x[1]) if hourly_activity else (0, 0)
        peak_day = max(daily_activity.items(), key=lambda x: x[1]) if daily_activity else ("", 0)
        
        return {
            "hourly_distribution": hourly_activity,
            "daily_distribution": daily_activity,
            "peak_hour": {"hour": peak_hour[0], "count": peak_hour[1]},
            "peak_day": {"day": peak_day[0], "count": peak_day[1]},
            "total_active_hours": len(hourly_activity),
            "average_hourly_activity": sum(hourly_activity.values()) / len(hourly_activity) if hourly_activity else 0
        }
    
    def _analyze_top_websites(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze most visited websites"""
        website_counts = {}
        
        for entry in entries:
            if entry.get("type") == "navigation":
                data = entry.get("data", {})
                url = data.get("url", "")
                title = data.get("title", "")
                
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc
                        
                        if domain not in website_counts:
                            website_counts[domain] = {
                                "domain": domain,
                                "count": 0,
                                "title": title,
                                "last_visit": entry.get("timestamp")
                            }
                        
                        website_counts[domain]["count"] += 1
                        
                        # Update last visit if more recent
                        if entry.get("timestamp") > website_counts[domain]["last_visit"]:
                            website_counts[domain]["last_visit"] = entry.get("timestamp")
                            website_counts[domain]["title"] = title
                        
                    except:
                        continue
        
        # Sort by visit count and return top 10
        top_websites = sorted(
            website_counts.values(), 
            key=lambda x: x["count"], 
            reverse=True
        )[:10]
        
        # Convert timestamps to strings
        for site in top_websites:
            if site["last_visit"]:
                site["last_visit"] = site["last_visit"].isoformat()
        
        return top_websites
    
    def _calculate_productivity_insights(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate productivity insights"""
        insights = {
            "total_automation_tasks": 0,
            "completed_automations": 0,
            "ai_interactions": 0,
            "avg_session_duration": 0,
            "productivity_score": 0
        }
        
        session_durations = []
        
        for entry in entries:
            entry_type = entry.get("type", "")
            data = entry.get("data", {})
            metadata = entry.get("metadata", {})
            
            if entry_type == "automation":
                insights["total_automation_tasks"] += 1
                if data.get("status") == "completed":
                    insights["completed_automations"] += 1
            
            elif entry_type == "chat":
                insights["ai_interactions"] += 1
            
            # Track session durations
            duration = metadata.get("duration", 0)
            if duration > 0:
                session_durations.append(duration)
        
        # Calculate averages
        if session_durations:
            insights["avg_session_duration"] = sum(session_durations) / len(session_durations)
        
        # Calculate productivity score
        if insights["total_automation_tasks"] > 0:
            completion_rate = insights["completed_automations"] / insights["total_automation_tasks"]
            insights["productivity_score"] = completion_rate * 100
        
        return insights
    
    def _analyze_ai_interactions(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze AI interaction patterns"""
        stats = {
            "total_interactions": 0,
            "avg_message_length": 0,
            "interaction_types": {},
            "response_times": []
        }
        
        message_lengths = []
        
        for entry in entries:
            if entry.get("type") == "chat":
                stats["total_interactions"] += 1
                
                data = entry.get("data", {})
                message = data.get("message", "")
                response_time = data.get("response_time", 0)
                
                if message:
                    message_lengths.append(len(message))
                
                if response_time > 0:
                    stats["response_times"].append(response_time)
                
                # Categorize interaction type
                if any(keyword in message.lower() for keyword in ["automate", "workflow", "task"]):
                    category = "automation_planning"
                elif any(keyword in message.lower() for keyword in ["help", "how", "explain"]):
                    category = "assistance"
                else:
                    category = "general"
                
                stats["interaction_types"][category] = stats["interaction_types"].get(category, 0) + 1
        
        # Calculate averages
        if message_lengths:
            stats["avg_message_length"] = sum(message_lengths) / len(message_lengths)
        
        if stats["response_times"]:
            stats["avg_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
        
        return stats
    
    def _analyze_automation_usage(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze automation usage patterns"""
        stats = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "task_types": {},
            "success_rate": 0,
            "avg_task_duration": 0
        }
        
        task_durations = []
        
        for entry in entries:
            if entry.get("type") == "automation":
                stats["total_tasks"] += 1
                
                data = entry.get("data", {})
                status = data.get("status", "")
                task_type = data.get("automation_type", "unknown")
                duration = data.get("duration", 0)
                
                if status == "completed":
                    stats["successful_tasks"] += 1
                elif status == "failed":
                    stats["failed_tasks"] += 1
                
                stats["task_types"][task_type] = stats["task_types"].get(task_type, 0) + 1
                
                if duration > 0:
                    task_durations.append(duration)
        
        # Calculate success rate
        if stats["total_tasks"] > 0:
            stats["success_rate"] = (stats["successful_tasks"] / stats["total_tasks"]) * 100
        
        # Calculate average task duration
        if task_durations:
            stats["avg_task_duration"] = sum(task_durations) / len(task_durations)
        
        return stats
    
    def _convert_to_csv(self, entries: List[Dict[str, Any]]) -> str:
        """Convert timeline entries to CSV format"""
        if not entries:
            return "timestamp,type,summary,url,category\n"
        
        csv_lines = ["timestamp,type,summary,url,category"]
        
        for entry in entries:
            timestamp = entry.get("timestamp", "")
            entry_type = entry.get("type", "")
            summary = entry.get("summary", "").replace(",", ";").replace("\n", " ")
            url = entry.get("data", {}).get("url", "")
            category = entry.get("category", "")
            
            csv_line = f'"{timestamp}","{entry_type}","{summary}","{url}","{category}"'
            csv_lines.append(csv_line)
        
        return "\n".join(csv_lines)

# Global function to initialize timeline manager
def initialize_timeline_manager(mongo_client: MongoClient):
    global timeline_manager
    timeline_manager = TimelineManager(mongo_client)
    return timeline_manager

# Global instance
timeline_manager = None