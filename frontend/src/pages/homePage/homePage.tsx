import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Elevator from '../../services/elevator_api';

function HomePage() {
  const [floors, setFloors] = useState('8');
  const [elevators, setElevators] = useState('1');
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const numFloors = parseInt(floors);
    const numElevators = parseInt(elevators);

    new Elevator().setFloors(numFloors);
    
    if (numFloors > 0 && numElevators > 0) {
      navigate('/elevator', { 
        state: { 
          floors: numFloors, 
          elevators: numElevators 
        } 
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="bg-white/5 backdrop-blur-md rounded-lg shadow-2xl p-8 w-full max-w-md border border-white/30">
        <h1 className="text-3xl font-bold text-center text-white/90 mb-6">
          Single-Elevator System Simulation
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
              disabled
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600/80 hover:bg-blue-700/90 text-white font-semibold py-3 rounded-lg transition duration-200 shadow-lg hover:shadow-xl backdrop-blur-sm"
          >
            Start Simulation
          </button>
        </form>
      </div>
    </div>
  );
}

export default HomePage;