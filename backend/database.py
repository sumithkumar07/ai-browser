"""
Database module for AETHER Browser
Provides database connection and utilities
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global database client
_client = None
_db = None

def get_database():
    """Get MongoDB database instance"""
    global _client, _db
    
    if _db is None:
        try:
            mongo_url = os.getenv("MONGO_URL")
            if not mongo_url:
                raise Exception("MONGO_URL environment variable not set")
            
            _client = MongoClient(mongo_url, maxPoolSize=50, minPoolSize=10)
            _db = _client.aether_browser
            
            # Test connection
            _client.admin.command('ping')
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    return _db

def get_client():
    """Get MongoDB client instance"""
    global _client
    
    if _client is None:
        get_database()  # This will initialize both client and database
    
    return _client

def close_database():
    """Close database connection"""
    global _client, _db
    
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("Database connection closed")

# Collections helper
class Collections:
    """Database collections accessor"""
    
    def __init__(self):
        self.db = get_database()
    
    @property
    def chat_sessions(self):
        return self.db.chat_sessions
    
    @property
    def recent_tabs(self):
        return self.db.recent_tabs
    
    @property
    def page_summaries(self):
        return self.db.page_summaries
    
    @property
    def automation_tasks(self):
        return self.db.automation_tasks
    
    @property
    def workflows(self):
        return self.db.workflows
    
    @property
    def user_sessions(self):
        return self.db.user_sessions
    
    @property
    def integrations(self):
        return self.db.integrations
    
    @property
    def performance_metrics(self):
        return self.db.performance_metrics
    
    @property
    def cache_data(self):
        return self.db.cache_data
    
    @property
    def ai_interactions(self):
        return self.db.ai_interactions
    
    @property
    def user_patterns(self):
        return self.db.user_patterns
    
    @property
    def memory_data(self):
        return self.db.memory_data
    
    @property
    def voice_commands(self):
        return self.db.voice_commands
    
    @property
    def keyboard_shortcuts(self):
        return self.db.keyboard_shortcuts

# Global collections instance
collections = Collections()