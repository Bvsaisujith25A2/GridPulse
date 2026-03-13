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
  house: HouseNode
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

const initialNodes: Node<GridNodeData>[] = [
  {
    id: "1",
    position: { x: 100, y: 100 },
    data: {
      label: "Power Plant",
      status: "red",
      parameters: {
        category: "Generation",
        input: "Fuel / Steam",
        output: "High-voltage Power",
        capacityMW: 520
      }
    },
    type: "powerPlant"
  },
  {
    id: "2",
    position: { x: 300, y: 100 },
    data: {
      label: "Grid Substation",
      status: "red",
      parameters: {
        category: "Transmission",
        input: "220kV",
        output: "132kV",
        breakerState: "Closed"
      }
    },
    type: "gridSubstation"
  },
  {
    id: "3",
    position: { x: 500, y: 100 },
    data: {
      label: "Distribution Substation",
      status: "red",
      parameters: {
        category: "Distribution",
        input: "132kV",
        output: "33kV",
        feederCount: 12
      }
    },
    type: "distributionSubstation"
  },
  {
    id: "4",
    position: { x: 700, y: 100 },
    data: {
      label: "Transformer",
      status: "red",
      parameters: {
        category: "Conversion",
        input: "33kV",
        output: "11kV",
        loadPercent: 71
      }
    },
    type: "transformer"
  },
  {
    id: "5",
    position: { x: 900, y: 100 },
    data: {
      label: "House",
      status: "red",
      parameters: {
        category: "Consumer",
        input: "11kV",
        output: "Usage",
        demandKW: 4.5
      }
    },
    type: "house"
  }
];

const initialEdges: Edge<LineEdgeData>[] = [
  {
    id: "e1-2",
    source: "1",
    target: "2",
    type: "unifiedLine",
    data: lineRelationMap["powerPlant->gridSubstation"],
    animated: true
  },
  {
    id: "e2-3",
    source: "2",
    target: "3",
    type: "unifiedLine",
    data: lineRelationMap["gridSubstation->distributionSubstation"],
    animated: true
  },
  {
    id: "e3-4",
    source: "3",
    target: "4",
    type: "unifiedLine",
    data: lineRelationMap["distributionSubstation->transformer"],
    animated: true
  },
  {
    id: "e4-5",
    source: "4",
    target: "5",
    type: "unifiedLine",
    data: lineRelationMap["transformer->house"],
    animated: true
  }
];

function App() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<LineEdgeData>(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [panelPosition, setPanelPosition] = useState({ x: 16, y: 16 });

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

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/grid-status/`);

    const isNodeStatus = (value: unknown): value is NodeStatus => {
      return value === "red" || value === "yellow" || value === "green";
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as {
          id?: string | number;
          nodeId?: string | number;
          status?: unknown;
          statuses?: Record<string, unknown>;
        };

        const nextStatuses: Record<string, NodeStatus> = {};

        if (payload.statuses && typeof payload.statuses === "object") {
          Object.entries(payload.statuses).forEach(([nodeId, status]) => {
            if (isNodeStatus(status)) {
              nextStatuses[nodeId] = status;
            }
          });
        }

        const singleNodeId = payload.nodeId ?? payload.id;
        if (singleNodeId !== undefined && isNodeStatus(payload.status)) {
          nextStatuses[String(singleNodeId)] = payload.status;
        }

        if (Object.keys(nextStatuses).length === 0) {
          return;
        }

        setNodes((currentNodes) =>
          currentNodes.map((node) => {
            const nextStatus = nextStatuses[node.id];

            if (!nextStatus || node.data.status === nextStatus) {
              return node;
            }

            return {
              ...node,
              data: {
                ...node.data,
                status: nextStatus
              }
            };
          })
        );
      } catch {
        return;
      }
    };

    return () => {
      socket.close();
    };
  }, [setNodes]);

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