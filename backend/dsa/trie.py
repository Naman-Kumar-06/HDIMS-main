class TrieNode:
    """Node in a Trie data structure."""
    
    def __init__(self):
        # Each node contains a dictionary mapping characters to child nodes
        self.children = {}
        # Flag to indicate if this node represents the end of a word
        self.is_end_of_word = False
        # Optional data to store at the end of a word
        self.data = None

class Trie:
    """
    Trie data structure for efficient prefix-based retrieval.
    Used for autocomplete functionality in patient/disease search.
    """
    
    def __init__(self):
        """Initialize an empty Trie with a root node."""
        self.root = TrieNode()
    
    def insert(self, word, data=None):
        """
        Insert a word into the Trie.
        
        Args:
            word (str): The word to insert
            data (any, optional): Additional data to associate with this word
        """
        node = self.root
        
        # Traverse the Trie, creating new nodes as needed
        for char in word.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        # Mark the end of the word and store data if provided
        node.is_end_of_word = True
        if data:
            node.data = data
    
    def search(self, word):
        """
        Search for a complete word in the Trie.
        
        Args:
            word (str): The word to search for
            
        Returns:
            tuple: (bool, any) - (True if word exists, associated data or None)
        """
        node = self.root
        
        # Traverse the Trie following the characters in the word
        for char in word.lower():
            if char not in node.children:
                return False, None
            node = node.children[char]
        
        # Return whether this is a complete word and any associated data
        return node.is_end_of_word, node.data
    
    def starts_with(self, prefix):
        """
        Find all words that start with the given prefix.
        
        Args:
            prefix (str): The prefix to search for
            
        Returns:
            list: List of (word, data) tuples for words starting with prefix
        """
        node = self.root
        
        # Navigate to the node representing the end of the prefix
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all words starting from this prefix node
        results = []
        self._collect_words(node, prefix.lower(), results)
        return results
    
    def _collect_words(self, node, prefix, results):
        """
        Helper method to recursively collect all words from a given node.
        
        Args:
            node (TrieNode): Current node in traversal
            prefix (str): Prefix accumulated so far
            results (list): List to populate with (word, data) tuples
        """
        # If this node is the end of a word, add it to results
        if node.is_end_of_word:
            results.append((prefix, node.data))
        
        # Recursively traverse all children
        for char, child_node in node.children.items():
            self._collect_words(child_node, prefix + char, results)
    
    def delete(self, word):
        """
        Delete a word from the Trie.
        
        Args:
            word (str): The word to delete
            
        Returns:
            bool: True if the word was deleted, False if not found
        """
        return self._delete_helper(self.root, word.lower(), 0)
    
    def _delete_helper(self, node, word, index):
        """
        Helper method for recursively deleting a word.
        
        Args:
            node (TrieNode): Current node in traversal
            word (str): Word to delete
            index (int): Current character index in word
            
        Returns:
            bool: True if the word was deleted
        """
        # Base case: reached the end of the word
        if index == len(word):
            # If word doesn't exist in Trie
            if not node.is_end_of_word:
                return False
                
            # Mark the node as not the end of a word
            node.is_end_of_word = False
            node.data = None
            
            # Return True if node has no children, indicating it can be removed
            return len(node.children) == 0
        
        char = word[index]
        
        # If character doesn't exist in Trie
        if char not in node.children:
            return False
        
        # Recursively delete in child node
        should_delete_node = self._delete_helper(node.children[char], word, index + 1)
        
        # If child node should be deleted
        if should_delete_node:
            del node.children[char]
            # Return True if this node can also be deleted
            return len(node.children) == 0 and not node.is_end_of_word
        
        return False
