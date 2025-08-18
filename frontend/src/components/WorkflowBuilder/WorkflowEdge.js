import React from 'react';
import { getSmoothStepPath, EdgeLabelRenderer, useReactFlow } from 'reactflow';

const WorkflowEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data = {}
}) => {
  const { setEdges } = useReactFlow();
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const onEdgeClick = () => {
    setEdges((edges) => edges.filter((edge) => edge.id !== id));
  };

  return (
    <>
      <path
        id={id}
        style={{ stroke: '#3b82f6', strokeWidth: 2 }}
        className="react-flow__edge-path"
        d={edgePath}
      />
      <EdgeLabelRenderer>
        {data.label && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            }}
            className="nodrag nopan bg-white px-2 py-1 rounded border text-xs"
          >
            {data.label}
          </div>
        )}
      </EdgeLabelRenderer>
    </>
  );
};

export default WorkflowEdge;