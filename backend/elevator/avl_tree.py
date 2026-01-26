class Node:
    def __init__(self, key, id):
        self.key = key   # for tracking floor
        self.id = id     # for tracking unique request IDs
        self.left = None
        self.right = None
        self.height = 1

class AVLTree:
    def __init__(self):
        self.root = None
        self.total_nodes = 0

    # --- Public API ---
    def insert(self, key, id):
        self.root = self._insert(self.root, key, id)

    def find(self, key):
        node = self.root
        while node:
            if key < node.key:
                node = node.left
            elif key > node.key:
                node = node.right
            else: # key == node.key
                return node.id
        return None

    def delete_by_key(self, key):
        self.root = self._delete(self.root, key)

    # O(n) - ID is not the index, so we must search the whole tree
    def delete_by_id(self, id):
        if not self.root:
            return
            
        # DFS to find the key corresponding to the ID
        stack = [self.root]
        target_key = None
        
        while stack:
            node = stack.pop()
            if node.id == id:
                target_key = node.key
                break
            
            if node.right: stack.append(node.right)
            if node.left: stack.append(node.left)
        
        # If found, delete using the optimized tree key
        if target_key is None: return None

        self.delete_by_key(target_key)
        return target_key

    def get_min(self):
        if not self.root: return (None, None)
        node = self.root
        while node.left: node = node.left
        return (node.key, node.id)

    def get_max(self):
        if not self.root: return (None, None)
        node = self.root
        while node.right: node = node.right
        return (node.key, node.id)
    
    def delete_min(self):
        if self.root:
            self.root = self._delete_min(self.root)

    def delete_max(self):
        if self.root:
            self.root = self._delete_max(self.root)

    # --- Range Query --- O(log n + k)
    def count_nodes_in_range(self, l, r):
        return self._count_range(self.root, l, r)

    def __len__(self):
        return self.total_nodes

    # --- Helpers ---
    def _height(self, node):
        return node.height if node else 0

    def _update_height(self, node):
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0

    # --- Core Logic ---
    def _insert(self, node, key, id):
        if not node:
            self.total_nodes += 1
            return Node(key, id)
        
        if key < node.key:
            node.left = self._insert(node.left, key, id)
        elif key > node.key:
            node.right = self._insert(node.right, key, id)
        else:
            # Duplicate keys not allowed: Not updating total_nodes
            node.id = id # Update ID to track latest request
            return node 

        return self._rebalance(node)

    def _delete(self, node, key):
        if not node: return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node found
            # Case 1: 0 or 1 child
            if not node.left:
                self.total_nodes -= 1
                return node.right
            if not node.right:
                self.total_nodes -= 1
                return node.left
            
            # Case 2: 2 Children
            # Get successor (min of right subtree)
            temp = node.right
            while temp.left: temp = temp.left
            
            # Copy BOTH key and id from successor
            node.key = temp.key
            node.id = temp.id
            
            # Delete successor (recursion will handle total_nodes decrement)
            node.right = self._delete(node.right, temp.key)

        return self._rebalance(node)
    
    def _delete_min(self, node):
        if not node.left:
            self.total_nodes -= 1
            return node.right
            
        node.left = self._delete_min(node.left)
        return self._rebalance(node)

    def _delete_max(self, node):
        if not node.right:
            self.total_nodes -= 1
            return node.left
            
        node.right = self._delete_max(node.right)
        return self._rebalance(node)
    
    # Optimization: If you need strictly O(log n) speed regardless of range size
    # you can augment nodes with subtree counts.
    def _count_range(self, node, l, r):
        if not node:
            return 0
        
        # Case 1: Node key is strictly less than l
        # The node and its entire left subtree are too small. Move Right.
        if node.key < l:
            return self._count_range(node.right, l, r)
            
        # Case 2: Node key is strictly greater than r
        # The node and its entire right subtree are too big. Move Left.
        elif node.key > r:
            return self._count_range(node.left, l, r)
            
        # Case 3: Node is inside the range [l, r]
        # Count this node (1) + check both sides
        else:
            return 1 + self._count_range(node.left, l, r) + self._count_range(node.right, l, r)

    # --- Balancing Magic ---
    def _rebalance(self, node):
        self._update_height(node)
        balance = self._balance_factor(node)

        # Left Heavy
        if balance > 1:
            if self._balance_factor(node.left) < 0: # Left-Right Case
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Right Heavy
        if balance < -1:
            if self._balance_factor(node.right) > 0: # Right-Left Case
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def _rotate_left(self, z):
        y = z.right
        z.right = y.left
        y.left = z
        self._update_height(z)
        self._update_height(y)
        return y

    def _rotate_right(self, z):
        y = z.left
        z.left = y.right
        y.right = z
        self._update_height(z)
        self._update_height(y)
        return y