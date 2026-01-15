import { useState, useEffect } from 'react';
import InternalButtons from './InternalButtons';

interface ElevatorProps {
  id: number;
  isDoorOpen: boolean;
  direction: 'U' | 'D' | 'IDLE';
  numFloors?: number;
  onFloorSelect?: (floor: number) => void;
}

function ElevatorInterface({id, isDoorOpen, direction, numFloors = 1,  onFloorSelect}: ElevatorProps) {
  const [showButtons, setShowButtons] = useState(false);
  const elevatorWidth = 50;
  const elevatorHeight = elevatorWidth + 20;
  const isMoving = direction !== 'IDLE';

  // Close dialog when door closes
  useEffect(() => {
    if (!isDoorOpen) {
      setShowButtons(false);
    }
  }, [isDoorOpen]);

  const handleElevatorClick = () => {
    if (isDoorOpen) {
      setShowButtons(true);
    }
  };

  return (
      <>
      {/* Interior buttons dialog */}
      {showButtons && (
        <div onClick={() => setShowButtons(false)}>
          <div onClick={(e) => e.stopPropagation()}>
            <InternalButtons 
              elevatorId={id}
              numFloors={numFloors} 
              isDoorOpen={isDoorOpen}
              onFloorSelect={(floor) => {
                onFloorSelect?.(floor);
              }}
            />
          </div>
        </div>
      )}

      {/* Elevator shaft (optional background) */}
      <div className="relative">
        {/* Elevator car */}
        <div
          className="bg-gradient-to-b from-blue-600/80 to-purple-600/80 backdrop-blur-sm border-2 border-white/30 rounded-lg shadow-xl flex flex-col items-center justify-center relative overflow-hidden cursor-pointer hover:shadow-2xl transition-shadow"
          style={{
            width: `${elevatorWidth}px`,
            height: `${elevatorHeight}px`,
          }}
          onClick={handleElevatorClick}
        >
        
        {/* Elevator doors - dark interior when open */}
        <div
          className={`absolute inset-0 bg-slate-700 transition-all duration-1000 ease-in-out flex items-center justify-center ${
            isDoorOpen ? 'opacity-100 scale-x-90' : 'opacity-0 scale-x-0'
          }`}
          style={{
            width: isDoorOpen ? `${elevatorWidth * 0.9}px` : '0px',
            height: `${elevatorHeight}px`,
            left: '45%',
            transform: 'translateX(-50%)',
          }}
        />
          
          {/* Elevator label */}
          <span className="text-white font-bold text-sm z-10">
            E{id + 1}
          </span>
          
          {/* Moving indicator */}
          {isMoving && (
            <div className="absolute bottom-1 w-full flex justify-center">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            </div>
          )}
        </div>
      </div>
      </>
  );
}

export default ElevatorInterface;
