import React, { useState, useEffect, useCallback } from 'react';
import { useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { DndProvider } from 'react-dnd';
import DraggableItem from './DraggableItem';
import DropZone from './DropZone';
import SmartActions from './SmartActions';

const DragDropLayer = ({ children, onSmartAction, isEnabled = true }) => {
  const [dragState, setDragState] = useState({
    isDragging: false,
    draggedItem: null,
    dropZones: [],
    smartSuggestions: []
  });

  const [dropHistory, setDropHistory] = useState([]);

  // Smart drop zone detection based on content
  const detectDropZones = useCallback((item) => {
    const zones = [];

    if (item.type === 'text') {
      zones.push(
        { id: 'summarize', label: 'Summarize Text', icon: '📄', action: 'summarize' },
        { id: 'translate', label: 'Translate', icon: '🌐', action: 'translate' },
        { id: 'analyze', label: 'Analyze Content', icon: '🔍', action: 'analyze' }
      );
    }

    if (item.type === 'url' || item.type === 'link') {
      zones.push(
        { id: 'browse', label: 'Open in Browser', icon: '🌐', action: 'browse' },
        { id: 'extract', label: 'Extract Content', icon: '📃', action: 'extract' },
        { id: 'monitor', label: 'Monitor Changes', icon: '👁️', action: 'monitor' }
      );
    }

    if (item.type === 'image') {
      zones.push(
        { id: 'analyze-image', label: 'Analyze Image', icon: '🖼️', action: 'analyze_image' },
        { id: 'extract-text', label: 'Extract Text (OCR)', icon: '📝', action: 'ocr' },
        { id: 'describe', label: 'Describe Image', icon: '💬', action: 'describe_image' }
      );
    }

    if (item.type === 'file') {
      zones.push(
        { id: 'process', label: 'Process File', icon: '⚙️', action: 'process_file' },
        { id: 'convert', label: 'Convert Format', icon: '🔄', action: 'convert' },
        { id: 'upload', label: 'Upload & Share', icon: '☁️', action: 'upload' }
      );
    }

    // Always available zones
    zones.push(
      { id: 'chat', label: 'Ask AI About This', icon: '🤖', action: 'chat' },
      { id: 'save', label: 'Save to Collection', icon: '💾', action: 'save' },
      { id: 'workflow', label: 'Create Workflow', icon: '⚡', action: 'create_workflow' }
    );

    return zones;
  }, []);

  // Generate smart suggestions based on context and history
  const generateSmartSuggestions = useCallback((item) => {
    const suggestions = [];

    // Historical pattern analysis
    const similarDrops = dropHistory.filter(drop => 
      drop.itemType === item.type || drop.action === item.suggestedAction
    );

    if (similarDrops.length > 0) {
      const mostCommon = similarDrops.reduce((acc, drop) => {
        acc[drop.action] = (acc[drop.action] || 0) + 1;
        return acc;
      }, {});

      const topAction = Object.entries(mostCommon).sort(([,a], [,b]) => b - a)[0];
      if (topAction) {
        suggestions.push({
          type: 'historical',
          action: topAction[0],
          confidence: Math.min(0.9, topAction[1] / similarDrops.length),
          reason: `You've used this action ${topAction[1]} times before`
        });
      }
    }

    // Content-based suggestions
    if (item.type === 'text' && item.content) {
      const wordCount = item.content.split(' ').length;
      if (wordCount > 100) {
        suggestions.push({
          type: 'content',
          action: 'summarize',
          confidence: 0.8,
          reason: 'Long text detected - summarization recommended'
        });
      }

      // Language detection for translation
      if (/[^\x00-\x7F]/.test(item.content)) {
        suggestions.push({
          type: 'content',
          action: 'translate',
          confidence: 0.7,
          reason: 'Non-English characters detected'
        });
      }
    }

    if (item.type === 'url') {
      const url = item.content || item.url;
      if (url && url.includes('youtube.com')) {
        suggestions.push({
          type: 'context',
          action: 'extract_transcript',
          confidence: 0.9,
          reason: 'YouTube video detected'
        });
      }
      
      if (url && (url.includes('github.com') || url.includes('gitlab.com'))) {
        suggestions.push({
          type: 'context',
          action: 'analyze_code',
          confidence: 0.8,
          reason: 'Code repository detected'
        });
      }
    }

    return suggestions.sort((a, b) => b.confidence - a.confidence).slice(0, 3);
  }, [dropHistory]);

  const handleDragStart = useCallback((item) => {
    const zones = detectDropZones(item);
    const suggestions = generateSmartSuggestions(item);

    setDragState({
      isDragging: true,
      draggedItem: item,
      dropZones: zones,
      smartSuggestions: suggestions
    });
  }, [detectDropZones, generateSmartSuggestions]);

  const handleDragEnd = useCallback(() => {
    setDragState({
      isDragging: false,
      draggedItem: null,
      dropZones: [],
      smartSuggestions: []
    });
  }, []);

  const handleDrop = useCallback(async (item, dropZone) => {
    try {
      // Record drop in history
      const dropRecord = {
        id: Date.now(),
        itemType: item.type,
        action: dropZone.action,
        timestamp: new Date().toISOString(),
        success: true
      };

      setDropHistory(prev => [...prev.slice(-19), dropRecord]);

      // Execute the action
      if (onSmartAction) {
        await onSmartAction({
          action: dropZone.action,
          item: item,
          dropZone: dropZone
        });
      }

      // Show success feedback
      showDropFeedback(`${item.type} ${dropZone.action}ed successfully!`, 'success');

    } catch (error) {
      console.error('Drop action failed:', error);
      showDropFeedback(`Failed to ${dropZone.action} ${item.type}`, 'error');
      
      // Update history with failure
      setDropHistory(prev => [
        ...prev.slice(-19),
        {
          id: Date.now(),
          itemType: item.type,
          action: dropZone.action,
          timestamp: new Date().toISOString(),
          success: false,
          error: error.message
        }
      ]);
    }
  }, [onSmartAction]);

  const showDropFeedback = (message, type) => {
    // Create temporary notification
    const notification = document.createElement('div');
    notification.className = `
      fixed top-4 right-4 px-4 py-2 rounded-lg z-50 text-white
      ${type === 'success' ? 'bg-green-500' : 'bg-red-500'}
      transform transition-transform duration-300 ease-out
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
      notification.style.transform = 'translateY(0)';
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
      notification.style.transform = 'translateY(-100%)';
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  };

  if (!isEnabled) {
    return <>{children}</>;
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="relative w-full h-full">
        {children}
        
        {/* Drag overlay with drop zones */}
        {dragState.isDragging && (
          <DragOverlay
            draggedItem={dragState.draggedItem}
            dropZones={dragState.dropZones}
            smartSuggestions={dragState.smartSuggestions}
            onDrop={handleDrop}
          />
        )}

        {/* Smart Actions Panel */}
        <SmartActions
          suggestions={dragState.smartSuggestions}
          isVisible={dragState.isDragging}
          onActionClick={(suggestion) => {
            handleDrop(dragState.draggedItem, {
              action: suggestion.action,
              label: suggestion.action,
              icon: '⚡'
            });
          }}
        />
      </div>
    </DndProvider>
  );
};

const DragOverlay = ({ draggedItem, dropZones, smartSuggestions, onDrop }) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };

    document.addEventListener('mousemove', handleMouseMove);
    return () => document.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <>
      {/* Semi-transparent overlay */}
      <div className="fixed inset-0 bg-black bg-opacity-20 z-40 pointer-events-none" />
      
      {/* Drop zones */}
      <div className="fixed inset-0 z-50 pointer-events-none">
        <div className="relative w-full h-full">
          {dropZones.map((zone, index) => (
            <DropZone
              key={zone.id}
              zone={zone}
              index={index}
              totalZones={dropZones.length}
              draggedItem={draggedItem}
              onDrop={onDrop}
            />
          ))}
        </div>
      </div>

      {/* Dragged item preview */}
      <div
        className="fixed z-50 pointer-events-none transform -translate-x-1/2 -translate-y-1/2"
        style={{ left: position.x, top: position.y }}
      >
        <div className="bg-white border-2 border-blue-300 rounded-lg p-2 shadow-lg max-w-xs">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getItemIcon(draggedItem.type)}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {draggedItem.title || draggedItem.content || 'Dragged Item'}
              </p>
              <p className="text-xs text-gray-500 capitalize">
                {draggedItem.type}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const getItemIcon = (type) => {
  switch (type) {
    case 'text': return '📝';
    case 'url': case 'link': return '🔗';
    case 'image': return '🖼️';
    case 'file': return '📁';
    default: return '📄';
  }
};

// Hook for making elements draggable
export const useDraggable = (item, onDragStart, onDragEnd) => {
  const [{ isDragging }, drag] = useDrop(() => ({
    type: 'DRAGGABLE_ITEM',
    item: () => {
      if (onDragStart) onDragStart(item);
      return item;
    },
    end: () => {
      if (onDragEnd) onDragEnd();
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging()
    })
  }), [item]);

  return { isDragging, drag };
};

// Enhanced text selection handler
export const useTextSelection = (onTextSelected) => {
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const selectedText = selection.toString().trim();
      
      if (selectedText.length > 0) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        // Create draggable item from selection
        const textItem = {
          type: 'text',
          content: selectedText,
          title: selectedText.substring(0, 50) + (selectedText.length > 50 ? '...' : ''),
          source: 'selection',
          position: { x: rect.x, y: rect.y }
        };
        
        if (onTextSelected) {
          onTextSelected(textItem);
        }
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => document.removeEventListener('mouseup', handleSelection);
  }, [onTextSelected]);
};

export default DragDropLayer;