#!/usr/bin/env python3
"""
Arkista's Ring Background Extractor
-----------------------------------
Extracts background tiles and level layouts from the ArkistasRingMapAllStages.png file.
Preserves the original palette and organizes tiles by theme/level.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import json
import argparse
from PIL import Image, ImageDraw

# Constants
TILE_SIZE = 16      # Background tile size (typically 16x16 in games like Arkista's Ring)
TRANSPARENT_COLOR = (0, 0, 0, 0)  # Transparent color for output sprites

def extract_background_tiles(image_path, output_dir, tile_size=TILE_SIZE):
    """
    Extract unique background tiles from the map image
    
    Args:
        image_path: Path to the map image
        output_dir: Directory to save extracted tiles
        tile_size: Size of tiles to extract (default 16x16)
    
    Returns:
        Dictionary mapping tile hash to tile info
    """
    try:
        source_img = Image.open(image_path)
        # Convert to RGBA if needed
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return {}
    
    # Get image dimensions
    width, height = source_img.size
    
    # Create output directory for tiles
    tiles_dir = os.path.join(output_dir, "tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    
    unique_tiles = {}
    tile_count = 0
    
    # Scan the image for tiles
    for y in range(0, height - tile_size + 1, tile_size):
        for x in range(0, width - tile_size + 1, tile_size):
            # Crop the tile
            tile = source_img.crop((x, y, x + tile_size, y + tile_size))
            
            # Create a hash of the tile to identify duplicates
            tile_hash = hash(tile.tobytes())
            
            # If we haven't seen this tile before
            if tile_hash not in unique_tiles:
                tile_count += 1
                tile_id = f"bg_tile_{tile_count:03d}"
                
                # Save the tile
                tile_filename = f"{tile_id}.png"
                tile_path = os.path.join(tiles_dir, tile_filename)
                tile.save(tile_path)
                
                # Store tile info
                unique_tiles[tile_hash] = {
                    "id": tile_id,
                    "hash": tile_hash,
                    "path": tile_path,
                    "first_position": (x, y),
                    "positions": [(x, y)]
                }
            else:
                # Add this position to the existing tile
                unique_tiles[tile_hash]["positions"].append((x, y))
    
    print(f"Extracted {len(unique_tiles)} unique background tiles to {tiles_dir}")
    return unique_tiles

def detect_levels(image_path, unique_tiles, output_dir, tile_size=TILE_SIZE):
    """
    Detect different level layouts based on the background image
    and create level maps using tile IDs
    """
    source_img = Image.open(image_path)
    # Convert to RGBA to ensure consistent pixel format
    if source_img.mode != 'RGBA':
        source_img = source_img.convert('RGBA')
    
    width, height = source_img.size
    
    # Create reverse lookup from position to tile ID
    position_to_tile = {}
    for tile_hash, tile_info in unique_tiles.items():
        for pos in tile_info["positions"]:
            position_to_tile[pos] = tile_info["id"]
    
    # Scan for potential level boundaries
    # In Arkista's Ring, levels are typically laid out vertically in the map image
    potential_levels = []
    
    # Look for empty rows as level separators
    empty_rows = []
    for y in range(0, height - tile_size + 1, tile_size):
        is_empty_row = True
        for x in range(0, width - tile_size + 1, tile_size):
            tile = source_img.crop((x, y, x + tile_size, y + tile_size))
            # Check if this tile is empty (all pixels are transparent/black)
            # Convert tile to RGBA to ensure we can access color components
            tile_rgba = tile.convert('RGBA')
            if not all(pixel[0] == 0 and pixel[1] == 0 and pixel[2] == 0 for pixel in tile_rgba.getdata()):
                is_empty_row = False
                break
        
        if is_empty_row:
            empty_rows.append(y)
    
    # Use empty rows to define level boundaries
    level_boundaries = []
    start_y = 0
    
    for empty_y in empty_rows:
        # If there's content between the last boundary and this empty row
        if empty_y - start_y > tile_size:
            level_boundaries.append((start_y, empty_y))
        start_y = empty_y + tile_size
    
    # Add the last level if needed
    if height - start_y > tile_size:
        level_boundaries.append((start_y, height))
    
    # Extract each level
    levels_dir = os.path.join(output_dir, "levels")
    os.makedirs(levels_dir, exist_ok=True)
    
    level_data = []
    
    for i, (level_start, level_end) in enumerate(level_boundaries):
        level_id = f"level_{i+1:02d}"
        level_height = (level_end - level_start) // tile_size
        level_width = width // tile_size
        
        # Create a visual representation of the level
        level_img = source_img.crop((0, level_start, width, level_end))
        level_img_path = os.path.join(levels_dir, f"{level_id}.png")
        level_img.save(level_img_path)
        
        # Create a tile map for this level
        tile_map = []
        for y in range(level_start, level_end, tile_size):
            row = []
            for x in range(0, width, tile_size):
                pos = (x, y)
                tile_id = position_to_tile.get(pos, "empty")
                row.append(tile_id)
            tile_map.append(row)
        
        level_info = {
            "id": level_id,
            "dimensions": (level_width, level_height),
            "pixel_range": (level_start, level_end),
            "tile_map": tile_map,
            "image_path": level_img_path
        }
        
        level_data.append(level_info)
        
        # Create the level's tile map as a JSON file
        level_map_path = os.path.join(levels_dir, f"{level_id}_map.json")
        with open(level_map_path, 'w') as f:
            json.dump(level_info, f, indent=2)
    
    print(f"Extracted {len(level_data)} level layouts to {levels_dir}")
    return level_data

def create_tileset(unique_tiles, output_dir, columns=16):
    """
    Create a combined tileset from extracted background tiles
    """
    if not unique_tiles:
        return None
    
    # Get tile images
    tile_images = []
    for tile_hash, tile_info in unique_tiles.items():
        try:
            img = Image.open(tile_info["path"])
            tile_images.append((tile_info["id"], img))
        except Exception as e:
            print(f"Error opening tile {tile_info['path']}: {e}")
    
    if not tile_images:
        return None
    
    # Sort tiles by ID
    tile_images.sort(key=lambda x: x[0])
    
    # Determine tileset dimensions
    tile_width = tile_images[0][1].width
    tile_height = tile_images[0][1].height
    
    cols = min(columns, len(tile_images))
    rows = (len(tile_images) + cols - 1) // cols
    
    # Create tileset image
    sheet_width = cols * tile_width
    sheet_height = rows * tile_height
    sheet_img = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Add tiles to sheet
    for i, (tile_id, img) in enumerate(tile_images):
        x = (i % cols) * tile_width
        y = (i // cols) * tile_height
        sheet_img.paste(img, (x, y))
    
    # Save tileset
    sheet_path = os.path.join(output_dir, "background_tileset.png")
    sheet_img.save(sheet_path)
    print(f"Created background tileset with {len(tile_images)} tiles: {sheet_path}")
    
    return sheet_path

def create_config_file(unique_tiles, levels, output_dir):
    """
    Create a configuration file mapping tile IDs to their properties
    """
    # Convert the dictionary to a list for the config
    tiles_list = []
    for tile_hash, tile_info in unique_tiles.items():
        tiles_list.append({
            "id": tile_info["id"],
            "first_position": tile_info["first_position"],
            "positions_count": len(tile_info["positions"]),
            "relative_path": os.path.relpath(tile_info["path"], output_dir)
        })
    
    # Sort tiles by ID
    tiles_list.sort(key=lambda x: x["id"])
    
    config = {
        "tile_size": TILE_SIZE,
        "tiles_count": len(tiles_list),
        "levels_count": len(levels),
        "tiles": tiles_list,
        "levels": [{
            "id": level["id"],
            "dimensions": level["dimensions"],
            "relative_path": os.path.relpath(level["image_path"], output_dir)
        } for level in levels]
    }
    
    config_path = os.path.join(output_dir, "background_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created background configuration file: {config_path}")
    return config_path

def main():
    parser = argparse.ArgumentParser(description='Arkista\'s Ring Background Extractor')
    parser.add_argument('--input', '-i', 
                        default='../arspritesheets/ArkistasRingMapAllStages.png',
                        help='Path to the background map image')
    parser.add_argument('--output', '-o', 
                        default='../assets/extracted_backgrounds',
                        help='Output directory for extracted backgrounds')
    parser.add_argument('--tile-size', '-t', type=int, default=16,
                        help='Size of background tiles to extract')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file {args.input} does not exist")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Extract unique tiles
    unique_tiles = extract_background_tiles(args.input, args.output, args.tile_size)
    
    if not unique_tiles:
        print("No background tiles were extracted.")
        return 1
    
    # Detect level layouts
    levels = detect_levels(args.input, unique_tiles, args.output, args.tile_size)
    
    # Create combined tileset
    create_tileset(unique_tiles, args.output)
    
    # Create configuration file
    create_config_file(unique_tiles, levels, args.output)
    
    print("Background extraction completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
