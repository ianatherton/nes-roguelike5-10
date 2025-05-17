#!/usr/bin/env python3
"""
PNG to CHR Converter for NES Assets
Converts PNG images to NES CHR format for use in NES games.

The script handles both background tiles and sprites.
"""

import os
import sys
import argparse
from PIL import Image
import glob

def rgb_to_nes_color(rgb):
    """Convert an RGB value to the closest NES palette index."""
    # Simplified NES palette conversion - just uses brightness
    # In real implementation, you'd want a proper NES palette mapping
    brightness = (rgb[0] + rgb[1] + rgb[2]) // 3
    if brightness < 64:
        return 0  # Transparent/black
    elif brightness < 128:
        return 1  # Dark color
    elif brightness < 192:
        return 2  # Medium color
    else:
        return 3  # Light color

def convert_tile(img, x_offset=0, y_offset=0, tile_size=8):
    """Convert an 8x8 section of an image to NES tile data (2 bitplanes)."""
    # NES tiles are 8x8 with 2 bits per pixel (2 bitplanes)
    # Each bitplane is 8 bytes, so 16 bytes total per tile
    bitplane0 = bytearray(8)
    bitplane1 = bytearray(8)
    
    # Process each row in the tile
    for y in range(8):
        bp0_byte = 0
        bp1_byte = 0
        
        # Process each pixel in the row
        for x in range(8):
            try:
                pixel = img.getpixel((x_offset + x, y_offset + y))
            except IndexError:
                # If we're out of bounds, assume transparent
                pixel = (0, 0, 0, 0)
            
            # Handle different image formats
            if isinstance(pixel, int):  # Paletted image
                nes_color = pixel & 3  # Use lower 2 bits
            elif len(pixel) >= 3:  # RGB or RGBA
                if len(pixel) > 3 and pixel[3] == 0:  # Transparent
                    nes_color = 0
                else:
                    nes_color = rgb_to_nes_color(pixel)
            else:
                nes_color = 0
            
            # Set bits in the bitplanes if color value has those bits set
            if nes_color & 1:
                bp0_byte |= (1 << (7 - x))
            if nes_color & 2:
                bp1_byte |= (1 << (7 - x))
        
        # Store the bytes for this row
        bitplane0[y] = bp0_byte
        bitplane1[y] = bp1_byte
    
    # Return the combined bitplanes (upper followed by lower)
    return bytes(bitplane0) + bytes(bitplane1)

def convert_image_to_chr(image_path, output_path, tile_size=8, sprite_mode=False):
    """Convert a PNG image to CHR data."""
    # Load the image
    img = Image.open(image_path)
    
    # For sprite mode, we expect 16x16 sprite tiles (which are made of 4 8x8 NES tiles)
    # which we need to arrange in a specific order
    if sprite_mode and (img.width, img.height) == (16, 16):
        # Sprite is 16x16, so we need to convert it to 4 8x8 tiles
        # in the order: top-left, top-right, bottom-left, bottom-right
        chr_data = b''
        chr_data += convert_tile(img, 0, 0)     # Top-left
        chr_data += convert_tile(img, 8, 0)     # Top-right
        chr_data += convert_tile(img, 0, 8)     # Bottom-left
        chr_data += convert_tile(img, 8, 8)     # Bottom-right
        return chr_data
    
    # Standard mode - convert entire image to CHR tiles
    width_tiles = img.width // tile_size
    height_tiles = img.height // tile_size
    
    chr_data = bytearray()
    
    # Process each tile in the image
    for y_tile in range(height_tiles):
        for x_tile in range(width_tiles):
            # Convert the tile
            tile_data = convert_tile(
                img, 
                x_tile * tile_size, 
                y_tile * tile_size,
                tile_size
            )
            chr_data.extend(tile_data)
    
    return bytes(chr_data)

def convert_dir_to_chr(input_dir, output_path, sprite_mode=False):
    """Convert all PNG files in a directory to a single CHR file."""
    # Get all PNG files in the directory
    png_files = glob.glob(os.path.join(input_dir, "*.png"))
    png_files.sort()  # Sort for consistent output
    
    print(f"Found {len(png_files)} PNG files in {input_dir}")
    
    # Convert each file
    chr_data = bytearray()
    for png_file in png_files:
        print(f"Converting {os.path.basename(png_file)}...")
        file_data = convert_image_to_chr(png_file, None, 8, sprite_mode)
        chr_data.extend(file_data)
    
    # Write the CHR data to the output file
    with open(output_path, 'wb') as f:
        f.write(chr_data)
    
    print(f"Wrote {len(chr_data)} bytes to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Convert PNG images to NES CHR format.')
    parser.add_argument('--input', help='Input PNG file')
    parser.add_argument('--input_dir', help='Input directory containing PNG files')
    parser.add_argument('--output_file', required=True, help='Output CHR file')
    parser.add_argument('--sprite_mode', action='store_true', 
                      help='Process input as 16x16 sprite tiles (each becomes 4 8x8 tiles)')
    
    args = parser.parse_args()
    
    if args.input and os.path.exists(args.input):
        # Convert a single file
        chr_data = convert_image_to_chr(args.input, args.output_file, 8, args.sprite_mode)
        with open(args.output_file, 'wb') as f:
            f.write(chr_data)
        print(f"Wrote {len(chr_data)} bytes to {args.output_file}")
    elif args.input_dir and os.path.exists(args.input_dir):
        # Convert all files in a directory
        convert_dir_to_chr(args.input_dir, args.output_file, args.sprite_mode)
    else:
        print("Error: Please specify either --input or --input_dir with a valid path")
        sys.exit(1)

if __name__ == "__main__":
    main()
