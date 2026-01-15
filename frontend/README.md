┌─────────────────────────────────────────────────────────────┐
│                     Zustand Store                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ total_floors, total_elevators                        │   │
│  │ elevators: [                                         │   │
│  │   { elevator_id, current_floor, direction,           │   │
│  │     is_door_open, up_stops[], down_stops[] }         │   │
│  │ ]                                                    │   │
│  │ externalStops: [{ floor, direction }]                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         ▲                              │
         │ updateAllElevators()         │ useElevators()
         │                              ▼
┌────────────────────┐         ┌─────────────────────┐
│   WebSocket Hook   │         │   elevatorPage.tsx  │
│  (receives state)  │         │   (renders UI)      │
└────────────────────┘         └─────────────────────┘