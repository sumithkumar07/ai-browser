import os
import asyncio
import json
import base64
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from urllib.parse import urlencode
import httpx
import logging

# Import database
from database import get_database

logger = logging.getLogger(__name__)

class AuthType(Enum):
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"

class IntegrationConfig:
    def __init__(self, id: str, name: str, description: str, auth_type: AuthType, 
                 base_url: str, endpoints: Dict[str, str], features: List[str],
                 rate_limits: Dict[str, int], required_credentials: List[str],
                 oauth_config: Dict[str, str] = None, webhooks_supported: bool = False):
        self.id = id
        self.name = name
        self.description = description
        self.auth_type = auth_type
        self.base_url = base_url
        self.endpoints = endpoints
        self.features = features
        self.rate_limits = rate_limits
        self.required_credentials = required_credentials
        self.oauth_config = oauth_config or {}
        self.webhooks_supported = webhooks_supported

class EnhancedIntegrationManager:
    def __init__(self):
        self.db = get_database()
        self.integrations_collection = self.db.integrations
        self.oauth_sessions_collection = self.db.oauth_sessions
        self.rate_limits_collection = self.db.rate_limits
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Active connections cache
        self.active_connections = {}
        
        # Integration configurations
        self.integration_configs = self._initialize_integration_configs()
        
        # Background tasks
        self._background_tasks = []
    
    async def _initialize_background_tasks(self):
        """Initialize background tasks"""
        try:
            self._background_tasks.append(asyncio.create_task(self._background_cleanup()))
            self._background_tasks.append(asyncio.create_task(self._background_health_checks()))
        except RuntimeError:
            pass  # No event loop running yet
    
    def _initialize_integration_configs(self) -> Dict[str, IntegrationConfig]:
        """Initialize integration configurations"""
        integrations = {
            "linkedin": IntegrationConfig(
                id="linkedin",
                name="LinkedIn",
                description="Professional networking and job search automation",
                auth_type=AuthType.OAUTH2,
                base_url="https://api.linkedin.com/v2",
                endpoints={
                    "profile": "/people/~",
                    "connections": "/people/~/connections",
                    "jobs": "/jobSearch",
                    "posts": "/ugcPosts",
                    "companies": "/companies"
                },
                features=[
                    "job_search", "profile_management", "network_building", 
                    "content_posting", "lead_generation", "company_research"
                ],
                rate_limits={"requests_per_day": 500},
                required_credentials=["client_id", "client_secret"],
                oauth_config={
                    "authorization_url": "https://www.linkedin.com/oauth/v2/authorization",
                    "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
                    "scope": "r_liteprofile r_emailaddress w_member_social rw_organization_admin"
                }
            ),
            
            "gmail": IntegrationConfig(
                id="gmail",
                name="Gmail",
                description="Email automation and management",
                auth_type=AuthType.OAUTH2,
                base_url="https://gmail.googleapis.com/gmail/v1",
                endpoints={
                    "messages": "/users/me/messages",
                    "send": "/users/me/messages/send",
                    "labels": "/users/me/labels",
                    "threads": "/users/me/threads",
                    "profile": "/users/me/profile"
                },
                features=[
                    "send_emails", "read_emails", "organize_inbox", 
                    "email_templates", "auto_reply", "email_scheduling"
                ],
                rate_limits={"requests_per_second": 10, "requests_per_day": 1000000000},
                required_credentials=["client_id", "client_secret"],
                oauth_config={
                    "authorization_url": "https://accounts.google.com/o/oauth2/auth",
                    "token_url": "https://oauth2.googleapis.com/token",
                    "scope": "https://www.googleapis.com/auth/gmail.modify"
                }
            ),
            
            "notion": IntegrationConfig(
                id="notion",
                name="Notion",
                description="Knowledge management and productivity",
                auth_type=AuthType.BEARER_TOKEN,
                base_url="https://api.notion.com/v1",
                endpoints={
                    "databases": "/databases",
                    "pages": "/pages",
                    "search": "/search",
                    "users": "/users",
                    "blocks": "/blocks"
                },
                features=[
                    "create_pages", "update_pages", "create_databases", 
                    "save_research", "organize_content", "team_collaboration"
                ],
                rate_limits={"requests_per_second": 3},
                required_credentials=["api_key"]
            ),
            
            "github": IntegrationConfig(
                id="github",
                name="GitHub",
                description="Code repository and project management",
                auth_type=AuthType.BEARER_TOKEN,
                base_url="https://api.github.com",
                endpoints={
                    "repos": "/repos",
                    "issues": "/repos/{owner}/{repo}/issues",
                    "pulls": "/repos/{owner}/{repo}/pulls",
                    "user": "/user",
                    "search": "/search"
                },
                features=[
                    "create_repos", "manage_issues", "code_analysis", 
                    "project_management", "team_collaboration", "ci_cd_automation"
                ],
                rate_limits={"requests_per_hour": 5000},
                required_credentials=["token"]
            ),
            
            "slack": IntegrationConfig(
                id="slack",
                name="Slack",
                description="Team communication and collaboration",
                auth_type=AuthType.OAUTH2,
                base_url="https://slack.com/api",
                endpoints={
                    "channels": "/channels.list",
                    "messages": "/chat.postMessage",
                    "files": "/files.upload",
                    "users": "/users.list",
                    "conversations": "/conversations.list"
                },
                features=[
                    "send_messages", "share_content", "create_channels", 
                    "file_sharing", "workflow_automation", "team_notifications"
                ],
                rate_limits={"requests_per_minute": 100},
                required_credentials=["client_id", "client_secret"],
                oauth_config={
                    "authorization_url": "https://slack.com/oauth/v2/authorize",
                    "token_url": "https://slack.com/api/oauth.v2.access",
                    "scope": "chat:write channels:read groups:read im:read mpim:read files:write"
                }
            ),
            
            "twitter": IntegrationConfig(
                id="twitter",
                name="Twitter/X",
                description="Social media engagement and content sharing",
                auth_type=AuthType.OAUTH2,
                base_url="https://api.twitter.com/2",
                endpoints={
                    "tweets": "/tweets",
                    "users": "/users",
                    "media": "/media",
                    "lists": "/lists",
                    "search": "/tweets/search/recent"
                },
                features=[
                    "post_tweets", "schedule_content", "engage_audience", 
                    "social_listening", "trend_analysis", "audience_growth"
                ],
                rate_limits={"requests_per_15min": 300},
                required_credentials=["client_id", "client_secret"],
                oauth_config={
                    "authorization_url": "https://twitter.com/i/oauth2/authorize",
                    "token_url": "https://api.twitter.com/2/oauth2/token",
                    "scope": "tweet.read tweet.write users.read offline.access"
                }
            ),
            
            "openai": IntegrationConfig(
                id="openai",
                name="OpenAI",
                description="Advanced AI capabilities and GPT models",
                auth_type=AuthType.BEARER_TOKEN,
                base_url="https://api.openai.com/v1",
                endpoints={
                    "chat": "/chat/completions",
                    "completions": "/completions",
                    "images": "/images/generations",
                    "audio": "/audio/transcriptions",
                    "models": "/models"
                },
                features=[
                    "text_generation", "image_generation", "audio_transcription", 
                    "code_completion", "content_analysis", "custom_ai_workflows"
                ],
                rate_limits={"requests_per_minute": 60},
                required_credentials=["api_key"]
            )
        }
        
        return integrations
    
    async def get_available_integrations(self, include_status: bool = False) -> List[Dict[str, Any]]:
        """Get list of available integrations with optional status information"""
        
        integrations = []
        
        for integration_id, config in self.integration_configs.items():
            integration_data = {
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "features": config.features,
                "auth_type": config.auth_type.value,
                "webhooks_supported": config.webhooks_supported
            }
            
            if include_status:
                # Check if integration has active connections
                active_count = len([
                    conn for conn in self.active_connections.values()
                    if conn.get("integration_id") == integration_id
                ])
                
                integration_data["active_connections"] = active_count
                integration_data["status"] = "active" if active_count > 0 else "available"
            
            integrations.append(integration_data)
        
        return integrations
    
    async def initiate_oauth_flow(self, integration_id: str, user_session: str, 
                                 redirect_uri: str, state: str = None) -> Dict[str, Any]:
        """Initiate OAuth 2.0 authorization flow"""
        
        if integration_id not in self.integration_configs:
            raise ValueError(f"Integration {integration_id} not found")
        
        config = self.integration_configs[integration_id]
        
        if config.auth_type != AuthType.OAUTH2:
            raise ValueError(f"Integration {integration_id} does not support OAuth 2.0")
        
        oauth_config = config.oauth_config
        if not oauth_config:
            raise ValueError(f"OAuth configuration not found for {integration_id}")
        
        # Generate state if not provided
        if not state:
            state = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        
        # Store OAuth session
        oauth_session = {
            "user_session": user_session,
            "integration_id": integration_id,
            "state": state,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow(),
            "status": "initiated"
        }
        
        self.oauth_sessions_collection.insert_one(oauth_session)
        
        # Build authorization URL
        auth_params = {
            "client_id": os.getenv(f"{integration_id.upper()}_CLIENT_ID", "demo_client_id"),
            "redirect_uri": redirect_uri,
            "scope": oauth_config["scope"],
            "state": state,
            "response_type": "code"
        }
        
        authorization_url = f"{oauth_config['authorization_url']}?{urlencode(auth_params)}"
        
        return {
            "authorization_url": authorization_url,
            "state": state,
            "expires_in": 600  # 10 minutes
        }
    
    async def complete_oauth_flow(self, integration_id: str, authorization_code: str, 
                                 state: str, redirect_uri: str) -> Dict[str, Any]:
        """Complete OAuth 2.0 authorization flow"""
        
        # Verify OAuth session
        oauth_session = self.oauth_sessions_collection.find_one({
            "integration_id": integration_id,
            "state": state,
            "status": "initiated"
        })
        
        if not oauth_session:
            raise ValueError("Invalid OAuth session")
        
        config = self.integration_configs[integration_id]
        oauth_config = config.oauth_config
        
        # For demo purposes, simulate token exchange
        access_token = f"demo_access_token_{integration_id}_{uuid.uuid4().hex[:8]}"
        refresh_token = f"demo_refresh_token_{integration_id}_{uuid.uuid4().hex[:8]}"
        expires_in = 3600
        
        # Update OAuth session
        self.oauth_sessions_collection.update_one(
            {"_id": oauth_session["_id"]},
            {
                "$set": {
                    "status": "completed",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Store in integrations collection for the user
        integration_data = {
            "user_session": oauth_session["user_session"],
            "integration_id": integration_id,
            "auth_type": "oauth2",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in),
            "created_at": datetime.utcnow(),
            "last_used": None,
            "status": "active"
        }
        
        # Replace or insert
        self.integrations_collection.replace_one(
            {"user_session": oauth_session["user_session"], "integration_id": integration_id},
            integration_data,
            upsert=True
        )
        
        return {
            "success": True,
            "integration_id": integration_id,
            "user_session": oauth_session["user_session"],
            "features_available": config.features
        }
    
    async def store_api_key_integration(self, user_session: str, integration_id: str, 
                                      credentials: Dict[str, str]) -> Dict[str, Any]:
        """Store API key-based integration"""
        
        if integration_id not in self.integration_configs:
            raise ValueError(f"Integration {integration_id} not found")
        
        config = self.integration_configs[integration_id]
        
        # Validate credentials
        validation_result = await self._validate_credentials(integration_id, credentials)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": validation_result["message"]
            }
        
        # Store integration
        integration_data = {
            "user_session": user_session,
            "integration_id": integration_id,
            "auth_type": config.auth_type.value,
            "credentials": self._encrypt_credentials(credentials),
            "created_at": datetime.utcnow(),
            "last_used": None,
            "status": "active"
        }
        
        # Replace or insert
        self.integrations_collection.replace_one(
            {"user_session": user_session, "integration_id": integration_id},
            integration_data,
            upsert=True
        )
        
        return {
            "success": True,
            "integration_id": integration_id,
            "features_available": config.features,
            "message": f"Successfully connected to {config.name}"
        }
    
    async def execute_integration_action(self, user_session: str, integration_id: str, 
                                       action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action using a specific integration"""
        
        if integration_id not in self.integration_configs:
            raise ValueError(f"Integration {integration_id} not found")
        
        # Get user's integration
        user_integration = self.integrations_collection.find_one({
            "user_session": user_session,
            "integration_id": integration_id,
            "status": "active"
        })
        
        if not user_integration:
            raise ValueError(f"No active {integration_id} integration found for user")
        
        # Check rate limits
        if not await self._check_rate_limits(user_session, integration_id):
            raise Exception(f"Rate limit exceeded for {integration_id}")
        
        config = self.integration_configs[integration_id]
        
        try:
            # Get authentication headers
            auth_headers = await self._get_auth_headers(user_integration)
            
            # Execute action based on integration type
            if integration_id == "linkedin":
                result = await self._execute_linkedin_action(action, parameters, auth_headers)
            elif integration_id == "gmail":
                result = await self._execute_gmail_action(action, parameters, auth_headers)
            elif integration_id == "notion":
                result = await self._execute_notion_action(action, parameters, auth_headers)
            elif integration_id == "github":
                result = await self._execute_github_action(action, parameters, auth_headers)
            elif integration_id == "slack":
                result = await self._execute_slack_action(action, parameters, auth_headers)
            elif integration_id == "twitter":
                result = await self._execute_twitter_action(action, parameters, auth_headers)
            elif integration_id == "openai":
                result = await self._execute_openai_action(action, parameters, auth_headers)
            else:
                result = await self._execute_generic_action(integration_id, action, parameters, auth_headers)
            
            # Update last used timestamp
            self.integrations_collection.update_one(
                {"_id": user_integration["_id"]},
                {"$set": {"last_used": datetime.utcnow()}}
            )
            
            # Record rate limit usage
            await self._record_rate_limit_usage(user_session, integration_id)
            
            return {
                "success": True,
                "integration": integration_id,
                "action": action,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Integration {integration_id} action {action} failed: {e}")
            
            # Check if it's an authentication error
            if "401" in str(e) or "unauthorized" in str(e).lower():
                # Mark integration as needing re-authentication
                self.integrations_collection.update_one(
                    {"_id": user_integration["_id"]},
                    {"$set": {"status": "unauthorized"}}
                )
            
            return {
                "success": False,
                "integration": integration_id,
                "action": action,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_auth_headers(self, user_integration: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers for integration"""
        
        integration_id = user_integration["integration_id"]
        config = self.integration_configs[integration_id]
        
        if config.auth_type == AuthType.OAUTH2:
            access_token = user_integration["access_token"]
            
            # Check if token needs refresh
            if user_integration.get("expires_at") and datetime.utcnow() > user_integration["expires_at"]:
                access_token = await self._refresh_oauth_token(user_integration)
            
            return {"Authorization": f"Bearer {access_token}"}
            
        elif config.auth_type == AuthType.BEARER_TOKEN:
            credentials = self._decrypt_credentials(user_integration["credentials"])
            api_key = credentials.get("api_key") or credentials.get("token")
            return {"Authorization": f"Bearer {api_key}"}
            
        elif config.auth_type == AuthType.API_KEY:
            credentials = self._decrypt_credentials(user_integration["credentials"])
            # Different integrations use different header names
            if integration_id == "notion":
                return {"Authorization": f"Bearer {credentials['api_key']}"}
            else:
                return {"X-API-Key": credentials["api_key"]}
        
        return {}
    
    async def _refresh_oauth_token(self, user_integration: Dict[str, Any]) -> str:
        """Refresh OAuth 2.0 access token"""
        
        integration_id = user_integration["integration_id"]
        
        if not user_integration.get("refresh_token"):
            raise Exception("No refresh token available")
        
        # For demo purposes, generate new token
        new_access_token = f"demo_refreshed_token_{integration_id}_{uuid.uuid4().hex[:8]}"
        new_refresh_token = user_integration["refresh_token"]
        expires_in = 3600
        
        self.integrations_collection.update_one(
            {"_id": user_integration["_id"]},
            {
                "$set": {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
                }
            }
        )
        
        return new_access_token
    
    # Integration-specific action handlers (simplified for demo)
    
    async def _execute_linkedin_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute LinkedIn-specific action"""
        if action == "search_jobs":
            return {
                "jobs_found": 15,
                "keywords": parameters.get("keywords", []),
                "location": parameters.get("location", "Remote")
            }
        elif action == "post_content":
            return {"post_published": True, "post_id": f"linkedin_post_{uuid.uuid4().hex[:8]}"}
        else:
            return {"action": action, "result": "simulated", "platform": "linkedin"}
    
    async def _execute_gmail_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Gmail-specific action"""
        if action == "send_email":
            return {"email_sent": True, "message_id": f"gmail_msg_{uuid.uuid4().hex[:8]}"}
        elif action == "list_emails":
            return {"emails": [{"id": "1", "subject": "Demo Email", "from": "demo@example.com"}]}
        else:
            return {"action": action, "result": "simulated", "platform": "gmail"}
    
    async def _execute_notion_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Notion-specific action"""
        if action == "create_page":
            return {"page_created": True, "page_id": f"notion_page_{uuid.uuid4().hex[:8]}"}
        else:
            return {"action": action, "result": "simulated", "platform": "notion"}
    
    async def _execute_github_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute GitHub-specific action"""
        return {"action": action, "result": "simulated", "platform": "github"}
    
    async def _execute_slack_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Slack-specific action"""
        return {"action": action, "result": "simulated", "platform": "slack"}
    
    async def _execute_twitter_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Twitter-specific action"""
        return {"action": action, "result": "simulated", "platform": "twitter"}
    
    async def _execute_openai_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute OpenAI-specific action"""
        return {"action": action, "result": "simulated", "platform": "openai"}
    
    async def _execute_generic_action(self, integration_id: str, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute generic integration action"""
        return {
            "integration_id": integration_id,
            "action": action,
            "parameters": parameters,
            "result": "executed"
        }
    
    # Rate limiting and validation methods
    
    async def _check_rate_limits(self, user_session: str, integration_id: str) -> bool:
        """Check if user is within rate limits for integration"""
        # Simplified rate limiting - always return True for demo
        return True
    
    async def _record_rate_limit_usage(self, user_session: str, integration_id: str):
        """Record rate limit usage"""
        self.rate_limits_collection.insert_one({
            "user_session": user_session,
            "integration_id": integration_id,
            "timestamp": datetime.utcnow()
        })
    
    async def _validate_credentials(self, integration_id: str, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Validate integration credentials"""
        
        config = self.integration_configs[integration_id]
        
        # Check required fields
        missing_fields = [
            field for field in config.required_credentials
            if field not in credentials or not credentials[field]
        ]
        
        if missing_fields:
            return {
                "valid": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Integration-specific validation
        try:
            if integration_id == "notion":
                api_key = credentials.get("api_key", "")
                if not api_key.startswith("secret_"):
                    return {
                        "valid": False,
                        "message": "Notion API key must start with 'secret_'"
                    }
            
            elif integration_id == "github":
                token = credentials.get("token", "")
                if not (token.startswith("ghp_") or token.startswith("github_pat_")):
                    return {
                        "valid": False,
                        "message": "GitHub token format invalid"
                    }
            
            return {
                "valid": True,
                "message": f"{config.name} credentials are valid",
                "features_available": config.features
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Credential validation error: {str(e)}"
            }
    
    def _encrypt_credentials(self, credentials: Dict[str, str]) -> Dict[str, str]:
        """Encrypt credentials for storage"""
        # Simple encryption - in production, use proper encryption
        encrypted = {}
        for key, value in credentials.items():
            encrypted[key] = base64.b64encode(value.encode()).decode()
        return encrypted
    
    def _decrypt_credentials(self, encrypted_credentials: Dict[str, str]) -> Dict[str, str]:
        """Decrypt stored credentials"""
        # Simple decryption - in production, use proper decryption
        decrypted = {}
        for key, value in encrypted_credentials.items():
            decrypted[key] = base64.b64decode(value.encode()).decode()
        return decrypted
    
    # Background tasks
    
    async def _background_cleanup(self):
        """Background cleanup of expired sessions and tokens"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.utcnow()
                
                # Clean expired OAuth sessions
                self.oauth_sessions_collection.delete_many({
                    "created_at": {"$lt": current_time - timedelta(hours=1)},
                    "status": "initiated"
                })
                
                # Clean old rate limit records
                self.rate_limits_collection.delete_many({
                    "timestamp": {"$lt": current_time - timedelta(days=1)}
                })
                
                logger.info("Integration cleanup completed")
                
            except Exception as e:
                logger.error(f"Integration cleanup error: {e}")
    
    async def _background_health_checks(self):
        """Background health checks for integrations"""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                
                # Check for integrations that need token refresh
                expired_integrations = self.integrations_collection.find({
                    "auth_type": "oauth2",
                    "expires_at": {"$lt": datetime.utcnow() + timedelta(minutes=10)},
                    "status": "active"
                })
                
                for integration in expired_integrations:
                    try:
                        await self._refresh_oauth_token(integration)
                        logger.info(f"Refreshed token for {integration['integration_id']}")
                    except Exception as e:
                        logger.error(f"Failed to refresh token for {integration['integration_id']}: {e}")
                        # Mark as needing re-authentication
                        self.integrations_collection.update_one(
                            {"_id": integration["_id"]},
                            {"$set": {"status": "unauthorized"}}
                        )
                
            except Exception as e:
                logger.error(f"Integration health check error: {e}")

# Global enhanced integration manager instance
enhanced_integration_manager = EnhancedIntegrationManager()