"""
LinkedIn Platform Integration for AETHER
Professional networking automation and content management
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability

class LinkedInConnector(BasePlatformConnector):
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        super().__init__(credentials, config)
        self.access_token = credentials.get('access_token')
        self.client_id = credentials.get('client_id') 
        self.client_secret = credentials.get('client_secret')
    
    @property
    def platform_name(self) -> str:
        return "linkedin"
    
    @property 
    def auth_type(self) -> AuthType:
        return AuthType.OAUTH2
    
    @property
    def base_url(self) -> str:
        return "https://api.linkedin.com/v2"
    
    async def authenticate(self) -> bool:
        """Authenticate with LinkedIn API"""
        if not self.access_token:
            return False
        self.auth_token = self.access_token
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test LinkedIn API connection"""
        try:
            response = await self.make_request("GET", "/me")
            return {
                "success": response.success,
                "platform": "linkedin",
                "user": response.data.get("localizedFirstName") if response.success else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get LinkedIn platform capabilities"""
        return [
            PlatformCapability(
                name="profile_management",
                description="Manage LinkedIn profile information",
                methods=["get_profile", "update_profile"]
            ),
            PlatformCapability(
                name="content_publishing",
                description="Create and manage LinkedIn posts",
                methods=["create_post", "get_posts", "delete_post"]
            ),
            PlatformCapability(
                name="network_management", 
                description="Manage connections and network",
                methods=["get_connections", "send_invitation", "get_network_stats"]
            ),
            PlatformCapability(
                name="company_pages",
                description="Manage company pages and content",
                methods=["get_company_info", "post_company_update"]
            )
        ]
    
    # Profile Management
    async def get_profile(self) -> Dict[str, Any]:
        """Get user profile information"""
        response = await self.make_request("GET", "/me?projection=(id,firstName,lastName,headline,profilePicture)")
        return {"success": response.success, "profile": response.data}
    
    async def get_connections(self) -> Dict[str, Any]:
        """Get user connections"""
        response = await self.make_request("GET", "/connections")
        return {"success": response.success, "connections": response.data}
    
    # Content Management
    async def create_post(self, text: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Create a LinkedIn post"""
        post_data = {
            "author": f"urn:li:person:{await self._get_person_id()}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "ARTICLE" if media_urls else "NONE"
                }
            }
        }
        
        if media_urls:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {"status": "READY", "originalUrl": url} for url in media_urls
            ]
        
        response = await self.make_request("POST", "/ugcPosts", data=post_data)
        return {"success": response.success, "post_id": response.data.get("id") if response.success else None}
    
    async def _get_person_id(self) -> str:
        """Get the authenticated user's person ID"""
        if not hasattr(self, '_person_id'):
            response = await self.make_request("GET", "/me")
            self._person_id = response.data.get("id") if response.success else "unknown"
        return self._person_id