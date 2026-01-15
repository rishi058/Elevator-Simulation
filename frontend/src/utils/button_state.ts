/**
 * @deprecated This file is deprecated. Use Zustand store instead.
 * Import from: import { useMultiElevatorSystemStore } from '../store/elevatorStore';
 * 
 * This file is kept for backwards compatibility only.
 */

// Types for button state
export interface ExternalButtonGlow {
  upStops: Set<number>;
  downStops: Set<number>;
}

export interface InternalButtonGlow {
  stops: Set<number>;
}

// Legacy singleton pattern - now redirects to Zustand
// Note: This is not reactive. Use Zustand hooks for reactive updates.
class ExternalButtonState {
  private upStops: Set<number> = new Set();
  private downStops: Set<number> = new Set();

  addStop(floor: number, direction: 'U' | 'D') {
    if (direction === 'U') {
      this.upStops.add(floor);
    } else {
      this.downStops.add(floor);
    }
  }

  removeStop(floor: number, direction: 'U' | 'D') {
    if (direction === 'U') {
      this.upStops.delete(floor);
    } else {
      this.downStops.delete(floor);
    }
  }

  hasUpStop(floor: number): boolean {
    return this.upStops.has(floor);
  }

  hasDownStop(floor: number): boolean {
    return this.downStops.has(floor);
  }
}

class InternalButtonState {
  public stops: Set<number> = new Set();
 
  addStop(floor: number) {
    this.stops.add(floor);
  }

  removeStop(floor: number) {
    this.stops.delete(floor);
  }

  hasStop(floor: number): boolean {
    return this.stops.has(floor);
  }
}

export const externalButtonInstance = new ExternalButtonState();
export const internalButtonInstance = new InternalButtonState();