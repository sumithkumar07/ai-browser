import React, { useState } from 'react';
import { useDrop } from 'react-dnd';

const DropZone = ({ zone, index, totalZones, draggedItem, onDrop }) => {
  const [isHovered, setIsHovered] = useState(false);

  const [{ isOver, canDrop }, drop] = useDrop(() => ({
    accept: 'DRAGGABLE_ITEM',
    drop: (item) => {
      if (onDrop) {
        onDrop(item, zone);
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
      canDrop: monitor.canDrop()
    })
  }), [zone, onDrop]);

  // Calculate position around the screen edges
  const getZonePosition = () => {
    const padding = 20;
    const zoneSize = 120;
    const screenWidth = window.innerWidth;
    const screenHeight = window.innerHeight;

    // Distribute zones around the screen edges
    if (totalZones <= 4) {
      // Corner positions
      const positions = [
        { top: padding, right: padding }, // Top right
        { top: padding, left: padding }, // Top left
        { bottom: padding, right: padding }, // Bottom right
        { bottom: padding, left: padding } // Bottom left
      ];
      return positions[index % 4];
    } else {
      // Distribute around edges
      const perEdge = Math.ceil(totalZones / 4);
      const edgeIndex = Math.floor(index / perEdge);
      const positionInEdge = index % perEdge;

      switch (edgeIndex) {
        case 0: // Top edge
          return {
            top: padding,
            left: padding + (positionInEdge * (screenWidth - 2 * padding - zoneSize) / (perEdge - 1))
          };
        case 1: // Right edge
          return {
            right: padding,
            top: padding + (positionInEdge * (screenHeight - 2 * padding - zoneSize) / (perEdge - 1))
          };
        case 2: // Bottom edge
          return {
            bottom: padding,
            right: padding + (positionInEdge * (screenWidth - 2 * padding - zoneSize) / (perEdge - 1))
          };
        case 3: // Left edge
        default:
          return {
            left: padding,
            bottom: padding + (positionInEdge * (screenHeight - 2 * padding - zoneSize) / (perEdge - 1))
          };
      }
    }
  };

  const position = getZonePosition();
  const isActive = isOver && canDrop;
  const isRelevant = isZoneRelevant(draggedItem, zone);

  return (
    <div
      ref={drop}
      className={`
        absolute w-32 h-20 rounded-lg border-2 border-dashed transition-all duration-200
        flex flex-col items-center justify-center text-center p-2 cursor-pointer
        ${isActive 
          ? 'border-blue-500 bg-blue-100 scale-110 shadow-lg' 
          : isRelevant 
            ? 'border-green-400 bg-green-50 hover:bg-green-100' 
            : 'border-gray-400 bg-gray-50 hover:bg-gray-100'
        }
        ${isRelevant ? 'opacity-100' : 'opacity-75'}
      `}
      style={position}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`text-2xl mb-1 ${isActive ? 'animate-bounce' : ''}`}>
        {zone.icon}
      </div>
      <div className={`text-xs font-medium ${isActive ? 'text-blue-700' : 'text-gray-700'}`}>
        {zone.label}
      </div>
      
      {/* Relevance indicator */}
      {isRelevant && !isActive && (
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
      )}
      
      {/* Hover tooltip */}
      {isHovered && (
        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 
                        bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
          {getActionDescription(zone, draggedItem)}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 
                          w-0 h-0 border-l-2 border-r-2 border-t-2 
                          border-l-transparent border-r-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  );
};

const isZoneRelevant = (draggedItem, zone) => {
  if (!draggedItem) return false;

  const relevanceMap = {
    text: ['summarize', 'translate', 'analyze', 'chat'],
    url: ['browse', 'extract', 'monitor', 'chat'],
    link: ['browse', 'extract', 'monitor', 'chat'],
    image: ['analyze_image', 'ocr', 'describe_image', 'chat'],
    file: ['process_file', 'convert', 'upload', 'chat']
  };

  const relevantActions = relevanceMap[draggedItem.type] || ['chat', 'save'];
  return relevantActions.includes(zone.action);
};

const getActionDescription = (zone, draggedItem) => {
  const descriptions = {
    summarize: `Summarize this ${draggedItem?.type}`,
    translate: `Translate this ${draggedItem?.type}`,
    analyze: `Analyze this ${draggedItem?.type} with AI`,
    browse: `Open ${draggedItem?.type} in browser`,
    extract: `Extract content from ${draggedItem?.type}`,
    monitor: `Monitor ${draggedItem?.type} for changes`,
    analyze_image: `Analyze image with AI vision`,
    ocr: `Extract text from image`,
    describe_image: `Get AI description of image`,
    process_file: `Process file with automation`,
    convert: `Convert file to different format`,
    upload: `Upload file to cloud storage`,
    chat: `Ask AI about this ${draggedItem?.type}`,
    save: `Save ${draggedItem?.type} to collection`,
    create_workflow: `Create workflow from ${draggedItem?.type}`
  };

  return descriptions[zone.action] || `Perform ${zone.action} on ${draggedItem?.type}`;
};

export default DropZone;