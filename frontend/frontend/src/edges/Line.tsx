import { BaseEdge, getBezierPath, type EdgeProps } from "reactflow";
import { type NodeParameters } from "../nodes/nodeStatus";

export type LineEdgeData = {
  lineName: string;
  characteristic: string;
  isActive?: boolean;
  highlighted?: boolean;
  dimmed?: boolean;
  parameters?: NodeParameters;
};

const getLineStyle = (edgeData?: LineEdgeData, isActive?: boolean) => {
  const category = String(edgeData?.parameters?.category ?? "");

  if (category === "TransmissionLine" || category === "Transmission") {
    return {
      strokeWidth: 6,
      strokeDasharray: undefined
    };
  }

  if (category === "SubTransmissionLine" || category === "Sub-Transmission") {
    return {
      strokeWidth: 4.8,
      strokeDasharray: isActive ? "14 7" : "10 8"
    };
  }

  if (category === "Feeder11kV" || category === "Primary Distribution") {
    return {
      strokeWidth: 3.8,
      strokeDasharray: isActive ? "10 8" : "8 7"
    };
  }

  if (category === "SecondaryDistributionLine" || category === "Secondary Distribution") {
    return {
      strokeWidth: 2.8,
      strokeDasharray: isActive ? "7 7" : "6 7"
    };
  }

  return {
    strokeWidth: 2.2,
    strokeDasharray: isActive ? "6 8" : "5 8"
  };
};

const Line = ({
  id,
  data,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition
}: EdgeProps<LineEdgeData>) => {
  const isActive = data?.isActive ?? data?.parameters?.active === "On";
  const isHighlighted = data?.highlighted ?? false;
  const isDimmed = data?.dimmed ?? false;
  const lineStyle = getLineStyle(data, isActive);
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
          stroke: isHighlighted ? "#ffffff" : isActive ? "#1fb6ff" : "#ff4d4f",
          strokeWidth: isHighlighted ? lineStyle.strokeWidth + 1.6 : lineStyle.strokeWidth,
          strokeDasharray: isHighlighted ? undefined : lineStyle.strokeDasharray,
          opacity: isDimmed ? 0.15 : 1,
          animation:
            isHighlighted || isDimmed ? undefined : isActive ? "unified-line-flow 0.9s linear infinite" : undefined,
          filter: isDimmed
            ? "none"
            : isHighlighted
              ? "drop-shadow(0 0 8px rgba(255, 255, 255, 0.95))"
              : isActive
                ? "drop-shadow(0 0 4px rgba(31, 182, 255, 0.9))"
                : "drop-shadow(0 0 4px rgba(255, 77, 79, 0.75))"
        }}
      />
      <path id={motionPathId} d={path} fill="none" stroke="transparent" />
      {isActive && !isDimmed && !isHighlighted && (
        <g className="unified-moving-arrow">
          <path d="M0,-7 L11,0 L0,7 Z" />
          <animateMotion dur="1.4s" repeatCount="indefinite" rotate="auto">
            <mpath href={`#${motionPathId}`} />
          </animateMotion>
        </g>
      )}
    </>
  );
};

export default Line;
