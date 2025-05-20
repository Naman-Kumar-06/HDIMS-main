class Graph:
    """
    Graph data structure for doctor referrals and disease tracking.
    Implemented as an adjacency list.
    """
    
    def __init__(self):
        """Initialize an empty graph."""
        self.vertices = {}  # Map of vertex_id to properties
        self.edges = {}     # Map of vertex_id to list of (neighbor_id, weight, properties)
    
    def add_vertex(self, vertex_id, properties=None):
        """
        Add a vertex to the graph.
        
        Args:
            vertex_id: Unique identifier for the vertex
            properties (dict, optional): Properties associated with the vertex
            
        Returns:
            bool: True if added, False if vertex already exists
        """
        if vertex_id in self.vertices:
            return False
        
        self.vertices[vertex_id] = properties or {}
        self.edges[vertex_id] = []
        return True
    
    def add_edge(self, from_id, to_id, weight=1, properties=None):
        """
        Add a directed edge between two vertices.
        
        Args:
            from_id: Source vertex ID
            to_id: Target vertex ID
            weight (float): Edge weight (default: 1)
            properties (dict, optional): Properties associated with the edge
            
        Returns:
            bool: True if added, False if either vertex doesn't exist
        """
        if from_id not in self.vertices or to_id not in self.vertices:
            return False
        
        # Check if edge already exists
        for i, (neighbor, _, _) in enumerate(self.edges[from_id]):
            if neighbor == to_id:
                # Update existing edge
                self.edges[from_id][i] = (to_id, weight, properties or {})
                return True
        
        # Add new edge
        self.edges[from_id].append((to_id, weight, properties or {}))
        return True
    
    def add_undirected_edge(self, vertex1_id, vertex2_id, weight=1, properties=None):
        """
        Add an undirected edge (two directed edges) between vertices.
        
        Args:
            vertex1_id: First vertex ID
            vertex2_id: Second vertex ID
            weight (float): Edge weight (default: 1)
            properties (dict, optional): Properties associated with the edge
            
        Returns:
            bool: True if both edges were added
        """
        success1 = self.add_edge(vertex1_id, vertex2_id, weight, properties)
        success2 = self.add_edge(vertex2_id, vertex1_id, weight, properties)
        return success1 and success2
    
    def get_vertex(self, vertex_id):
        """
        Get a vertex's properties.
        
        Args:
            vertex_id: The vertex ID to look up
            
        Returns:
            dict: Vertex properties or None if not found
        """
        return self.vertices.get(vertex_id)
    
    def get_neighbors(self, vertex_id):
        """
        Get all neighbors of a vertex.
        
        Args:
            vertex_id: The vertex ID to get neighbors for
            
        Returns:
            list: List of (neighbor_id, weight, properties) tuples or None if vertex not found
        """
        if vertex_id not in self.vertices:
            return None
        return self.edges[vertex_id]
    
    def remove_vertex(self, vertex_id):
        """
        Remove a vertex and all its edges from the graph.
        
        Args:
            vertex_id: The vertex ID to remove
            
        Returns:
            bool: True if removed, False if vertex doesn't exist
        """
        if vertex_id not in self.vertices:
            return False
        
        # Remove this vertex from the vertices and edges dictionaries
        del self.vertices[vertex_id]
        del self.edges[vertex_id]
        
        # Remove all edges pointing to this vertex
        for v_id in self.edges:
            self.edges[v_id] = [(n_id, w, p) for n_id, w, p in self.edges[v_id] if n_id != vertex_id]
        
        return True
    
    def remove_edge(self, from_id, to_id):
        """
        Remove a directed edge.
        
        Args:
            from_id: Source vertex ID
            to_id: Target vertex ID
            
        Returns:
            bool: True if removed, False if edge doesn't exist
        """
        if from_id not in self.vertices or to_id not in self.vertices:
            return False
        
        original_length = len(self.edges[from_id])
        self.edges[from_id] = [(n_id, w, p) for n_id, w, p in self.edges[from_id] if n_id != to_id]
        
        # Return True if an edge was actually removed
        return len(self.edges[from_id]) < original_length
    
    def get_all_vertices(self):
        """
        Get all vertices in the graph.
        
        Returns:
            dict: Map of vertex_id to properties
        """
        return self.vertices
    
    def get_edge(self, from_id, to_id):
        """
        Get the properties of an edge.
        
        Args:
            from_id: Source vertex ID
            to_id: Target vertex ID
            
        Returns:
            tuple: (weight, properties) or None if edge doesn't exist
        """
        if from_id not in self.vertices or to_id not in self.vertices:
            return None
        
        for neighbor, weight, props in self.edges[from_id]:
            if neighbor == to_id:
                return (weight, props)
        
        return None
    
    def bfs(self, start_id):
        """
        Perform breadth-first search from a starting vertex.
        
        Args:
            start_id: Starting vertex ID
            
        Returns:
            list: Order of vertices visited
        """
        if start_id not in self.vertices:
            return []
        
        visited = {vertex_id: False for vertex_id in self.vertices}
        queue = [start_id]
        visited[start_id] = True
        result = []
        
        while queue:
            vertex_id = queue.pop(0)
            result.append(vertex_id)
            
            for neighbor, _, _ in self.edges[vertex_id]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    queue.append(neighbor)
        
        return result
    
    def dfs(self, start_id):
        """
        Perform depth-first search from a starting vertex.
        
        Args:
            start_id: Starting vertex ID
            
        Returns:
            list: Order of vertices visited
        """
        if start_id not in self.vertices:
            return []
        
        visited = {vertex_id: False for vertex_id in self.vertices}
        result = []
        
        def dfs_recursive(vertex_id):
            visited[vertex_id] = True
            result.append(vertex_id)
            
            for neighbor, _, _ in self.edges[vertex_id]:
                if not visited[neighbor]:
                    dfs_recursive(neighbor)
        
        dfs_recursive(start_id)
        return result
    
    def shortest_path(self, start_id, end_id):
        """
        Find the shortest path between two vertices using Dijkstra's algorithm.
        
        Args:
            start_id: Source vertex ID
            end_id: Target vertex ID
            
        Returns:
            tuple: (distance, path) where path is a list of vertex IDs
        """
        import heapq
        
        if start_id not in self.vertices or end_id not in self.vertices:
            return float('inf'), []
        
        # Initialize distances and previous vertices
        distances = {vertex_id: float('inf') for vertex_id in self.vertices}
        previous = {vertex_id: None for vertex_id in self.vertices}
        distances[start_id] = 0
        
        # Priority queue for vertices to process
        pq = [(0, start_id)]
        
        while pq:
            current_distance, current_id = heapq.heappop(pq)
            
            # If we've reached the destination, we're done
            if current_id == end_id:
                break
            
            # Skip if we've found a better path already
            if current_distance > distances[current_id]:
                continue
            
            # Check all neighbors
            for neighbor, weight, _ in self.edges[current_id]:
                distance = current_distance + weight
                
                # If we found a shorter path
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_id
                    heapq.heappush(pq, (distance, neighbor))
        
        # Reconstruct the path
        if distances[end_id] == float('inf'):
            return float('inf'), []
        
        path = []
        current = end_id
        while current:
            path.append(current)
            current = previous[current]
        
        return distances[end_id], list(reversed(path))
