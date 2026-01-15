import { create } from 'zustand';

interface ElevatorStatus {
  elevator_id: number;
  current_floor: number;
  direction: "U" | "D" | "IDLE";
  is_door_open: boolean;

  external_up_requests: number[];
  external_down_requests: number[];
  internal_requests: number[];
} 

export interface MultiElevatorStatus {
  elevators: ElevatorStatus[];
  total_floors: number;
  total_elevators: number;
  timestamp?: number;
}

interface MultiElevatorStore extends MultiElevatorStatus {
  // Elevator status actions
  updateMultiElevatorStatus: (status: Partial<MultiElevatorStatus>) => void;
  // Optimistic update for internal stops
  addInternalStop:(elevator_id: number, floor: number) => void;
}

export const useMultiElevatorStore = create<MultiElevatorStore>()((set) => ({
  // Initial elevator status
  total_floors: 0,
  total_elevators: 0,
  elevators: [],
  timestamp: undefined,
  
  // Elevator status actions
  updateMultiElevatorStatus: (status) => set((state) => ({
    ...state,
    ...status,
  })),

  // Optimistic update - immediately add floor to internal requests
  addInternalStop: (elevator_id, floor) => set((state) => ({
    ...state,
    elevators: state.elevators.map((elevator, index) => 
      index === elevator_id
        ? {
            ...elevator,
            internal_requests: elevator.internal_requests.includes(floor)
              ? elevator.internal_requests
              : [...elevator.internal_requests, floor],
          }
        : elevator
    ),
  })),

}));

// Selector for internal stops (used by InternalButtons component)
export const useInternalStops = (elevator_id: number) => 
  useMultiElevatorStore((state) => state.elevators[elevator_id]?.internal_requests);