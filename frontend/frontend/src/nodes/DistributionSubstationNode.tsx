import { Handle, Position, type NodeProps } from "reactflow";
import distributionSubstationIcon from "../icons/distributionsubstation.svg";
import { getNodeStatusClass, type GridNodeData } from "./nodeStatus";

const DistributionSubstationNode = ({ data }: NodeProps<GridNodeData>) => {
  const statusClass = getNodeStatusClass(data?.status);

  return (
    <div style={{ position: "relative", display: "inline-flex" }}>
      <Handle type="target" position={Position.Left} />
      <img
        src={distributionSubstationIcon}
        alt="Distribution Substation"
        className={statusClass}
        style={{ width: "88px", height: "88px" }}
      />
      {data?.showLabel && <div className="grid-node-label">{data?.label ?? "Distribution Substation"}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default DistributionSubstationNode;