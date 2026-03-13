import { Handle, Position, type NodeProps } from "reactflow";
import gridSubstationIcon from "../icons/gridsubstation.svg";
import { getNodeStatusClass, type GridNodeData } from "./nodeStatus";

const GridSubstationNode = ({ data }: NodeProps<GridNodeData>) => {
  const statusClass = getNodeStatusClass(data?.status);

  return (
    <div style={{ position: "relative", display: "inline-flex" }}>
      <Handle type="target" position={Position.Left} />
      <img
        src={gridSubstationIcon}
        alt="Grid Substation"
        className={statusClass}
        style={{ width: "88px", height: "88px" }}
      />
      {data?.showLabel && <div className="grid-node-label">{data?.label ?? "Grid Substation"}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default GridSubstationNode;