import heapq
import math
from collections import Counter, namedtuple
from typing import Dict, Any, Tuple, Optional

class Node:
    """
    Represents a node in the coding tree.
    """
    def __init__(self, char: Optional[str], freq: int):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        """
        Comparison for priority queue (min-heap).
        """
        if self.freq == other.freq:
            # Tie-breaker logic for deterministic trees
            # Prefer leaf nodes over internal nodes? Or just char?
            if self.char is not None and other.char is not None:
                return self.char < other.char
            if self.char is not None:
                return True # Prefer leaves
            if other.char is not None:
                return False
            # If both internal, just use ID or something stable? 
            # In Python, we can't easily rely on creation order without an extra field.
            # But for now, returning False implies equality, which is fine for heapq 
            # unless we specifically need a consistent tree shape.
            return False
        return self.freq < other.freq

def calculate_entropy(data: bytes) -> float:
    """
    Calculates the Shannon entropy of the given data.
    
    Args:
        data: The input byte data.
        
    Returns:
        float: The entropy value in bits.
    """
    if not data:
        return 0.0
    
    counter = Counter(data)
    total_len = len(data)
    entropy = 0.0
    
    for count in counter.values():
        p = count / total_len
        if p > 0:
            entropy -= p * math.log2(p)
            
    return entropy

class BaseCoder:
    """
    Base class for source coding algorithms ensuring a common interface.
    """
    def encode(self, data: bytes) -> Tuple[str, Dict[str, str], Any]:
        """
        Encodes the data.
        Returns:
            - Encoded bit string
            - The codebook (dict)
            - The tree or metadata needed for decoding
        """
        raise NotImplementedError

    def decode(self, encoded_bits: str, tree: Any) -> bytes:
        """
        Decodes the bit string using the provided tree/metadata.
        """
        raise NotImplementedError

class HuffmanCoder(BaseCoder):
    """
    Implements Huffman Coding: A bottom-up approach using a priority queue.
    """
    
    def encode(self, data: bytes) -> Tuple[str, Dict[int, str], Node]:
        """
        Builds the Huffman tree and encodes the data.
        
        Why:
            Using a min-heap guarantees O(n log n) complexity for building the tree,
            where n is the number of unique symbols.
        """
        if not data:
            return "", {}, None

        # Calculate frequencies
        freq = Counter(data)
        
        # Priority queue for building the tree bottom-up
        pq = [Node(char, count) for char, count in freq.items()]
        heapq.heapify(pq)
        
        # Build the tree
        while len(pq) > 1:
            left = heapq.heappop(pq)
            right = heapq.heappop(pq)
            
            merged = Node(None, left.freq + right.freq)
            merged.left = left
            merged.right = right
            
            heapq.heappush(pq, merged)
            
        root = pq[0]
        
        # Generate codes
        codes = {} # Map byte (int) -> bitstring
        self._generate_codes(root, "", codes)
        
        # Encode data
        encoded_bits = "".join(codes[byte] for byte in data)
        
        return encoded_bits, codes, root

    def _generate_codes(self, node: Node, current_code: str, codes: Dict[int, str]):
        if node is None:
            return
        
        if node.char is not None:
             codes[node.char] = current_code
             return
        
        self._generate_codes(node.left, current_code + "0", codes)
        self._generate_codes(node.right, current_code + "1", codes)

    def decode(self, encoded_bits: str, root: Node) -> bytes:
        """
        Decodes the bit string by traversing the Huffman tree.
        """
        if not encoded_bits or root is None:
            return b""
            
        decoded_bytes = bytearray()
        current_node = root
        
        for bit in encoded_bits:
            if bit == '0':
                current_node = current_node.left
            else:
                current_node = current_node.right
            
            if current_node.char is not None:
                decoded_bytes.append(current_node.char)
                current_node = root
                
        return bytes(decoded_bytes)


class ShannonFanoCoder(BaseCoder):
    """
    Implements Shannon-Fano Coding: A top-down approach (recursive slicing).
    """

    def encode(self, data: bytes) -> Tuple[str, Dict[int, str], Dict[int, str]]:
        """
        Generates codes using Shannon-Fano algorithm.
        
        Why:
            Splitting the sorted probabilities as close to 50/50 as possible 
            approximates the entropy limit, though less optimally than Huffman.
        """
        if not data:
            return "", {}, {}

        # Calculate frequencies
        freq = Counter(data)
        # Sort by frequency descending
        sorted_symbols = sorted(freq.items(), key=lambda item: item[1], reverse=True)
        
        codes = {}
        self._recursive_split(sorted_symbols, "", codes)
        
        # Encode data
        encoded_bits = "".join(codes[byte] for byte in data)
        
        # For Shannon-Fano, we can verify with just the codebook for simplicity, 
        # or rebuild a tree. The requirements say "decode(encoded_data, tree/map)".
        # We'll return the codebook as the 'map' for decoding.
        
        return encoded_bits, codes, codes

    def _recursive_split(self, symbols: list, current_code: str, codes: Dict[int, str]):
        """
        Recursively splits the list of symbols into two parts with roughly equal 
        frequencies.
        """
        if not symbols:
            return
        
        if len(symbols) == 1:
            codes[symbols[0][0]] = current_code or "0" # Handle single unique char case
            return
        
        # Find the split point that minimizes the difference in sums
        total_sum = sum(s[1] for s in symbols)
        running_sum = 0
        split_idx = 0
        min_diff = float('inf')
        
        for i in range(len(symbols) - 1): # Must have at least one on each side
            running_sum += symbols[i][1]
            # Sum of the rest
            remaining_sum = total_sum - running_sum
            diff = abs(running_sum - remaining_sum)
            
            if diff < min_diff:
                min_diff = diff
                split_idx = i
            # internal note: removed 'else: break' to ensure global minimum is found
            # even if the function isn't perfectly convex in local steps.
                
        # Split
        left_part = symbols[:split_idx + 1]
        right_part = symbols[split_idx + 1:]
        
        self._recursive_split(left_part, current_code + "0", codes)
        self._recursive_split(right_part, current_code + "1", codes)

    def decode(self, encoded_bits: str, codes: Dict[int, str]) -> bytes:
        """
        Decodes using the reverse mapping of the codebook.
        Note: This is less efficient than tree traversal for long streams,
        but satisfies the requirement dealing with the map.
        We can optimize by building a temporary tree from the map.
        """
        # Build a reverse map for fast lookups if we were doing simple matching,
        # but these are prefix codes, so we can walk through bits.
        # Let's build a simple tree for decoding to ensure O(N) decoding logic.
        
        root = Node(None, 0)
        for symbol, code in codes.items():
            curr = root
            for bit in code:
                if bit == '0':
                    if not curr.left: curr.left = Node(None, 0)
                    curr = curr.left
                else:
                    if not curr.right: curr.right = Node(None, 0)
                    curr = curr.right
            curr.char = symbol
            
        # Decode using the tree
        if not encoded_bits:
            return b""
            
        decoded_bytes = bytearray()
        current_node = root
        
        for bit in encoded_bits:
            if bit == '0':
                current_node = current_node.left
            else:
                current_node = current_node.right
            
            # Since these are prefix codes, we will reach a leaf
            if current_node.char is not None:
                decoded_bytes.append(current_node.char)
                current_node = root
                
        return bytes(decoded_bytes)
