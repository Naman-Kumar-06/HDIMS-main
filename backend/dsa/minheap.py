class MinHeap:
    """
    MinHeap data structure for prioritizing appointments based on urgency.
    Lower values have higher priority (more urgent).
    """
    
    def __init__(self):
        """Initialize an empty min heap."""
        self.heap = []
        self.position_map = {}  # Maps appointment_id to its position in the heap
    
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
        while i > 0 and self.heap[i][0] < self.heap[self.parent(i)][0]:
            self.swap(i, self.parent(i))
            i = self.parent(i)
    
    def heapify_down(self, i):
        """Move a node down to maintain heap property."""
        smallest = i
        left = self.left_child(i)
        right = self.right_child(i)
        
        # Check if left child is smaller than current node
        if left < len(self.heap) and self.heap[left][0] < self.heap[smallest][0]:
            smallest = left
        
        # Check if right child is smaller than current smallest
        if right < len(self.heap) and self.heap[right][0] < self.heap[smallest][0]:
            smallest = right
        
        # If smallest is not current node, swap and continue heapifying
        if smallest != i:
            self.swap(i, smallest)
            self.heapify_down(smallest)
    
    def insert(self, urgency, appointment_id, appointment_data):
        """
        Insert a new appointment into the heap.
        
        Args:
            urgency (int): Priority/urgency level (lower is more urgent)
            appointment_id (int): Unique ID of the appointment
            appointment_data (dict): Additional appointment information
        """
        # Add the new element to the end of the heap
        self.heap.append([urgency, appointment_id, appointment_data])
        # Update position map
        self.position_map[appointment_id] = len(self.heap) - 1
        # Restore heap property
        self.heapify_up(len(self.heap) - 1)
    
    def extract_min(self):
        """
        Remove and return the most urgent appointment.
        
        Returns:
            tuple: (urgency, appointment_id, appointment_data) or None if heap is empty
        """
        if len(self.heap) == 0:
            return None
        
        # Get the min element
        min_element = self.heap[0]
        
        # Replace root with last element
        last_element = self.heap.pop()
        
        if len(self.heap) > 0:
            self.heap[0] = last_element
            self.position_map[last_element[1]] = 0
            # Restore heap property
            self.heapify_down(0)
        
        # Remove from position map
        del self.position_map[min_element[1]]
        
        return min_element
    
    def get_min(self):
        """
        Get the most urgent appointment without removing it.
        
        Returns:
            tuple: (urgency, appointment_id, appointment_data) or None if heap is empty
        """
        if len(self.heap) == 0:
            return None
        return self.heap[0]
    
    def update_priority(self, appointment_id, new_urgency):
        """
        Update the urgency/priority of an existing appointment.
        
        Args:
            appointment_id (int): ID of the appointment to update
            new_urgency (int): New urgency value
            
        Returns:
            bool: True if updated successfully, False if appointment not found
        """
        if appointment_id not in self.position_map:
            return False
        
        # Get current position
        pos = self.position_map[appointment_id]
        old_urgency = self.heap[pos][0]
        
        # Update urgency
        self.heap[pos][0] = new_urgency
        
        # Restore heap property
        if new_urgency < old_urgency:
            self.heapify_up(pos)
        else:
            self.heapify_down(pos)
        
        return True
    
    def remove(self, appointment_id):
        """
        Remove a specific appointment from the heap.
        
        Args:
            appointment_id (int): ID of the appointment to remove
            
        Returns:
            bool: True if removed successfully, False if not found
        """
        if appointment_id not in self.position_map:
            return False
        
        # Get position of appointment to remove
        pos = self.position_map[appointment_id]
        
        # Replace with last element
        last_element = self.heap.pop()
        
        # If the removed element was not the last one
        if pos < len(self.heap):
            self.heap[pos] = last_element
            self.position_map[last_element[1]] = pos
            
            # Get old urgency for comparison
            old_urgency = self.heap[pos][0]
            
            # Restore heap property
            if last_element[0] < old_urgency:
                self.heapify_up(pos)
            else:
                self.heapify_down(pos)
        
        # Remove from position map
        del self.position_map[appointment_id]
        
        return True
    
    def size(self):
        """Get the number of appointments in the heap."""
        return len(self.heap)
    
    def is_empty(self):
        """Check if the heap is empty."""
        return len(self.heap) == 0
