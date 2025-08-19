"""
OpenAI Platform Integration for AETHER
AI model access and automation capabilities
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..base_connector import BasePlatformConnector, AuthType, PlatformCapability

class OpenAIConnector(BasePlatformConnector):
    def __init__(self, credentials: Dict[str, str], config: Optional[Dict[str, Any]] = None):
        super().__init__(credentials, config)
        self.api_key = credentials.get('api_key')
        self.organization_id = credentials.get('organization_id')
        
    @property
    def platform_name(self) -> str:
        return "openai"
    
    @property
    def auth_type(self) -> AuthType:
        return AuthType.BEARER_TOKEN
    
    @property
    def base_url(self) -> str:
        return "https://api.openai.com/v1"
    
    async def authenticate(self) -> bool:
        """Authenticate with OpenAI API"""
        if not self.api_key:
            return False
        self.auth_token = self.api_key
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI API connection"""
        try:
            response = await self.make_request("GET", "/models")
            return {
                "success": response.success,
                "platform": "openai",
                "available_models": len(response.data.get("data", [])) if response.success else 0
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_capabilities(self) -> List[PlatformCapability]:
        """Get OpenAI platform capabilities"""
        return [
            PlatformCapability(
                name="text_generation",
                description="Generate text using GPT models",
                methods=["chat_completion", "text_completion"]
            ),
            PlatformCapability(
                name="image_generation",
                description="Generate images using DALL-E",
                methods=["create_image", "edit_image", "create_variation"]
            ),
            PlatformCapability(
                name="embeddings",
                description="Create text embeddings for similarity search",
                methods=["create_embedding", "similarity_search"]
            ),
            PlatformCapability(
                name="moderation",
                description="Content moderation using OpenAI models",
                methods=["moderate_content", "classify_content"]
            ),
            PlatformCapability(
                name="fine_tuning",
                description="Fine-tune models on custom data",
                methods=["create_fine_tune", "list_fine_tunes", "get_fine_tune"]
            )
        ]
    
    # Text Generation
    async def chat_completion(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo", 
                             temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """Generate chat completion"""
        try:
            request_data = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.make_request("POST", "/chat/completions", data=request_data)
            
            if response.success:
                choice = response.data["choices"][0]
                return {
                    "success": True,
                    "content": choice["message"]["content"],
                    "model": response.data["model"],
                    "usage": response.data["usage"],
                    "finish_reason": choice["finish_reason"]
                }
            else:
                return {"success": False, "error": response.error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def text_completion(self, prompt: str, model: str = "text-davinci-003",
                             temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """Generate text completion"""
        try:
            request_data = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.make_request("POST", "/completions", data=request_data)
            
            if response.success:
                choice = response.data["choices"][0]
                return {
                    "success": True,
                    "text": choice["text"],
                    "model": response.data["model"],
                    "usage": response.data["usage"],
                    "finish_reason": choice["finish_reason"]
                }
            else:
                return {"success": False, "error": response.error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Image Generation
    async def create_image(self, prompt: str, n: int = 1, size: str = "1024x1024") -> Dict[str, Any]:
        """Generate images using DALL-E"""
        try:
            request_data = {
                "prompt": prompt,
                "n": n,
                "size": size
            }
            
            response = await self.make_request("POST", "/images/generations", data=request_data)
            
            if response.success:
                return {
                    "success": True,
                    "images": response.data["data"],
                    "created": response.data["created"]
                }
            else:
                return {"success": False, "error": response.error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Embeddings
    async def create_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        """Create text embedding"""
        try:
            request_data = {
                "model": model,
                "input": text
            }
            
            response = await self.make_request("POST", "/embeddings", data=request_data)
            
            if response.success:
                return {
                    "success": True,
                    "embedding": response.data["data"][0]["embedding"],
                    "model": response.data["model"],
                    "usage": response.data["usage"]
                }
            else:
                return {"success": False, "error": response.error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Moderation
    async def moderate_content(self, text: str) -> Dict[str, Any]:
        """Moderate content using OpenAI"""
        try:
            request_data = {"input": text}
            
            response = await self.make_request("POST", "/moderations", data=request_data)
            
            if response.success:
                result = response.data["results"][0]
                return {
                    "success": True,
                    "flagged": result["flagged"],
                    "categories": result["categories"],
                    "category_scores": result["category_scores"]
                }
            else:
                return {"success": False, "error": response.error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Advanced Features
    async def bulk_process_texts(self, texts: List[str], operation: str = "summarize") -> Dict[str, Any]:
        """Process multiple texts in bulk"""
        try:
            results = []
            
            for text in texts:
                if operation == "summarize":
                    prompt = f"Summarize the following text in 2-3 sentences:\n\n{text}"
                    result = await self.text_completion(prompt, max_tokens=150)
                elif operation == "analyze_sentiment":
                    prompt = f"Analyze the sentiment of this text (positive/negative/neutral):\n\n{text}"
                    result = await self.text_completion(prompt, max_tokens=10)
                elif operation == "extract_keywords":
                    prompt = f"Extract the main keywords from this text:\n\n{text}"
                    result = await self.text_completion(prompt, max_tokens=100)
                else:
                    result = {"success": False, "error": f"Unknown operation: {operation}"}
                
                results.append({
                    "original_text": text[:100] + "..." if len(text) > 100 else text,
                    "result": result
                })
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            successful_results = [r for r in results if r["result"].get("success")]
            
            return {
                "success": True,
                "operation": operation,
                "total_texts": len(texts),
                "successful_processing": len(successful_results),
                "results": results
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_conversation_agent(self, system_prompt: str, personality: str = "helpful") -> Dict[str, Any]:
        """Create a conversational AI agent"""
        try:
            agent_config = {
                "id": f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "system_prompt": system_prompt,
                "personality": personality,
                "model": "gpt-3.5-turbo",
                "conversation_history": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Test agent with initial message
            test_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hello, introduce yourself."}
            ]
            
            test_response = await self.chat_completion(test_messages)
            
            if test_response["success"]:
                agent_config["status"] = "active"
                agent_config["test_response"] = test_response["content"]
            else:
                agent_config["status"] = "error"
                agent_config["error"] = test_response["error"]
            
            return {
                "success": True,
                "agent": agent_config
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def continue_conversation(self, agent_config: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        """Continue conversation with an AI agent"""
        try:
            # Build conversation history
            messages = [{"role": "system", "content": agent_config["system_prompt"]}]
            messages.extend(agent_config.get("conversation_history", []))
            messages.append({"role": "user", "content": user_message})
            
            response = await self.chat_completion(messages, model=agent_config.get("model", "gpt-3.5-turbo"))
            
            if response["success"]:
                # Update conversation history
                agent_config["conversation_history"].append({"role": "user", "content": user_message})
                agent_config["conversation_history"].append({"role": "assistant", "content": response["content"]})
                
                # Keep conversation history manageable (last 20 messages)
                if len(agent_config["conversation_history"]) > 20:
                    agent_config["conversation_history"] = agent_config["conversation_history"][-20:]
                
                return {
                    "success": True,
                    "response": response["content"],
                    "usage": response["usage"],
                    "conversation_length": len(agent_config["conversation_history"])
                }
            else:
                return {"success": False, "error": response["error"]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Model Management
    async def list_models(self) -> Dict[str, Any]:
        """List available OpenAI models"""
        try:
            response = await self.make_request("GET", "/models")
            
            if response.success:
                models = response.data["data"]
                
                # Categorize models
                text_models = [m for m in models if "text" in m["id"] or "gpt" in m["id"]]
                image_models = [m for m in models if "dall-e" in m["id"]]
                embedding_models = [m for m in models if "embedding" in m["id"]]
                
                return {
                    "success": True,
                    "total_models": len(models),
                    "categories": {
                        "text_generation": len(text_models),
                        "image_generation": len(image_models),
                        "embeddings": len(embedding_models)
                    },
                    "models": {
                        "text": [{"id": m["id"], "created": m["created"]} for m in text_models],
                        "image": [{"id": m["id"], "created": m["created"]} for m in image_models],
                        "embedding": [{"id": m["id"], "created": m["created"]} for m in embedding_models]
                    }
                }
            else:
                return {"success": False, "error": response.error}
        except Exception as e:
            return {"success": False, "error": str(e)}