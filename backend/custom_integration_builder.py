# Phase 4: Custom Integration Builder
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pymongo import MongoClient
import uuid
import httpx
import yaml
from enum import Enum

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    WEBHOOK = "webhook"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"

class FieldType(Enum):
    TEXT = "text"
    PASSWORD = "password"
    URL = "url"
    EMAIL = "email"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    TEXTAREA = "textarea"

class CustomIntegrationBuilder:
    """
    Phase 4: Advanced Custom Integration Builder
    Allows users to create custom integrations with third-party services
    """
    
    def __init__(self, mongo_client: MongoClient):
        self.client = mongo_client
        self.db = mongo_client.aether_browser
        self.integration_templates = self._load_integration_templates()
        self.validation_rules = self._initialize_validation_rules()
        
    async def create_custom_integration(self, integration_config: Dict[str, Any], user_session: str) -> Dict[str, Any]:
        """Create a new custom integration"""
        try:
            integration_id = str(uuid.uuid4())
            
            # Validate configuration
            validation_result = await self._validate_integration_config(integration_config)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "Configuration validation failed",
                    "validation_errors": validation_result["errors"]
                }
            
            # Generate integration code
            integration_code = await self._generate_integration_code(integration_config)
            
            # Create integration record
            integration_record = {
                "integration_id": integration_id,
                "name": integration_config["name"],
                "description": integration_config.get("description", ""),
                "type": integration_config["type"],
                "creator_session": user_session,
                "status": "draft",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "config": integration_config,
                "generated_code": integration_code,
                "test_results": [],
                "deployment_status": "not_deployed",
                "usage_count": 0,
                "last_tested": None,
                "version": "1.0.0"
            }
            
            self.db.custom_integrations.insert_one(integration_record)
            
            return {
                "success": True,
                "integration_id": integration_id,
                "message": "Custom integration created successfully",
                "generated_code": integration_code,
                "test_endpoint": f"/api/test-custom-integration/{integration_id}"
            }
            
        except Exception as e:
            logger.error(f"Custom integration creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_integration_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate integration configuration"""
        errors = []
        
        # Required fields
        required_fields = ["name", "type", "endpoints", "authentication"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate integration type
        if "type" in config:
            try:
                IntegrationType(config["type"])
            except ValueError:
                errors.append(f"Invalid integration type: {config['type']}")
        
        # Validate endpoints
        if "endpoints" in config:
            endpoint_errors = self._validate_endpoints(config["endpoints"])
            errors.extend(endpoint_errors)
        
        # Validate authentication
        if "authentication" in config:
            auth_errors = self._validate_authentication(config["authentication"])
            errors.extend(auth_errors)
        
        # Validate custom fields
        if "custom_fields" in config:
            field_errors = self._validate_custom_fields(config["custom_fields"])
            errors.extend(field_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[str]:
        """Validate endpoint configurations"""
        errors = []
        
        for i, endpoint in enumerate(endpoints):
            # Required endpoint fields
            required = ["name", "method", "url", "description"]
            for field in required:
                if field not in endpoint:
                    errors.append(f"Endpoint {i}: Missing required field '{field}'")
            
            # Validate HTTP method
            if "method" in endpoint:
                valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
                if endpoint["method"].upper() not in valid_methods:
                    errors.append(f"Endpoint {i}: Invalid HTTP method '{endpoint['method']}'")
            
            # Validate URL format
            if "url" in endpoint:
                if not endpoint["url"].startswith(("http://", "https://", "{{", "/")):
                    errors.append(f"Endpoint {i}: Invalid URL format")
        
        return errors
    
    def _validate_authentication(self, auth: Dict[str, Any]) -> List[str]:
        """Validate authentication configuration"""
        errors = []
        
        if "type" not in auth:
            errors.append("Authentication: Missing type")
            return errors
        
        auth_type = auth["type"]
        
        if auth_type == "api_key":
            if "key_location" not in auth:
                errors.append("API Key auth: Missing key_location")
            if "key_name" not in auth:
                errors.append("API Key auth: Missing key_name")
        
        elif auth_type == "oauth2":
            required_oauth = ["client_id_field", "client_secret_field", "auth_url", "token_url"]
            for field in required_oauth:
                if field not in auth:
                    errors.append(f"OAuth2 auth: Missing {field}")
        
        elif auth_type == "bearer":
            if "token_field" not in auth:
                errors.append("Bearer auth: Missing token_field")
        
        return errors
    
    def _validate_custom_fields(self, fields: List[Dict[str, Any]]) -> List[str]:
        """Validate custom field configurations"""
        errors = []
        
        for i, field in enumerate(fields):
            # Required field properties
            required = ["name", "type", "label"]
            for prop in required:
                if prop not in field:
                    errors.append(f"Field {i}: Missing required property '{prop}'")
            
            # Validate field type
            if "type" in field:
                try:
                    FieldType(field["type"])
                except ValueError:
                    errors.append(f"Field {i}: Invalid field type '{field['type']}'")
            
            # Validate select options
            if field.get("type") == "select" and "options" not in field:
                errors.append(f"Field {i}: Select field missing options")
        
        return errors
    
    async def _generate_integration_code(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate integration code from configuration"""
        
        integration_type = config["type"]
        name = config["name"]
        endpoints = config["endpoints"]
        auth_config = config["authentication"]
        
        # Generate Python class code
        python_code = self._generate_python_integration_class(config)
        
        # Generate JavaScript SDK code
        js_code = self._generate_javascript_sdk(config)
        
        # Generate OpenAPI specification
        openapi_spec = self._generate_openapi_spec(config)
        
        # Generate usage examples
        usage_examples = self._generate_usage_examples(config)
        
        # Generate test cases
        test_cases = self._generate_test_cases(config)
        
        return {
            "python_class": python_code,
            "javascript_sdk": js_code,
            "openapi_spec": openapi_spec,
            "usage_examples": usage_examples,
            "test_cases": test_cases,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_python_integration_class(self, config: Dict[str, Any]) -> str:
        """Generate Python integration class"""
        
        name = config["name"]
        class_name = f"{name.replace(' ', '').replace('-', '')}Integration"
        endpoints = config["endpoints"]
        auth_config = config["authentication"]
        
        code_parts = []
        
        # Class header
        code_parts.append(f'''import asyncio
import httpx
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class {class_name}:
    """
    Custom integration for {name}
    Generated by AETHER Custom Integration Builder
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.base_url = "{config.get('base_url', '')}"
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()''')
        
        # Authentication method
        auth_method = self._generate_auth_method(auth_config)
        code_parts.append(auth_method)
        
        # Generate endpoint methods
        for endpoint in endpoints:
            method_code = self._generate_endpoint_method(endpoint, auth_config)
            code_parts.append(method_code)
        
        # Utility methods
        code_parts.append('''
    async def _make_request(self, method: str, url: str, headers: Dict[str, str] = None, 
                           data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated HTTP request"""
        try:
            # Prepare headers
            request_headers = await self._get_auth_headers()
            if headers:
                request_headers.update(headers)
            
            # Make request
            response = await self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                json=data,
                params=params
            )
            
            response.raise_for_status()
            return {
                "success": True,
                "data": response.json() if response.content else {},
                "status_code": response.status_code
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint"""
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"''')
        
        return '\n'.join(code_parts)
    
    def _generate_auth_method(self, auth_config: Dict[str, Any]) -> str:
        """Generate authentication method"""
        
        auth_type = auth_config["type"]
        
        if auth_type == "api_key":
            key_location = auth_config.get("key_location", "header")
            key_name = auth_config.get("key_name", "X-API-Key")
            
            if key_location == "header":
                return f'''
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {{
            "{key_name}": self.credentials.get("api_key", ""),
            "Content-Type": "application/json"
        }}'''
            
        elif auth_type == "bearer":
            return '''
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.credentials.get('token', '')}",
            "Content-Type": "application/json"
        }'''
        
        elif auth_type == "oauth2":
            return '''
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        # OAuth2 token should be refreshed as needed
        access_token = await self._get_oauth_token()
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _get_oauth_token(self) -> str:
        """Get or refresh OAuth2 token"""
        # Implementation depends on OAuth2 flow
        return self.credentials.get("access_token", "")'''
        
        return '''
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {"Content-Type": "application/json"}'''
    
    def _generate_endpoint_method(self, endpoint: Dict[str, Any], auth_config: Dict[str, Any]) -> str:
        """Generate method for endpoint"""
        
        method_name = endpoint["name"].lower().replace(" ", "_").replace("-", "_")
        http_method = endpoint["method"].upper()
        url = endpoint["url"]
        description = endpoint.get("description", "")
        
        # Generate parameters
        params = endpoint.get("parameters", [])
        param_list = []
        param_docs = []
        
        for param in params:
            param_name = param["name"]
            param_type = param.get("type", "str")
            is_required = param.get("required", False)
            
            if is_required:
                param_list.append(f"{param_name}: {param_type}")
            else:
                param_list.append(f"{param_name}: Optional[{param_type}] = None")
            
            param_docs.append(f"        {param_name}: {param.get('description', '')}")
        
        param_str = ", ".join(param_list)
        if param_str:
            param_str = ", " + param_str
        
        doc_params = "\n".join(param_docs) if param_docs else "        No parameters"
        
        method_code = f'''
    async def {method_name}(self{param_str}) -> Dict[str, Any]:
        """
        {description}
        
        Parameters:
{doc_params}
        
        Returns:
            Dict containing the API response
        """
        url = self._build_url("{url}")
        
        # Prepare request data
        data = {{}}
        params = {{}}'''
        
        # Add parameter handling
        for param in params:
            param_name = param["name"]
            location = param.get("location", "body")
            
            if location == "body":
                method_code += f'''
        if {param_name} is not None:
            data["{param_name}"] = {param_name}'''
            elif location == "query":
                method_code += f'''
        if {param_name} is not None:
            params["{param_name}"] = {param_name}'''
        
        method_code += f'''
        
        return await self._make_request("{http_method}", url, data=data, params=params)'''
        
        return method_code
    
    def _generate_javascript_sdk(self, config: Dict[str, Any]) -> str:
        """Generate JavaScript SDK"""
        
        name = config["name"]
        class_name = f"{name.replace(' ', '').replace('-', '')}SDK"
        
        js_code = f'''/**
 * {name} JavaScript SDK
 * Generated by AETHER Custom Integration Builder
 */

class {class_name} {{
    constructor(credentials) {{
        this.credentials = credentials;
        this.baseUrl = "{config.get('base_url', '')}";
    }}
    
    async makeRequest(method, endpoint, data = null, params = null) {{
        const url = this.buildUrl(endpoint);
        const headers = await this.getAuthHeaders();
        
        const config = {{
            method: method,
            headers: headers
        }};
        
        if (data) {{
            config.body = JSON.stringify(data);
        }}
        
        if (params) {{
            const urlParams = new URLSearchParams(params);
            url += '?' + urlParams.toString();
        }}
        
        try {{
            const response = await fetch(url, config);
            const result = await response.json();
            
            return {{
                success: response.ok,
                data: result,
                status: response.status
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message
            }};
        }}
    }}
    
    buildUrl(endpoint) {{
        if (endpoint.startsWith('http')) {{
            return endpoint;
        }}
        return `${{this.baseUrl.replace(/\/$/, '')}}/${{endpoint.replace(/^\//, '')}}`;
    }}
    
    async getAuthHeaders() {{
        const headers = {{
            'Content-Type': 'application/json'
        }};
        
        // Add authentication based on type
        {self._generate_js_auth_logic(config["authentication"])}
        
        return headers;
    }}'''
        
        # Add endpoint methods
        for endpoint in config["endpoints"]:
            method_name = endpoint["name"].replace(" ", "").replace("-", "")
            method_name = method_name[0].lower() + method_name[1:]
            
            js_code += f'''
    
    async {method_name}(params = {{}}) {{
        return await this.makeRequest('{endpoint["method"]}', '{endpoint["url"]}', params);
    }}'''
        
        js_code += '\n}\n\n'
        js_code += f'// Export for use\nif (typeof module !== "undefined") {{ module.exports = {class_name}; }}'
        
        return js_code
    
    def _generate_js_auth_logic(self, auth_config: Dict[str, Any]) -> str:
        """Generate JavaScript authentication logic"""
        
        auth_type = auth_config["type"]
        
        if auth_type == "api_key":
            key_name = auth_config.get("key_name", "X-API-Key")
            return f'''headers['{key_name}'] = this.credentials.apiKey;'''
        
        elif auth_type == "bearer":
            return '''headers['Authorization'] = `Bearer ${this.credentials.token}`;'''
        
        elif auth_type == "oauth2":
            return '''headers['Authorization'] = `Bearer ${this.credentials.accessToken}`;'''
        
        return '// No additional authentication headers'
    
    def _generate_openapi_spec(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI specification"""
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{config['name']} API",
                "description": config.get("description", ""),
                "version": "1.0.0",
                "contact": {
                    "name": "AETHER Custom Integration",
                    "url": "https://aether.ai"
                }
            },
            "servers": [
                {
                    "url": config.get("base_url", ""),
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": self._generate_security_schemes(config["authentication"])
            }
        }
        
        # Add paths from endpoints
        for endpoint in config["endpoints"]:
            path = endpoint["url"]
            method = endpoint["method"].lower()
            
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            
            spec["paths"][path][method] = {
                "summary": endpoint["name"],
                "description": endpoint.get("description", ""),
                "parameters": self._generate_openapi_parameters(endpoint.get("parameters", [])),
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
        
        return spec
    
    def _generate_security_schemes(self, auth_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate OpenAPI security schemes"""
        
        auth_type = auth_config["type"]
        
        if auth_type == "api_key":
            key_location = auth_config.get("key_location", "header")
            key_name = auth_config.get("key_name", "X-API-Key")
            
            return {
                "apiKey": {
                    "type": "apiKey",
                    "in": key_location,
                    "name": key_name
                }
            }
        
        elif auth_type == "bearer":
            return {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer"
                }
            }
        
        elif auth_type == "oauth2":
            return {
                "oauth2": {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": auth_config.get("auth_url", ""),
                            "tokenUrl": auth_config.get("token_url", ""),
                            "scopes": auth_config.get("scopes", {})
                        }
                    }
                }
            }
        
        return {}
    
    def _generate_openapi_parameters(self, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate OpenAPI parameters"""
        
        openapi_params = []
        
        for param in params:
            location = param.get("location", "query")
            if location == "body":
                continue  # Body parameters handled separately
            
            openapi_param = {
                "name": param["name"],
                "in": location,
                "description": param.get("description", ""),
                "required": param.get("required", False),
                "schema": {
                    "type": param.get("type", "string")
                }
            }
            
            openapi_params.append(openapi_param)
        
        return openapi_params
    
    def _generate_usage_examples(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Generate usage examples"""
        
        name = config["name"]
        class_name = f"{name.replace(' ', '').replace('-', '')}Integration"
        
        python_example = f'''# Python Usage Example
import asyncio
from {class_name.lower()} import {class_name}

async def main():
    credentials = {{
        "api_key": "your_api_key_here"  # Replace with actual credentials
    }}
    
    async with {class_name}(credentials) as integration:
        # Example API call
        result = await integration.{config["endpoints"][0]["name"].lower().replace(" ", "_")}()
        
        if result["success"]:
            print("Success:", result["data"])
        else:
            print("Error:", result["error"])

if __name__ == "__main__":
    asyncio.run(main())'''
        
        js_example = f'''// JavaScript Usage Example
const {class_name.replace("Integration", "SDK")} = require('./{class_name.lower()}_sdk');

const credentials = {{
    apiKey: "your_api_key_here"  // Replace with actual credentials
}};

const sdk = new {class_name.replace("Integration", "SDK")}(credentials);

// Example API call
sdk.{config["endpoints"][0]["name"].replace(" ", "").replace("-", "")[0].lower() + config["endpoints"][0]["name"].replace(" ", "").replace("-", "")[1:]}()
    .then(result => {{
        if (result.success) {{
            console.log("Success:", result.data);
        }} else {{
            console.log("Error:", result.error);
        }}
    }})
    .catch(error => {{
        console.error("Request failed:", error);
    }});'''
        
        curl_example = f'''# cURL Example
curl -X {config["endpoints"][0]["method"]} \\
  "{config.get("base_url", "")}{config["endpoints"][0]["url"]}" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your_api_key_here" \\
  -d '{{}}'
'''
        
        return {
            "python": python_example,
            "javascript": js_example,
            "curl": curl_example
        }
    
    def _generate_test_cases(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate test cases for the integration"""
        
        test_cases = []
        
        for endpoint in config["endpoints"]:
            test_case = {
                "name": f"Test {endpoint['name']}",
                "endpoint": endpoint["name"],
                "method": endpoint["method"],
                "url": endpoint["url"],
                "description": f"Test the {endpoint['name']} endpoint",
                "test_data": self._generate_test_data(endpoint),
                "expected_response": {
                    "status_code": 200,
                    "success": True
                },
                "validation_rules": [
                    "Response should have success field",
                    "Status code should be 200 for successful requests",
                    "Response should be valid JSON"
                ]
            }
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_test_data(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test data for endpoint"""
        
        test_data = {}
        params = endpoint.get("parameters", [])
        
        for param in params:
            param_name = param["name"]
            param_type = param.get("type", "string")
            
            # Generate sample data based on type
            if param_type == "string":
                test_data[param_name] = f"test_{param_name}"
            elif param_type == "number" or param_type == "integer":
                test_data[param_name] = 123
            elif param_type == "boolean":
                test_data[param_name] = True
            elif param_type == "array":
                test_data[param_name] = ["item1", "item2"]
            else:
                test_data[param_name] = f"sample_{param_name}"
        
        return test_data
    
    async def test_custom_integration(self, integration_id: str, test_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test a custom integration"""
        try:
            # Get integration record
            integration = self.db.custom_integrations.find_one({"integration_id": integration_id})
            if not integration:
                return {
                    "success": False,
                    "error": "Integration not found"
                }
            
            # Get test cases
            test_cases = integration["generated_code"]["test_cases"]
            test_results = []
            
            # Run tests
            for test_case in test_cases:
                result = await self._run_integration_test(integration, test_case, test_config)
                test_results.append(result)
            
            # Calculate overall success rate
            successful_tests = len([r for r in test_results if r["success"]])
            success_rate = successful_tests / len(test_results) if test_results else 0
            
            # Update integration record
            self.db.custom_integrations.update_one(
                {"integration_id": integration_id},
                {
                    "$set": {
                        "last_tested": datetime.utcnow(),
                        "test_results": test_results
                    }
                }
            )
            
            return {
                "success": True,
                "integration_id": integration_id,
                "test_results": test_results,
                "success_rate": success_rate,
                "total_tests": len(test_results),
                "successful_tests": successful_tests
            }
            
        except Exception as e:
            logger.error(f"Integration testing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_integration_test(self, integration: Dict[str, Any], test_case: Dict[str, Any], test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run individual integration test"""
        
        try:
            # Prepare test request
            method = test_case["method"]
            url = test_case["url"]
            test_data = test_case.get("test_data", {})
            
            # Build full URL
            base_url = integration["config"].get("base_url", "")
            if not url.startswith("http"):
                url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            
            # Prepare headers (use test credentials if provided)
            headers = {"Content-Type": "application/json"}
            
            # Add authentication
            auth_config = integration["config"]["authentication"]
            if test_config and "credentials" in test_config:
                auth_headers = self._get_test_auth_headers(auth_config, test_config["credentials"])
                headers.update(auth_headers)
            
            # Make test request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=test_data if method.upper() in ["POST", "PUT", "PATCH"] else None,
                    params=test_data if method.upper() == "GET" else None
                )
                
                # Validate response
                validation_results = self._validate_test_response(response, test_case)
                
                return {
                    "test_name": test_case["name"],
                    "success": validation_results["valid"],
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "validation_results": validation_results,
                    "tested_at": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            return {
                "test_name": test_case["name"],
                "success": False,
                "error": str(e),
                "tested_at": datetime.utcnow().isoformat()
            }
    
    def _get_test_auth_headers(self, auth_config: Dict[str, Any], credentials: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers for testing"""
        
        headers = {}
        auth_type = auth_config["type"]
        
        if auth_type == "api_key":
            key_name = auth_config.get("key_name", "X-API-Key")
            headers[key_name] = credentials.get("api_key", "")
        
        elif auth_type == "bearer":
            headers["Authorization"] = f"Bearer {credentials.get('token', '')}"
        
        elif auth_type == "oauth2":
            headers["Authorization"] = f"Bearer {credentials.get('access_token', '')}"
        
        return headers
    
    def _validate_test_response(self, response: httpx.Response, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Validate test response"""
        
        validation_results = {
            "valid": True,
            "checks": [],
            "errors": []
        }
        
        expected = test_case.get("expected_response", {})
        
        # Check status code
        expected_status = expected.get("status_code", 200)
        if response.status_code == expected_status:
            validation_results["checks"].append(f"Status code: {response.status_code} ✓")
        else:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Expected status {expected_status}, got {response.status_code}")
        
        # Check response content type
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            validation_results["checks"].append("Content-Type: application/json ✓")
        else:
            validation_results["errors"].append(f"Unexpected content-type: {content_type}")
        
        # Try to parse JSON
        try:
            response_data = response.json()
            validation_results["checks"].append("Valid JSON response ✓")
            
            # Check for success field if expected
            if expected.get("success") is not None:
                if response_data.get("success") == expected["success"]:
                    validation_results["checks"].append(f"Success field: {response_data.get('success')} ✓")
                else:
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"Expected success: {expected['success']}, got: {response_data.get('success')}")
        
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Invalid JSON response: {str(e)}")
        
        return validation_results
    
    async def deploy_custom_integration(self, integration_id: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy custom integration to production"""
        try:
            integration = self.db.custom_integrations.find_one({"integration_id": integration_id})
            if not integration:
                return {
                    "success": False,
                    "error": "Integration not found"
                }
            
            # Validate deployment readiness
            if not integration.get("test_results"):
                return {
                    "success": False,
                    "error": "Integration must be tested before deployment"
                }
            
            # Create deployment record
            deployment_id = str(uuid.uuid4())
            deployment_record = {
                "deployment_id": deployment_id,
                "integration_id": integration_id,
                "deployed_at": datetime.utcnow(),
                "deployment_config": deployment_config,
                "status": "active",
                "version": integration.get("version", "1.0.0"),
                "endpoints": self._create_deployment_endpoints(integration)
            }
            
            self.db.integration_deployments.insert_one(deployment_record)
            
            # Update integration status
            self.db.custom_integrations.update_one(
                {"integration_id": integration_id},
                {
                    "$set": {
                        "deployment_status": "deployed",
                        "deployed_at": datetime.utcnow(),
                        "deployment_id": deployment_id
                    }
                }
            )
            
            return {
                "success": True,
                "deployment_id": deployment_id,
                "integration_id": integration_id,
                "endpoints": deployment_record["endpoints"],
                "message": "Integration deployed successfully"
            }
            
        except Exception as e:
            logger.error(f"Integration deployment failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_deployment_endpoints(self, integration: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create deployment endpoints"""
        
        endpoints = []
        integration_id = integration["integration_id"]
        
        for endpoint_config in integration["config"]["endpoints"]:
            endpoint = {
                "name": endpoint_config["name"],
                "method": endpoint_config["method"],
                "path": f"/api/custom-integrations/{integration_id}/{endpoint_config['name'].lower().replace(' ', '-')}",
                "description": endpoint_config.get("description", ""),
                "parameters": endpoint_config.get("parameters", [])
            }
            endpoints.append(endpoint)
        
        return endpoints
    
    async def get_custom_integration(self, integration_id: str) -> Dict[str, Any]:
        """Get custom integration details"""
        
        integration = self.db.custom_integrations.find_one(
            {"integration_id": integration_id},
            {"_id": 0}
        )
        
        if not integration:
            return {
                "success": False,
                "error": "Integration not found"
            }
        
        return {
            "success": True,
            "integration": integration
        }
    
    async def list_custom_integrations(self, user_session: str = None, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """List custom integrations"""
        
        query = {}
        if user_session:
            query["creator_session"] = user_session
        
        if filters:
            if "status" in filters:
                query["status"] = filters["status"]
            if "type" in filters:
                query["type"] = filters["type"]
        
        integrations = list(self.db.custom_integrations.find(
            query,
            {"_id": 0, "generated_code": 0}  # Exclude large generated code
        ).sort("created_at", -1))
        
        return {
            "success": True,
            "integrations": integrations,
            "total": len(integrations)
        }
    
    def _load_integration_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined integration templates"""
        
        return {
            "rest_api": {
                "name": "REST API Integration",
                "description": "Generic REST API integration template",
                "type": "api_key",
                "authentication": {
                    "type": "api_key",
                    "key_location": "header",
                    "key_name": "X-API-Key"
                },
                "endpoints": [
                    {
                        "name": "Get Data",
                        "method": "GET",
                        "url": "/api/data",
                        "description": "Retrieve data from API"
                    },
                    {
                        "name": "Create Record",
                        "method": "POST", 
                        "url": "/api/records",
                        "description": "Create a new record"
                    }
                ]
            },
            "oauth_api": {
                "name": "OAuth API Integration",
                "description": "OAuth-based API integration template",
                "type": "oauth2",
                "authentication": {
                    "type": "oauth2",
                    "auth_url": "https://api.example.com/oauth/authorize",
                    "token_url": "https://api.example.com/oauth/token"
                },
                "endpoints": [
                    {
                        "name": "Get User Profile",
                        "method": "GET",
                        "url": "/api/user/profile",
                        "description": "Get authenticated user profile"
                    }
                ]
            }
        }
    
    def _initialize_validation_rules(self) -> Dict[str, List[str]]:
        """Initialize validation rules"""
        
        return {
            "required_fields": ["name", "type", "endpoints", "authentication"],
            "valid_auth_types": ["api_key", "oauth2", "bearer", "basic"],
            "valid_http_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "valid_field_types": ["text", "password", "url", "email", "number", "boolean", "select", "textarea"]
        }

# Global instance
custom_integration_builder = None

def initialize_custom_integration_builder(mongo_client: MongoClient):
    global custom_integration_builder
    custom_integration_builder = CustomIntegrationBuilder(mongo_client)
    return custom_integration_builder