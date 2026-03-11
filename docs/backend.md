To build the **GridPulse Backend** in alignment with "Vertical Construction" philosophy, we  need a technical requirements document that ensures the "Ground Floor" (ML) supports the "Penthouse" (Simulation).

Below is the phase-by-phase backend requirement breakdown derived from your **PRD** and **SRS**.

---

## Phase 1: The Ground Floor (ML & Data Engineering)

*Focus: Creating the predictive "brain" using the UCI dataset.*

* **Data Augmentation Script:** Implement a Python script to perform $3!$ (6x) permutations on the three consumer nodes ($p_2, p_3, p_4$) to expand the dataset from 10k to 60k records.
* **GRU Model Architecture:** Construct a **Keras Sequential** model using Gated Recurrent Units (GRU) to optimize for low-latency serverless execution.
* **Preprocessing Pipeline:** Develop a **Min-Max Scaler** object that must be saved alongside the model to ensure consistent input normalization during inference.
* **Success Metric:** Achieve a Mean Absolute Error (MAE) $< 0.035$ and a prediction accuracy $> 95\%$.

## Phase 2: The First Floor (Local API Development)

*Focus: Wrapping the model in a FastAPI service with strict validation.*

* **Pydantic Schema Enforcement:** Define a `GridTelemetry` model that strictly validates all 12 parameters ($\tau_{1-4}, p_{1-4}, g_{1-4}$) according to the SRS constraints.
* **Conservation Logic:** The API must programmatically verify the conservation law: $p_1 = \text{abs}(p_2 + p_3 + p_4)$.
* **Inference Endpoint (`/predict`):** Create a POST endpoint that ingests JSON, scales the data, and returns both the $stab$ index (regression) and $stabf$ label (classification).
* **Observability Integration:** Implement **Logfire** or standard logging to trace every request from entry to prediction.

## Phase 3: The Second Floor (Cloud Migration & Serverless)

*Focus: Optimizing the backend for AWS Lambda deployment.*

* **TF-Lite Conversion:** Convert the `.h5` model to `.tflite` format to stay under the 250MB Lambda limit (aiming for $< 50\text{MB}$).
* **Containerization:** Build a Docker image using the **AWS Lambda Python base image** and include the `tflite-runtime`.
* **Mangum Adapter:** Wrap the FastAPI app with the **Mangum** adapter to handle API Gateway events as ASGI logic.
* **Performance Requirement:** Ensure a warm-start inference latency of $< 200\text{ms}$.

## Phase 4: The Penthouse (Intelligence & Simulation)

*Focus: Adding the recommendation engine and grid validation.*

* **Recommendation Logic (`/recommend`):** Develop logic that triggers on "Unstable" predictions to identify the consumer node with the highest price elasticity ($g$) for load reduction.
* **OpenDSS Integration:** Use **OpenDSSDirect.py** to bridge the AI predictions with a power flow simulator.
* **Simulation API:** Create an endpoint to trigger "What-If" scenarios, demonstrating how recommendations prevent a simulated blackout.

---

### Backend Technical Stack Summary

| Component | Technology | Role |
| --- | --- | --- |
| **Model** | TensorFlow/Keras $\rightarrow$ TF-Lite | Core stability forecasting. |
| **API** | FastAPI + Pydantic | Orchestration and validation. |
| **Deployment** | Docker + AWS Lambda | Serverless scalability. |
| **Simulation** | OpenDSSDirect.py | Closed-loop validation. |
| **Monitoring** | Logfire | Traceability and performance. |