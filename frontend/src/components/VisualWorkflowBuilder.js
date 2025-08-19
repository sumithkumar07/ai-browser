import React, { useState, useEffect, useCallback } from 'react';

// Simple Node Component
const WorkflowNode = ({ node, onConnect, onDelete, isConnecting, onSelect }) => {
  const getNodeColor = (type) => {
    const colors = {
      trigger: 'bg-green-600 border-green-500',
      action: 'bg-blue-600 border-blue-500',
      transform: 'bg-purple-600 border-purple-500',
      output: 'bg-orange-600 border-orange-500',
      monitor: 'bg-pink-600 border-pink-500'
    };
    return colors[type] || 'bg-gray-600 border-gray-500';
  };

  const getNodeIcon = (type) => {
    const icons = {
      trigger: '▶️',
      action: '⚡',
      transform: '🔄',
      output: '📤',
      monitor: '📊'
    };
    return icons[type] || '📦';
  };

  return (
    <div
      className={`absolute border-2 rounded-lg p-3 min-w-32 cursor-move ${getNodeColor(node.node_type)} text-white shadow-lg`}
      style={{
        left: node.position.x,
        top: node.position.y,
        zIndex: 10
      }}
      onClick={() => onSelect?.(node)}
    >
      <div className="flex items-center space-x-2 mb-2">
        <span className="text-sm">{getNodeIcon(node.node_type)}</span>
        <span className="text-sm font-medium">{node.template_key.replace('_', ' ')}</span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete?.(node.node_id);
          }}
          className="text-xs text-red-300 hover:text-red-100 ml-auto"
        >
          ×
        </button>
      </div>
      
      {/* Connection Points */}
      <div className="flex justify-between">
        <div
          className="w-3 h-3 bg-white rounded-full border-2 border-current cursor-pointer hover:scale-110 transition-transform"
          title="Input"
        />
        <div
          className="w-3 h-3 bg-white rounded-full border-2 border-current cursor-pointer hover:scale-110 transition-transform"
          onClick={(e) => {
            e.stopPropagation();
            onConnect?.(node.node_id);
          }}
          title="Output - Click to connect"
        />
      </div>
      
      {node.parameters && Object.keys(node.parameters).length > 0 && (
        <div className="mt-2 text-xs opacity-75">
          {Object.keys(node.parameters).length} parameter{Object.keys(node.parameters).length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

const VisualWorkflowBuilder = ({ backendUrl, userSession }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [workflows, setWorkflows] = useState([]);
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflowNodes, setWorkflowNodes] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [sourceNode, setSourceNode] = useState(null);

  useEffect(() => {
    if (isVisible && userSession) {
      loadWorkflowTemplates();
      loadUserWorkflows();
    }
  }, [isVisible, userSession]);

  useEffect(() => {
    if (activeWorkflow) {
      loadWorkflowNodes();
    }
  }, [activeWorkflow]);

  const loadWorkflowTemplates = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflows/templates`);
      if (response.ok) {
        const result = await response.json();
        setTemplates(result.templates || []);
      }
    } catch (error) {
      console.error('Failed to load workflow templates:', error);
    }
  };

  const loadUserWorkflows = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflows/user/${userSession}`);
      if (response.ok) {
        const result = await response.json();
        setWorkflows(result.workflows || []);
      }
    } catch (error) {
      console.error('Failed to load user workflows:', error);
    }
  };

  const loadWorkflowNodes = async () => {
    if (!activeWorkflow) return;

    try {
      const response = await fetch(`${backendUrl}/api/workflows/${activeWorkflow}`);
      if (response.ok) {
        const result = await response.json();
        setWorkflowNodes(result.nodes || []);
      }
    } catch (error) {
      console.error('Failed to load workflow nodes:', error);
    }
  };

  const createNewWorkflow = async () => {
    const name = prompt('Enter workflow name:');
    if (!name) return;

    const description = prompt('Enter workflow description (optional):') || '';

    try {
      const response = await fetch(`${backendUrl}/api/workflows/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          created_by: userSession
        })
      });

      if (response.ok) {
        const result = await response.json();
        setActiveWorkflow(result.workflow_id);
        loadUserWorkflows(); // Refresh workflows list
      }
    } catch (error) {
      console.error('Failed to create workflow:', error);
    }
  };

  const addNodeToWorkflow = async (templateKey, x = 100, y = 100) => {
    if (!activeWorkflow) return;

    try {
      const response = await fetch(`${backendUrl}/api/workflows/add-node`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: activeWorkflow,
          template_key: templateKey,
          position_x: x + Math.random() * 100, // Add some randomness
          position_y: y + Math.random() * 100,
          parameters: {}
        })
      });

      if (response.ok) {
        loadWorkflowNodes(); // Refresh nodes
      }
    } catch (error) {
      console.error('Failed to add node:', error);
    }
  };

  const deleteNode = async (nodeId) => {
    // In a full implementation, this would call the backend to delete the node
    setWorkflowNodes(prev => prev.filter(node => node.node_id !== nodeId));
  };

  const connectNodes = async (sourceNodeId, targetNodeId) => {
    if (!activeWorkflow) return;

    try {
      const response = await fetch(`${backendUrl}/api/workflows/connect-nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: activeWorkflow,
          source_node: sourceNodeId,
          target_node: targetNodeId,
          source_output: 'output',
          target_input: 'input',
          connection_type: 'success'
        })
      });

      if (response.ok) {
        // In a full implementation, this would reload the workflow with connections
        console.log('Nodes connected successfully');
      }
    } catch (error) {
      console.error('Failed to connect nodes:', error);
    }
  };

  const handleNodeConnect = (nodeId) => {
    if (!isConnecting) {
      setIsConnecting(true);
      setSourceNode(nodeId);
    } else {
      // Complete the connection
      if (sourceNode && sourceNode !== nodeId) {
        connectNodes(sourceNode, nodeId);
      }
      setIsConnecting(false);
      setSourceNode(null);
    }
  };

  const getTemplateOptions = () => {
    const nodeTemplates = [
      { key: 'url_input', label: '🌐 URL Input', type: 'trigger' },
      { key: 'extract_data', label: '📊 Extract Data', type: 'action' },
      { key: 'process_data', label: '🔄 Process Data', type: 'transform' },
      { key: 'save_results', label: '💾 Save Results', type: 'output' },
      { key: 'send_notification', label: '📢 Send Notification', type: 'action' },
      { key: 'schedule_task', label: '⏰ Schedule Task', type: 'trigger' },
      { key: 'filter_content', label: '🔍 Filter Content', type: 'transform' },
      { key: 'monitor_changes', label: '👁️ Monitor Changes', type: 'monitor' }
    ];
    return nodeTemplates;
  };

  return (
    <>
      {/* Visual Workflow Builder Button */}
      <button
        className="nav-btn workflow-btn"
        onClick={() => setIsVisible(!isVisible)}
        title="Visual Workflow Builder - Drag & Drop Automation"
        aria-label="Toggle workflow builder"
      >
        🔧
      </button>

      {/* Workflow Builder Panel */}
      {isVisible && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50">
          <div className="absolute inset-4 bg-gray-900 border border-gray-600 rounded-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gray-800 p-4 border-b border-gray-600">
              <div className="flex items-center justify-between">
                <h2 className="text-white font-medium flex items-center">
                  <span className="mr-2">🔧</span>
                  Visual Workflow Builder
                </h2>
                <div className="flex items-center space-x-4">
                  {/* Workflow Selector */}
                  <select
                    value={activeWorkflow || ''}
                    onChange={(e) => setActiveWorkflow(e.target.value)}
                    className="bg-gray-700 text-white text-sm px-3 py-1 rounded"
                  >
                    <option value="">Select workflow...</option>
                    {workflows.map((workflow) => (
                      <option key={workflow.workflow_id} value={workflow.workflow_id}>
                        {workflow.name}
                      </option>
                    ))}
                  </select>
                  
                  <button
                    onClick={createNewWorkflow}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  >
                    + New Workflow
                  </button>
                  
                  <button
                    onClick={() => setIsVisible(false)}
                    className="text-gray-400 hover:text-white text-xl"
                  >
                    ×
                  </button>
                </div>
              </div>
            </div>

            <div className="flex h-full">
              {/* Node Palette */}
              <div className="w-64 bg-gray-800 p-4 border-r border-gray-600 overflow-y-auto">
                <h3 className="text-white font-medium mb-3">Node Palette</h3>
                
                {isConnecting && (
                  <div className="mb-4 p-3 bg-blue-900 border border-blue-600 rounded">
                    <div className="text-blue-200 text-sm">
                      🔗 Connection Mode Active
                    </div>
                    <div className="text-blue-300 text-xs mt-1">
                      Click another node to connect
                    </div>
                    <button
                      onClick={() => {
                        setIsConnecting(false);
                        setSourceNode(null);
                      }}
                      className="mt-2 text-xs text-blue-400 hover:text-blue-300"
                    >
                      Cancel
                    </button>
                  </div>
                )}

                <div className="space-y-2">
                  {getTemplateOptions().map((template) => (
                    <button
                      key={template.key}
                      onClick={() => addNodeToWorkflow(template.key)}
                      className="w-full text-left p-2 bg-gray-700 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                      disabled={!activeWorkflow}
                    >
                      {template.label}
                    </button>
                  ))}
                </div>

                {!activeWorkflow && (
                  <div className="mt-4 text-gray-400 text-sm">
                    Create or select a workflow to add nodes
                  </div>
                )}
              </div>

              {/* Canvas */}
              <div className="flex-1 relative bg-gray-900 overflow-hidden">
                {activeWorkflow ? (
                  <div className="relative w-full h-full">
                    {/* Grid Background */}
                    <div
                      className="absolute inset-0 opacity-20"
                      style={{
                        backgroundImage: `
                          linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
                        `,
                        backgroundSize: '20px 20px'
                      }}
                    />

                    {/* Nodes */}
                    {workflowNodes.map((node) => (
                      <WorkflowNode
                        key={node.node_id}
                        node={node}
                        onConnect={handleNodeConnect}
                        onDelete={deleteNode}
                        isConnecting={isConnecting}
                      />
                    ))}

                    {workflowNodes.length === 0 && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center text-gray-400">
                          <div className="text-4xl mb-4">🔧</div>
                          <div className="text-lg mb-2">Empty Workflow Canvas</div>
                          <div className="text-sm">Add nodes from the palette to get started</div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center text-gray-400">
                      <div className="text-6xl mb-4">🔧</div>
                      <div className="text-xl mb-2">Visual Workflow Builder</div>
                      <div className="text-sm mb-4">Create drag-and-drop automation workflows</div>
                      <button
                        onClick={createNewWorkflow}
                        className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        Create Your First Workflow
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default VisualWorkflowBuilder;