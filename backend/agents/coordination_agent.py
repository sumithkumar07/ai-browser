"""
Coordination Agent - Orchestrates multi-agent collaborations
Implements Fellou.ai's Deep Action (ADA) style coordination
"""
import asyncio
from typing import Dict, List, Any
from .base_agent import BaseAgent

class CoordinationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type="coordinator",
            capabilities=[
                "task_decomposition",
                "agent_selection", 
                "workflow_orchestration",
                "result_compilation",
                "parallel_coordination"
            ]
        )
        self.available_agents = {}
        self.active_workflows = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent for coordination"""
        self.available_agents[agent.agent_id] = agent
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate execution of complex multi-agent tasks"""
        await self.update_status("analyzing", task)
        
        # 1. Analyze task complexity and decompose
        subtasks = await self._decompose_task(task)
        
        # 2. Create execution plan with agent assignments
        execution_plan = await self._create_execution_plan(subtasks)
        
        # 3. Execute plan with parallel agent coordination
        await self.update_status("executing", task)
        results = await self._execute_coordinated_plan(execution_plan)
        
        # 4. Compile and optimize final result
        final_result = await self._compile_results(results, task)
        
        await self.update_status("completed", task)
        await self.learn_from_execution(task, final_result)
        
        return final_result
    
    async def _decompose_task(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose complex task into manageable subtasks"""
        task_description = task.get("description", "")
        complexity = task.get("complexity", "medium")
        
        # Analyze task for decomposition patterns
        subtasks = []
        
        if "research" in task_description.lower():
            subtasks.append({
                "id": f"{task['id']}_research",
                "type": "research",
                "description": f"Research phase: {task_description}",
                "assigned_agent_type": "research",
                "priority": 1
            })
        
        if "automate" in task_description.lower() or "workflow" in task_description.lower():
            subtasks.append({
                "id": f"{task['id']}_automation", 
                "type": "automation",
                "description": f"Automation phase: {task_description}",
                "assigned_agent_type": "automation",
                "priority": 2
            })
        
        if "analyze" in task_description.lower() or "data" in task_description.lower():
            subtasks.append({
                "id": f"{task['id']}_analysis",
                "type": "analysis", 
                "description": f"Analysis phase: {task_description}",
                "assigned_agent_type": "analysis",
                "priority": 3
            })
        
        # Default subtask if no specific patterns found
        if not subtasks:
            subtasks.append({
                "id": f"{task['id']}_general",
                "type": "general_execution",
                "description": task_description,
                "assigned_agent_type": "automation",
                "priority": 1
            })
        
        return subtasks
    
    async def _create_execution_plan(self, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create optimized execution plan with agent assignments"""
        execution_phases = []
        current_phase = []
        
        # Group subtasks into parallel execution phases
        for subtask in sorted(subtasks, key=lambda x: x.get("priority", 1)):
            # Check if subtask can run in parallel with current phase
            can_parallelize = await self._can_run_in_parallel(subtask, current_phase)
            
            if can_parallelize and len(current_phase) < 3:  # Max 3 parallel tasks
                current_phase.append(subtask)
            else:
                # Start new phase
                if current_phase:
                    execution_phases.append(current_phase)
                current_phase = [subtask]
        
        # Add final phase
        if current_phase:
            execution_phases.append(current_phase)
        
        return {
            "phases": execution_phases,
            "estimated_duration": self._estimate_execution_time(execution_phases),
            "agent_requirements": self._calculate_agent_requirements(execution_phases)
        }
    
    async def _execute_coordinated_plan(self, execution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute the coordinated plan with multiple agents"""
        all_results = []
        
        for phase_idx, phase in enumerate(execution_plan["phases"]):
            phase_results = []
            
            # Execute subtasks in parallel within each phase
            phase_tasks = []
            for subtask in phase:
                # Find appropriate agent for subtask
                agent = await self._select_agent_for_task(subtask)
                if agent:
                    task_coroutine = agent.execute(subtask)
                    phase_tasks.append(task_coroutine)
                else:
                    # Fallback to coordination agent handling
                    phase_results.append({
                        "subtask_id": subtask["id"],
                        "success": False,
                        "error": "No suitable agent available"
                    })
            
            # Execute phase tasks in parallel
            if phase_tasks:
                parallel_results = await asyncio.gather(*phase_tasks, return_exceptions=True)
                
                for i, result in enumerate(parallel_results):
                    if isinstance(result, Exception):
                        phase_results.append({
                            "subtask_id": phase[i]["id"],
                            "success": False,
                            "error": str(result)
                        })
                    else:
                        phase_results.append(result)
            
            all_results.extend(phase_results)
            
            # Brief pause between phases for system stability
            if phase_idx < len(execution_plan["phases"]) - 1:
                await asyncio.sleep(0.1)
        
        return all_results
    
    async def _select_agent_for_task(self, subtask: Dict[str, Any]) -> BaseAgent:
        """Select the best available agent for a subtask"""
        required_agent_type = subtask.get("assigned_agent_type", "automation")
        
        # Find agents of the required type that are available
        suitable_agents = []
        for agent in self.available_agents.values():
            if (agent.agent_type == required_agent_type and 
                agent.status in ["idle", "available"] and
                await agent.can_handle_task(subtask)):
                suitable_agents.append(agent)
        
        if not suitable_agents:
            return None
        
        # Select agent with best performance metrics for this task type
        best_agent = max(suitable_agents, key=lambda a: self._calculate_agent_score(a, subtask))
        return best_agent
    
    def _calculate_agent_score(self, agent: BaseAgent, subtask: Dict[str, Any]) -> float:
        """Calculate agent suitability score for a subtask"""
        base_score = 0.5
        
        # Performance history bonus
        metrics = agent.get_performance_metrics()
        success_rate_bonus = metrics["success_rate"] * 0.3
        
        # Task type experience bonus
        task_type = subtask.get("type", "unknown")
        if task_type in agent.learning_data:
            experience_bonus = min(len(agent.learning_data[task_type]) / 10, 0.2)
        else:
            experience_bonus = 0
        
        return base_score + success_rate_bonus + experience_bonus
    
    async def _can_run_in_parallel(self, subtask: Dict[str, Any], current_phase: List[Dict[str, Any]]) -> bool:
        """Check if subtask can run in parallel with current phase tasks"""
        if not current_phase:
            return True
        
        # Check for dependencies or conflicts
        subtask_type = subtask.get("type", "")
        
        for phase_task in current_phase:
            phase_task_type = phase_task.get("type", "")
            
            # Research and analysis can usually run in parallel
            if (subtask_type in ["research", "analysis"] and 
                phase_task_type in ["research", "analysis"]):
                return True
            
            # Automation tasks might conflict
            if subtask_type == "automation" and phase_task_type == "automation":
                return False
        
        return True
    
    def _estimate_execution_time(self, execution_phases: List[List[Dict[str, Any]]]) -> float:
        """Estimate total execution time for the plan"""
        total_time = 0
        
        for phase in execution_phases:
            # Phase time is max of individual subtask times (parallel execution)
            phase_time = 0
            for subtask in phase:
                estimated_subtask_time = subtask.get("estimated_duration", 30)  # Default 30 seconds
                phase_time = max(phase_time, estimated_subtask_time)
            
            total_time += phase_time
        
        return total_time
    
    def _calculate_agent_requirements(self, execution_phases: List[List[Dict[str, Any]]]) -> Dict[str, int]:
        """Calculate agent requirements for the execution plan"""
        requirements = {}
        
        for phase in execution_phases:
            for subtask in phase:
                agent_type = subtask.get("assigned_agent_type", "automation")
                requirements[agent_type] = requirements.get(agent_type, 0) + 1
        
        return requirements
    
    async def _compile_results(self, results: List[Dict[str, Any]], original_task: Dict[str, Any]) -> Dict[str, Any]:
        """Compile individual agent results into final coordinated result"""
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]
        
        # Aggregate data from successful results
        compiled_data = {}
        for result in successful_results:
            if "data" in result:
                compiled_data.update(result["data"])
        
        # Generate summary
        summary = f"Multi-agent coordination completed: {len(successful_results)}/{len(results)} subtasks successful"
        
        return {
            "success": len(successful_results) > len(failed_results),
            "agent_coordination": True,
            "total_subtasks": len(results),
            "successful_subtasks": len(successful_results),
            "failed_subtasks": len(failed_results),
            "compiled_data": compiled_data,
            "summary": summary,
            "coordination_agent_id": self.agent_id,
            "execution_time": sum(r.get("execution_time", 0) for r in results),
            "detailed_results": results
        }