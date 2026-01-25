
### **Test Case 1:**

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