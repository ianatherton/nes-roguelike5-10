#!/usr/bin/env python3
"""
Grid-Based Level Extractor for Arkista's Ring
---------------------------------------------
Extracts levels and background tiles from the ArkistasRingMapAllStages.png
based on the grid layout visible in the image.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import json
import argparse
from collections import defaultdict
from PIL import Image, ImageDraw, ImageStat

# Constants
TILE_SIZE = 16      # Background tile size
GRID_WIDTH = 4      # Number of level slots horizontally in the grid
GRID_HEIGHT = 9     # Approximate number of rows in the grid
LEVEL_WIDTH = 256   # Width of a level in pixels (typically 16 tiles)
LEVEL_HEIGHT = 240  # Height of a level in pixels (typically 15 tiles)

def extract_levels_from_grid(image_path, output_dir):
    """
    Extract levels based on the grid layout visible in the image
    """
    try:
        source_img = Image.open(image_path)
        # Convert to RGBA for consistent processing
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return []
    
    # Get image dimensions
    width, height = source_img.size
    print(f"Image dimensions: {width}x{height}")
    
    # Create output directory for levels
    levels_dir = os.path.join(output_dir, "levels")
    os.makedirs(levels_dir, exist_ok=True)
    
    # Calculate level dimensions and grid dimensions
    # Use fixed values for Arkista's Ring levels
    level_width = LEVEL_WIDTH
    level_height = LEVEL_HEIGHT
    
    # Lists to track levels and tiles
    levels = []
    all_tiles = {}
    tile_count = 0
    tile_positions = {}
    
    # Track unique level types by content hash
    unique_level_types = {}
    
    # Extract levels from the grid layout
    level_num = 0
    for grid_y in range(GRID_HEIGHT):
        for grid_x in range(GRID_WIDTH):
            # Calculate level position
            level_x = grid_x * level_width
            level_y = grid_y * level_height
            
            # Skip if outside image bounds
            if level_x + level_width > width or level_y + level_height > height:
                continue
                
            # Extract the level image
            level_img = source_img.crop((level_x, level_y, 
                                         level_x + level_width, 
                                         level_y + level_height))
            
            # Check if level has content (not all black)
            if is_empty_image(level_img):
                continue
                
            level_num += 1
            level_id = f"level_{level_num:02d}"
            
            # Save the level image
            level_path = os.path.join(levels_dir, f"{level_id}.png")
            level_img.save(level_path)
            
            # Get level type based on content
            level_hash = hash(level_img.tobytes())
            if level_hash in unique_level_types:
                level_type = unique_level_types[level_hash]
            else:
                # Determine level type based on dominant colors
                level_type = classify_level_type(level_img)
                unique_level_types[level_hash] = level_type
            
            # Extract tiles from this level
            level_tiles, level_tile_map = extract_tiles_from_level(
                level_img, level_id, level_x, level_y, output_dir, all_tiles, tile_count)
            
            # Update tile count
            tile_count += len(level_tiles)
            
            # Update tile positions
            for pos, tile_id in level_tile_map.items():
                tile_positions[pos] = tile_id
                
            # Add new tiles to all_tiles
            all_tiles.update(level_tiles)
            
            # Store level information
            level_info = {
                "id": level_id,
                "grid_position": (grid_x, grid_y),
                "pixel_position": (level_x, level_y),
                "width_pixels": level_width,
                "height_pixels": level_height,
                "width_tiles": level_width // TILE_SIZE,
                "height_tiles": level_height // TILE_SIZE,
                "type": level_type,
                "image_path": level_path,
                "tile_count": len(level_tiles)
            }
            
            levels.append(level_info)
            print(f"Extracted level {level_id} ({level_type}) at grid position ({grid_x}, {grid_y})")
    
    print(f"Extracted {len(levels)} levels and {len(all_tiles)} unique tiles")
    return levels, all_tiles, tile_positions

def is_empty_image(img):
    """Check if an image is mostly empty (black)"""
    stat = ImageStat.Stat(img)
    if sum(stat.mean[:3]) < 10:  # Low brightness threshold
        return True
    return False

def classify_level_type(level_img):
    """Classify level type based on dominant colors and patterns"""
    # Convert to RGB for color analysis
    if level_img.mode != 'RGB':
        level_img = level_img.convert('RGB')
        
    # Get color statistics
    stat = ImageStat.Stat(level_img)
    r, g, b = stat.mean[:3]
    
    # Simple classification based on dominant colors
    if b > max(r, g) + 50:  # Mostly blue - water levels
        return "water"
    elif g > max(r, b) + 50:  # Mostly green - forest/grass levels
        return "forest"
    elif r > 150 and g < 100 and b > 150:  # Purple/pink - special levels
        return "special"
    elif r > 150 and g > 150 and b < 100:  # Yellow/orange - desert/fire levels
        return "desert"
    elif abs(r - g) < 30 and abs(g - b) < 30 and r > 150:  # Light gray/white - maze/dungeon
        return "stone_maze"
    elif abs(r - g) < 30 and abs(g - b) < 30 and r < 100:  # Dark gray - cave/dungeon
        return "dungeon"
    else:
        return "mixed"

def extract_tiles_from_level(level_img, level_id, level_x, level_y, output_dir, existing_tiles, tile_count):
    """Extract unique tiles from a level image"""
    # Create directory for tiles
    tiles_dir = os.path.join(output_dir, "tiles", level_id)
    os.makedirs(tiles_dir, exist_ok=True)
    
    # Get level dimensions
    width, height = level_img.size
    
    # Track new tiles and tile map
    new_tiles = {}
    tile_map = {}
    
    # Extract tiles
    for y in range(0, height, TILE_SIZE):
        for x in range(0, width, TILE_SIZE):
            # Skip if outside bounds
            if x + TILE_SIZE > width or y + TILE_SIZE > height:
                continue
                
            # Extract tile
            tile = level_img.crop((x, y, x + TILE_SIZE, y + TILE_SIZE))
            
            # Skip empty tiles
            if is_empty_image(tile):
                continue
                
            # Hash the tile to check for duplicates
            tile_hash = hash(tile.tobytes())
            
            # Check if we've seen this tile before (globally)
            tile_id = None
            for existing_id, existing_tile in existing_tiles.items():
                if existing_tile["hash"] == tile_hash:
                    tile_id = existing_id
                    break
            
            # If not, create a new tile
            if not tile_id:
                next_count = tile_count + len(new_tiles) + 1
                tile_id = f"tile_{next_count:04d}"
                
                # Save the tile
                tile_path = os.path.join(tiles_dir, f"{tile_id}.png")
                tile.save(tile_path)
                
                # Store tile info
                new_tiles[tile_id] = {
                    "id": tile_id,
                    "hash": tile_hash,
                    "source_level": level_id,
                    "path": tile_path,
                    "position_in_level": (x, y),
                    "global_position": (level_x + x, level_y + y)
                }
            
            # Add to tile map
            global_pos = (level_x + x, level_y + y)
            tile_map[global_pos] = tile_id
    
    return new_tiles, tile_map

def create_level_tile_maps(levels, tile_positions, output_dir):
    """Create tile maps for each level"""
    for level in levels:
        level_x, level_y = level["pixel_position"]
        level_width = level["width_pixels"]
        level_height = level["height_pixels"]
        
        # Create tile map for this level
        tile_map = []
        for y in range(level_y, level_y + level_height, TILE_SIZE):
            row = []
            for x in range(level_x, level_x + level_width, TILE_SIZE):
                pos = (x, y)
                tile_id = tile_positions.get(pos, "empty")
                row.append(tile_id)
            tile_map.append(row)
        
        # Add tile map to level info
        level["tile_map"] = tile_map
        
        # Create JSON file for this level
        map_path = os.path.join(output_dir, "levels", f"{level['id']}_map.json")
        with open(map_path, 'w') as f:
            json.dump({
                "id": level["id"],
                "type": level["type"],
                "dimensions": {
                    "width_tiles": level["width_tiles"],
                    "height_tiles": level["height_tiles"]
                },
                "tile_map": level["tile_map"]
            }, f, indent=2)
    
    print(f"Created tile maps for {len(levels)} levels")
    return levels

def organize_tiles_by_type(all_tiles, levels, output_dir):
    """Organize tiles by level type"""
    # Group tiles by level type
    tiles_by_type = defaultdict(list)
    
    for tile_id, tile_info in all_tiles.items():
        # Find the level this tile came from
        level_id = tile_info["source_level"]
        level_type = None
        
        # Find the level type
        for level in levels:
            if level["id"] == level_id:
                level_type = level["type"]
                break
        
        if level_type:
            tiles_by_type[level_type].append(tile_info)
    
    # Create directories and tilesets for each type
    for level_type, tiles in tiles_by_type.items():
        # Create directory
        type_dir = os.path.join(output_dir, "tiles_by_type", level_type)
        os.makedirs(type_dir, exist_ok=True)
        
        # Create tileset
        create_tileset(tiles, os.path.join(output_dir, f"tileset_{level_type}.png"))
        
        # Copy tiles to type directory
        for tile_info in tiles:
            # Create a symlink or copy the tile
            tile_path = tile_info["path"]
            type_path = os.path.join(type_dir, os.path.basename(tile_path))
            if not os.path.exists(type_path):
                # Copy the tile
                try:
                    img = Image.open(tile_path)
                    img.save(type_path)
                except Exception as e:
                    print(f"Error copying tile {tile_path}: {e}")
    
    print(f"Organized tiles by {len(tiles_by_type)} level types")
    return tiles_by_type

def create_tileset(tiles, output_path, columns=16):
    """Create a tileset from a list of tiles"""
    if not tiles:
        return None
        
    # Calculate dimensions
    cols = min(columns, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    
    # Create tileset image
    sheet_width = cols * TILE_SIZE
    sheet_height = rows * TILE_SIZE
    sheet_img = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Add tiles to sheet
    for i, tile_info in enumerate(tiles):
        x = (i % cols) * TILE_SIZE
        y = (i // cols) * TILE_SIZE
        
        try:
            tile_img = Image.open(tile_info["path"])
            sheet_img.paste(tile_img, (x, y))
        except Exception as e:
            print(f"Error adding tile {tile_info['path']} to tileset: {e}")
    
    # Save tileset
    sheet_img.save(output_path)
    print(f"Created tileset with {len(tiles)} tiles: {output_path}")
    
    return output_path

def create_master_tileset(all_tiles, output_dir):
    """Create a master tileset with all tiles"""
    # Convert to list and sort by ID
    tiles_list = list(all_tiles.values())
    tiles_list.sort(key=lambda x: x["id"])
    
    # Create master tileset
    master_path = os.path.join(output_dir, "master_tileset.png")
    create_tileset(tiles_list, master_path)
    
    return master_path

def create_config_file(levels, all_tiles, tiles_by_type, output_dir):
    """Create a configuration file with all extracted data"""
    # Convert tiles to a list for the JSON
    tiles_list = []
    for tile_id, tile_info in all_tiles.items():
        tiles_list.append({
            "id": tile_id,
            "source_level": tile_info["source_level"],
            "position_in_level": tile_info["position_in_level"],
            "relative_path": os.path.relpath(tile_info["path"], output_dir)
        })
    
    # Sort tiles by ID
    tiles_list.sort(key=lambda x: x["id"])
    
    # Create type information
    types_info = {}
    for level_type, tiles in tiles_by_type.items():
        types_info[level_type] = {
            "count": len(tiles),
            "tileset_path": f"tileset_{level_type}.png",
            "tiles": [tile["id"] for tile in tiles]
        }
    
    # Create level information
    levels_info = []
    for level in levels:
        levels_info.append({
            "id": level["id"],
            "type": level["type"],
            "grid_position": level["grid_position"],
            "dimensions": {
                "width_tiles": level["width_tiles"],
                "height_tiles": level["height_tiles"]
            },
            "relative_path": os.path.relpath(level["image_path"], output_dir),
            "map_file": f"levels/{level['id']}_map.json"
        })
    
    # Create config
    config = {
        "tile_size": TILE_SIZE,
        "levels_count": len(levels),
        "tiles_count": len(all_tiles),
        "level_types": list(tiles_by_type.keys()),
        "master_tileset": "master_tileset.png",
        "levels": levels_info,
        "tiles": tiles_list,
        "types": types_info
    }
    
    # Save config
    config_path = os.path.join(output_dir, "arkista_levels_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created configuration file: {config_path}")
    return config_path

def main():
    parser = argparse.ArgumentParser(description='Grid-Based Level Extractor for Arkista\'s Ring')
    parser.add_argument('--input', '-i', 
                        default='arspritesheets/ArkistasRingMapAllStages.png',
                        help='Path to the background map image')
    parser.add_argument('--output', '-o', 
                        default='assets/extracted_ar_levels',
                        help='Output directory for extracted levels')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input):
        print(f"Error: Input file {args.input} does not exist")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Extract levels and tiles
    levels, all_tiles, tile_positions = extract_levels_from_grid(args.input, args.output)
    
    if not levels:
        print("No levels were extracted.")
        return 1
    
    # Create level tile maps
    create_level_tile_maps(levels, tile_positions, args.output)
    
    # Organize tiles by level type
    tiles_by_type = organize_tiles_by_type(all_tiles, levels, args.output)
    
    # Create master tileset
    create_master_tileset(all_tiles, args.output)
    
    # Create configuration file
    create_config_file(levels, all_tiles, tiles_by_type, args.output)
    
    print("Grid-based level extraction completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
