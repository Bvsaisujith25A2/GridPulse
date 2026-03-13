import { Handle, Position, type NodeProps } from "reactflow";
import houseIcon from "../icons/house.svg";
import { getNodeStatusClass, type GridNodeData } from "./nodeStatus";

const HouseNode = ({ data }: NodeProps<GridNodeData>) => {
  const statusClass = getNodeStatusClass(data?.status);

  return (
    <div style={{ position: "relative", display: "inline-flex" }}>
      <Handle type="target" position={Position.Left} />
      <img
        src={houseIcon}
        alt="House"
        className={statusClass}
        style={{
          width: "88px",
          height: "88px"
        }}
      />
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default HouseNode;