import { type MouseEvent as ReactMouseEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  addEdge,
  type Connection,
  type Edge,
  type EdgeTypes,
  type Node,
  useEdgesState,
  useNodesState
} from "reactflow";
import "reactflow/dist/style.css";
import PowerPlantNode from "./nodes/PowerPlantNode";
import GridSubstationNode from "./nodes/GridSubstationNode";
import DistributionSubstationNode from "./nodes/DistributionSubstationNode";
import TransformerNode from "./nodes/TransformerNode";
import HouseNode from "./nodes/HouseNode";
import { type GridNodeData, type NodeStatus } from "./nodes/nodeStatus";
import Line, { type LineEdgeData } from "./edges/Line";

const nodeTypes = {
  powerPlant: PowerPlantNode,
  gridSubstation: GridSubstationNode,
  distributionSubstation: DistributionSubstationNode,
  transformer: TransformerNode,
  house: HouseNode,
  industry: HouseNode
};

const edgeTypes: EdgeTypes = {
  unifiedLine: Line
};

const lineRelationMap: Record<string, LineEdgeData> = {
  "powerPlant->gridSubstation": {
    lineName: "Transmission Lines",
    characteristic: "Extra High Voltage Bulk Transfer",
    parameters: {
      category: "Transmission",
      input: "Power Plant Output",
      output: "Grid Substation Input",
      voltage: "400 / 220 kV"
    }
  },
  "gridSubstation->distributionSubstation": {
    lineName: "Sub-Transmission Lines (132 / 66 / 33 kV)",
    characteristic: "Step-Down Sub-Transmission Corridor",
    parameters: {
      category: "Sub-Transmission",
      input: "Grid Substation",
      output: "Distribution Substation",
      voltage: "132 / 66 / 33 kV"
    }
  },
  "distributionSubstation->transformer": {
    lineName: "11 kV Feeders",
    characteristic: "Primary Distribution Feeders",
    parameters: {
      category: "Primary Distribution",
      input: "Distribution Substation",
      output: "Distribution Transformer",
      voltage: "11 kV"
    }
  },
  "transformer->house": {
    lineName: "Secondary Distribution Lines",
    characteristic: "Low Voltage Consumer Delivery",
    parameters: {
      category: "Secondary Distribution",
      input: "Transformer LT Side",
      output: "Houses / Industries",
      voltage: "415 / 230 V"
    }
  },
  "transformer->industry": {
    lineName: "Secondary Distribution Lines",
    characteristic: "Low Voltage Industrial Delivery",
    parameters: {
      category: "Secondary Distribution",
      input: "Transformer LT Side",
      output: "Industries",
      voltage: "415 / 230 V"
    }
  }
};

const getLineRelation = (sourceType?: string, targetType?: string) => {
  if (!sourceType || !targetType) {
    return null;
  }

  return lineRelationMap[`${sourceType}->${targetType}`] ?? null;
};

const formatParameterKey = (key: string) => {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/^./, (char) => char.toUpperCase());
};

const getOrderedParameters = (parameters?: GridNodeData["parameters"]) => {
  if (!parameters) {
    return [] as [string, string | number][];
  }

  const commonOrder = ["category", "input", "output"];
  const entries = Object.entries(parameters);
  const orderedCommon = commonOrder
    .filter((key) => key in parameters)
    .map((key) => [key, parameters[key]] as [string, string | number]);
  const remaining = entries.filter(([key]) => !commonOrder.includes(key));

  return [...orderedCommon, ...remaining];
};

type BackendNode = {
  id: string;
  label: string;
  type: string;
  position: { x: number; y: number };
};

type BackendEdge = {
  id: string;
  source: string;
  target: string;
  data?: LineEdgeData;
};

type StreamEdgeUpdate = {
  lineName?: string;
  characteristic?: string;
  isActive?: boolean;
  parameters?: GridNodeData["parameters"];
};

const toReactFlowNodeType = (value: string): Node["type"] => {
  if (value in nodeTypes) {
    return value as Node["type"];
  }
  return "house";
};

const toReactFlowNodes = (backendNodes: BackendNode[]): Node<GridNodeData>[] => {
  return backendNodes.map((node) => ({
    id: node.id,
    type: toReactFlowNodeType(node.type),
    position: node.position,
    data: {
      label: node.label,
      status: "red",
      parameters: {
        category: "Loading",
        input: "--",
        output: "--"
      }
    }
  }));
};

const toReactFlowEdges = (
  backendEdges: BackendEdge[],
  reactNodes: Node<GridNodeData>[]
): Edge<LineEdgeData>[] => {
  return backendEdges.map((edge) => {
    const sourceNode = reactNodes.find((node) => node.id === edge.source);
    const targetNode = reactNodes.find((node) => node.id === edge.target);
    const fallback = getLineRelation(sourceNode?.type, targetNode?.type) ?? {
      lineName: "Grid Line",
      characteristic: "Power Transfer",
      parameters: {
        category: "Grid",
        input: sourceNode?.data?.label ?? "Source",
        output: targetNode?.data?.label ?? "Target"
      }
    };

    return {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "unifiedLine",
      data: edge.data ?? fallback,
      animated: edge.data?.isActive ?? true
    };
  });
};

function App() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<LineEdgeData>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [panelPosition, setPanelPosition] = useState({ x: 16, y: 16 });
  const [pendingNodeId, setPendingNodeId] = useState<string | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);
  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) {
      return null;
    }

    return nodes.find((node) => node.id === selectedNodeId) ?? null;
  }, [nodes, selectedNodeId]);

  const updatePanelPosition = (event: ReactMouseEvent<Element, MouseEvent>) => {
    const containerRect = containerRef.current?.getBoundingClientRect();

    if (!containerRect) {
      return;
    }

    const nextX = event.clientX - containerRect.left + 14;
    const nextY = event.clientY - containerRect.top - 10;

    setPanelPosition({ x: nextX, y: nextY });
  };

  const applyBackendPayload = (payload: {
    statuses?: Record<string, unknown>;
    nodes?: Record<
      string,
      {
        status?: unknown;
        parameters?: GridNodeData["parameters"];
      }
    >;
    edges?: Record<string, StreamEdgeUpdate>;
    topology?: {
      nodes?: BackendNode[];
      edges?: BackendEdge[];
    };
  }) => {
    const isNodeStatus = (value: unknown): value is NodeStatus => {
      return value === "red" || value === "yellow" || value === "green";
    };

    const nextStatuses: Record<string, NodeStatus> = {};
    const nextParameters: Record<string, GridNodeData["parameters"]> = {};
    const nextEdges: Record<string, StreamEdgeUpdate> = {};

    if (payload.statuses && typeof payload.statuses === "object") {
      Object.entries(payload.statuses).forEach(([nodeId, status]) => {
        if (isNodeStatus(status)) {
          nextStatuses[nodeId] = status;
        }
      });
    }

    if (payload.nodes && typeof payload.nodes === "object") {
      Object.entries(payload.nodes).forEach(([nodeId, nodeData]) => {
        if (isNodeStatus(nodeData?.status)) {
          nextStatuses[nodeId] = nodeData.status;
        }

        if (nodeData?.parameters && typeof nodeData.parameters === "object") {
          nextParameters[nodeId] = nodeData.parameters;
        }
      });
    }

    if (payload.edges && typeof payload.edges === "object") {
      Object.entries(payload.edges).forEach(([edgeId, edgeData]) => {
        nextEdges[edgeId] = edgeData;
      });
    }

    if (payload.topology?.nodes && payload.topology?.edges) {
      const nextNodes = toReactFlowNodes(payload.topology.nodes);
      const nextEdgesList = toReactFlowEdges(payload.topology.edges, nextNodes);
      setNodes(nextNodes);
      setEdges(nextEdgesList);
    }

    if (Object.keys(nextStatuses).length > 0 || Object.keys(nextParameters).length > 0) {
      setNodes((currentNodes) =>
        currentNodes.map((node) => {
          const nextStatus = nextStatuses[node.id];
          const nextNodeParameters = nextParameters[node.id];
          const hasStatusChange = !!nextStatus && node.data.status !== nextStatus;
          const hasParameterChange = !!nextNodeParameters;

          if (!hasStatusChange && !hasParameterChange) {
            return node;
          }

          return {
            ...node,
            data: {
              ...node.data,
              ...(hasStatusChange ? { status: nextStatus } : {}),
              ...(hasParameterChange ? { parameters: nextNodeParameters } : {}),
            }
          };
        })
      );
    }

    if (Object.keys(nextEdges).length > 0) {
      setEdges((currentEdges) =>
        currentEdges.map((edge) => {
          const nextEdge = nextEdges[edge.id];
          if (!nextEdge) {
            return edge;
          }

          const nextLineName = nextEdge.lineName ?? edge.data?.lineName ?? "Grid Line";
          const nextCharacteristic =
            nextEdge.characteristic ?? edge.data?.characteristic ?? "Power Transfer";

          return {
            ...edge,
            animated: nextEdge.isActive ?? edge.animated,
            data: {
              lineName: nextLineName,
              characteristic: nextCharacteristic,
              ...edge.data,
              ...(nextEdge.isActive !== undefined ? { isActive: nextEdge.isActive } : {}),
              ...(nextEdge.parameters ? { parameters: nextEdge.parameters } : {}),
            }
          };
        })
      );
    }
  };

  const handlePowerToggle = async (state: "on" | "off") => {
    if (!selectedNode) {
      return;
    }

    setPendingNodeId(selectedNode.id);
    setPanelMessage(null);

    try {
      const response = await fetch(
        `${backendBaseUrl}/grid/nodes/${selectedNode.id}/power/?state=${state}`,
        {
          method: "POST"
        }
      );

      if (!response.ok) {
        setPanelMessage("Unable to update node power state.");
        return;
      }

      const payload = (await response.json()) as {
        statuses?: Record<string, unknown>;
        nodes?: Record<string, { status?: unknown; parameters?: GridNodeData["parameters"] }>;
        edges?: Record<string, StreamEdgeUpdate>;
        topology?: { nodes?: BackendNode[]; edges?: BackendEdge[] };
      };

      applyBackendPayload(payload);
      setPanelMessage(state === "on" ? "Node switched on." : "Node switched off.");
    } catch {
      setPanelMessage("Backend update failed.");
    } finally {
      setPendingNodeId(null);
    }
  };

  useEffect(() => {
    const loadTopology = async () => {
      try {
        const response = await fetch(`${backendBaseUrl}/grid/topology/`);
        if (!response.ok) {
          return;
        }

        const payload = (await response.json()) as {
          nodes?: BackendNode[];
          edges?: BackendEdge[];
        };

        const backendNodes = payload.nodes ?? [];
        const backendEdges = payload.edges ?? [];
        const nextNodes = toReactFlowNodes(backendNodes);
        const nextEdges = toReactFlowEdges(backendEdges, nextNodes);

        setNodes(nextNodes);
        setEdges(nextEdges);
      } catch {
        return;
      }
    };

    void loadTopology();

    const stream = new EventSource(`${backendBaseUrl}/grid/stream/`);

    stream.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as {
          statuses?: Record<string, unknown>;
          nodes?: Record<
            string,
            {
              status?: unknown;
              parameters?: GridNodeData["parameters"];
            }
          >;
          edges?: Record<string, StreamEdgeUpdate>;
          topology?: {
            nodes?: BackendNode[];
            edges?: BackendEdge[];
          };
        };

        applyBackendPayload(payload);
      } catch {
        return;
      }
    };

    return () => {
      stream.close();
    };
  }, [backendBaseUrl, setEdges, setNodes]);

  return (
    <div ref={containerRef} style={{ width: "100%", height: "100vh", position: "relative" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={(connection: Connection) => {
          if (!connection.source || !connection.target) {
            return;
          }

          const sourceNode = nodes.find((node) => node.id === connection.source);
          const targetNode = nodes.find((node) => node.id === connection.target);
          const relation = getLineRelation(sourceNode?.type, targetNode?.type);

          if (!relation) {
            return;
          }

          const alreadyExists = edges.some(
            (edge) => edge.source === connection.source && edge.target === connection.target
          );

          if (alreadyExists) {
            return;
          }

          setEdges((currentEdges) =>
            addEdge(
              {
                ...connection,
                type: "unifiedLine",
                data: relation,
                animated: true
              },
              currentEdges
            )
          );
        }}
        onNodeDoubleClick={(event, node) => {
          setSelectedNodeId(node.id);
          updatePanelPosition(event);
        }}
        nodesDraggable
      />

      {selectedNode && (
        <div
          className="node-action-panel"
          style={{
            left: `${panelPosition.x}px`,
            top: `${panelPosition.y}px`
          }}
        >
          <div className="node-action-header">
            <div className="node-action-title">
              {selectedNode.data.label ?? selectedNode.id}
            </div>
            <button
              className="node-action-close"
              type="button"
              onClick={() => {
                setSelectedNodeId(null);
              }}
              aria-label="Close panel"
            >
              ✕
            </button>
          </div>

          <div className="node-action-buttons">
            <button
              className="node-action-button node-action-button-on"
              type="button"
              disabled={pendingNodeId === selectedNode.id || selectedNode.data.parameters?.powerActive === "On"}
              onClick={() => {
                void handlePowerToggle("on");
              }}
            >
              On
            </button>
            <button
              className="node-action-button node-action-button-off"
              type="button"
              disabled={pendingNodeId === selectedNode.id || selectedNode.data.parameters?.powerActive === "Off"}
              onClick={() => {
                void handlePowerToggle("off");
              }}
            >
              Off
            </button>
          </div>

          {panelMessage && <div className="node-action-message">{panelMessage}</div>}

          <div className="node-parameters-list">
            {getOrderedParameters(selectedNode.data.parameters).map(([key, value]) => (
              <div key={key} className="node-parameter-row">
                <span className="node-parameter-key">{formatParameterKey(key)}</span>
                <span className="node-parameter-value">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;