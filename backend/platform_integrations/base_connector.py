from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import logging
from enum import Enum
from pydantic import BaseModel

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"

class AuthType(Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    CUSTOM = "custom"

class PlatformCapability(BaseModel):
    name: str
    description: str
    methods: List[str]
    rate_limit: Optional[int] = None
    requires_premium: bool = False

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

class BasePlatformConnector(ABC):
    """Base class for all platform integrations"""
    
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        self.credentials = credentials
        self.config = config or {}
        self.status = ConnectionStatus.DISCONNECTED
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(f"connector.{self.platform_name}")
        
        # Rate limiting
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        self.request_queue = asyncio.Queue()
        
        # Authentication
        self.auth_token = None
        self.auth_expires_at = None
        
        # Statistics
        self.stats = {
            "requests_made": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "last_request": None,
            "connection_time": None
        }
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform name identifier"""
        pass
    
    @property
    @abstractmethod
    def auth_type(self) -> AuthType:
        """Authentication type used by the platform"""
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for API endpoints"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the platform"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get platform capabilities"""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the connector"""
        try:
            self.status = ConnectionStatus.CONNECTING
            
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Authenticate
            auth_success = await self.authenticate()
            if not auth_success:
                self.status = ConnectionStatus.ERROR
                return False
            
            # Test connection
            test_result = await self.test_connection()
            if not test_result.get("success", False):
                self.status = ConnectionStatus.ERROR
                return False
            
            self.status = ConnectionStatus.CONNECTED
            self.stats["connection_time"] = datetime.now()
            
            self.logger.info(f"{self.platform_name} connector initialized successfully")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.logger.error(f"Failed to initialize {self.platform_name} connector: {e}")
            return False
    
    async def make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, str]] = None,
                          headers: Optional[Dict[str, str]] = None) -> ApiResponse:
        """Make an API request with rate limiting and error handling"""
        
        if not self.session:
            return ApiResponse(success=False, error="Connector not initialized")
        
        # Check authentication
        if await self._is_auth_expired():
            await self.authenticate()
        
        # Apply rate limiting
        await self._handle_rate_limiting()
        
        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        request_headers = await self._get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        try:
            self.stats["requests_made"] += 1
            self.stats["last_request"] = datetime.now()
            
            async with self.session.request(
                method=method.upper(),
                url=url,
                json=data if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
                params=params,
                headers=request_headers
            ) as response:
                
                # Update rate limit info
                await self._update_rate_limit_info(response)
                
                # Handle response
                if response.status == 429:  # Rate limited
                    self.stats["rate_limited_requests"] += 1
                    self.status = ConnectionStatus.RATE_LIMITED
                    
                    return ApiResponse(
                        success=False,
                        error="Rate limited",
                        rate_limit_remaining=0,
                        rate_limit_reset=self.rate_limit_reset
                    )
                
                response_data = None
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                if 200 <= response.status < 300:
                    self.stats["successful_requests"] += 1
                    return ApiResponse(
                        success=True,
                        data=response_data,
                        rate_limit_remaining=self.rate_limit_remaining,
                        rate_limit_reset=self.rate_limit_reset
                    )
                else:
                    self.stats["failed_requests"] += 1
                    return ApiResponse(
                        success=False,
                        error=f"HTTP {response.status}: {response_data}",
                        rate_limit_remaining=self.rate_limit_remaining,
                        rate_limit_reset=self.rate_limit_reset
                    )
                    
        except Exception as e:
            self.stats["failed_requests"] += 1
            self.logger.error(f"Request failed: {e}")
            
            return ApiResponse(
                success=False,
                error=str(e)
            )
    
    async def _is_auth_expired(self) -> bool:
        """Check if authentication token has expired"""
        if not self.auth_expires_at:
            return False
        
        return datetime.now() >= self.auth_expires_at
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        headers = {
            "User-Agent": "AETHER/2.0 Platform Connector",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if self.auth_type == AuthType.API_KEY:
            api_key = self.credentials.get("api_key")
            if api_key:
                # Different platforms use different header names
                key_header = self.config.get("api_key_header", "Authorization")
                if key_header == "Authorization":
                    headers["Authorization"] = f"Bearer {api_key}"
                else:
                    headers[key_header] = api_key
        
        elif self.auth_type == AuthType.BEARER_TOKEN:
            token = self.auth_token or self.credentials.get("access_token")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        
        elif self.auth_type == AuthType.BASIC_AUTH:
            username = self.credentials.get("username")
            password = self.credentials.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        return headers
    
    async def _handle_rate_limiting(self):
        """Handle rate limiting with exponential backoff"""
        if self.status == ConnectionStatus.RATE_LIMITED:
            if self.rate_limit_reset and datetime.now() < self.rate_limit_reset:
                wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
                await asyncio.sleep(min(wait_time, 60))  # Max 1 minute wait
            
            self.status = ConnectionStatus.CONNECTED
    
    async def _update_rate_limit_info(self, response: aiohttp.ClientResponse):
        """Update rate limit information from response headers"""
        # Common rate limit headers
        remaining_headers = [
            "X-RateLimit-Remaining",
            "X-Rate-Limit-Remaining", 
            "RateLimit-Remaining"
        ]
        
        reset_headers = [
            "X-RateLimit-Reset",
            "X-Rate-Limit-Reset",
            "RateLimit-Reset"
        ]
        
        # Try to find rate limit remaining
        for header in remaining_headers:
            if header in response.headers:
                try:
                    self.rate_limit_remaining = int(response.headers[header])
                    break
                except ValueError:
                    pass
        
        # Try to find rate limit reset time
        for header in reset_headers:
            if header in response.headers:
                try:
                    reset_timestamp = int(response.headers[header])
                    self.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
                    break
                except ValueError:
                    pass
    
    async def get_status(self) -> Dict[str, Any]:
        """Get connector status and statistics"""
        return {
            "platform": self.platform_name,
            "status": self.status.value,
            "auth_type": self.auth_type.value,
            "stats": self.stats,
            "rate_limit": {
                "remaining": self.rate_limit_remaining,
                "reset": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None
            },
            "capabilities": [cap.dict() for cap in await self.get_capabilities()]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            test_result = await self.test_connection()
            
            return {
                "healthy": test_result.get("success", False),
                "platform": self.platform_name,
                "status": self.status.value,
                "last_check": datetime.now().isoformat(),
                "response_time": test_result.get("response_time"),
                "error": test_result.get("error")
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "platform": self.platform_name,
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def refresh_auth(self) -> bool:
        """Refresh authentication if supported"""
        try:
            return await self.authenticate()
        except Exception as e:
            self.logger.error(f"Failed to refresh auth: {e}")
            return False
    
    async def close(self):
        """Close the connector and cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.status = ConnectionStatus.DISCONNECTED
        self.logger.info(f"{self.platform_name} connector closed")
    
    # Common utility methods for subclasses
    async def paginate_request(self, endpoint: str, params: Optional[Dict[str, str]] = None,
                              page_param: str = "page", per_page_param: str = "per_page",
                              max_pages: int = 10) -> List[Any]:
        """Handle paginated API requests"""
        all_results = []
        page = 1
        
        while page <= max_pages:
            page_params = params.copy() if params else {}
            page_params[page_param] = str(page)
            
            if per_page_param not in page_params:
                page_params[per_page_param] = "100"  # Default page size
            
            response = await self.make_request("GET", endpoint, params=page_params)
            
            if not response.success:
                break
            
            page_data = response.data
            if isinstance(page_data, dict):
                # Try common pagination response formats
                items = (
                    page_data.get("items") or
                    page_data.get("data") or 
                    page_data.get("results") or
                    page_data.get("content") or
                    []
                )
            elif isinstance(page_data, list):
                items = page_data
            else:
                break
            
            if not items:
                break
            
            all_results.extend(items)
            
            # Check if there are more pages
            if isinstance(page_data, dict):
                has_next = (
                    page_data.get("has_next") or
                    page_data.get("has_more") or
                    (page_data.get("total_pages", 0) > page)
                )
                
                if not has_next:
                    break
            
            page += 1
        
        return all_results
    
    def validate_credentials(self, required_fields: List[str]) -> bool:
        """Validate that required credential fields are present"""
        missing_fields = [field for field in required_fields if field not in self.credentials]
        
        if missing_fields:
            self.logger.error(f"Missing required credentials: {missing_fields}")
            return False
        
        return True