# Elevator Scheduling Algorithms

Scheduling strategies for elevator systems, adapted from OS disk scheduling algorithms with real-world constraints.

## Table of Contents
- [Algorithm Comparison](#algorithm-comparison)
- [Algorithm Details](#algorithm-details)
- [Directional Intent Problem](#directional-intent-problem)
- [Modified LOOK Implementation](#modified-look-implementation)
- [Known Limitations](#known-limitations)

---

## Algorithm Comparison

| Algorithm | Efficiency | Fairness | Starvation | Direction-Aware | Production Use |
|-----------|-----------|----------|------------|-----------------|----------------|
| **FCFS**  | Low | Excellent | None | No | Rarely |
| **SSTF**  | Good | Poor | High | No | Rarely |
| **SCAN**  | Good | Moderate | Moderate | Partial | Uncommon |
| **LOOK**  | Very Good | Moderate | Moderate | Partial | Common |
| **Modified LOOK** | Excellent | Good | Low | Yes | ✅ **Industry Standard** |

**Goals:** Minimize wait time, prevent starvation, respect directional intent, optimize energy.

---

## Algorithm Details

### 1. FCFS (First Come First Served)

**Logic:** Queue-based FIFO, ignores distance and direction.

**Example:**
```
Floor: 5 | Queue: [10, 2, 8, 3]
Path: 5→10→2→8→3 | Distance: 24 floors
```

| Pros | Cons |
|------|------|
| Simple, no starvation | Inefficient (excessive zig-zagging) |
| Perfectly fair | High energy consumption |
| Predictable | Poor user experience |

---

### 2. SSTF (Shortest Seek Time First)

**Logic:** Always service nearest floor (`min(|current - requested|)`).

**Example:**
```
Floor: 5 | Requests: [10, 2, 8, 3]
Path: 5→3→2→8→10 | Distance: 11 floors (54% reduction vs FCFS)
```

| Pros | Cons |
|------|------|
| Efficient movement | **Starvation risk** (distant floors ignored) |
| Low energy use | Unpredictable direction changes |
| | Ignores passenger intent (UP/DOWN) |

**Critical Flaw:** Elevator at Floor 5 going UP to 10. Request at Floor 6 going DOWN. SSTF stops (confusion/inefficiency).

---

### 3. SCAN / LOOK

| Feature | SCAN | LOOK |
|---------|------|------|
| **Movement** | To physical end, then reverse | To last request, then reverse |
| **Example** | 5→7→9→10→[TOP]→3→2 | 5→7→9→[reverse]→3→2 |
| **Efficiency** | Wastes energy at ends | Optimized (no wasted trips) |
| **Fairness** | Edge floors favored | Better distribution |

| Pros | Cons |
|------|------|
| Predictable pattern | Still ignores directional intent |
| Direction-aware | Can service wrong requests |
| Better than FCFS/SSTF | Moderate starvation risk |

**Note:** C-SCAN/C-LOOK (circular variants) unsuitable for elevators—jumping from top to bottom wastes time.

---

## Directional Intent Problem

**Core Issue:** Classic LOOK doesn't distinguish between passenger **location** vs **destination intent**.

### Problem Scenario

```
Floor: 0 | Requests: 3U (Floor 3↑), 3D (Floor 3↓), 5D (Floor 5↓)
At 3U, passenger presses internal button 7

❌ Naive LOOK: 0→3→5(WRONG!)→7→back
✅ Expected:     0→3(pickup UP)→7(dropoff)→5(pickup DOWN)→3(pickup DOWN)
```

**Why:** Classic LOOK merges all requests blindly, servicing 5D while going UP (passenger wants DOWN, elevator going UP = confusion).

**Rule:** Only service requests matching current direction intent.

---

## Modified LOOK Implementation

### Data Structures (6 AVL Trees)

| Tree | Purpose | Example |
|------|---------|---------|
| `internal_up` | Car buttons, going UP | Passenger inside pressed 7 |
| `internal_down` | Car buttons, going DOWN | Passenger inside pressed 2 |
| `up_up` | Hall call UP, elevator UP (Phase 1) | Floor 5 wants UP, elevator going UP |
| `down_down` | Hall call DOWN, elevator DOWN (Phase 1) | Floor 3 wants DOWN, elevator going DOWN |
| `up_down` | Hall call DOWN, elevator UP (Phase 2) | Floor 7 wants DOWN, elevator going UP (serve on return) |
| `down_up` | Hall call UP, elevator DOWN (Phase 2) | Floor 2 wants UP, elevator going DOWN (serve on return) |

### Request Classification Logic

| Scenario | Floor | Direction | Tree | Phase |
|----------|-------|-----------|------|-------|
| Elevator IDLE, request above | 8 | UP | `up_up` | 1 |
| Going UP, request ahead wants DOWN | 7 | DOWN | `up_down` | 2 (turnaround) |
| Going UP, missed request below wants UP | 2 | UP | `down_up` | 2 (missed) |

### 3-Phase Scheduling

| Phase | Description | Trees Checked (Going UP) |
|-------|-------------|--------------------------|
| **1. Standard** | Same-direction service | `internal_up`, `up_up`, `down_up` (missed) |
| **2. Turnaround** | Opportunistic pickup before reversing | `up_down` (highest first) |
| **3. Switch** | Check opposite direction, reverse if needed | `down_down`, `internal_down`, `up_down` |

### Barrier Mechanism

```python
only_same_direction = True   # 🛑 Barrier ON (moving)
only_same_direction = False  # ✅ Barrier OFF (idle/completing)
```

| State | Barrier | Behavior |
|-------|---------|----------|
| Actively moving | ON | Only Phase 1 (smooth predictable movement) |
| IDLE / End of direction | OFF | Phase 2 + 3 allowed (turnarounds/switches) |

### Priority System

```
0 = INTERNAL (passengers inside)
1 = EXTERNAL (hall calls matching direction)
2 = MISSED (requests that were behind)
```

**Tie-breaking:** UP → lowest floor | DOWN → highest floor

### Complete Example

```
Floor: 0 | Requests: 3U, 3D, 5D

Step 1: add_request(3, UP)
  → up_up.insert(3), direction=UP

Step 2: add_request(3, DOWN)
  → up_down.insert(3)  # Phase 2 (turnaround)

Step 3: add_request(5, DOWN)
  → up_down.insert(5)  # Phase 2 (turnaround)

Step 4: get_next_stop() | barrier=ON
  → Phase 1: up_up.min()=3 ✅ | return 3

Step 5: At Floor 3, add_stop(7)
  → internal_up.insert(7)

Step 6: get_next_stop() | barrier=ON
  → Phase 1: internal_up.min()=7 ✅ | return 7
  → (Floor 5D skipped—barrier prevents Phase 2)

Step 7: At Floor 7, get_next_stop() | barrier=ON
  → Phase 1: None | return None
  → Loop sets barrier=OFF, calls again
  → Phase 2: up_down.max()=5 ✅ | return 5

Step 8: At Floor 5, passenger boards going DOWN ✅

Step 9: get_next_stop()
  → Phase 2: up_down.max()=3 ✅ | return 3

Final Path: 0→3↑→7↑→5↓→3↓
```

---

## Known Limitations

| Issue | Description | Solution |
|-------|-------------|----------|
| **Full Capacity** | Elevator stops at hall calls when full (wasted stop) | Add `is_overloaded` check, skip external requests |
| **Starvation** | Distant floors ignored during high traffic (e.g., Floor 10 during rush hour) | Implement age-based priority escalation |
| **Peak Hour** | Same algorithm for all traffic patterns (morning UP rush vs evening DOWN rush) | Time-based mode switching or ML prediction |
| **Multi-Elevator** | Single elevator only | Dispatcher system for load balancing & zone assignment |

### Starvation Prevention (Not Implemented)

```python
class TimestampedRequest:
    def __init__(self, floor, direction):
        self.timestamp = time.time()
    
    def age(self):
        return time.time() - self.timestamp
    
    def priority_boost(self):
        return self.age() / 10  # +1 priority per 10 seconds
```

**Real-world target:** < 90 seconds max wait time.

---

## Performance Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Average Wait Time (AWT)** | Request to pickup | < 30s |
| **Average Journey Time (AJT)** | Pickup to destination | Minimize |
| **Total Distance** | Energy efficiency | Minimize |
| **Max Wait Time** | Starvation indicator | < 90s |
| **Stop Efficiency** | Useful stops / Total stops | > 95% |

---

## Summary

**Modified LOOK** balances efficiency, fairness, and user experience through:
- ✅ Directional intent filtering (prevents wrong pickups)
- ✅ 3-phase scheduling (standard → turnaround → switch)
- ✅ Barrier mechanism (predictable movement)
- ✅ AVL trees (O(log n) operations)

**Production additions needed:** Load sensing, request aging, traffic adaptation, multi-elevator coordination.

---

**Last Updated:** January 2026  



