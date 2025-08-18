import asyncio
import httpx
import json
import uuid
from typing import Dict, List, Optional, Any, Callable
import os
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import base64
import hashlib
from urllib.parse import urlencode, parse_qs
import jwt

logger = logging.getLogger(__name__)

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"

class AuthType(Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"

@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    id: str
    name: str
    description: str
    auth_type: AuthType
    base_url: str
    endpoints: Dict[str, str]
    features: List[str]
    rate_limits: Dict[str, int]
    required_credentials: List[str]
    optional_credentials: List[str] = None
    webhooks_supported: bool = False
    oauth_config: Dict[str, Any] = None

class EnhancedIntegrationManager:
    """Advanced integration management system with OAuth 2.0, rate limiting, and smart routing"""
    
    def __init__(self, db_client):
        self.db = db_client.aether_browser
        self.integrations_collection = self.db.integrations
        self.oauth_sessions_collection = self.db.oauth_sessions
        self.rate_limits_collection = self.db.rate_limits
        
        # Integration configurations
        self.integration_configs = self._initialize_integrations()
        
        # Runtime state
        self.active_connections = {}
        self.rate_limit_trackers = {}
        self.oauth_handlers = {}
        
        # HTTP client with retry and rate limiting
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        
        # Background tasks
        self._cleanup_task = None
        self._health_check_task = None
        
    def start_integration_engine(self):
        """Start background integration management tasks"""
        if self._cleanup_task is None:
            try:
                self._cleanup_task = asyncio.create_task(self._background_cleanup())
                self._health_check_task = asyncio.create_task(self._background_health_checks())
            except RuntimeError:
                pass
    
    def _initialize_integrations(self) -> Dict[str, IntegrationConfig]:
        """Initialize available integrations"""
        
        integrations = {
            "linkedin": IntegrationConfig(
                id="linkedin",
                name="LinkedIn",
                description="Professional networking and job search automation",
                auth_type=AuthType.OAUTH2,
                base_url="https://api.linkedin.com/v2",
                endpoints={
                    "profile": "/people/~",
                    "jobs": "/jobSearch",
                    "connections": "/people/~/connections",
                    "posts": "/ugcPosts",
                    "companies": "/companies"
                },
                features=[
                    "job_search", "apply_jobs", "connect_professionals", 
                    "post_content", "message_connections", "company_research"
                ],
                rate_limits={"requests_per_hour": 500, "requests_per_day": 5000},
                required_credentials=["client_id", "client_secret"],
                webhooks_supported=True,
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
            "client_id": os.getenv(f"{integration_id.upper()}_CLIENT_ID"),
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
        
        # Exchange authorization code for access token
        token_data = {
            "client_id": os.getenv(f"{integration_id.upper()}_CLIENT_ID"),
            "client_secret": os.getenv(f"{integration_id.upper()}_CLIENT_SECRET"),
            "code": authorization_code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        async with self.http_client as client:
            response = await client.post(
                oauth_config["token_url"],
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise Exception(f"OAuth token exchange failed: {response.text}")
            
            token_response = response.json()
        
        # Store access token and update session
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)
        
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
        config = self.integration_configs[integration_id]
        oauth_config = config.oauth_config
        
        if not user_integration.get("refresh_token"):
            raise Exception("No refresh token available")
        
        # Refresh token request
        refresh_data = {
            "client_id": os.getenv(f"{integration_id.upper()}_CLIENT_ID"),
            "client_secret": os.getenv(f"{integration_id.upper()}_CLIENT_SECRET"),
            "refresh_token": user_integration["refresh_token"],
            "grant_type": "refresh_token"
        }
        
        async with self.http_client as client:
            response = await client.post(
                oauth_config["token_url"],
                data=refresh_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.text}")
            
            token_response = response.json()
        
        # Update stored tokens
        new_access_token = token_response["access_token"]
        new_refresh_token = token_response.get("refresh_token", user_integration["refresh_token"])
        expires_in = token_response.get("expires_in", 3600)
        
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
    
    # Integration-specific action handlers
    
    async def _execute_linkedin_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute LinkedIn-specific action"""
        
        base_url = self.integration_configs["linkedin"].base_url
        
        if action == "get_profile":
            async with self.http_client as client:
                response = await client.get(
                    f"{base_url}/people/~",
                    headers=auth_headers
                )
                response.raise_for_status()
                return {"profile": response.json()}
        
        elif action == "search_jobs":
            keywords = parameters.get("keywords", [])
            location = parameters.get("location", "")
            
            # Simulate job search (actual implementation would use LinkedIn API)
            return {
                "jobs_found": 15,
                "keywords": keywords,
                "location": location,
                "jobs": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "location": location or "Remote",
                        "posted": "2 days ago"
                    }
                ]
            }
        
        elif action == "post_content":
            content = parameters.get("content", "")
            
            post_data = {
                "author": "urn:li:person:CURRENT_USER_ID",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            async with self.http_client as client:
                response = await client.post(
                    f"{base_url}/ugcPosts",
                    headers={**auth_headers, "Content-Type": "application/json"},
                    json=post_data
                )
                
                if response.status_code == 201:
                    return {"post_published": True, "post_id": response.json().get("id")}
                else:
                    raise Exception(f"LinkedIn post failed: {response.text}")
        
        else:
            raise ValueError(f"Unsupported LinkedIn action: {action}")
    
    async def _execute_gmail_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Gmail-specific action"""
        
        base_url = self.integration_configs["gmail"].base_url
        
        if action == "send_email":
            to_email = parameters.get("to", "")
            subject = parameters.get("subject", "")
            body = parameters.get("body", "")
            
            # Create email message
            email_message = {
                "raw": base64.urlsafe_b64encode(
                    f"To: {to_email}\nSubject: {subject}\n\n{body}".encode()
                ).decode()
            }
            
            async with self.http_client as client:
                response = await client.post(
                    f"{base_url}/users/me/messages/send",
                    headers={**auth_headers, "Content-Type": "application/json"},
                    json=email_message
                )
                response.raise_for_status()
                return {"email_sent": True, "message_id": response.json().get("id")}
        
        elif action == "list_emails":
            query = parameters.get("query", "")
            max_results = parameters.get("max_results", 10)
            
            async with self.http_client as client:
                params = {"q": query, "maxResults": max_results}
                response = await client.get(
                    f"{base_url}/users/me/messages",
                    headers=auth_headers,
                    params=params
                )
                response.raise_for_status()
                return {"emails": response.json().get("messages", [])}
        
        else:
            raise ValueError(f"Unsupported Gmail action: {action}")
    
    async def _execute_notion_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Notion-specific action"""
        
        base_url = self.integration_configs["notion"].base_url
        
        # Notion requires specific version header
        notion_headers = {
            **auth_headers,
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        if action == "create_page":
            parent_id = parameters.get("parent_id", "")
            title = parameters.get("title", "")
            content = parameters.get("content", "")
            
            page_data = {
                "parent": {"database_id": parent_id} if parent_id else {"type": "page_id", "page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    }
                ]
            }
            
            async with self.http_client as client:
                response = await client.post(
                    f"{base_url}/pages",
                    headers=notion_headers,
                    json=page_data
                )
                response.raise_for_status()
                return {"page_created": True, "page_id": response.json().get("id")}
        
        elif action == "search_pages":
            query = parameters.get("query", "")
            
            search_data = {"query": query}
            
            async with self.http_client as client:
                response = await client.post(
                    f"{base_url}/search",
                    headers=notion_headers,
                    json=search_data
                )
                response.raise_for_status()
                return {"results": response.json().get("results", [])}
        
        else:
            raise ValueError(f"Unsupported Notion action: {action}")
    
    # Rate limiting and validation methods
    
    async def _check_rate_limits(self, user_session: str, integration_id: str) -> bool:
        """Check if user is within rate limits for integration"""
        
        config = self.integration_configs[integration_id]
        rate_limits = config.rate_limits
        
        current_time = datetime.utcnow()
        
        # Check each rate limit type
        for limit_type, limit_value in rate_limits.items():
            
            # Determine time window
            if "per_second" in limit_type:
                window_start = current_time - timedelta(seconds=1)
            elif "per_minute" in limit_type:
                window_start = current_time - timedelta(minutes=1)
            elif "per_hour" in limit_type:
                window_start = current_time - timedelta(hours=1)
            elif "per_day" in limit_type:
                window_start = current_time - timedelta(days=1)
            elif "per_15min" in limit_type:
                window_start = current_time - timedelta(minutes=15)
            else:
                continue
            
            # Count requests in window
            request_count = self.rate_limits_collection.count_documents({
                "user_session": user_session,
                "integration_id": integration_id,
                "timestamp": {"$gte": window_start}
            })
            
            if request_count >= limit_value:
                return False
        
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
    
    # Additional integration actions (placeholder implementations)
    
    async def _execute_github_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute GitHub-specific action"""
        # Implementation for GitHub actions
        return {"action": action, "result": "simulated"}
    
    async def _execute_slack_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Slack-specific action"""
        # Implementation for Slack actions
        return {"action": action, "result": "simulated"}
    
    async def _execute_twitter_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute Twitter-specific action"""
        # Implementation for Twitter actions
        return {"action": action, "result": "simulated"}
    
    async def _execute_openai_action(self, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute OpenAI-specific action"""
        # Implementation for OpenAI actions
        return {"action": action, "result": "simulated"}
    
    async def _execute_generic_action(self, integration_id: str, action: str, parameters: Dict, auth_headers: Dict) -> Dict[str, Any]:
        """Execute generic integration action"""
        return {
            "integration_id": integration_id,
            "action": action,
            "parameters": parameters,
            "result": "executed"
        }

# Global enhanced integration manager instance
enhanced_integration_manager = None  # Will be initialized in server.py