# Copilot Instructions - Elevator Simulation Frontend

## Architecture Overview
This is a React + TypeScript + Vite frontend for an elevator simulation system that communicates with a backend API (`http://localhost:8000`). The app uses a two-page structure with react-router-dom for navigation.

### Key Components
- **HomePage** ([src/pages/homePage/homePage.tsx](../src/pages/homePage/homePage.tsx)): Input form for configuring floors and elevators, navigates to simulation with state
- **ElevatorPage** ([src/pages/elevatorPage/elevatorPage.tsx](../src/pages/elevatorPage/elevatorPage.tsx)): Main simulation interface with polling-based status updates (500ms interval)
- **Floor/Elevator Components**: Visual representation using absolute positioning with calculated transforms

## State Management Pattern
Global singleton instances manage button states across components:
```typescript
// src/utils/button_state.ts exports shared instances
externalButtonInstance  // External floor call buttons
internalButtonInstance  // Internal elevator buttons
```
These are imported and used directly in components to track active requests. When doors open, both button states are cleared for that floor.

## API Service Architecture
All API calls extend the base `Api` class ([src/services/api_interceptor.ts](../src/services/api_interceptor.ts)):
- Axios interceptors handle toast notifications automatically
- Response interceptor shows success toasts for `response.data.message`
- Error interceptor shows error toasts with formatted messages
- Base URL: `http://localhost:8000`

**Never manually show toasts in API response handlers** - the interceptor handles this automatically.

### Elevator API Methods
- `getStatus()`: Currently returns mock data (commented API call)
- `addRequest(floor, direction)`: External floor button press → updates externalButtonInstance
- `addStop(stop)`: Internal elevator button press → updates internalButtonInstance
- `setFloors(floors)`: Configure total floors in system

## Styling Conventions
- **TailwindCSS v4** with Vite plugin (not PostCSS)
- Dark theme with glassmorphism: `bg-white/5 backdrop-blur-md border border-white/30`
- Gradient backgrounds: `from-gray-950 via-blue-950 to-purple-950`
- Active button glow effect using inline styles with boxShadow (see [Floor.tsx](../src/pages/elevatorPage/components/Floor.tsx#L34))
- Transitions: `transition-all duration-1000 ease-in-out` for smooth elevator movement

## Development Workflow
```bash
npm run dev      # Start dev server (Vite HMR)
npm run build    # TypeScript check + Vite build
npm run lint     # ESLint with TypeScript
npm run preview  # Preview production build
```

## Critical Patterns
1. **Position Calculations**: Elevator position uses `(numFloors - current_floor) * floorHeight` for inverted coordinate system
2. **Polling Pattern**: useEffect with 500ms interval for status updates, cleanup with `clearInterval`
3. **Navigation Guards**: ElevatorPage checks for state and redirects to home if missing
4. **Toast Configuration**: Dark theme with 5s autoClose, consistent across all toasts ([src/utils/toast.ts](../src/utils/toast.ts))

## Type Interfaces
```typescript
// Elevator status from API
interface ElevatorStatus {
  current_floor: number;
  is_moving: boolean;
  is_door_open: boolean;
  direction: "U" | "D" | "IDLE";
}

// Router state transfer
interface LocationState {
  floors: number;
  elevators: number;
}
```

## Known Issues & TODOs
- Internal buttons component ([InternalButtons.tsx](../src/pages/elevatorPage/components/InternalButtons.tsx)) is a stub
- Most API endpoints in Elevator class have commented-out calls with mock returns
- handleCallElevator in ElevatorPage only logs, doesn't call API
- No multi-elevator support (maps over numElevators but uses single shared status)

## Integration Points
- Backend expected at `localhost:8000` with endpoints: `/api/status`, `/api/request`, `/api/stop`, `/api/total_floors`
- react-toastify for notifications (configured in dark theme)
- Framer Motion installed but not currently used
