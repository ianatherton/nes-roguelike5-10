#!/usr/bin/env python3
"""
Arkista's Ring Background Tile Extractor
----------------------------------------
This tool specializes in extracting background tiles from Arkista's Ring
ROM data, extracting background patterns, and saving them in a format
compatible with the Asset Wizard.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw

# Constants for NES sprite properties
TILE_SIZE = 8  # Standard NES tile size is 8x8 pixels
BACKGROUND_TILE_SIZE = 16  # Background tiles are typically 16x16 (2x2 tiles)

# Default palette - NES standard grayscale
DEFAULT_PALETTE = [
    (0, 0, 0),       # Black
    (85, 85, 85),    # Dark Gray
    (170, 170, 170), # Light Gray
    (255, 255, 255)  # White
]

# Background tile mapping for Arkista's Ring
# Bank 1 and Bank 3 typically contain background tiles
BACKGROUND_TILE_MAPPING = {
    # Bank 1 background elements (walls, floors, etc.)
    "bank1": {
        "wall_tiles": {
            "start_index": 0x00,  # Starting tile index
            "count": 16,          # Number of consecutive tiles
            "description": "Wall tiles used in various levels",
            "tags": ["wall", "structure"]
        },
        "floor_tiles": {
            "start_index": 0x10,
            "count": 16,
            "description": "Floor patterns for different environments",
            "tags": ["floor", "ground"]
        },
        "stairs_tiles": {
            "start_index": 0x20,
            "count": 6,
            "description": "Stairs and ladders for level transitions",
            "tags": ["stairs", "ladder", "transition"]
        },
        "decorative_tiles": {
            "start_index": 0x30,
            "count": 24,
            "description": "Decorative elements for environments",
            "tags": ["decoration", "environment"]
        },
        "water_tiles": {
            "start_index": 0x50,
            "count": 8,
            "description": "Water and liquid tiles",
            "tags": ["water", "liquid"]
        }
    },
    
    # Bank 3 has additional environment elements
    "bank3": {
        "outdoor_tiles": {
            "start_index": 0x00,
            "count": 20,
            "description": "Outdoor environment elements",
            "tags": ["outdoor", "nature"]
        },
        "cave_tiles": {
            "start_index": 0x20,
            "count": 16,
            "description": "Cave and dungeon specific elements",
            "tags": ["cave", "dungeon"]
        },
        "door_tiles": {
            "start_index": 0x40,
            "count": 8,
            "description": "Door and entrance tiles",
            "tags": ["door", "entrance", "exit"]
        },
        "treasure_tiles": {
            "start_index": 0x50,
            "count": 6,
            "description": "Treasure chests and reward objects",
            "tags": ["treasure", "reward"]
        }
    }
}

def extract_tiles_from_chr(chr_path, output_dir, palette=None, bank_name=None):
    """
    Extract individual 8x8 tiles from a CHR bank image
    
    Args:
        chr_path: Path to the CHR bank image
        output_dir: Directory to save extracted tiles
        palette: Optional color palette to use
        bank_name: Name of the bank for mapping purposes
    
    Returns:
        List of tile images
    """
    if palette is None:
        palette = DEFAULT_PALETTE
        
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the CHR bank image
    chr_img = Image.open(chr_path)
    
    # Determine dimensions of the CHR bank image
    width, height = chr_img.size
    tiles_per_row = width // TILE_SIZE
    
    # Extract each 8x8 tile
    tiles = []
    for y in range(0, height, TILE_SIZE):
        for x in range(0, width, TILE_SIZE):
            # Extract the tile
            tile = chr_img.crop((x, y, x + TILE_SIZE, y + TILE_SIZE))
            
            # Calculate tile index
            tile_index = (y // TILE_SIZE) * tiles_per_row + (x // TILE_SIZE)
            
            # Create a new colored version of the tile
            colored_tile = Image.new("RGB", (TILE_SIZE, TILE_SIZE))
            
            # Color each pixel according to palette
            for py in range(TILE_SIZE):
                for px in range(TILE_SIZE):
                    pixel = tile.getpixel((px, py))
                    if isinstance(pixel, tuple):
                        # Handle RGB/RGBA format
                        grayscale = int(sum(pixel[:3]) / 3)
                    else:
                        # Handle grayscale format
                        grayscale = pixel
                    
                    # Map grayscale to palette index (divide by 64 to get 0-3)
                    palette_index = min(grayscale // 64, 3)
                    colored_tile.putpixel((px, py), palette[palette_index])
            
            # Save the tile
            tile_path = os.path.join(output_dir, f"tile_{tile_index:03d}.png")
            colored_tile.save(tile_path)
            
            # Add to our tiles list
            tiles.append({
                "image": colored_tile,
                "index": tile_index,
                "path": tile_path
            })
    
    # Return the list of tiles
    return tiles

def compose_background_tiles(tiles, output_dir, tile_mapping, bank_name):
    """
    Create background tile sets from individual tiles using mapping data
    
    Args:
        tiles: List of extracted tiles
        output_dir: Directory to save composed background tiles
        tile_mapping: Mapping data for background tiles
        bank_name: Name of the bank being processed
    
    Returns:
        List of composed background tile objects
    """
    # Create the output directory if it doesn't exist
    backgrounds_dir = os.path.join(output_dir, "backgrounds")
    os.makedirs(backgrounds_dir, exist_ok=True)
    
    # Bank-specific subdirectory
    bank_dir = os.path.join(backgrounds_dir, bank_name)
    os.makedirs(bank_dir, exist_ok=True)
    
    # Metadata for all background tiles
    background_metadata = {
        "bank": bank_name,
        "tiles": []
    }
    
    # Process each tile set from the mapping
    composed_tiles = []
    for set_name, set_data in tile_mapping.items():
        # Create a directory for this tile set
        set_dir = os.path.join(bank_dir, set_name)
        os.makedirs(set_dir, exist_ok=True)
        
        start_index = set_data["start_index"]
        count = set_data["count"]
        
        # Create metadata for this set
        set_metadata = {
            "name": set_name,
            "description": set_data["description"],
            "tags": set_data["tags"],
            "tiles": []
        }
        
        # Process each tile in the set
        for i in range(count):
            tile_index = start_index + i
            
            # Find the corresponding tile
            tile_data = next((t for t in tiles if t["index"] == tile_index), None)
            if tile_data is None:
                print(f"Warning: Tile index {tile_index} not found")
                continue
            
            # Save the individual background tile
            bg_tile_filename = f"{set_name}_{i:02d}.png"
            bg_tile_path = os.path.join(set_dir, bg_tile_filename)
            tile_data["image"].save(bg_tile_path)
            
            # Create 16x16 composed tile (duplicated for now - in a real scenario 
            # you'd combine 4 different 8x8 tiles to make a 16x16 background tile)
            composed_image = Image.new("RGB", (BACKGROUND_TILE_SIZE, BACKGROUND_TILE_SIZE))
            
            # Top-left
            composed_image.paste(tile_data["image"], (0, 0))
            # Top-right (same tile for demo purposes)
            composed_image.paste(tile_data["image"], (TILE_SIZE, 0))
            # Bottom-left (same tile for demo purposes)
            composed_image.paste(tile_data["image"], (0, TILE_SIZE))
            # Bottom-right (same tile for demo purposes)
            composed_image.paste(tile_data["image"], (TILE_SIZE, TILE_SIZE))
            
            # Save the composed background tile
            composed_filename = f"{set_name}_composed_{i:02d}.png"
            composed_path = os.path.join(set_dir, composed_filename)
            composed_image.save(composed_path)
            
            # Add to metadata
            tile_metadata = {
                "index": tile_index,
                "file": bg_tile_filename,
                "composed_file": composed_filename
            }
            set_metadata["tiles"].append(tile_metadata)
            
            # Add to our output list
            composed_tiles.append({
                "name": f"{set_name}_{i:02d}",
                "path": composed_path,
                "set": set_name,
                "index": i,
                "description": f"{set_data['description']} (Tile {i+1} of {count})"
            })
        
        # Add this set metadata to the overall metadata
        background_metadata["tiles"].append(set_metadata)
    
    # Save the complete metadata
    metadata_path = os.path.join(backgrounds_dir, f"{bank_name}_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(background_metadata, f, indent=2)
    
    return composed_tiles

def generate_asset_wizard_metadata(bank_name, tiles, output_dir):
    """
    Generate metadata compatible with the Asset Wizard
    
    Args:
        bank_name: Name of the CHR bank
        tiles: List of composed background tiles
        output_dir: Directory to save metadata
    """
    # Create wizard metadata directory
    wizard_dir = os.path.join(output_dir, "wizard_metadata")
    os.makedirs(wizard_dir, exist_ok=True)
    
    # Group tiles by set
    sets = {}
    for tile in tiles:
        set_name = tile["set"]
        if set_name not in sets:
            sets[set_name] = []
        sets[set_name].append(tile)
    
    # Generate asset metadata for each set
    for set_name, set_tiles in sets.items():
        # Create asset metadata
        asset_metadata = {
            "id": f"bg_{bank_name}_{set_name}",
            "name": f"{set_name.replace('_', ' ').title()} Set",
            "category": "Background",
            "description": set_tiles[0]["description"] if set_tiles else "",
            "tags": [set_name, bank_name, "background"],
            "chr_bank": int(bank_name[-1]) if bank_name[-1].isdigit() else 0,
            "width": BACKGROUND_TILE_SIZE,
            "height": BACKGROUND_TILE_SIZE,
            "created_at": "",  # Will be filled by asset wizard
            "updated_at": "",  # Will be filled by asset wizard
            "sprites": []
        }
        
        # Add each tile as a sprite
        for tile in set_tiles:
            sprite_metadata = {
                "id": f"sprite_{tile['index']}",
                "name": tile["name"],
                "asset_id": asset_metadata["id"],
                "animation_type": "idle",
                "direction": "none",
                "frame_number": tile["index"],
                "file_path": os.path.relpath(tile["path"], output_dir)
            }
            asset_metadata["sprites"].append(sprite_metadata)
        
        # Save asset metadata
        metadata_path = os.path.join(wizard_dir, f"{set_name}_asset.json")
        with open(metadata_path, "w") as f:
            json.dump(asset_metadata, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Extract background tiles from Arkista's Ring CHR data")
    parser.add_argument("--input", "-i", help="Path to the CHR bank directory")
    parser.add_argument("--output", "-o", help="Path to output directory")
    parser.add_argument("--bank", "-b", choices=["bank1", "bank3", "all"], default="all", 
                        help="CHR bank to extract from: bank1, bank3, or all")
    
    args = parser.parse_args()
    
    # Set default paths if not provided
    if not args.input:
        args.input = "../assets/arkista_assets/chr_data"
    if not args.output:
        args.output = "../assets/arkista_assets/backgrounds"
    
    # Convert to absolute paths
    input_dir = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output)
    
    # Ensure the input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist")
        return 1
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine which banks to process
    banks_to_process = []
    if args.bank == "bank1" or args.bank == "all":
        banks_to_process.append(("bank1", "chr_bank_1.png"))
    if args.bank == "bank3" or args.bank == "all":
        banks_to_process.append(("bank3", "chr_bank_3.png"))
    
    # Process each bank
    all_composed_tiles = []
    for bank_name, bank_file in banks_to_process:
        print(f"Processing {bank_name}...")
        
        # Path to the CHR bank image
        chr_path = os.path.join(input_dir, bank_file)
        if not os.path.exists(chr_path):
            print(f"Warning: CHR bank file '{chr_path}' not found")
            continue
        
        # Extract tiles from the CHR bank
        print(f"Extracting tiles from {bank_file}...")
        tiles = extract_tiles_from_chr(chr_path, os.path.join(output_dir, f"{bank_name}_tiles"), None, bank_name)
        
        # Compose background tiles
        print(f"Composing background tiles for {bank_name}...")
        tile_mapping = BACKGROUND_TILE_MAPPING.get(bank_name, {})
        composed_tiles = compose_background_tiles(tiles, output_dir, tile_mapping, bank_name)
        all_composed_tiles.extend(composed_tiles)
        
        # Generate asset wizard metadata
        print(f"Generating Asset Wizard metadata for {bank_name}...")
        generate_asset_wizard_metadata(bank_name, composed_tiles, output_dir)
    
    print(f"Background tile extraction complete! Output saved to: {output_dir}")
    print(f"Total background tiles extracted: {len(all_composed_tiles)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
