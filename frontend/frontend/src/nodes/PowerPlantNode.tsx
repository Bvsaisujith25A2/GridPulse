import { Handle, Position, type NodeProps } from "reactflow";
import powerPlantIcon from "../icons/powerplant.svg";
import { getNodeStatusClass, type GridNodeData } from "./nodeStatus";

const PowerPlantNode = ({ data }: NodeProps<GridNodeData>) => {
  const statusClass = getNodeStatusClass(data?.status);

  return (
    <div style={{ position: "relative", display: "inline-flex" }}>
      <Handle type="target" position={Position.Left} />
      <img
        src={powerPlantIcon}
        alt="Power Plant"
        className={statusClass}
        style={{ width: "88px", height: "88px" }}
      />
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default PowerPlantNode;