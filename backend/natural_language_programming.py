# 🗣️ NATURAL LANGUAGE PROGRAMMING FRAMEWORK - Eko-Equivalent System
# Workstream A3: Convert Natural Language to Executable Workflows

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import json
import re
import logging
from enum import Enum
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of workflow actions"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    WAIT = "wait"
    CONDITION = "condition"
    LOOP = "loop"
    API_CALL = "api_call"
    TRANSFORM = "transform"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    DRAFT = "draft"
    GENERATED = "generated"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    step_number: int
    action_type: ActionType
    description: str
    parameters: Dict[str, Any]
    expected_result: str
    timeout: int
    retry_count: int
    conditions: List[str]

@dataclass
class GeneratedWorkflow:
    """Generated workflow from natural language"""
    workflow_id: str
    name: str
    description: str
    original_prompt: str
    steps: List[WorkflowStep]
    estimated_duration: int
    complexity_score: float
    confidence: float
    status: WorkflowStatus
    generated_at: datetime

@dataclass
class ExecutionResult:
    """Workflow execution result"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: Optional[datetime]
    steps_completed: int
    total_steps: int
    results: Dict[str, Any]
    error_message: Optional[str]

class NaturalLanguageProgramming:
    """Convert natural language descriptions to executable workflows"""
    
    def __init__(self, db_client: MongoClient):
        self.db = db_client.aether_browser
        self.workflows_collection = self.db.nl_workflows
        self.executions_collection = self.db.workflow_executions
        self.patterns_collection = self.db.nl_patterns
        
        # Language parsing components
        self.intent_parser = IntentParser()
        self.workflow_generator = WorkflowGenerator()
        self.code_generator = CodeGenerator()
        self.execution_engine = ExecutionEngine()
        
        # Initialize language patterns
        self.language_patterns = self._initialize_language_patterns()
        
        logger.info("🗣️ Natural Language Programming Framework initialized")

    def _initialize_language_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize natural language patterns for workflow generation"""
        return {
            "navigation_patterns": {
                "patterns": [
                    "go to {url}",
                    "visit {website}",
                    "open {page}",
                    "navigate to {destination}",
                    "browse to {site}"
                ],
                "action_type": ActionType.NAVIGATE,
                "parameters": ["url", "website", "page", "destination", "site"]
            },
            "interaction_patterns": {
                "patterns": [
                    "click on {element}",
                    "press {button}",
                    "select {option}",
                    "choose {item}",
                    "tap {control}"
                ],
                "action_type": ActionType.CLICK,
                "parameters": ["element", "button", "option", "item", "control"]
            },
            "input_patterns": {
                "patterns": [
                    "type {text}",
                    "enter {input}",
                    "fill in {field} with {value}",
                    "input {data}",
                    "write {content}"
                ],
                "action_type": ActionType.TYPE,
                "parameters": ["text", "input", "field", "value", "data", "content"]
            },
            "extraction_patterns": {
                "patterns": [
                    "extract {data} from {source}",
                    "get {information} from {page}",
                    "scrape {content}",
                    "collect {items}",
                    "gather {details}"
                ],
                "action_type": ActionType.EXTRACT,
                "parameters": ["data", "source", "information", "page", "content", "items", "details"]
            },
            "analysis_patterns": {
                "patterns": [
                    "analyze {data}",
                    "summarize {content}",
                    "review {information}",
                    "examine {details}",
                    "process {input}"
                ],
                "action_type": ActionType.ANALYZE,
                "parameters": ["data", "content", "information", "details", "input"]
            },
            "conditional_patterns": {
                "patterns": [
                    "if {condition} then {action}",
                    "when {event} occurs do {task}",
                    "check if {condition}",
                    "verify that {requirement}",
                    "ensure {state}"
                ],
                "action_type": ActionType.CONDITION,
                "parameters": ["condition", "action", "event", "task", "requirement", "state"]
            },
            "loop_patterns": {
                "patterns": [
                    "repeat {action} {count} times",
                    "for each {item} do {task}",
                    "loop through {collection}",
                    "iterate over {data}",
                    "continue until {condition}"
                ],
                "action_type": ActionType.LOOP,
                "parameters": ["action", "count", "item", "task", "collection", "data", "condition"]
            }
        }

    async def generate_workflow(self, natural_language_prompt: str, 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate executable workflow from natural language description"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # Parse the natural language prompt
            parsed_intent = await self.intent_parser.parse_intent(
                natural_language_prompt, context or {}
            )
            
            if not parsed_intent["success"]:
                return {
                    "success": False,
                    "error": "Failed to parse natural language intent",
                    "details": parsed_intent.get("error", "Unknown parsing error")
                }
            
            # Generate workflow steps
            workflow_generation = await self.workflow_generator.generate_steps(
                parsed_intent["intents"], natural_language_prompt
            )
            
            if not workflow_generation["success"]:
                return {
                    "success": False,
                    "error": "Failed to generate workflow steps",
                    "details": workflow_generation.get("error", "Unknown generation error")
                }
            
            # Create workflow object
            workflow = GeneratedWorkflow(
                workflow_id=workflow_id,
                name=workflow_generation["workflow_name"],
                description=workflow_generation["description"],
                original_prompt=natural_language_prompt,
                steps=workflow_generation["steps"],
                estimated_duration=workflow_generation["estimated_duration"],
                complexity_score=workflow_generation["complexity_score"],
                confidence=workflow_generation["confidence"],
                status=WorkflowStatus.GENERATED,
                generated_at=datetime.utcnow()
            )
            
            # Store workflow
            workflow_doc = asdict(workflow)
            workflow_doc["status"] = workflow.status.value
            workflow_doc["generated_at"] = workflow.generated_at
            
            # Convert steps to storable format
            workflow_doc["steps"] = [
                {
                    "step_id": step.step_id,
                    "step_number": step.step_number,
                    "action_type": step.action_type.value,
                    "description": step.description,
                    "parameters": step.parameters,
                    "expected_result": step.expected_result,
                    "timeout": step.timeout,
                    "retry_count": step.retry_count,
                    "conditions": step.conditions
                }
                for step in workflow.steps
            ]
            
            self.workflows_collection.insert_one(workflow_doc)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "steps_generated": len(workflow.steps),
                "estimated_duration": workflow.estimated_duration,
                "confidence": workflow.confidence,
                "complexity_score": workflow.complexity_score,
                "steps": [
                    {
                        "step_number": step.step_number,
                        "action_type": step.action_type.value,
                        "description": step.description,
                        "expected_result": step.expected_result
                    }
                    for step in workflow.steps
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_workflow(self, workflow_id: str, execution_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute generated workflow"""
        try:
            # Get workflow
            workflow_doc = self.workflows_collection.find_one({"workflow_id": workflow_id})
            if not workflow_doc:
                return {"success": False, "error": "Workflow not found"}
            
            if workflow_doc["status"] not in [WorkflowStatus.GENERATED.value, WorkflowStatus.VALIDATED.value]:
                return {"success": False, "error": f"Workflow status is {workflow_doc['status']}, cannot execute"}
            
            # Create execution record
            execution_id = str(uuid.uuid4())
            execution_result = ExecutionResult(
                execution_id=execution_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING,
                started_at=datetime.utcnow(),
                completed_at=None,
                steps_completed=0,
                total_steps=len(workflow_doc["steps"]),
                results={},
                error_message=None
            )
            
            # Store execution record
            execution_doc = asdict(execution_result)
            execution_doc["status"] = execution_result.status.value
            execution_doc["started_at"] = execution_result.started_at
            
            self.executions_collection.insert_one(execution_doc)
            
            # Execute workflow steps
            step_results = []
            for step_data in workflow_doc["steps"]:
                step = WorkflowStep(
                    step_id=step_data["step_id"],
                    step_number=step_data["step_number"],
                    action_type=ActionType(step_data["action_type"]),
                    description=step_data["description"],
                    parameters=step_data["parameters"],
                    expected_result=step_data["expected_result"],
                    timeout=step_data["timeout"],
                    retry_count=step_data["retry_count"],
                    conditions=step_data["conditions"]
                )
                
                step_result = await self.execution_engine.execute_step(
                    step, execution_context or {}
                )
                
                step_results.append(step_result)
                execution_result.steps_completed += 1
                
                if not step_result["success"]:
                    execution_result.status = WorkflowStatus.FAILED
                    execution_result.error_message = step_result["error"]
                    break
            
            # Update execution result
            if execution_result.status == WorkflowStatus.RUNNING:
                execution_result.status = WorkflowStatus.COMPLETED
            
            execution_result.completed_at = datetime.utcnow()
            execution_result.results = {
                "step_results": step_results,
                "total_execution_time": (execution_result.completed_at - execution_result.started_at).total_seconds()
            }
            
            # Update execution record
            self.executions_collection.update_one(
                {"execution_id": execution_id},
                {
                    "$set": {
                        "status": execution_result.status.value,
                        "completed_at": execution_result.completed_at,
                        "steps_completed": execution_result.steps_completed,
                        "results": execution_result.results,
                        "error_message": execution_result.error_message
                    }
                }
            )
            
            return {
                "success": execution_result.status == WorkflowStatus.COMPLETED,
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": execution_result.status.value,
                "steps_completed": execution_result.steps_completed,
                "total_steps": execution_result.total_steps,
                "execution_time": execution_result.results["total_execution_time"],
                "step_results": step_results,
                "error_message": execution_result.error_message
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def modify_workflow(self, workflow_id: str, modification_prompt: str) -> Dict[str, Any]:
        """Modify existing workflow based on natural language instructions"""
        try:
            # Get existing workflow
            workflow_doc = self.workflows_collection.find_one({"workflow_id": workflow_id})
            if not workflow_doc:
                return {"success": False, "error": "Workflow not found"}
            
            # Parse modification intent
            modification_intent = await self.intent_parser.parse_modification_intent(
                modification_prompt, workflow_doc["original_prompt"]
            )
            
            if not modification_intent["success"]:
                return {
                    "success": False,
                    "error": "Failed to parse modification intent",
                    "details": modification_intent.get("error")
                }
            
            # Apply modifications
            modified_workflow = await self.workflow_generator.modify_workflow(
                workflow_doc, modification_intent["modifications"]
            )
            
            if not modified_workflow["success"]:
                return {
                    "success": False,
                    "error": "Failed to apply modifications",
                    "details": modified_workflow.get("error")
                }
            
            # Update workflow
            self.workflows_collection.update_one(
                {"workflow_id": workflow_id},
                {
                    "$set": {
                        "steps": modified_workflow["steps"],
                        "description": modified_workflow["description"],
                        "estimated_duration": modified_workflow["estimated_duration"],
                        "modified_at": datetime.utcnow(),
                        "modification_prompt": modification_prompt
                    }
                }
            )
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "modifications_applied": len(modification_intent["modifications"]),
                "new_steps_count": len(modified_workflow["steps"]),
                "message": "Workflow successfully modified"
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow modification error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_code(self, workflow_id: str, target_language: str = "python") -> Dict[str, Any]:
        """Generate executable code from workflow"""
        try:
            # Get workflow
            workflow_doc = self.workflows_collection.find_one({"workflow_id": workflow_id})
            if not workflow_doc:
                return {"success": False, "error": "Workflow not found"}
            
            # Generate code
            code_result = await self.code_generator.generate_code(
                workflow_doc, target_language
            )
            
            return code_result
            
        except Exception as e:
            logger.error(f"❌ Code generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_workflow_suggestions(self, partial_prompt: str) -> Dict[str, Any]:
        """Get workflow suggestions based on partial natural language input"""
        try:
            # Analyze partial prompt
            suggestions = await self._analyze_partial_prompt(partial_prompt)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "prompt": partial_prompt
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow suggestions error: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestions": []
            }

    # Helper methods
    async def _analyze_partial_prompt(self, partial_prompt: str) -> List[Dict[str, Any]]:
        """Analyze partial prompt and suggest completions"""
        suggestions = []
        
        # Match against known patterns
        for pattern_type, pattern_info in self.language_patterns.items():
            for pattern in pattern_info["patterns"]:
                if any(word in partial_prompt.lower() for word in pattern.split()[:2]):
                    suggestions.append({
                        "completion": pattern,
                        "action_type": pattern_info["action_type"].value,
                        "description": f"Complete {pattern_type.replace('_', ' ')} action",
                        "confidence": 0.8
                    })
        
        # Add common workflow templates
        if "automate" in partial_prompt.lower():
            suggestions.extend([
                {
                    "completion": "automate social media posting every day",
                    "action_type": ActionType.LOOP.value,
                    "description": "Automated social media workflow",
                    "confidence": 0.7
                },
                {
                    "completion": "automate data collection from websites",
                    "action_type": ActionType.EXTRACT.value,
                    "description": "Web scraping automation",
                    "confidence": 0.7
                }
            ])
        
        return suggestions[:5]  # Return top 5 suggestions


class IntentParser:
    """Parse natural language intents for workflow generation"""
    
    async def parse_intent(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse natural language prompt into structured intents"""
        try:
            intents = []
            
            # Tokenize and analyze prompt
            sentences = self._split_into_sentences(prompt)
            
            for sentence in sentences:
                intent = self._analyze_sentence(sentence, context)
                if intent:
                    intents.append(intent)
            
            return {
                "success": True,
                "intents": intents,
                "original_prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"Intent parsing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def parse_modification_intent(self, modification_prompt: str, original_prompt: str) -> Dict[str, Any]:
        """Parse modification instructions"""
        try:
            modifications = []
            
            # Analyze modification type
            if "add" in modification_prompt.lower() or "insert" in modification_prompt.lower():
                modifications.append({
                    "type": "add",
                    "description": modification_prompt,
                    "position": "end"  # Default position
                })
            
            elif "remove" in modification_prompt.lower() or "delete" in modification_prompt.lower():
                modifications.append({
                    "type": "remove",
                    "description": modification_prompt,
                    "target": self._extract_removal_target(modification_prompt)
                })
            
            elif "change" in modification_prompt.lower() or "modify" in modification_prompt.lower():
                modifications.append({
                    "type": "modify",
                    "description": modification_prompt,
                    "target": self._extract_modification_target(modification_prompt)
                })
            
            return {
                "success": True,
                "modifications": modifications
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _analyze_sentence(self, sentence: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze individual sentence for intent"""
        sentence_lower = sentence.lower().strip()
        
        # Navigation intent
        if any(word in sentence_lower for word in ["go to", "visit", "open", "navigate"]):
            return {
                "type": "navigation",
                "action": ActionType.NAVIGATE.value,
                "description": sentence,
                "parameters": self._extract_navigation_parameters(sentence)
            }
        
        # Interaction intent
        elif any(word in sentence_lower for word in ["click", "press", "select", "choose"]):
            return {
                "type": "interaction",
                "action": ActionType.CLICK.value,
                "description": sentence,
                "parameters": self._extract_interaction_parameters(sentence)
            }
        
        # Input intent
        elif any(word in sentence_lower for word in ["type", "enter", "fill", "input"]):
            return {
                "type": "input",
                "action": ActionType.TYPE.value,
                "description": sentence,
                "parameters": self._extract_input_parameters(sentence)
            }
        
        # Extraction intent
        elif any(word in sentence_lower for word in ["extract", "get", "scrape", "collect"]):
            return {
                "type": "extraction",
                "action": ActionType.EXTRACT.value,
                "description": sentence,
                "parameters": self._extract_extraction_parameters(sentence)
            }
        
        return None

    def _extract_navigation_parameters(self, sentence: str) -> Dict[str, Any]:
        """Extract parameters for navigation actions"""
        # Simple URL extraction
        url_match = re.search(r'https?://[^\s]+', sentence)
        if url_match:
            return {"url": url_match.group()}
        
        # Website name extraction
        for site in ["google", "github", "youtube", "facebook", "twitter", "linkedin"]:
            if site in sentence.lower():
                return {"website": site, "url": f"https://{site}.com"}
        
        return {"description": sentence}

    def _extract_interaction_parameters(self, sentence: str) -> Dict[str, Any]:
        """Extract parameters for interaction actions"""
        # Extract element description
        click_words = ["click", "press", "select", "choose"]
        for word in click_words:
            if word in sentence.lower():
                parts = sentence.lower().split(word)
                if len(parts) > 1:
                    element = parts[1].strip().split()[0:3]  # Take first 3 words
                    return {"element": " ".join(element)}
        
        return {"description": sentence}

    def _extract_input_parameters(self, sentence: str) -> Dict[str, Any]:
        """Extract parameters for input actions"""
        # Extract quoted text
        quoted_match = re.search(r'"([^"]*)"', sentence)
        if quoted_match:
            return {"text": quoted_match.group(1)}
        
        # Extract text after input keywords
        input_words = ["type", "enter", "fill", "input"]
        for word in input_words:
            if word in sentence.lower():
                parts = sentence.lower().split(word)
                if len(parts) > 1:
                    text = parts[1].strip()
                    return {"text": text}
        
        return {"description": sentence}

    def _extract_extraction_parameters(self, sentence: str) -> Dict[str, Any]:
        """Extract parameters for extraction actions"""
        return {"description": sentence, "target": "page_content"}

    def _extract_removal_target(self, modification_prompt: str) -> str:
        """Extract what should be removed"""
        # Simple extraction of removal target
        words = modification_prompt.lower().split()
        remove_idx = -1
        for i, word in enumerate(words):
            if word in ["remove", "delete"]:
                remove_idx = i
                break
        
        if remove_idx >= 0 and remove_idx + 1 < len(words):
            return " ".join(words[remove_idx + 1:remove_idx + 4])  # Next 3 words
        
        return "unspecified"

    def _extract_modification_target(self, modification_prompt: str) -> str:
        """Extract what should be modified"""
        # Simple extraction of modification target
        words = modification_prompt.lower().split()
        change_idx = -1
        for i, word in enumerate(words):
            if word in ["change", "modify"]:
                change_idx = i
                break
        
        if change_idx >= 0 and change_idx + 1 < len(words):
            return " ".join(words[change_idx + 1:change_idx + 4])  # Next 3 words
        
        return "unspecified"


class WorkflowGenerator:
    """Generate workflow steps from parsed intents"""
    
    async def generate_steps(self, intents: List[Dict[str, Any]], original_prompt: str) -> Dict[str, Any]:
        """Generate workflow steps from intents"""
        try:
            steps = []
            step_number = 1
            
            for intent in intents:
                step = WorkflowStep(
                    step_id=str(uuid.uuid4()),
                    step_number=step_number,
                    action_type=ActionType(intent["action"]),
                    description=intent["description"],
                    parameters=intent["parameters"],
                    expected_result=self._generate_expected_result(intent),
                    timeout=30,  # Default timeout
                    retry_count=3,
                    conditions=[]
                )
                
                steps.append(step)
                step_number += 1
            
            # Generate workflow metadata
            workflow_name = self._generate_workflow_name(original_prompt)
            description = self._generate_workflow_description(steps, original_prompt)
            estimated_duration = self._estimate_duration(steps)
            complexity_score = self._calculate_complexity(steps)
            
            return {
                "success": True,
                "workflow_name": workflow_name,
                "description": description,
                "steps": steps,
                "estimated_duration": estimated_duration,
                "complexity_score": complexity_score,
                "confidence": 0.8  # Default confidence
            }
            
        except Exception as e:
            logger.error(f"Workflow generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def modify_workflow(self, workflow_doc: Dict[str, Any], modifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply modifications to existing workflow"""
        try:
            steps = workflow_doc["steps"].copy()
            
            for modification in modifications:
                if modification["type"] == "add":
                    # Add new step
                    new_step = {
                        "step_id": str(uuid.uuid4()),
                        "step_number": len(steps) + 1,
                        "action_type": ActionType.NAVIGATE.value,  # Default
                        "description": modification["description"],
                        "parameters": {},
                        "expected_result": "Step completed successfully",
                        "timeout": 30,
                        "retry_count": 3,
                        "conditions": []
                    }
                    steps.append(new_step)
                
                elif modification["type"] == "remove":
                    # Remove matching steps
                    steps = [s for s in steps if modification["target"].lower() not in s["description"].lower()]
                
                elif modification["type"] == "modify":
                    # Modify matching steps
                    for step in steps:
                        if modification["target"].lower() in step["description"].lower():
                            step["description"] = f"{step['description']} (Modified: {modification['description']})"
            
            # Renumber steps
            for i, step in enumerate(steps):
                step["step_number"] = i + 1
            
            return {
                "success": True,
                "steps": steps,
                "description": f"Modified: {workflow_doc['description']}",
                "estimated_duration": self._estimate_duration_from_docs(steps)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_expected_result(self, intent: Dict[str, Any]) -> str:
        """Generate expected result for a workflow step"""
        action_type = intent["action"]
        
        result_templates = {
            ActionType.NAVIGATE.value: "Successfully navigated to the specified page",
            ActionType.CLICK.value: "Successfully clicked the target element",
            ActionType.TYPE.value: "Successfully entered the specified text",
            ActionType.EXTRACT.value: "Successfully extracted the requested data",
            ActionType.ANALYZE.value: "Successfully analyzed the specified content"
        }
        
        return result_templates.get(action_type, "Action completed successfully")

    def _generate_workflow_name(self, original_prompt: str) -> str:
        """Generate name for workflow based on prompt"""
        # Extract key action words
        action_words = []
        for word in original_prompt.split()[:5]:  # First 5 words
            if word.lower() not in ["the", "a", "an", "to", "and", "or", "but"]:
                action_words.append(word.capitalize())
        
        return " ".join(action_words[:3]) + " Workflow"

    def _generate_workflow_description(self, steps: List[WorkflowStep], original_prompt: str) -> str:
        """Generate description for workflow"""
        return f"Automated workflow with {len(steps)} steps based on: {original_prompt[:100]}..."

    def _estimate_duration(self, steps: List[WorkflowStep]) -> int:
        """Estimate workflow duration in seconds"""
        base_time = 5  # Base time per step
        return len(steps) * base_time

    def _estimate_duration_from_docs(self, steps: List[Dict[str, Any]]) -> int:
        """Estimate duration from step documents"""
        return len(steps) * 5

    def _calculate_complexity(self, steps: List[WorkflowStep]) -> float:
        """Calculate workflow complexity score"""
        complexity = 0.0
        
        for step in steps:
            if step.action_type == ActionType.CONDITION:
                complexity += 0.3
            elif step.action_type == ActionType.LOOP:
                complexity += 0.4
            elif step.action_type == ActionType.ANALYZE:
                complexity += 0.2
            else:
                complexity += 0.1
        
        return min(complexity, 1.0)


class CodeGenerator:
    """Generate executable code from workflows"""
    
    async def generate_code(self, workflow_doc: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Generate code in target language"""
        try:
            if target_language.lower() == "python":
                code = self._generate_python_code(workflow_doc)
            elif target_language.lower() == "javascript":
                code = self._generate_javascript_code(workflow_doc)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported target language: {target_language}"
                }
            
            return {
                "success": True,
                "language": target_language,
                "code": code,
                "workflow_id": workflow_doc["workflow_id"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_python_code(self, workflow_doc: Dict[str, Any]) -> str:
        """Generate Python code"""
        code_lines = [
            "# Auto-generated workflow code",
            f"# Workflow: {workflow_doc['name']}",
            f"# Description: {workflow_doc['description']}",
            "",
            "import time",
            "from selenium import webdriver",
            "from selenium.webdriver.common.by import By",
            "",
            "def execute_workflow():",
            "    \"\"\"Execute the generated workflow\"\"\"",
            "    driver = webdriver.Chrome()",
            "    try:"
        ]
        
        for step in workflow_doc["steps"]:
            action_type = step["action_type"]
            
            if action_type == "navigate":
                url = step["parameters"].get("url", "https://example.com")
                code_lines.append(f"        # Step {step['step_number']}: {step['description']}")
                code_lines.append(f"        driver.get('{url}')")
                code_lines.append("        time.sleep(2)")
            
            elif action_type == "click":
                element = step["parameters"].get("element", "button")
                code_lines.append(f"        # Step {step['step_number']}: {step['description']}")
                code_lines.append(f"        driver.find_element(By.XPATH, '//*[contains(text(), \"{element}\")]').click()")
                code_lines.append("        time.sleep(1)")
            
            elif action_type == "type":
                text = step["parameters"].get("text", "sample text")
                code_lines.append(f"        # Step {step['step_number']}: {step['description']}")
                code_lines.append(f"        driver.find_element(By.TAG_NAME, 'input').send_keys('{text}')")
                code_lines.append("        time.sleep(1)")
        
        code_lines.extend([
            "    finally:",
            "        driver.quit()",
            "",
            "if __name__ == '__main__':",
            "    execute_workflow()"
        ])
        
        return "\n".join(code_lines)

    def _generate_javascript_code(self, workflow_doc: Dict[str, Any]) -> str:
        """Generate JavaScript code"""
        code_lines = [
            "// Auto-generated workflow code",
            f"// Workflow: {workflow_doc['name']}",
            f"// Description: {workflow_doc['description']}",
            "",
            "const puppeteer = require('puppeteer');",
            "",
            "async function executeWorkflow() {",
            "    const browser = await puppeteer.launch();",
            "    const page = await browser.newPage();",
            "    try {"
        ]
        
        for step in workflow_doc["steps"]:
            action_type = step["action_type"]
            
            if action_type == "navigate":
                url = step["parameters"].get("url", "https://example.com")
                code_lines.append(f"        // Step {step['step_number']}: {step['description']}")
                code_lines.append(f"        await page.goto('{url}');")
                code_lines.append("        await page.waitForTimeout(2000);")
            
            elif action_type == "click":
                element = step["parameters"].get("element", "button")
                code_lines.append(f"        // Step {step['step_number']}: {step['description']}")
                code_lines.append(f"        await page.click('*:contains(\"{element}\")');")
                code_lines.append("        await page.waitForTimeout(1000);")
            
            elif action_type == "type":
                text = step["parameters"].get("text", "sample text")
                code_lines.append(f"        // Step {step['step_number']}: {step['description']}")
                code_lines.append(f"        await page.type('input', '{text}');")
                code_lines.append("        await page.waitForTimeout(1000);")
        
        code_lines.extend([
            "    } finally {",
            "        await browser.close();",
            "    }",
            "}",
            "",
            "executeWorkflow().catch(console.error);"
        ])
        
        return "\n".join(code_lines)


class ExecutionEngine:
    """Execute workflow steps"""
    
    async def execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual workflow step"""
        try:
            # Simulate step execution
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Basic step execution simulation
            result = {
                "success": True,
                "step_id": step.step_id,
                "step_number": step.step_number,
                "action_type": step.action_type.value,
                "description": step.description,
                "result": step.expected_result,
                "execution_time": 0.1,
                "output": {}
            }
            
            # Add action-specific outputs
            if step.action_type == ActionType.NAVIGATE:
                result["output"] = {"url": step.parameters.get("url", "unknown")}
            elif step.action_type == ActionType.EXTRACT:
                result["output"] = {"data_extracted": f"Sample data from {step.description}"}
            elif step.action_type == ActionType.ANALYZE:
                result["output"] = {"analysis": f"Analysis result for {step.description}"}
            
            return result
            
        except Exception as e:
            logger.error(f"Step execution error: {e}")
            return {
                "success": False,
                "step_id": step.step_id,
                "step_number": step.step_number,
                "error": str(e),
                "execution_time": 0
            }


# Initialize functions for integration
def initialize_natural_language_programming(db_client: MongoClient) -> NaturalLanguageProgramming:
    """Initialize and return natural language programming framework"""
    return NaturalLanguageProgramming(db_client)

def get_natural_language_programming() -> Optional[NaturalLanguageProgramming]:
    """Get the global natural language programming instance"""
    return getattr(get_natural_language_programming, '_instance', None)

def set_natural_language_programming_instance(instance: NaturalLanguageProgramming):
    """Set the global natural language programming instance"""
    get_natural_language_programming._instance = instance