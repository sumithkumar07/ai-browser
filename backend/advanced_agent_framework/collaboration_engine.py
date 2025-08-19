"""
Advanced Collaboration Engine for AETHER
Enables sophisticated multi-agent coordination and teamwork
"""

import asyncio
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import logging

class CollaborationPattern(Enum):
    PIPELINE = "pipeline"  # Sequential processing
    PARALLEL = "parallel"  # Independent parallel work
    HIERARCHICAL = "hierarchical"  # Leader-subordinate
    MESH = "mesh"  # Full interconnected collaboration
    CONSENSUS = "consensus"  # Group decision making

class CommunicationProtocol(Enum):
    DIRECT = "direct"  # Agent-to-agent
    BROADCAST = "broadcast"  # One-to-many
    PUBLISH_SUBSCRIBE = "pub_sub"  # Event-driven
    REQUEST_RESPONSE = "req_resp"  # Synchronous communication

@dataclass
class CollaborationSession:
    id: str
    name: str
    participants: List[str]
    pattern: CollaborationPattern
    protocol: CommunicationProtocol
    objectives: List[str]
    constraints: Dict[str, Any]
    created_at: datetime
    status: str = "active"
    leader_id: Optional[str] = None
    shared_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.shared_context is None:
            self.shared_context = {}

@dataclass  
class Message:
    id: str
    sender_id: str
    recipient_id: Optional[str]  # None for broadcast
    content: Dict[str, Any]
    message_type: str
    timestamp: datetime
    requires_response: bool = False
    response_timeout: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class CollaborationEngine:
    def __init__(self):
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.message_queue: List[Message] = []
        self.communication_channels: Dict[str, List[str]] = {}  # session_id -> participant_ids
        self.shared_workspaces: Dict[str, Dict[str, Any]] = {}
        self.collaboration_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("CollaborationEngine")
        
        # Advanced features
        self.conflict_resolver = ConflictResolver()
        self.decision_engine = GroupDecisionEngine()
        self.knowledge_base = SharedKnowledgeBase()

    async def create_collaboration_session(self, session_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collaboration session"""
        try:
            session_id = session_config.get("id") or str(uuid.uuid4())
            
            session = CollaborationSession(
                id=session_id,
                name=session_config["name"],
                participants=session_config["participants"],
                pattern=CollaborationPattern(session_config.get("pattern", "parallel")),
                protocol=CommunicationProtocol(session_config.get("protocol", "broadcast")),
                objectives=session_config.get("objectives", []),
                constraints=session_config.get("constraints", {}),
                created_at=datetime.now(),
                leader_id=session_config.get("leader_id")
            )
            
            self.active_sessions[session_id] = session
            self.communication_channels[session_id] = session.participants.copy()
            self.shared_workspaces[session_id] = {"documents": {}, "data": {}, "decisions": []}
            
            # Initialize participants
            await self.initialize_collaboration_participants(session_id)
            
            # Set up communication protocols
            await self.setup_communication_protocols(session_id)
            
            self.logger.info(f"Collaboration session '{session.name}' created with {len(session.participants)} participants")
            
            return {
                "success": True,
                "session_id": session_id,
                "participants": len(session.participants),
                "pattern": session.pattern.value,
                "protocol": session.protocol.value,
                "workspace_url": f"/collaboration/{session_id}/workspace"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def initialize_collaboration_participants(self, session_id: str):
        """Initialize participants in a collaboration session"""
        try:
            session = self.active_sessions[session_id]
            
            # Send welcome message to all participants
            welcome_message = Message(
                id=str(uuid.uuid4()),
                sender_id="system",
                recipient_id=None,  # Broadcast
                content={
                    "type": "session_start",
                    "session_id": session_id,
                    "session_name": session.name,
                    "participants": session.participants,
                    "objectives": session.objectives,
                    "collaboration_pattern": session.pattern.value
                },
                message_type="system_notification",
                timestamp=datetime.now()
            )
            
            await self.broadcast_message(session_id, welcome_message)
            
            # Assign roles based on collaboration pattern
            if session.pattern == CollaborationPattern.HIERARCHICAL:
                await self.assign_hierarchical_roles(session_id)
            elif session.pattern == CollaborationPattern.CONSENSUS:
                await self.setup_consensus_mechanism(session_id)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize participants: {e}")

    async def setup_communication_protocols(self, session_id: str):
        """Set up communication protocols for the session"""
        try:
            session = self.active_sessions[session_id]
            
            if session.protocol == CommunicationProtocol.PUBLISH_SUBSCRIBE:
                # Set up topic-based communication
                await self.setup_pub_sub_topics(session_id)
            elif session.protocol == CommunicationProtocol.REQUEST_RESPONSE:
                # Set up synchronous communication handlers
                await self.setup_req_resp_handlers(session_id)
            
        except Exception as e:
            self.logger.error(f"Failed to setup communication protocols: {e}")

    async def send_message(self, session_id: str, sender_id: str, message_content: Dict[str, Any], 
                          recipient_id: Optional[str] = None) -> Dict[str, Any]:
        """Send a message within a collaboration session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            if sender_id not in session.participants:
                return {"success": False, "error": "Sender not a participant"}
            
            message = Message(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=message_content,
                message_type=message_content.get("type", "general"),
                timestamp=datetime.now(),
                requires_response=message_content.get("requires_response", False),
                response_timeout=message_content.get("response_timeout")
            )
            
            # Route message based on protocol
            if recipient_id:
                await self.route_direct_message(session_id, message)
            else:
                await self.broadcast_message(session_id, message)
            
            return {
                "success": True,
                "message_id": message.id,
                "delivered_at": datetime.now().isoformat(),
                "recipients": 1 if recipient_id else len(session.participants) - 1
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def route_direct_message(self, session_id: str, message: Message):
        """Route a direct message to specific recipient"""
        # In real implementation, this would send to the actual agent
        self.message_queue.append(message)
        
        # Log communication
        self.collaboration_history.append({
            "session_id": session_id,
            "action": "direct_message",
            "sender": message.sender_id,
            "recipient": message.recipient_id,
            "timestamp": message.timestamp,
            "message_type": message.message_type
        })

    async def broadcast_message(self, session_id: str, message: Message):
        """Broadcast a message to all participants"""
        session = self.active_sessions[session_id]
        
        # Send to all participants except sender
        for participant_id in session.participants:
            if participant_id != message.sender_id:
                direct_message = Message(
                    id=str(uuid.uuid4()),
                    sender_id=message.sender_id,
                    recipient_id=participant_id,
                    content=message.content,
                    message_type=message.message_type,
                    timestamp=message.timestamp
                )
                self.message_queue.append(direct_message)
        
        # Log broadcast
        self.collaboration_history.append({
            "session_id": session_id,
            "action": "broadcast",
            "sender": message.sender_id,
            "recipients": len(session.participants) - 1,
            "timestamp": message.timestamp,
            "message_type": message.message_type
        })

    async def coordinate_task_execution(self, session_id: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate task execution across multiple agents"""
        try:
            session = self.active_sessions[session_id]
            
            coordination_result = None
            
            if session.pattern == CollaborationPattern.PIPELINE:
                coordination_result = await self.coordinate_pipeline_execution(session_id, task_config)
            elif session.pattern == CollaborationPattern.PARALLEL:
                coordination_result = await self.coordinate_parallel_execution(session_id, task_config)
            elif session.pattern == CollaborationPattern.HIERARCHICAL:
                coordination_result = await self.coordinate_hierarchical_execution(session_id, task_config)
            elif session.pattern == CollaborationPattern.MESH:
                coordination_result = await self.coordinate_mesh_execution(session_id, task_config)
            elif session.pattern == CollaborationPattern.CONSENSUS:
                coordination_result = await self.coordinate_consensus_execution(session_id, task_config)
            
            return coordination_result or {"success": False, "error": "Unsupported collaboration pattern"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def coordinate_pipeline_execution(self, session_id: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate sequential pipeline execution"""
        try:
            session = self.active_sessions[session_id]
            participants = session.participants
            subtasks = task_config.get("subtasks", [])
            
            if len(subtasks) != len(participants):
                # Auto-distribute task
                subtasks = self.auto_distribute_task(task_config, len(participants))
            
            results = []
            current_data = task_config.get("input_data", {})
            
            for i, (participant_id, subtask) in enumerate(zip(participants, subtasks)):
                # Send task to participant
                task_message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="coordinator",
                    recipient_id=participant_id,
                    content={
                        "type": "task_assignment",
                        "subtask": subtask,
                        "input_data": current_data,
                        "pipeline_position": i,
                        "total_stages": len(participants)
                    },
                    message_type="task_assignment",
                    timestamp=datetime.now(),
                    requires_response=True,
                    response_timeout=300
                )
                
                await self.route_direct_message(session_id, task_message)
                
                # Simulate task execution and response
                await asyncio.sleep(1)  # Simulated processing time
                
                # Simulate successful completion
                execution_result = {
                    "success": True,
                    "participant_id": participant_id,
                    "subtask_id": subtask.get("id", f"subtask_{i}"),
                    "output_data": {**current_data, f"stage_{i}_result": f"processed_by_{participant_id}"},
                    "execution_time": 1.0
                }
                
                results.append(execution_result)
                current_data = execution_result["output_data"]
            
            return {
                "success": True,
                "coordination_type": "pipeline",
                "total_stages": len(participants),
                "results": results,
                "final_output": current_data,
                "total_execution_time": sum(r.get("execution_time", 0) for r in results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def coordinate_parallel_execution(self, session_id: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate parallel execution across agents"""
        try:
            session = self.active_sessions[session_id]
            participants = session.participants
            subtasks = task_config.get("subtasks", [])
            
            if len(subtasks) != len(participants):
                subtasks = self.auto_distribute_task(task_config, len(participants))
            
            # Send tasks to all participants simultaneously
            task_assignments = []
            for i, (participant_id, subtask) in enumerate(zip(participants, subtasks)):
                task_message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="coordinator",
                    recipient_id=participant_id,
                    content={
                        "type": "task_assignment",
                        "subtask": subtask,
                        "input_data": task_config.get("input_data", {}),
                        "parallel_id": i,
                        "coordination_mode": "parallel"
                    },
                    message_type="task_assignment",
                    timestamp=datetime.now(),
                    requires_response=True,
                    response_timeout=300
                )
                
                task_assignments.append(self.route_direct_message(session_id, task_message))
            
            # Wait for all assignments to be sent
            await asyncio.gather(*task_assignments)
            
            # Simulate parallel execution
            await asyncio.sleep(2)  # Simulated processing time
            
            # Collect results
            results = []
            for i, participant_id in enumerate(participants):
                execution_result = {
                    "success": True,
                    "participant_id": participant_id,
                    "subtask_id": subtasks[i].get("id", f"subtask_{i}"),
                    "output_data": {f"parallel_result_{i}": f"processed_by_{participant_id}"},
                    "execution_time": 2.0
                }
                results.append(execution_result)
            
            # Merge parallel results
            merged_output = {}
            for result in results:
                merged_output.update(result["output_data"])
            
            return {
                "success": True,
                "coordination_type": "parallel",
                "participants": len(participants),
                "results": results,
                "merged_output": merged_output,
                "max_execution_time": max(r.get("execution_time", 0) for r in results),
                "efficiency_gain": f"{len(participants)}x parallelization"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def auto_distribute_task(self, task_config: Dict[str, Any], num_participants: int) -> List[Dict[str, Any]]:
        """Automatically distribute a task among participants"""
        main_task = task_config.get("description", "Main task")
        task_type = task_config.get("type", "general")
        
        subtasks = []
        for i in range(num_participants):
            subtasks.append({
                "id": f"auto_subtask_{i}",
                "description": f"{main_task} - Part {i+1}/{num_participants}",
                "type": task_type,
                "requirements": task_config.get("requirements", []),
                "estimated_duration": task_config.get("estimated_duration", 300) // num_participants
            })
        
        return subtasks

    async def manage_shared_workspace(self, session_id: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage shared workspace for collaboration"""
        try:
            if session_id not in self.shared_workspaces:
                return {"success": False, "error": "Workspace not found"}
            
            workspace = self.shared_workspaces[session_id]
            
            if action == "add_document":
                doc_id = data.get("id") or str(uuid.uuid4())
                workspace["documents"][doc_id] = {
                    "id": doc_id,
                    "title": data["title"],
                    "content": data["content"],
                    "created_by": data["created_by"],
                    "created_at": datetime.now().isoformat(),
                    "version": 1,
                    "collaborators": []
                }
                return {"success": True, "document_id": doc_id}
            
            elif action == "update_document":
                doc_id = data["id"]
                if doc_id in workspace["documents"]:
                    doc = workspace["documents"][doc_id]
                    doc["content"] = data["content"]
                    doc["version"] += 1
                    doc["last_modified"] = datetime.now().isoformat()
                    doc["last_modified_by"] = data["modified_by"]
                    
                    if data["modified_by"] not in doc["collaborators"]:
                        doc["collaborators"].append(data["modified_by"])
                    
                    return {"success": True, "version": doc["version"]}
                else:
                    return {"success": False, "error": "Document not found"}
            
            elif action == "share_data":
                data_key = data["key"]
                workspace["data"][data_key] = {
                    "value": data["value"],
                    "shared_by": data["shared_by"],
                    "shared_at": datetime.now().isoformat(),
                    "access_level": data.get("access_level", "read_write")
                }
                return {"success": True, "data_key": data_key}
            
            elif action == "make_decision":
                decision = {
                    "id": str(uuid.uuid4()),
                    "description": data["description"],
                    "options": data["options"],
                    "proposed_by": data["proposed_by"],
                    "proposed_at": datetime.now().isoformat(),
                    "status": "proposed",
                    "votes": {}
                }
                workspace["decisions"].append(decision)
                return {"success": True, "decision_id": decision["id"]}
            
            elif action == "get_workspace":
                return {
                    "success": True,
                    "workspace": workspace,
                    "last_activity": max([
                        doc.get("last_modified", doc["created_at"]) 
                        for doc in workspace["documents"].values()
                    ] + [datetime.now().isoformat()])
                }
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def resolve_conflicts(self, session_id: str, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicts in collaboration"""
        return await self.conflict_resolver.resolve_conflict(session_id, conflict_data)

    async def make_group_decision(self, session_id: str, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Facilitate group decision making"""
        return await self.decision_engine.process_decision(session_id, decision_data)

    async def get_collaboration_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a collaboration session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            # Get session history
            session_history = [
                event for event in self.collaboration_history 
                if event["session_id"] == session_id
            ]
            
            # Calculate metrics
            total_messages = len(session_history)
            message_types = {}
            participant_activity = {}
            
            for event in session_history:
                msg_type = event.get("message_type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
                
                sender = event.get("sender", "unknown")
                participant_activity[sender] = participant_activity.get(sender, 0) + 1
            
            # Calculate collaboration effectiveness
            effectiveness_score = self.calculate_collaboration_effectiveness(session_id, session_history)
            
            analytics = {
                "session_id": session_id,
                "session_name": session.name,
                "duration": (datetime.now() - session.created_at).total_seconds(),
                "participants": len(session.participants),
                "pattern": session.pattern.value,
                "protocol": session.protocol.value,
                "metrics": {
                    "total_messages": total_messages,
                    "message_types": message_types,
                    "participant_activity": participant_activity,
                    "effectiveness_score": effectiveness_score,
                    "objectives_completed": len(session.objectives)  # Simplified
                },
                "workspace_stats": {
                    "documents": len(self.shared_workspaces.get(session_id, {}).get("documents", {})),
                    "shared_data": len(self.shared_workspaces.get(session_id, {}).get("data", {})),
                    "decisions": len(self.shared_workspaces.get(session_id, {}).get("decisions", []))
                }
            }
            
            return {"success": True, "analytics": analytics}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def calculate_collaboration_effectiveness(self, session_id: str, history: List[Dict[str, Any]]) -> float:
        """Calculate collaboration effectiveness score"""
        try:
            if not history:
                return 0.0
            
            session = self.active_sessions[session_id]
            
            # Participation balance (all participants should be active)
            participant_counts = {}
            for event in history:
                sender = event.get("sender", "unknown")
                if sender != "system" and sender != "coordinator":
                    participant_counts[sender] = participant_counts.get(sender, 0) + 1
            
            if participant_counts:
                participation_balance = 1.0 - (max(participant_counts.values()) - min(participant_counts.values())) / max(participant_counts.values())
            else:
                participation_balance = 0.0
            
            # Communication efficiency (fewer messages per objective is better)
            communication_efficiency = min(1.0, len(session.objectives) / max(len(history), 1))
            
            # Pattern adherence (messages follow expected pattern)
            pattern_adherence = 0.8  # Simplified calculation
            
            # Overall effectiveness
            effectiveness = (participation_balance * 0.4) + (communication_efficiency * 0.3) + (pattern_adherence * 0.3)
            
            return round(effectiveness, 2)
        except Exception:
            return 0.5  # Default moderate effectiveness

    async def end_collaboration_session(self, session_id: str) -> Dict[str, Any]:
        """End a collaboration session"""
        try:
            if session_id not in self.active_sessions:
                return {"success": False, "error": "Session not found"}
            
            session = self.active_sessions[session_id]
            session.status = "completed"
            
            # Generate final report
            analytics = await self.get_collaboration_analytics(session_id)
            
            # Archive session data
            archive_data = {
                "session": session.__dict__,
                "workspace": self.shared_workspaces.get(session_id, {}),
                "analytics": analytics.get("analytics", {}),
                "ended_at": datetime.now().isoformat()
            }
            
            # Clean up active data
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            if session_id in self.communication_channels:
                del self.communication_channels[session_id]
            if session_id in self.shared_workspaces:
                del self.shared_workspaces[session_id]
            
            return {
                "success": True,
                "session_id": session_id,
                "final_report": archive_data,
                "message": "Collaboration session ended successfully"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Supporting classes
class ConflictResolver:
    """Resolve conflicts in collaborative environments"""
    
    async def resolve_conflict(self, session_id: str, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve a collaboration conflict"""
        conflict_type = conflict_data.get("type", "resource_contention")
        
        if conflict_type == "resource_contention":
            return await self.resolve_resource_conflict(conflict_data)
        elif conflict_type == "decision_disagreement":
            return await self.resolve_decision_conflict(conflict_data)
        else:
            return {"success": False, "error": f"Unknown conflict type: {conflict_type}"}
    
    async def resolve_resource_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve resource contention conflicts"""
        # Implement resource allocation algorithm
        return {
            "success": True,
            "resolution": "time_sharing",
            "allocation": conflict_data.get("participants", [])
        }
    
    async def resolve_decision_conflict(self, conflict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve decision disagreements"""
        # Implement consensus building algorithm
        return {
            "success": True,
            "resolution": "majority_vote",
            "recommended_action": "proceed_with_majority_decision"
        }

class GroupDecisionEngine:
    """Facilitate group decision making processes"""
    
    async def process_decision(self, session_id: str, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a group decision"""
        decision_type = decision_data.get("type", "majority_vote")
        
        if decision_type == "majority_vote":
            return await self.majority_vote_decision(decision_data)
        elif decision_type == "consensus":
            return await self.consensus_decision(decision_data)
        elif decision_type == "weighted_vote":
            return await self.weighted_vote_decision(decision_data)
        else:
            return {"success": False, "error": f"Unknown decision type: {decision_type}"}
    
    async def majority_vote_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process majority vote decision"""
        votes = decision_data.get("votes", {})
        if not votes:
            return {"success": False, "error": "No votes provided"}
        
        vote_counts = {}
        for vote in votes.values():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        winner = max(vote_counts.items(), key=lambda x: x[1])
        
        return {
            "success": True,
            "decision": winner[0],
            "vote_counts": vote_counts,
            "winning_margin": winner[1] / len(votes)
        }
    
    async def consensus_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process consensus decision"""
        # Simplified consensus - all must agree
        votes = decision_data.get("votes", {})
        unique_votes = set(votes.values())
        
        if len(unique_votes) == 1:
            return {
                "success": True,
                "decision": list(unique_votes)[0],
                "consensus_achieved": True
            }
        else:
            return {
                "success": False,
                "consensus_achieved": False,
                "conflicting_options": list(unique_votes)
            }
    
    async def weighted_vote_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process weighted vote decision"""
        votes = decision_data.get("votes", {})
        weights = decision_data.get("weights", {})
        
        weighted_scores = {}
        for voter, vote in votes.items():
            weight = weights.get(voter, 1.0)
            weighted_scores[vote] = weighted_scores.get(vote, 0) + weight
        
        winner = max(weighted_scores.items(), key=lambda x: x[1])
        
        return {
            "success": True,
            "decision": winner[0],
            "weighted_scores": weighted_scores,
            "total_weight": sum(weights.values())
        }

class SharedKnowledgeBase:
    """Shared knowledge base for collaborative learning"""
    
    def __init__(self):
        self.knowledge_entries = {}
        self.learning_patterns = {}
    
    async def add_knowledge(self, session_id: str, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add knowledge to shared base"""
        if session_id not in self.knowledge_entries:
            self.knowledge_entries[session_id] = []
        
        knowledge_entry = {
            "id": str(uuid.uuid4()),
            "content": knowledge_data["content"],
            "source": knowledge_data["source"],
            "timestamp": datetime.now(),
            "relevance_score": knowledge_data.get("relevance_score", 1.0)
        }
        
        self.knowledge_entries[session_id].append(knowledge_entry)
        
        return {"success": True, "knowledge_id": knowledge_entry["id"]}
    
    async def query_knowledge(self, session_id: str, query: str) -> Dict[str, Any]:
        """Query the shared knowledge base"""
        if session_id not in self.knowledge_entries:
            return {"success": True, "results": []}
        
        # Simple text matching (in production, use more sophisticated NLP)
        results = []
        for entry in self.knowledge_entries[session_id]:
            if query.lower() in entry["content"].lower():
                results.append(entry)
        
        return {"success": True, "results": results}