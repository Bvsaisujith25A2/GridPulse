import { type MouseEvent as ReactMouseEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  addEdge,
  type Connection,
  type Edge,
  type EdgeTypes,
  MiniMap,
  type Node,
  type ReactFlowInstance,
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
import gridPulseLogo from "./icons/gridpulse.jpeg";
import powerPlantIcon from "./icons/powerplant.svg";
import gridSubstationIcon from "./icons/gridsubstation.svg";
import distributionSubstationIcon from "./icons/distributionsubstation.svg";
import transformerIcon from "./icons/transformer.svg";
import houseIcon from "./icons/house.svg";

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

type NodePanel = {
  nodeId: string;
  x: number;
  y: number;
  zIndex: number;
};

const deckTypeOptions: Array<{ value: string; label: string }> = [
  { value: "powerPlant", label: "Power Plant" },
  { value: "gridSubstation", label: "Grid Substation" },
  { value: "distributionSubstation", label: "Distribution Substation" },
  { value: "transformer", label: "Transformer" },
  { value: "house", label: "House" },
  { value: "industry", label: "Industry" }
];

const deckTypeVisuals: Record<string, { label: string; icon: string }> = {
  powerPlant: { label: "Power Plant", icon: powerPlantIcon },
  gridSubstation: { label: "Grid Substation", icon: gridSubstationIcon },
  distributionSubstation: { label: "Distribution Substation", icon: distributionSubstationIcon },
  transformer: { label: "Transformer", icon: transformerIcon },
  house: { label: "House", icon: houseIcon },
  industry: { label: "Industry", icon: houseIcon }
};

const requiredParentByType: Record<string, string | null> = {
  powerPlant: null,
  gridSubstation: "powerPlant",
  distributionSubstation: "gridSubstation",
  transformer: "distributionSubstation",
  house: "transformer",
  industry: "transformer"
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
  const dragStateRef = useRef<{ nodeId: string; offsetX: number; offsetY: number } | null>(null);
  const panelZCounterRef = useRef(10);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<LineEdgeData>([]);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [openPanels, setOpenPanels] = useState<NodePanel[]>([]);
  const [highlightRootId, setHighlightRootId] = useState<string | null>(null);
  const [highlightedNodeIds, setHighlightedNodeIds] = useState<Set<string>>(new Set());
  const [highlightedEdgeIds, setHighlightedEdgeIds] = useState<Set<string>>(new Set());
  const [pendingNodeId, setPendingNodeId] = useState<string | null>(null);
  const [panelMessages, setPanelMessages] = useState<Record<string, string>>({});
  const [deckType, setDeckType] = useState<string>("gridSubstation");
  const [deckName, setDeckName] = useState<string>("");
  const [deckParentId, setDeckParentId] = useState<string>("");
  const [deckMessage, setDeckMessage] = useState<string>("");
  const [deckPending, setDeckPending] = useState<boolean>(false);
  const backendBaseUrl = import.meta.env.VITE_BACKEND_URL ?? "http://127.0.0.1:8000";

  const nodesById = useMemo(() => {
    const map = new Map<string, Node<GridNodeData>>();
    nodes.forEach((node) => {
      map.set(node.id, node);
    });
    return map;
  }, [nodes]);

  const parentTypeNeeded = requiredParentByType[deckType] ?? null;
  const parentCandidates = useMemo(() => {
    if (!parentTypeNeeded) {
      return [] as Node<GridNodeData>[];
    }

    return nodes
      .filter((node) => node.type === parentTypeNeeded)
      .sort((a, b) => String(a.data.label ?? a.id).localeCompare(String(b.data.label ?? b.id)));
  }, [deckType, nodes, parentTypeNeeded]);

  const computeTrackToPowerPlant = (startNodeId: string, currentEdges: Edge<LineEdgeData>[]) => {
    const incomingMap = new Map<string, Edge<LineEdgeData>[]>();

    currentEdges.forEach((edge) => {
      const incoming = incomingMap.get(edge.target) ?? [];
      incoming.push(edge);
      incomingMap.set(edge.target, incoming);
    });

    const nodeIds = new Set<string>();
    const edgeIds = new Set<string>();
    const stack = [startNodeId];

    while (stack.length > 0) {
      const currentNodeId = stack.pop();
      if (!currentNodeId || nodeIds.has(currentNodeId)) {
        continue;
      }

      nodeIds.add(currentNodeId);
      const incomingEdges = incomingMap.get(currentNodeId) ?? [];
      incomingEdges.forEach((edge) => {
        edgeIds.add(edge.id);
        if (!nodeIds.has(edge.source)) {
          stack.push(edge.source);
        }
      });
    }

    return { nodeIds, edgeIds };
  };

  const handleShowTrack = (nodeId: string) => {
    const sourceNode = nodesById.get(nodeId);
    if (!sourceNode) {
      return;
    }

    setHighlightRootId(nodeId);
    const { nodeIds, edgeIds } = computeTrackToPowerPlant(nodeId, edges);
    setHighlightedNodeIds(nodeIds);
    setHighlightedEdgeIds(edgeIds);
    setPanelMessages((current) => ({
      ...current,
      [nodeId]: "Path highlighted to upstream source."
    }));

    if (reactFlowInstance) {
      const focusNodes = nodes.filter((node) => nodeIds.has(node.id));
      if (focusNodes.length > 0) {
        reactFlowInstance.fitView({ nodes: focusNodes, padding: 0.3, duration: 450 });
      }
    }
  };

  const handleClearTrack = () => {
    setHighlightRootId(null);
    setHighlightedNodeIds(new Set());
    setHighlightedEdgeIds(new Set());
    setPanelMessages((current) => {
      const next = { ...current };
      Object.keys(next).forEach((nodeId) => {
        next[nodeId] = "Path highlight cleared.";
      });
      return next;
    });
    if (reactFlowInstance) {
      reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
    }
  };

  const displayNodes = useMemo(() => {
    return nodes.map((node) => {
      const isHighlighted = highlightedNodeIds.has(node.id);
      const showLabel = zoomLevel >= 1.35 || (!!highlightRootId && isHighlighted);

      if (!highlightRootId) {
        return {
          ...node,
          data: {
            ...node.data,
            showLabel
          }
        };
      }

      return {
        ...node,
        data: {
          ...node.data,
          showLabel
        },
        style: {
          ...(node.style ?? {}),
          opacity: isHighlighted ? 1 : 0.16,
          transition: "opacity 0.2s ease"
        }
      };
    });
  }, [highlightRootId, highlightedNodeIds, nodes, zoomLevel]);

  const displayEdges = useMemo(() => {
    if (!highlightRootId) {
      return edges;
    }

    return edges.map((edge) => {
      const isHighlighted = highlightedEdgeIds.has(edge.id);
      return {
        ...edge,
        animated: isHighlighted ? false : edge.animated,
        data: {
          ...edge.data,
          highlighted: isHighlighted,
          dimmed: !isHighlighted
        }
      };
    });
  }, [edges, highlightedEdgeIds, highlightRootId]);

  const zoomLabel = `${Math.round(zoomLevel * 100)}%`;

  const bringPanelToFront = (nodeId: string) => {
    panelZCounterRef.current += 1;
    const nextZ = panelZCounterRef.current;
    setOpenPanels((currentPanels) =>
      currentPanels.map((panel) =>
        panel.nodeId === nodeId
          ? {
              ...panel,
              zIndex: nextZ
            }
          : panel
      )
    );
  };

  const openPanelAt = (nodeId: string, x: number, y: number) => {
    panelZCounterRef.current += 1;
    const nextZ = panelZCounterRef.current;
    setOpenPanels((currentPanels) => {
      const existing = currentPanels.find((panel) => panel.nodeId === nodeId);
      if (existing) {
        return currentPanels.map((panel) =>
          panel.nodeId === nodeId
            ? {
                ...panel,
                x,
                y,
                zIndex: nextZ
              }
            : panel
        );
      }

      return [
        ...currentPanels,
        {
          nodeId,
          x,
          y,
          zIndex: nextZ
        }
      ];
    });
  };

  const closePanel = (nodeId: string) => {
    setOpenPanels((currentPanels) => currentPanels.filter((panel) => panel.nodeId !== nodeId));
    setPanelMessages((current) => {
      const next = { ...current };
      delete next[nodeId];
      return next;
    });
  };

  const handlePanelDragStart = (event: ReactMouseEvent<HTMLDivElement>, panel: NodePanel) => {
    bringPanelToFront(panel.nodeId);

    dragStateRef.current = {
      nodeId: panel.nodeId,
      offsetX: event.clientX - panel.x,
      offsetY: event.clientY - panel.y
    };
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

  const handlePowerToggle = async (nodeId: string, state: "on" | "off") => {
    const node = nodesById.get(nodeId);
    if (!node) {
      return;
    }

    setPendingNodeId(node.id);
    setPanelMessages((current) => ({ ...current, [node.id]: "" }));

    try {
      const response = await fetch(
        `${backendBaseUrl}/grid/nodes/${node.id}/power/?state=${state}`,
        {
          method: "POST"
        }
      );

      if (!response.ok) {
        setPanelMessages((current) => ({
          ...current,
          [node.id]: "Unable to update node power state."
        }));
        return;
      }

      const payload = (await response.json()) as {
        statuses?: Record<string, unknown>;
        nodes?: Record<string, { status?: unknown; parameters?: GridNodeData["parameters"] }>;
        edges?: Record<string, StreamEdgeUpdate>;
        topology?: { nodes?: BackendNode[]; edges?: BackendEdge[] };
      };

      applyBackendPayload(payload);
      setPanelMessages((current) => ({
        ...current,
        [node.id]: state === "on" ? "Node switched on." : "Node switched off."
      }));
    } catch {
      setPanelMessages((current) => ({
        ...current,
        [node.id]: "Backend update failed."
      }));
    } finally {
      setPendingNodeId(null);
    }
  };

  const handleCreateNode = async () => {
    const trimmedName = deckName.trim();
    if (!trimmedName) {
      setDeckMessage("Node name is required.");
      return;
    }

    if (parentTypeNeeded && !deckParentId) {
      setDeckMessage("Select a parent node for this type.");
      return;
    }

    setDeckPending(true);
    setDeckMessage("");

    try {
      const response = await fetch(`${backendBaseUrl}/grid/nodes/create/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          type: deckType,
          name: trimmedName,
          parentId: parentTypeNeeded ? deckParentId : null
        })
      });

      const payload = (await response.json()) as {
        error?: string;
        statuses?: Record<string, unknown>;
        nodes?: Record<string, { status?: unknown; parameters?: GridNodeData["parameters"] }>;
        edges?: Record<string, StreamEdgeUpdate>;
        topology?: { nodes?: BackendNode[]; edges?: BackendEdge[] };
      };

      if (!response.ok) {
        setDeckMessage(payload.error ?? "Unable to create node.");
        return;
      }

      applyBackendPayload(payload);
      setDeckName("");
      setDeckParentId("");
      setDeckMessage("Node created and synced with backend.");
    } catch {
      setDeckMessage("Node creation failed.");
    } finally {
      setDeckPending(false);
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

  useEffect(() => {
    const onMouseMove = (event: MouseEvent) => {
      if (!dragStateRef.current) {
        return;
      }

      const containerRect = containerRef.current?.getBoundingClientRect();
      if (!containerRect) {
        return;
      }

      const nextX = event.clientX - dragStateRef.current.offsetX;
      const nextY = event.clientY - dragStateRef.current.offsetY;

      setOpenPanels((currentPanels) =>
        currentPanels.map((panel) =>
          panel.nodeId === dragStateRef.current?.nodeId
            ? {
                ...panel,
                x: nextX,
                y: nextY
              }
            : panel
        )
      );
    };

    const onMouseUp = () => {
      dragStateRef.current = null;
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  useEffect(() => {
    if (!highlightRootId) {
      return;
    }

    const { nodeIds, edgeIds } = computeTrackToPowerPlant(highlightRootId, edges);
    setHighlightedNodeIds(nodeIds);
    setHighlightedEdgeIds(edgeIds);
  }, [edges, highlightRootId]);

  return (
    <div ref={containerRef} className="gridpulse-shell">
      <div className="gridpulse-atmosphere" aria-hidden="true" />
      <div className="gridpulse-hud">
        <div className="gridpulse-title-wrap">
          <img src={gridPulseLogo} alt="GridPulse" className="gridpulse-logo" />
          <div className="gridpulse-kicker">National Grid Console</div>
          <div className="gridpulse-title">GridPulse Live Map</div>
        </div>
        <div className="gridpulse-status-wrap">
          <span className="gridpulse-chip">Zoom {zoomLabel}</span>
          <span className="gridpulse-chip">{nodes.length} Modules</span>
        </div>
      </div>

      <aside className="gridpulse-deck">
        <div className="gridpulse-deck-title">Node Deck</div>
        <label className="gridpulse-field-label" htmlFor="deck-node-type">
          Module Type
        </label>
        <select
          id="deck-node-type"
          className="gridpulse-input"
          value={deckType}
          onChange={(event) => {
            const nextType = event.target.value;
            setDeckType(nextType);
            setDeckParentId("");
          }}
          disabled={deckPending}
        >
          {deckTypeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <div className="gridpulse-resource-showcase">
          {deckTypeOptions.map((option) => {
            const visual = deckTypeVisuals[option.value];
            const isActive = deckType === option.value;

            return (
              <button
                key={option.value}
                type="button"
                className={`gridpulse-resource-option${isActive ? " is-active" : ""}`}
                onClick={() => {
                  setDeckType(option.value);
                  setDeckParentId("");
                }}
                disabled={deckPending}
              >
                <img src={visual.icon} alt={visual.label} className="gridpulse-resource-icon" />
                <span className="gridpulse-resource-label">{visual.label}</span>
              </button>
            );
          })}
        </div>

        <label className="gridpulse-field-label" htmlFor="deck-node-name">
          Node Name
        </label>
        <input
          id="deck-node-name"
          className="gridpulse-input"
          type="text"
          placeholder="Enter node name"
          value={deckName}
          onChange={(event) => {
            setDeckName(event.target.value);
          }}
          disabled={deckPending}
        />

        {parentTypeNeeded && (
          <>
            <label className="gridpulse-field-label" htmlFor="deck-parent-node">
              Parent Node
            </label>
            <select
              id="deck-parent-node"
              className="gridpulse-input"
              value={deckParentId}
              onChange={(event) => {
                setDeckParentId(event.target.value);
              }}
              disabled={deckPending}
            >
              <option value="">Select parent...</option>
              {parentCandidates.map((node) => (
                <option key={node.id} value={node.id}>
                  {String(node.data.label ?? node.id)}
                </option>
              ))}
            </select>
          </>
        )}

        <button
          className="gridpulse-create-btn"
          type="button"
          onClick={() => {
            void handleCreateNode();
          }}
          disabled={deckPending}
        >
          {deckPending ? "Adding..." : "Add Module"}
        </button>

        {deckMessage && <div className="gridpulse-deck-message">{deckMessage}</div>}
      </aside>

      <div className="gridpulse-canvas-wrap">
      <ReactFlow
        nodes={displayNodes}
        edges={displayEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onInit={setReactFlowInstance}
        onMove={(_event, viewport) => {
          setZoomLevel(viewport.zoom);
        }}
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
          const containerRect = containerRef.current?.getBoundingClientRect();
          if (!containerRect) {
            return;
          }

          const nextX = event.clientX - containerRect.left + 14;
          const nextY = event.clientY - containerRect.top - 10;
          openPanelAt(node.id, nextX, nextY);
        }}
        nodesDraggable
      >
        <MiniMap
          pannable
          zoomable
          position="bottom-right"
          nodeColor="#1aa6ff"
          maskColor="rgba(4, 11, 27, 0.7)"
          style={{
            background: "rgba(7, 21, 47, 0.9)",
            border: "1px solid rgba(69, 231, 255, 0.35)",
            borderRadius: "10px"
          }}
        />
      </ReactFlow>
      </div>

      {openPanels
        .slice()
        .sort((a, b) => a.zIndex - b.zIndex)
        .map((panel) => {
          const panelNode = nodesById.get(panel.nodeId);
          if (!panelNode) {
            return null;
          }

          const panelMessage = panelMessages[panel.nodeId];

          return (
            <div
              key={panel.nodeId}
              className="node-action-panel"
              style={{
                left: `${panel.x}px`,
                top: `${panel.y}px`,
                zIndex: panel.zIndex
              }}
              onMouseDown={() => bringPanelToFront(panel.nodeId)}
            >
              <div className="node-action-header" onMouseDown={(event) => handlePanelDragStart(event, panel)}>
                <div className="node-action-title">{panelNode.data.label ?? panelNode.id}</div>
                <button
                  className="node-action-close"
                  type="button"
                  onClick={() => {
                    closePanel(panel.nodeId);
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
                  disabled={pendingNodeId === panelNode.id || panelNode.data.parameters?.powerActive === "On"}
                  onClick={() => {
                    void handlePowerToggle(panelNode.id, "on");
                  }}
                >
                  On
                </button>
                <button
                  className="node-action-button node-action-button-off"
                  type="button"
                  disabled={pendingNodeId === panelNode.id || panelNode.data.parameters?.powerActive === "Off"}
                  onClick={() => {
                    void handlePowerToggle(panelNode.id, "off");
                  }}
                >
                  Off
                </button>
                <button
                  className="node-action-button node-action-button-track"
                  type="button"
                  onClick={() => {
                    handleShowTrack(panelNode.id);
                  }}
                >
                  Show Track
                </button>
                <button
                  className="node-action-button node-action-button-track-clear"
                  type="button"
                  onClick={handleClearTrack}
                  disabled={!highlightRootId}
                >
                  Clear
                </button>
              </div>

              {panelMessage && <div className="node-action-message">{panelMessage}</div>}

              <div className="node-parameters-list">
                {getOrderedParameters(panelNode.data.parameters).map(([key, value]) => (
                  <div key={key} className="node-parameter-row">
                    <span className="node-parameter-key">{formatParameterKey(key)}</span>
                    <span className="node-parameter-value">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
    </div>
  );
}

export default App;