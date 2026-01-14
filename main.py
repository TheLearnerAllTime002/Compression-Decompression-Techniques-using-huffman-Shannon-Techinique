import argparse
import os
import time
import pickle
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# Import custom modules
# Ensure src is in python path if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.algorithms import HuffmanCoder, ShannonFanoCoder, calculate_entropy, Node
from src.error_analysis import apply_noise, calculate_ber, calculate_mse, calculate_psnr, calculate_ser_text

def get_size(obj, seen=None):
    """Recursively finds size of objects in bytes"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

def main():
    parser = argparse.ArgumentParser(description="Image/File Compression using Huffman or Shannon-Fano Coding with Error Analysis")
    parser.add_argument("file_path", nargs='?', help="Path to the source file")
    parser.add_argument("--algo", type=str, choices=["huffman", "shannon"], help="Compression algorithm to use")
    parser.add_argument("--simulate-noise", type=float, default=0.0, help="Simulate Binary Symmetric Channel with this Bit Error Rate (0.0 - 1.0)")
    
    args = parser.parse_args()

    # Interactive mode if arguments are missing
    if not args.file_path:
        print("--- Interactive Mode ---")
        file_path_input = input("Enter file path (e.g., test.png): ").strip().strip('"').strip("'")
        algo_input = input("Enter algorithm (huffman/shannon) [default: huffman]: ").strip().lower() or 'huffman'
        noise_input = input("Enter Noise BER (0.0 - 1.0) [default: 0.0]: ").strip()
        
        args.file_path = file_path_input
        args.algo = algo_input
        try:
            args.simulate_noise = float(noise_input) if noise_input else 0.0
        except ValueError:
            print("Invalid noise value, defaulting to 0.0")
            args.simulate_noise = 0.0

    if not args.algo:
        args.algo = 'huffman'

    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return

    # 1. Read and Preprocess File
    print(f"Reading file: {file_path}")
    
    is_image = False
    image_dims = None # (width, height)
    original_image = None
    
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    if file_path.suffix.lower() in image_extensions:
        try:
            print("Detected image file. Processing...")
            orig_img = Image.open(file_path)
            # Convert to Grayscale (L mode)
            gray_img = orig_img.convert('L')
            original_image = gray_img
            image_dims = gray_img.size # (width, height)
            
            # Flatten to 1D sequence of bytes
            original_data = gray_img.tobytes()
            is_image = True
            print(f"Image processed: {image_dims[0]}x{image_dims[1]}")
        except Exception as e:
            print(f"Failed to process image: {e}")
            return
    else:
        # Regular file reading
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
    
    # 4. Save to .bin file (Bit Packing with Metadata)
    output_bin_path = file_path.with_suffix(f'.{args.algo}.bin')
    
    # Calculate padding
    extra_padding = 8 - (len(encoded_bits) % 8)
    if extra_padding == 8:
        extra_padding = 0
        
    padded_bits = encoded_bits + "0" * extra_padding
    
    # Convert bit string to bytes
    if len(padded_bits) > 0:
        byte_array = int(padded_bits, 2).to_bytes(len(padded_bits) // 8, byteorder='big')
    else:
        byte_array = b""
        
    print(f"Saving compressed file with {extra_padding} padding bits...")
    
    with open(output_bin_path, 'wb') as f:
        # Protocol: 1. Padding (int), 2. Dims (tuple/None), 3. Codes (dict), 4. Content (bytes)
        pickle.dump(extra_padding, f)
        pickle.dump(image_dims, f)
        pickle.dump(codes, f)
        pickle.dump(byte_array, f)
        
    predicted_compressed_size = os.path.getsize(output_bin_path)
    
    # 5. Noise Simulation and Decoding
    ber = args.simulate_noise
    bits_to_decode = encoded_bits # No padding for simulation decode usually, or strip it
    
    decoding_status = "Success"
    decoded_data = b""
    
    if ber > 0:
        print(f"\n--- Simulating Noise (BER={ber}) ---")
        # Existing bits are 'encoded_bits' (raw string).
        # We simulate on the raw stream or the padded stream?
        # Usually channel noise affects the transmitted stream (padded_bits).
        # But we must strip padding after.
        noisy_padded_bits = apply_noise(padded_bits, ber)
        
        # Calculate BER on the stream
        actual_ber = calculate_ber(padded_bits, noisy_padded_bits)
        print(f"Actual BER: {actual_ber:.6f}")
        
        # Strip padding for decoding
        if extra_padding > 0:
            noisy_bits_for_decode = noisy_padded_bits[:-extra_padding]
        else:
            noisy_bits_for_decode = noisy_padded_bits
            
        print("Attempting to decode noisy bitstream...")
        try:
            decoded_data = coder.decode(noisy_bits_for_decode, tree_or_map)
        except Exception as e:
            print(f"Decoding Failed: {e}")
            decoding_status = "Failed"
            decoded_data = b""
    else:
        # No noise, just standard verification
        print("\nVerifying integrity (No Noise)...")
        if extra_padding > 0:
             bits_to_decode = padded_bits[:-extra_padding]
        else:
             bits_to_decode = padded_bits
             
        decoded_data = coder.decode(bits_to_decode, tree_or_map)
        
        if decoded_data == original_data:
            print("Integrity Check Passed: Perfect reconstruction.")
        else:
            print("Warning: Integrity Check Failed (Logic Error?)")
            decoding_status = "Mismatch"

    # 6. Analysis and Image Reconstruction
    
    # Metrics
    mse = 0.0
    psnr = float('inf')
    ser = 0.0
    
    if decoding_status == "Success" and len(decoded_data) > 0:
        if is_image:
            mse = calculate_mse(original_data, decoded_data)
            psnr = calculate_psnr(mse)
            ser = calculate_ser_text(original_data, decoded_data) # Pixel error rate effectively
        else:
            ser = calculate_ser_text(original_data, decoded_data)

    # Performance Report
    compressed_file_size = predicted_compressed_size
    entropy = calculate_entropy(original_data)
    compression_ratio = original_size / compressed_file_size if compressed_file_size > 0 else 0
    space_saving = (1 - (compressed_file_size / original_size)) * 100 if original_size > 0 else 0
    
    print("\n" + "="*40)
    print(f" REPORT: {algo_name}")
    print("="*40)
    print(f"{'Original Size':<25} | {original_size:,} bytes")
    print(f"{'Compressed Size':<25} | {compressed_file_size:,} bytes")
    print(f"{'Compression Ratio':<25} | {compression_ratio:.2f}")
    print(f"{'Space Saving':<25} | {space_saving:.2f} %")
    print(f"{'Entropy':<25} | {entropy:.4f} bits/symbol")
    print("-" * 43)
    if ber > 0:
        print(f"{'Noise (BER)':<25} | {ber}")
        print(f"{'Decoding Status':<25} | {decoding_status}")
        if is_image:
            print(f"{'MSE':<25} | {mse:.4f}")
            print(f"{'PSNR':<25} | {psnr:.2f} dB")
        print(f"{'SER':<25} | {ser:.4f}")
    print("="*40)

    # 7. Image Reconstruction and Visualization
    if is_image and decoding_status == "Success" and len(decoded_data) > 0:
        try:
            # Reconstruct image from bytes
            width, height = image_dims
            expected_size = width * height
            
            # Truncate or pad if necessary
            if len(decoded_data) < expected_size:
                print(f"Warning: Decoded data shorter than expected. Padding with zeros.")
                decoded_data = decoded_data + b'\x00' * (expected_size - len(decoded_data))
            elif len(decoded_data) > expected_size:
                print(f"Warning: Decoded data longer than expected. Truncating.")
                decoded_data = decoded_data[:expected_size]
            
            # Create image from bytes
            decoded_image = Image.frombytes('L', (width, height), decoded_data)
            
            # Save reconstructed image
            output_img_path = file_path.with_suffix(f'.{args.algo}.reconstructed.png')
            decoded_image.save(output_img_path)
            print(f"Reconstructed image saved to: {output_img_path}")
            
            # Visualization
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            axes[0].imshow(original_image, cmap='gray')
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            axes[1].imshow(decoded_image, cmap='gray')
            axes[1].set_title(f'Reconstructed (BER={ber})')
            axes[1].axis('off')
            
            plt.tight_layout()
            viz_path = file_path.with_suffix(f'.{args.algo}.comparison.png')
            plt.savefig(viz_path, dpi=150, bbox_inches='tight')
            print(f"Comparison visualization saved to: {viz_path}")
            plt.close()
            
        except Exception as e:
            print(f"Image reconstruction failed: {e}")
    
    print(f"\nCompressed file saved to: {output_bin_path}")

if __name__ == "__main__":
    main()
