# File Compression System

A Python implementation of **Huffman Coding** and **Shannon-Fano Coding** algorithms for lossless data compression with entropy analysis and performance metrics.

## Features

- **Dual Algorithm Support**: Huffman and Shannon-Fano coding
- **Universal File Compression**: Works with text, images, and binary files
- **Entropy Calculation**: Shannon entropy analysis for theoretical compression limits
- **Integrity Verification**: Automatic decompression validation
- **Performance Metrics**: Compression ratio, space savings, execution time
- **Interactive & CLI Modes**: Flexible usage options

## Project Structure

```
shannon fano coding/
├── src/
│   ├── algorithms.py      # Core compression algorithms
│   └── file_handler.py    # Bit-level I/O utilities
├── main.py                # Main compression program
├── read_bin.py            # Standalone decompression utility
└── README.md
```

## Installation

**Requirements**: Python 3.7+

No external dependencies required - uses only Python standard library.

```bash
# Clone or download the project
cd "shannon fano coding"
```

## Usage

### Command Line Mode

```bash
# Huffman compression
python main.py test.txt --algo huffman

# Shannon-Fano compression
python main.py test.txt --algo shannon
```

### Interactive Mode

```bash
python main.py
# Follow the prompts to enter file path and algorithm
```

### Reading Compressed Files

```bash
python read_bin.py test.huffman.bin
```

## Workflow

### 1. Compression Process

```
Input File → Frequency Analysis → Tree/Code Generation → Bit Encoding → Binary Output
```

**Step-by-step:**

1. **File Reading**: Load file as raw bytes
2. **Frequency Calculation**: Count occurrence of each byte value
3. **Code Generation**:
   - **Huffman**: Build min-heap, merge nodes bottom-up
   - **Shannon-Fano**: Sort by frequency, split recursively top-down
4. **Encoding**: Replace each byte with its variable-length code
5. **Bit Packing**: Convert bit string to bytes with padding
6. **Serialization**: Save metadata (padding, codebook) + compressed data using pickle

### 2. Decompression Process

```
Binary File → Metadata Extraction → Bit Unpacking → Tree Traversal → Original Data
```

**Step-by-step:**

1. **Load Metadata**: Read padding count and codebook from file header
2. **Bit Extraction**: Convert bytes back to bit string
3. **Remove Padding**: Strip trailing padding bits
4. **Decode**: Traverse tree/map to reconstruct original bytes
5. **Verification**: Compare with original data (in main.py)

### 3. Algorithm Comparison

| Algorithm | Approach | Optimality | Complexity |
|-----------|----------|------------|------------|
| **Huffman** | Bottom-up (greedy) | Optimal prefix code | O(n log n) |
| **Shannon-Fano** | Top-down (divide) | Near-optimal | O(n log n) |

**Huffman** typically achieves better compression due to optimal tree construction.

## Code Architecture

### Core Components

**algorithms.py**
- `Node`: Tree node for prefix codes
- `BaseCoder`: Abstract interface for coders
- `HuffmanCoder`: Implements Huffman algorithm
- `ShannonFanoCoder`: Implements Shannon-Fano algorithm
- `calculate_entropy()`: Shannon entropy calculation

**main.py**
- Argument parsing (CLI + interactive)
- Compression pipeline orchestration
- Integrity verification
- Performance reporting

**read_bin.py**
- Standalone decompression utility
- Metadata parsing
- Human-readable output

### File Format

Compressed `.bin` files contain:
```
[Pickled Padding Count] [Pickled Codebook] [Pickled Compressed Bytes]
```

## Performance Metrics

The system reports:
- **Original Size**: Input file size in bytes
- **Compressed Size**: Output file size in bytes
- **Compression Ratio**: Original/Compressed (higher is better)
- **Space Saving**: Percentage reduction
- **Execution Time**: Compression time in milliseconds
- **Entropy**: Theoretical compression limit (bits/byte)

## Example Output

```
==========================================
 PERFORMANCE REPORT: Huffman Coding
==========================================
Metric                    | Value          
-------------------------------------------
Original Size             | 1,024 bytes
Compressed Size           | 512 bytes
Compression Ratio         | 2.00
Space Saving              | 50.00 %
Execution Time            | 15.23 ms
Entropy                   | 4.5234 bits/byte
==========================================
```

## Technical Details

### Huffman Coding
- Uses min-heap for O(n log n) tree construction
- Generates optimal prefix-free codes
- Left child = '0', right child = '1'
- Deterministic tie-breaking for consistent trees

### Shannon-Fano Coding
- Sorts symbols by frequency (descending)
- Recursively splits into balanced groups
- Minimizes frequency difference between splits
- Builds tree from codebook for decoding

### Entropy Analysis
Shannon entropy formula:
```
H(X) = -Σ p(x) * log₂(p(x))
```
Represents theoretical minimum bits per symbol.

## Limitations

- Metadata overhead significant for small files
- Pickle format not cross-language compatible
- Memory-intensive for very large files (loads entire file)
- No streaming compression support

## Future Enhancements

- Adaptive Huffman coding for streaming data
- Arithmetic coding implementation
- Multi-threaded compression for large files
- Cross-platform binary format (replace pickle)
- Compression of file directories

## License

Educational project - free to use and modify.

## Author

Created as a demonstration of information theory and lossless compression algorithms.
