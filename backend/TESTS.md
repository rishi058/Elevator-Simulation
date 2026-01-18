### Test Cases for Multi-Elevator System

The following test cases cover the `SCAN` algorithm logic, priority handling (Internal vs. External), Phase 1/2 transitions, and dynamic dispatching logic implemented in your system.

**System Configuration:**

* **Floors:** 8 (0 to 7)
* **Elevators:** 3 (IDs: 0, 1, 2)
* **Home Position:** Assumed `0` unless specified.

#### 1. Single Elevator Logic (Pathing & Priorities)

These tests focus on the behavior of a single elevator unit's scheduler (`StopScheduler`).

| Case | Start Floor | Input Sequence (In Order) | Expected Sequence | Logic Tested |
| --- | --- | --- | --- | --- |
| **1** | 0 | `5 (Int)` | 0 → 5 | **Basic Internal**: Simple point-to-point movement. |
| **2** | 0 | `7 (Int)` → `(Wait 1s)` → `3U` | 0 → 3 → 7 | **Standard Interruption (SCAN)**: A request appearing *en route* in the same direction (3U) is serviced before the final destination (7). |
| **3** | 0 | `4 (Int)` → `2D` | 0 → 4 → 2 | **Phase 2 Skipping**: `2D` is a "Turnaround" request (Phase 2). Even though 2 is physically closer than 4, the elevator finishes Phase 1 (Up to 4) before servicing the turnaround (2). |
| **4** | 4 | `0 (Int)` → `(Wait 1s)` → `2U` | 4 → 0 → 2 | **Turnaround (Down-to-Up)**: Moving DOWN to 0. `2U` is an UP request. Elevator must complete the DOWN trip to 0 before switching direction to handle 2. |
| **5** | 2 | `4 (Int)` → `(Wait 1s)` → `1U` | 2 → 4 → 1 | **Missed Floor (Behind)**: Elevator is at 2 going UP to 4. `1U` is added. Since 1 < 2, it is "behind" the car. It is queued for the return trip (Phase 2/3). |
| **6** | 0 | `4 (Int)` → `2U` → `3D` | 0 → 2 → 4 → 3 | **Complex Priority**: <br>

<br>1. `2U` & `4(Int)` are Phase 1 (Up). Sorted 2 → 4.<br>

<br>2. `3D` is Phase 2 (Turnaround).<br>

<br>Order: Phase 1 (2, 4) then Phase 2 (3). |
| **7** | 3 | `3U` → `3 (Int)` | 3 (Doors Open) | **Duplicate/Same Floor**: Requests for the current floor (Internal or External) should immediately trigger door open logic without movement. |
| **8** | 5 | `2 (Int)` → `(Wait)` → `6U` | 5 → 2 → 6 | **Direction Commitment**: Elevator commits to DOWN for `2(Int)`. `6U` is UP. Elevator finishes DOWN trip (2) before servicing UP (6). |

---

#### 2. Multi-Elevator Dispatch Logic (Controller)

These tests focus on the `CollectiveDispatchController` and how it assigns external requests to specific elevators based on Cost.

**Setup for Dispatch Tests:**

* **Elevator 0:** At Floor 0 (IDLE)
* **Elevator 1:** At Floor 7 (IDLE)
* **Elevator 2:** At Floor 3 (Moving UP to 5)

| Case | Input Request | Assigned To | Expected Behavior | Logic Tested |
| --- | --- | --- | --- | --- |
| **9** | `1U` | **Elev 0** | Elev 0 moves 0 → 1 | **Proximity (Idle)**: Elev 0 is closest (dist=1). Elev 1 is far (dist=6). Elev 2 is moving away. |
| **10** | `6D` | **Elev 1** | Elev 1 moves 7 → 6 | **Proximity (Idle)**: Elev 1 is at 7, request is 6. Distance is 1. Very low cost. |
| **11** | `4U` | **Elev 2** | Elev 2 moves 3 → 4 → 5 | **En-Route Optimization**: Elev 2 is at 3 going to 5. 4 is directly on its path. Cost is minimal (just a stop penalty). Elev 0 would have to travel 0->4 (distance 4). |
| **12** | `2D` | **Elev 0** | Elev 0 moves 0 → 2 | **Empty Car Priority**: Elev 2 is at 3 going UP. To serve `2D`, it must go 3->5, then down to 2. Elev 0 is Idle at 0; moving 0->2 is cheaper than waiting for Elev 2's round trip. |
| **13** | `5U` | **Elev 2** | Elev 2 moves 3 → 5 | **Destination Match**: Elev 2 is already going to 5. The cost is effectively 0 (already going there). |

---

#### 3. Edge Cases & Stress Tests

| Case | Start | Input Sequence | Expected Sequence | Logic Tested |
| --- | --- | --- | --- | --- |
| **14** | 0 | `7U` → `7D` | 0 → 7 (Open, Open) | **Dual Request at Extremity**: Reaching top floor (7) should clear both UP and DOWN external requests if they exist there (Terminal floor logic). |
| **15** | 0 | `1U` (Assign E0) → `1D` (Assign E0) | 0 → 1 (Open) | **Opposite Requests same floor**: If Elevator arrives at 1 going UP, it serves `1U`. If no further UP requests exist, it should *turn around* and serve `1D` immediately without moving. |
| **16** | 0 | `1U`, `2U`, `3U`, `4U` | 0 → 1 → 2 → 3 → 4 | **The "Milk Run"**: Continuous interruptions in valid direction. System should not skip stops. |
| **17** | 4 | `1D`, `2D` (Wait) `5U`, `6U` | 4 → 2 → 1 → 5 → 6 | **Full Cycle (V-Pattern)**: Complete the DOWN sweep (4->2->1) before starting the UP sweep (5->6). |

### Summary of Priority Logic (Used for Verification)

1. **Phase 1 (Current Direction, Ahead):** Highest Priority. (e.g., At 2 Going UP: `3U`, `5(Int)`)
2. **Phase 2 (Current Direction, Turnaround):** Medium Priority. Requests that require the elevator to go to a floor in the *current* direction but then switch direction. (e.g., At 2 Going UP: `5D`)
3. **Phase 3 (Opposite Direction/Behind):** Lowest Priority. Requests strictly behind the elevator. (e.g., At 2 Going UP: `1U`, `1D`)