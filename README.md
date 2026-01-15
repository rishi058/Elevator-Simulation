# Elevator System Simulation
> Real-time, concurrent elevator scheduling system with intelligent request handling

## 📋 Project Overview

A full-stack elevator simulation system that demonstrates concurrent request processing, real-time state synchronization, and intelligent scheduling algorithms. The system simulates a elevator serving multiple floors with external call buttons (up/down) and internal destination buttons.

**Key Highlights:**
- **Real-time Updates**: WebSocket-based live state broadcasting for instant UI updates
- **Intelligent Scheduling**: Custom heap-based algorithm for efficient floor request optimization
- **Concurrent Request Handling**: Asynchronous architecture supporting multiple simultaneous requests
- **State Synchronization**: Optimized state broadcasting with change detection to minimize network overhead

This project is ideal for understanding:
- Event-driven architectures
- Real-time communication patterns
- Scheduling algorithms and data structures
- Full-stack async/concurrent programming

---

## ✨ Features

- **Smart Request Queuing**: Dynamically prioritizes requests based on elevator direction and proximity
- **Dual-Heap Scheduling**: Separate min-heap (upward) and max-heap (downward) for optimal stop ordering
- **Door Simulation**: Realistic door open/close cycles with configurable delays
- **Visual Feedback**: Real-time floor position updates with smooth animations (frontend)
- **Button State Management**: External (up/down) and internal (floor) button tracking with visual indicators
- **WebSocket State Sync**: Efficient delta-based state updates to connected clients
- **RESTful API**: Clean endpoint design for floor requests, stops, and status queries
- **Configurable Building**: Dynamic total floor configuration via API
- **Thread-Safe Design**: Async-first architecture with concurrent request handling

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core language |
| **FastAPI** | Async web framework, REST API & WebSocket server |
| **Uvicorn** | ASGI server for production deployment |
| **Pydantic** | Request/response validation & serialization |
| **asyncio** | Concurrent task management & elevator simulation loop |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **TypeScript** | Type-safe development |
| **Vite** | Build tool & dev server |
| **Zustand** | Lightweight state management |
| **TailwindCSS 4** | Utility-first styling |
| **Axios** | HTTP client with interceptors |
| **React Router** | Client-side routing |
| **React Toastify** | Toast notifications |

### Custom Data Structures
- **MinHeap / MaxHeap**: Custom implementations for upward/downward stop prioritization

---

## 🔌 API Endpoints & WebSocket

### REST API Endpoints

**Base URL**: `http://localhost:8000/api`

#### 1. Get Elevator Status
```http
GET /api/status
```
**Response**:
```json
{
  "current_floor": 2.5,
  "direction": "UP",
  "is_door_open": false,
  "external_up_requests": [5, 7],
  "external_down_requests": [3],
  "internal_requests": [8, 10]
}
```

#### 2. Add External Request (Call Button)
```http
POST /api/request
Content-Type: application/json

{
  "floor": 5,
  "direction": "U"  // "U" for up, "D" for down
}
```
**Use Case**: Someone on floor 5 presses the UP button

**Response**:
```json
{
  "message": "Request added successfully",
  "success": true
}
```

#### 3. Add Internal Stop (Destination Button)
```http
POST /api/stop
Content-Type: application/json

{
  "floor": 7
}
```
**Use Case**: Passenger inside elevator presses floor 7 button

**Response**:
```json
{
  "message": "Stop added successfully",
  "success": true
}
```

#### 4. Configure Building Floors
```http
POST /api/total_floors
Content-Type: application/json

{
  "total_floors": 15
}
```
**Note**: Resets elevator state and creates a new elevator instance

### WebSocket Connection

**Endpoint**: `ws://localhost:8000/api/ws`

**Purpose**: Real-time elevator state updates pushed from server to clients

**Message Format** (Server → Client):
```json
{
  "current_floor": 3.75,
  "direction": "UP",
  "is_door_open": false,
  "external_up_requests": [6],
  "external_down_requests": [],
  "internal_requests": [8],
  "timestamp": 1234567.89
}
```

**Update Frequency**: Only when state changes (optimized with delta detection)

**Frontend Usage**:
```typescript
// Custom hook: useElevatorWebSocket.ts
const ws = new WebSocket('ws://localhost:8000/api/ws');
ws.onmessage = (event) => {
  const state = JSON.parse(event.data);
  updateStore(state); // Update Zustand store
};
```

---

## 🏗 Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND (React)                       │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Elevator   │  │  Floor       │  │  Internal        │    │
│  │ Component  │  │  Buttons     │  │  Buttons         │    │
│  └─────┬──────┘  └──────┬───────┘  └────────┬─────────┘    │
│        │                │                    │               │
│        └────────────────┴────────────────────┘               │
│                         │                                    │
│                  ┌──────▼───────┐                           │
│                  │ Zustand Store │◄────────────┐            │
│                  └──────┬───────┘              │            │
│                         │                      │            │
│          ┌──────────────┴─────────────┐       │            │
│          │                            │       │            │
│     ┌────▼─────┐              ┌──────▼──────┐│            │
│     │ Axios API│              │  WebSocket  ││            │
│     │ Calls    │              │  Hook       ││            │
│     └────┬─────┘              └──────┬──────┘│            │
└──────────┼─────────────────────────────┼─────────────────────┘
           │                             │
           │ HTTP                        │ WS
           │                             │
┌──────────▼─────────────────────────────▼─────────────────────┐
│                    BACKEND (FastAPI)                          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  API Router                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │  │
│  │  │ /status  │  │ /request │  │ /stop  │ /ws     │    │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬───┘ └───┬───┘    │  │
│  └───────┼─────────────┼─────────────┼─────────┼─────────┘  │
│          │             │             │         │            │
│  ┌───────▼─────────────▼─────────────▼─────┐   │            │
│  │         Methods Layer                   │   │            │
│  │  (add_request, add_stop, get_status)    │   │            │
│  └───────┬─────────────────────────────────┘   │            │
│          │                                     │            │
│  ┌───────▼─────────────────────────────────┐   │            │
│  │    Global Elevator Instance              │   │            │
│  │  ┌───────────────────────────────────┐  │   │            │
│  │  │   Elevator Class                  │  │   │            │
│  │  │  ┌──────────┐  ┌──────────────┐  │  │   │            │
│  │  │  │ MinHeap  │  │  MaxHeap     │  │  │   │            │
│  │  │  │(up_stops)│  │(down_stops)  │  │  │   │            │
│  │  │  └──────────┘  └──────────────┘  │  │   │            │
│  │  │                                   │  │   │            │
│  │  │  async run() loop:                │  │   │            │
│  │  │  - Check next floor               │  │   │            │
│  │  │  - Move elevator                  │  │   │            │
│  │  │  - Open/close doors               │  │   │            │
│  │  │  - Broadcast state ───────────────┼──┼───┘            │
│  │  └───────────────────────────────────┘  │                │
│  └──────────────────────────────────────────┘                │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │         WebSocket Manager                              │  │
│  │  - Maintains active connections                        │  │
│  │  - Broadcasts to all clients                           │  │
│  └────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

### Elevator Scheduling Algorithm

The system uses a **dual-heap approach** for intelligent request handling:

1. **Direction-Based Queuing**:
   - `MinHeap` (up_stops): Stores upward destinations in ascending order
   - `MaxHeap` (down_stops): Stores downward destinations in descending order

2. **Request Processing Logic**:
   ```python
   if elevator.direction == UP:
       service all floors in up_stops (ascending)
       then switch to down_stops (descending)
   elif elevator.direction == DOWN:
       service all floors in down_stops (descending)
       then switch to up_stops (ascending)
   ```

3. **State Flow**:
   ```
   IDLE → Request arrives → Determine direction → MOVING
   → Reach floor → DOOR_OPEN (5s delay) → DOOR_CLOSE
   → Next floor or IDLE
   ```

### Data Flow

1. **Request Path** (HTTP POST):
   ```
   User clicks button → Frontend API call → Backend endpoint
   → Elevator.add_request() → Heap insertion → State change
   → WebSocket broadcast → UI update
   ```

2. **Real-time Update Path** (WebSocket):
   ```
   Elevator.run() loop → State change detected
   → broadcast_state() → WebSocket Manager
   → All connected clients → Zustand store update
   → React re-render
   ```

---

## 🚀 How to Reproduce This Project

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **npm** or **pnpm** or **yarn**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd single-elevator-system
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn pydantic

# Run the server
python main.py
```

Server will start at: `http://localhost:8000`

**Verify**: Open `http://localhost:8000/docs` for interactive API documentation

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will start at: `http://localhost:5173`

### 4. Test the System

1. Open browser at `http://localhost:5173`
2. Click floor buttons to add requests
3. Watch elevator move in real-time
4. Open DevTools → Network → WS to see WebSocket messages

---

## 🔧 Things to Improve

### Performance & Scalability
- [ ] **Optimized Scheduling**: Implement optimized SCAN or LOOK algorithms for better efficiency
- [ ] **Request Batching**: Group nearby requests to reduce stops

### Concurrency & Safety
- [ ] **Thread-Safe Heap Operations**: Add `asyncio.Lock` to prevent race conditions during concurrent requests (see NOTES.txt)
- [ ] **Request Cancellation**: Allow users to cancel pending requests
- [ ] **Timeout Handling**: Add request expiration for abandoned calls

### Features
- [ ] **Weight/Capacity Limits**: Simulate maximum passenger capacity
- [ ] **Emergency Mode**: Priority handling for emergency floor requests
- [ ] **Maintenance Mode**: Disable elevator and queue requests
- [ ] **Floor Skipping**: Some floors only accessible with key/permission
- [ ] **Energy Optimization**: Idle position strategy (e.g., return to ground floor)

### UX Enhancements
- [ ] **Audio Feedback**: Ding sound on arrival, button click sounds
- [ ] **Arrival Predictions**: Show estimated time to arrival for each floor
- [ ] **Mobile Responsive**: Better mobile/tablet layouts

### Code Quality
- [ ] **Unit Tests**: Backend logic testing (pytest)
- [ ] **Integration Tests**: API endpoint testing
- [ ] **Frontend Tests**: Component testing (Vitest/React Testing Library)
- [ ] **Type Coverage**: Improve TypeScript strict mode compliance
- [ ] **Error Boundaries**: Better error handling in React components
- [ ] **Logging**: Structured logging with levels (debug, info, error)

### DevOps
- [ ] **Docker Compose**: Containerize frontend + backend
- [ ] **CI/CD Pipeline**: Automated testing and deployment
- [ ] **Environment Configs**: Better management of dev/prod settings
- [ ] **Monitoring**: Add metrics for request latency, elevator utilization

### Documentation
- [ ] **API Documentation**: OpenAPI/Swagger enhancements
- [ ] **Architecture Diagrams**: Sequence diagrams for request flows
- [ ] **Code Comments**: Inline documentation for complex logic
- [ ] **Video Demo**: Screen recording of system in action

---

## 📁 Project Structure

```
single-elevator-system/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── elevator/
│   │   ├── elevator.py         # Core elevator logic & run loop
│   │   ├── direction.py        # Direction enum (UP/DOWN/IDLE)
│   │   └── heap.py             # MinHeap/MaxHeap implementations
│   ├── helper/
│   │   ├── router.py           # API route definitions
│   │   ├── models.py           # Pydantic request/response models
│   │   ├── global_elevator.py  # Singleton elevator instance
│   │   └── websocket_manager.py # WebSocket connection manager
│   └── methods/
│       ├── add_request.py      # POST /request handler
│       ├── add_stop.py         # POST /stop handler
│       ├── get_status.py       # GET /status handler
│       └── set_floors.py       # POST /total_floors handler
│
└── frontend/
    ├── src/
    │   ├── App.tsx             # Main app component
    │   ├── routes.tsx          # React Router config
    │   ├── hooks/
    │   │   └── useElevatorWebSocket.ts  # WebSocket hook
    │   ├── pages/
    │   │   └── elevatorPage/
    │   │       ├── elevatorPage.tsx
    │   │       └── components/
    │   │           ├── Elevator.tsx         # Elevator shaft visualization
    │   │           ├── Floor.tsx            # Floor with call buttons
    │   │           └── InternalButtons.tsx  # Destination buttons
    │   ├── services/
    │   │   ├── elevator_api.ts       # Axios API client
    │   │   └── api_interceptor.ts    # Request/response interceptors
    │   └── store/
    │       └── elevatorStore.ts      # Zustand state management
    ├── package.json
    └── vite.config.ts
```

---

## 📝 License

This project is open-source and available for educational purposes.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests with improvements
- Share feedback on the architecture

**Happy Coding!** 🚀