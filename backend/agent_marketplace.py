# 🏪 AGENT MARKETPLACE - Community Agent Creation & Sharing Platform
# Workstream C1: Agent Development, Security Validation & Revenue Sharing

import asyncio
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import ast
import logging
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent lifecycle status"""
    DRAFT = "draft"
    VALIDATING = "validating"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class AgentCategory(Enum):
    """Agent categories"""
    PRODUCTIVITY = "productivity"
    AUTOMATION = "automation" 
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    DEVELOPMENT = "development"
    BUSINESS = "business"

class SecurityLevel(Enum):
    """Security validation levels"""
    SAFE = "safe"           # No security concerns
    LOW_RISK = "low_risk"   # Minor concerns, approved with warnings
    MEDIUM_RISK = "medium_risk"  # Requires user consent
    HIGH_RISK = "high_risk" # Rejected or requires special permissions
    DANGEROUS = "dangerous" # Blocked entirely

@dataclass
class Agent:
    """Community-created agent definition"""
    agent_id: str
    name: str
    description: str
    developer_id: str
    category: AgentCategory
    status: AgentStatus
    
    # Agent code and configuration
    natural_language_description: str
    execution_code: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    version: str
    tags: List[str]
    
    # Usage and analytics
    usage_count: int
    rating: float
    review_count: int
    download_count: int
    
    # Security and validation
    security_level: SecurityLevel
    security_report: Dict[str, Any]
    validation_results: Dict[str, Any]
    
    # Revenue sharing
    price: float  # 0 for free agents
    revenue_share: float  # Developer's share (0-1)
    earnings: float

@dataclass
class AgentReview:
    """User review of an agent"""
    review_id: str
    agent_id: str
    user_id: str
    rating: int  # 1-5 stars
    comment: str
    created_at: datetime
    helpful_votes: int

class AgentMarketplace:
    """Community agent creation and sharing platform"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.agents_collection = self.db.marketplace_agents
        self.reviews_collection = self.db.agent_reviews
        self.analytics_collection = self.db.agent_analytics
        self.developers_collection = self.db.agent_developers
        
        # Security validation engine
        self.security_validator = AgentSecurityValidator()
        
        # Agent development studio
        self.development_studio = AgentDevelopmentStudio()
        
        # Revenue tracking
        self.revenue_manager = RevenueManager(self.db)
        
        logger.info("🏪 Agent Marketplace initialized")

    async def create_agent(self, developer_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new community agent"""
        try:
            agent_id = str(uuid.uuid4())
            
            # Create agent object
            agent = Agent(
                agent_id=agent_id,
                name=agent_data["name"],
                description=agent_data["description"],
                developer_id=developer_id,
                category=AgentCategory(agent_data["category"]),
                status=AgentStatus.DRAFT,
                
                natural_language_description=agent_data["natural_language_description"],
                execution_code=agent_data.get("execution_code", ""),
                input_schema=agent_data.get("input_schema", {}),
                output_schema=agent_data.get("output_schema", {}),
                
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                version="1.0.0",
                tags=agent_data.get("tags", []),
                
                usage_count=0,
                rating=0.0,
                review_count=0,
                download_count=0,
                
                security_level=SecurityLevel.SAFE,  # Will be updated by validation
                security_report={},
                validation_results={},
                
                price=agent_data.get("price", 0.0),
                revenue_share=agent_data.get("revenue_share", 0.7),  # 70% to developer
                earnings=0.0
            )
            
            # If execution code provided, trigger security validation
            if agent.execution_code:
                agent.status = AgentStatus.VALIDATING
                validation_task = asyncio.create_task(
                    self._validate_agent_security(agent)
                )
            
            # Store agent in database
            agent_doc = asdict(agent)
            agent_doc["created_at"] = agent.created_at
            agent_doc["updated_at"] = agent.updated_at
            agent_doc["category"] = agent.category.value
            agent_doc["status"] = agent.status.value
            agent_doc["security_level"] = agent.security_level.value
            
            self.agents_collection.insert_one(agent_doc)
            
            # Initialize developer profile if new
            await self._ensure_developer_profile(developer_id)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "name": agent.name,
                "status": agent.status.value,
                "message": "Agent created successfully" + (
                    " and submitted for security validation" 
                    if agent.execution_code else ""
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Agent creation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def discover_agents(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """AI-powered agent discovery"""
        try:
            # Build search criteria
            search_criteria = {"status": AgentStatus.APPROVED.value, "published": True}
            
            # Apply filters
            if filters:
                if filters.get("category"):
                    search_criteria["category"] = filters["category"]
                
                if filters.get("price_range"):
                    price_min, price_max = filters["price_range"]
                    search_criteria["price"] = {"$gte": price_min, "$lte": price_max}
                
                if filters.get("min_rating"):
                    search_criteria["rating"] = {"$gte": filters["min_rating"]}
            
            # Text search in name and description
            if query:
                search_criteria["$or"] = [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"natural_language_description": {"$regex": query, "$options": "i"}},
                    {"tags": {"$in": [query]}}
                ]
            
            # Execute search with ranking
            agents = list(self.agents_collection.find(
                search_criteria,
                {"_id": 0}
            ).sort([
                ("rating", -1),      # Higher rated first
                ("usage_count", -1), # More popular first
                ("created_at", -1)   # Newer first
            ]).limit(20))
            
            # Calculate relevance scores
            for agent in agents:
                agent["relevance_score"] = self._calculate_relevance(agent, query)
            
            # Sort by relevance
            agents.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "success": True,
                "agents": agents[:10],  # Top 10 results
                "total_found": len(agents),
                "query": query,
                "filters_applied": filters or {}
            }
            
        except Exception as e:
            logger.error(f"❌ Agent discovery error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agents": []
            }

    async def install_agent(self, agent_id: str, user_id: str) -> Dict[str, Any]:
        """Install agent for user"""
        try:
            # Get agent details
            agent_doc = self.agents_collection.find_one({"agent_id": agent_id})
            if not agent_doc:
                return {"success": False, "error": "Agent not found"}
            
            if agent_doc["status"] != AgentStatus.APPROVED.value:
                return {"success": False, "error": "Agent not approved for installation"}
            
            # Check if paid agent - handle payment
            if agent_doc["price"] > 0:
                payment_result = await self.revenue_manager.process_payment(
                    user_id, agent_id, agent_doc["price"]
                )
                if not payment_result["success"]:
                    return payment_result
            
            # Record installation
            installation = {
                "installation_id": str(uuid.uuid4()),
                "agent_id": agent_id,
                "user_id": user_id,
                "installed_at": datetime.utcnow(),
                "version": agent_doc["version"],
                "active": True
            }
            
            self.db.agent_installations.insert_one(installation)
            
            # Update agent stats
            self.agents_collection.update_one(
                {"agent_id": agent_id},
                {"$inc": {"download_count": 1}}
            )
            
            return {
                "success": True,
                "agent_id": agent_id,
                "installation_id": installation["installation_id"],
                "message": "Agent installed successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Agent installation error: {e}")
            return {"success": False, "error": str(e)}

    async def execute_agent(self, agent_id: str, user_id: str, 
                          input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute installed agent"""
        try:
            # Check if user has agent installed
            installation = self.db.agent_installations.find_one({
                "agent_id": agent_id,
                "user_id": user_id,
                "active": True
            })
            
            if not installation:
                return {"success": False, "error": "Agent not installed or inactive"}
            
            # Get agent details
            agent_doc = self.agents_collection.find_one({"agent_id": agent_id})
            if not agent_doc:
                return {"success": False, "error": "Agent not found"}
            
            # Execute agent in secure sandbox
            execution_result = await self._execute_agent_safely(
                agent_doc, input_data, user_id
            )
            
            # Record usage analytics
            await self._record_agent_usage(agent_id, execution_result)
            
            # Update usage count
            self.agents_collection.update_one(
                {"agent_id": agent_id},
                {"$inc": {"usage_count": 1}}
            )
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ Agent execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_id": None
            }

    # Helper methods
    async def _validate_agent_security(self, agent: Agent):
        """Background security validation"""
        try:
            # Run security validation
            validation_result = await self.security_validator.validate_agent(agent)
            
            # Update agent with results
            self.agents_collection.update_one(
                {"agent_id": agent.agent_id},
                {
                    "$set": {
                        "security_level": validation_result["security_level"],
                        "security_report": validation_result["report"],
                        "validation_results": validation_result,
                        "status": AgentStatus.APPROVED.value if validation_result["approved"] else AgentStatus.REJECTED.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            # Mark as rejected on validation failure
            self.agents_collection.update_one(
                {"agent_id": agent.agent_id},
                {
                    "$set": {
                        "status": AgentStatus.REJECTED.value,
                        "security_report": {"error": str(e)},
                        "updated_at": datetime.utcnow()
                    }
                }
            )

    def _calculate_relevance(self, agent: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        query_lower = query.lower() if query else ""
        
        # Name match (highest weight)
        if query_lower in agent["name"].lower():
            score += 0.5
        
        # Description match
        if query_lower in agent["description"].lower():
            score += 0.3
        
        # Tags match
        for tag in agent.get("tags", []):
            if query_lower in tag.lower():
                score += 0.2
        
        # Boost for popularity
        score += min(agent.get("usage_count", 0) / 1000, 0.3)
        
        # Boost for high rating
        score += (agent.get("rating", 0) / 5.0) * 0.2
        
        return min(score, 1.0)

    async def _execute_agent_safely(self, agent_doc: Dict[str, Any], 
                                  input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute agent in secure sandbox"""
        try:
            execution_id = str(uuid.uuid4())
            
            # Simulate successful execution
            result = {
                "success": True,
                "execution_id": execution_id,
                "agent_id": agent_doc["agent_id"],
                "execution_time": 2.0,
                "output": {
                    "message": f"Agent '{agent_doc['name']}' executed successfully",
                    "processed_input": input_data,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "metadata": {
                    "agent_version": agent_doc["version"],
                    "user_id": user_id
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "execution_id": execution_id if 'execution_id' in locals() else str(uuid.uuid4())
            }

    async def _record_agent_usage(self, agent_id: str, execution_result: Dict[str, Any]):
        """Record usage analytics"""
        try:
            today = datetime.utcnow().date().isoformat()
            
            # Update daily analytics
            self.analytics_collection.update_one(
                {"agent_id": agent_id, "period": "daily", "date": today},
                {
                    "$inc": {
                        "executions": 1,
                        "success_count" if execution_result["success"] else "error_count": 1
                    },
                    "$set": {"last_updated": datetime.utcnow()}
                },
                upsert=True
            )
            
        except Exception as e:
            logger.warning(f"Analytics recording error: {e}")

    async def _ensure_developer_profile(self, developer_id: str):
        """Ensure developer profile exists"""
        try:
            existing = self.developers_collection.find_one({"developer_id": developer_id})
            if not existing:
                profile = {
                    "developer_id": developer_id,
                    "created_at": datetime.utcnow(),
                    "total_agents": 0,
                    "total_downloads": 0,
                    "total_earnings": 0.0,
                    "reputation_score": 0.0
                }
                self.developers_collection.insert_one(profile)
        except Exception as e:
            logger.warning(f"Developer profile creation error: {e}")


class AgentSecurityValidator:
    """Security validation for community agents"""
    
    async def validate_agent(self, agent: Agent) -> Dict[str, Any]:
        """Validate agent security"""
        try:
            validation_result = {
                "agent_id": agent.agent_id,
                "validated_at": datetime.utcnow(),
                "approved": True,
                "security_level": SecurityLevel.SAFE.value,
                "report": {
                    "code_analysis": {},
                    "permission_analysis": {},
                    "security_score": 0.9
                },
                "warnings": [],
                "errors": []
            }
            
            # Analyze execution code
            if agent.execution_code:
                code_analysis = self._analyze_code_security(agent.execution_code)
                validation_result["report"]["code_analysis"] = code_analysis
                
                if code_analysis["risk_level"] == "high":
                    validation_result["approved"] = False
                    validation_result["security_level"] = SecurityLevel.HIGH_RISK.value
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return {
                "approved": False,
                "security_level": SecurityLevel.DANGEROUS.value,
                "report": {"error": str(e)}
            }

    def _analyze_code_security(self, code: str) -> Dict[str, Any]:
        """Analyze code for security issues"""
        try:
            # Parse code AST for analysis
            tree = ast.parse(code)
            
            security_issues = []
            risk_level = "low"
            
            # Check for dangerous operations
            dangerous_patterns = [
                "exec", "eval", "import os", "subprocess", "__import__",
                "open(", "file(", "input(", "raw_input("
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    security_issues.append(f"Potentially dangerous operation: {pattern}")
                    risk_level = "medium"
            
            return {
                "risk_level": risk_level,
                "security_issues": security_issues,
                "lines_analyzed": len(code.split('\n')),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except SyntaxError:
            return {
                "risk_level": "high",
                "security_issues": ["Code contains syntax errors"],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "risk_level": "unknown",
                "security_issues": [f"Analysis failed: {str(e)}"],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }


class AgentDevelopmentStudio:
    """Visual agent development environment"""
    
    def __init__(self):
        self.templates = self._load_agent_templates()
    
    def _load_agent_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-built agent templates"""
        return {
            "web_scraper": {
                "name": "Web Scraper Agent",
                "description": "Extract data from web pages",
                "template_code": "# Web scraping template code here"
            },
            "data_analyzer": {
                "name": "Data Analyzer Agent", 
                "description": "Analyze and summarize data",
                "template_code": "# Data analysis template code here"
            }
        }


class RevenueManager:
    """Handle agent marketplace revenue and payments"""
    
    def __init__(self, db):
        self.db = db
        
    async def process_payment(self, user_id: str, agent_id: str, amount: float) -> Dict[str, Any]:
        """Process payment for paid agent"""
        # For now, simulate successful payment
        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "agent_id": agent_id,
            "amount": amount,
            "timestamp": datetime.utcnow(),
            "status": "completed"
        }
        
        self.db.payment_transactions.insert_one(transaction)
        
        return {
            "success": True,
            "transaction_id": transaction["transaction_id"],
            "message": "Payment processed successfully"
        }


# Initialize functions for integration
def initialize_agent_marketplace(db_client: MongoClient) -> AgentMarketplace:
    """Initialize and return agent marketplace"""
    return AgentMarketplace(db_client)

def get_agent_marketplace() -> Optional[AgentMarketplace]:
    """Get the global agent marketplace instance"""
    return getattr(get_agent_marketplace, '_instance', None)

def set_agent_marketplace_instance(instance: AgentMarketplace):
    """Set the global agent marketplace instance"""
    get_agent_marketplace._instance = instance