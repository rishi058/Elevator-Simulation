import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import Floor from './components/Floor';
import ElevatorInterface from './components/Elevator';
import { useMultiElevatorWebSocket } from '../../hooks/useMultiElevatorWebSocket';
import Elevator from '../../services/elevator_api';
import { useMultiElevatorStore } from '../../store/elevatorStore';


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
  useMultiElevatorWebSocket();
  
  const elevators = useMultiElevatorStore((store) => store.elevators);
  
  // Helper functions to check stops (derived from reactive data)
  function hasUpStop(floor: number) {
    // run a loop through all elevators to see if any have an up stop at this floor
    const externalUpRequests = elevators.flatMap(e => e.external_up_requests);
    return externalUpRequests.includes(floor);
  }
  
  function hasDownStop(floor: number) {
    const externalDownRequests = elevators.flatMap(e => e.external_down_requests);
    return externalDownRequests.includes(floor);
  }


  // Initialize building on mount
  useEffect(() => {
    if (!state || !state.floors || !state.elevators) {
      navigate('/');
      return;
    }
    
  }, [state, navigate]);

  const handleCallElevator = (floor: number, direction: 'U' | 'D') => {
    new Elevator().addRequest(floor, direction);
  };
  
  const addInternalStop = useMultiElevatorStore((state) => state.addInternalStop);
  
  const handleFloorSelect = (elevator_id: number, floor: number) => {
    // Optimistic update - immediately show the button as selected
    addInternalStop(elevator_id, floor);
    // Then send the request to the server
    new Elevator().addStop(elevator_id, floor);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-blue-950 to-purple-950 p-8 overflow-x-auto">
      <div className="mb-8 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-white/90">
          Multi-Elevator Simulation
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
        <div className="text-white/90 text-sm flex items-center gap-6">
          <span className="font-semibold">Internal Stops:</span>
          {elevators.map((elevator) => {
              return (
                <div key={elevator.elevator_id} className="flex items-center">
                  <span className="text-blue-300">E{elevator.elevator_id + 1}:</span>
                  {elevator.internal_requests.length === 0 ? (
                    <span className="text-white/60 italic ml-2">None</span>
                  ) : (
                    <span className="ml-2">{[...elevator.internal_requests].sort((a, b) => a - b).join(', ')}</span>
                  )}
                </div>
              );
            })
          }
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