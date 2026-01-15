import { useEffect, useRef, useCallback, useState } from 'react';
import { useElevatorStore, type ElevatorStatus } from '../store/elevatorStore';
import { showErrorToast } from '../utils/toast';
import Elevator from '../services/elevator_api';

const WS_URL = 'ws://localhost:8000/api/ws';
const RECONNECT_DELAY = 3000; // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 5;

export const useElevatorWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const initialFetchDoneRef = useRef(false);

  const updateElevatorStatus = useElevatorStore((state) => state.updateElevatorStatus);

  const connectRef = useRef<(() => void) | null>(null);

  // Fetch initial status from backend on mount
  const fetchInitialStatus = useCallback(async () => {
    if (initialFetchDoneRef.current) return;
    initialFetchDoneRef.current = true;
    
    try {
      const status = await new Elevator().getStatus();
      if (status) {
        console.log('[Initial] Fetched elevator status:', status);
        updateElevatorStatus(status);
      }
    } catch (error) {
      console.error('[Initial] Failed to fetch elevator status:', error);
    }
  }, [updateElevatorStatus]);

//-------------------------------------------------------------------------------------------------
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      
      ws.onopen = () => {
        console.log('[WebSocket] Connected to elevator service');
        reconnectAttemptsRef.current = 0;
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data: ElevatorStatus = JSON.parse(event.data);
          console.log('[WebSocket] Received:', data);
          
          updateElevatorStatus(data);
        
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        wsRef.current = null;
        setIsConnected(false);
        
        // Attempt to reconnect
        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current++;
          console.log(`[WebSocket] Reconnecting... (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectRef.current?.();
          }, RECONNECT_DELAY);
        } else {
          showErrorToast('Lost connection to elevator service');
          console.error('[WebSocket] Max reconnection attempts reached');
        }
      };
    } 
    catch (error) {
      console.error('[WebSocket] Connection error:', error);
    }
  }, [updateElevatorStatus]);

//-------------------------------------------------------------------------------------------------


  // Store connect function in ref using useEffect
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Fetch initial status and connect WebSocket on mount
  useEffect(() => {
    // Fetch initial status immediately to show correct elevator position
    fetchInitialStatus();
    
    // Then connect WebSocket for real-time updates
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  return {
    isConnected,
    reconnect: connect,
    disconnect,
  };
};
