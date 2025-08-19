"""
Google Drive Platform Integration for AETHER
Cloud storage and document management automation
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability

class GoogleDriveConnector(BasePlatformConnector):
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        super().__init__(credentials, config)
        self.access_token = credentials.get('access_token')
        self.refresh_token = credentials.get('refresh_token')
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
    
    @property
    def platform_name(self) -> str:
        return "google_drive"
    
    @property
    def auth_type(self) -> AuthType:
        return AuthType.OAUTH2
    
    @property
    def base_url(self) -> str:
        return "https://www.googleapis.com/drive/v3"
    
    async def authenticate(self) -> bool:
        """Authenticate with Google Drive API"""
        if not self.access_token:
            return False
        self.auth_token = self.access_token
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Google Drive API connection"""
        try:
            response = await self.make_request("GET", "/about", params={"fields": "user"})
            return {
                "success": response.success,
                "platform": "google_drive",
                "user": response.data.get("user", {}).get("displayName") if response.success else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get Google Drive platform capabilities"""
        return [
            PlatformCapability(
                name="file_management",
                description="Upload, download, and manage files",
                methods=["upload_file", "download_file", "delete_file", "move_file"]
            ),
            PlatformCapability(
                name="folder_management", 
                description="Create and organize folders",
                methods=["create_folder", "list_folders", "get_folder_contents"]
            ),
            PlatformCapability(
                name="sharing_management",
                description="Manage file and folder permissions",
                methods=["share_file", "get_permissions", "update_permissions"]
            ),
            PlatformCapability(
                name="document_collaboration",
                description="Collaborate on Google Docs, Sheets, Slides",
                methods=["create_document", "get_document_content", "update_document"]
            ),
            PlatformCapability(
                name="storage_analytics",
                description="Analyze storage usage and organization",
                methods=["get_storage_quota", "analyze_file_types", "generate_usage_report"]
            )
        ]
    
    # File Management
    async def list_files(self, folder_id: str = None, query: str = None, max_results: int = 100) -> Dict[str, Any]:
        """List files in Drive"""
        params = {
            "pageSize": str(max_results),
            "fields": "files(id,name,mimeType,size,createdTime,modifiedTime,parents)"
        }
        
        # Build query
        query_parts = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if query:
            query_parts.append(f"name contains '{query}'")
        
        if query_parts:
            params["q"] = " and ".join(query_parts)
            
        response = await self.make_request("GET", "/files", params=params)
        return {"success": response.success, "files": response.data.get("files", []) if response.success else []}
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get detailed file information"""
        params = {"fields": "id,name,mimeType,size,createdTime,modifiedTime,parents,permissions,webViewLink"}
        response = await self.make_request("GET", f"/files/{file_id}", params=params)
        return {"success": response.success, "file": response.data}
    
    async def create_folder(self, name: str, parent_id: str = None) -> Dict[str, Any]:
        """Create a new folder"""
        folder_data = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        
        if parent_id:
            folder_data["parents"] = [parent_id]
            
        response = await self.make_request("POST", "/files", data=folder_data)
        return {"success": response.success, "folder": response.data}
    
    async def move_file(self, file_id: str, new_parent_id: str, old_parent_id: str = None) -> Dict[str, Any]:
        """Move file to different folder"""
        params = {"addParents": new_parent_id}
        if old_parent_id:
            params["removeParents"] = old_parent_id
            
        response = await self.make_request("PATCH", f"/files/{file_id}", params=params)
        return {"success": response.success, "file": response.data}
    
    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete file permanently"""
        response = await self.make_request("DELETE", f"/files/{file_id}")
        return {"success": response.success}
    
    # Sharing Management
    async def share_file(self, file_id: str, email: str, role: str = "reader", type: str = "user") -> Dict[str, Any]:
        """Share file with user"""
        permission_data = {
            "role": role,  # reader, writer, commenter
            "type": type,  # user, group, domain, anyone
            "emailAddress": email
        }
        
        response = await self.make_request("POST", f"/files/{file_id}/permissions", data=permission_data)
        return {"success": response.success, "permission": response.data}
    
    async def get_permissions(self, file_id: str) -> Dict[str, Any]:
        """Get file permissions"""
        response = await self.make_request("GET", f"/files/{file_id}/permissions")
        return {"success": response.success, "permissions": response.data.get("permissions", []) if response.success else []}
    
    async def make_public(self, file_id: str) -> Dict[str, Any]:
        """Make file publicly accessible"""
        permission_data = {
            "role": "reader",
            "type": "anyone"
        }
        
        response = await self.make_request("POST", f"/files/{file_id}/permissions", data=permission_data)
        if response.success:
            # Get public link
            file_info = await self.get_file_info(file_id)
            return {
                "success": True,
                "public_link": file_info.get("file", {}).get("webViewLink"),
                "permission": response.data
            }
        return response.dict()
    
    # Document Operations (Google Docs/Sheets/Slides)
    async def create_document(self, title: str, doc_type: str = "document") -> Dict[str, Any]:
        """Create Google Workspace document"""
        mime_types = {
            "document": "application/vnd.google-apps.document",
            "spreadsheet": "application/vnd.google-apps.spreadsheet", 
            "presentation": "application/vnd.google-apps.presentation"
        }
        
        doc_data = {
            "name": title,
            "mimeType": mime_types.get(doc_type, mime_types["document"])
        }
        
        response = await self.make_request("POST", "/files", data=doc_data)
        return {"success": response.success, "document": response.data}
    
    # Storage Analytics
    async def get_storage_quota(self) -> Dict[str, Any]:
        """Get storage usage information"""
        params = {"fields": "storageQuota"}
        response = await self.make_request("GET", "/about", params=params)
        
        if response.success and "storageQuota" in response.data:
            quota = response.data["storageQuota"]
            return {
                "success": True,
                "storage": {
                    "limit": int(quota.get("limit", 0)),
                    "usage": int(quota.get("usage", 0)),
                    "usage_in_drive": int(quota.get("usageInDrive", 0)),
                    "usage_in_photos": int(quota.get("usageInDriveTrash", 0)),
                    "available": int(quota.get("limit", 0)) - int(quota.get("usage", 0))
                }
            }
        return {"success": False, "error": "Could not retrieve storage information"}
    
    async def analyze_file_types(self, folder_id: str = None) -> Dict[str, Any]:
        """Analyze file types in drive or folder"""
        files_result = await self.list_files(folder_id=folder_id, max_results=1000)
        if not files_result["success"]:
            return files_result
        
        files = files_result["files"]
        file_type_stats = {}
        total_size = 0
        
        for file in files:
            mime_type = file.get("mimeType", "unknown")
            file_size = int(file.get("size", 0))
            
            if mime_type not in file_type_stats:
                file_type_stats[mime_type] = {
                    "count": 0,
                    "total_size": 0,
                    "files": []
                }
            
            file_type_stats[mime_type]["count"] += 1
            file_type_stats[mime_type]["total_size"] += file_size
            file_type_stats[mime_type]["files"].append({
                "name": file["name"],
                "id": file["id"],
                "size": file_size
            })
            
            total_size += file_size
        
        # Convert to more readable format
        analysis = {
            "total_files": len(files),
            "total_size": total_size,
            "file_types": []
        }
        
        for mime_type, stats in file_type_stats.items():
            analysis["file_types"].append({
                "mime_type": mime_type,
                "count": stats["count"],
                "total_size": stats["total_size"],
                "percentage": round((stats["total_size"] / total_size * 100), 2) if total_size > 0 else 0,
                "average_size": round(stats["total_size"] / stats["count"]) if stats["count"] > 0 else 0
            })
        
        # Sort by total size
        analysis["file_types"].sort(key=lambda x: x["total_size"], reverse=True)
        
        return {"success": True, "analysis": analysis}
    
    # Bulk Operations
    async def bulk_organize_files(self, organization_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk organize files based on rules"""
        results = []
        
        for rule in organization_rules:
            rule_type = rule["type"]  # "move_by_type", "move_by_name", etc.
            
            if rule_type == "move_by_type":
                mime_type = rule["mime_type"]
                target_folder = rule["target_folder_id"]
                
                # Find files of this type
                files = await self.list_files(query=f"mimeType='{mime_type}'")
                if files["success"]:
                    moved_count = 0
                    for file in files["files"]:
                        move_result = await self.move_file(file["id"], target_folder)
                        if move_result["success"]:
                            moved_count += 1
                        await asyncio.sleep(0.1)  # Rate limiting
                    
                    results.append({
                        "rule": rule_type,
                        "mime_type": mime_type,
                        "moved_files": moved_count
                    })
        
        return {"success": True, "organization_results": results}
    
    async def cleanup_duplicates(self, folder_id: str = None) -> Dict[str, Any]:
        """Find and optionally remove duplicate files"""
        files_result = await self.list_files(folder_id=folder_id, max_results=1000)
        if not files_result["success"]:
            return files_result
        
        files = files_result["files"]
        name_groups = {}
        
        # Group files by name
        for file in files:
            name = file["name"]
            if name not in name_groups:
                name_groups[name] = []
            name_groups[name].append(file)
        
        # Find duplicates
        duplicates = []
        for name, file_group in name_groups.items():
            if len(file_group) > 1:
                # Sort by modification time (keep newest)
                file_group.sort(key=lambda f: f.get("modifiedTime", ""), reverse=True)
                duplicates.append({
                    "name": name,
                    "total_copies": len(file_group),
                    "newest_file": file_group[0],
                    "duplicate_files": file_group[1:]
                })
        
        return {
            "success": True,
            "total_files_scanned": len(files),
            "duplicate_groups": len(duplicates),
            "total_duplicates": sum(len(d["duplicate_files"]) for d in duplicates),
            "duplicates": duplicates
        }