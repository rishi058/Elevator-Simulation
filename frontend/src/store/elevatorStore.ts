import { create } from 'zustand';

export interface ElevatorStatus {
  current_floor: number;
  direction: "U" | "D" | "IDLE";
  is_door_open: boolean;
  timestamp?: number;
}

interface ExternalStop {
  floor: number;
  direction: 'U' | 'D';
}

interface ButtonState {
  internalStops: number[];
  externalStops: ExternalStop[];
}

interface ElevatorStore extends ElevatorStatus, ButtonState {
  // Elevator status actions
  updateElevatorStatus: (status: Partial<ElevatorStatus>) => void;
  
  // Internal button actions
  addInternalStop: (floor: number) => void;
  removeInternalStop: (floor: number) => void;
  clearInternalStops: () => void;
  
  // External button actions
  addExternalStop: (floor: number, direction: 'U' | 'D') => void;
  removeExternalStop: (floor: number, direction: 'U' | 'D') => boolean;
  hasUpStop: (floor: number) => boolean;
  hasDownStop: (floor: number) => boolean;
  clearExternalStops: () => void;
}

export const useElevatorStore = create<ElevatorStore>((set, get) => ({ 
  
  // Initial elevator status
  current_floor: 0,
  direction: "IDLE",
  is_door_open: false,
  timestamp: undefined,
  
  // Initial button states (using arrays for proper reactivity)
  internalStops: [],
  externalStops: [],
  
  // Elevator status actions
  updateElevatorStatus: (status) => set((state) => ({
    ...state,
    ...status,
  })),
  
  // Internal button actions
  addInternalStop: (floor) => set((state) => {
    if (state.internalStops.includes(floor)) {
      return state; // Already exists, no change
    }
    return { internalStops: [...state.internalStops, floor] };
  }),
  
  removeInternalStop: (floor) => set((state) => ({
    internalStops: state.internalStops.filter(f => f !== floor)
  })),
  
  clearInternalStops: () => set({ internalStops: [] }),
  
  // External button actions
  addExternalStop: (floor, direction) => set((state) => {
    const exists = state.externalStops.some(
      s => s.floor === floor && s.direction === direction
    );
    if (exists) {
      return state; // Already exists, no change
    }
    return { externalStops: [...state.externalStops, { floor, direction }] };
  }),
  
  removeExternalStop: (floor, direction) => {
    const state = get();
    const exists = state.externalStops.some(
      s => s.floor === floor && s.direction === direction
    );
    if (!exists) {
      return false;
    }
    set({
      externalStops: state.externalStops.filter(
        s => !(s.floor === floor && s.direction === direction)
      )
    });
    return true;
  },
  
  hasUpStop: (floor) => {
    const state = get();
    return state.externalStops.some(s => s.floor === floor && s.direction === 'U');
  },
  
  hasDownStop: (floor) => {
    const state = get();
    return state.externalStops.some(s => s.floor === floor && s.direction === 'D');
  },
  
  clearExternalStops: () => set({ externalStops: [] }),
}));

// Simple selectors for internal stops
export const useInternalStops = () => 
  useElevatorStore((state) => state.internalStops);

// Simple selectors for external stops
export const useExternalStops = () => 
  useElevatorStore((state) => state.externalStops);

// Helper to check if a floor has an up stop
export const useHasUpStop = (floor: number) => 
  useElevatorStore((state) => state.externalStops.some(s => s.floor === floor && s.direction === 'U'));

// Helper to check if a floor has a down stop
export const useHasDownStop = (floor: number) => 
  useElevatorStore((state) => state.externalStops.some(s => s.floor === floor && s.direction === 'D'));

// Helper to check if a floor is in internal stops
export const useHasInternalStop = (floor: number) => 
  useElevatorStore((state) => state.internalStops.includes(floor));
