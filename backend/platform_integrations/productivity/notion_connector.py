import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability, ApiResponse

class NotionConnector(BasePlatformConnector):
    """Notion integration for productivity and knowledge management"""
    
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
        try:
            if not self.validate_credentials(["integration_token"]):
                return False
            
            self.auth_token = self.credentials["integration_token"]
            
            # Test authentication by listing users
            response = await self.make_request("GET", "/users")
            
            if response.success:
                self.logger.info("Notion authentication successful")
                return True
            else:
                self.logger.error(f"Notion authentication failed: {response.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Notion authentication error: {e}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Notion API connection"""
        try:
            start_time = datetime.now()
            response = await self.make_request("GET", "/users")
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": response.success,
                "platform": "notion",
                "response_time": response_time,
                "error": response.error if not response.success else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "platform": "notion",
                "error": str(e)
            }
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get Notion integration capabilities"""
        return [
            PlatformCapability(
                name="Database Management",
                description="Create, query and manage Notion databases",
                methods=["create_database", "query_database", "get_database", "update_database"],
                rate_limit=3
            ),
            PlatformCapability(
                name="Page Management",
                description="Create, read, update and manage Notion pages",
                methods=["create_page", "get_page", "update_page", "delete_page"],
                rate_limit=3
            ),
            PlatformCapability(
                name="Content Management",
                description="Manage blocks and content within pages",
                methods=["get_blocks", "append_blocks", "update_block", "delete_block"],
                rate_limit=3
            ),
            PlatformCapability(
                name="Search",
                description="Search across Notion workspace",
                methods=["search_pages", "search_databases"],
                rate_limit=3
            ),
            PlatformCapability(
                name="User Management",
                description="Manage workspace users and permissions",
                methods=["get_users", "get_user", "get_bot_user"],
                rate_limit=3
            )
        ]
    
    # Database Methods
    async def create_database(self, parent_page_id: str, title: str, 
                            properties: Dict[str, Any]) -> ApiResponse:
        """Create a new Notion database"""
        database_data = {
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ],
            "properties": properties
        }
        
        return await self.make_request("POST", "/databases", data=database_data)
    
    async def query_database(self, database_id: str, filter_data: Optional[Dict] = None,
                           sorts: Optional[List[Dict]] = None, start_cursor: Optional[str] = None,
                           page_size: int = 100) -> ApiResponse:
        """Query a Notion database"""
        query_data = {
            "page_size": page_size
        }
        
        if filter_data:
            query_data["filter"] = filter_data
        
        if sorts:
            query_data["sorts"] = sorts
        
        if start_cursor:
            query_data["start_cursor"] = start_cursor
        
        return await self.make_request("POST", f"/databases/{database_id}/query", data=query_data)
    
    async def get_database(self, database_id: str) -> ApiResponse:
        """Get database information"""
        return await self.make_request("GET", f"/databases/{database_id}")
    
    async def update_database(self, database_id: str, title: Optional[str] = None,
                            properties: Optional[Dict[str, Any]] = None) -> ApiResponse:
        """Update database properties"""
        update_data = {}
        
        if title:
            update_data["title"] = [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ]
        
        if properties:
            update_data["properties"] = properties
        
        return await self.make_request("PATCH", f"/databases/{database_id}", data=update_data)
    
    # Page Methods
    async def create_page(self, parent: Dict[str, Any], properties: Dict[str, Any],
                         children: Optional[List[Dict]] = None) -> ApiResponse:
        """Create a new Notion page"""
        page_data = {
            "parent": parent,
            "properties": properties
        }
        
        if children:
            page_data["children"] = children
        
        return await self.make_request("POST", "/pages", data=page_data)
    
    async def get_page(self, page_id: str) -> ApiResponse:
        """Get page information"""
        return await self.make_request("GET", f"/pages/{page_id}")
    
    async def update_page(self, page_id: str, properties: Dict[str, Any]) -> ApiResponse:
        """Update page properties"""
        update_data = {
            "properties": properties
        }
        
        return await self.make_request("PATCH", f"/pages/{page_id}", data=update_data)
    
    async def delete_page(self, page_id: str) -> ApiResponse:
        """Archive/delete a page"""
        update_data = {
            "archived": True
        }
        
        return await self.make_request("PATCH", f"/pages/{page_id}", data=update_data)
    
    # Block Methods
    async def get_blocks(self, block_id: str, start_cursor: Optional[str] = None,
                        page_size: int = 100) -> ApiResponse:
        """Get child blocks of a block"""
        params = {
            "page_size": str(page_size)
        }
        
        if start_cursor:
            params["start_cursor"] = start_cursor
        
        return await self.make_request("GET", f"/blocks/{block_id}/children", params=params)
    
    async def append_blocks(self, block_id: str, children: List[Dict[str, Any]]) -> ApiResponse:
        """Append blocks to a page or block"""
        append_data = {
            "children": children
        }
        
        return await self.make_request("PATCH", f"/blocks/{block_id}/children", data=append_data)
    
    async def update_block(self, block_id: str, block_data: Dict[str, Any]) -> ApiResponse:
        """Update a block"""
        return await self.make_request("PATCH", f"/blocks/{block_id}", data=block_data)
    
    async def delete_block(self, block_id: str) -> ApiResponse:
        """Delete a block"""
        update_data = {
            "archived": True
        }
        
        return await self.make_request("PATCH", f"/blocks/{block_id}", data=update_data)
    
    # Search Methods
    async def search_pages(self, query: str, filter_type: Optional[str] = None) -> ApiResponse:
        """Search for pages in workspace"""
        search_data = {
            "query": query
        }
        
        if filter_type:
            search_data["filter"] = {
                "value": filter_type,
                "property": "object"
            }
        
        return await self.make_request("POST", "/search", data=search_data)
    
    # User Methods
    async def get_users(self) -> ApiResponse:
        """Get all users in workspace"""
        return await self.make_request("GET", "/users")
    
    async def get_user(self, user_id: str) -> ApiResponse:
        """Get specific user information"""
        return await self.make_request("GET", f"/users/{user_id}")
    
    async def get_bot_user(self) -> ApiResponse:
        """Get bot user information"""
        return await self.make_request("GET", "/users/me")
    
    # Automation Helper Methods
    async def create_task_database(self, parent_page_id: str) -> ApiResponse:
        """Create a task management database"""
        properties = {
            "Task Name": {
                "title": {}
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "Not Started", "color": "red"},
                        {"name": "In Progress", "color": "yellow"},
                        {"name": "Completed", "color": "green"}
                    ]
                }
            },
            "Priority": {
                "select": {
                    "options": [
                        {"name": "Low", "color": "gray"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "High", "color": "red"}
                    ]
                }
            },
            "Due Date": {
                "date": {}
            },
            "Assignee": {
                "people": {}
            },
            "Description": {
                "rich_text": {}
            }
        }
        
        return await self.create_database(parent_page_id, "Task Management", properties)
    
    async def create_task(self, database_id: str, task_name: str, status: str = "Not Started",
                         priority: str = "Medium", due_date: Optional[str] = None,
                         description: Optional[str] = None) -> ApiResponse:
        """Create a task in task database"""
        properties = {
            "Task Name": {
                "title": [
                    {
                        "text": {
                            "content": task_name
                        }
                    }
                ]
            },
            "Status": {
                "select": {
                    "name": status
                }
            },
            "Priority": {
                "select": {
                    "name": priority
                }
            }
        }
        
        if due_date:
            properties["Due Date"] = {
                "date": {
                    "start": due_date
                }
            }
        
        if description:
            properties["Description"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": description
                        }
                    }
                ]
            }
        
        parent = {
            "type": "database_id",
            "database_id": database_id
        }
        
        return await self.create_page(parent, properties)
    
    async def create_note_page(self, parent_page_id: str, title: str, content: str) -> ApiResponse:
        """Create a simple note page"""
        parent = {
            "type": "page_id",
            "page_id": parent_page_id
        }
        
        properties = {
            "title": [
                {
                    "text": {
                        "content": title
                    }
                }
            ]
        }
        
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
        
        return await self.create_page(parent, properties, children)
    
    async def create_meeting_notes(self, parent_page_id: str, meeting_title: str,
                                 attendees: List[str], agenda: List[str],
                                 notes: str, action_items: List[str]) -> ApiResponse:
        """Create structured meeting notes"""
        children = []
        
        # Meeting info
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Meeting Information"}}]
            }
        })
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"Date: {datetime.now().strftime('%Y-%m-%d')}"}}]
            }
        })
        
        # Attendees
        attendees_text = ", ".join(attendees)
        children.append({
            "object": "block",
            "type": "paragraph", 
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"Attendees: {attendees_text}"}}]
            }
        })
        
        # Agenda
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Agenda"}}]
            }
        })
        
        for item in agenda:
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": item}}]
                }
            })
        
        # Notes
        children.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Notes"}}]
            }
        })
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": notes}}]
            }
        })
        
        # Action Items
        children.append({
            "object": "block",
            "type": "heading_2", 
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "Action Items"}}]
            }
        })
        
        for item in action_items:
            children.append({
                "object": "block",
                "type": "to_do",
                "to_do": {
                    "rich_text": [{"type": "text", "text": {"content": item}}],
                    "checked": False
                }
            })
        
        parent = {
            "type": "page_id",
            "page_id": parent_page_id
        }
        
        properties = {
            "title": [
                {
                    "text": {
                        "content": meeting_title
                    }
                }
            ]
        }
        
        return await self.create_page(parent, properties, children)
    
    async def get_overridden_headers(self) -> Dict[str, str]:
        """Get Notion-specific headers"""
        headers = await self._get_auth_headers()
        headers["Notion-Version"] = "2022-06-28"
        return headers
    
    async def make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, str]] = None,
                          headers: Optional[Dict[str, str]] = None) -> ApiResponse:
        """Override to add Notion-specific headers"""
        notion_headers = await self.get_overridden_headers()
        if headers:
            notion_headers.update(headers)
        
        return await super().make_request(method, endpoint, data, params, notion_headers)