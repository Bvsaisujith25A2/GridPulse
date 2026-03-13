import { Handle, Position, type NodeProps } from "reactflow";
import transformerIcon from "../icons/transformer.svg";
import { getNodeStatusClass, type GridNodeData } from "./nodeStatus";

const TransformerNode = ({ data }: NodeProps<GridNodeData>) => {
  const statusClass = getNodeStatusClass(data?.status);

  return (
    <div style={{ position: "relative", display: "inline-flex" }}>
      <Handle type="target" position={Position.Left} />
      <img
        src={transformerIcon}
        alt="Transformer"
        className={statusClass}
        style={{ width: "88px", height: "88px" }}
      />
      {data?.showLabel && <div className="grid-node-label">{data?.label ?? "Transformer"}</div>}
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

export default TransformerNode;
