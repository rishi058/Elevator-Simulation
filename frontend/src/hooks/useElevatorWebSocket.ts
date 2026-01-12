import { useEffect, useRef, useCallback, useState } from 'react';
import { useElevatorStore, type ElevatorStatus } from '../store/elevatorStore';
import { showErrorToast } from '../utils/toast';

const WS_URL = 'ws://localhost:8000/api/ws';
const RECONNECT_DELAY = 3000; // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 5;

export const useElevatorWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const lastButtonClearTimeRef = useRef<number>(0);
  const [isConnected, setIsConnected] = useState(false);

  const updateElevatorStatus = useElevatorStore((state) => state.updateElevatorStatus);
  const removeInternalStop = useElevatorStore((state) => state.removeInternalStop);
  const removeExternalStop = useElevatorStore((state) => state.removeExternalStop);
  
  const connectRef = useRef<(() => void) | null>(null);

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
        // showToast('Connected to elevator');
      };

      ws.onmessage = (event) => {
        try {
          const data: ElevatorStatus = JSON.parse(event.data);
          console.log('[WebSocket] Received:', data);
          
          // Update elevator status in store
          updateElevatorStatus(data);

          // Auto-clear buttons when elevator arrives at floor with door open
          // Throttled to once every 4 seconds
          if (data.is_door_open) {
            const now = Date.now();
            const THROTTLE_DELAY = 4000; // 4 seconds
            
            if (now - lastButtonClearTimeRef.current >= THROTTLE_DELAY) {
              lastButtonClearTimeRef.current = now;
              
              const floor = Math.floor(data.current_floor);
             
              if (data.direction === "U"){
                const ok = removeExternalStop(floor, "U");
                if(!ok){
                  removeExternalStop(floor, "D");
                }
              }
              else if (data.direction === "D"){
                const ok = removeExternalStop(floor, "D");
                if(!ok){
                  removeExternalStop(floor, "U");
                }
              }
            }

            removeInternalStop(Math.floor(data.current_floor));
          }
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
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
    }
  }, [updateElevatorStatus, removeInternalStop, removeExternalStop]);

  // Store connect function in ref using useEffect
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
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
