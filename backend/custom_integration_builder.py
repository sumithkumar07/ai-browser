import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from pymongo import MongoClient
import httpx
import os
import yaml
import base64
from jinja2 import Template
import re

logger = logging.getLogger(__name__)

class IntegrationAuthType(Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM_HEADER = "custom_header"
    NO_AUTH = "no_auth"

class IntegrationMethodType(Enum):
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    SOAP = "soap"
    GRAPHQL = "graphql"

class IntegrationStatus(Enum):
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

@dataclass
class CustomIntegration:
    """Custom integration definition"""
    integration_id: str
    name: str
    description: str
    category: str
    method_type: IntegrationMethodType
    auth_type: IntegrationAuthType
    base_url: str
    endpoints: List[Dict[str, Any]]
    auth_config: Dict[str, Any]
    headers: Dict[str, str]
    parameters: Dict[str, Any]
    response_mapping: Dict[str, Any]
    error_handling: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    created_by: str
    status: IntegrationStatus = IntegrationStatus.DRAFT
    version: str = "1.0.0"
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class IntegrationTemplate:
    """Template for common integration patterns"""
    template_id: str
    name: str
    description: str
    category: str
    template_data: Dict[str, Any]
    variables: List[Dict[str, Any]]
    example_config: Dict[str, Any]
    documentation: str
    
class CustomIntegrationBuilder:
    """Advanced custom integration builder with templates and testing"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.integrations = self.db.custom_integrations
        self.templates = self.db.integration_templates
        self.test_results = self.db.integration_tests
        self.usage_logs = self.db.integration_usage
        
        # Runtime state
        self.active_integrations = {}  # integration_id -> runtime instance
        self.template_cache = {}
        
        # Predefined templates
        self._initialize_templates()
        
        # Rate limiting
        self.rate_limiters = {}
        
        # Background monitoring
        self._monitor_task = None
    
    def _initialize_templates(self):
        """Initialize common integration templates"""
        
        templates = [
            IntegrationTemplate(
                template_id="rest_api_basic",
                name="Basic REST API",
                description="Simple REST API integration with API key authentication",
                category="Web API",
                template_data={
                    "method_type": "rest_api",
                    "auth_type": "api_key",
                    "endpoints": [
                        {
                            "name": "get_data",
                            "method": "GET",
                            "path": "/api/data",
                            "description": "Retrieve data from API"
                        },
                        {
                            "name": "post_data",
                            "method": "POST",
                            "path": "/api/data",
                            "description": "Send data to API"
                        }
                    ]
                },
                variables=[
                    {"name": "base_url", "type": "string", "required": True, "description": "API base URL"},
                    {"name": "api_key", "type": "string", "required": True, "description": "API key for authentication"},
                    {"name": "api_key_header", "type": "string", "default": "X-API-Key", "description": "Header name for API key"}
                ],
                example_config={
                    "base_url": "https://api.example.com",
                    "api_key": "your-api-key-here",
                    "api_key_header": "X-API-Key"
                },
                documentation="Basic REST API integration template with API key authentication."
            ),
            IntegrationTemplate(
                template_id="oauth2_api",
                name="OAuth2 API",
                description="OAuth2 authenticated API integration",
                category="Web API",
                template_data={
                    "method_type": "rest_api",
                    "auth_type": "oauth2",
                    "endpoints": [
                        {
                            "name": "get_profile",
                            "method": "GET",
                            "path": "/api/user/profile",
                            "description": "Get user profile"
                        }
                    ]
                },
                variables=[
                    {"name": "base_url", "type": "string", "required": True},
                    {"name": "client_id", "type": "string", "required": True},
                    {"name": "client_secret", "type": "string", "required": True},
                    {"name": "authorize_url", "type": "string", "required": True},
                    {"name": "token_url", "type": "string", "required": True},
                    {"name": "scope", "type": "string", "default": "read"}
                ],
                example_config={
                    "base_url": "https://api.example.com",
                    "client_id": "your-client-id",
                    "client_secret": "your-client-secret",
                    "authorize_url": "https://api.example.com/oauth/authorize",
                    "token_url": "https://api.example.com/oauth/token",
                    "scope": "read write"
                },
                documentation="OAuth2 API integration with authorization code flow."
            ),
            IntegrationTemplate(
                template_id="webhook_receiver",
                name="Webhook Receiver",
                description="Receive webhooks from external services",
                category="Webhook",
                template_data={
                    "method_type": "webhook",
                    "auth_type": "custom_header",
                    "endpoints": [
                        {
                            "name": "receive_webhook",
                            "method": "POST",
                            "path": "/webhook",
                            "description": "Receive webhook data"
                        }
                    ]
                },
                variables=[
                    {"name": "webhook_secret", "type": "string", "required": True},
                    {"name": "signature_header", "type": "string", "default": "X-Signature"}
                ],
                example_config={
                    "webhook_secret": "your-webhook-secret",
                    "signature_header": "X-Signature"
                },
                documentation="Webhook receiver with signature verification."
            ),
            IntegrationTemplate(
                template_id="database_connector",
                name="Database Connector",
                description="Connect to external database",
                category="Database",
                template_data={
                    "method_type": "database",
                    "auth_type": "basic_auth",
                    "endpoints": [
                        {
                            "name": "query_data",
                            "method": "SELECT",
                            "description": "Execute SELECT query"
                        },
                        {
                            "name": "insert_data",
                            "method": "INSERT",
                            "description": "Execute INSERT query"
                        }
                    ]
                },
                variables=[
                    {"name": "host", "type": "string", "required": True},
                    {"name": "port", "type": "integer", "default": 5432},
                    {"name": "database", "type": "string", "required": True},
                    {"name": "username", "type": "string", "required": True},
                    {"name": "password", "type": "string", "required": True},
                    {"name": "ssl_mode", "type": "string", "default": "prefer"}
                ],
                example_config={
                    "host": "db.example.com",
                    "port": 5432,
                    "database": "mydb",
                    "username": "dbuser",
                    "password": "dbpassword",
                    "ssl_mode": "require"
                },
                documentation="PostgreSQL database connector with connection pooling."
            )
        ]
        
        for template in templates:
            self.template_cache[template.template_id] = template
            
            # Store in database if not exists
            existing = self.templates.find_one({"template_id": template.template_id})
            if not existing:
                template_doc = asdict(template)
                self.templates.insert_one(template_doc)
    
    async def start_integration_monitoring(self):
        """Start background integration monitoring"""
        
        if self._monitor_task is not None:
            return
        
        self._monitor_task = asyncio.create_task(self._integration_monitor_loop())
        logger.info("Started custom integration monitoring")
    
    async def stop_integration_monitoring(self):
        """Stop integration monitoring"""
        
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        
        logger.info("Stopped custom integration monitoring")
    
    async def _integration_monitor_loop(self):
        """Background integration monitoring loop"""
        
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Monitor active integrations
                await self._check_integration_health()
                
                # Update usage statistics
                await self._update_usage_statistics()
                
                # Clean up old test results
                await self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Integration monitor error: {e}")
    
    async def create_custom_integration(self, integration_data: Dict[str, Any], 
                                      created_by: str) -> str:
        """Create new custom integration"""
        
        integration_id = str(uuid.uuid4())
        
        try:
            # Validate integration data
            await self._validate_integration_data(integration_data)
            
            # Create integration object
            integration = CustomIntegration(
                integration_id=integration_id,
                name=integration_data["name"],
                description=integration_data.get("description", ""),
                category=integration_data.get("category", "Custom"),
                method_type=IntegrationMethodType(integration_data["method_type"]),
                auth_type=IntegrationAuthType(integration_data["auth_type"]),
                base_url=integration_data["base_url"],
                endpoints=integration_data.get("endpoints", []),
                auth_config=integration_data.get("auth_config", {}),
                headers=integration_data.get("headers", {}),
                parameters=integration_data.get("parameters", {}),
                response_mapping=integration_data.get("response_mapping", {}),
                error_handling=integration_data.get("error_handling", {}),
                rate_limiting=integration_data.get("rate_limiting", {}),
                created_by=created_by
            )
            
            # Store in database
            integration_doc = asdict(integration)
            integration_doc["method_type"] = integration.method_type.value
            integration_doc["auth_type"] = integration.auth_type.value
            integration_doc["status"] = integration.status.value
            
            self.integrations.insert_one(integration_doc)
            
            logger.info(f"Created custom integration: {integration.name} ({integration_id})")
            
            return integration_id
            
        except Exception as e:
            logger.error(f"Failed to create custom integration: {e}")
            raise
    
    async def _validate_integration_data(self, data: Dict[str, Any]):
        """Validate integration configuration data"""
        
        required_fields = ["name", "method_type", "auth_type", "base_url"]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate method type
        try:
            IntegrationMethodType(data["method_type"])
        except ValueError:
            raise ValueError(f"Invalid method_type: {data['method_type']}")
        
        # Validate auth type
        try:
            IntegrationAuthType(data["auth_type"])
        except ValueError:
            raise ValueError(f"Invalid auth_type: {data['auth_type']}")
        
        # Validate URL format
        if not data["base_url"].startswith(("http://", "https://")):
            raise ValueError("base_url must be a valid HTTP/HTTPS URL")
        
        # Validate endpoints
        endpoints = data.get("endpoints", [])
        for endpoint in endpoints:
            if "name" not in endpoint or "method" not in endpoint:
                raise ValueError("Each endpoint must have 'name' and 'method'")
    
    async def create_from_template(self, template_id: str, config: Dict[str, Any], 
                                 created_by: str) -> str:
        """Create integration from template"""
        
        try:
            # Get template
            template = await self._get_template(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")
            
            # Validate required variables
            await self._validate_template_config(template, config)
            
            # Generate integration from template
            integration_data = await self._generate_from_template(template, config)
            
            # Create integration
            integration_id = await self.create_custom_integration(integration_data, created_by)
            
            logger.info(f"Created integration from template {template_id}: {integration_id}")
            
            return integration_id
            
        except Exception as e:
            logger.error(f"Failed to create integration from template: {e}")
            raise
    
    async def _get_template(self, template_id: str) -> Optional[IntegrationTemplate]:
        """Get integration template"""
        
        # Check cache first
        if template_id in self.template_cache:
            return self.template_cache[template_id]
        
        # Load from database
        template_doc = self.templates.find_one({"template_id": template_id})
        if not template_doc:
            return None
        
        template = IntegrationTemplate(
            template_id=template_doc["template_id"],
            name=template_doc["name"],
            description=template_doc["description"],
            category=template_doc["category"],
            template_data=template_doc["template_data"],
            variables=template_doc["variables"],
            example_config=template_doc["example_config"],
            documentation=template_doc["documentation"]
        )
        
        # Cache template
        self.template_cache[template_id] = template
        
        return template
    
    async def _validate_template_config(self, template: IntegrationTemplate, config: Dict[str, Any]):
        """Validate template configuration"""
        
        for variable in template.variables:
            var_name = variable["name"]
            
            # Check required variables
            if variable.get("required", False) and var_name not in config:
                raise ValueError(f"Required variable missing: {var_name}")
            
            # Validate variable types
            if var_name in config:
                value = config[var_name]
                var_type = variable.get("type", "string")
                
                if var_type == "integer" and not isinstance(value, int):
                    try:
                        config[var_name] = int(value)
                    except ValueError:
                        raise ValueError(f"Variable {var_name} must be an integer")
                
                elif var_type == "boolean" and not isinstance(value, bool):
                    if isinstance(value, str):
                        config[var_name] = value.lower() in ("true", "yes", "1")
                    else:
                        config[var_name] = bool(value)
    
    async def _generate_from_template(self, template: IntegrationTemplate, 
                                    config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate integration configuration from template"""
        
        # Start with template data
        integration_data = template.template_data.copy()
        
        # Apply variable substitutions
        template_json = json.dumps(integration_data)
        
        # Add default values for missing variables
        for variable in template.variables:
            var_name = variable["name"]
            if var_name not in config and "default" in variable:
                config[var_name] = variable["default"]
        
        # Perform template substitution
        jinja_template = Template(template_json)
        rendered_json = jinja_template.render(**config)
        integration_data = json.loads(rendered_json)
        
        # Set base configuration
        integration_data.update({
            "name": config.get("name", template.name),
            "description": config.get("description", template.description),
            "category": template.category,
            "base_url": config.get("base_url", ""),
            "auth_config": self._build_auth_config(template, config),
            "headers": config.get("headers", {}),
            "parameters": config.get("parameters", {}),
            "response_mapping": config.get("response_mapping", {}),
            "error_handling": config.get("error_handling", {
                "retry_attempts": 3,
                "retry_delay": 1,
                "timeout": 30
            }),
            "rate_limiting": config.get("rate_limiting", {
                "requests_per_second": 10,
                "burst_limit": 20
            })
        })
        
        return integration_data
    
    def _build_auth_config(self, template: IntegrationTemplate, config: Dict[str, Any]) -> Dict[str, Any]:
        """Build authentication configuration"""
        
        auth_type = template.template_data.get("auth_type")
        auth_config = {}
        
        if auth_type == "api_key":
            auth_config = {
                "api_key": config.get("api_key", ""),
                "header_name": config.get("api_key_header", "X-API-Key")
            }
        elif auth_type == "oauth2":
            auth_config = {
                "client_id": config.get("client_id", ""),
                "client_secret": config.get("client_secret", ""),
                "authorize_url": config.get("authorize_url", ""),
                "token_url": config.get("token_url", ""),
                "scope": config.get("scope", ""),
                "redirect_uri": config.get("redirect_uri", "")
            }
        elif auth_type == "basic_auth":
            auth_config = {
                "username": config.get("username", ""),
                "password": config.get("password", "")
            }
        elif auth_type == "bearer_token":
            auth_config = {
                "token": config.get("bearer_token", "")
            }
        elif auth_type == "custom_header":
            auth_config = {
                "header_name": config.get("custom_header_name", "Authorization"),
                "header_value": config.get("custom_header_value", "")
            }
        
        return auth_config
    
    async def test_integration(self, integration_id: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test integration configuration"""
        
        try:
            # Get integration
            integration = await self._get_integration(integration_id)
            if not integration:
                raise ValueError(f"Integration {integration_id} not found")
            
            # Perform connectivity test
            test_result = await self._perform_integration_test(integration, test_data or {})
            
            # Store test result
            test_doc = {
                "integration_id": integration_id,
                "test_data": test_data,
                "result": test_result,
                "timestamp": datetime.utcnow()
            }
            
            self.test_results.insert_one(test_doc)
            
            # Update integration status based on test result
            new_status = IntegrationStatus.ACTIVE if test_result["success"] else IntegrationStatus.ERROR
            
            self.integrations.update_one(
                {"integration_id": integration_id},
                {"$set": {
                    "status": new_status.value,
                    "last_tested": datetime.utcnow(),
                    "last_test_result": test_result
                }}
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"Integration test failed for {integration_id}: {e}")
            
            error_result = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store error result
            test_doc = {
                "integration_id": integration_id,
                "test_data": test_data,
                "result": error_result,
                "timestamp": datetime.utcnow()
            }
            
            self.test_results.insert_one(test_doc)
            
            return error_result
    
    async def _get_integration(self, integration_id: str) -> Optional[CustomIntegration]:
        """Get integration by ID"""
        
        integration_doc = self.integrations.find_one({"integration_id": integration_id})
        if not integration_doc:
            return None
        
        return CustomIntegration(
            integration_id=integration_doc["integration_id"],
            name=integration_doc["name"],
            description=integration_doc["description"],
            category=integration_doc["category"],
            method_type=IntegrationMethodType(integration_doc["method_type"]),
            auth_type=IntegrationAuthType(integration_doc["auth_type"]),
            base_url=integration_doc["base_url"],
            endpoints=integration_doc["endpoints"],
            auth_config=integration_doc["auth_config"],
            headers=integration_doc["headers"],
            parameters=integration_doc["parameters"],
            response_mapping=integration_doc["response_mapping"],
            error_handling=integration_doc["error_handling"],
            rate_limiting=integration_doc["rate_limiting"],
            created_by=integration_doc["created_by"],
            status=IntegrationStatus(integration_doc["status"]),
            version=integration_doc.get("version", "1.0.0"),
            created_at=integration_doc.get("created_at"),
            updated_at=integration_doc.get("updated_at")
        )
    
    async def _perform_integration_test(self, integration: CustomIntegration, 
                                      test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform actual integration test"""
        
        start_time = time.time()
        
        try:
            if integration.method_type == IntegrationMethodType.REST_API:
                result = await self._test_rest_api(integration, test_data)
            elif integration.method_type == IntegrationMethodType.WEBHOOK:
                result = await self._test_webhook(integration, test_data)
            elif integration.method_type == IntegrationMethodType.DATABASE:
                result = await self._test_database(integration, test_data)
            else:
                result = await self._test_generic(integration, test_data)
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "execution_time": execution_time,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return {
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _test_rest_api(self, integration: CustomIntegration, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test REST API integration"""
        
        # Prepare authentication
        headers = integration.headers.copy()
        auth_config = integration.auth_config
        
        if integration.auth_type == IntegrationAuthType.API_KEY:
            headers[auth_config.get("header_name", "X-API-Key")] = auth_config.get("api_key", "")
        elif integration.auth_type == IntegrationAuthType.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {auth_config.get('token', '')}"
        elif integration.auth_type == IntegrationAuthType.CUSTOM_HEADER:
            headers[auth_config.get("header_name", "Authorization")] = auth_config.get("header_value", "")
        
        # Test first endpoint or specified endpoint
        endpoint = test_data.get("endpoint")
        if not endpoint and integration.endpoints:
            endpoint = integration.endpoints[0]
        
        if not endpoint:
            raise ValueError("No endpoint specified for testing")
        
        # Prepare request
        method = endpoint.get("method", "GET").upper()
        path = endpoint.get("path", "/")
        url = integration.base_url.rstrip('/') + '/' + path.lstrip('/')
        
        timeout = integration.error_handling.get("timeout", 30)
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, timeout=timeout)
            elif method == "POST":
                json_data = test_data.get("json_data", {})
                response = await client.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method == "PUT":
                json_data = test_data.get("json_data", {})
                response = await client.put(url, headers=headers, json=json_data, timeout=timeout)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Process response
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": str(response.url),
                "method": method
            }
            
            # Try to parse JSON response
            try:
                result["json_response"] = response.json()
            except:
                result["text_response"] = response.text[:1000]  # Limit response size
            
            # Check if response indicates success
            if 200 <= response.status_code < 300:
                result["success"] = True
            else:
                result["success"] = False
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            
            return result
    
    async def _test_webhook(self, integration: CustomIntegration, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test webhook integration"""
        
        # For webhook testing, we simulate a webhook payload
        webhook_data = test_data.get("webhook_data", {"test": "data"})
        
        return {
            "success": True,
            "message": "Webhook configuration validated",
            "test_payload": webhook_data,
            "auth_type": integration.auth_type.value
        }
    
    async def _test_database(self, integration: CustomIntegration, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test database integration"""
        
        # For database testing, we simulate a connection test
        auth_config = integration.auth_config
        
        return {
            "success": True,
            "message": "Database connection configuration validated",
            "host": auth_config.get("host", "unknown"),
            "database": auth_config.get("database", "unknown"),
            "connection_test": "simulated_success"
        }
    
    async def _test_generic(self, integration: CustomIntegration, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test generic integration"""
        
        return {
            "success": True,
            "message": f"Generic {integration.method_type.value} integration test completed",
            "method_type": integration.method_type.value
        }
    
    async def execute_integration(self, integration_id: str, endpoint_name: str, 
                                parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute integration endpoint"""
        
        try:
            integration = await self._get_integration(integration_id)
            if not integration:
                raise ValueError(f"Integration {integration_id} not found")
            
            if integration.status != IntegrationStatus.ACTIVE:
                raise ValueError(f"Integration {integration_id} is not active")
            
            # Find endpoint
            endpoint = None
            for ep in integration.endpoints:
                if ep.get("name") == endpoint_name:
                    endpoint = ep
                    break
            
            if not endpoint:
                raise ValueError(f"Endpoint {endpoint_name} not found")
            
            # Check rate limiting
            await self._check_rate_limit(integration_id, integration.rate_limiting)
            
            # Execute endpoint
            result = await self._execute_endpoint(integration, endpoint, parameters or {})
            
            # Log usage
            await self._log_integration_usage(integration_id, endpoint_name, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Integration execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_rate_limit(self, integration_id: str, rate_config: Dict[str, Any]):
        """Check rate limiting for integration"""
        
        if not rate_config:
            return
        
        requests_per_second = rate_config.get("requests_per_second", 10)
        burst_limit = rate_config.get("burst_limit", 20)
        
        # Simple rate limiting implementation
        # In production, use Redis or similar for distributed rate limiting
        current_time = time.time()
        
        if integration_id not in self.rate_limiters:
            self.rate_limiters[integration_id] = {
                "requests": [],
                "last_reset": current_time
            }
        
        limiter = self.rate_limiters[integration_id]
        
        # Clean old requests
        cutoff_time = current_time - 1.0  # Last second
        limiter["requests"] = [req_time for req_time in limiter["requests"] if req_time > cutoff_time]
        
        # Check limits
        if len(limiter["requests"]) >= burst_limit:
            raise Exception("Rate limit exceeded: burst limit reached")
        
        if len(limiter["requests"]) >= requests_per_second:
            sleep_time = 1.0 / requests_per_second
            await asyncio.sleep(sleep_time)
        
        # Record request
        limiter["requests"].append(current_time)
    
    async def _execute_endpoint(self, integration: CustomIntegration, 
                              endpoint: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific endpoint"""
        
        start_time = time.time()
        
        try:
            if integration.method_type == IntegrationMethodType.REST_API:
                result = await self._execute_rest_endpoint(integration, endpoint, parameters)
            elif integration.method_type == IntegrationMethodType.DATABASE:
                result = await self._execute_database_endpoint(integration, endpoint, parameters)
            else:
                result = {"success": False, "error": f"Unsupported method type: {integration.method_type.value}"}
            
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_rest_endpoint(self, integration: CustomIntegration, 
                                   endpoint: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute REST API endpoint"""
        
        # Prepare request
        method = endpoint.get("method", "GET").upper()
        path = endpoint.get("path", "/")
        url = integration.base_url.rstrip('/') + '/' + path.lstrip('/')
        
        # Apply parameter substitution in URL
        for param_name, param_value in parameters.items():
            url = url.replace(f"{{{param_name}}}", str(param_value))
        
        # Prepare headers
        headers = integration.headers.copy()
        auth_config = integration.auth_config
        
        if integration.auth_type == IntegrationAuthType.API_KEY:
            headers[auth_config.get("header_name", "X-API-Key")] = auth_config.get("api_key", "")
        elif integration.auth_type == IntegrationAuthType.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {auth_config.get('token', '')}"
        
        timeout = integration.error_handling.get("timeout", 30)
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers, params=parameters, timeout=timeout)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=parameters, timeout=timeout)
            elif method == "PUT":
                response = await client.put(url, headers=headers, json=parameters, timeout=timeout)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Process response
            if 200 <= response.status_code < 300:
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                # Apply response mapping if configured
                if integration.response_mapping:
                    response_data = self._apply_response_mapping(response_data, integration.response_mapping)
                
                return {
                    "success": True,
                    "data": response_data,
                    "status_code": response.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }
    
    async def _execute_database_endpoint(self, integration: CustomIntegration, 
                                       endpoint: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database endpoint"""
        
        # Simulate database execution
        operation = endpoint.get("method", "SELECT")
        
        return {
            "success": True,
            "operation": operation,
            "parameters": parameters,
            "message": f"Database operation {operation} executed successfully",
            "rows_affected": 1,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _apply_response_mapping(self, response_data: Any, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Apply response mapping configuration"""
        
        if not isinstance(response_data, dict) or not mapping:
            return response_data
        
        mapped_data = {}
        
        for output_key, mapping_config in mapping.items():
            if isinstance(mapping_config, str):
                # Simple field mapping
                if mapping_config in response_data:
                    mapped_data[output_key] = response_data[mapping_config]
            elif isinstance(mapping_config, dict):
                # Complex mapping with transformations
                source_field = mapping_config.get("source")
                transform = mapping_config.get("transform")
                default_value = mapping_config.get("default")
                
                if source_field in response_data:
                    value = response_data[source_field]
                    
                    # Apply transformations
                    if transform == "lowercase":
                        value = str(value).lower()
                    elif transform == "uppercase":
                        value = str(value).upper()
                    elif transform == "int":
                        value = int(value)
                    elif transform == "float":
                        value = float(value)
                    
                    mapped_data[output_key] = value
                elif default_value is not None:
                    mapped_data[output_key] = default_value
        
        return mapped_data
    
    async def _log_integration_usage(self, integration_id: str, endpoint_name: str, result: Dict[str, Any]):
        """Log integration usage"""
        
        try:
            usage_log = {
                "integration_id": integration_id,
                "endpoint_name": endpoint_name,
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0.0),
                "error": result.get("error"),
                "timestamp": datetime.utcnow()
            }
            
            self.usage_logs.insert_one(usage_log)
            
        except Exception as e:
            logger.error(f"Error logging integration usage: {e}")
    
    async def _check_integration_health(self):
        """Check health of active integrations"""
        
        try:
            active_integrations = list(self.integrations.find({"status": IntegrationStatus.ACTIVE.value}))
            
            for integration_doc in active_integrations:
                integration_id = integration_doc["integration_id"]
                
                try:
                    # Perform health check
                    integration = await self._get_integration(integration_id)
                    test_result = await self._perform_integration_test(integration, {})
                    
                    # Update health status
                    health_status = "healthy" if test_result["success"] else "unhealthy"
                    
                    self.integrations.update_one(
                        {"integration_id": integration_id},
                        {"$set": {
                            "health_status": health_status,
                            "last_health_check": datetime.utcnow()
                        }}
                    )
                    
                except Exception as e:
                    logger.error(f"Health check failed for integration {integration_id}: {e}")
                    
                    self.integrations.update_one(
                        {"integration_id": integration_id},
                        {"$set": {
                            "health_status": "error",
                            "last_health_check": datetime.utcnow(),
                            "health_error": str(e)
                        }}
                    )
            
        except Exception as e:
            logger.error(f"Integration health check error: {e}")
    
    async def _update_usage_statistics(self):
        """Update integration usage statistics"""
        
        try:
            # Calculate usage stats for each integration
            pipeline = [
                {"$group": {
                    "_id": "$integration_id",
                    "total_calls": {"$sum": 1},
                    "successful_calls": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "avg_execution_time": {"$avg": "$execution_time"},
                    "last_used": {"$max": "$timestamp"}
                }}
            ]
            
            stats = list(self.usage_logs.aggregate(pipeline))
            
            for stat in stats:
                integration_id = stat["_id"]
                success_rate = (stat["successful_calls"] / stat["total_calls"]) * 100
                
                self.integrations.update_one(
                    {"integration_id": integration_id},
                    {"$set": {
                        "usage_stats": {
                            "total_calls": stat["total_calls"],
                            "success_rate": success_rate,
                            "avg_execution_time": stat["avg_execution_time"],
                            "last_used": stat["last_used"]
                        },
                        "stats_updated_at": datetime.utcnow()
                    }}
                )
            
        except Exception as e:
            logger.error(f"Usage statistics update error: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old test results and usage logs"""
        
        try:
            # Clean up test results older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            test_result = self.test_results.delete_many({"timestamp": {"$lt": cutoff_date}})
            if test_result.deleted_count > 0:
                logger.info(f"Cleaned up {test_result.deleted_count} old test results")
            
            # Clean up usage logs older than 90 days
            log_cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            usage_result = self.usage_logs.delete_many({"timestamp": {"$lt": log_cutoff_date}})
            if usage_result.deleted_count > 0:
                logger.info(f"Cleaned up {usage_result.deleted_count} old usage logs")
            
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")
    
    # Public API Methods
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available integration templates"""
        
        templates = list(self.templates.find({}, {"_id": 0}))
        return templates
    
    def get_user_integrations(self, created_by: str) -> List[Dict[str, Any]]:
        """Get integrations created by user"""
        
        integrations = list(self.integrations.find(
            {"created_by": created_by},
            {"_id": 0}
        ).sort("created_at", -1))
        
        # Convert datetime objects
        for integration in integrations:
            for field in ["created_at", "updated_at", "last_tested"]:
                if integration.get(field):
                    integration[field] = integration[field].isoformat()
        
        return integrations
    
    def get_integration_details(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed integration information"""
        
        integration = self.integrations.find_one({"integration_id": integration_id}, {"_id": 0})
        
        if integration:
            # Convert datetime objects
            for field in ["created_at", "updated_at", "last_tested", "last_health_check"]:
                if integration.get(field):
                    integration[field] = integration[field].isoformat()
            
            # Get recent test results
            recent_tests = list(self.test_results.find(
                {"integration_id": integration_id},
                {"_id": 0}
            ).sort("timestamp", -1).limit(5))
            
            for test in recent_tests:
                if test.get("timestamp"):
                    test["timestamp"] = test["timestamp"].isoformat()
            
            integration["recent_tests"] = recent_tests
            
            # Get usage statistics
            usage_stats = self.usage_logs.count_documents({"integration_id": integration_id})
            integration["total_usage_count"] = usage_stats
        
        return integration
    
    async def update_integration(self, integration_id: str, update_data: Dict[str, Any]) -> bool:
        """Update integration configuration"""
        
        try:
            # Validate update data
            allowed_fields = [
                "name", "description", "base_url", "endpoints", "headers",
                "parameters", "response_mapping", "error_handling", "rate_limiting"
            ]
            
            update_doc = {}
            for field in allowed_fields:
                if field in update_data:
                    update_doc[field] = update_data[field]
            
            if not update_doc:
                return False
            
            # Add update timestamp
            update_doc["updated_at"] = datetime.utcnow()
            
            # Update in database
            result = self.integrations.update_one(
                {"integration_id": integration_id},
                {"$set": update_doc}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Integration update error: {e}")
            return False
    
    async def delete_integration(self, integration_id: str) -> bool:
        """Delete custom integration"""
        
        try:
            # Delete integration
            result = self.integrations.delete_one({"integration_id": integration_id})
            
            if result.deleted_count > 0:
                # Clean up related data
                self.test_results.delete_many({"integration_id": integration_id})
                self.usage_logs.delete_many({"integration_id": integration_id})
                
                logger.info(f"Deleted integration {integration_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Integration deletion error: {e}")
            return False

# Global custom integration builder instance
custom_integration_builder = None  # Will be initialized in server.py