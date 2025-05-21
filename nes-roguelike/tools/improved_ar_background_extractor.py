#!/usr/bin/env python3
"""
Improved Arkista's Ring Background Extractor
--------------------------------------------
Specialized tool to extract background tiles from ArkistasRingMapAllStages.png,
with enhanced level detection and tile categorization.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import json
import argparse
from collections import defaultdict
from PIL import Image, ImageDraw, ImageChops, ImageStat

# Constants
TILE_SIZE = 16      # Background tile size
TRANSPARENT_COLOR = (0, 0, 0, 0)  # Transparent color
COLORS = {
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "CYAN": (0, 255, 255),
    "DARK_GREEN": (0, 128, 0),
    "PINK": (255, 0, 255),
    "ORANGE": (255, 165, 0),
    "PURPLE": (128, 0, 128),
    "DARK_BLUE": (0, 0, 128),
}

def extract_background_tiles(image_path, output_dir, tile_size=TILE_SIZE):
    """
    Extract unique background tiles from the map image
    """
    try:
        source_img = Image.open(image_path)
        # Convert to RGBA for consistent processing
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
    
    # Track unique tiles and their positions
    unique_tiles = {}
    tile_positions = defaultdict(list)
    tile_count = 0
    
    # Scan the image for tiles
    for y in range(0, height - tile_size + 1, tile_size):
        for x in range(0, width - tile_size + 1, tile_size):
            # Skip if we're outside the image bounds
            if x + tile_size > width or y + tile_size > height:
                continue
                
            # Crop the tile
            tile = source_img.crop((x, y, x + tile_size, y + tile_size))
            
            # Check if the tile has content (not completely black/transparent)
            if is_empty_tile(tile):
                continue
                
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
                    "positions": [(x, y)],
                    "color_profile": get_dominant_color(tile)
                }
            else:
                # Add this position to the existing tile
                unique_tiles[tile_hash]["positions"].append((x, y))
            
            # Track which tile is at this position
            tile_positions[(x, y)] = tile_hash
    
    print(f"Extracted {len(unique_tiles)} unique background tiles to {tiles_dir}")
    return unique_tiles, tile_positions

def is_empty_tile(tile):
    """Check if a tile is empty (all black/transparent)"""
    # Convert to RGBA if not already
    if tile.mode != 'RGBA':
        tile = tile.convert('RGBA')
        
    # Get image statistics
    stat = ImageStat.Stat(tile)
    # If the average brightness is very low, tile is likely empty
    if sum(stat.mean[:3]) < 10:  # Low threshold to catch nearly-black tiles
        return True
    return False

def get_dominant_color(tile):
    """Get the dominant color of a tile for categorization"""
    # Convert to RGB mode if in RGBA
    if tile.mode == 'RGBA':
        bg = Image.new('RGB', tile.size, (0, 0, 0))
        bg.paste(tile, (0, 0), tile)
        tile = bg
    
    # Get color statistics
    stat = ImageStat.Stat(tile)
    r, g, b = stat.mean[:3]
    
    # Return the RGB values
    return (int(r), int(g), int(b))

def find_level_boundaries(image, tile_size=TILE_SIZE):
    """
    Find level boundaries by detecting rows/columns of empty tiles
    or significant color changes
    """
    width, height = image.size
    
    # A level boundary is defined by a row that's mostly empty tiles
    # or has a significant change in color theme
    boundaries = []
    
    # First, check for rows with many empty tiles
    for y in range(0, height - tile_size + 1, tile_size):
        empty_count = 0
        for x in range(0, width - tile_size + 1, tile_size):
            tile = image.crop((x, y, x + tile_size, y + tile_size))
            if is_empty_tile(tile):
                empty_count += 1
        
        # If most of the row is empty tiles
        if empty_count > (width // tile_size) * 0.7:  # 70% threshold
            boundaries.append(y)
    
    # Add the bottom boundary
    boundaries.append(height)
    
    return boundaries

def identify_level_regions(image_path, output_dir, tile_size=TILE_SIZE):
    """
    Identify separate level regions based on visual appearance
    """
    source_img = Image.open(image_path)
    # Convert to RGBA for consistent processing
    if source_img.mode != 'RGBA':
        source_img = source_img.convert('RGBA')
    
    width, height = source_img.size
    
    # Find boundary rows with empty space
    boundaries = find_level_boundaries(source_img, tile_size)
    
    # Create level regions using the boundaries
    levels = []
    for i in range(len(boundaries) - 1):
        start_y = boundaries[i]
        end_y = boundaries[i + 1]
        
        # Only consider regions with reasonable height (at least 3 tiles)
        if end_y - start_y < tile_size * 3:
            continue
            
        # Extract the level region
        level_img = source_img.crop((0, start_y, width, end_y))
        level_height = end_y - start_y
        
        # Give each level a unique ID
        level_id = f"level_{i+1:02d}"
        
        # Calculate dimensions in tiles
        level_width_tiles = width // tile_size
        level_height_tiles = level_height // tile_size
        
        # Store level information
        level_info = {
            "id": level_id,
            "y_range": (start_y, end_y),
            "width_pixels": width,
            "height_pixels": level_height,
            "width_tiles": level_width_tiles,
            "height_tiles": level_height_tiles,
            "dominant_color": get_dominant_color(level_img)
        }
        
        levels.append(level_info)
    
    # Now detect sub-levels within each level (columns)
    processed_levels = []
    
    for level in levels:
        start_y, end_y = level["y_range"]
        level_height = end_y - start_y
        
        # Look for vertical separations (empty columns)
        column_boundaries = [0]  # Start with left edge
        
        for x in range(0, width - tile_size + 1, tile_size):
            empty_count = 0
            for y in range(start_y, end_y, tile_size):
                tile = source_img.crop((x, y, x + tile_size, y + tile_size))
                if is_empty_tile(tile):
                    empty_count += 1
            
            # If most of the column is empty tiles
            if empty_count > ((end_y - start_y) // tile_size) * 0.7:  # 70% threshold
                column_boundaries.append(x)
        
        # Add right edge
        column_boundaries.append(width)
        
        # Create sub-levels for this level
        for j in range(len(column_boundaries) - 1):
            start_x = column_boundaries[j]
            end_x = column_boundaries[j + 1]
            
            # Only consider regions with reasonable width (at least 3 tiles)
            if end_x - start_x < tile_size * 3:
                continue
                
            # Extract the sublevel region
            sublevel_id = f"{level['id']}_sub_{j+1:02d}"
            sublevel_img = source_img.crop((start_x, start_y, end_x, end_y))
            
            # Calculate dimensions in tiles
            sublevel_width_tiles = (end_x - start_x) // tile_size
            sublevel_height_tiles = (end_y - start_y) // tile_size
            
            # Save the sublevel image
            sublevels_dir = os.path.join(output_dir, "levels")
            os.makedirs(sublevels_dir, exist_ok=True)
            sublevel_path = os.path.join(sublevels_dir, f"{sublevel_id}.png")
            sublevel_img.save(sublevel_path)
            
            # Store sublevel info
            sublevel_info = {
                "id": sublevel_id,
                "parent_level": level["id"],
                "x_range": (start_x, end_x),
                "y_range": (start_y, end_y),
                "width_pixels": end_x - start_x,
                "height_pixels": end_y - start_y,
                "width_tiles": sublevel_width_tiles,
                "height_tiles": sublevel_height_tiles,
                "dominant_color": get_dominant_color(sublevel_img),
                "image_path": sublevel_path
            }
            
            processed_levels.append(sublevel_info)
    
    # Return all detected level regions
    print(f"Detected {len(processed_levels)} level regions")
    return processed_levels

def categorize_tiles_by_type(unique_tiles):
    """
    Categorize tiles by their visual appearance
    """
    tile_categories = defaultdict(list)
    
    # Define tile categories based on dominant colors
    for tile_hash, tile_info in unique_tiles.items():
        r, g, b = tile_info["color_profile"]
        
        # Simple categorization based on dominant color
        if r < 50 and g < 50 and b > 150:  # Mostly blue
            category = "water"
        elif r < 50 and g > 150 and b < 50:  # Mostly green
            category = "grass"
        elif r > 150 and g < 50 and b < 50:  # Mostly red
            category = "danger"
        elif r > 150 and g > 150 and b < 50:  # Mostly yellow
            category = "sand"
        elif r > 150 and g > 150 and b > 150:  # Mostly white/gray
            category = "stone"
        elif r < 50 and g < 50 and b < 50:  # Mostly black
            category = "void"
        elif abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:  # Gray tones
            category = "stone"
        elif r > 150 and g < 100 and b > 150:  # Purple/pink
            category = "special"
        else:
            category = "misc"
        
        # Add tile to this category
        tile_categories[category].append(tile_info)
    
    # Print category statistics
    print("Tile categories:")
    for category, tiles in tile_categories.items():
        print(f"  {category}: {len(tiles)} tiles")
    
    return tile_categories

def create_tile_map(level_info, unique_tiles, tile_positions, tile_size=TILE_SIZE):
    """
    Create a tile map for a level region
    """
    start_x, end_x = level_info["x_range"]
    start_y, end_y = level_info["y_range"]
    
    # Create empty tile map
    tile_map = []
    
    # Fill in the tile map with tile IDs
    for y in range(start_y, end_y, tile_size):
        row = []
        for x in range(start_x, end_x, tile_size):
            # Get the tile at this position
            tile_hash = tile_positions.get((x, y))
            if tile_hash and tile_hash in unique_tiles:
                tile_id = unique_tiles[tile_hash]["id"]
                row.append(tile_id)
            else:
                row.append("empty")
        tile_map.append(row)
    
    return tile_map

def create_tileset_by_category(tile_categories, output_dir, tile_size=TILE_SIZE):
    """
    Create a tileset for each category of tiles
    """
    for category, tiles in tile_categories.items():
        if not tiles:
            continue
            
        # Create a directory for this category
        category_dir = os.path.join(output_dir, "tiles_by_category", category)
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a tileset for this category
        cols = min(16, len(tiles))
        rows = (len(tiles) + cols - 1) // cols
        
        sheet_width = cols * tile_size
        sheet_height = rows * tile_size
        sheet_img = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
        
        # Add tiles to sheet
        for i, tile_info in enumerate(tiles):
            x = (i % cols) * tile_size
            y = (i // cols) * tile_size
            
            # Open the tile image
            try:
                tile_img = Image.open(tile_info["path"])
                sheet_img.paste(tile_img, (x, y))
                
                # Also copy the tile to the category directory
                tile_filename = os.path.basename(tile_info["path"])
                category_path = os.path.join(category_dir, tile_filename)
                tile_img.save(category_path)
            except Exception as e:
                print(f"Error processing tile {tile_info['path']}: {e}")
        
        # Save the category tileset
        sheet_path = os.path.join(output_dir, f"tileset_{category}.png")
        sheet_img.save(sheet_path)
        print(f"Created {category} tileset with {len(tiles)} tiles: {sheet_path}")

def create_level_maps(levels, unique_tiles, tile_positions, output_dir, tile_size=TILE_SIZE):
    """
    Create tile maps for each detected level
    """
    levels_data = []
    
    for level_info in levels:
        # Create tile map for this level
        tile_map = create_tile_map(level_info, unique_tiles, tile_positions, tile_size)
        
        # Add tile map to the level info
        level_info["tile_map"] = tile_map
        
        # Create a JSON file for this level
        level_id = level_info["id"]
        map_path = os.path.join(output_dir, "levels", f"{level_id}_map.json")
        
        # Create a simplified version of the level info for the JSON file
        level_json = {
            "id": level_info["id"],
            "parent_level": level_info.get("parent_level"),
            "dimensions": {
                "width_tiles": level_info["width_tiles"],
                "height_tiles": level_info["height_tiles"],
                "width_pixels": level_info["width_pixels"],
                "height_pixels": level_info["height_pixels"]
            },
            "position": {
                "x": level_info["x_range"][0],
                "y": level_info["y_range"][0]
            },
            "tile_map": level_info["tile_map"]
        }
        
        with open(map_path, 'w') as f:
            json.dump(level_json, f, indent=2)
        
        levels_data.append(level_json)
    
    # Create a combined levels info file
    levels_path = os.path.join(output_dir, "levels_data.json")
    with open(levels_path, 'w') as f:
        json.dump({
            "levels_count": len(levels),
            "levels": [{
                "id": level["id"],
                "parent_level": level.get("parent_level"),
                "dimensions": {
                    "width_tiles": level["width_tiles"],
                    "height_tiles": level["height_tiles"]
                },
                "map_file": f"levels/{level['id']}_map.json"
            } for level in levels_data]
        }, f, indent=2)
    
    print(f"Created level maps for {len(levels)} levels")
    return levels_data

def create_combined_tileset(unique_tiles, output_dir, columns=16, tile_size=TILE_SIZE):
    """
    Create a combined tileset from all unique tiles
    """
    # Convert dictionary to list
    tiles_list = list(unique_tiles.values())
    
    # Sort tiles by ID
    tiles_list.sort(key=lambda x: x["id"])
    
    # Calculate tileset dimensions
    cols = min(columns, len(tiles_list))
    rows = (len(tiles_list) + cols - 1) // cols
    
    sheet_width = cols * tile_size
    sheet_height = rows * tile_size
    sheet_img = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Add tiles to sheet
    for i, tile_info in enumerate(tiles_list):
        x = (i % cols) * tile_size
        y = (i // cols) * tile_size
        
        try:
            tile_img = Image.open(tile_info["path"])
            sheet_img.paste(tile_img, (x, y))
        except Exception as e:
            print(f"Error adding tile {tile_info['path']} to tileset: {e}")
    
    # Save tileset
    sheet_path = os.path.join(output_dir, "complete_tileset.png")
    sheet_img.save(sheet_path)
    print(f"Created complete tileset with {len(tiles_list)} tiles: {sheet_path}")
    
    return sheet_path

def create_config_file(unique_tiles, levels, tile_categories, output_dir):
    """
    Create a configuration file with all extracted data
    """
    # Convert tiles dictionary to list for the JSON
    tiles_list = []
    for tile_hash, tile_info in unique_tiles.items():
        tiles_list.append({
            "id": tile_info["id"],
            "first_position": tile_info["first_position"],
            "positions_count": len(tile_info["positions"]),
            "color_profile": tile_info["color_profile"],
            "relative_path": os.path.relpath(tile_info["path"], output_dir)
        })
    
    # Sort tiles by ID
    tiles_list.sort(key=lambda x: x["id"])
    
    # Add category information
    categories = {}
    for category, tiles in tile_categories.items():
        categories[category] = {
            "count": len(tiles),
            "tiles": [tile["id"] for tile in tiles]
        }
    
    # Build the config
    config = {
        "tile_size": TILE_SIZE,
        "tiles_count": len(tiles_list),
        "levels_count": len(levels),
        "categories": categories,
        "tiles": tiles_list,
        "levels": [{
            "id": level["id"],
            "parent_level": level.get("parent_level"),
            "dimensions": {
                "width_tiles": level["width_tiles"],
                "height_tiles": level["height_tiles"]
            },
            "relative_path": os.path.relpath(level["image_path"], output_dir)
        } for level in levels]
    }
    
    # Save the config
    config_path = os.path.join(output_dir, "ar_background_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created background configuration file: {config_path}")
    return config_path

def main():
    parser = argparse.ArgumentParser(description='Improved Arkista\'s Ring Background Extractor')
    parser.add_argument('--input', '-i', 
                        default='arspritesheets/ArkistasRingMapAllStages.png',
                        help='Path to the background map image')
    parser.add_argument('--output', '-o', 
                        default='assets/extracted_backgrounds',
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
    
    # Extract unique tiles and their positions
    unique_tiles, tile_positions = extract_background_tiles(args.input, args.output, args.tile_size)
    
    if not unique_tiles:
        print("No background tiles were extracted.")
        return 1
    
    # Identify level regions
    levels = identify_level_regions(args.input, args.output, args.tile_size)
    
    # Categorize tiles by type
    tile_categories = categorize_tiles_by_type(unique_tiles)
    
    # Create tilesets by category
    create_tileset_by_category(tile_categories, args.output, args.tile_size)
    
    # Create level maps
    create_level_maps(levels, unique_tiles, tile_positions, args.output, args.tile_size)
    
    # Create combined tileset
    create_combined_tileset(unique_tiles, args.output, 16, args.tile_size)
    
    # Create configuration file
    create_config_file(unique_tiles, levels, tile_categories, args.output)
    
    print("Enhanced background extraction completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
