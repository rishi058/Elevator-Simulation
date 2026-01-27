# 🏢 Multi-Elevator Smart Control System

## 🚀 Overview

The **Multi-Elevator System** is an advanced, full-stack simulation of a modern vertical transportation network. It is designed to model the complexity of "Collective Control" logic used in skyscrapers, where multiple elevators must coordinate to serve thousands of requests efficiently.

This project is not just a visual demo; it is a **distributed system** composed of independent microservices (Frontend & Backend) communicating in real-time. It solves the **"Knapsack-like" optimization problem** of assigning passengers to cars to minimize average wait time (AWT) and system energy consumption.

**Key Technical Highlights:**
- **Asynchronous IO:** Handles 1000+ concurrent requests using Python's `asyncio` loop.
- **Data Structure Optimization:** Uses AVL Trees for `O(log n)` stop insertion, preventing performance degradation as queues grow.
- **Dynamic Dispatching:** Implements a "stolen request" algorithm where elevators can re-assign tasks if a better candidate appears mid-flight.
- **State Synchronization:** Uses a push-based WebSocket architecture to ensure the UI is physically accurate within <100ms latency.

---

## 🏗 High-Level Architecture

The system follows a clean **Microservices Architecture**, separating the "Brain" (Decision Logic) from the "View" (Visualization).

```mermaid
graph TD
    subgraph Client_Layer["Client Layer"]
        Browser["User Browser - React SPA"]
    end

    subgraph Network_Layer["Network Layer"]
        HTTP["REST API (Command)"]
        WS["WebSocket (Status Stream)"]
    end

    subgraph Backend_Core["Backend Core - The Brain"]
        API["FastAPI Gateway"]
        Dispatcher["Collective Dispatch Controller"]

        subgraph Agent_Cluster["Agent Cluster"]
            E1["Elevator 0 - Independent Loop"]
            E2["Elevator 1 - Independent Loop"]
            E3["Elevator 2 - Independent Loop"]
        end

        State["Global State Manager"]
    end

    Browser -->|POST /api/request| API
    API -->|queue_request()| Dispatcher
    Dispatcher -->|assign_best()| E1
    Dispatcher -->|assign_best()| E2
    Dispatcher -->|assign_best()| E3
    E1 -->|update_position()| State
    State -->|broadcast_json()| WS
    WS -->|push_payload| Browser
```

---

## 🌍 Real-World Applications

This project serves as a reference implementation for several high-level software engineering concepts.

### 1. **For System Design Interviews (SDE-2 / Senior)**
   - **Concurrency:** How to manage shared state (the request queue) without race conditions using async primitives.
   - **Scalability:** The "Controller" pattern matches how Kubernetes orchestrates pods or how Uber matches riders to drivers.
   - **Protocol Design:** Why optimize JSON payloads over WebSockets instead of Long-Polling.

### 2. **For IoT & Control Systems**
   - **Simulation:** Can be used to test new dispatch algorithms (e.g., Destination Dispatch vs. Hall Call) before deploying firmware to physical PLCs.
   - **Digital Twin:** The frontend can serve as a "Digital Twin" for a real building if connected to physical elevator sensors via MQTT.

### 3. **Commercial Use Cases**
   - **Traffic Analysis:** Simulating peak morning rush hour logic to determine the optimal number of elevators for a new building design.
   - **Energy Optimization:** Testing "Green Mode" algorithms that prioritize gathering passengers to strict zones to save motor movement.

---

## 📚 Detailed Documentation

We have split the technical deep-dives into their respective directories to keep things organized.

| Module | Description | Technical Focus | Link |
| :--- | :--- | :--- | :--- |
| **Backend** | The "Brain" of the system. | AVL Trees, Cost Functions, Dispatch Algorithms, FastAPI | [Backend Docs](./backend/README.md) |
| **Frontend** | The "View" dashboard. | React, Zustand, Framer Motion, WebSockets | [Frontend Docs](./frontend/README.md) |

---

## 📂 Project Directory Structure

```bash
multi-elevator-system/
├── backend/                   # [MICROSERVICE] Python/FastAPI
│   ├── elevator/              # Core Domain Logic
│   │   ├── avl_tree.py        # Custom BST Implementation
│   │   ├── elevator_system.py # Individual Elevator State Machine
│   │   └── multi_elevator_system.py # Global Dispatcher Logic
│   ├── helper/                # Infrastructure
│   │   └── websocket_manager.py # Real-time Broadcaster
│   ├── main.py                # Application Entry Point
│   └── tests/                 # Unit & Logic Tests
│
├── frontend/                  # [MICROSERVICE] React/Vite
│   ├── src/
│   │   ├── components/        # Visual Components (Grid, ElevatorNode)
│   │   ├── store/             # Global State (Zustand)
│   │   └── api/               # Network Clients (Axios, WS)
│   └── public/                # Static Assets
│
├── tests/                     # [INTEGRATION] End-to-End Scenarios
│   └── test_scenarios.py      # Script running complex user flows
│
└── README.md                  # System Overview
```

---

## 🚀 Getting Started

To run the full simulation locally, you will need two terminal windows.

### Terminal 1: Start the Brain (Backend)
```bash
cd backend
# Recommended: Create a venv first
pip install -r requirements.txt  # or: pip install fastapi uvicorn
python main.py
```
*Server will start on `http://localhost:8000`*

### Terminal 2: Start the UI (Frontend)
```bash
cd frontend
npm install
npm run dev
```
*UI will open at `http://localhost:5173`*

---

## 🧠 algorithmic Deep Dive (The "SCAN" Logic)

The system does not simply go to the nearest call. It uses a variation of the **SCAN (Elevator) Algorithm** combined with a **Cost-Minimization Function**.

**The Decision Hierarchy:**
1.  **Safety First:** If doors are opening/closing, wait.
2.  **Internal Priority:** If a passenger *inside* pressed a button, go there first (strictly obeying direction).
3.  **Directional Commitment (Phase 1):** If moving UP, continue serving all UP requests located *above* the car.
4.  **Turnaround (Phase 2):** Only switch direction once all requests in the current direction are exhausted.

**Cost Function ($C$):**
When you press a button, the system calculates $C$ for all 3 elevators:
```python
Cost = (Distance * TravelSpeed) + (StopsPenalty * 5s) + (TurnPenalty * 30s)
```
The elevator with the **lowest $C$** gets the job. If, 2 seconds later, another elevator becomes free and has a significantly lower $C$ (e.g., >5s improvement), the system **dynamically re-assigns** the request to the new elevator.
