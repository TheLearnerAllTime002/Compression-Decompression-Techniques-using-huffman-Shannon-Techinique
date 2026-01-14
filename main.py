import argparse
import os
import time
import pickle
import math
from pathlib import Path
from src.algorithms import HuffmanCoder, ShannonFanoCoder, calculate_entropy, Node
# from src.file_handler import BitWriter, BitReader # Unused in this version, using pickle instead

def get_size(obj, seen=None):
    """Recursively finds size of objects in bytes"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

import sys

def main():
    if len(sys.argv) == 1:
        print("--- Interactive Mode ---")
        print("No arguments provided. Please enter details below.")
        
        # Robust path handling: strip spaces, then strip quotes
        file_path_input = input("Enter file path (e.g., test.txt): ").strip()
        file_path_input = file_path_input.strip('"').strip("'")
            
        algo_input = input("Enter algorithm (huffman/shannon) [default: huffman]: ").strip().lower()
        if not algo_input:
            algo_input = 'huffman'
        elif algo_input not in ['huffman', 'shannon']:
            print(f"Invalid algorithm '{algo_input}', defaulting to huffman.")
            algo_input = 'huffman'
            
        class Args:
            pass
        args = Args()
        args.file_path = file_path_input
        args.algo = algo_input
        
    else:
        parser = argparse.ArgumentParser(description="Image/File Compression using Huffman or Shannon-Fano Coding")
        parser.add_argument("file_path", type=str, help="Path to the source file")
        parser.add_argument("--algo", type=str, choices=["huffman", "shannon"], required=True, help="Compression algorithm to use")
        
        args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return

    # 1. Read Original File
    print(f"Reading file: {file_path}")
    with open(file_path, 'rb') as f:
        original_data = f.read()
        
    original_size = len(original_data)
    if original_size == 0:
        print("File is empty.")
        return

    # 2. Select Algorithm
    if args.algo == 'huffman':
        coder = HuffmanCoder()
        algo_name = "Huffman Coding"
    else:
        coder = ShannonFanoCoder()
        algo_name = "Shannon-Fano Coding"
        
    print(f"Running {algo_name}...")

    # 3. Compress
    start_time = time.perf_counter() * 1000 # ms
    encoded_bits, codes, tree_or_map = coder.encode(original_data)
    end_time = time.perf_counter() * 1000 # ms
    compression_time = end_time - start_time
    
    # 4. Save to .bin file (Bit Packing)
    output_bin_path = file_path.with_suffix(f'.{args.algo}.bin')
    
    # 4. Save to .bin file (Bit Packing with Metadata)
    output_bin_path = file_path.with_suffix(f'.{args.algo}.bin')
    
    # Calculate padding
    extra_padding = 8 - (len(encoded_bits) % 8)
    if extra_padding == 8:
        extra_padding = 0
        
    padded_bits = encoded_bits + "0" * extra_padding
    
    # Convert bit string to bytes
    # int(string, 2) is efficient, then to_bytes
    if len(padded_bits) > 0:
        byte_array = int(padded_bits, 2).to_bytes(len(padded_bits) // 8, byteorder='big')
    else:
        byte_array = b""
        
    print(f"Saving compressed file with {extra_padding} padding bits...")
    
    with open(output_bin_path, 'wb') as f:
        # Pickle the metadata first so the reader knows how to decode
        pickle.dump(extra_padding, f)
        pickle.dump(codes, f)
        # Pickle the compressed body to avoid file pointer sync issues with mixed reads
        pickle.dump(byte_array, f)
        
    predicted_compressed_size = os.path.getsize(output_bin_path)
    
    # 5. Verify (Decompression)
    print("Verifying integrity via decompression...")
    
    # Read back the bits
    # Read back the file to verify
    with open(output_bin_path, 'rb') as f:
        read_padding = pickle.load(f)
        read_codes = pickle.load(f)
        read_content = pickle.load(f)
        
    # Convert bytes back to bits
    read_bits = ""
    if len(read_content) > 0:

        read_bits = "".join(format(b, '08b') for b in read_content)
        
    if read_padding > 0:
        read_bits = read_bits[:-read_padding]
        
    # Decode
    decoded_data = coder.decode(read_bits, tree_or_map)
    
    assert original_data == decoded_data, "Integrity Check Failed: Decoded data does not match original!"
    print("Integrity Check Passed: Data perfectly reconstructed.")

    # 6. Performance Report
    compressed_file_size = predicted_compressed_size
    entropy = calculate_entropy(original_data)
    compression_ratio = original_size / compressed_file_size if compressed_file_size > 0 else 0
    space_saving = (1 - (compressed_file_size / original_size)) * 100 if original_size > 0 else 0
    
    print("\n" + "="*40)
    print(f" PERFORMANCE REPORT: {algo_name}")
    print("="*40)
    print(f"{'Metric':<25} | {'Value':<15}")
    print("-" * 43)
    print(f"{'Original Size':<25} | {original_size:,} bytes")
    print(f"{'Compressed Size':<25} | {compressed_file_size:,} bytes")
    print(f"{'Compression Ratio':<25} | {compression_ratio:.2f}")
    print(f"{'Space Saving':<25} | {space_saving:.2f} %")
    print(f"{'Execution Time':<25} | {compression_time:.2f} ms")
    print(f"{'Entropy':<25} | {entropy:.4f} bits/byte")
    print("="*40)
    print(f"Compressed file saved to: {output_bin_path}")

if __name__ == "__main__":
    main()
