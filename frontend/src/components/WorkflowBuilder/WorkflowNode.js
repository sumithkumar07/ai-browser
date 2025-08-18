import React from 'react';
import { Handle, Position } from 'reactflow';

const WorkflowNode = ({ id, data, selected }) => {
  const getNodeStyle = (stepType) => {
    switch (stepType) {
      case 'trigger':
        return 'bg-green-100 border-green-300 text-green-800';
      case 'condition':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800';
      case 'integration':
        return 'bg-purple-100 border-purple-300 text-purple-800';
      default:
        return 'bg-blue-100 border-blue-300 text-blue-800';
    }
  };

  const getIcon = (stepType) => {
    switch (stepType) {
      case 'trigger': return '⚡';
      case 'condition': return '❓';
      case 'integration': return '🔌';
      default: return '⚙️';
    }
  };

  return (
    <div
      className={`
        px-4 py-2 shadow-md rounded-md border-2 min-w-[150px]
        ${getNodeStyle(data.stepType)}
        ${selected ? 'ring-2 ring-blue-500' : ''}
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3"
      />
      
      <div className="flex items-center space-x-2">
        <span className="text-lg">{getIcon(data.stepType)}</span>
        <div className="flex-1">
          <div className="font-bold text-sm">{data.label}</div>
          {data.description && (
            <div className="text-xs opacity-75">{data.description}</div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3"
      />
    </div>
  );
};

export default WorkflowNode;