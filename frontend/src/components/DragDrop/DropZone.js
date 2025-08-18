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

  // Position the drop zone around the screen edges
  const getZonePosition = () => {
    const padding = 20;
    const zoneSize = 120;
    const spacing = (window.innerWidth - 2 * padding) / Math.max(totalZones, 1);
    
    return {
      left: padding + (index * spacing) - (zoneSize / 2),
      bottom: padding,
      width: zoneSize,
      height: zoneSize
    };
  };

  const position = getZonePosition();

  return (
    <div
      ref={drop}
      className={`
        absolute pointer-events-auto flex flex-col items-center justify-center
        border-2 border-dashed rounded-lg transition-all duration-200
        ${isOver && canDrop 
          ? 'border-blue-500 bg-blue-100 scale-110 shadow-lg' 
          : 'border-gray-300 bg-white bg-opacity-90 hover:border-blue-400 hover:bg-blue-50'
        }
      `}
      style={position}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span className="text-2xl mb-1">{zone.icon}</span>
      <span className="text-xs font-medium text-center px-2">
        {zone.label}
      </span>
      
      {(isHovered || isOver) && (
        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs px-2 py-1 rounded whitespace-nowrap">
          Drop to {zone.label.toLowerCase()}
        </div>
      )}
    </div>
  );
};

export default DropZone;