import json
import random
import time
from collections import defaultdict

from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import (
	DistributionSubstation,
	DistributionTransformer,
	GridEdge,
	GridNode,
	GridSubstation,
	House,
	Industry,
	PowerPlant,
)
from .telemetry import record_latest


CATEGORY_META = {
	"CAT-PP": {"frontend_type": "powerPlant", "unit": "kV", "min": 220.0, "max": 400.0, "label": "Generation"},
	"CAT-GS": {"frontend_type": "gridSubstation", "unit": "kV", "min": 110.0, "max": 132.0, "label": "Transmission"},
	"CAT-DS": {
		"frontend_type": "distributionSubstation",
		"unit": "kV",
		"min": 31.0,
		"max": 33.0,
		"label": "Distribution",
	},
	"CAT-DT": {"frontend_type": "transformer", "unit": "kV", "min": 10.8, "max": 11.2, "label": "Conversion"},
	"CAT-HS": {"frontend_type": "house", "unit": "kW", "min": 1.0, "max": 6.0, "label": "Consumer"},
	"CAT-ID": {"frontend_type": "industry", "unit": "kW", "min": 10.0, "max": 45.0, "label": "Industrial"},
}

LINE_META = {
	"TransmissionLine": {
		"lineName": "Transmission Lines",
		"characteristic": "Extra High Voltage Bulk Transfer",
	},
	"SubTransmissionLine": {
		"lineName": "Sub-Transmission Lines",
		"characteristic": "Step-Down Sub-Transmission Corridor",
	},
	"Feeder11kV": {
		"lineName": "11 kV Feeders",
		"characteristic": "Primary Distribution Feeders",
	},
	"SecondaryDistributionLine": {
		"lineName": "Secondary Distribution Lines",
		"characteristic": "Low Voltage Consumer Delivery",
	},
	"ServiceLine": {
		"lineName": "Service Lines",
		"characteristic": "Last-mile Service Connection",
	},
}

DEPTH_BY_CATEGORY = {
	"CAT-PP": 0,
	"CAT-GS": 1,
	"CAT-DS": 2,
	"CAT-DT": 3,
	"CAT-HS": 4,
	"CAT-ID": 4,
}


def _is_node_live(node: GridNode) -> bool:
	return node.power_active and node.status != "Offline"


def _json_cors_response(payload: dict, status: int = 200) -> JsonResponse:
	response = JsonResponse(payload, status=status)
	response["Access-Control-Allow-Origin"] = "*"
	response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
	response["Access-Control-Allow-Headers"] = "Content-Type"
	return response


def _options_cors_response() -> HttpResponse:
	response = HttpResponse(status=204)
	response["Access-Control-Allow-Origin"] = "*"
	response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
	response["Access-Control-Allow-Headers"] = "Content-Type"
	return response


def _get_concrete_node(node_id: str):
	node = GridNode.objects.select_related("category").get(pk=node_id)
	model_map = {
		"CAT-PP": PowerPlant,
		"CAT-GS": GridSubstation,
		"CAT-DS": DistributionSubstation,
		"CAT-DT": DistributionTransformer,
		"CAT-HS": House,
		"CAT-ID": Industry,
	}
	model_class = model_map.get(node.category_id)
	if model_class is None:
		return node
	return model_class.objects.get(pk=node_id)


def _is_edge_visually_active(edge: GridEdge) -> bool:
	return _is_node_live(edge.source)


def _build_edge_payload() -> dict[str, dict[str, object]]:
	edge_payload = {}
	for edge in GridEdge.objects.select_related("source", "target"):
		line_meta = LINE_META.get(edge.type, LINE_META["ServiceLine"])
		is_active = _is_edge_visually_active(edge)
		edge_payload[str(edge.id)] = {
			"isActive": is_active,
			"parameters": {
				"category": edge.type,
				"capacityKW": round(edge.capacity, 2),
				"active": "On" if is_active else "Off",
			},
			"lineName": line_meta["lineName"],
			"characteristic": line_meta["characteristic"],
		}
	return edge_payload


def _status_from_ratio(value: float, min_value: float, max_value: float) -> str:
	span = max(max_value - min_value, 0.0001)
	ratio = (value - min_value) / span
	# Near the lower/upper limits means caution zone.
	if ratio <= 0.12 or ratio >= 0.88:
		return "yellow"
	return "green"


def _ensure_topology():
    if PowerPlant.objects.exists():
        return

    power_plant = PowerPlant.objects.create(name="Power Plant")
    grid_substation = GridSubstation.objects.create(name="Grid Substation", power_plant=power_plant)
    distribution_substation = DistributionSubstation.objects.create(
        name="Distribution Substation",
        grid_substation=grid_substation,
    )
    transformer = DistributionTransformer.objects.create(
        name="Transformer",
        distribution_substation=distribution_substation,
    )
    House.objects.create(name="House", distribution_transformer=transformer)
    Industry.objects.create(name="Industry", distribution_transformer=transformer)


def _randomize_telemetry():
	_ensure_topology()

	node_inputs: dict[str, float] = {}
	node_outputs: dict[str, float] = {}

	for power_plant in PowerPlant.objects.all():
		node_id = str(power_plant.id)
		if _is_node_live(power_plant):
			node_inputs[node_id] = random.uniform(75.0, 100.0)
			node_outputs[node_id] = random.uniform(220.0, 400.0)
		else:
			node_inputs[node_id] = 0.0
			node_outputs[node_id] = 0.0

	for grid_substation in GridSubstation.objects.select_related("power_plant"):
		node_id = str(grid_substation.id)
		parent_id = str(grid_substation.power_plant_id) if grid_substation.power_plant_id else None
		upstream = node_outputs.get(parent_id, random.uniform(220.0, 400.0))
		if _is_node_live(grid_substation) and upstream > 0:
			node_inputs[node_id] = upstream * random.uniform(0.97, 0.995)
			node_outputs[node_id] = random.uniform(110.0, 132.0)
		else:
			node_inputs[node_id] = 0.0
			node_outputs[node_id] = 0.0

	for distribution_substation in DistributionSubstation.objects.select_related("grid_substation"):
		node_id = str(distribution_substation.id)
		parent_id = str(distribution_substation.grid_substation_id) if distribution_substation.grid_substation_id else None
		upstream = node_outputs.get(parent_id, random.uniform(110.0, 132.0))
		if _is_node_live(distribution_substation) and upstream > 0:
			node_inputs[node_id] = upstream * random.uniform(0.98, 0.995)
			node_outputs[node_id] = random.uniform(31.0, 33.0)
		else:
			node_inputs[node_id] = 0.0
			node_outputs[node_id] = 0.0

	for transformer in DistributionTransformer.objects.select_related("distribution_substation"):
		node_id = str(transformer.id)
		parent_id = str(transformer.distribution_substation_id) if transformer.distribution_substation_id else None
		upstream = node_outputs.get(parent_id, random.uniform(31.0, 33.0))
		if _is_node_live(transformer) and upstream > 0:
			node_inputs[node_id] = upstream * random.uniform(0.98, 0.995)
			node_outputs[node_id] = random.uniform(10.8, 11.2)
		else:
			node_inputs[node_id] = 0.0
			node_outputs[node_id] = 0.0

	for house in House.objects.select_related("distribution_transformer"):
		node_id = str(house.id)
		parent_id = str(house.distribution_transformer_id) if house.distribution_transformer_id else None
		upstream = node_outputs.get(parent_id, random.uniform(10.8, 11.2))
		if _is_node_live(house) and upstream > 0:
			node_inputs[node_id] = upstream
			node_outputs[node_id] = random.uniform(1.0, 6.0)
		else:
			node_inputs[node_id] = 0.0
			node_outputs[node_id] = 0.0

	for industry in Industry.objects.select_related("distribution_transformer"):
		node_id = str(industry.id)
		parent_id = str(industry.distribution_transformer_id) if industry.distribution_transformer_id else None
		upstream = node_outputs.get(parent_id, random.uniform(10.8, 11.2))
		if _is_node_live(industry) and upstream > 0:
			node_inputs[node_id] = upstream
			node_outputs[node_id] = random.uniform(10.0, 45.0)
		else:
			node_inputs[node_id] = 0.0
			node_outputs[node_id] = 0.0

	return node_inputs, node_outputs


def _build_topology_response():
	_ensure_topology()

	nodes = list(GridNode.objects.select_related("category").all())
	grouped = defaultdict(list)
	for node in nodes:
		depth = DEPTH_BY_CATEGORY.get(node.category_id, 5)
		grouped[depth].append(node)

	topology_nodes = []
	for depth in sorted(grouped.keys()):
		ordered = sorted(grouped[depth], key=lambda item: (item.name.lower(), str(item.id)))
		total = len(ordered)
		spacing = min(170.0, max(56.0, 980.0 / max(total - 1, 1)))
		for index, node in enumerate(ordered):
			meta = CATEGORY_META.get(node.category_id, CATEGORY_META["CAT-HS"])
			y_offset = (index - (total - 1) / 2.0) * spacing
			topology_nodes.append(
				{
					"id": str(node.id),
					"label": node.name,
					"type": meta["frontend_type"],
					"position": {"x": 120 + depth * 240, "y": 280 + y_offset},
				}
			)

	topology_edges = []
	for edge in GridEdge.objects.select_related("source", "target"):
		line_meta = LINE_META.get(edge.type, LINE_META["ServiceLine"])
		is_active = _is_edge_visually_active(edge)
		topology_edges.append(
			{
				"id": str(edge.id),
				"source": str(edge.source_id),
				"target": str(edge.target_id),
				"data": {
					"lineName": line_meta["lineName"],
					"characteristic": line_meta["characteristic"],
					"isActive": is_active,
					"parameters": {
						"category": edge.type,
						"capacityKW": round(edge.capacity, 2),
						"active": "On" if is_active else "Off",
					},
				},
			}
		)

	return {"nodes": topology_nodes, "edges": topology_edges}


def _build_stream_payload():
	node_inputs, node_outputs = _randomize_telemetry()

	statuses = {}
	node_payload = {}
	for node in GridNode.objects.select_related("category").all():
		meta = CATEGORY_META.get(node.category_id, CATEGORY_META["CAT-HS"])
		node_id = str(node.id)
		input_value = node_inputs.get(node_id, 0.0)
		output_value = node_outputs.get(node_id, 0.0)
		if not _is_node_live(node):
			status = "red"
			input_value = 0.0
			output_value = 0.0
		else:
			ratio_status = _status_from_ratio(output_value, meta["min"], meta["max"])
			status = "yellow" if node.status == "Critical" else ratio_status
		record_latest(
			node_id,
			input_value=input_value,
			output_value=output_value,
			status=status,
			persisted_status=node.status if not _is_node_live(node) else None,
		)
		statuses[node_id] = status
		node_payload[node_id] = {
			"status": status,
			"parameters": {
				"category": meta["label"],
				"input": f"{input_value:.2f} {meta['unit']}",
				"output": f"{output_value:.2f} {meta['unit']}",
				"powerActive": "On" if node.power_active else "Off",
			},
		}

	return {"statuses": statuses, "nodes": node_payload, "edges": _build_edge_payload()}


def grid_topology(request):
	return _json_cors_response(_build_topology_response())


def grid_status_snapshot(request):
	payload = _build_stream_payload()
	payload["topology"] = _build_topology_response()
	return _json_cors_response(payload)


def grid_status_stream(request):
	def event_stream():
		counter = 0
		while True:
			payload = _build_stream_payload()
			if counter % 10 == 0:
				payload["topology"] = _build_topology_response()
			yield f"data: {json.dumps(payload)}\n\n"
			counter += 1
			time.sleep(1)

	response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
	response["Cache-Control"] = "no-cache"
	response["X-Accel-Buffering"] = "no"
	response["Access-Control-Allow-Origin"] = "*"
	return response


@csrf_exempt
def grid_node_power(request, node_id):
	if request.method == "OPTIONS":
		return _options_cors_response()

	if request.method != "POST":
		return _json_cors_response({"error": "Method not allowed"}, status=405)

	state = request.GET.get("state")
	if state not in {"on", "off"}:
		return _json_cors_response({"error": "state must be 'on' or 'off'"}, status=400)

	try:
		node = _get_concrete_node(str(node_id))
	except GridNode.DoesNotExist:
		return _json_cors_response({"error": "Node not found"}, status=404)

	node.status = "Stable" if state == "on" else "Offline"
	node.save()

	payload = _build_stream_payload()
	payload["topology"] = _build_topology_response()
	payload["updatedNodeId"] = str(node.id)
	payload["requestedState"] = state
	return _json_cors_response(payload)
