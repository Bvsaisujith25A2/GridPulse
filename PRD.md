This Product Requirements Document (PRD) for **Project GridPulse** is structured using a "Vertical Construction" philosophy. Each stage provides a functional "floor" that supports the weight of the next, ensuring that you build upon your code rather than rewriting it.

---

# PRD: Project GridPulse (AI-Driven Smart Grid Stability)

## 1. Project Overview

GridPulse is a high-fidelity stability forecasting system designed for decentralized smart grids. It utilizes deep learning to predict "Blackout Risks" 30 minutes in advance based on node telemetry (reaction times, power balance, and price elasticity).

## 2. Implementation Roadmap

### **Stage 1: The Ground Floor (Data Engineering & Core ML)**

*Focus: Creating the predictive "brain" and the data pipeline.*

* **Objective:** Develop a robust LSTM/GRU model trained on the augmented UCI Electrical Grid Stability dataset.
* **Key Requirements:**
* **Data Augmentation:** Implement a script to perform $3!$ (6x) permutations on the 3 consumer nodes of the UCI dataset, expanding the 10,000 instances to 60,000 to improve generalization.


* **Model Architecture:** Build a Keras Sequential model. While LSTMs capture temporal dependencies well, consider a **GRU (Gated Recurrent Unit)** for this stage to ensure lower latency and smaller memory footprint for the future serverless layer.


* **Artifact Generation:** The output must be a versioned `.h5` or `SavedModel` file and a scaler object (Min-Max) for consistent input normalization.


* **"Forward-Proofing":** Use standard Keras/TensorFlow so the model can be converted to TF-Lite later without changing the training logic.

### **Stage 2: The First Floor (The Local API Service)**

*Focus: Wrapping the brain in a communicative interface.*

* **Objective:** Build a FastAPI backend that serves the model for real-time inference.
* **Key Requirements:**
* **Schema Definition:** Use **Pydantic** to define strict data models for grid telemetry (e.g., `tau[1-4]`, `p[1-4]`, `g[1-4]`). This ensures the API rejects malformed data before it hits the model.
* **Inference Endpoint:** Create a `/predict` POST endpoint. The logic should:
1. Receive JSON telemetry.
2. Scale the data using the Stage 1 scaler.
3. Return a `stab` index (regression) and a `stabf` label (stable/unstable).




* **Observability:** Integrate **Logfire** or standard logging to track every prediction request and model performance in real-time.


* **"Forward-Proofing":** Developing with FastAPI allows the same code to run in Stage 3 using the Mangum adapter.

### **Stage 3: The Second Floor (Serverless & Cloud Scaling)**

*Focus: Moving from "local" to "global" availability.*

* **Objective:** Deploy the FastAPI app to AWS Lambda for pay-per-request scaling.
* **Key Requirements:**
* **TF-Lite Conversion:** Convert the Stage 1 model to `.tflite`. This reduces the size from ~500MB+ to under 50MB, crucial for bypassing Lambda's package limits.


* **Containerization:** Use the **AWS Lambda Python base image** to build a Docker container. Install the `tflite-runtime` (use the raw wheel link to avoid build errors).


* **Mangum Adapter:** Wrap the FastAPI `app` object with `handler = Mangum(app)` to bridge the gap between API Gateway events and FastAPI's ASGI logic.


* **AWS ECR/Lambda:** Push the image to Amazon ECR and link it to a Lambda function with at least 1024MB RAM (for faster CPU allocation during inference).




* **"Forward-Proofing":** Containerization ensures your local environment perfectly matches the cloud environment.

### **Stage 4: The Penthouse (Intelligent Load Balancing & Simulation)**

*Focus: Adding active decision-making and grid validation.*

* **Objective:** Implement a recommendation engine and validate it against a grid simulator.
* **Key Requirements:**
* **Recommendation Logic:** Add a `/recommend` endpoint that, if a node is predicted as "unstable," identifies which consumer node ($p_2, p_3, p_4$) has the highest price elasticity ($g$) and recommends a load reduction.


* **Simulation Bridge:** Use **OpenDSSDirect.py** to run "What-If" scenarios. Script a simulated blackout in OpenDSS and show how the GridPulse recommendation prevents the collapse by adjusting node consumption.


* **Dashboard UI:** (Optional Hackathon "Wow" Factor) Create a React dashboard that polls the Stage 3 API and visualizes the grid "Heat Map" based on stability indices.





---

## 3. Technical Stack Summary

| Layer | Technology | Purpose |
| --- | --- | --- |
| **Data** | UCI Grid Stability (Augmented) | Training source for 4-node star topology. |
| **Model** | Keras/TensorFlow (converted to TF-Lite) | Core predictive logic for stability. |
| **Backend** | FastAPI + Pydantic | API orchestration and data validation. |
| **Deployment** | Docker + AWS ECR + AWS Lambda | Elastic, serverless hosting. |
| **Simulator** | OpenDSSDirect.py | Validation of load-balancing impact. |

## 4. Input Telemetry Data Schema (Pydantic Example)

```python
from pydantic import BaseModel, Field

class GridTelemetry(BaseModel):
    tau1: float = Field(..., description="Producer reaction time", ge=0.5, le=10)
    p2: float = Field(..., description="Consumer 1 power balance", ge=-2.0, le=-0.5)
    g3: float = Field(..., description="Consumer 2 price elasticity", ge=0.05, le=1.0)
    #... include all 12 parameters (tau1-4, p1-4, g1-4)

```

## 5. Success Metrics

* **Prediction Accuracy:** $>95\%$ on the augmented test set.


* **Inference Latency:** $<200\text{ms}$ per request (warm start).


* **Recovery Efficiency:** Simulation shows a $30\%$ reduction in blackout risk when load-balancing recommendations are followed.