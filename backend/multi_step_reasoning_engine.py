# Phase 1: Multi-Step Reasoning Engine
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid
from enum import Enum

logger = logging.getLogger(__name__)

class ReasoningStep(Enum):
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    VALIDATE = "validate"
    ADAPT = "adapt"

class MultiStepReasoningEngine:
    """
    Phase 1: Advanced Multi-Step Reasoning Engine
    Provides intelligent problem-solving with step-by-step reasoning
    """
    
    def __init__(self):
        self.active_reasoning_chains = {}
        self.reasoning_templates = self._load_reasoning_templates()
        self.step_executors = self._initialize_step_executors()
    
    async def create_reasoning_chain(self, problem_description: str, context: Dict[str, Any] = None) -> str:
        """Create a new multi-step reasoning chain"""
        try:
            chain_id = str(uuid.uuid4())
            
            # Analyze problem and create reasoning steps
            reasoning_steps = await self._decompose_problem(problem_description, context)
            
            reasoning_chain = {
                "chain_id": chain_id,
                "problem_description": problem_description,
                "context": context or {},
                "steps": reasoning_steps,
                "current_step": 0,
                "status": "created",
                "created_at": datetime.utcnow(),
                "results": [],
                "intermediate_conclusions": [],
                "confidence_scores": []
            }
            
            self.active_reasoning_chains[chain_id] = reasoning_chain
            
            logger.info(f"Created reasoning chain: {chain_id} with {len(reasoning_steps)} steps")
            return chain_id
            
        except Exception as e:
            logger.error(f"Failed to create reasoning chain: {e}")
            raise
    
    async def execute_reasoning_chain(self, chain_id: str) -> Dict[str, Any]:
        """Execute the entire reasoning chain with adaptive intelligence"""
        try:
            if chain_id not in self.active_reasoning_chains:
                raise ValueError(f"Reasoning chain {chain_id} not found")
            
            chain = self.active_reasoning_chains[chain_id]
            chain["status"] = "executing"
            chain["started_at"] = datetime.utcnow()
            
            # Execute each step in sequence with adaptive logic
            for step_index, step in enumerate(chain["steps"]):
                chain["current_step"] = step_index
                
                # Execute individual step
                step_result = await self._execute_reasoning_step(step, chain)
                
                # Store intermediate results
                chain["results"].append(step_result)
                
                # Analyze step result and adapt if necessary
                adaptation_result = await self._analyze_and_adapt(step_result, chain)
                
                if adaptation_result["should_adapt"]:
                    # Modify subsequent steps based on learning
                    chain["steps"] = await self._adapt_reasoning_steps(
                        chain["steps"], 
                        step_index, 
                        adaptation_result
                    )
                
                # Check if early termination is beneficial
                if adaptation_result["can_terminate_early"]:
                    logger.info(f"Early termination beneficial for chain {chain_id}")
                    break
                
                # Update confidence and conclusions
                chain["confidence_scores"].append(step_result.get("confidence", 0.7))
                if step_result.get("conclusion"):
                    chain["intermediate_conclusions"].append(step_result["conclusion"])
            
            # Generate final synthesis
            final_result = await self._synthesize_final_result(chain)
            
            chain["status"] = "completed"
            chain["completed_at"] = datetime.utcnow()
            chain["final_result"] = final_result
            
            return {
                "chain_id": chain_id,
                "status": "completed",
                "final_result": final_result,
                "steps_executed": len(chain["results"]),
                "total_confidence": self._calculate_overall_confidence(chain),
                "execution_time": (chain["completed_at"] - chain["started_at"]).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Reasoning chain execution failed: {e}")
            if chain_id in self.active_reasoning_chains:
                self.active_reasoning_chains[chain_id]["status"] = "failed"
                self.active_reasoning_chains[chain_id]["error"] = str(e)
            raise
    
    async def _decompose_problem(self, problem: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose complex problem into reasoning steps"""
        
        # Use AI to intelligently decompose the problem
        decomposition_prompt = f"""
        Decompose this problem into logical reasoning steps:
        
        Problem: {problem}
        Context: {json.dumps(context, default=str)}
        
        Create a sequence of reasoning steps that should include:
        1. Analysis of the problem
        2. Planning the approach
        3. Execution steps
        4. Validation of results
        5. Adaptation if needed
        
        Return as JSON array with: step_type, description, inputs, expected_outputs, dependencies
        """
        
        # Get AI decomposition
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=decomposition_prompt,
            context=None,
            session_history=[],
            query_type="problem_decomposition"
        )
        
        try:
            # Extract JSON from AI response
            import re
            json_match = re.search(r'\[.*\]', ai_response["response"], re.DOTALL)
            if json_match:
                steps = json.loads(json_match.group())
                return self._enhance_reasoning_steps(steps)
            else:
                return self._create_default_steps(problem, context)
        except:
            return self._create_default_steps(problem, context)
    
    def _enhance_reasoning_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
        """Enhance reasoning steps with additional metadata"""
        enhanced_steps = []
        
        for i, step in enumerate(steps):
            enhanced_step = {
                **step,
                "step_id": str(uuid.uuid4()),
                "step_index": i,
                "status": "pending",
                "estimated_complexity": self._estimate_step_complexity(step),
                "required_capabilities": self._identify_required_capabilities(step),
                "fallback_strategies": self._generate_fallback_strategies(step),
                "success_criteria": self._define_success_criteria(step)
            }
            enhanced_steps.append(enhanced_step)
        
        return enhanced_steps
    
    def _create_default_steps(self, problem: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create default reasoning steps when AI decomposition fails"""
        
        steps = [
            {
                "step_type": "analyze",
                "description": f"Analyze the problem: {problem}",
                "inputs": {"problem": problem, "context": context},
                "expected_outputs": {"analysis": "problem_analysis", "key_factors": "list"},
                "dependencies": []
            },
            {
                "step_type": "plan",
                "description": "Plan solution approach",
                "inputs": {"analysis_result": "from_previous"},
                "expected_outputs": {"plan": "solution_plan", "steps": "action_steps"},
                "dependencies": ["analyze"]
            },
            {
                "step_type": "execute",
                "description": "Execute planned solution",
                "inputs": {"plan": "from_previous"},
                "expected_outputs": {"result": "execution_result"},
                "dependencies": ["plan"]
            },
            {
                "step_type": "validate",
                "description": "Validate solution effectiveness",
                "inputs": {"execution_result": "from_previous"},
                "expected_outputs": {"validation": "validation_result"},
                "dependencies": ["execute"]
            }
        ]
        
        return self._enhance_reasoning_steps(steps)
    
    async def _execute_reasoning_step(self, step: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual reasoning step"""
        step_type = step.get("step_type", "analyze")
        step_id = step["step_id"]
        
        logger.info(f"Executing reasoning step {step_id}: {step_type}")
        
        try:
            # Route to appropriate step executor
            if step_type in self.step_executors:
                executor = self.step_executors[step_type]
                result = await executor(step, chain)
            else:
                result = await self._execute_generic_step(step, chain)
            
            return {
                "step_id": step_id,
                "step_type": step_type,
                "success": True,
                "result": result,
                "confidence": result.get("confidence", 0.8),
                "conclusion": result.get("conclusion", ""),
                "executed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Step execution failed {step_id}: {e}")
            return {
                "step_id": step_id,
                "step_type": step_type,
                "success": False,
                "error": str(e),
                "confidence": 0.0,
                "executed_at": datetime.utcnow().isoformat()
            }
    
    async def _execute_analyze_step(self, step: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis reasoning step"""
        
        problem = chain["problem_description"]
        context = chain["context"]
        
        analysis_prompt = f"""
        Perform deep analysis of this problem:
        
        Problem: {problem}
        Context: {json.dumps(context, default=str)}
        
        Provide:
        1. Key problem components
        2. Underlying factors
        3. Constraints and limitations
        4. Success criteria
        5. Risk factors
        
        Be thorough and logical in your analysis.
        """
        
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=analysis_prompt,
            context=None,
            session_history=[],
            query_type="deep_analysis"
        )
        
        return {
            "analysis": ai_response["response"],
            "key_components": self._extract_key_components(ai_response["response"]),
            "confidence": 0.9,
            "conclusion": f"Analysis completed for: {problem[:100]}..."
        }
    
    async def _execute_plan_step(self, step: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning reasoning step"""
        
        # Get analysis from previous step
        previous_results = [r for r in chain["results"] if r["step_type"] == "analyze"]
        analysis_result = previous_results[-1]["result"] if previous_results else {}
        
        planning_prompt = f"""
        Based on the analysis, create a detailed solution plan:
        
        Analysis: {analysis_result.get("analysis", "No previous analysis")}
        Problem: {chain["problem_description"]}
        
        Create a step-by-step plan that addresses:
        1. Immediate actions needed
        2. Resource requirements
        3. Potential obstacles
        4. Success metrics
        5. Contingency plans
        
        Be specific and actionable.
        """
        
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=planning_prompt,
            context=None,
            session_history=[],
            query_type="strategic_planning"
        )
        
        return {
            "plan": ai_response["response"],
            "action_steps": self._extract_action_steps(ai_response["response"]),
            "confidence": 0.85,
            "conclusion": "Solution plan created with actionable steps"
        }
    
    async def _execute_execute_step(self, step: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Execute execution reasoning step"""
        
        # Get plan from previous step
        previous_results = [r for r in chain["results"] if r["step_type"] == "plan"]
        plan_result = previous_results[-1]["result"] if previous_results else {}
        
        # This would integrate with actual execution systems
        execution_result = {
            "executed_actions": plan_result.get("action_steps", []),
            "execution_status": "simulated_execution",
            "results_achieved": "Execution completed in simulation mode",
            "metrics_collected": {
                "execution_time": "estimated",
                "success_rate": "projected",
                "resource_usage": "calculated"
            }
        }
        
        return {
            "execution_result": execution_result,
            "confidence": 0.7,  # Lower confidence for simulated execution
            "conclusion": "Execution completed with projected results"
        }
    
    async def _execute_validate_step(self, step: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation reasoning step"""
        
        # Get execution results
        previous_results = [r for r in chain["results"] if r["step_type"] == "execute"]
        execution_result = previous_results[-1]["result"] if previous_results else {}
        
        validation_prompt = f"""
        Validate the execution results against the original problem:
        
        Original Problem: {chain["problem_description"]}
        Execution Results: {json.dumps(execution_result, default=str)}
        
        Evaluate:
        1. Did the solution address the core problem?
        2. Are the results satisfactory?
        3. What improvements could be made?
        4. Are there any remaining issues?
        5. Overall effectiveness score (1-10)
        
        Provide honest assessment.
        """
        
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=validation_prompt,
            context=None,
            session_history=[],
            query_type="result_validation"
        )
        
        return {
            "validation_result": ai_response["response"],
            "effectiveness_score": self._extract_effectiveness_score(ai_response["response"]),
            "confidence": 0.8,
            "conclusion": "Solution validation completed with recommendations"
        }
    
    async def _execute_generic_step(self, step: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic reasoning step"""
        
        step_description = step.get("description", "Generic step")
        
        generic_prompt = f"""
        Execute this reasoning step:
        
        Step: {step_description}
        Context: {json.dumps(step.get("inputs", {}), default=str)}
        Problem Context: {chain["problem_description"]}
        
        Provide thoughtful reasoning and conclusions.
        """
        
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=generic_prompt,
            context=None,
            session_history=[],
            query_type="generic_reasoning"
        )
        
        return {
            "step_result": ai_response["response"],
            "confidence": 0.7,
            "conclusion": f"Completed reasoning step: {step_description}"
        }
    
    async def _analyze_and_adapt(self, step_result: Dict[str, Any], chain: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze step result and determine adaptations needed"""
        
        confidence = step_result.get("confidence", 0.7)
        success = step_result.get("success", True)
        
        adaptation_result = {
            "should_adapt": False,
            "adaptation_type": None,
            "can_terminate_early": False,
            "confidence_threshold": 0.6
        }
        
        # Check if adaptation is needed based on confidence
        if confidence < adaptation_result["confidence_threshold"]:
            adaptation_result["should_adapt"] = True
            adaptation_result["adaptation_type"] = "low_confidence_recovery"
        
        # Check for early termination opportunities
        if confidence > 0.9 and len(chain["results"]) >= 2:
            adaptation_result["can_terminate_early"] = True
        
        # Check for failure recovery
        if not success:
            adaptation_result["should_adapt"] = True
            adaptation_result["adaptation_type"] = "failure_recovery"
        
        return adaptation_result
    
    async def _adapt_reasoning_steps(self, steps: List[Dict], current_index: int, adaptation: Dict[str, Any]) -> List[Dict]:
        """Adapt subsequent reasoning steps based on learning"""
        
        if adaptation["adaptation_type"] == "low_confidence_recovery":
            # Add validation step after low confidence result
            validation_step = {
                "step_type": "validate",
                "description": "Additional validation due to low confidence",
                "inputs": {"previous_result": "validation_needed"},
                "step_id": str(uuid.uuid4())
            }
            steps.insert(current_index + 1, validation_step)
        
        elif adaptation["adaptation_type"] == "failure_recovery":
            # Add recovery step after failure
            recovery_step = {
                "step_type": "adapt",
                "description": "Recovery from previous step failure",
                "inputs": {"failed_step": "recovery_needed"},
                "step_id": str(uuid.uuid4())
            }
            steps.insert(current_index + 1, recovery_step)
        
        return steps
    
    async def _synthesize_final_result(self, chain: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final result from all reasoning steps"""
        
        all_results = [r["result"] for r in chain["results"] if r["success"]]
        all_conclusions = chain["intermediate_conclusions"]
        
        synthesis_prompt = f"""
        Synthesize the final result from this multi-step reasoning:
        
        Original Problem: {chain["problem_description"]}
        
        Step Results: {json.dumps(all_results, default=str)}
        
        Intermediate Conclusions: {json.dumps(all_conclusions, default=str)}
        
        Provide:
        1. Final solution/answer
        2. Confidence in the result
        3. Key insights gained
        4. Remaining uncertainties
        5. Recommendations for improvement
        """
        
        from enhanced_ai_manager import enhanced_ai_manager
        
        ai_response = await enhanced_ai_manager.get_enhanced_ai_response(
            message=synthesis_prompt,
            context=None,
            session_history=[],
            query_type="result_synthesis"
        )
        
        return {
            "final_solution": ai_response["response"],
            "overall_confidence": self._calculate_overall_confidence(chain),
            "key_insights": self._extract_key_insights(ai_response["response"]),
            "steps_used": len(chain["results"]),
            "reasoning_quality": "high" if self._calculate_overall_confidence(chain) > 0.8 else "medium",
            "synthesis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _initialize_step_executors(self) -> Dict:
        """Initialize step executors for different reasoning types"""
        return {
            "analyze": self._execute_analyze_step,
            "plan": self._execute_plan_step,
            "execute": self._execute_execute_step,
            "validate": self._execute_validate_step,
            "adapt": self._execute_generic_step
        }
    
    def _load_reasoning_templates(self) -> Dict[str, Dict]:
        """Load predefined reasoning templates"""
        return {
            "problem_solving": {
                "steps": ["analyze", "plan", "execute", "validate"],
                "description": "General problem-solving template"
            },
            "decision_making": {
                "steps": ["analyze", "evaluate_options", "compare", "decide", "validate"],
                "description": "Decision-making template"
            },
            "research": {
                "steps": ["define_scope", "gather_info", "analyze", "synthesize", "conclude"],
                "description": "Research and analysis template"
            }
        }
    
    def _estimate_step_complexity(self, step: Dict) -> str:
        """Estimate complexity of reasoning step"""
        step_type = step.get("step_type", "")
        description = step.get("description", "")
        
        if step_type in ["analyze", "validate"]:
            return "high"
        elif step_type in ["plan", "adapt"]:
            return "medium" 
        else:
            return "low"
    
    def _identify_required_capabilities(self, step: Dict) -> List[str]:
        """Identify capabilities required for step"""
        capabilities = ["reasoning", "analysis"]
        
        step_type = step.get("step_type", "")
        if step_type == "execute":
            capabilities.append("automation")
        elif step_type == "plan":
            capabilities.append("strategic_thinking")
        elif step_type == "validate":
            capabilities.append("critical_evaluation")
        
        return capabilities
    
    def _generate_fallback_strategies(self, step: Dict) -> List[str]:
        """Generate fallback strategies for step"""
        return [
            "simplify_approach",
            "use_alternative_method",
            "skip_if_not_critical",
            "request_human_input"
        ]
    
    def _define_success_criteria(self, step: Dict) -> Dict[str, Any]:
        """Define success criteria for step"""
        return {
            "min_confidence": 0.6,
            "required_outputs": step.get("expected_outputs", {}),
            "max_execution_time": 300,  # 5 minutes
            "quality_threshold": "acceptable"
        }
    
    def _calculate_overall_confidence(self, chain: Dict[str, Any]) -> float:
        """Calculate overall confidence for reasoning chain"""
        scores = chain.get("confidence_scores", [])
        if not scores:
            return 0.5
        
        # Weighted average with recent steps having higher weight
        weights = [1.0 + i * 0.1 for i in range(len(scores))]
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _extract_key_components(self, analysis_text: str) -> List[str]:
        """Extract key components from analysis text"""
        # Simple keyword extraction
        keywords = []
        lines = analysis_text.split('\n')
        
        for line in lines:
            if any(indicator in line.lower() for indicator in ['key', 'important', 'critical', 'main']):
                cleaned_line = line.strip('- ').strip()
                if cleaned_line and len(cleaned_line) > 10:
                    keywords.append(cleaned_line)
        
        return keywords[:5]  # Top 5 key components
    
    def _extract_action_steps(self, plan_text: str) -> List[str]:
        """Extract action steps from plan text"""
        steps = []
        lines = plan_text.split('\n')
        
        for line in lines:
            if any(indicator in line.lower() for indicator in ['step', 'action', 'do', 'perform']):
                cleaned_line = line.strip('- ').strip()
                if cleaned_line and len(cleaned_line) > 5:
                    steps.append(cleaned_line)
        
        return steps[:10]  # Top 10 action steps
    
    def _extract_effectiveness_score(self, validation_text: str) -> float:
        """Extract effectiveness score from validation text"""
        import re
        
        # Look for score patterns like "8/10", "score: 7", "effectiveness: 85%"
        patterns = [
            r'(\d+)/10',
            r'score:?\s*(\d+)',
            r'effectiveness:?\s*(\d+)%',
            r'(\d+)\s*out of 10'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, validation_text.lower())
            if matches:
                try:
                    score = float(matches[0])
                    if score <= 10:
                        return score / 10.0
                    elif score <= 100:
                        return score / 100.0
                except:
                    continue
        
        return 0.7  # Default score
    
    def _extract_key_insights(self, synthesis_text: str) -> List[str]:
        """Extract key insights from synthesis text"""
        insights = []
        lines = synthesis_text.split('\n')
        
        for line in lines:
            if any(indicator in line.lower() for indicator in ['insight', 'learned', 'discovered', 'found']):
                cleaned_line = line.strip('- ').strip()
                if cleaned_line and len(cleaned_line) > 15:
                    insights.append(cleaned_line)
        
        return insights[:5]  # Top 5 insights
    
    async def get_reasoning_status(self, chain_id: str) -> Dict[str, Any]:
        """Get status of reasoning chain"""
        if chain_id not in self.active_reasoning_chains:
            return {"error": "Chain not found"}
        
        chain = self.active_reasoning_chains[chain_id]
        return {
            "chain_id": chain_id,
            "status": chain["status"],
            "current_step": chain["current_step"],
            "total_steps": len(chain["steps"]),
            "confidence_scores": chain["confidence_scores"],
            "intermediate_conclusions": chain["intermediate_conclusions"]
        }

# Global instance
multi_step_reasoning_engine = MultiStepReasoningEngine()