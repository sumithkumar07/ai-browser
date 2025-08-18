import React from 'react';

const NodePalette = () => {
  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const nodeTypes = [
    {
      type: 'trigger',
      label: 'Trigger',
      icon: '⚡',
      description: 'Start workflow',
      color: 'bg-green-100 text-green-800'
    },
    {
      type: 'action',
      label: 'Action',
      icon: '⚙️',
      description: 'Execute task',
      color: 'bg-blue-100 text-blue-800'
    },
    {
      type: 'condition',
      label: 'Condition',
      icon: '❓',
      description: 'Check condition',
      color: 'bg-yellow-100 text-yellow-800'
    },
    {
      type: 'integration',
      label: 'Integration',
      icon: '🔌',
      description: 'External service',
      color: 'bg-purple-100 text-purple-800'
    }
  ];

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Node Palette</h3>
      
      <div className="space-y-2">
        {nodeTypes.map((node) => (
          <div
            key={node.type}
            className={`
              flex items-center space-x-3 p-3 rounded-lg border cursor-move
              hover:shadow-md transition-shadow ${node.color}
            `}
            draggable
            onDragStart={(event) => onDragStart(event, node.type)}
          >
            <span className="text-lg">{node.icon}</span>
            <div className="flex-1">
              <div className="font-medium text-sm">{node.label}</div>
              <div className="text-xs opacity-75">{node.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NodePalette;