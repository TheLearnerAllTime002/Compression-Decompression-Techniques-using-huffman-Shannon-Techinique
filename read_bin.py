import pickle
import os
import sys

def read_and_decode(bin_filename):
    if not os.path.exists(bin_filename):
        print(f"Error: File '{bin_filename}' not found.")
        return

    print(f"--- READING: {bin_filename} ---")
    
    with open(bin_filename, 'rb') as f:
        # STEP 1: Load the Header (Metadata)
        try:
            # We assume the file starts with:
            # 1. Pickled Padding Count
            # 2. Pickled Codebook
            padding_bits = pickle.load(f)
            image_dims = pickle.load(f)
            codes = pickle.load(f)
            
            print(f"[Header] Padding Bits: {padding_bits}")
            print(f"[Header] Image Dims: {image_dims if image_dims else 'N/A'}")
            print(f"[Header] Codebook Size: {len(codes)} symbols")
            
            # STEP 2: Read the Compressed Body (Pickled Bytes)
            compressed_data = pickle.load(f)
            print(f"[Body] Compressed Bytes: {len(compressed_data)}")
            
        except Exception as e:
            print(f"Error reading structure: {e}")
            return

    # STEP 3: DECOMPRESSION LOGIC
    print("\n--- DECODING CONTENT ---")
    
    if len(compressed_data) == 0:
        print("File contains no data.")
        return

    # A. Convert bytes back to a long string of bits
    # Using a list comprehension is faster for large files
    bit_chunks = [format(byte, '08b') for byte in compressed_data]
    bit_string = "".join(bit_chunks)
        
    # B. Remove the padding bits from the end
    if padding_bits > 0:
        bit_string = bit_string[:-padding_bits]
        
    # C. Reverse the Codebook (We need Code -> Symbol, not Symbol -> Code)
    # The saved dict is likely {Symbol: Code}. We need {Code: Symbol}.
    reverse_codes = {v: k for k, v in codes.items()}
    
    # D. Walk through bits and match them to symbols
    # This is a basic decoding loop (slow for large data but fine for learning)
    # Note: For production systems, a prefix-tree (Trie) traversal is O(N) 
    # and preferred over dictionary lookups O(1)*L for variable length codes.
    decoded_bytes = bytearray()
    current_buffer = ""
    
    # Pre-calculate max code length for optimization (optional but good practice)
    # max_code_len = max(len(k) for k in reverse_codes.keys()) if reverse_codes else 0
    
    for bit in bit_string:
        current_buffer += bit
        if current_buffer in reverse_codes:
            symbol = reverse_codes[current_buffer]
            # Symbol might be an int (byte) or a char depending on python version/logic
            if isinstance(symbol, int):
                decoded_bytes.append(symbol)
            else:
                # If it was saved as str/char
                if isinstance(symbol, str) and len(symbol) == 1:
                    decoded_bytes.append(ord(symbol))
            
            current_buffer = ""  # Reset buffer after finding a match
            
    # STEP 4: OUTPUT
    print(f"Decoded {len(decoded_bytes)} bytes.")
    
    # If image, try to reconstruct
    if image_dims:
        try:
            from PIL import Image
            width, height = image_dims
            expected_size = width * height
            
            if len(decoded_bytes) >= expected_size:
                img = Image.frombytes('L', (width, height), bytes(decoded_bytes[:expected_size]))
                output_path = bin_filename.replace('.bin', '.decoded.png')
                img.save(output_path)
                print(f"Image reconstructed and saved to: {output_path}")
            else:
                print(f"Warning: Not enough data for image reconstruction")
        except Exception as e:
            print(f"Image reconstruction failed: {e}")
    else:
        # Attempt to decode as text for display
        try:
            decoded_text = decoded_bytes.decode('utf-8')
            print("Decoded Text Content:")
            print("-" * 30)
            print(repr(decoded_text))
            print("-" * 30)
        except UnicodeDecodeError:
            print("Decoded Content (Binary):")
            print("-" * 30)
            print(decoded_bytes[:100], "...")
            print("-" * 30)

    print(f"Success! Reconstructed {len(decoded_bytes)} bytes.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        read_and_decode(sys.argv[1])
    else:
        # Default for testing
        print("Usage: python read_bin.py <filename>")
