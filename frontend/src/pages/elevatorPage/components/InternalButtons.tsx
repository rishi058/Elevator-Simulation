import { useInternalStops } from '../../../store/elevatorStore';

interface InternalButtonsProps {
  numFloors: number;
  isDoorOpen: boolean;
  onFloorSelect?: (floor: number) => void;
}

function InternalButtons({ numFloors, isDoorOpen, onFloorSelect }: InternalButtonsProps) {
  const internalStopsArray = useInternalStops();

  const handleFloorClick = (floor: number) => {
    onFloorSelect?.(floor);
  };

  // Create array of floor numbers from 0 to numFloors-1
  const floorNumbers = Array.from({ length: numFloors }, (_, i) => i);
  const columns = 3;
  const buttonSize = 40; // Square buttons
  const gap = 15;
  const padding = 15;
  const dialogWidth = 200;
  const dialogHeight = 300;

  return (
    <div
      className={`absolute bg-gradient-to-b from-gray-900 to-slate-800 backdrop-blur-md rounded-xl border-2 border-white/40 transition-all duration-300 ${
        isDoorOpen ? 'opacity-100 visible' : 'opacity-0 invisible'
      }`}
      style={{
        width: `${dialogWidth}px`,
        maxHeight: `${dialogHeight}px`,
        display: 'flex',
        flexDirection: 'column',
        zIndex: 50,
        padding: `${padding}px`,
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(59, 130, 246, 0.2)',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, 0)',
      }}
    >
      {/* Header */}
      <div className="mb-4 pb-3 border-b border-white/20">
        <h3 className="text-white/90 text-sm font-semibold text-center">Select Floor</h3>
      </div>

      {/* Scrollable buttons container */}
      <div
        className="overflow-y-auto flex-1"
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap: `${gap}px`,
          paddingRight: '4px',
        }}
      >
        {floorNumbers.map((floor) => (
          <button
            key={floor}
            onClick={() => handleFloorClick(floor)}
            className={`rounded-lg font-bold text-sm transition-all duration-200 flex items-center justify-center ${
              internalStopsArray.includes(floor)
                ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50 scale-95'
                : 'bg-white/10 hover:bg-white/20 text-white/80 hover:text-white border border-white/30'
            }`}
            style={{
              width: `${buttonSize}px`,
              height: `${buttonSize}px`,
              minWidth: `${buttonSize}px`,
              minHeight: `${buttonSize}px`,
            }}
          >
            {floor}
          </button>
        ))}
      </div>
    </div>
  );
}

export default InternalButtons;