# Single Elevator System

A full-stack elevator simulation system implementing real-world scheduling algorithms, built with FastAPI and React.

## 📸 DEMO 

![Elevator System Demo](https://github.com/rishi058/Elevator-Simulation/tree/single-elevator/frontend/public/demo.gif)

## 📋 Project Summary

This project simulates a single elevator system with intelligent scheduling algorithms inspired by disk scheduling strategies (FCFS, SSTF, LOOK, Elevator-LOOK). It features real-time visualization, WebSocket-based state synchronization, and interrupt-driven request handling.

**Key Highlights:**
- 4 scheduling algorithms with detailed documentation
- Real-time WebSocket updates 
- Interrupt handling for dynamic stop re-prioritization
- Production-ready architecture with TypeScript and Python

## 🌍 Real-World Applications

### **For Whom:**
- **Interview Preparation** - SDE-2/Senior engineer system design practice
- **IoT Platform Developers** - Real-time control systems

### **Use Cases:**
- **Commercial Buildings** - Optimize tenant wait times

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

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Zustand** - State management
- **Tailwind CSS** - Styling
- **Vite** - Build tool

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

## 📝 License

This project is for educational purposes.

---

**Built with ❤️ for learning system design and real-time web applications.**
