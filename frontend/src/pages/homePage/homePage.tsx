import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ElevatorApi from '../../services/elevator_api';

function HomePage() {
  const [floors, setFloors] = useState('11');
  const [elevators, setElevators] = useState('3');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const numFloors = parseInt(floors);
    const numElevators = parseInt(elevators);

    
    new ElevatorApi().initialize_building(numFloors, numElevators);
    
    if (numFloors > 0 && numElevators > 0) {
      setIsLoading(true);
      setTimeout(() => {
        navigate('/elevator', { 
          state: { 
            floors: numFloors, 
            elevators: numElevators 
          } 
        });
      }, 1500);
    }

  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="bg-white/5 backdrop-blur-md rounded-lg shadow-2xl p-8 w-full max-w-md border border-white/30">
        <h1 className="text-3xl font-bold text-center text-white/90 mb-6">
          Multi-Elevator Simulation
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="floors" className="block text-sm font-medium text-white mb-2">
              Number of Floors
            </label>
            <input
              type="number"
              id="floors"
              min="2"
              value={floors}
              onChange={(e) => setFloors(e.target.value)}
              className="w-full px-4 py-2 bg-white/5 backdrop-blur-sm border border-white/50 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition text-white placeholder-white/60"
              placeholder="Enter number of floors"
              required
            />
          </div>

          <div>
            <label htmlFor="elevators" className="block text-sm font-medium text-white mb-2">
              Number of Elevators
            </label>
            <input
              type="number"
              id="elevators"
              min="1"
              value={elevators}
              onChange={(e) => setElevators(e.target.value)}
              className="w-full px-4 py-2 bg-white/5 backdrop-blur-sm border border-white/50 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none transition text-white placeholder-white/60"
              placeholder="Enter number of elevators"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600/80 hover:bg-blue-700/90 text-white font-semibold py-3 rounded-lg transition duration-200 shadow-lg hover:shadow-xl backdrop-blur-sm flex items-center justify-center disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <svg className="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              'Start Simulation'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}

export default HomePage;