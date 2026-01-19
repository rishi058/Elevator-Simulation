import heapq

class MinHeap:
    def __init__(self):
        self.heap = []
    
    def insert(self, floor, uuid):
        for item in self.heap:
            if item[1] == uuid: return 
        heapq.heappush(self.heap, (floor, uuid))

    def extract_min(self):
        if not self.heap: return None
        return heapq.heappop(self.heap)
    
    def get_min(self):
        if not self.heap: return None
        return self.heap[0] 
    
    def get_min_value(self):
        val = self.get_min()
        return val[0] if val else None

    def get_max_value(self):
        if not self.heap: return None
        return max(self.heap, key=lambda x: x[0])[0]

    def remove_by_uuid(self, uuid):
        """Removes item by UUID and returns the floor (int) or None."""
        for i, item in enumerate(self.heap):
            if item[1] == uuid:
                val = self.heap.pop(i)
                heapq.heapify(self.heap)
                return val[0] # Return the floor
        return None
    
    def __len__(self):
        return len(self.heap)

class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def insert(self, floor, uuid):
        for item in self.heap:
            if item[1] == uuid: return
        heapq.heappush(self.heap, (-floor, uuid))

    def extract_max(self):
        if not self.heap: return None
        val = heapq.heappop(self.heap)
        return (-val[0], val[1])
    
    def get_max(self):
        if not self.heap: return None
        val = self.heap[0]
        return (-val[0], val[1]) 
    
    def get_max_value(self):
        val = self.get_max()
        return val[0] if val else None

    def get_min_value(self):
        if not self.heap: return None
        return -max(self.heap, key=lambda x: x[0])[0]

    def remove_by_uuid(self, uuid):
        """Removes item by UUID and returns the positive floor (int) or None."""
        for i, item in enumerate(self.heap):
            if item[1] == uuid:
                val = self.heap.pop(i)
                heapq.heapify(self.heap)
                return -val[0] # Return positive floor (it was stored as negative)
        return None

    def __len__(self):
        return len(self.heap)