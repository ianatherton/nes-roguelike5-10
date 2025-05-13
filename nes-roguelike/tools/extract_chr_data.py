#!/usr/bin/env python3
"""
NES ROM CHR Data Extraction Tool
--------------------------------
This tool extracts character/tile data (CHR) from NES ROMs and saves it as PNG images.
Specifically designed to help extract assets from Arkista's Ring for the Craven Caverns project.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import argparse
from PIL import Image

NES_HEADER_SIZE = 16  # Standard iNES header size
CHR_BANK_SIZE = 8192  # Size of one CHR bank (8KB)
TILES_PER_BANK = 512  # Number of 8x8 tiles in a bank

def extract_chr_banks(rom_path, output_dir):
    """Extract CHR banks from a NES ROM file"""
    try:
        # Make sure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Open and read the ROM file
        with open(rom_path, 'rb') as rom_file:
            rom_data = rom_file.read()
        
        # Check if it's a valid iNES format
        if rom_data[:4] != b'NES\x1a':
            print("Error: Not a valid NES ROM (missing iNES header)")
            return False
        
        # Get the number of CHR banks
        chr_banks = rom_data[5]
        if chr_banks == 0:
            print("This ROM uses CHR RAM rather than CHR ROM and cannot be extracted directly.")
            return False
        
        print(f"Found {chr_banks} CHR banks in the ROM.")
        
        # Calculate where the CHR data begins
        prg_banks = rom_data[4]
        chr_start = NES_HEADER_SIZE + (prg_banks * 16384)  # 16KB per PRG bank
        
        # Extract each CHR bank
        for bank in range(chr_banks):
            bank_start = chr_start + (bank * CHR_BANK_SIZE)
            bank_end = bank_start + CHR_BANK_SIZE
            bank_data = rom_data[bank_start:bank_end]
            
            # Convert the bank to an image (16x32 tiles, each 8x8 pixels)
            img = Image.new('RGB', (128, 128), color='black')
            pixels = img.load()
            
            # NES color palette (simplified grayscale for now)
            palette = [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)]
            
            # Process each tile in the bank
            for tile_idx in range(TILES_PER_BANK // 2):  # Process in 8x16 pairs
                tile_offset = tile_idx * 16
                
                # Calculate position in the output image
                tile_x = (tile_idx % 16) * 8
                tile_y = (tile_idx // 16) * 8
                
                # Process each row of the tile
                for row in range(8):
                    # Each row is defined by 2 bytes in the NES CHR format
                    byte1 = bank_data[tile_offset + row]
                    byte2 = bank_data[tile_offset + row + 8]
                    
                    # Process each pixel in the row
                    for col in range(8):
                        # Get the color value (0-3) for this pixel
                        bit1 = (byte1 >> (7 - col)) & 1
                        bit2 = (byte2 >> (7 - col)) & 1
                        color_idx = (bit2 << 1) | bit1
                        
                        # Set the pixel in the image
                        pixels[tile_x + col, tile_y + row] = palette[color_idx]
            
            # Save the bank as a PNG image
            output_path = os.path.join(output_dir, f'chr_bank_{bank}.png')
            img.save(output_path)
            print(f"Saved CHR bank {bank} to {output_path}")
        
        return True
    
    except Exception as e:
        print(f"Error extracting CHR data: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract CHR data from NES ROMs')
    parser.add_argument('rom_path', help='Path to the NES ROM file')
    parser.add_argument('--output', '-o', default='chr_output', 
                        help='Output directory for extracted files')
    
    args = parser.parse_args()
    
    print(f"Extracting CHR data from: {args.rom_path}")
    success = extract_chr_banks(args.rom_path, args.output)
    
    if success:
        print("Extraction completed successfully!")
    else:
        print("Extraction failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
