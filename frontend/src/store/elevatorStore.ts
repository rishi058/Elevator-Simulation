import { create } from 'zustand';

export interface ElevatorStatus {
  current_floor: number;
  direction: "U" | "D" | "IDLE";
  is_door_open: boolean;

  external_up_requests: number[];
  external_down_requests: number[];
  internal_requests: number[];
  
  timestamp?: number;
}

interface ElevatorStore extends ElevatorStatus {
  // Elevator status actions
  updateElevatorStatus: (status: Partial<ElevatorStatus>) => void;
}

export const useElevatorStore = create<ElevatorStore>()((set) => ({
  // Initial elevator status
  current_floor: 0,
  direction: "IDLE",
  is_door_open: false,
  
  external_up_requests: [],
  external_down_requests: [],
  internal_requests: [],

  timestamp: undefined,
  
  // Elevator status actions
  updateElevatorStatus: (status) => set((state) => ({
    ...state,
    ...status,
  })),
}));

// Selector for internal stops (used by InternalButtons component)
export const useInternalStops = () => 
  useElevatorStore((state) => state.internal_requests);
