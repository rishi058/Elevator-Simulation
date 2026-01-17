# Elevator System Architecture

A modular, object-oriented elevator control system built with Python and asyncio, featuring hierarchical inheritance for clean separation of concerns.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INHERITANCE CHAIN                        │
└─────────────────────────────────────────────────────────────┘

     ┌──────────────────┐
     │  BaseElevator    │  ← Foundation Layer
     │                  │
     │ • current_floor  │
     │ • direction      │
     │ • is_door_open   │
     │ • open_door()    │
     └────────┬─────────┘
              │
              │ inherits
              ▼
     ┌──────────────────┐
     │  StopScheduler   │  ← Algorithm Layer
     │                  │
     │ • up_stops       │
     │ • down_stops     │
     │ • add_request()  │
     │ • add_stop()     │
     │ • get_next_stop()│
     └────────┬─────────┘
              │
              │ inherits
              ▼
     ┌──────────────────┐
     │ UIStateManager   │  ← Presentation Layer
     │                  │
     │ • ui_external_*  │
     │ • ui_internal_*  │
     │ • update_ui_*()  │
     └────────┬─────────┘
              │
              │ inherits
              ▼
     ┌──────────────────┐
     │    Elevator      │  ← Orchestration Layer
     │                  │
     │ • ws_manager     │
     │ • run()          │
     │ • broadcast()    │
     └──────────────────┘
```

## 📦 Class Responsibilities

### 1. BaseElevator (Foundation Layer)
**Purpose**: Core elevator state and basic operations

**Responsibilities**:
- Track current floor position (can be fractional during movement)
- Manage elevator direction (UP, DOWN, IDLE)
- Handle door state (open/closed)
- Provide door open/close operations
- Calculate effective direction

**Key Attributes**:
```python
current_floor: float      # 0.0 to total_floors
direction: Direction      # UP, DOWN, or IDLE
is_door_open: bool
moving_direction: Direction  # Last direction before going IDLE
total_floors: int
```

**Key Methods**:
- `open_door()` - Async door open operation (5 seconds)
- `get_effective_direction()` - Returns actual movement direction

---

### 2. StopScheduler (Algorithm Layer)
**Purpose**: Intelligent stop scheduling using heap-based algorithm

**Responsibilities**:
- Manage stop requests using min/max heaps for efficiency
- Implement elevator algorithm (SCAN/LOOK algorithm variant)
- Handle both internal (passenger) and external (call button) requests
- Optimize stop order for efficiency

**Key Attributes**:
```python
up_stops: MinHeap      # Stops while going up (sorted ascending)
down_stops: MaxHeap    # Stops while going down (sorted descending)
```

**Key Methods**:
- `add_request(floor, direction)` - Add external call button request
- `add_stop(floor)` - Add internal passenger request
- `get_next_stop(delete)` - Get next stop in optimal order

**Algorithm Logic**:
```
IF going UP:
  → Serve all UP requests ahead
  → Then reverse to serve DOWN requests
  
IF going DOWN:
  → Serve all DOWN requests ahead
  → Then reverse to serve UP requests
  
IF IDLE:
  → Prefer UP direction
  → Choose nearest request
```

---

### 3. UIStateManager (Presentation Layer)
**Purpose**: Track UI state for button illumination

**Responsibilities**:
- Maintain sets of active button requests
- Update UI state when stops are served
- Provide button on/off state tracking

**Key Attributes**:
```python
ui_external_up_requests: set    # Floor buttons (UP)
ui_external_down_requests: set  # Floor buttons (DOWN)
ui_internal_requests: set       # Cabin buttons
```

**Key Methods**:
- `update_ui_requests()` - Clear served requests from UI
- Overrides `add_request()` and `add_stop()` to track UI state

---

### 4. Elevator (Orchestration Layer)
**Purpose**: Main control loop and WebSocket integration

**Responsibilities**:
- Run the main elevator control loop
- Coordinate all subsystems
- Broadcast state updates via WebSocket
- Handle movement between floors
- Manage cleanup

**Key Attributes**:
```python
ws_manager: WebSocketManager  # For real-time updates
prev_state: dict              # For state change detection
```

**Key Methods**:
- `run()` - Main async control loop
- `broadcast_state()` - Send updates to connected clients
- `set_websocket_manager()` - Configure WebSocket connection
- `cleanup()` - Resource cleanup

---

## 🎯 Design Patterns Used

### Hierarchical Inheritance
Each class builds upon the previous, adding one layer of responsibility:
```
Base State → Scheduling → UI Tracking → Orchestration
```

### Single Responsibility Principle
- **BaseElevator**: State management
- **StopScheduler**: Scheduling algorithm
- **UIStateManager**: UI state
- **Elevator**: System orchestration

### Template Method Pattern
Base classes define structure, derived classes extend behavior:
```python
# UIStateManager extends StopScheduler behavior
def add_request(self, floor, direction):
    self.ui_external_requests.add(floor)  # UI tracking
    super().add_request(floor, direction)  # Scheduling logic
```

---

## 🚀 Usage Example

```python
from elevator import Elevator
from websocket_manager import WebSocketManager

# Initialize elevator
elevator = Elevator(total_floors=10)

# Set up WebSocket broadcasting
ws_manager = WebSocketManager()
elevator.set_websocket_manager(ws_manager)

# Add requests
elevator.add_request(5, "UP")      # External: Floor 5, going UP
elevator.add_stop(8)                # Internal: Go to floor 8

# Start the elevator
await elevator.run()
```

---

## 🔄 Elevator State Flow

```
┌─────────┐
│  IDLE   │ ◄─────────────────┐
└────┬────┘                   │
     │ Request received       │
     ▼                        │
┌─────────┐                   │
│ MOVING  │ ──────────────────┤
└────┬────┘  No more stops    │
     │                        │
     │ Reached floor          │
     ▼                        │
┌─────────┐                   │
│ STOPPED │                   │
│ Door    │ ──────────────────┘
│ Open    │  Door closes
└─────────┘
```

---

## 📊 Broadcast State Schema

The elevator broadcasts the following state via WebSocket:

```javascript
{
  "current_floor": 3.4,              // Float during movement
  "direction": "UP",                 // "UP", "DOWN", or "IDLE"
  "is_door_open": false,
  "external_up_requests": [5, 7, 9],
  "external_down_requests": [2],
  "internal_requests": [8, 10],
  "timestamp": 1234567890.123
}
```

---

## ⚙️ Movement Mechanics

```
Floor Movement:
├─ Speed: 0.2 floors per second
├─ Time per floor: 5 seconds
├─ Door open time: 5 seconds
└─ Fractional floors tracked during movement

Example:
Floor 1.0 → 1.2 → 1.4 → 1.6 → 1.8 → 2.0
  (1s)   (1s)   (1s)   (1s)   (1s)
```

---

## 🧹 Cleanup

```python
# Proper cleanup
elevator.cleanup()

# Clears:
# - All stop queues
# - UI state sets
# - WebSocket connection
# - State history
```

---

## 🎓 Why This Architecture?

### ✅ Advantages

1. **Modularity**: Each class has one clear purpose
2. **Testability**: Test each layer independently
3. **Maintainability**: Changes isolated to specific classes
4. **Extensibility**: Easy to add new features at appropriate layer
5. **Readability**: Clear hierarchy shows system structure

### 🔧 Future Extensions

Easy to add new layers:
```
Elevator → SafetyMonitor → MaintenanceTracker
         → EnergyOptimizer → Analytics
```

---

## 📝 Notes

- Uses asyncio for concurrent operations
- Heap-based scheduling for O(log n) efficiency
- WebSocket broadcasting with state deduplication
- Fractional floor tracking for smooth UI updates
- Immutable state snapshots prevent race conditions

---

## 🏛️ Class Hierarchy Visual

```
        ┌───────────────────────────────────┐
        │         ELEVATOR SYSTEM           │
        └───────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    ┌───────┐      ┌────────┐     ┌─────────┐
    │ State │      │Schedule│     │   UI    │
    │Manager│ ───► │Algorithm──►  │ Manager │
    └───────┘      └────────┘     └─────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
                ┌───────────────┐
                │  Orchestrator │
                └───────────────┘
```

---

**Built with**: Python 3.8+, asyncio, type hints  
**Architecture**: Hierarchical Inheritance with Single Responsibility  
**Algorithm**: Modified SCAN/LOOK elevator algorithm