import { createBrowserRouter, Outlet } from 'react-router-dom'; 
import HomePage from './pages/homePage/homePage'; 
import ElevatorPage from './pages/elevatorPage/elevatorPage';    


const router = createBrowserRouter([
  {
    path: '/',
    element: <Outlet />,
    children: [
      {
        path : "",
        element: <HomePage />
      },
      {
        path: "elevator",
        element: <ElevatorPage />
      }
    ]
  }
]);

export default router;