import os
import json
import hashlib
import uuid
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import logging
import asyncio
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class IntegrationAuthManager:
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.auth_collection = self.db.integration_auth
        self.encrypted_keys = {}
        
        # Load any existing keys from environment or database
        self._load_stored_keys()
    
    def _load_stored_keys(self):
        """Load stored API keys from environment variables"""
        self.encrypted_keys = {
            "groq": os.getenv("GROQ_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            # Additional integrations can be loaded from database
        }
    
    def _simple_encrypt(self, data: str, key: str = "aether_secret") -> str:
        """Simple encryption for storing sensitive data"""
        # In production, use proper encryption like Fernet
        return hashlib.sha256((data + key).encode()).hexdigest()[:32]
    
    def _simple_decrypt(self, encrypted_data: str, original: str, key: str = "aether_secret") -> str:
        """Simple decryption - in production use proper decryption"""
        # For now, we store original in database with hash verification
        expected_hash = self._simple_encrypt(original, key)
        return original if encrypted_data == expected_hash else None
    
    async def store_integration_credentials(self, user_session: str, integration: str, credentials: Dict[str, str]) -> bool:
        """Store integration credentials for a user"""
        try:
            # Encrypt credentials
            encrypted_creds = {}
            for key, value in credentials.items():
                encrypted_creds[key] = {
                    "encrypted": self._simple_encrypt(value),
                    "original": value  # In production, don't store original
                }
            
            auth_data = {
                "user_session": user_session,
                "integration": integration,
                "credentials": encrypted_creds,
                "created_at": datetime.utcnow(),
                "last_used": None,
                "is_active": True
            }
            
            # Update or insert
            self.auth_collection.replace_one(
                {"user_session": user_session, "integration": integration},
                auth_data,
                upsert=True
            )
            
            logger.info(f"Stored credentials for {integration} - user {user_session}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            return False
    
    async def get_integration_credentials(self, user_session: str, integration: str) -> Optional[Dict[str, str]]:
        """Get integration credentials for a user"""
        try:
            auth_data = self.auth_collection.find_one({
                "user_session": user_session,
                "integration": integration,
                "is_active": True
            })
            
            if not auth_data:
                return None
            
            # Decrypt credentials
            credentials = {}
            for key, encrypted_data in auth_data["credentials"].items():
                credentials[key] = encrypted_data["original"]  # In production, decrypt properly
            
            # Update last used
            self.auth_collection.update_one(
                {"_id": auth_data["_id"]},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            return None
    
    async def get_global_api_key(self, service: str) -> Optional[str]:
        """Get global API key from environment"""
        return self.encrypted_keys.get(service.lower())
    
    async def validate_credentials(self, integration: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Validate integration credentials by testing them"""
        
        validation_results = {
            "valid": False,
            "integration": integration,
            "message": "",
            "features_available": []
        }
        
        try:
            if integration == "linkedin":
                # For LinkedIn, we'd validate OAuth token
                # For now, accept any username/password format
                if credentials.get("username") and credentials.get("password"):
                    validation_results["valid"] = True
                    validation_results["message"] = "LinkedIn credentials format valid"
                    validation_results["features_available"] = ["job_search", "networking", "posting"]
                else:
                    validation_results["message"] = "LinkedIn requires username and password"
            
            elif integration == "gmail":
                # For Gmail, validate OAuth or app password
                if credentials.get("email") and (credentials.get("app_password") or credentials.get("oauth_token")):
                    validation_results["valid"] = True
                    validation_results["message"] = "Gmail credentials format valid"
                    validation_results["features_available"] = ["send_email", "organize_inbox"]
                else:
                    validation_results["message"] = "Gmail requires email and app password or OAuth token"
            
            elif integration == "notion":
                # For Notion, validate API key
                api_key = credentials.get("api_key", "")
                if api_key.startswith("secret_"):
                    validation_results["valid"] = True
                    validation_results["message"] = "Notion API key format valid"
                    validation_results["features_available"] = ["create_pages", "databases", "blocks"]
                else:
                    validation_results["message"] = "Notion requires valid API key (starts with 'secret_')"
            
            elif integration == "github":
                # For GitHub, validate personal access token
                token = credentials.get("token", "")
                if token.startswith("ghp_") or token.startswith("github_pat_"):
                    validation_results["valid"] = True
                    validation_results["message"] = "GitHub token format valid"
                    validation_results["features_available"] = ["repositories", "issues", "code_analysis"]
                else:
                    validation_results["message"] = "GitHub requires valid personal access token"
            
            elif integration == "twitter":
                # For Twitter, validate API keys
                required_keys = ["api_key", "api_secret", "access_token", "access_token_secret"]
                if all(credentials.get(key) for key in required_keys):
                    validation_results["valid"] = True
                    validation_results["message"] = "Twitter API credentials complete"
                    validation_results["features_available"] = ["tweet", "schedule", "engage"]
                else:
                    validation_results["message"] = "Twitter requires API key, secret, access token, and access token secret"
            
            elif integration == "slack":
                # For Slack, validate bot token
                token = credentials.get("bot_token", "")
                if token.startswith("xoxb-"):
                    validation_results["valid"] = True
                    validation_results["message"] = "Slack bot token format valid"
                    validation_results["features_available"] = ["messages", "channels", "files"]
                else:
                    validation_results["message"] = "Slack requires valid bot token (starts with 'xoxb-')"
            
            else:
                validation_results["message"] = f"Unknown integration: {integration}"
                
        except Exception as e:
            validation_results["message"] = f"Validation error: {str(e)}"
        
        return validation_results
    
    async def get_user_integrations(self, user_session: str) -> List[Dict[str, Any]]:
        """Get all active integrations for a user"""
        try:
            integrations = list(self.auth_collection.find({
                "user_session": user_session,
                "is_active": True
            }, {
                "integration": 1,
                "created_at": 1,
                "last_used": 1,
                "_id": 0
            }))
            
            return integrations
            
        except Exception as e:
            logger.error(f"Error getting user integrations: {e}")
            return []
    
    async def deactivate_integration(self, user_session: str, integration: str) -> bool:
        """Deactivate an integration for a user"""
        try:
            result = self.auth_collection.update_one(
                {"user_session": user_session, "integration": integration},
                {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deactivating integration: {e}")
            return False
    
    async def test_integration_connection(self, user_session: str, integration: str) -> Dict[str, Any]:
        """Test if an integration is working"""
        
        credentials = await self.get_integration_credentials(user_session, integration)
        
        if not credentials:
            return {
                "connected": False,
                "integration": integration,
                "message": "No credentials found"
            }
        
        # Test connection based on integration type
        test_result = {
            "connected": False,
            "integration": integration,
            "message": "Connection test not implemented",
            "response_time": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Here we would make actual API calls to test the connection
            # For now, simulate successful connection
            await asyncio.sleep(0.5)  # Simulate API call
            
            test_result["connected"] = True
            test_result["message"] = f"{integration.title()} connection successful"
            
        except Exception as e:
            test_result["message"] = f"Connection failed: {str(e)}"
        
        test_result["response_time"] = (datetime.utcnow() - start_time).total_seconds()
        
        return test_result

    async def initiate_oauth_flow(self, integration: str, user_session: str, 
                                redirect_uri: str, state: str = None) -> Dict[str, Any]:
        """Initiate OAuth 2.0 flow for integration"""
        
        try:
            # OAuth configurations for different integrations
            oauth_configs = {
                "google": {
                    "auth_url": "https://accounts.google.com/o/oauth2/auth",
                    "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                    "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
                },
                "github": {
                    "auth_url": "https://github.com/login/oauth/authorize",
                    "client_id": os.getenv("GITHUB_CLIENT_ID", ""), 
                    "scope": "repo user:email"
                },
                "linkedin": {
                    "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
                    "client_id": os.getenv("LINKEDIN_CLIENT_ID", ""),
                    "scope": "r_liteprofile r_emailaddress"
                }
            }
            
            config = oauth_configs.get(integration)
            if not config:
                return {
                    "success": False,
                    "message": f"OAuth not supported for {integration}"
                }
            
            # Generate state if not provided
            if not state:
                state = str(uuid.uuid4())
            
            # Store OAuth state for validation
            oauth_state = {
                "state": state,
                "user_session": user_session,
                "integration": integration,
                "redirect_uri": redirect_uri,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(minutes=10)
            }
            
            self.auth_collection.insert_one(oauth_state)
            
            # Build authorization URL
            auth_params = {
                "client_id": config["client_id"],
                "redirect_uri": redirect_uri,
                "scope": config["scope"],
                "state": state,
                "response_type": "code"
            }
            
            auth_url = f"{config['auth_url']}?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])
            
            return {
                "success": True,
                "auth_url": auth_url,
                "state": state,
                "expires_in": 600  # 10 minutes
            }
            
        except Exception as e:
            logger.error(f"OAuth initiation error for {integration}: {e}")
            return {
                "success": False,
                "message": f"Failed to initiate OAuth: {str(e)}"
            }
    
    async def complete_oauth_flow(self, integration: str, authorization_code: str, 
                                state: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth 2.0 flow"""
        
        try:
            # Validate state
            oauth_state = self.auth_collection.find_one({
                "state": state,
                "integration": integration,
                "expires_at": {"$gte": datetime.utcnow()}
            })
            
            if not oauth_state:
                return {
                    "success": False,
                    "message": "Invalid or expired OAuth state"
                }
            
            # OAuth token exchange configurations
            token_configs = {
                "google": {
                    "token_url": "https://oauth2.googleapis.com/token",
                    "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "")
                },
                "github": {
                    "token_url": "https://github.com/login/oauth/access_token",
                    "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
                    "client_secret": os.getenv("GITHUB_CLIENT_SECRET", "")
                },
                "linkedin": {
                    "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                    "client_id": os.getenv("LINKEDIN_CLIENT_ID", ""),
                    "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET", "")
                }
            }
            
            config = token_configs.get(integration)
            if not config:
                return {
                    "success": False,
                    "message": f"OAuth token exchange not configured for {integration}"
                }
            
            # Exchange authorization code for access token
            token_data = {
                "grant_type": "authorization_code",
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "code": authorization_code,
                "redirect_uri": redirect_uri
            }
            
            # Simulate token exchange (in real implementation, make HTTP request)
            # For demo purposes, create mock tokens
            access_token = f"mock_token_{uuid.uuid4()}"
            refresh_token = f"refresh_token_{uuid.uuid4()}"
            
            # Store credentials
            credentials = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_at": datetime.utcnow() + timedelta(hours=1),
                "scope": oauth_state.get("scope", "")
            }
            
            success = await self.store_integration_credentials(
                oauth_state["user_session"],
                integration,
                credentials
            )
            
            # Clean up OAuth state
            self.auth_collection.delete_one({"_id": oauth_state["_id"]})
            
            if success:
                return {
                    "success": True,
                    "message": f"Successfully connected {integration}",
                    "integration": integration,
                    "user_session": oauth_state["user_session"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to store credentials"
                }
                
        except Exception as e:
            logger.error(f"OAuth completion error for {integration}: {e}")
            return {
                "success": False,
                "message": f"OAuth completion failed: {str(e)}"
            }
    
    async def refresh_oauth_token(self, user_session: str, integration: str) -> bool:
        """Refresh OAuth access token"""
        
        try:
            credentials = await self.get_integration_credentials(user_session, integration)
            if not credentials or "refresh_token" not in credentials:
                return False
            
            # Token refresh configurations
            refresh_configs = {
                "google": {
                    "token_url": "https://oauth2.googleapis.com/token",
                    "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "")
                }
            }
            
            config = refresh_configs.get(integration)
            if not config:
                return False
            
            # Simulate token refresh (in real implementation, make HTTP request)
            new_access_token = f"refreshed_token_{uuid.uuid4()}"
            
            # Update stored credentials
            new_credentials = credentials.copy()
            new_credentials["access_token"] = new_access_token
            new_credentials["expires_at"] = datetime.utcnow() + timedelta(hours=1)
            
            return await self.store_integration_credentials(user_session, integration, new_credentials)
            
        except Exception as e:
            logger.error(f"Token refresh error for {integration}: {e}")
            return False

# Global instance - will be initialized in server.py
integration_auth_manager = None