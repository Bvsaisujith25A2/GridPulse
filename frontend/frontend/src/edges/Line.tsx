import { BaseEdge, getBezierPath, type EdgeProps } from "reactflow";
import { type NodeParameters } from "../nodes/nodeStatus";

export type LineEdgeData = {
  lineName: string;
  characteristic: string;
  parameters?: NodeParameters;
};

const Line = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition
}: EdgeProps<LineEdgeData>) => {
  const [path] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition
  });
  const motionPathId = `unified-line-motion-${id}`;

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        style={{
          stroke: "#1fb6ff",
          strokeWidth: 3,
          strokeDasharray: "10 8",
          animation: "unified-line-flow 0.9s linear infinite",
          filter: "drop-shadow(0 0 4px rgba(31, 182, 255, 0.9))"
        }}
      />
      <path id={motionPathId} d={path} fill="none" stroke="transparent" />
      <g className="unified-moving-arrow">
        <path d="M0,-7 L11,0 L0,7 Z" />
        <animateMotion dur="1.4s" repeatCount="indefinite" rotate="auto">
          <mpath href={`#${motionPathId}`} />
        </animateMotion>
      </g>
    </>
  );
};

export default Line;
