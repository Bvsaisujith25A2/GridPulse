To build the **GridPulse Penthouse** (Frontend) in alignment with  "Vertical Construction" philosophy, you need a structured requirements document that mirrors the backend's progression.

Based on the **PRD** and **SRS**, here is the requirement breakdown for the frontend, organized into implementation phases.

---

## Phase 1: The Foundation (Mock Data & Static UI)

*Focus: Mapping the 4-node star topology and defining the data shape.*

* **Node Visualization:** Create a static SVG or Canvas-based layout representing the 1 producer and 3 consumer nodes.
* **Telemetry Forms:** Build a data entry interface using the **Pydantic-defined constraints** (e.g., $\tau_{1-4} \in [0.5, 10]$, $p_2 \in [-2.0, -0.5]$).
* **Mock State Management:** Implement a local state (using React Context or Redux) to handle "Stable" vs. "Unstable" UI themes without a live API.
* **Success Metric:** UI correctly rejects manual inputs that violate the conservation law ($p_1 = \text{abs}(p_2 + p_3 + p_4)$).

## Phase 2: The Integration (Live API Connectivity)

*Focus: Connecting to the Stage 2/3 FastAPI/Lambda backend.*

* **Async Data Fetching:** Implement hooks to POST telemetry to the `/predict` endpoint.
* **Stability Gauges:** Integrated radial gauges or line charts to visualize the $stab$ index (regression) and $stabf$ label (classification).
* **Latency Monitoring:** A "System Health" footer that displays the round-trip time (RTT) for each inference request to monitor the $<200\text{ms}$ performance requirement.
* **Error Handling:** Visual toast notifications for API validation errors or Lambda cold-start timeouts.

## Phase 3: The Command Center (Recommendations & Simulation)

*Focus: Implementing the Stage 4 "Intelligent Load Balancing" logic.*

* **Recommendation Engine UI:** A dedicated panel that activates when `stabf == 'unstable'`. It must highlight the consumer node with the highest price elasticity ($g$) and display the "Action Required" message.
* **Simulation Controls:** A "Run What-If Scenario" button that triggers the **OpenDSSDirect.py** bridge to show how grid recovery looks in real-time.
* **Heat Map Logic:** Dynamically update node colors based on the stability index:
* **Green:** $stab < 0$ (Stable)
* **Yellow:** $0 < stab < 0.01$ (Marginal Risk)
* **Red:** $stab > 0.01$ (High Blackout Risk).



## Phase 4: The Polished Penthouse (Observability & UX)

*Focus: Professional-grade monitoring and hackathon "Wow" factors.*

* **Logfire Trace Viewer:** An admin-only tab that displays structured logs/traces from the backend to verify model transparency.
* **Historical Trends:** A "Persistence" view showing the last 50 telemetry snapshots to identify patterns leading to instability.
* **Responsive Design:** Optimization for "Grid Operator" tablet views for field monitoring.

---

### Technical Requirements Summary

| Component | Technology | Requirement |
| --- | --- | --- |
| **State Management** | React (Hooks/Context) | Must sync with the 12-parameter telemetry schema. |
| **Charts/Visuals** | Recharts or D3.js | Real-time plotting of the stability index $stab$. |
| **Validation** | Formik or React Hook Form | Must mirror the **Pydantic** constraints defined in the SRS. |
| **Communication** | Axios / Fetch | Interface with the **Mangum**-wrapped AWS Lambda handler. |

