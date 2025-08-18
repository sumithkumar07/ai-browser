import React from 'react';

const SmartActions = ({ suggestions, isVisible, onActionClick }) => {
  if (!isVisible || !suggestions || suggestions.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 left-4 z-50 bg-white rounded-lg shadow-lg border border-gray-200 p-3 max-w-sm">
      <h3 className="text-sm font-semibold text-gray-800 mb-2">
        💡 Smart Suggestions
      </h3>
      
      <div className="space-y-2">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onActionClick(suggestion)}
            className={`
              w-full text-left p-2 rounded text-sm transition-colors
              ${suggestion.confidence > 0.8 
                ? 'bg-green-50 hover:bg-green-100 border border-green-200' 
                : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
              }
            `}
          >
            <div className="flex items-center justify-between">
              <span className="font-medium capitalize">
                {suggestion.action.replace(/_/g, ' ')}
              </span>
              <span className={`
                text-xs px-2 py-1 rounded-full
                ${suggestion.confidence > 0.8 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
                }
              `}>
                {Math.round(suggestion.confidence * 100)}%
              </span>
            </div>
            
            <p className="text-xs text-gray-600 mt-1">
              {suggestion.reason}
            </p>
          </button>
        ))}
      </div>
      
      <div className="mt-3 pt-2 border-t border-gray-100 text-xs text-gray-500">
        Based on your usage patterns and content analysis
      </div>
    </div>
  );
};

export default SmartActions;