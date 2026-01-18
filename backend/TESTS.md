
### **Test Case 1: The "User's Bug" (Interruption + Turnaround)**

*This tests the specific fix we just implemented: ensuring a Down request doesn't get converted into an Internal stop when interrupted.*

* **Initial State:** Floor 0 (IDLE).
* **Events:**
1. Press **2D**. (Elevator starts moving UP to service the turnaround).
2. While moving (e.g., at Floor 0.2), press **1U**.
3. At Floor 1 (Door Open), press **3(Int)**.


* **Expected Stop Sequence:**
`0 -> 1 -> 3 -> 2`
* **Reasoning:**
1. **2D** starts the lift UP.
2. **1U** appears. It is closer and in the same direction (UP).
3. **Interruption Logic:** The lift switches target to **1**.
* *Crucially:* **2D** is re-queued as an **External DOWN** request (Phase 2), *not* an Internal request.


4. At Floor 1, we add **3(Int)**.
5. **Next Stop Decision:** The scheduler compares **3(Int)** (Phase 1: Standard UP) vs. **2D** (Phase 2: Turnaround). Phase 1 wins.
6. Lift goes to 3, drops off, then goes down to 2.



---

### **Test Case 2: The "Skipped Turnaround" (Standard Phase 2)**

*Verifies that the elevator skips a "Down" request while it is traveling "Up" to a higher floor.*

* **Initial State:** Floor 0 (IDLE).
* **Events:**
1. Press **4(Int)** (Internal car button).
2. Press **2D** (External hall button).


* **Expected Stop Sequence:**
`0 -> 4 -> 2`
* **Reasoning:**
* The elevator is going UP to 4.
* **2D** is physically on the way, but directionally opposed (Turnaround).
* It should **SKIP** 2 on the way up, drop the passenger at 4, and then pick up 2 on the way down.



---

### **Test Case 3: The "Closer Stop" Interruption (Standard Phase 1)**

*Verifies that the elevator correctly stops for a new request that is closer and in the same direction.*

* **Initial State:** Floor 0 (IDLE).
* **Events:**
1. Press **4U**. (Lift starts moving UP).
2. While moving (at Floor 1.0), press **2U**.


* **Expected Stop Sequence:**
`0 -> 2 -> 4`
* **Reasoning:**
* **2U** is strictly closer than 4 and is a "Standard UP" request (Phase 1).
* The elevator must interrupt its travel to 4 and stop at 2 first.



---

### **Test Case 4: The "Ground Floor" Turnaround (Falsey 0 Check)**

*Verifies that Floor 0 is treated as a valid valid floor and not ignored (fixing the `if floor:` bug).*

* **Initial State:** Floor 4 (IDLE).
* **Events:**
1. Press **0(Int)**. (Lift starts moving DOWN).
2. While moving (at Floor 3.0), press **2U**.


* **Expected Stop Sequence:**
`4 -> 0 -> 2`
* **Reasoning:**
* Lift is going DOWN to 0.
* **2U** is a "Turnaround" (Going DOWN, wants UP).
* Lift must complete the trip to 0 (Phase 1).
* At 0, it switches direction (Phase 3 logic) to serve 2.



---

### **Test Case 5: The "Missed" Floor (Request Behind)**

*Verifies that if a request comes in for a floor we already passed, we don't reverse immediately.*

* **Initial State:** Floor 2 (Moving UP towards 4).
* **Events:**
1. Current Target is **4(Int)**.
2. Press **1U**.


* **Expected Stop Sequence:**
`2 -> 4 -> 1`
* **Reasoning:**
* We are at 2, moving UP. **1** is below us.
* Even though we want to go UP, we cannot turn back. 1 is added to the `down_up` (Missed/Turnaround) queue.
* We finish the trip to 4, then go down to pick up 1.



---

### **Test Case 6: Complex Multi-Request (Priority Check)**

*Tests the priority of Internal vs. External vs. Turnaround.*

* **Initial State:** Floor 0 (IDLE).
* **Events:**
1. Press **4(Int)**.
2. Press **2U**.
3. Press **3D**.


* **Expected Stop Sequence:**
`0 -> 2 -> 4 -> 3`
* **Reasoning:**
* **Direction:** UP.
* **2U:** Standard UP (Phase 1). **Closest**. -> Stop 1.
* **4(Int):** Standard UP (Phase 1). -> Stop 2.
* **3D:** Turnaround (Phase 2). -> Stop 3.
* Note: It skips 3 on the way UP because 3 is a "Down" request.



---

### **Summary Table**

| Case | Start | Input Sequence | Expected Sequence | Logic Tested |
| --- | --- | --- | --- | --- |
| **1** | 0 | 2D, (wait), 1U, (at 1) 3(Int) | **0 -> 1 -> 3 -> 2** | Interruption Re-queueing |
| **2** | 0 | 4(Int), 2D | **0 -> 4 -> 2** | Phase 2 Skipping |
| **3** | 0 | 4U, (wait), 2U | **0 -> 2 -> 4** | Standard Interruption |
| **4** | 4 | 0(Int), (wait), 2U | **4 -> 0 -> 2** | Falsey 0 / Down Logic |
| **5** | 2 | Target=4(Int), add 1U | **2 -> 4 -> 1** | Missed Floor (Behind) |
| **6** | 0 | 4(Int), 2U, 3D | **0 -> 2 -> 4 -> 3** | Priority Sorting |