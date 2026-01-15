import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { useShallow } from 'zustand/react/shallow';

// ============== Types ==============

export type Direction = "U" | "D" | "IDLE";

export interface ElevatorStatus {
  elevator_id: number;
  current_floor: number;
  direction: Direction;
  is_door_open: boolean;
  up_stops: number[];    // Internal stops going up
  down_stops: number[];  // Internal stops going down
}

export interface ExternalStop {
  floor: number;
  direction: 'U' | 'D';
}

export interface MultiElevatorSystemState {
  // Building configuration
  total_floors: number;
  total_elevators: number;
  
  // All elevators status
  elevators: ElevatorStatus[];
  
  // External button states (hall calls - shared across all elevators)
  externalStops: ExternalStop[];
  
  // Last update timestamp
  timestamp?: number;
  
  // Hydration flag
  _hasHydrated: boolean;
}

interface MultiElevatorSystemActions {
  // Building actions
  initializeBuilding: (totalFloors: number, totalElevators: number) => void;
  syncFromBackend: (totalFloors: number, elevators: ElevatorStatus[]) => void;
  
  // Elevator status actions
  updateAllElevators: (elevators: ElevatorStatus[], timestamp?: number) => void;
  updateSingleElevator: (elevatorId: number, status: Partial<ElevatorStatus>) => void;
  
  // Internal button actions (per elevator)
  addInternalStop: (elevatorId: number, floor: number) => void;
  removeInternalStop: (elevatorId: number, floor: number) => void;
  getInternalStops: (elevatorId: number) => number[];
  hasInternalStop: (elevatorId: number, floor: number) => boolean;
  clearInternalStops: (elevatorId?: number) => void;
  
  // External button actions (hall calls)
  addExternalStop: (floor: number, direction: 'U' | 'D') => void;
  removeExternalStop: (floor: number, direction: 'U' | 'D') => boolean;
  hasUpStop: (floor: number) => boolean;
  hasDownStop: (floor: number) => boolean;
  clearExternalStops: () => void;
  
  // Getters
  getElevator: (elevatorId: number) => ElevatorStatus | undefined;
  reset: () => void;
}

type MultiElevatorStore = MultiElevatorSystemState & MultiElevatorSystemActions;

// ============== Initial State ==============

const initialState: MultiElevatorSystemState = {
  total_floors: 0,
  total_elevators: 0,
  elevators: [],
  externalStops: [],
  timestamp: undefined,
  _hasHydrated: false,
};

// ============== Store ==============

export const useMultiElevatorSystemStore = create<MultiElevatorStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Building actions
      initializeBuilding: (totalFloors, totalElevators) => {
        const elevators: ElevatorStatus[] = Array.from({ length: totalElevators }, (_, i) => ({
          elevator_id: i,
          current_floor: 0,
          direction: "IDLE" as Direction,
          is_door_open: false,
          up_stops: [],
          down_stops: [],
        }));

        set({
          total_floors: totalFloors,
          total_elevators: totalElevators,
          elevators,
          externalStops: [],
          timestamp: Date.now(),
        });
      },

  // Sync state from backend (preserves internal & external stops from local state)
  syncFromBackend: (totalFloors, elevators) => set((state) => {
    // Don't sync until hydration is complete to avoid overwriting persisted data
    if (!state._hasHydrated) {
      return state;
    }
    
    // Get persisted stops from current state
    const getLocalStops = (elevatorId: number) => {
      const localElevator = state.elevators.find((e) => e.elevator_id === elevatorId);
      return {
        up_stops: localElevator?.up_stops ?? [],
        down_stops: localElevator?.down_stops ?? [],
      };
    };

    return {
      total_floors: totalFloors,
      total_elevators: elevators.length,
      elevators: elevators.map((e) => {
        const localStops = getLocalStops(e.elevator_id);
        return {
          elevator_id: e.elevator_id,
          current_floor: e.current_floor,
          direction: e.direction,
          is_door_open: e.is_door_open,
          // Preserve local internal stops, don't use backend stops
          up_stops: localStops.up_stops,
          down_stops: localStops.down_stops,
        };
      }),
      // Keep external stops from local state (they are managed by frontend)
      externalStops: state.externalStops,
      timestamp: Date.now(),
    };
  }),

  // Elevator status actions
  updateAllElevators: (elevators, timestamp) => set({
    elevators,
    timestamp: timestamp ?? Date.now(),
  }),

  updateSingleElevator: (elevatorId, status) => set((state) => ({
    elevators: state.elevators.map((elevator) =>
      elevator.elevator_id === elevatorId
        ? { ...elevator, ...status }
        : elevator
    ),
    timestamp: Date.now(),
  })),

  // Internal button actions (stored per elevator in up_stops/down_stops)
  addInternalStop: (elevatorId, floor) => set((state) => {
    const elevator = state.elevators.find((e) => e.elevator_id === elevatorId);
    if (!elevator) return state;

    // Determine direction based on current floor
    const direction = floor > elevator.current_floor ? 'up' : 'down';
    const stopsKey = direction === 'up' ? 'up_stops' : 'down_stops';
    
    if (elevator[stopsKey].includes(floor)) {
      return state; // Already exists
    }

    return {
      elevators: state.elevators.map((e) =>
        e.elevator_id === elevatorId
          ? { ...e, [stopsKey]: [...e[stopsKey], floor].sort((a, b) => 
              direction === 'up' ? a - b : b - a
            )}
          : e
      ),
    };
  }),

  removeInternalStop: (elevatorId, floor) => set((state) => ({
    elevators: state.elevators.map((e) =>
      e.elevator_id === elevatorId
        ? {
            ...e,
            up_stops: e.up_stops.filter((f) => f !== floor),
            down_stops: e.down_stops.filter((f) => f !== floor),
          }
        : e
    ),
  })),

  getInternalStops: (elevatorId) => {
    const elevator = get().elevators.find((e) => e.elevator_id === elevatorId);
    if (!elevator) return [];
    return [...elevator.up_stops, ...elevator.down_stops];
  },

  hasInternalStop: (elevatorId, floor) => {
    const elevator = get().elevators.find((e) => e.elevator_id === elevatorId);
    if (!elevator) return false;
    return elevator.up_stops.includes(floor) || elevator.down_stops.includes(floor);
  },

  clearInternalStops: (elevatorId) => set((state) => ({
    elevators: state.elevators.map((e) =>
      elevatorId === undefined || e.elevator_id === elevatorId
        ? { ...e, up_stops: [], down_stops: [] }
        : e
    ),
  })),

  // External button actions (hall calls)
  addExternalStop: (floor, direction) => set((state) => {
    const exists = state.externalStops.some(
      (s) => s.floor === floor && s.direction === direction
    );
    if (exists) return state;
    return { externalStops: [...state.externalStops, { floor, direction }] };
  }),

  removeExternalStop: (floor, direction) => {
    const state = get();
    const exists = state.externalStops.some(
      (s) => s.floor === floor && s.direction === direction
    );
    if (!exists) return false;
    
    set({
      externalStops: state.externalStops.filter(
        (s) => !(s.floor === floor && s.direction === direction)
      ),
    });
    return true;
  },

  hasUpStop: (floor) => {
    return get().externalStops.some((s) => s.floor === floor && s.direction === 'U');
  },

  hasDownStop: (floor) => {
    return get().externalStops.some((s) => s.floor === floor && s.direction === 'D');
  },

  clearExternalStops: () => set({ externalStops: [] }),

  // Getters
  getElevator: (elevatorId) => {
    return get().elevators.find((e) => e.elevator_id === elevatorId);
  },

  reset: () => set(initialState),
    }),
    {
      name: 'elevator-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist the stops data
        elevators: state.elevators.map((e) => ({
          elevator_id: e.elevator_id,
          up_stops: e.up_stops,
          down_stops: e.down_stops,
        })),
        externalStops: state.externalStops,
        total_floors: state.total_floors,
        total_elevators: state.total_elevators,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state._hasHydrated = true;
        }
      },
      merge: (persistedState, currentState) => {
        const persisted = persistedState as Partial<MultiElevatorSystemState>;
        
        // Handle initial load: currentState.elevators is empty, restore from persisted
        let mergedElevators: ElevatorStatus[];
        
        if (currentState.elevators.length === 0 && persisted.elevators && persisted.elevators.length > 0) {
          // Initial load - restore elevator structure from persisted data
          mergedElevators = persisted.elevators.map((pe) => ({
            elevator_id: pe.elevator_id,
            current_floor: 0,
            direction: "IDLE" as Direction,
            is_door_open: false,
            up_stops: pe.up_stops ?? [],
            down_stops: pe.down_stops ?? [],
          }));
        } else {
          // Runtime - merge persisted stops into current elevators
          mergedElevators = currentState.elevators.map((elevator) => {
            const persistedElevator = persisted.elevators?.find(
              (e) => e.elevator_id === elevator.elevator_id
            );
            return {
              ...elevator,
              up_stops: persistedElevator?.up_stops ?? elevator.up_stops,
              down_stops: persistedElevator?.down_stops ?? elevator.down_stops,
            };
          });
        }
        
        return {
          ...currentState,
          externalStops: persisted.externalStops ?? currentState.externalStops,
          total_floors: persisted.total_floors ?? currentState.total_floors,
          total_elevators: persisted.total_elevators ?? currentState.total_elevators,
          elevators: mergedElevators,
          _hasHydrated: false, // Will be set to true by onRehydrateStorage
        };
      },
    }
  )
);

// ============== Selectors ==============

// Building selectors
export const useTotalFloors = () =>
  useMultiElevatorSystemStore((state) => state.total_floors);

export const useTotalElevators = () =>
  useMultiElevatorSystemStore((state) => state.total_elevators);

// Elevator selectors
export const useElevators = () =>
  useMultiElevatorSystemStore((state) => state.elevators);

export const useElevator = (elevatorId: number) =>
  useMultiElevatorSystemStore((state) =>
    state.elevators.find((e) => e.elevator_id === elevatorId)
  );

// External stops selectors
export const useExternalStops = () =>
  useMultiElevatorSystemStore((state) => state.externalStops);

export const useHasUpStop = (floor: number) =>
  useMultiElevatorSystemStore((state) =>
    state.externalStops.some((s) => s.floor === floor && s.direction === 'U')
  );

export const useHasDownStop = (floor: number) =>
  useMultiElevatorSystemStore((state) =>
    state.externalStops.some((s) => s.floor === floor && s.direction === 'D')
  );

//! Internal stops selectors
export const useInternalStops = (elevatorId: number): number[] => {
  return useMultiElevatorSystemStore(
    useShallow((state) => {
      const elevator = state.elevators.find((e) => e.elevator_id === elevatorId);
      if (!elevator) return [];
      return [...elevator.up_stops, ...elevator.down_stops];
    })
  );
};

export const useHasInternalStop = (elevatorId: number, floor: number) =>
  useMultiElevatorSystemStore((state) => {
    const elevator = state.elevators.find((e) => e.elevator_id === elevatorId);
    if (!elevator) return false;
    return elevator.up_stops.includes(floor) || elevator.down_stops.includes(floor);
  });

// Timestamp selector
export const useTimestamp = () =>
  useMultiElevatorSystemStore((state) => state.timestamp);

// Hydration selector
export const useHasHydrated = () =>
  useMultiElevatorSystemStore((state) => state._hasHydrated);