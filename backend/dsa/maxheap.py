class MaxHeap:
    """
    MaxHeap data structure for finding most available doctors.
    Higher values have higher priority (more available slots).
    """
    
    def __init__(self):
        """Initialize an empty max heap."""
        self.heap = []
        self.position_map = {}  # Maps doctor_id to its position in the heap
    
    def parent(self, i):
        """Get the parent index of a node."""
        return (i - 1) // 2
    
    def left_child(self, i):
        """Get the left child index of a node."""
        return 2 * i + 1
    
    def right_child(self, i):
        """Get the right child index of a node."""
        return 2 * i + 2
    
    def swap(self, i, j):
        """Swap two nodes in the heap and update position map."""
        # Update position map
        self.position_map[self.heap[i][1]] = j
        self.position_map[self.heap[j][1]] = i
        
        # Swap elements
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
    
    def heapify_up(self, i):
        """Move a node up to maintain heap property."""
        while i > 0 and self.heap[i][0] > self.heap[self.parent(i)][0]:
            self.swap(i, self.parent(i))
            i = self.parent(i)
    
    def heapify_down(self, i):
        """Move a node down to maintain heap property."""
        largest = i
        left = self.left_child(i)
        right = self.right_child(i)
        
        # Check if left child is larger than current node
        if left < len(self.heap) and self.heap[left][0] > self.heap[largest][0]:
            largest = left
        
        # Check if right child is larger than current largest
        if right < len(self.heap) and self.heap[right][0] > self.heap[largest][0]:
            largest = right
        
        # If largest is not current node, swap and continue heapifying
        if largest != i:
            self.swap(i, largest)
            self.heapify_down(largest)
    
    def insert(self, availability, doctor_id, doctor_data):
        """
        Insert a new doctor into the heap.
        
        Args:
            availability (int): Number of available slots (higher is better)
            doctor_id (int): Unique ID of the doctor
            doctor_data (dict): Additional doctor information
        """
        # Add the new element to the end of the heap
        self.heap.append([availability, doctor_id, doctor_data])
        # Update position map
        self.position_map[doctor_id] = len(self.heap) - 1
        # Restore heap property
        self.heapify_up(len(self.heap) - 1)
    
    def extract_max(self):
        """
        Remove and return the most available doctor.
        
        Returns:
            tuple: (availability, doctor_id, doctor_data) or None if heap is empty
        """
        if len(self.heap) == 0:
            return None
        
        # Get the max element
        max_element = self.heap[0]
        
        # Replace root with last element
        last_element = self.heap.pop()
        
        if len(self.heap) > 0:
            self.heap[0] = last_element
            self.position_map[last_element[1]] = 0
            # Restore heap property
            self.heapify_down(0)
        
        # Remove from position map
        del self.position_map[max_element[1]]
        
        return max_element
    
    def get_max(self):
        """
        Get the most available doctor without removing them.
        
        Returns:
            tuple: (availability, doctor_id, doctor_data) or None if heap is empty
        """
        if len(self.heap) == 0:
            return None
        return self.heap[0]
    
    def update_availability(self, doctor_id, new_availability):
        """
        Update the availability of an existing doctor.
        
        Args:
            doctor_id (int): ID of the doctor to update
            new_availability (int): New availability value
            
        Returns:
            bool: True if updated successfully, False if doctor not found
        """
        if doctor_id not in self.position_map:
            return False
        
        # Get current position
        pos = self.position_map[doctor_id]
        old_availability = self.heap[pos][0]
        
        # Update availability
        self.heap[pos][0] = new_availability
        
        # Restore heap property
        if new_availability > old_availability:
            self.heapify_up(pos)
        else:
            self.heapify_down(pos)
        
        return True
    
    def remove(self, doctor_id):
        """
        Remove a specific doctor from the heap.
        
        Args:
            doctor_id (int): ID of the doctor to remove
            
        Returns:
            bool: True if removed successfully, False if not found
        """
        if doctor_id not in self.position_map:
            return False
        
        # Get position of doctor to remove
        pos = self.position_map[doctor_id]
        
        # Replace with last element
        last_element = self.heap.pop()
        
        # If the removed element was not the last one
        if pos < len(self.heap):
            self.heap[pos] = last_element
            self.position_map[last_element[1]] = pos
            
            # Get old availability for comparison
            old_availability = self.heap[pos][0]
            
            # Restore heap property
            if last_element[0] > old_availability:
                self.heapify_up(pos)
            else:
                self.heapify_down(pos)
        
        # Remove from position map
        del self.position_map[doctor_id]
        
        return True
    
    def get_top_n(self, n):
        """
        Get the top N most available doctors without removing them.
        
        Args:
            n (int): Number of doctors to return
            
        Returns:
            list: List of (availability, doctor_id, doctor_data) tuples
        """
        if n <= 0:
            return []
        
        # Clone the heap to avoid modifying the original
        temp_heap = MaxHeap()
        temp_heap.heap = [item.copy() for item in self.heap]
        temp_heap.position_map = self.position_map.copy()
        
        # Extract the top N doctors
        result = []
        for _ in range(min(n, len(temp_heap.heap))):
            result.append(temp_heap.extract_max())
        
        return result
    
    def size(self):
        """Get the number of doctors in the heap."""
        return len(self.heap)
    
    def is_empty(self):
        """Check if the heap is empty."""
        return len(self.heap) == 0
