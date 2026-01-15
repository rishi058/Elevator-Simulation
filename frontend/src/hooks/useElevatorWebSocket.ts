import { useEffect, useRef, useCallback, useState } from 'react';
import { useMultiElevatorSystemStore, type ElevatorStatus } from '../store/elevatorStore';
import { showErrorToast } from '../utils/toast';

const WS_URL = 'ws://localhost:8000/api/ws';
const RECONNECT_DELAY = 3000; // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 5;

// WebSocket message format from backend
interface WebSocketMessage {
  type: 'state_update';
  total_floors: number;
  elevators: ElevatorStatus[];
  timestamp: number;
}

export const useElevatorWebSocket = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const lastButtonClearTimeRef = useRef<Record<number, number>>({}); // Per-elevator throttle
  const [isConnected, setIsConnected] = useState(false);

  const syncFromBackend = useMultiElevatorSystemStore((state) => state.syncFromBackend);
  const removeExternalStop = useMultiElevatorSystemStore((state) => state.removeExternalStop);
  
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
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('[WebSocket] Received:', message);
          
          if (message.type !== 'state_update') {
            console.warn('[WebSocket] Unknown message type:', message.type);
            return;
          }

          // Sync all elevator data from backend (includes up_stops, down_stops)
          syncFromBackend(message.total_floors, message.elevators);

          // Auto-clear external buttons when any elevator arrives at floor with door open
          // Throttled per elevator to once every 4 seconds
          const THROTTLE_DELAY = 4000; // 4 seconds
          const now = Date.now();

          for (const elevator of message.elevators) {
            if (elevator.is_door_open) {
              const lastClear = lastButtonClearTimeRef.current[elevator.elevator_id] || 0;
              
              if (now - lastClear >= THROTTLE_DELAY) {
                lastButtonClearTimeRef.current[elevator.elevator_id] = now;
                
                const floor = Math.floor(elevator.current_floor);
               
                // Clear external stop based on elevator direction
                if (elevator.direction === "U") {
                  const ok = removeExternalStop(floor, "U");
                  if (!ok) {
                    removeExternalStop(floor, "D");
                  }
                } else if (elevator.direction === "D") {
                  const ok = removeExternalStop(floor, "D");
                  if (!ok) {
                    removeExternalStop(floor, "U");
                  }
                }
              }
            }
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
  }, [syncFromBackend, removeExternalStop]);

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
