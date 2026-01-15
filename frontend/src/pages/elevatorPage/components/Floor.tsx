interface FloorProps {
  floorNumber: number;
  isTop: boolean;
  isBottom: boolean;
  onCallUp?: () => void;
  onCallDown?: () => void;
  floorHeight: number;
  upGlow?: boolean;
  downGlow?: boolean;
}

function Floor({ floorNumber, isTop, isBottom, onCallUp, onCallDown, floorHeight, upGlow = false, downGlow = false}: FloorProps) {

  return (
    <div
      className="relative"
      style={{ 
        height: `${floorHeight}px`,
        borderBottom: !isBottom ? '2px solid rgba(255, 255, 255, 0.2)' : 'none'
      }}
    >
      {/* Floor Label */}
      <div className="absolute left-0 top-1/2 -translate-y-1/2 text-white/70 font-semibold text-sm bg-white/5 backdrop-blur-sm px-3 py-1 rounded-lg border border-white/10">
        Floor {floorNumber}
      </div>

      {/* Control Buttons */}
      <div className="absolute left-24 top-1/2 -translate-y-1/2 flex flex-col gap-2">
        {!isTop && onCallUp && (
          <button
            onClick={onCallUp}
            className="w-10 h-10 bg-green-600/80 hover:bg-green-700/90 text-white rounded-lg shadow-lg backdrop-blur-sm border border-white/20 flex items-center justify-center transition transform hover:scale-105"
            style={upGlow ? { boxShadow: '0 0 20px rgba(34, 197, 94, 0.8), 0 0 40px rgba(34, 197, 94, 0.4)' } : {}}
            title={`Call elevator UP from floor ${floorNumber}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
            </svg>
          </button>
        )}
        {!isBottom && onCallDown && (
          <button
            onClick={onCallDown}
            className="w-10 h-10 bg-red-600/80 hover:bg-red-700/90 text-white rounded-lg shadow-lg backdrop-blur-sm border border-white/20 flex items-center justify-center transition transform hover:scale-105"
            style={downGlow ? { boxShadow: '0 0 20px rgba(220, 38, 38, 0.8), 0 0 40px rgba(220, 38, 38, 0.4)' } : {}}
            title={`Call elevator DOWN from floor ${floorNumber}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

export default Floor;