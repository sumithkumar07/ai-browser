"""
Notion Platform Integration for AETHER
Knowledge management and database automation
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability

class NotionConnector(BasePlatformConnector):
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        super().__init__(credentials, config)
        self.access_token = credentials.get('access_token')
        self.version = "2022-06-28"  # Notion API version
    
    @property
    def platform_name(self) -> str:
        return "notion"
    
    @property
    def auth_type(self) -> AuthType:
        return AuthType.BEARER_TOKEN
    
    @property
    def base_url(self) -> str:
        return "https://api.notion.com/v1"
    
    async def authenticate(self) -> bool:
        """Authenticate with Notion API"""
        if not self.access_token:
            return False
        self.auth_token = self.access_token
        return True
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get Notion-specific headers"""
        headers = await super()._get_auth_headers()
        headers["Notion-Version"] = self.version
        return headers
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Notion API connection"""
        try:
            response = await self.make_request("GET", "/users/me")
            return {
                "success": response.success,
                "platform": "notion",
                "user": response.data.get("name") if response.success else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get Notion platform capabilities"""
        return [
            PlatformCapability(
                name="database_management",
                description="Create and manage Notion databases",
                methods=["create_database", "query_database", "get_database"]
            ),
            PlatformCapability(
                name="page_management",
                description="Create and manage Notion pages",
                methods=["create_page", "get_page", "update_page", "delete_page"]
            ),
            PlatformCapability(
                name="content_automation",
                description="Automate content creation and updates",
                methods=["bulk_create_pages", "sync_data", "generate_reports"]
            ),
            PlatformCapability(
                name="workspace_integration",
                description="Integrate with workspace and teams",
                methods=["get_workspace_info", "manage_permissions"]
            )
        ]
    
    # Database Management
    async def create_database(self, parent_page_id: str, title: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Notion database"""
        database_data = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": properties
        }
        
        response = await self.make_request("POST", "/databases", data=database_data)
        return {"success": response.success, "database": response.data}
    
    async def query_database(self, database_id: str, filter_conditions: Dict = None, sorts: List[Dict] = None) -> Dict[str, Any]:
        """Query a Notion database"""
        query_data = {}
        
        if filter_conditions:
            query_data["filter"] = filter_conditions
        if sorts:
            query_data["sorts"] = sorts
            
        response = await self.make_request("POST", f"/databases/{database_id}/query", data=query_data)
        return {"success": response.success, "results": response.data.get("results", []) if response.success else []}
    
    async def get_database(self, database_id: str) -> Dict[str, Any]:
        """Get database information"""
        response = await self.make_request("GET", f"/databases/{database_id}")
        return {"success": response.success, "database": response.data}
    
    # Page Management  
    async def create_page(self, parent_id: str, parent_type: str, title: str, content: List[Dict] = None) -> Dict[str, Any]:
        """Create a new Notion page"""
        page_data = {
            "parent": {
                "type": parent_type,  # "page_id" or "database_id"
                parent_type: parent_id
            },
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            }
        }
        
        if content:
            page_data["children"] = content
            
        response = await self.make_request("POST", "/pages", data=page_data)
        return {"success": response.success, "page": response.data}
    
    async def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page information"""
        response = await self.make_request("GET", f"/pages/{page_id}")
        return {"success": response.success, "page": response.data}
    
    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update page properties"""
        update_data = {"properties": properties}
        
        response = await self.make_request("PATCH", f"/pages/{page_id}", data=update_data)
        return {"success": response.success, "page": response.data}
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get page content blocks"""
        response = await self.make_request("GET", f"/blocks/{page_id}/children")
        return {"success": response.success, "blocks": response.data.get("results", []) if response.success else []}
    
    async def append_page_content(self, page_id: str, blocks: List[Dict]) -> Dict[str, Any]:
        """Append content blocks to page"""
        content_data = {"children": blocks}
        
        response = await self.make_request("PATCH", f"/blocks/{page_id}/children", data=content_data)
        return {"success": response.success, "results": response.data}
    
    # Content Automation
    async def bulk_create_pages(self, database_id: str, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple pages in bulk"""
        results = []
        
        for page_data in pages_data:
            result = await self.create_page(
                parent_id=database_id,
                parent_type="database_id", 
                title=page_data["title"],
                content=page_data.get("content")
            )
            results.append(result)
            await asyncio.sleep(0.5)  # Rate limiting
        
        successful_creates = sum(1 for result in results if result["success"])
        return {
            "success": successful_creates > 0,
            "total_pages": len(pages_data),
            "successful_creates": successful_creates,
            "results": results
        }
    
    async def sync_external_data(self, database_id: str, external_data: List[Dict], mapping: Dict[str, str]) -> Dict[str, Any]:
        """Sync external data to Notion database"""
        synced_records = 0
        
        for record in external_data:
            # Map external fields to Notion properties
            notion_properties = {}
            for external_field, notion_field in mapping.items():
                if external_field in record:
                    notion_properties[notion_field] = {
                        "rich_text": [{"type": "text", "text": {"content": str(record[external_field])}}]
                    }
            
            # Create page with mapped data
            result = await self.create_page(
                parent_id=database_id,
                parent_type="database_id",
                title=record.get("title", "Synced Record"),
                content=None
            )
            
            if result["success"] and notion_properties:
                # Update with properties
                await self.update_page(result["page"]["id"], notion_properties)
                synced_records += 1
            
            await asyncio.sleep(0.3)  # Rate limiting
        
        return {
            "success": synced_records > 0,
            "total_records": len(external_data),
            "synced_records": synced_records
        }
    
    async def generate_database_report(self, database_id: str) -> Dict[str, Any]:
        """Generate analytics report for database"""
        try:
            # Get database info
            db_info = await self.get_database(database_id)
            if not db_info["success"]:
                return db_info
            
            # Query all records
            all_records = await self.query_database(database_id)
            if not all_records["success"]:
                return all_records
            
            records = all_records["results"]
            
            # Generate analytics
            total_pages = len(records)
            properties = db_info["database"]["properties"]
            
            # Analyze properties
            property_stats = {}
            for prop_name, prop_config in properties.items():
                prop_type = prop_config["type"]
                property_stats[prop_name] = {
                    "type": prop_type,
                    "filled_count": 0,
                    "empty_count": 0
                }
            
            # Count filled vs empty properties
            for record in records:
                record_props = record.get("properties", {})
                for prop_name in properties.keys():
                    if prop_name in record_props:
                        prop_value = record_props[prop_name]
                        is_filled = self._is_property_filled(prop_value)
                        if is_filled:
                            property_stats[prop_name]["filled_count"] += 1
                        else:
                            property_stats[prop_name]["empty_count"] += 1
            
            report = {
                "database_id": database_id,
                "database_title": db_info["database"]["title"][0]["text"]["content"],
                "total_pages": total_pages,
                "property_count": len(properties),
                "property_statistics": property_stats,
                "generated_at": datetime.now().isoformat(),
                "completeness_score": self._calculate_completeness_score(property_stats, total_pages)
            }
            
            return {"success": True, "report": report}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _is_property_filled(self, property_value: Dict[str, Any]) -> bool:
        """Check if a property has a value"""
        prop_type = property_value.get("type")
        
        if prop_type == "title":
            return bool(property_value.get("title"))
        elif prop_type == "rich_text":
            return bool(property_value.get("rich_text"))
        elif prop_type == "number":
            return property_value.get("number") is not None
        elif prop_type == "select":
            return property_value.get("select") is not None
        elif prop_type == "multi_select":
            return bool(property_value.get("multi_select"))
        elif prop_type == "date":
            return property_value.get("date") is not None
        elif prop_type == "checkbox":
            return True  # Checkbox always has a value
        elif prop_type == "url":
            return bool(property_value.get("url"))
        elif prop_type == "email":
            return bool(property_value.get("email"))
        elif prop_type == "phone_number":
            return bool(property_value.get("phone_number"))
        else:
            return False
    
    def _calculate_completeness_score(self, property_stats: Dict[str, Any], total_pages: int) -> float:
        """Calculate database completeness score"""
        if total_pages == 0:
            return 0.0
        
        total_filled = sum(stats["filled_count"] for stats in property_stats.values())
        total_possible = len(property_stats) * total_pages
        
        return round((total_filled / total_possible) * 100, 2) if total_possible > 0 else 0.0
    
    # Workspace Integration
    async def get_workspace_users(self) -> Dict[str, Any]:
        """Get workspace users"""
        response = await self.make_request("GET", "/users")
        return {"success": response.success, "users": response.data.get("results", []) if response.success else []}
    
    async def search_workspace(self, query: str, filter_type: str = None) -> Dict[str, Any]:
        """Search workspace content"""
        search_data = {"query": query}
        
        if filter_type:
            search_data["filter"] = {"property": "type", "value": filter_type}
            
        response = await self.make_request("POST", "/search", data=search_data)
        return {"success": response.success, "results": response.data.get("results", []) if response.success else []}