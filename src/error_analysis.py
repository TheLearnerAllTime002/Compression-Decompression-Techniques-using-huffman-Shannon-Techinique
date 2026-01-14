
import numpy as np
import math
import random

def apply_noise(bit_string: str, ber: float) -> str:
    """
    Simulates a Binary Symmetric Channel (BSC) by flipping bits with probability ber.
    
    Args:
        bit_string: The original string of '0's and '1's.
        ber: Bit Error Rate (0.0 to 1.0).
        
    Returns:
        The noisy bit string.
    """
    if ber <= 0.0:
        return bit_string
    
    noisy_bits = []
    for bit in bit_string:
        if random.random() < ber:
            # Flip the bit
            noisy_bits.append('1' if bit == '0' else '0')
        else:
            noisy_bits.append(bit)
    
    return "".join(noisy_bits)

def calculate_ber(original_bits: str, noisy_bits: str) -> float:
    """
    Calculates the actual Bit Error Rate observed.
    """
    if len(original_bits) != len(noisy_bits):
        raise ValueError("Bit strings must be of same length for BER calculation")
        
    if not original_bits:
        return 0.0
        
    mismatches = 0
    for b1, b2 in zip(original_bits, noisy_bits):
        if b1 != b2:
            mismatches += 1
            
    return mismatches / len(original_bits)

def calculate_mse(original_data: bytes, decoded_data: bytes) -> float:
    """
    Calculates Mean Squared Error between two byte sequences.
    Treats them as arrays of unsigned integers (0-255).
    """
    # Truncate to the shorter length to compare prefix (or handle mismatch)
    # Usually for image comparison we expect same dimensions, but noise might cause
    # symbol shifts if synchronization is lost (though Huffman usually stays mostly in sync
    # or produces garbage of same-ish length).
    # For robust image MSE, we strictly align.
    
    min_len = min(len(original_data), len(decoded_data))
    
    if min_len == 0:
        return 0.0
    
    arr_orig = np.frombuffer(original_data[:min_len], dtype=np.uint8)
    arr_dec = np.frombuffer(decoded_data[:min_len], dtype=np.uint8)
    
    # MSE = mean((A-B)^2)
    mse = np.mean((arr_orig - arr_dec) ** 2)
    return float(mse)

def calculate_psnr(mse: float, max_pixel: int = 255) -> float:
    """
    Calculates Peak Signal-to-Noise Ratio.
    """
    if mse == 0:
        return float('inf')
    
    return 10 * math.log10((max_pixel ** 2) / mse)

def calculate_ser_text(original: bytes, decoded: bytes) -> float:
    """
    Calculates Symbol Error Rate for text/bytes.
    """
    min_len = min(len(original), len(decoded))
    if min_len == 0:
        return 0.0
        
    mismatches = 0
    for i in range(min_len):
        if original[i] != decoded[i]:
            mismatches += 1
            
    # Account for length difference errors
    len_diff = abs(len(original) - len(decoded))
    
    total_symbols = len(original)
    if total_symbols == 0: 
        return 0.0
        
    return (mismatches + len_diff) / total_symbols
