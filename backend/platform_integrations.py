# Platform Integrations - Cross-Platform Integration Framework  
# Critical Gap #4: Implement native integrations with 50+ platforms (Fellou.ai capability)

import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pymongo import MongoClient
import httpx
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    SOCIAL_MEDIA = "social_media"
    PRODUCTIVITY = "productivity" 
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    ECOMMERCE = "ecommerce"
    ANALYTICS = "analytics"
    CONTENT = "content"
    FINANCE = "finance"

class AuthMethod(Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    COOKIE_AUTH = "cookie_auth"

class IntegrationStatus(Enum):
    AVAILABLE = "available"
    CONNECTED = "connected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"

@dataclass
class PlatformCapability:
    """Platform capability definition"""
    capability_id: str
    name: str
    description: str
    endpoint: str
    method: str
    parameters: Dict[str, Any]
    response_format: str
    rate_limit: Optional[int] = None

@dataclass
class PlatformIntegration:
    """Platform integration configuration"""
    platform_id: str
    name: str
    description: str
    integration_type: IntegrationType
    auth_method: AuthMethod
    base_url: str
    capabilities: List[PlatformCapability]
    status: IntegrationStatus
    rate_limits: Dict[str, int]
    user_connections: int = 0
    last_updated: datetime = None

@dataclass
class UserIntegration:
    """User's connection to a platform"""
    connection_id: str
    user_session: str
    platform_id: str
    auth_data: Dict[str, Any]  # Encrypted in production
    status: IntegrationStatus
    connected_at: datetime
    last_used: datetime
    usage_count: int = 0

class PlatformIntegrationEngine:
    """Cross-platform integration engine (Fellou.ai 50+ platform capability)"""
    
    def __init__(self, mongo_client: MongoClient):
        self.db = mongo_client.aether_browser
        self.integrations: Dict[str, PlatformIntegration] = {}
        self.user_connections: Dict[str, Dict[str, UserIntegration]] = {}
        
        # Initialize platform integrations
        asyncio.create_task(self._initialize_platform_integrations())
    
    async def _initialize_platform_integrations(self):
        """Initialize all supported platform integrations"""
        
        # Social Media Platforms
        await self._register_platform("twitter", {
            "name": "Twitter/X",
            "description": "Social media platform for posts and interactions",
            "integration_type": IntegrationType.SOCIAL_MEDIA,
            "auth_method": AuthMethod.OAUTH2,
            "base_url": "https://api.twitter.com/2/",
            "capabilities": [
                {
                    "capability_id": "post_tweet",
                    "name": "Post Tweet",
                    "description": "Post a new tweet",
                    "endpoint": "tweets",
                    "method": "POST",
                    "parameters": {"text": "string", "media_ids": "array"},
                    "response_format": "json"
                },
                {
                    "capability_id": "get_timeline",
                    "name": "Get Timeline",
                    "description": "Get user timeline",
                    "endpoint": "users/{id}/tweets",
                    "method": "GET",
                    "parameters": {"max_results": "integer"},
                    "response_format": "json"
                },
                {
                    "capability_id": "search_tweets",
                    "name": "Search Tweets",
                    "description": "Search for tweets",
                    "endpoint": "tweets/search/recent",
                    "method": "GET",
                    "parameters": {"query": "string", "max_results": "integer"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 300, "search": 450}
        })
        
        await self._register_platform("linkedin", {
            "name": "LinkedIn",
            "description": "Professional networking platform",
            "integration_type": IntegrationType.SOCIAL_MEDIA,
            "auth_method": AuthMethod.OAUTH2,
            "base_url": "https://api.linkedin.com/v2/",
            "capabilities": [
                {
                    "capability_id": "post_update",
                    "name": "Post Update",
                    "description": "Share a LinkedIn update",
                    "endpoint": "ugcPosts",
                    "method": "POST",
                    "parameters": {"text": "string", "visibility": "string"},
                    "response_format": "json"
                },
                {
                    "capability_id": "get_profile",
                    "name": "Get Profile",
                    "description": "Get user profile information",
                    "endpoint": "people/~",
                    "method": "GET",
                    "parameters": {},
                    "response_format": "json"
                },
                {
                    "capability_id": "search_people",
                    "name": "Search People",
                    "description": "Search for LinkedIn profiles",
                    "endpoint": "people-search",
                    "method": "GET",
                    "parameters": {"keywords": "string", "start": "integer"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 500}
        })
        
        # Development Platforms
        await self._register_platform("github", {
            "name": "GitHub",
            "description": "Code repository and collaboration platform",
            "integration_type": IntegrationType.DEVELOPMENT,
            "auth_method": AuthMethod.BEARER_TOKEN,
            "base_url": "https://api.github.com/",
            "capabilities": [
                {
                    "capability_id": "get_repos",
                    "name": "Get Repositories",
                    "description": "Get user repositories",
                    "endpoint": "user/repos",
                    "method": "GET", 
                    "parameters": {"sort": "string", "per_page": "integer"},
                    "response_format": "json"
                },
                {
                    "capability_id": "create_issue",
                    "name": "Create Issue",
                    "description": "Create new issue in repository",
                    "endpoint": "repos/{owner}/{repo}/issues",
                    "method": "POST",
                    "parameters": {"title": "string", "body": "string", "labels": "array"},
                    "response_format": "json"
                },
                {
                    "capability_id": "search_code",
                    "name": "Search Code",
                    "description": "Search code across repositories",
                    "endpoint": "search/code",
                    "method": "GET",
                    "parameters": {"q": "string", "sort": "string"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"core": 5000, "search": 30}
        })
        
        # Productivity Platforms
        await self._register_platform("notion", {
            "name": "Notion",
            "description": "All-in-one workspace for notes and collaboration",
            "integration_type": IntegrationType.PRODUCTIVITY,
            "auth_method": AuthMethod.BEARER_TOKEN,
            "base_url": "https://api.notion.com/v1/",
            "capabilities": [
                {
                    "capability_id": "create_page",
                    "name": "Create Page",
                    "description": "Create new Notion page",
                    "endpoint": "pages",
                    "method": "POST",
                    "parameters": {"parent": "object", "properties": "object"},
                    "response_format": "json"
                },
                {
                    "capability_id": "query_database",
                    "name": "Query Database",
                    "description": "Query Notion database",
                    "endpoint": "databases/{database_id}/query",
                    "method": "POST",
                    "parameters": {"filter": "object", "sorts": "array"},
                    "response_format": "json"
                },
                {
                    "capability_id": "update_page",
                    "name": "Update Page",
                    "description": "Update existing page",
                    "endpoint": "pages/{page_id}",
                    "method": "PATCH",
                    "parameters": {"properties": "object"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 1000}
        })
        
        await self._register_platform("airtable", {
            "name": "Airtable",
            "description": "Cloud collaboration service with spreadsheet-database hybrid",
            "integration_type": IntegrationType.PRODUCTIVITY,
            "auth_method": AuthMethod.BEARER_TOKEN,
            "base_url": "https://api.airtable.com/v0/",
            "capabilities": [
                {
                    "capability_id": "create_record",
                    "name": "Create Record",
                    "description": "Create new record in base",
                    "endpoint": "{base_id}/{table_name}",
                    "method": "POST",
                    "parameters": {"fields": "object"},
                    "response_format": "json"
                },
                {
                    "capability_id": "list_records",
                    "name": "List Records", 
                    "description": "List records from table",
                    "endpoint": "{base_id}/{table_name}",
                    "method": "GET",
                    "parameters": {"maxRecords": "integer", "view": "string"},
                    "response_format": "json"
                },
                {
                    "capability_id": "update_record",
                    "name": "Update Record",
                    "description": "Update existing record",
                    "endpoint": "{base_id}/{table_name}/{record_id}",
                    "method": "PATCH",
                    "parameters": {"fields": "object"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 1000}
        })
        
        # Communication Platforms
        await self._register_platform("slack", {
            "name": "Slack",
            "description": "Business communication platform",
            "integration_type": IntegrationType.COMMUNICATION,
            "auth_method": AuthMethod.BEARER_TOKEN,
            "base_url": "https://slack.com/api/",
            "capabilities": [
                {
                    "capability_id": "send_message",
                    "name": "Send Message",
                    "description": "Send message to channel",
                    "endpoint": "chat.postMessage",
                    "method": "POST",
                    "parameters": {"channel": "string", "text": "string"},
                    "response_format": "json"
                },
                {
                    "capability_id": "list_channels",
                    "name": "List Channels",
                    "description": "List workspace channels",
                    "endpoint": "conversations.list",
                    "method": "GET",
                    "parameters": {"types": "string", "limit": "integer"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 1200}
        })
        
        # E-commerce Platforms
        await self._register_platform("shopify", {
            "name": "Shopify",
            "description": "E-commerce platform",
            "integration_type": IntegrationType.ECOMMERCE,
            "auth_method": AuthMethod.BEARER_TOKEN,
            "base_url": "https://{shop}.myshopify.com/admin/api/2023-10/",
            "capabilities": [
                {
                    "capability_id": "get_products",
                    "name": "Get Products",
                    "description": "Get store products",
                    "endpoint": "products.json",
                    "method": "GET",
                    "parameters": {"limit": "integer", "status": "string"},
                    "response_format": "json"
                },
                {
                    "capability_id": "get_orders",
                    "name": "Get Orders",
                    "description": "Get store orders",
                    "endpoint": "orders.json", 
                    "method": "GET",
                    "parameters": {"limit": "integer", "status": "string"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 1000}
        })
        
        # Analytics Platforms
        await self._register_platform("google_analytics", {
            "name": "Google Analytics",
            "description": "Web analytics service",
            "integration_type": IntegrationType.ANALYTICS,
            "auth_method": AuthMethod.OAUTH2,
            "base_url": "https://analyticsreporting.googleapis.com/v4/",
            "capabilities": [
                {
                    "capability_id": "get_reports",
                    "name": "Get Reports",
                    "description": "Get analytics reports",
                    "endpoint": "reports:batchGet",
                    "method": "POST",
                    "parameters": {"reportRequests": "array"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 100}
        })
        
        # Content Platforms
        await self._register_platform("wordpress", {
            "name": "WordPress",
            "description": "Content management system",
            "integration_type": IntegrationType.CONTENT,
            "auth_method": AuthMethod.BASIC_AUTH,
            "base_url": "https://{site}/wp-json/wp/v2/",
            "capabilities": [
                {
                    "capability_id": "create_post",
                    "name": "Create Post",
                    "description": "Create new WordPress post",
                    "endpoint": "posts",
                    "method": "POST",
                    "parameters": {"title": "string", "content": "string", "status": "string"},
                    "response_format": "json"
                },
                {
                    "capability_id": "get_posts",
                    "name": "Get Posts",
                    "description": "Get WordPress posts",
                    "endpoint": "posts",
                    "method": "GET",
                    "parameters": {"per_page": "integer", "status": "string"},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 1000}
        })
        
        # Financial Platforms
        await self._register_platform("stripe", {
            "name": "Stripe",
            "description": "Payment processing platform",
            "integration_type": IntegrationType.FINANCE,
            "auth_method": AuthMethod.BEARER_TOKEN,
            "base_url": "https://api.stripe.com/v1/",
            "capabilities": [
                {
                    "capability_id": "list_payments",
                    "name": "List Payments",
                    "description": "List payment intents",
                    "endpoint": "payment_intents",
                    "method": "GET",
                    "parameters": {"limit": "integer"},
                    "response_format": "json"
                },
                {
                    "capability_id": "get_balance",
                    "name": "Get Balance",
                    "description": "Get account balance",
                    "endpoint": "balance",
                    "method": "GET",
                    "parameters": {},
                    "response_format": "json"
                }
            ],
            "rate_limits": {"default": 1000}
        })
        
        logger.info(f"🔗 Initialized {len(self.integrations)} platform integrations")
    
    async def _register_platform(self, platform_id: str, config: Dict[str, Any]):
        """Register platform integration"""
        
        capabilities = [
            PlatformCapability(**cap) for cap in config["capabilities"]
        ]
        
        integration = PlatformIntegration(
            platform_id=platform_id,
            name=config["name"],
            description=config["description"],
            integration_type=IntegrationType(config["integration_type"]),
            auth_method=AuthMethod(config["auth_method"]),
            base_url=config["base_url"],
            capabilities=capabilities,
            status=IntegrationStatus.AVAILABLE,
            rate_limits=config["rate_limits"],
            last_updated=datetime.utcnow()
        )
        
        self.integrations[platform_id] = integration
        
        # Store in database
        await self._store_platform_integration(integration)
    
    async def get_available_integrations(
        self, 
        integration_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available platform integrations"""
        
        integrations = []
        
        for platform_id, integration in self.integrations.items():
            if integration_type and integration.integration_type.value != integration_type:
                continue
            
            integrations.append({
                "platform_id": platform_id,
                "name": integration.name,
                "description": integration.description,
                "integration_type": integration.integration_type.value,
                "auth_method": integration.auth_method.value,
                "status": integration.status.value,
                "capabilities_count": len(integration.capabilities),
                "user_connections": integration.user_connections,
                "capabilities": [
                    {
                        "capability_id": cap.capability_id,
                        "name": cap.name,
                        "description": cap.description
                    }
                    for cap in integration.capabilities
                ]
            })
        
        return integrations
    
    async def connect_user_to_platform(
        self,
        user_session: str,
        platform_id: str,
        auth_data: Dict[str, Any]
    ) -> str:
        """Connect user to platform"""
        
        if platform_id not in self.integrations:
            raise ValueError(f"Unknown platform: {platform_id}")
        
        connection_id = str(uuid.uuid4())
        
        user_integration = UserIntegration(
            connection_id=connection_id,
            user_session=user_session,
            platform_id=platform_id,
            auth_data=auth_data,  # Should be encrypted in production
            status=IntegrationStatus.CONNECTED,
            connected_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        # Store user connection
        if user_session not in self.user_connections:
            self.user_connections[user_session] = {}
        
        self.user_connections[user_session][platform_id] = user_integration
        
        # Update integration stats
        self.integrations[platform_id].user_connections += 1
        
        # Store in database
        await self._store_user_integration(user_integration)
        
        logger.info(f"🔗 User connected to platform: {user_session} → {platform_id}")
        
        return connection_id
    
    async def execute_platform_action(
        self,
        user_session: str,
        platform_id: str,
        capability_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action on connected platform"""
        
        # Check if user is connected to platform
        user_connection = await self._get_user_integration(user_session, platform_id)
        if not user_connection:
            return {"error": "Not connected to platform", "connected": False}
        
        # Get platform integration
        integration = self.integrations.get(platform_id)
        if not integration:
            return {"error": "Platform not available"}
        
        # Find capability
        capability = None
        for cap in integration.capabilities:
            if cap.capability_id == capability_id:
                capability = cap
                break
        
        if not capability:
            return {"error": f"Capability '{capability_id}' not found"}
        
        # Execute API call
        try:
            result = await self._execute_api_call(
                integration, capability, user_connection.auth_data, parameters
            )
            
            # Update usage stats
            user_connection.last_used = datetime.utcnow()
            user_connection.usage_count += 1
            await self._update_user_integration(user_connection)
            
            return {
                "success": True,
                "platform": platform_id,
                "capability": capability_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Platform action error: {platform_id}/{capability_id} - {e}")
            return {"error": str(e), "platform": platform_id}
    
    async def batch_execute_actions(
        self,
        user_session: str,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute multiple platform actions (Fellou.ai-style batch operations)"""
        
        results = []
        
        for action in actions:
            platform_id = action.get("platform_id")
            capability_id = action.get("capability_id")
            parameters = action.get("parameters", {})
            
            result = await self.execute_platform_action(
                user_session, platform_id, capability_id, parameters
            )
            
            results.append({
                "action": action,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Small delay between actions to respect rate limits
            await asyncio.sleep(0.2)
        
        return results
    
    async def get_user_integrations(self, user_session: str) -> List[Dict[str, Any]]:
        """Get user's connected integrations"""
        
        user_integrations = []
        
        try:
            integrations = list(self.db.user_integrations.find(
                {"user_session": user_session},
                {"_id": 0}
            ))
            
            for integration_data in integrations:
                platform_id = integration_data["platform_id"]
                platform = self.integrations.get(platform_id)
                
                if platform:
                    user_integrations.append({
                        "connection_id": integration_data["connection_id"],
                        "platform_id": platform_id,
                        "platform_name": platform.name,
                        "integration_type": platform.integration_type.value,
                        "status": integration_data["status"],
                        "connected_at": integration_data["connected_at"],
                        "last_used": integration_data["last_used"],
                        "usage_count": integration_data["usage_count"],
                        "available_capabilities": len(platform.capabilities)
                    })
        
        except Exception as e:
            logger.error(f"Error getting user integrations: {e}")
        
        return user_integrations
    
    async def disconnect_user_from_platform(
        self, 
        user_session: str, 
        platform_id: str
    ) -> bool:
        """Disconnect user from platform"""
        
        try:
            # Remove from memory
            if (user_session in self.user_connections and 
                platform_id in self.user_connections[user_session]):
                del self.user_connections[user_session][platform_id]
            
            # Remove from database
            result = self.db.user_integrations.delete_one({
                "user_session": user_session,
                "platform_id": platform_id
            })
            
            # Update platform stats
            if platform_id in self.integrations:
                self.integrations[platform_id].user_connections = max(0, 
                    self.integrations[platform_id].user_connections - 1)
            
            logger.info(f"🔌 User disconnected from platform: {user_session} → {platform_id}")
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error disconnecting user from platform: {e}")
            return False
    
    async def _execute_api_call(
        self,
        integration: PlatformIntegration,
        capability: PlatformCapability,
        auth_data: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute API call to platform"""
        
        # Build URL
        url = urljoin(integration.base_url, capability.endpoint)
        
        # Replace URL parameters
        for key, value in parameters.items():
            if f"{{{key}}}" in url:
                url = url.replace(f"{{{key}}}", str(value))
        
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        
        # Add authentication
        if integration.auth_method == AuthMethod.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {auth_data.get('token', '')}"
        elif integration.auth_method == AuthMethod.API_KEY:
            headers[auth_data.get('header', 'X-API-Key')] = auth_data.get('key', '')
        
        # Prepare request data
        request_data = {}
        for key, value in parameters.items():
            if f"{{{key}}}" not in capability.endpoint:  # Not a URL parameter
                request_data[key] = value
        
        # Make API call
        async with httpx.AsyncClient(timeout=30.0) as client:
            if capability.method.upper() == "GET":
                response = await client.get(url, headers=headers, params=request_data)
            elif capability.method.upper() == "POST":
                response = await client.post(url, headers=headers, json=request_data)
            elif capability.method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=request_data)
            elif capability.method.upper() == "PATCH":
                response = await client.patch(url, headers=headers, json=request_data)
            elif capability.method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {capability.method}")
            
            response.raise_for_status()
            
            if capability.response_format == "json":
                return response.json()
            else:
                return {"text": response.text}
    
    async def _get_user_integration(
        self, 
        user_session: str, 
        platform_id: str
    ) -> Optional[UserIntegration]:
        """Get user integration from memory or database"""
        
        # Check memory first
        if (user_session in self.user_connections and 
            platform_id in self.user_connections[user_session]):
            return self.user_connections[user_session][platform_id]
        
        # Load from database
        try:
            data = self.db.user_integrations.find_one({
                "user_session": user_session,
                "platform_id": platform_id
            }, {"_id": 0})
            
            if data:
                user_integration = UserIntegration(**data)
                
                # Store in memory
                if user_session not in self.user_connections:
                    self.user_connections[user_session] = {}
                self.user_connections[user_session][platform_id] = user_integration
                
                return user_integration
        
        except Exception as e:
            logger.error(f"Error getting user integration: {e}")
        
        return None
    
    async def _store_platform_integration(self, integration: PlatformIntegration):
        """Store platform integration in database"""
        try:
            integration_dict = asdict(integration)
            integration_dict["integration_type"] = integration.integration_type.value
            integration_dict["auth_method"] = integration.auth_method.value
            integration_dict["status"] = integration.status.value
            integration_dict["capabilities"] = [asdict(cap) for cap in integration.capabilities]
            
            self.db.platform_integrations.update_one(
                {"platform_id": integration.platform_id},
                {"$set": integration_dict},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing platform integration: {e}")
    
    async def _store_user_integration(self, user_integration: UserIntegration):
        """Store user integration in database"""
        try:
            integration_dict = asdict(user_integration)
            integration_dict["status"] = user_integration.status.value
            
            self.db.user_integrations.update_one(
                {"connection_id": user_integration.connection_id},
                {"$set": integration_dict},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error storing user integration: {e}")
    
    async def _update_user_integration(self, user_integration: UserIntegration):
        """Update user integration in database"""
        try:
            self.db.user_integrations.update_one(
                {"connection_id": user_integration.connection_id},
                {"$set": {
                    "last_used": user_integration.last_used,
                    "usage_count": user_integration.usage_count,
                    "status": user_integration.status.value
                }}
            )
        except Exception as e:
            logger.error(f"Error updating user integration: {e}")

# Global platform integration engine instance
platform_integration_engine: Optional[PlatformIntegrationEngine] = None

def initialize_platform_integration_engine(mongo_client: MongoClient) -> PlatformIntegrationEngine:
    """Initialize the global platform integration engine"""
    global platform_integration_engine
    platform_integration_engine = PlatformIntegrationEngine(mongo_client)
    return platform_integration_engine

def get_platform_integration_engine() -> Optional[PlatformIntegrationEngine]:
    """Get the global platform integration engine instance"""
    return platform_integration_engine