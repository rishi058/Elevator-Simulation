# Single Elevator System

A full-stack elevator simulation system implementing real-world scheduling algorithms, built with FastAPI and React.

## 📋 Project Summary

This project simulates a single elevator system with intelligent scheduling algorithms inspired by disk scheduling strategies (FCFS, SSTF, LOOK, Elevator-LOOK). It features real-time visualization, WebSocket-based state synchronization, and interrupt-driven request handling.

**Key Highlights:**
- 4 scheduling algorithms with detailed documentation
- Real-time WebSocket updates (0.2s intervals)
- AVL tree for O(log n) floor lookups
- Optimistic UI updates with server validation
- Interrupt handling for dynamic stop re-prioritization
- Production-ready architecture with TypeScript and Python

## 🌍 Real-World Applications

### **For Whom:**
- **Building Management Systems** - Smart elevators in commercial buildings
- **IoT Platform Developers** - Real-time control systems
- **System Design Learners** - Study distributed systems and scheduling algorithms
- **Interview Preparation** - SDE-2/Senior engineer system design practice

### **Use Cases:**
- **Commercial Buildings** - Optimize tenant wait times
- **Hospitals** - Priority-based floor servicing
- **Hotels** - Handle peak traffic (check-in/check-out)
- **Residential Towers** - Reduce energy consumption
- **Educational Labs** - Teach OS scheduling concepts

### **SDE-2 System Design Concepts:**
This project demonstrates:
- **Microservice Architecture** - Decoupled frontend/backend
- **Real-time Communication** - WebSocket protocol implementation
- **State Management** - Zustand (client) + Singleton pattern (server)
- **Algorithm Optimization** - AVL trees, interrupt handling
- **Async Programming** - FastAPI coroutines, React hooks
- **API Design** - RESTful endpoints with Pydantic validation
- **Scalability** - Stateless requests, connection pooling

## 🗂️ Repository Structure

```
single-elevator-system/
├── backend/                 # FastAPI microservice
│   ├── README.md           # Backend-specific documentation
│   ├── elevator/           # Core elevator logic & algorithms
│   ├── helper/             # Utilities (WebSocket, router, models)
│   └── methods/            # API endpoint handlers
│
├── frontend/               # React + TypeScript UI
│   ├── README.md          # Frontend-specific documentation
│   └── src/
│       ├── pages/         # Route components
│       ├── hooks/         # Custom React hooks
│       ├── store/         # Zustand state management
│       └── services/      # API integration
│
└── README.md              # This file
```

## 📚 Documentation

- **[Backend Documentation](./backend/README.md)** - FastAPI setup, API docs, architecture
- **[Frontend Documentation](./frontend/README.md)** - React setup, state management, WebSocket
- **[Scheduling Algorithms](./backend/elevator/Scheduling%20Algorithms/NOTES.md)** - Algorithm comparison & analysis 
- **[Manual TESTs](./backend/TESTS.md)** - Sequences of Requests and Stops to check functioning.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### 1. Start Backend
```powershell
cd backend
pip install fastapi uvicorn
python main.py
```
Backend runs on `http://localhost:8000`

### 2. Start Frontend
```powershell
cd frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

### 3. Access Application
Open browser to `http://localhost:5173` and interact with the elevator system.

## 🎥 Demo

> **Example Usage:**
> 
> ![Elevator Demo](./demo.gif)
> 
> *Add a GIF showing:*
> - Elevator moving between floors
> - Button states changing
> - Real-time request handling
> - Door open/close animations

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Async web framework
- **Uvicorn** - ASGI server
- **WebSocket** - Real-time communication
- **AVL Tree** - Efficient data structure

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Zustand** - State management
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **Framer Motion** - Animations

## 🔧 Features

✅ **4 Scheduling Algorithms** (FCFS, SSTF, LOOK, Elevator-LOOK)  
✅ **Real-time Updates** via WebSocket  
✅ **Optimistic UI** for instant feedback  
✅ **Auto-reconnection** with exponential backoff  
✅ **Interrupt Handling** for request re-prioritization  
✅ **Door Animations** with realistic timing  
✅ **AVL Tree** for O(log n) operations  
✅ **TypeScript** for type safety  
✅ **Responsive Design** for mobile/desktop  

## 📊 System Design Highlights

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (Client)                       │
│  ┌────────────────┐        WebSocket         ┌───────────┐ │
│  │  React UI      │◄──────────────────────────┤  Zustand  │ │
│  │  (Components)  │      Real-time State      │  Store    │ │
│  └────────┬───────┘                           └─────┬─────┘ │
│           │                                         │       │
│           │ REST API (Axios)                        │       │
└───────────┼─────────────────────────────────────────┼───────┘
            │                                         │
            ▼                                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌──────────┐      ┌────────────┐      ┌────────────────┐  │
│  │  Router  │─────►│  Methods   │─────►│ Global Elevator│  │
│  │  (API)   │      │ (Handlers) │      │   (Singleton)  │  │
│  └──────────┘      └────────────┘      └────────┬───────┘  │
│                                                  │          │
│                                                  ▼          │
│                                    ┌──────────────────────┐ │
│                                    │ Elevator Controller  │ │
│                                    │  • async run()       │ │
│                                    │  • broadcast_state() │ │
│                                    │  • AVL Tree          │ │
│                                    │  • Scheduling Algo   │ │
│                                    └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 System Design Concepts Covered

1. **Microservices** - Independent frontend/backend deployment
2. **Real-time Sync** - WebSocket bidirectional communication
3. **State Management** - Centralized state with Zustand/Singleton
4. **Async Processing** - Non-blocking I/O with FastAPI/React
5. **Algorithm Optimization** - AVL trees for O(log n) complexity
6. **API Design** - RESTful principles with Pydantic validation
7. **Error Handling** - Graceful degradation and reconnection
8. **Scalability** - Stateless API design for horizontal scaling

## 📝 License

This project is for educational purposes.

---

**Built with ❤️ for learning system design and real-time web applications.**
