#!/usr/bin/env python3
"""
Simple Sprite Extraction Tool for Arkista's Ring
------------------------------------------------
This tool extracts and combines sprites from Arkista's Ring CHR banks without
attempting to identify or categorize them. It extracts:
1. All possible 16x16 character sprites (2x2 tiles) using correct quadrant arrangement
2. All individual 8x8 tiles for UI elements, icons, etc.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import json
import argparse
from PIL import Image, ImageDraw

# Constants for NES sprite properties
TILE_SIZE = 8      # Standard NES tile size is 8x8 pixels
SPRITE_SIZE = 16   # Character sprites are 16x16 (2x2 tiles)

# Sprite arrangement pattern for Arkista's Ring (swapped top-right and bottom-left quadrants)
ARKISTA_ARRANGEMENT = [0, 2, 1, 3]

def extract_tiles(image_path, output_dir):
    """Extract all individual 8x8 tiles from a CHR bank image"""
    try:
        source_img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return []
    
    # Get image dimensions
    width, height = source_img.size
    
    # Calculate number of tiles in each dimension
    tiles_x = width // TILE_SIZE
    tiles_y = height // TILE_SIZE
    total_tiles = tiles_x * tiles_y
    
    print(f"Found {total_tiles} individual 8x8 tiles")
    
    tiles = []
    
    # Create output directory for tiles
    tiles_dir = os.path.join(output_dir, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    
    # Extract each tile
    for y in range(tiles_y):
        for x in range(tiles_x):
            # Calculate tile position
            left = x * TILE_SIZE
            upper = y * TILE_SIZE
            right = left + TILE_SIZE
            lower = upper + TILE_SIZE
            
            # Crop the tile
            tile = source_img.crop((left, upper, right, lower))
            tile_idx = y * tiles_x + x
            
            # Save the tile
            tile_filename = f"tile_{tile_idx:03d}.png"
            tile_path = os.path.join(tiles_dir, tile_filename)
            tile.save(tile_path)
            
            # Add to the tiles list
            tiles.append(tile)
    
    print(f"Extracted {len(tiles)} individual tiles to {tiles_dir}")
    return tiles

def extract_character_sprites(tiles, output_dir, arrangement=None):
    """Extract all possible 16x16 character sprites (2x2 tiles)"""
    if arrangement is None:
        arrangement = ARKISTA_ARRANGEMENT
    
    # We'll assume all potential 2x2 tile combinations with a 4-tile stride
    # This should catch most character sprites without making assumptions about what they are
    sprites_dir = os.path.join(output_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    
    # Track all extracted sprites
    sprites = []
    
    # Limit to a reasonable number of sprites to avoid creating garbage
    # Only process complete sets of 4 tiles, with a stride of 4
    # This assumes character sprites are aligned on 4-tile boundaries (common in NES games)
    for base_idx in range(0, len(tiles) - 3, 4):  # Step by 4 tiles at a time
        sprite_img = Image.new('RGBA', (SPRITE_SIZE, SPRITE_SIZE), (0, 0, 0, 0))
        
        # Check if we have enough tiles for a complete sprite
        if base_idx + 3 >= len(tiles):
            break
        
        # Use the special Arkista's Ring tile arrangement
        for i, rel_idx in enumerate(arrangement):
            # Calculate position in the composed image
            x = (i % 2) * TILE_SIZE
            y = (i // 2) * TILE_SIZE
            
            # Get the actual tile index
            tile_idx = base_idx + rel_idx
            
            # Ensure the tile exists
            if tile_idx < len(tiles):
                sprite_img.paste(tiles[tile_idx], (x, y))
        
        # Save the sprite
        sprite_filename = f"sprite_{base_idx:03d}.png"
        sprite_path = os.path.join(sprites_dir, sprite_filename)
        sprite_img.save(sprite_path)
        sprites.append({
            "id": f"sprite_{base_idx:03d}",
            "base_tile": base_idx,
            "path": sprite_path
        })
    
    print(f"Extracted {len(sprites)} potential character sprites to {sprites_dir}")
    return sprites

def create_sprite_sheet(sprites, output_dir):
    """Create a sprite sheet containing all extracted character sprites"""
    if not sprites:
        return None
    
    # Get all sprite images
    sprite_images = []
    for sprite in sprites:
        try:
            img = Image.open(sprite["path"])
            sprite_images.append((sprite["id"], img))
        except Exception as e:
            print(f"Error opening sprite {sprite['path']}: {e}")
    
    if not sprite_images:
        return None
    
    # Determine sprite sheet dimensions
    sprite_width = sprite_images[0][1].width
    sprite_height = sprite_images[0][1].height
    
    # Arrange sprites in a grid
    cols = min(16, len(sprite_images))  # Max 16 columns
    rows = (len(sprite_images) + cols - 1) // cols  # Ceiling division
    
    # Create sprite sheet image
    sheet_width = cols * sprite_width
    sheet_height = rows * sprite_height
    sheet_img = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Add sprites to sheet
    for i, (sprite_id, img) in enumerate(sprite_images):
        x = (i % cols) * sprite_width
        y = (i // cols) * sprite_height
        sheet_img.paste(img, (x, y))
    
    # Save sprite sheet
    sheet_path = os.path.join(output_dir, "sprite_sheet.png")
    sheet_img.save(sheet_path)
    print(f"Created sprite sheet with {len(sprite_images)} sprites: {sheet_path}")
    
    return sheet_path

def create_config_file(sprites, output_dir):
    """Create a configuration file mapping sprite IDs to base tile indices"""
    config = {
        "sprite_size": SPRITE_SIZE,
        "tile_size": TILE_SIZE,
        "tile_arrangement": ARKISTA_ARRANGEMENT,
        "sprites": {}
    }
    
    for sprite in sprites:
        config["sprites"][sprite["id"]] = {
            "base_tile": sprite["base_tile"],
            "relative_path": os.path.relpath(sprite["path"], output_dir)
        }
    
    config_path = os.path.join(output_dir, "sprite_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created sprite configuration file: {config_path}")
    return config_path

def main():
    parser = argparse.ArgumentParser(description='Simple Sprite Extraction Tool for Arkista\'s Ring')
    parser.add_argument('input', help='Path to CHR bank PNG file')
    parser.add_argument('--output', '-o', default='extracted_sprites', 
                        help='Output directory for extracted sprites')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file {args.input} does not exist")
        return False
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    print(f"Processing CHR bank image: {args.input}")
    
    # Extract individual tiles
    tiles = extract_tiles(args.input, args.output)
    if not tiles:
        print("Failed to extract tiles")
        return False
    
    # Extract character sprites
    sprites = extract_character_sprites(tiles, args.output)
    
    # Create sprite sheet
    create_sprite_sheet(sprites, args.output)
    
    # Create configuration file
    create_config_file(sprites, args.output)
    
    print(f"\nSprite extraction complete!")
    print(f"Results are in: {args.output}")
    print(f"- {len(tiles)} individual 8x8 tiles in: {os.path.join(args.output, 'tiles')}")
    print(f"- {len(sprites)} character sprites in: {os.path.join(args.output, 'sprites')}")
    print("\nNext steps:")
    print("1. Review the extracted sprites and organize them by character")
    print("2. Group similar sprites that belong to the same character")
    print("3. Create a custom metadata file that maps sprites to characters")
    return True

if __name__ == '__main__':
    main()
