import struct

class BitWriter:
    """
    Helper class to write bits into a binary file.
    It buffers bits until it has a full byte, then writes it.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.buffer = 0
        self.buffer_len = 0
        self.file = open(self.filepath, 'wb')
        
        # Reserve the first byte for the padding count (0-7)
        # We will write the actual value when closing the file.
        self.file.write(struct.pack('B', 0))

    def write_bits(self, bit_string: str):
        """
        Accumulates bits and writes full bytes to the file.
        """
        for bit in bit_string:
            val = int(bit)
            # Shift buffer left and add new bit
            self.buffer = (self.buffer << 1) | val
            self.buffer_len += 1
            
            if self.buffer_len == 8:
                self.file.write(struct.pack('B', self.buffer))
                self.buffer = 0
                self.buffer_len = 0

    def close(self):
        """
        Flushes remaining bits (padding with 0s) and updates the header
        with the number of valid bits in the last byte (or padding count).
        
        Requirement: "store the padding count in the file header"
        """
        padding_count = 0
        if self.buffer_len > 0:
            padding_count = 8 - self.buffer_len
            self.buffer = self.buffer << padding_count
            self.file.write(struct.pack('B', self.buffer))
            
        # Go back to start and write the padding count
        self.file.seek(0)
        self.file.write(struct.pack('B', padding_count))
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class BitReader:
    """
    Helper class to read bits from a binary file.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = open(self.filepath, 'rb')
        
        # Read the padding count
        data = self.file.read(1)
        if len(data) < 1:
            self.padding_count = 0 
            # Empty file or error? 
        else:
            self.padding_count = struct.unpack('B', data)[0]
            
    def read_all_bits(self) -> str:
        """
        Reads the whole file and returns the bit string.
        (For large files, a generator would be better, but strings are requested for the interface).
        """
        content = self.file.read()
        if not content:
            return ""
            
        bit_list = []
        # Convert each byte to 8 bits
        for byte in content:
            # format(byte, '08b') creates '00010100'
            bit_list.append(f"{byte:08b}")
            
        full_string = "".join(bit_list)
        
        # Remove padding from the end
        if self.padding_count > 0:
            full_string = full_string[:-self.padding_count]
            
        return full_string

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
