export type NodeStatus = "red" | "yellow" | "green";

export type NodeParameterValue = string | number;

export type NodeParameters = Record<string, NodeParameterValue>;

export type GridNodeData = {
  label?: string;
  status?: NodeStatus;
  parameters?: NodeParameters;
};

export const getNodeStatusClass = (status?: NodeStatus) => {
  switch (status) {
    case "green":
      return "node-status-green";
    case "yellow":
      return "node-status-yellow";
    case "red":
    default:
      return "node-status-red";
  }
};
