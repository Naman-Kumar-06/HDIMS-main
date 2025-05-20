class SegmentTree:
    """
    Segment Tree data structure for efficient range queries.
    Used for performance metrics over time ranges.
    """
    
    def __init__(self, arr, operation=max):
        """
        Initialize a segment tree from an array.
        
        Args:
            arr (list): Input array
            operation (function): Function to use for combining segments (default: max)
        """
        self.operation = operation
        self.n = len(arr)
        
        # Size of segment tree array
        x = 1
        while x < self.n:
            x *= 2
        x *= 2
        
        # Initialize segment tree with identity element
        if operation == max:
            self.identity = float('-inf')
        elif operation == min:
            self.identity = float('inf')
        elif operation == sum:
            self.identity = 0
        else:
            self.identity = None
        
        self.tree = [self.identity] * x
        
        # Build the tree
        self._build(arr, 0, 0, self.n - 1)
    
    def _build(self, arr, node, start, end):
        """
        Recursively build the segment tree.
        
        Args:
            arr (list): Input array
            node (int): Current node index in the segment tree
            start (int): Start index of the current segment in the input array
            end (int): End index of the current segment in the input array
        """
        if start == end:
            # Leaf node
            self.tree[node] = arr[start]
        else:
            mid = (start + end) // 2
            
            # Recursively build left and right subtrees
            self._build(arr, 2 * node + 1, start, mid)
            self._build(arr, 2 * node + 2, mid + 1, end)
            
            # Combine results from subtrees
            self.tree[node] = self.operation(self.tree[2 * node + 1], self.tree[2 * node + 2])
    
    def query(self, start, end):
        """
        Query the segment tree for a range.
        
        Args:
            start (int): Start index of the query range
            end (int): End index of the query range
            
        Returns:
            any: Result of applying the operation over the range
        """
        if start < 0 or end >= self.n or start > end:
            raise ValueError("Invalid query range")
        
        return self._query(0, 0, self.n - 1, start, end)
    
    def _query(self, node, node_start, node_end, query_start, query_end):
        """
        Recursively query the segment tree.
        
        Args:
            node (int): Current node index in the segment tree
            node_start (int): Start index of the current node's segment
            node_end (int): End index of the current node's segment
            query_start (int): Start index of the query range
            query_end (int): End index of the query range
            
        Returns:
            any: Result of applying the operation over the range
        """
        # No overlap
        if node_end < query_start or node_start > query_end:
            return self.identity
        
        # Complete overlap
        if query_start <= node_start and node_end <= query_end:
            return self.tree[node]
        
        # Partial overlap - query both children
        mid = (node_start + node_end) // 2
        left_result = self._query(2 * node + 1, node_start, mid, query_start, query_end)
        right_result = self._query(2 * node + 2, mid + 1, node_end, query_start, query_end)
        
        return self.operation(left_result, right_result)
    
    def update(self, index, value):
        """
        Update a value in the segment tree.
        
        Args:
            index (int): Index in the original array to update
            value (any): New value
        """
        if index < 0 or index >= self.n:
            raise ValueError("Invalid index")
        
        self._update(0, 0, self.n - 1, index, value)
    
    def _update(self, node, node_start, node_end, index, value):
        """
        Recursively update the segment tree.
        
        Args:
            node (int): Current node index in the segment tree
            node_start (int): Start index of the current node's segment
            node_end (int): End index of the current node's segment
            index (int): Index to update
            value (any): New value
        """
        # Found the leaf node
        if node_start == node_end:
            self.tree[node] = value
            return
        
        mid = (node_start + node_end) // 2
        
        # Update appropriate child
        if index <= mid:
            self._update(2 * node + 1, node_start, mid, index, value)
        else:
            self._update(2 * node + 2, mid + 1, node_end, index, value)
        
        # Update current node
        self.tree[node] = self.operation(self.tree[2 * node + 1], self.tree[2 * node + 2])
    
    def get_array(self):
        """
        Get the current array represented by the segment tree.
        
        Returns:
            list: Current array
        """
        result = []
        for i in range(self.n):
            result.append(self._query(0, 0, self.n - 1, i, i))
        return result
