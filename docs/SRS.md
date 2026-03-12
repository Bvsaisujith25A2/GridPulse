This Software Requirements Specification (SRS) for **Project GridPulse** details the functional and non-functional requirements for the AI-driven smart grid stability system. It aligns with the "Vertical Construction" strategy from the previous roadmap, ensuring each technical requirement supports a scalable, production-ready implementation.

---

# Software Requirements Specification (SRS): GridPulse

## 1. Introduction

### 1.1 Purpose

The purpose of this document is to specify the software requirements for Project GridPulse. GridPulse is an AI-native system designed to predict decentralized smart grid stability with a 30-minute lead time and provide automated load-balancing recommendations.

### 1.2 Scope

The system will ingest telemetry from a 4-node star topology (1 producer, 3 consumers) and output a mathematical stability index ($stab$) and categorical label ($stabf$). It includes a serverless inference engine, a RESTful API, and a simulation-to-control bridge.

### 1.3 Definitions and Acronyms

* **DSGC:** Decentral Smart Grid Control.
* **DER:** Distributed Energy Resource.
* **STLF:** Short-Term Load Forecasting (30 minutes to 15 days).
* **$stab$:** Maximum real part of the characteristic equation root; positive indicates instability.


* **IEEE 1547:** Standard for Interconnecting Distributed Resources with Electric Power Systems.

---

## 2. Overall Description

### 2.1 Product Perspective

GridPulse is a standalone cloud-native application. It interacts with smart grid sensors (simulated or IoT) via API and utilizes **OpenDSS** for closed-loop validation.

### 2.2 Product Functions

* **Data Augmentation:** Permutate consumer node telemetry to expand training sets from 10k to 60k records.


* **Stability Prediction:** Use GRU/LSTM architectures to forecast "Blackout Risks".


* **API Orchestration:** Provide endpoints for telemetry ingestion and real-time inference.


* **Load Balancing Logic:** Recommend node-specific load reductions based on price elasticity ($g$).

### 2.3 User Classes and Characteristics

* **Grid Operators:** High-level users who monitor stability indices via dashboards.
* **Automated Agents:** Software clients that poll recommendations to execute DER switches.

### 2.4 Operating Environment

* **Training:** Python 3.10 with TensorFlow/Keras on GPU-enabled environments.
* **Inference:** AWS Lambda (Serverless) using TF-Lite and Python 3.10 runtime.



---

## 3. External Interface Requirements

### 3.1 User Interfaces

* **Dashboard:** A web-based UI showing real-time grid "Heat Maps" (stability vs. instability) and regional power distribution.



### 3.2 Software Interfaces

* **FastAPI:** Serves as the primary REST API framework.
* **Mangum:** Adapts FastAPI for AWS Lambda event-driven triggers.


* **OpenDSSDirect.py:** Interface for programmatic grid simulation and control.



### 3.3 Communication Protocols

* **REST/JSON:** For telemetry ingestion and inference responses.
* **MQTT (Optional):** For real-time IoT sensor data streaming to the cloud.

---

## 4. System Features (Functional Requirements)

### 4.1 Feature: Data Ingestion & Validation

* **Requirement ID:** FR-1
* **Description:** The system shall validate incoming JSON telemetry using Pydantic schemas.
* **Input Schema:** Must include reaction times ($\tau_1$ to $\tau_4$), power balance ($p_1$ to $p_4$), and elasticity ($g_1$ to $g_4$).


* **Constraint:** $p_1$ must satisfy the conservation law $p_1 = \text{abs}(p_2 + p_3 + p_4)$.

### 4.2 Feature: Stability Forecasting

* **Requirement ID:** FR-2
* **Description:** The system shall output a stability index ($stab$) where values $> 0$ trigger an "Unstable" state.


* **Model Specs:** The inference engine shall utilize a Gated Recurrent Unit (GRU) for its balance of accuracy (90.2%+) and low computational footprint.



### 4.3 Feature: Automated Recommendation

* **Requirement ID:** FR-3
* **Description:** If instability is predicted, the system shall identify the consumer node with the highest $g$ (willingness to adapt) and recommend a load reduction.

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements

* **Latency:** Inference response time shall be $< 200\text{ms}$ for warm-start Lambda invocations.


* **Forecasting Horizon:** The system must provide predictions with a lead time of exactly 30 minutes.

### 5.2 Security Requirements

* **Data Integrity:** All API inputs must be sanitized via Pydantic to prevent injection attacks.
* **Infrastructure:** AWS Lambda functions must use IAM roles with "Least Privilege" access to ECR and S3.



### 5.3 Reliability and Standards

* **Accuracy:** The model shall maintain a Mean Absolute Error (MAE) $< 0.035$ on validation sets.


* **Compliance:** Telemetry and control signals should align with IEEE 1547 interoperability guidelines for DERs.

---

## 6. AI/ML Specific Requirements

### 6.1 Model Lifecycle

* **Format:** Models must be converted to `.tflite` format to satisfy the 250MB uncompressed Lambda limit.


* **Preprocessing:** The inference handler must apply **Min-Max Normalization** using the exact scalars generated during the training phase.



### 6.2 Observability

* **Tracing:** The system shall integrate **Pydantic Logfire** to provide structured application traces from the API entry point to the ML model output.













This is the final, fully integrated **Software Requirements Specification (SRS)**. It combines the **Vertical Construction** (ML/Backend), the **Digital Twin Canvas**, the **Real-Time Spatial Streaming** (WebSockets for positioning), and the **Prosumer/Smart House** logic.

---

# Software Requirements Specification (SRS)

## Project: GridPulse – AI-Driven Smart Grid Digital Twin

**Version:** 1.5 (Real-Time Spatial Sync Edition)



**Environment:** Localhost (ThinkPad T495s) via Cloudflare Tunnels

---

## 1. Introduction

### 1.1 Purpose

GridPulse is a real-time "Digital Twin" platform for decentralized power networks. It provides a visual interface for grid topology, real-time telemetry streaming, and AI-driven stability forecasting. It allows for bi-directional control, where UI actions (moving nodes, toggling switches) interact directly with a Python-based electrical simulation and ML model.

### 1.2 Scope

The system integrates a **Django/FastAPI** backend with a **React Flow** canvas. Key innovations include auto-layout graph positioning, real-time coordinate streaming via WebSockets, and prosumer energy modeling (Smart Houses).

---

## 2. Overall Description

### 2.1 Product Perspective

GridPulse operates as a high-performance local server. By utilizing **Django Channels**, it treats spatial data (node positions) as telemetry, allowing for a collaborative, low-latency monitoring experience.

### 2.2 Functional Requirements

* **FR-1: Real-Time Spatial Streaming:** Node coordinates ($x, y$) are streamed via WebSockets. Moving a node on one client updates all other clients instantly.
* **FR-2: Auto-Layout Engine:** On initial load, nodes without fixed coordinates are placed using a Force-Directed Graph algorithm (Dagre/D3).
* **FR-3: Prosumer Logic (Smart Houses):** Houses act as dynamic nodes with net-metering logic ($P_{net} = P_{solar} - P_{load}$).
* **FR-4: Telemetry Mocking:** Every node type (Transformer, Plant, Pole) automatically generates real-world electrical mockup data (Voltage, Power, Frequency).
* **FR-5: AI Stability Prediction:** A GRU-based ANN predicts "Blackout Risk" based on current grid topology and load.

---

## 3. System Architecture (SAD)

The "Vertical Construction" architecture:

1. **Frontend (React + React Flow):** Manages the canvas and captures drag-and-drop events to emit WebSocket messages.
2. **Backend (Django + Channels):** The "State Coordinator." It manages the PostgreSQL database and broadcasts coordinate/telemetry updates.
3. **ML Engine (FastAPI + GRU):** The "Brain." It receives 12-parameter telemetry and returns stability indices ($stab$ and $stabf$).
4. **Simulation Layer (OpenDSSDirect):** Validates the physics of the grid connections created on the canvas.

---

## 4. Entity Relationship Diagram (ERD)

### **4.1 Entity: GridComponent (The Node)**

* `id`: UUID (PK)
* `type`: ENUM (Plant, Transformer, Station, Substation, Pole, House)
* `x_pos / y_pos`: Float (Streamed via WebSockets; can be `null` for auto-layout)
* `status`: ENUM (Stable, Warning, Critical, Offline)
* `mock_data`: JSONField (Stores current $V, P, f, Q$)

### **4.2 Entity: GridEdge (The Connection)**

* `source`: FK (GridComponent)
* `target`: FK (GridComponent)
* `flow_direction`: Integer (1: Forward, -1: Reverse, 0: No Flow)
* `capacity`: Float (Max kW)

---

## 5. Technical Stack Summary

| Layer | Technology | Role |
| --- | --- | --- |
| **Canvas UI** | React Flow + Dagre | Topology visualization & auto-layout. |
| **Real-Time** | Django Channels + Redis | WebSocket broadcasting of coordinates/metrics. |
| **Logic/DB** | Django + PostgreSQL | Asset management and "Source of Truth." |
| **AI Inference** | FastAPI + Keras (GRU) | Stability prediction and recommendation. |
| **Exhibition** | Cloudflare Tunnels | Exposing localhost for live demos. |

---

## 6. Detailed Component Metrics (Mockup Data)

Every node is initialized with the following real-life metrics:

* **Power Plant:** $P \approx 500MW$, $Q \approx 50MVAr$, $f = 50.0Hz \pm 0.05$.
* **Substation:** $V_{in} = 132kV$, $V_{out} = 33kV$, Power Factor $\approx 0.9$.
* **Smart Meter (House):** Consumption $1.5kW - 5.0kW$, Solar Gen $0.0kW - 4.5kW$.
* **Smart Pole:** Leakage Current $< 5mA$, Ambient Temp $25^\circ C - 45^\circ C$.

---

## 7. Mathematical & Logic Layer

### 7.1 Spatial Sync Logic

Whenever a `nodeDrag` event occurs:


$$Event_{emit} = \{id, x, y, timestamp\}$$


The Backend ignores any timestamp older than the last processed update to prevent "jitter."

### 7.2 Net Flow Direction

The animation speed and direction of the "Edges" (wires) are determined by:


$$Direction = \text{sign}(P_{solar} - P_{load})$$


If positive, the edge glows and moves toward the grid; if negative, it moves toward the house.

---

### **Final Deployment Strategy for Demo:**

1. **Start Local Services:** Run Redis, Django, and FastAPI on your ThinkPad.
2. **Launch Tunnel:** `cloudflared tunnel --url http://localhost:8000`.
3. **Demonstrate:** Share the generated URL. Move nodes on your laptop; watch them move on the judges' devices in real-time.


