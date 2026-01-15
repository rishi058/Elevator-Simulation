import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useCallback } from 'react';
import Floor from './components/Floor';
import ElevatorApi from '../../services/elevator_api';
import ElevatorInterface from './components/Elevator';
import { useElevatorWebSocket } from '../../hooks/useElevatorWebSocket';
import { 
  useMultiElevatorSystemStore,
  useElevators,
  useExternalStops,
} from '../../store/elevatorStore';

interface LocationState {
  floors: number;
  elevators: number;
}

function ElevatorPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState;

  const numFloors = state?.floors || 1;
  const numElevators = state?.elevators || 1;
  const floors = Array.from({ length: numFloors }, (_, i) => numFloors - 1 - i);
  const floorHeight = 150;
  const elevatorHeight = 70; // Match the elevator component height

  // Use WebSocket hook for real-time updates
  useElevatorWebSocket();
  
  // Store actions
  const initializeBuilding = useMultiElevatorSystemStore((state) => state.initializeBuilding);
  const syncFromBackend = useMultiElevatorSystemStore((state) => state.syncFromBackend);
  const addExternalStop = useMultiElevatorSystemStore((state) => state.addExternalStop);
  const addInternalStop = useMultiElevatorSystemStore((state) => state.addInternalStop);
  
  // Get all elevators status from Zustand store
  const elevators = useElevators();
  
  // Get button states from Zustand store
  const externalStopsData = useExternalStops();
  
  // Helper functions to check stops (derived from reactive data)
  const hasUpStop = (floor: number) => 
    externalStopsData.some(s => s.floor === floor && s.direction === 'U');
  const hasDownStop = (floor: number) => 
    externalStopsData.some(s => s.floor === floor && s.direction === 'D');

  // Fetch and sync initial status from backend
  const fetchInitialStatus = useCallback(async () => {
    try {
      const api = new ElevatorApi();
      const status = await api.getStatus();
      if (status && status.elevators) {
        syncFromBackend(status.total_floors, status.elevators);
        console.log('[ElevatorPage] Synced initial status from backend:', status);
      }
    } catch (error) {
      console.error('[ElevatorPage] Failed to fetch initial status:', error);
    }
  }, [syncFromBackend]);

  // Initialize building on mount
  useEffect(() => {
    if (!state || !state.floors || !state.elevators) {
      navigate('/');
      return;
    }
    
    // First initialize the store with default state
    initializeBuilding(numFloors, numElevators);
    
    // Then fetch actual status from backend to sync positions
    fetchInitialStatus();
  }, [state, navigate, initializeBuilding, numFloors, numElevators, fetchInitialStatus]);

  const handleCallElevator = (floor: number, direction: 'U' | 'D') => {
    new ElevatorApi().addRequest(floor, direction);
    addExternalStop(floor, direction); // Track with direction in Zustand
  };

  const handleFloorSelect = (elevatorId: number, floor: number) => {
    new ElevatorApi().addStop(elevatorId, floor);
    addInternalStop(elevatorId, floor); // Track in Zustand
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950 to-purple-950 p-8 overflow-x-auto">
      <div className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white/90">
          Elevator Simulation
        </h1>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg backdrop-blur-sm border border-white/30 transition"
        >
          Back to Home
        </button>
      </div>

      {/* Display Internal Stops per Elevator */}
      <div className="p-4 bg-white/10 backdrop-blur-sm rounded-lg border border-white/30 mb-4">
        <div className="text-white/90 text-sm space-y-1">
          <span className="font-semibold">Internal Stops:</span>
          {elevators.length === 0 ? (
            <span className="text-white/60 italic ml-2">No elevators</span>
          ) : (
            elevators.map((elevator) => {
              const stops = [...elevator.up_stops, ...elevator.down_stops].sort((a, b) => a - b);
              return (
                <div key={elevator.elevator_id} className="ml-4">
                  <span className="text-blue-300">Elevator {elevator.elevator_id + 1}:</span>
                  {stops.length === 0 ? (
                    <span className="text-white/60 italic ml-2">None</span>
                  ) : (
                    <span className="ml-2">{stops.join(', ')}</span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="relative" style={{ minWidth: `${(numElevators * 100) + 300}px`, height: `${(numFloors + 1) * floorHeight}px` }}>
        {/* Render floors */}
        {floors.map((floor) => (
          <Floor
            key={floor}
            floorNumber={floor}
            isTop={floor === numFloors - 1}
            isBottom={floor === 0}
            onCallUp={floor < numFloors - 1 ? () => handleCallElevator(floor, 'U') : undefined}
            onCallDown={floor > 0 ? () => handleCallElevator(floor, 'D') : undefined}
            floorHeight={floorHeight}
            upGlow={hasUpStop(floor)}
            downGlow={hasDownStop(floor)}
          />
        ))}

        {/* Render elevators */}
        {elevators.map((elevator) => {
          const xPosition = 220 + (elevator.elevator_id * 100);
          // Position elevator centered within the floor: 
          // (numFloors - 1 - current_floor) gives the floor index from top
          // Add half floor height and subtract half elevator height to center vertically
          const yPosition = (numFloors - 1 - elevator.current_floor) * floorHeight + (floorHeight - elevatorHeight) / 2;
          
          return (
            <div
              key={elevator.elevator_id}
              className="absolute transition-all duration-1000 ease-in-out"
              style={{
                left: `${xPosition}px`,
                top: `${yPosition}px`,
              }}
            >
              <ElevatorInterface
                id={elevator.elevator_id}
                isDoorOpen={elevator.is_door_open}
                direction={elevator.direction}
                numFloors={numFloors}
                onFloorSelect={(floor) => handleFloorSelect(elevator.elevator_id, floor)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ElevatorPage;