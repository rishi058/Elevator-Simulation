import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import Floor from './components/Floor';
import Elevator from '../../services/elevator_api';
import ElevatorInterface from './components/Elevator';
import { useElevatorWebSocket } from '../../hooks/useElevatorWebSocket';
import { useElevatorStore, useInternalStops, useExternalStops } from '../../store/elevatorStore';

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
  
  // Get elevator status from Zustand store - select individual values to prevent infinite re-renders
  const current_floor = useElevatorStore((state) => state.current_floor);
  const is_door_open = useElevatorStore((state) => state.is_door_open);
  const direction = useElevatorStore((state) => state.direction);
  
  // Get button states from Zustand store using custom hooks for proper reactivity
  const internalStopsArray = useInternalStops();
  const externalStopsData = useExternalStops();
  
  const addInternalStop = useElevatorStore((state) => state.addInternalStop);
  const addExternalStop = useElevatorStore((state) => state.addExternalStop);
  
  // Helper functions to check stops (derived from reactive data)
  const hasUpStop = (floor: number) => 
    externalStopsData.some(s => s.floor === floor && s.direction === 'U');
  const hasDownStop = (floor: number) => 
    externalStopsData.some(s => s.floor === floor && s.direction === 'D');

  useEffect(() => {
    if (!state || !state.floors || !state.elevators) {
      navigate('/');
      return;
    }
  }, [state, navigate]);

  const handleCallElevator = (floor: number, direction: 'U' | 'D') => {
    new Elevator().addRequest(floor, direction);
    addExternalStop(floor, direction); // Track with direction in Zustand
  };

  const handleFloorSelect = (floor: number) => {
    new Elevator().addStop(floor);
    addInternalStop(floor); // Track in Zustand
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950 to-purple-950 p-8 overflow-x-auto">
      <div className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white/90">
          Single-Elevator System Simulation
        </h1>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg backdrop-blur-sm border border-white/30 transition"
        >
          Back to Home
        </button>
      </div>

      {/* Display Internal Stops */}
      <div className="p-4 bg-white/10 backdrop-blur-sm rounded-lg border border-white/30">
        <div className="text-white/90 text-sm">
          <span className="font-semibold">Internal Stops:</span>
          {internalStopsArray.length === 0 ? (
            <span className="text-white/60 italic ml-2">None</span>
          ) : (
            <span className="ml-2">
              {[...internalStopsArray].sort((a, b) => a - b).join(', ')}
            </span>
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
        {Array.from({ length: numElevators }).map((_, elevatorIdx) => {
          const xPosition = 220 + (elevatorIdx * 100);
          // Position elevator centered within the floor: 
          // (numFloors - 1 - current_floor) gives the floor index from top
          // Add half floor height and subtract half elevator height to center vertically
          const yPosition = (numFloors - 1 - current_floor) * floorHeight + (floorHeight - elevatorHeight) / 2;
          
          return (
            <div
              key={elevatorIdx}
              className="absolute transition-all duration-1000 ease-in-out"
              style={{
                left: `${xPosition}px`,
                top: `${yPosition}px`,
              }}
            >
              <ElevatorInterface
                id={elevatorIdx}
                isDoorOpen={is_door_open}
                direction={direction}
                numFloors={numFloors}
                onFloorSelect={handleFloorSelect}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ElevatorPage;