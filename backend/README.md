# Backend - Single Elevator System

A FastAPI-based microservice that simulates real-world elevator operations with multiple scheduling algorithms and real-time WebSocket updates.

## 📁 Folder Structure

```
backend/
├── main.py                          # FastAPI application entry point
├── elevator/                        # Core elevator logic
│   ├── elevator_system.py          # Main elevator controller
│   ├── base_elevator.py            # Base elevator mechanics
│   ├── stop_scheduler.py           # Stop selection logic
│   ├── direction.py                # Direction enum (UP/DOWN/IDLE)
│   ├── avl_tree.py                 # AVL tree for efficient floor lookups
│   ├── ui_state_manager.py         # UI state tracking
│   └── Scheduling Algorithms/      # Different scheduling strategies
│       ├── 01_FCFS.py              # First Come First Serve
│       ├── 02_SSTF.py              # Shortest Seek Time First
│       ├── 03_LOOK.py              # LOOK algorithm
│       ├── 04_Elevator_LOOK.py     # Enhanced LOOK (production)
│       └── NOTES.md                # Algorithm documentation
├── helper/                          # Utility modules
│   ├── global_elevator.py          # Global elevator instance
│   ├── models.py                   # Pydantic request/response models
│   ├── router.py                   # API route definitions
│   └── websocket_manager.py        # WebSocket connection manager
└── methods/                         # API endpoint handlers
    ├── add_request.py              # Handle floor requests (external)
    ├── add_stop.py                 # Handle floor stops (internal)
    ├── get_status.py               # Get current elevator state
    └── set_floors.py               # Configure building floors
```

## 🛠️ Libraries Used

- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server for production
- **Pydantic** - Data validation and serialization
- **asyncio** - Asynchronous task management

## 🚀 Setup Instructions

1. **Navigate to backend directory:**
   ```powershell
   cd backend
   ```

2. **Install dependencies:**
   ```powershell
   pip install fastapi uvicorn
   ```

3. **Run the server:**
   ```powershell
   python main.py
   ```
   Or with Uvicorn directly:
   ```powershell
   uvicorn main:app --reload --port 8000
   ```

4. **Access the API:**
   - Server: `http://localhost:8000`
   - WebSocket: `ws://localhost:8000/api/ws`
   - Docs: `http://localhost:8000/docs` (Swagger UI)

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────┐      ┌─────────────┐      ┌──────────────┐  │
│  │   REST API │◄─────┤   Router    ├─────►│  WebSocket   │  │
│  │  Endpoints │      │  (helper/)  │      │   Manager    │  │
│  └─────┬──────┘      └──────┬──────┘      └──────┬───────┘  │
│        │                    │                    │          │
│        └────────────────────┼────────────────────┘          │
│                             ▼                               │
│                  ┌─────────────────────┐                    │
│                  │  Methods (handlers) │                    │
│                  │  • add_request()    │                    │
│                  │  • add_stop()       │                    │
│                  │  • get_status()     │                    │
│                  │  • set_floors()     │                    │
│                  └──────────┬──────────┘                    │
│                             ▼                               │
│                  ┌─────────────────────┐                    │
│                  │  Global Elevator    │                    │
│                  │   (Singleton)       │                    │
│                  └──────────┬──────────┘                    │
│                             ▼                               │
│              ┌──────────────────────────────┐               │
│              │    Elevator Controller       │               │
│              │  • run() - Main loop         │               │
│              │  • broadcast_state()         │               │
│              │  • Interrupt handling        │               │
│              └──────────┬───────────────────┘               │
│                         ▼                                   │
│         ┌───────────────────────────────────┐               │
│         │   Stop Scheduler (Algorithm)     │               │
│         │  • AVL Tree for fast lookups     │               │
│         │  • get_next_stop()               │               │
│         │  • Direction-aware selection    │               │
│         └───────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Lifespan Manager** - Handles elevator task startup/shutdown
- **CORS Middleware** - Enables cross-origin requests
- **Async Elevator Loop** - Runs continuously in background
- **AVL Tree** - O(log n) floor insertion/lookup
- **WebSocket Broadcasting** - Real-time state updates to all clients

## 📡 API Documentation

### **GET** `/api/status`
Get current elevator state.

**Response:**
```json
{
  "current_floor": 5,
  "direction": "U",
  "is_door_open": false,
  "external_up_requests": [7, 9],
  "external_down_requests": [3],
  "internal_requests": [8, 10]
}
```

---

### **POST** `/api/request`
Add an external floor request with direction.

**Request Body:**
```json
{
  "request": "7U"  // Floor 7, going Up
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Request added successfully"
}
```

---

### **POST** `/api/stop`
Add an internal elevator stop.

**Request Body:**
```json
{
  "stop": 8  // Go to floor 8
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Stop added successfully"
}
```

---

### **POST** `/api/total_floors`
Configure total building floors.

**Request Body:**
```json
{
  "total_floors": 15
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Total floors set successfully"
}
```

---

### **WebSocket** `/api/ws`
Real-time elevator state updates.

**Message Format:**
```json
{
  "current_floor": 5.4,
  "direction": "U",
  "is_door_open": false,
  "external_up_requests": [7, 9],
  "external_down_requests": [3],
  "internal_requests": [8],
  "timestamp": 1234567.89
}
```

## 📝 Summary

This backend implements a production-grade elevator control system with:

- **4 Scheduling Algorithms** (FCFS, SSTF, LOOK, Elevator-LOOK)
- **Interrupt Handling** - Dynamic stop re-prioritization
- **Efficient Data Structures** - AVL tree for O(log n) operations
- **Async Architecture** - Non-blocking operations with FastAPI
- **Scalable Design** - Singleton pattern for global state management

The system simulates realistic elevator behavior with door delays, gradual movement (0.2 floors/tick), and smart scheduling that minimizes wait times while preventing starvation.
