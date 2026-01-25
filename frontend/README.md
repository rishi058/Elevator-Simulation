# Frontend - Single Elevator System

A real-time elevator visualization built with React, TypeScript, and Tailwind CSS featuring WebSocket integration and smooth animations.

## 📸 DEMO 
![Elevator System Demo](https://github.com/user-attachments/assets/69bcbe19-32ef-43d7-9169-055935ae29aa)

## 📁 Folder Structure

```
frontend/
├── index.html                       # Entry HTML file
├── vite.config.ts                   # Vite build configuration
├── tsconfig.json                    # TypeScript configuration
├── package.json                     # Dependencies & scripts
├── src/
│   ├── main.tsx                     # Application entry point
│   ├── App.tsx                      # Root component with routing
│   ├── routes.tsx                   # Route definitions
│   ├── pages/                       # Page components
│   │   ├── homePage/                # Landing page
│   │   │   └── homePage.tsx
│   │   └── elevatorPage/            # Main elevator UI
│   │       ├── elevatorPage.tsx
│   │       └── components/
│   │           ├── Elevator.tsx     # Elevator shaft & cabin
│   │           ├── Floor.tsx        # Individual floor buttons
│   │           └── InternalButtons.tsx  # Inside elevator panel
│   ├── hooks/                       # Custom React hooks
│   │   └── useElevatorWebSocket.ts  # WebSocket connection logic
│   ├── services/                    # API layer
│   │   ├── api_interceptor.ts       # Axios configuration
│   │   └── elevator_api.ts          # API methods
│   ├── store/                       # State management
│   │   └── elevatorStore.ts         # Zustand store
│   └── utils/                       # Helpers
│       ├── button_state.ts          # Button styling logic
│       └── toast.ts                 # Toast notifications
└── public/                          # Static assets
```

## 🛠️ Libraries Used

- **React 19** - UI library with latest features
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first styling
- **Zustand** - Lightweight state management
- **Axios** - HTTP client for API calls
- **React Router** - Client-side routing
- **React Toastify** - Toast notifications

## 🚀 Setup Instructions

1. **Navigate to frontend directory:**
   ```powershell
   cd frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Start development server:**
   ```powershell
   npm run dev
   ```

4. **Access the application:**
   - Open browser: `http://localhost:5173`
   - Ensure backend is running on `http://localhost:8000`

## 🏗️ Architecture

### State Management (Zustand)
```
┌──────────────────────────────────────────────┐
│         Zustand Store (elevatorStore)        │
├──────────────────────────────────────────────┤
│  State:                                      │
│   • current_floor: number                    │
│   • direction: "U" | "D" | "IDLE"            │
│   • is_door_open: boolean                    │
│   • external_up_requests: number[]           │
│   • external_down_requests: number[]         │
│   • internal_requests: number[]              │
│                                              │
│  Actions:                                    │
│   • updateElevatorStatus()                   │
│   • addInternalStop() - Optimistic update   │
└──────────────────────────────────────────────┘
```

### WebSocket Flow
```
┌─────────────┐        WebSocket         ┌──────────────┐
│   Backend   │◄────────────────────────►│  useElevator │
│ (Port 8000) │   ws://localhost:8000    │   WebSocket  │
└─────────────┘                          └──────┬───────┘
                                                │
                                                ▼
                                    ┌───────────────────┐
                                    │  Parse & Update   │
                                    │  Zustand Store    │
                                    └─────────┬─────────┘
                                              ▼
                          ┌───────────────────────────────────┐
                          │    React Components Re-render     │
                          │  • Elevator position updates      │
                          │  • Button states change           │
                          │  • Door animation triggers        │
                          └───────────────────────────────────┘
```

### REST API Integration
```
┌──────────────────┐
│  elevator_api.ts │
├──────────────────┤
│  • getStatus()   │────┐
│  • addRequest()  │    │
│  • addStop()     │    │    ┌─────────────────┐
│  • setFloors()   │    ├───►│ Axios Instance  │
└──────────────────┘    │    │  (interceptor)  │
                        │    └────────┬────────┘
                        │             │
                        │             ▼
                        │    ┌─────────────────┐
                        └───►│ Backend API     │
                             │ localhost:8000  │
                             └─────────────────┘
```

### Component Architecture
```
                  ┌───────────────┐
                  │    App.tsx    │
                  │  (Router)     │
                  └───────┬───────┘
                          │
          ┌───────────────┴────────────────┐
          ▼                                ▼
   ┌─────────────┐              ┌──────────────────┐
   │  homePage   │              │  elevatorPage    │
   └─────────────┘              └────────┬─────────┘
                                         │
                          ┌──────────────┼──────────────┐
                          ▼              ▼              ▼
                   ┌───────────┐  ┌──────────┐  ┌─────────────────┐
                   │  Elevator │  │  Floor   │  │ InternalButtons │
                   │ (Visual)  │  │ (Buttons)│  │   (Panel)       │
                   └───────────┘  └──────────┘  └─────────────────┘
                          │              │              │
                          └──────────────┼──────────────┘
                                         ▼
                              ┌────────────────────┐
                              │  Zustand Store     │
                              │  (Global State)    │
                              └────────────────────┘
```

## 🎨 What This Frontend Does

- **Real-time Visualization** - Displays elevator position, direction, and door state
- **Interactive Controls** - External floor buttons (UP/DOWN) and internal floor panel
- **WebSocket Sync** - Automatic state updates from backend every 0.2s
- **Optimistic Updates** - Instant UI feedback before server confirmation
- **Auto-reconnection** - Recovers from WebSocket disconnections (max 5 attempts)
- **Responsive Design** - Tailwind CSS ensures mobile compatibility
- **Smooth Animations** - Framer Motion for elevator movement and door actions
- **Error Handling** - Toast notifications for failures and connection issues

### Key Features:
- **Button State Management** - Visual feedback (active/inactive/selected)
- **Direction Indicators** - Shows which direction elevator is heading
- **Floor Highlighting** - Highlights current floor in real-time
- **Door Animation** - Realistic open/close transitions
- **Request Queue Display** - Shows pending requests on buttons
---
