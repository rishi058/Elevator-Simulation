class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 1
        # self.count = 1  # For handling duplicates if needed

class AVLTree:
    def __init__(self):
        self.root = None

    # --- Public API ---
    def insert(self, key):
        self.root = self._insert(self.root, key)

    def delete(self, key):
        self.root = self._delete(self.root, key)

    def get_min(self):
        if not self.root: return None
        node = self.root
        while node.left: node = node.left
        return node.key

    def get_max(self):
        if not self.root: return None
        node = self.root
        while node.right: node = node.right
        return node.key
    
    def delete_min(self):
        if self.root:
            self.root = self._delete_min(self.root)

    def delete_max(self):
        if self.root:
            self.root = self._delete_max(self.root)

    # --- Helpers ---
    def _height(self, node):
        return node.height if node else 0

    def _update_height(self, node):
        node.height = 1 + max(self._height(node.left), self._height(node.right))

    def _balance_factor(self, node):
        return self._height(node.left) - self._height(node.right) if node else 0

    # --- Core Logic ---
    def _insert(self, node, key):
        if not node: return Node(key)
        
        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        else:
            return node  # Duplicate keys not allowed

        return self._rebalance(node)

    def _delete(self, node, key):
        if not node: return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            # Node found: Handle 0 or 1 child cases directly
            if not node.left: return node.right
            if not node.right: return node.left
            
            # 2 Children: Get successor (min of right subtree), copy value, delete successor
            temp = node.right
            while temp.left: temp = temp.left
            node.key = temp.key
            node.right = self._delete(node.right, temp.key)

        return self._rebalance(node)
    
    def _delete_min(self, node):
        # Base Case: We found the min (it has no left child)
        if not node.left: return node.right
        # Recursive Step: Go left
        node.left = self._delete_min(node.left)
        
        return self._rebalance(node)

    def _delete_max(self, node):
        # Base Case: We found the max (it has no right child)
        if not node.right: return node.left
        # Recursive Step: Go right
        node.right = self._delete_max(node.right)

        return self._rebalance(node)

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