import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';

const WorkflowNode = ({ id, data, isConnectable, selected }) => {
  const getNodeStyle = () => {
    const baseStyle = "px-4 py-2 shadow-md rounded-lg border-2 min-w-[160px] text-center";
    
    switch (data.stepType) {
      case 'trigger':
        return `${baseStyle} bg-green-50 border-green-200 ${selected ? 'ring-2 ring-green-400' : ''}`;
      case 'condition':
        return `${baseStyle} bg-yellow-50 border-yellow-200 ${selected ? 'ring-2 ring-yellow-400' : ''}`;
      case 'integration':
        return `${baseStyle} bg-purple-50 border-purple-200 ${selected ? 'ring-2 ring-purple-400' : ''}`;
      default:
        return `${baseStyle} bg-blue-50 border-blue-200 ${selected ? 'ring-2 ring-blue-400' : ''}`;
    }
  };

  const getNodeIcon = () => {
    switch (data.stepType) {
      case 'trigger':
        return '🚀';
      case 'condition':
        return '🤔';
      case 'integration':
        return '🔗';
      case 'action':
      default:
        return '⚙️';
    }
  };

  const getHandleStyle = () => {
    switch (data.stepType) {
      case 'trigger':
        return { background: '#10b981' };
      case 'condition':
        return { background: '#f59e0b' };
      case 'integration':
        return { background: '#8b5cf6' };
      default:
        return { background: '#3b82f6' };
    }
  };

  return (
    <div className={getNodeStyle()}>
      {/* Input Handle */}
      {data.stepType !== 'trigger' && (
        <Handle
          type="target"
          position={Position.Top}
          style={getHandleStyle()}
          isConnectable={isConnectable}
        />
      )}

      {/* Node Content */}
      <div className="flex flex-col items-center">
        <div className="text-lg mb-1">{getNodeIcon()}</div>
        <div className="font-medium text-sm text-gray-900">{data.label}</div>
        {data.description && (
          <div className="text-xs text-gray-500 mt-1 text-center">{data.description}</div>
        )}
        
        {/* Node Status Indicator */}
        {data.status && (
          <div className={`mt-2 px-2 py-0.5 rounded-full text-xs ${
            data.status === 'completed' ? 'bg-green-100 text-green-700' :
            data.status === 'error' ? 'bg-red-100 text-red-700' :
            data.status === 'running' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {data.status}
          </div>
        )}

        {/* Config Summary */}
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="mt-2 text-xs text-gray-400">
            {getConfigSummary(data.stepType, data.config)}
          </div>
        )}
      </div>

      {/* Output Handles */}
      {data.stepType === 'condition' ? (
        <>
          <Handle
            type="source"
            position={Position.Bottom}
            id="true"
            style={{ left: 10, background: '#10b981' }}
            isConnectable={isConnectable}
          />
          <Handle
            type="source"
            position={Position.Bottom}
            id="false"
            style={{ right: 10, left: 'auto', background: '#ef4444' }}
            isConnectable={isConnectable}
          />
        </>
      ) : (
        <Handle
          type="source"
          position={Position.Bottom}
          style={getHandleStyle()}
          isConnectable={isConnectable}
        />
      )}
    </div>
  );
};

const getConfigSummary = (stepType, config) => {
  switch (stepType) {
    case 'trigger':
      return config.trigger_type === 'schedule' 
        ? `Schedule: ${config.schedule}` 
        : config.trigger_type;
    
    case 'condition':
      return `${config.left_value} ${config.operator} ${config.right_value}`;
    
    case 'integration':
      return config.integration_id ? `${config.integration_id}` : 'Not configured';
    
    case 'action':
      return config.action_type === 'http_request'
        ? `${config.method || 'GET'} ${config.url || 'URL not set'}`
        : config.action_type;
    
    default:
      return 'Configured';
  }
};

export default memo(WorkflowNode);