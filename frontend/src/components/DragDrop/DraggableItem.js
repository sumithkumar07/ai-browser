import React from 'react';
import { useDrag } from 'react-dnd';

const DraggableItem = ({ item, children, onDragStart, onDragEnd }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
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

  return (
    <div 
      ref={drag}
      className={`
        cursor-move transition-opacity
        ${isDragging ? 'opacity-50' : 'opacity-100'}
      `}
    >
      {children}
    </div>
  );
};

export default DraggableItem;