"""
Discord Platform Integration for AETHER  
Community management and bot automation
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability

class DiscordConnector(BasePlatformConnector):
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        super().__init__(credentials, config)
        self.bot_token = credentials.get('bot_token')
        self.guild_id = credentials.get('guild_id')
    
    @property
    def platform_name(self) -> str:
        return "discord"
    
    @property
    def auth_type(self) -> AuthType:
        return AuthType.BEARER_TOKEN
    
    @property  
    def base_url(self) -> str:
        return "https://discord.com/api/v10"
    
    async def authenticate(self) -> bool:
        """Authenticate with Discord API"""
        if not self.bot_token:
            return False
        self.auth_token = self.bot_token
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Discord API connection"""
        try:
            response = await self.make_request("GET", "/users/@me")
            return {
                "success": response.success,
                "platform": "discord", 
                "bot_user": response.data.get("username") if response.success else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get Discord platform capabilities"""
        return [
            PlatformCapability(
                name="message_management",
                description="Send and manage messages in channels", 
                methods=["send_message", "get_messages", "delete_message"]
            ),
            PlatformCapability(
                name="server_management",
                description="Manage Discord server settings",
                methods=["get_guild_info", "manage_roles", "manage_channels"]
            ),
            PlatformCapability(
                name="member_management", 
                description="Manage server members and permissions",
                methods=["get_members", "kick_member", "ban_member"]
            ),
            PlatformCapability(
                name="webhook_integration",
                description="Create and manage webhooks for automation",
                methods=["create_webhook", "execute_webhook"]
            )
        ]
    
    # Message Management
    async def send_message(self, channel_id: str, content: str, embeds: List[Dict] = None) -> Dict[str, Any]:
        """Send message to Discord channel"""
        message_data = {"content": content}
        if embeds:
            message_data["embeds"] = embeds
            
        response = await self.make_request("POST", f"/channels/{channel_id}/messages", data=message_data)
        return {"success": response.success, "message_id": response.data.get("id") if response.success else None}
    
    async def get_messages(self, channel_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from Discord channel"""
        response = await self.make_request("GET", f"/channels/{channel_id}/messages", params={"limit": str(limit)})
        return {"success": response.success, "messages": response.data}
    
    # Server Management  
    async def get_guild_info(self) -> Dict[str, Any]:
        """Get Discord server information"""
        if not self.guild_id:
            return {"success": False, "error": "No guild ID configured"}
        
        response = await self.make_request("GET", f"/guilds/{self.guild_id}")
        return {"success": response.success, "guild": response.data}
    
    async def get_members(self, limit: int = 100) -> Dict[str, Any]:
        """Get server members"""
        if not self.guild_id:
            return {"success": False, "error": "No guild ID configured"}
        
        response = await self.make_request("GET", f"/guilds/{self.guild_id}/members", params={"limit": str(limit)})
        return {"success": response.success, "members": response.data}
    
    # Webhook Management
    async def create_webhook(self, channel_id: str, name: str) -> Dict[str, Any]:
        """Create webhook for channel automation"""
        webhook_data = {"name": name}
        response = await self.make_request("POST", f"/channels/{channel_id}/webhooks", data=webhook_data)
        return {"success": response.success, "webhook": response.data}
    
    async def execute_webhook(self, webhook_url: str, content: str, username: str = None) -> Dict[str, Any]:
        """Execute webhook to send automated message"""
        webhook_data = {"content": content}
        if username:
            webhook_data["username"] = username
            
        # Direct webhook execution (not through Discord API)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=webhook_data) as response:
                    return {"success": response.status < 300}
        except Exception as e:
            return {"success": False, "error": str(e)}