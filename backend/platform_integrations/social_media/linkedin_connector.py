import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability, ApiResponse

class LinkedInConnector(BasePlatformConnector):
    """LinkedIn integration for professional networking automation"""
    
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
        """Authenticate with LinkedIn API using OAuth2"""
        try:
            if not self.validate_credentials(["access_token"]):
                return False
            
            self.auth_token = self.credentials["access_token"]
            
            # Test authentication by getting profile
            response = await self.make_request("GET", "/people/~")
            
            if response.success:
                self.logger.info("LinkedIn authentication successful")
                return True
            else:
                self.logger.error(f"LinkedIn authentication failed: {response.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"LinkedIn authentication error: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test LinkedIn API connection"""
        try:
            start_time = datetime.now()
            response = await self.make_request("GET", "/people/~")
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": response.success,
                "platform": "linkedin",
                "response_time": response_time,
                "error": response.error if not response.success else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "platform": "linkedin", 
                "error": str(e)
            }
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get LinkedIn integration capabilities"""
        return [
            PlatformCapability(
                name="Profile Management",
                description="Get and update LinkedIn profile information",
                methods=["get_profile", "update_profile"],
                rate_limit=100
            ),
            PlatformCapability(
                name="Post Publishing",
                description="Create and manage LinkedIn posts",
                methods=["create_post", "get_posts", "delete_post"],
                rate_limit=50
            ),
            PlatformCapability(
                name="Connection Management", 
                description="Manage LinkedIn connections and networking",
                methods=["get_connections", "send_invitation", "get_invitations"],
                rate_limit=25
            ),
            PlatformCapability(
                name="Company Pages",
                description="Manage LinkedIn company pages",
                methods=["get_company_info", "post_to_company", "get_company_posts"],
                rate_limit=20,
                requires_premium=True
            ),
            PlatformCapability(
                name="Analytics",
                description="Access LinkedIn analytics and insights",
                methods=["get_post_analytics", "get_profile_analytics"],
                rate_limit=10,
                requires_premium=True
            )
        ]
    
    # Core LinkedIn Methods
    async def get_profile(self, fields: Optional[List[str]] = None) -> ApiResponse:
        """Get LinkedIn profile information"""
        default_fields = [
            "id", "firstName", "lastName", "headline", "summary",
            "industry", "location", "positions", "educations"
        ]
        
        projection_fields = fields or default_fields
        params = {"projection": f"({','.join(projection_fields)})"}
        
        return await self.make_request("GET", "/people/~", params=params)
    
    async def create_post(self, content: str, visibility: str = "PUBLIC") -> ApiResponse:
        """Create a LinkedIn post"""
        post_data = {
            "author": f"urn:li:person:{await self._get_profile_id()}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        return await self.make_request("POST", "/ugcPosts", data=post_data)
    
    async def create_article_post(self, title: str, content: str, article_url: str) -> ApiResponse:
        """Create a LinkedIn post with article link"""
        post_data = {
            "author": f"urn:li:person:{await self._get_profile_id()}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "description": {
                            "text": title
                        },
                        "originalUrl": article_url,
                        "title": {
                            "text": title
                        }
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        return await self.make_request("POST", "/ugcPosts", data=post_data)
    
    async def get_posts(self, count: int = 20) -> ApiResponse:
        """Get user's LinkedIn posts"""
        profile_id = await self._get_profile_id()
        params = {
            "q": "authors",
            "authors": f"urn:li:person:{profile_id}",
            "count": str(count)
        }
        
        return await self.make_request("GET", "/ugcPosts", params=params)
    
    async def get_connections(self, start: int = 0, count: int = 50) -> ApiResponse:
        """Get LinkedIn connections"""
        params = {
            "q": "viewer",
            "start": str(start),
            "count": str(count),
            "projection": "(elements*(to~))"
        }
        
        return await self.make_request("GET", "/people/~/connections", params=params)
    
    async def send_connection_request(self, profile_id: str, message: Optional[str] = None) -> ApiResponse:
        """Send connection invitation"""
        invitation_data = {
            "trackingId": f"invitation-{profile_id}",
            "message": message or "I'd like to connect with you on LinkedIn.",
            "invitations": [{
                "invitee": {
                    "com.linkedin.voyager.growth.invitation.InviteeProfile": {
                        "profileId": profile_id
                    }
                }
            }]
        }
        
        return await self.make_request("POST", "/people/~/mailbox", data=invitation_data)
    
    async def get_company_info(self, company_id: str) -> ApiResponse:
        """Get company information"""
        return await self.make_request("GET", f"/companies/{company_id}")
    
    async def post_to_company_page(self, company_id: str, content: str) -> ApiResponse:
        """Post to company LinkedIn page"""
        post_data = {
            "author": f"urn:li:organization:{company_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        return await self.make_request("POST", "/ugcPosts", data=post_data)
    
    async def search_people(self, keywords: str, limit: int = 25) -> ApiResponse:
        """Search for people on LinkedIn"""
        params = {
            "keywords": keywords,
            "start": "0",
            "count": str(limit)
        }
        
        return await self.make_request("GET", "/people-search", params=params)
    
    async def search_companies(self, keywords: str, limit: int = 25) -> ApiResponse:
        """Search for companies on LinkedIn"""
        params = {
            "keywords": keywords,
            "start": "0", 
            "count": str(limit)
        }
        
        return await self.make_request("GET", "/company-search", params=params)
    
    async def get_post_analytics(self, post_id: str) -> ApiResponse:
        """Get analytics for a specific post"""
        return await self.make_request("GET", f"/socialActions/{post_id}/comments")
    
    async def like_post(self, post_id: str) -> ApiResponse:
        """Like a LinkedIn post"""
        like_data = {
            "actor": f"urn:li:person:{await self._get_profile_id()}",
            "object": post_id
        }
        
        return await self.make_request("POST", "/socialActions/likes", data=like_data)
    
    async def comment_on_post(self, post_id: str, comment: str) -> ApiResponse:
        """Comment on a LinkedIn post"""
        comment_data = {
            "actor": f"urn:li:person:{await self._get_profile_id()}",
            "object": post_id,
            "message": {
                "text": comment
            }
        }
        
        return await self.make_request("POST", "/socialActions/comments", data=comment_data)
    
    async def get_skills(self) -> ApiResponse:
        """Get user's LinkedIn skills"""
        return await self.make_request("GET", "/people/~/skills")
    
    async def add_skill(self, skill_name: str) -> ApiResponse:
        """Add a skill to LinkedIn profile"""
        skill_data = {
            "name": {
                "localized": {
                    "en_US": skill_name
                },
                "preferredLocale": {
                    "country": "US",
                    "language": "en"
                }
            }
        }
        
        return await self.make_request("POST", "/people/~/skills", data=skill_data)
    
    # LinkedIn Automation Methods
    async def auto_connect_by_company(self, company_name: str, max_connections: int = 10) -> Dict[str, Any]:
        """Automatically connect with people from a specific company"""
        try:
            # Search for people at the company
            search_response = await self.search_people(f"company:{company_name}", limit=max_connections * 2)
            
            if not search_response.success:
                return {"error": "Failed to search for people", "success": False}
            
            people = search_response.data.get("elements", [])
            sent_requests = []
            
            for person in people[:max_connections]:
                profile_id = person.get("id")
                if profile_id:
                    # Send connection request
                    message = f"Hi! I'd like to connect as we both have connections to {company_name}."
                    request_response = await self.send_connection_request(profile_id, message)
                    
                    if request_response.success:
                        sent_requests.append(profile_id)
                    
                    # Rate limiting delay
                    await asyncio.sleep(2)
            
            return {
                "success": True,
                "connections_sent": len(sent_requests),
                "target_company": company_name,
                "profile_ids": sent_requests
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def auto_engage_posts(self, keywords: List[str], max_engagements: int = 5) -> Dict[str, Any]:
        """Automatically like and comment on posts with specific keywords"""
        try:
            engaged_posts = []
            
            for keyword in keywords:
                # This would require LinkedIn's content search API
                # For now, we'll use the user's network posts
                posts_response = await self.get_posts(count=20)
                
                if posts_response.success:
                    posts = posts_response.data.get("elements", [])
                    
                    for post in posts[:max_engagements // len(keywords)]:
                        post_id = post.get("id")
                        content = post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", "")
                        
                        if keyword.lower() in content.lower():
                            # Like the post
                            await self.like_post(post_id)
                            
                            # Add a relevant comment
                            comment = f"Great insights on {keyword}! Thanks for sharing."
                            await self.comment_on_post(post_id, comment)
                            
                            engaged_posts.append(post_id)
                            
                            # Rate limiting delay
                            await asyncio.sleep(3)
            
            return {
                "success": True,
                "engaged_posts": len(engaged_posts),
                "keywords": keywords,
                "post_ids": engaged_posts
            }
            
        except Exception as e:
            return {"error": str(e), "success": False}
    
    # Helper methods
    async def _get_profile_id(self) -> str:
        """Get the user's LinkedIn profile ID"""
        if not hasattr(self, '_cached_profile_id'):
            profile_response = await self.make_request("GET", "/people/~:(id)")
            if profile_response.success:
                self._cached_profile_id = profile_response.data.get("id")
            else:
                raise Exception("Could not get profile ID")
        
        return self._cached_profile_id