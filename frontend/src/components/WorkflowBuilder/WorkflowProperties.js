import React from 'react';

const WorkflowProperties = ({ 
  selectedNode, 
  workflowData, 
  onNodeUpdate, 
  onNodeDelete, 
  onWorkflowUpdate, 
  onClose 
}) => {
  const handleNodeChange = (field, value) => {
    if (selectedNode && onNodeUpdate) {
      onNodeUpdate(selectedNode.id, { [field]: value });
    }
  };

  const handleConfigChange = (configField, value) => {
    if (selectedNode && onNodeUpdate) {
      const newConfig = { ...selectedNode.data.config, [configField]: value };
      onNodeUpdate(selectedNode.id, { config: newConfig });
    }
  };

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold">Properties</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {selectedNode ? (
          <>
            {/* Node Properties */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Node Settings</h4>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    value={selectedNode.data.label}
                    onChange={(e) => handleNodeChange('label', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={selectedNode.data.description || ''}
                    onChange={(e) => handleNodeChange('description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm h-20"
                  />
                </div>
              </div>
            </div>

            {/* Node Configuration */}
            {selectedNode.data.config && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Configuration</h4>
                <NodeConfigForm 
                  config={selectedNode.data.config}
                  stepType={selectedNode.data.stepType}
                  onChange={handleConfigChange}
                />
              </div>
            )}

            {/* Delete Button */}
            <div className="pt-4 border-t border-gray-200">
              <button
                onClick={() => onNodeDelete(selectedNode.id)}
                className="w-full px-4 py-2 bg-red-100 text-red-700 rounded-md text-sm hover:bg-red-200"
              >
                Delete Node
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Workflow Properties */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Workflow Settings</h4>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name
                  </label>
                  <input
                    type="text"
                    value={workflowData.name}
                    onChange={(e) => onWorkflowUpdate({ ...workflowData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={workflowData.description}
                    onChange={(e) => onWorkflowUpdate({ ...workflowData, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm h-20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Category
                  </label>
                  <select
                    value={workflowData.category}
                    onChange={(e) => onWorkflowUpdate({ ...workflowData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="Custom">Custom</option>
                    <option value="Automation">Automation</option>
                    <option value="Integration">Integration</option>
                    <option value="Analytics">Analytics</option>
                  </select>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

const NodeConfigForm = ({ config, stepType, onChange }) => {
  const renderConfigField = (key, value) => {
    if (typeof value === 'boolean') {
      return (
        <div key={key} className="mb-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => onChange(key, e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm font-medium text-gray-700 capitalize">
              {key.replace(/_/g, ' ')}
            </span>
          </label>
        </div>
      );
    }

    return (
      <div key={key} className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
          {key.replace(/_/g, ' ')}
        </label>
        <input
          type="text"
          value={value || ''}
          onChange={(e) => onChange(key, e.target.value)}
          className="w-full px-3 py-1 border border-gray-300 rounded text-sm"
        />
      </div>
    );
  };

  return (
    <div className="space-y-2">
      {Object.entries(config).map(([key, value]) => renderConfigField(key, value))}
    </div>
  );
};

export default WorkflowProperties;