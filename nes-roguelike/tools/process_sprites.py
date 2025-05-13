#!/usr/bin/env python3
"""
Sprite Organization Tool for Craven Caverns NES Roguelike
--------------------------------------------------------
This tool processes the extracted CHR data from Arkista's Ring and
organizes it into categories useful for a roguelike game.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import argparse
from PIL import Image

# Categories to organize sprites
CATEGORIES = {
    "player": "Player character sprites",
    "enemies": "Enemy sprites",
    "items": "Item sprites (weapons, armor, potions, etc.)",
    "environment": "Environment tiles (walls, floors, doors)",
    "ui": "UI elements (fonts, indicators, etc.)"
}

def create_category_directories(base_dir):
    """Create directories for each sprite category"""
    for category in CATEGORIES:
        os.makedirs(os.path.join(base_dir, category), exist_ok=True)
    
    print(f"Created category directories in {base_dir}")

def extract_sprites(source_path, output_dir, tile_size=8):
    """Extract individual sprites from a CHR bank image"""
    # Load the source image
    try:
        source_img = Image.open(source_path)
    except Exception as e:
        print(f"Error opening image {source_path}: {e}")
        return False
    
    # Get image dimensions
    width, height = source_img.size
    
    # Calculate number of tiles in each dimension
    tiles_x = width // tile_size
    tiles_y = height // tile_size
    
    # Extract each tile
    for y in range(tiles_y):
        for x in range(tiles_x):
            # Calculate tile position
            left = x * tile_size
            upper = y * tile_size
            right = left + tile_size
            lower = upper + tile_size
            
            # Crop the tile
            tile = source_img.crop((left, upper, right, lower))
            
            # Save the tile
            tile_filename = f"tile_{y * tiles_x + x:03d}.png"
            tile_path = os.path.join(output_dir, "all_tiles", tile_filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.join(output_dir, "all_tiles"), exist_ok=True)
            
            # Save the tile
            tile.save(tile_path)
    
    print(f"Extracted {tiles_x * tiles_y} tiles from {source_path}")
    return True

def create_sprite_sheets(input_dir, output_dir):
    """Create larger sprite sheets for common game elements"""
    # Player character (8x16 or 16x16)
    # This would need to be customized based on actual sprite locations
    
    print("Creating sprite sheets is a manual process that requires")
    print("selecting specific tiles. For now, individual tiles have been")
    print("extracted to the 'all_tiles' directory. You can use these to")
    print("create custom sprite sheets or copy them to the appropriate")
    print("category directories.")

def main():
    parser = argparse.ArgumentParser(description='Process sprites for a NES roguelike game')
    parser.add_argument('input_dir', help='Directory containing CHR bank PNG files')
    parser.add_argument('--output', '-o', default='processed_sprites', 
                        help='Output directory for processed sprites')
    
    args = parser.parse_args()
    
    # Check if input directory exists
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory {args.input_dir} does not exist")
        return False
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(args.input_dir), args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Create category directories
    create_category_directories(output_dir)
    
    # Process each CHR bank image
    for filename in os.listdir(args.input_dir):
        if filename.endswith(".png") and filename.startswith("chr_bank_"):
            source_path = os.path.join(args.input_dir, filename)
            extract_sprites(source_path, output_dir)
    
    # Create sprite sheets
    create_sprite_sheets(args.input_dir, output_dir)
    
    print(f"Sprite processing completed successfully!")
    print(f"Processed sprites are in: {output_dir}")
    print("\nNext steps:")
    print("1. Review the extracted tiles in the 'all_tiles' directory")
    print("2. Move tiles to appropriate category directories based on their purpose")
    print("3. Update sprite indices in your game code to reference these tiles")
    
    return True

if __name__ == '__main__':
    main()
