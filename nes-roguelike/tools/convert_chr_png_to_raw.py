#!/usr/bin/env python3
"""
Convert PNG-format CHR data to raw binary CHR format for NES ROMs.
This script takes the PNG tile sheets extracted by organize_arkista_assets.py
and converts them to raw binary CHR data for inclusion in NES ROMs.
"""

import os
import sys
from PIL import Image

def png_to_chr(png_path, chr_path):
    """Convert a PNG file to raw CHR data."""
    print(f"Converting {png_path} to {chr_path}...")
    
    # Open the PNG file
    img = Image.open(png_path)
    width, height = img.size
    
    # Verify dimensions (should be 128x128 for a full CHR bank)
    if width != 128 or height != 128:
        print(f"Warning: Expected 128x128 image, got {width}x{height}")
    
    # Create binary data
    chr_data = bytearray()
    
    # Process each 8x8 tile
    for y_tile in range(0, height, 8):
        for x_tile in range(0, width, 8):
            # For each tile, we need to convert to the NES CHR format
            # NES uses two planes of 8-bit data for each tile
            plane0 = bytearray(8)
            plane1 = bytearray(8)
            
            # Process each row of the tile
            for row in range(8):
                # Process each pixel in the row
                for col in range(8):
                    x = x_tile + col
                    y = y_tile + row
                    
                    if x >= width or y >= height:
                        pixel = 0  # Padding
                    else:
                        # Get the pixel color (assuming grayscale or palette image)
                        pixel = img.getpixel((x, y))
                        
                        # For palette images, we need to extract the index
                        if isinstance(pixel, tuple):
                            # Just use the brightness as an approximation
                            pixel = sum(pixel[:3]) // 3
                        
                        # Normalize to 0-3 range for NES (2 bits per pixel)
                        pixel = min(3, pixel // 64)
                    
                    # Set the bits in the appropriate plane
                    if pixel & 0x1:  # Bit 0
                        plane0[row] |= (1 << (7 - col))
                    if pixel & 0x2:  # Bit 1
                        plane1[row] |= (1 << (7 - col))
            
            # Add the planes to our CHR data
            chr_data.extend(plane0)
            chr_data.extend(plane1)
    
    # Write the CHR data to the output file
    with open(chr_path, 'wb') as f:
        f.write(chr_data)
    
    print(f"Converted {len(chr_data)} bytes of CHR data")

def main():
    # Get the paths from command line arguments or use defaults
    if len(sys.argv) >= 3:
        png_path = sys.argv[1]
        chr_path = sys.argv[2]
    else:
        # Default paths
        png_path = '../assets/arkista_assets/chr_data/chr_bank_0.png'
        chr_path = '../assets/arkista_assets/chr_data/chr_bank_0.chr'
    
    # Make sure the output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(chr_path)), exist_ok=True)
    
    # Convert the PNG to CHR
    png_to_chr(png_path, chr_path)

if __name__ == '__main__':
    main()
