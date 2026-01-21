import heapq

# Can be converted to a optimzed data structure later
class MinHeap:
    def __init__(self):
        self.heap = []
    
    def insert(self, val):
        if val not in self.heap:
            heapq.heappush(self.heap, val)

    def extract_min(self):
        if not self.heap:
            return None
        return heapq.heappop(self.heap)  # Pop the smallest item off the heap,
    
    def get_min(self):
        if not self.heap:
            return None
        return self.heap[0]  # The smallest item is at the root of the heap  
    
    def get_max(self):
        if not self.heap: return None
        return max(self.heap)  # Return the maximum value in the min-heap
    
class MaxHeap:
    def __init__(self):
        self.heap = []
    
    def insert(self, val):
        if -val not in self.heap:
            heapq.heappush(self.heap, -val)  # Invert value for max-heap behavior

    def extract_max(self):
        if not self.heap:
            return None
        return -heapq.heappop(self.heap)  # Pop the largest item off the heap,
    
    def get_max(self):
        if not self.heap:
            return None
        return -self.heap[0]  # The largest item is at the root of the heap
    
    def get_min(self):
        if not self.heap: return None
        return -min(self.heap)  # Return the minimum value in the max-heap