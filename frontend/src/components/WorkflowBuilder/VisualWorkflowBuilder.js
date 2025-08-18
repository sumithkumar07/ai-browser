import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  useReactFlow,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';

import WorkflowNode from './WorkflowNode';
import WorkflowEdge from './WorkflowEdge';
import NodePalette from './NodePalette';
import WorkflowProperties from './WorkflowProperties';
import WorkflowTester from './WorkflowTester';

const nodeTypes = {
  action: WorkflowNode,
  condition: WorkflowNode,
  trigger: WorkflowNode,
  integration: WorkflowNode
};

const edgeTypes = {
  workflow: WorkflowEdge
};

const VisualWorkflowBuilder = ({ isVisible, onClose, initialWorkflow = null }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [isPropertiesOpen, setIsPropertiesOpen] = useState(false);
  const [isTesterOpen, setIsTesterOpen] = useState(false);
  const [workflowData, setWorkflowData] = useState({
    name: 'Untitled Workflow',
    description: '',
    category: 'Custom',
    triggers: [],
    variables: {},
    settings: {}
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const reactFlowWrapper = useRef(null);
  const { project, getViewport } = useReactFlow();

  useEffect(() => {
    if (initialWorkflow && isVisible) {
      loadWorkflow(initialWorkflow);
    }
  }, [initialWorkflow, isVisible]);

  const loadWorkflow = (workflow) => {
    setWorkflowData({
      name: workflow.name || 'Loaded Workflow',
      description: workflow.description || '',
      category: workflow.category || 'Custom',
      triggers: workflow.triggers || [],
      variables: workflow.variables || {},
      settings: workflow.settings || {}
    });

    // Convert workflow steps to nodes and edges
    const workflowNodes = [];
    const workflowEdges = [];

    if (workflow.steps) {
      workflow.steps.forEach((step, index) => {
        workflowNodes.push({
          id: step.id || `step-${index}`,
          type: step.type === 'condition' ? 'condition' : 'action',
          position: step.position || { x: 100 + index * 200, y: 100 },
          data: {
            label: step.name,
            config: step.config || {},
            stepType: step.type,
            description: step.description
          }
        });

        // Create edges based on dependencies
        if (step.dependencies) {
          step.dependencies.forEach(depId => {
            workflowEdges.push({
              id: `${depId}-${step.id}`,
              source: depId,
              target: step.id,
              type: 'workflow'
            });
          });
        }
      });
    }

    setNodes(workflowNodes);
    setEdges(workflowEdges);
  };

  const onConnect = useCallback((params) => {
    const edge = {
      ...params,
      type: 'workflow',
      id: `edge-${params.source}-${params.target}`,
      data: {
        condition: null,
        label: ''
      }
    };
    setEdges((eds) => addEdge(edge, eds));
  }, [setEdges]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event) => {
    event.preventDefault();

    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
    const nodeType = event.dataTransfer.getData('application/reactflow');

    if (typeof nodeType === 'undefined' || !nodeType) {
      return;
    }

    const position = project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    });

    const newNode = {
      id: `${nodeType}-${Date.now()}`,
      type: nodeType,
      position,
      data: getDefaultNodeData(nodeType),
    };

    setNodes((nds) => nds.concat(newNode));
  }, [project, setNodes]);

  const getDefaultNodeData = (nodeType) => {
    const defaults = {
      action: {
        label: 'New Action',
        stepType: 'action',
        config: {
          action_type: 'http_request',
          method: 'GET',
          url: '',
          headers: {}
        },
        description: 'Execute an action'
      },
      condition: {
        label: 'New Condition',
        stepType: 'condition',
        config: {
          left_value: '',
          operator: 'equals',
          right_value: '',
          on_true: 'continue',
          on_false: 'skip'
        },
        description: 'Check a condition'
      },
      trigger: {
        label: 'New Trigger',
        stepType: 'trigger',
        config: {
          trigger_type: 'manual',
          schedule: '',
          webhook_url: ''
        },
        description: 'Start the workflow'
      },
      integration: {
        label: 'New Integration',
        stepType: 'integration',
        config: {
          integration_id: '',
          endpoint: '',
          parameters: {}
        },
        description: 'Call external service'
      }
    };

    return defaults[nodeType] || defaults.action;
  };

  const onNodeClick = (event, node) => {
    setSelectedNode(node);
    setIsPropertiesOpen(true);
  };

  const onNodeDoubleClick = (event, node) => {
    // Quick edit node label
    const newLabel = prompt('Enter node name:', node.data.label);
    if (newLabel && newLabel !== node.data.label) {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === node.id
            ? { ...n, data: { ...n.data, label: newLabel } }
            : n
        )
      );
    }
  };

  const updateNodeData = (nodeId, newData) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...newData } }
          : node
      )
    );
  };

  const deleteNode = (nodeId) => {
    setNodes((nds) => nds.filter((n) => n.id !== nodeId));
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null);
      setIsPropertiesOpen(false);
    }
  };

  const saveWorkflow = async () => {
    setSaving(true);
    try {
      const workflowSteps = nodes.map(node => ({
        id: node.id,
        name: node.data.label,
        type: node.data.stepType,
        config: node.data.config,
        description: node.data.description,
        position: node.position,
        dependencies: edges
          .filter(edge => edge.target === node.id)
          .map(edge => edge.source)
      }));

      const workflow = {
        ...workflowData,
        steps: workflowSteps,
        metadata: {
          nodeCount: nodes.length,
          edgeCount: edges.length,
          lastModified: new Date().toISOString(),
          viewport: getViewport()
        }
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/workflows/visual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(workflow)
      });

      if (response.ok) {
        const result = await response.json();
        alert('Workflow saved successfully!');
        console.log('Saved workflow:', result.workflow_id);
      } else {
        throw new Error('Failed to save workflow');
      }
    } catch (error) {
      console.error('Error saving workflow:', error);
      alert('Failed to save workflow. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const testWorkflow = async () => {
    setTesting(true);
    setIsTesterOpen(true);
    
    try {
      const workflowSteps = nodes.map(node => ({
        id: node.id,
        name: node.data.label,
        type: node.data.stepType,
        config: node.data.config,
        dependencies: edges
          .filter(edge => edge.target === node.id)
          .map(edge => edge.source)
      }));

      const testData = {
        workflow: {
          ...workflowData,
          steps: workflowSteps
        },
        testParameters: {}
      };

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/workflows/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData)
      });

      const result = await response.json();
      return result;

    } catch (error) {
      console.error('Error testing workflow:', error);
      return {
        success: false,
        error: error.message
      };
    } finally {
      setTesting(false);
    }
  };

  const clearWorkflow = () => {
    if (window.confirm('Are you sure you want to clear the workflow? This cannot be undone.')) {
      setNodes([]);
      setEdges([]);
      setSelectedNode(null);
      setIsPropertiesOpen(false);
      setWorkflowData({
        name: 'Untitled Workflow',
        description: '',
        category: 'Custom',
        triggers: [],
        variables: {},
        settings: {}
      });
    }
  };

  const autoArrangeNodes = () => {
    // Simple auto-layout algorithm
    const nodeWidth = 200;
    const nodeHeight = 100;
    const horizontalSpacing = 250;
    const verticalSpacing = 150;

    // Topological sort to arrange nodes in order
    const inDegree = {};
    const adjList = {};

    nodes.forEach(node => {
      inDegree[node.id] = 0;
      adjList[node.id] = [];
    });

    edges.forEach(edge => {
      adjList[edge.source].push(edge.target);
      inDegree[edge.target]++;
    });

    const queue = [];
    const levels = {};
    let maxLevel = 0;

    // Find nodes with no incoming edges
    Object.keys(inDegree).forEach(nodeId => {
      if (inDegree[nodeId] === 0) {
        queue.push({ id: nodeId, level: 0 });
        levels[0] = levels[0] || [];
        levels[0].push(nodeId);
      }
    });

    // Process nodes level by level
    while (queue.length > 0) {
      const { id: currentId, level } = queue.shift();
      
      adjList[currentId].forEach(neighborId => {
        inDegree[neighborId]--;
        if (inDegree[neighborId] === 0) {
          const nextLevel = level + 1;
          maxLevel = Math.max(maxLevel, nextLevel);
          levels[nextLevel] = levels[nextLevel] || [];
          levels[nextLevel].push(neighborId);
          queue.push({ id: neighborId, level: nextLevel });
        }
      });
    }

    // Position nodes based on levels
    const updatedNodes = nodes.map(node => {
      let level = 0;
      for (let l = 0; l <= maxLevel; l++) {
        if (levels[l] && levels[l].includes(node.id)) {
          level = l;
          break;
        }
      }

      const nodesInLevel = levels[level] || [];
      const indexInLevel = nodesInLevel.indexOf(node.id);
      const totalInLevel = nodesInLevel.length;

      const x = level * horizontalSpacing + 100;
      const y = (indexInLevel - (totalInLevel - 1) / 2) * verticalSpacing + 300;

      return {
        ...node,
        position: { x, y }
      };
    });

    setNodes(updatedNodes);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-full h-full max-w-7xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">Visual Workflow Builder</h2>
            <input
              type="text"
              value={workflowData.name}
              onChange={(e) => setWorkflowData({ ...workflowData, name: e.target.value })}
              className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={autoArrangeNodes}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
            >
              Auto Arrange
            </button>
            <button
              onClick={clearWorkflow}
              className="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-700 rounded"
            >
              Clear
            </button>
            <button
              onClick={testWorkflow}
              disabled={testing || nodes.length === 0}
              className="px-4 py-1 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded disabled:opacity-50"
            >
              {testing ? 'Testing...' : 'Test'}
            </button>
            <button
              onClick={saveWorkflow}
              disabled={saving || nodes.length === 0}
              className="px-4 py-1 text-sm bg-green-100 hover:bg-green-200 text-green-700 rounded disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Node Palette */}
          <NodePalette />

          {/* Workflow Canvas */}
          <div className="flex-1 relative" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onDrop={onDrop}
              onDragOver={onDragOver}
              onNodeClick={onNodeClick}
              onNodeDoubleClick={onNodeDoubleClick}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              fitView
              attributionPosition="bottom-left"
            >
              <Background color="#f1f5f9" gap={20} />
              <Controls />
              <MiniMap
                nodeColor={(node) => {
                  switch (node.type) {
                    case 'trigger': return '#10b981';
                    case 'condition': return '#f59e0b';
                    case 'integration': return '#8b5cf6';
                    default: return '#3b82f6';
                  }
                }}
                nodeStrokeWidth={3}
                zoomable
                pannable
              />
              
              {/* Workflow Info Panel */}
              <Panel position="top-left">
                <div className="bg-white rounded-lg shadow-md p-3 text-sm">
                  <div className="flex items-center space-x-4 text-gray-600">
                    <span>Nodes: {nodes.length}</span>
                    <span>Connections: {edges.length}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      nodes.length > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {nodes.length > 0 ? 'Active' : 'Empty'}
                    </span>
                  </div>
                </div>
              </Panel>

              {/* Quick Actions Panel */}
              <Panel position="top-right">
                <div className="bg-white rounded-lg shadow-md p-2">
                  <div className="flex flex-col space-y-2">
                    <button
                      onClick={() => setIsPropertiesOpen(!isPropertiesOpen)}
                      className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                    >
                      {isPropertiesOpen ? 'Hide Properties' : 'Show Properties'}
                    </button>
                    <button
                      onClick={() => setIsTesterOpen(!isTesterOpen)}
                      className="px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded"
                    >
                      {isTesterOpen ? 'Hide Tester' : 'Show Tester'}
                    </button>
                  </div>
                </div>
              </Panel>
            </ReactFlow>
          </div>

          {/* Properties Panel */}
          {isPropertiesOpen && (
            <WorkflowProperties
              selectedNode={selectedNode}
              workflowData={workflowData}
              onNodeUpdate={updateNodeData}
              onNodeDelete={deleteNode}
              onWorkflowUpdate={setWorkflowData}
              onClose={() => setIsPropertiesOpen(false)}
            />
          )}
        </div>

        {/* Workflow Tester */}
        {isTesterOpen && (
          <WorkflowTester
            workflow={{ ...workflowData, steps: nodes, connections: edges }}
            onClose={() => setIsTesterOpen(false)}
            onTest={testWorkflow}
            testing={testing}
          />
        )}
      </div>
    </div>
  );
};

const VisualWorkflowBuilderWrapper = (props) => {
  return (
    <ReactFlowProvider>
      <VisualWorkflowBuilder {...props} />
    </ReactFlowProvider>
  );
};

export default VisualWorkflowBuilderWrapper;