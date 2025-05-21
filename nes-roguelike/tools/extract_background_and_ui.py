#!/usr/bin/env python3
"""
Arkista's Ring Background and UI Extractor
------------------------------------------
This tool extracts background and UI elements from Arkista's Ring ROM
for use in Craven Caverns.

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
TILE_SIZE = 8          # Standard NES tile size is 8x8 pixels
BACKGROUND_TILE_SIZE = 16  # Background tiles are typically 16x16 (2x2 tiles)
CHR_BANK_SIZE = 0x1000  # 4KB per CHR bank

# Default palette - NES standard grayscale
DEFAULT_PALETTE = [
    (0, 0, 0),         # Black
    (85, 85, 85),      # Dark Gray
    (170, 170, 170),   # Light Gray
    (255, 255, 255)    # White
]

# Game-specific palettes
ARKISTA_TITLE_PALETTE = [
    (0, 0, 0),         # Black
    (102, 182, 0),     # Green
    (238, 238, 238),   # Light Gray
    (255, 255, 255)    # White
]

ARKISTA_UI_PALETTE = [
    (0, 0, 0),         # Black
    (222, 127, 0),     # Orange
    (252, 200, 0),     # Yellow
    (255, 255, 255)    # White
]

ARKISTA_GRASS_PALETTE = [
    (0, 0, 0),         # Black
    (0, 182, 0),       # Green
    (142, 224, 142),   # Light Green
    (238, 238, 238)    # Light Gray
]

# Background and UI tile mapping for Arkista's Ring
TILE_MAPPING = {
    # Bank 0 contains UI elements and some background patterns
    "bank0": {
        "ui_elements": {
            "start_index": 0x00,
            "count": 32,
            "description": "UI elements including hearts, inventory slots, and digits",
            "tags": ["ui", "interface", "hud"]
        },
        "menu_tiles": {
            "start_index": 0x20, 
            "count": 16,
            "description": "Menu borders and backgrounds",
            "tags": ["ui", "menu", "interface"]
        },
        "text_elements": {
            "start_index": 0x40,
            "count": 64,
            "description": "Text and font characters",
            "tags": ["ui", "text", "font"]
        }
    },
    
    # Bank 1 contains mostly background elements
    "bank1": {
        "wall_tiles": {
            "start_index": 0x00,
            "count": 16,
            "description": "Wall tiles used in various levels",
            "tags": ["wall", "structure", "background"]
        },
        "floor_tiles": {
            "start_index": 0x10,
            "count": 16,
            "description": "Floor patterns for different environments",
            "tags": ["floor", "ground", "background"]
        },
        "stairs_tiles": {
            "start_index": 0x20,
            "count": 8,
            "description": "Stairs and ladders for level transitions",
            "tags": ["stairs", "ladder", "transition", "background"]
        },
        "decorative_tiles": {
            "start_index": 0x30,
            "count": 24,
            "description": "Decorative elements for environments",
            "tags": ["decoration", "environment", "background"]
        },
        "water_tiles": {
            "start_index": 0x50,
            "count": 8,
            "description": "Water and liquid tiles",
            "tags": ["water", "liquid", "background"]
        }
    },
    
    # Bank 2 contains more UI elements and special tiles
    "bank2": {
        "status_icons": {
            "start_index": 0x00,
            "count": 16,
            "description": "Status effect icons and indicators",
            "tags": ["ui", "status", "icon"]
        },
        "item_icons": {
            "start_index": 0x10,
            "count": 32,
            "description": "Item and equipment icons",
            "tags": ["ui", "item", "equipment"]
        },
        "dialog_elements": {
            "start_index": 0x40,
            "count": 16,
            "description": "Dialog box elements and borders",
            "tags": ["ui", "dialog", "border"]
        }
    },
    
    # Bank 3 has additional environment elements
    "bank3": {
        "outdoor_tiles": {
            "start_index": 0x00,
            "count": 20,
            "description": "Outdoor environment elements",
            "tags": ["outdoor", "nature", "background"]
        },
        "cave_tiles": {
            "start_index": 0x20,
            "count": 16,
            "description": "Cave and dungeon specific elements",
            "tags": ["cave", "dungeon", "background"]
        },
        "door_tiles": {
            "start_index": 0x40,
            "count": 8,
            "description": "Door and entrance tiles",
            "tags": ["door", "entrance", "exit", "background"]
        },
        "treasure_tiles": {
            "start_index": 0x50,
            "count": 6,
            "description": "Treasure chests and reward objects",
            "tags": ["treasure", "reward", "background"]
        }
    }
}

def extract_chr_data(rom_path, bank_number):
    """
    Extract CHR data for a specific bank from the ROM
    
    Args:
        rom_path: Path to the NES ROM file
        bank_number: CHR bank number to extract (0-based)
    
    Returns:
        Raw CHR data as bytes
    """
    try:
        with open(rom_path, 'rb') as rom_file:
            # Skip the 16-byte header
            rom_file.seek(16)
            
            # Skip to the desired CHR bank
            rom_file.seek(CHR_BANK_SIZE * bank_number, 1)
            
            # Read the entire CHR bank (4KB)
            chr_data = rom_file.read(CHR_BANK_SIZE)
            
            return chr_data
    except Exception as e:
        print(f"Error reading ROM file: {e}")
        return None

def decode_chr_tile(chr_data, tile_index):
    """
    Decode an 8x8 tile from CHR data
    
    Args:
        chr_data: Raw CHR data
        tile_index: Index of the tile to decode (0-based)
    
    Returns:
        2D list of pixel values (0-3) for the tile
    """
    # Each tile is 16 bytes (8 bytes for low bit plane, 8 bytes for high bit plane)
    tile_offset = tile_index * 16
    
    # Make sure we don't go out of bounds
    if tile_offset + 16 > len(chr_data):
        print(f"Warning: Tile index {tile_index} is out of bounds")
        return None
    
    # Initialize empty tile
    tile = [[0 for _ in range(8)] for _ in range(8)]
    
    # Process the tile data (8 rows)
    for row in range(8):
        # Get the data for this row from both bit planes
        low_byte = chr_data[tile_offset + row]
        high_byte = chr_data[tile_offset + row + 8]
        
        # Process each pixel in the row
        for col in range(8):
            bit_position = 7 - col  # Bits are in reverse order
            low_bit = (low_byte >> bit_position) & 1
            high_bit = (high_byte >> bit_position) & 1
            pixel_value = (high_bit << 1) | low_bit
            
            # Store the pixel value
            tile[row][col] = pixel_value
    
    return tile

def create_tile_image(tile_data, palette=None):
    """
    Create an image from tile data
    
    Args:
        tile_data: 2D list of pixel values for the tile
        palette: Color palette to use (list of RGB tuples)
    
    Returns:
        PIL Image of the tile
    """
    if palette is None:
        palette = DEFAULT_PALETTE
    
    # Create a new image with the right dimensions
    image = Image.new("RGB", (TILE_SIZE, TILE_SIZE))
    
    # Draw each pixel
    for y in range(TILE_SIZE):
        for x in range(TILE_SIZE):
            pixel_value = tile_data[y][x]
            image.putpixel((x, y), palette[pixel_value])
    
    return image

def extract_tiles_from_rom(rom_path, output_dir, bank_numbers, palette=None):
    """
    Extract tiles from specified banks in the ROM
    
    Args:
        rom_path: Path to the NES ROM file
        output_dir: Directory to save extracted tiles
        bank_numbers: List of CHR bank numbers to process
        palette: Optional color palette to use
    
    Returns:
        Dictionary of extracted tiles by bank
    """
    all_tiles = {}
    
    for bank_number in bank_numbers:
        # Extract the CHR data for this bank
        chr_data = extract_chr_data(rom_path, bank_number)
        if not chr_data:
            print(f"Failed to extract CHR data for bank {bank_number}")
            continue
        
        bank_name = f"bank{bank_number}"
        tiles = []
        
        # Create bank directory
        bank_dir = os.path.join(output_dir, "tiles", bank_name)
        os.makedirs(bank_dir, exist_ok=True)
        
        # Process all tiles in the bank (256 tiles per 4KB CHR bank)
        for tile_index in range(256):
            # Decode the tile data
            tile_data = decode_chr_tile(chr_data, tile_index)
            if not tile_data:
                continue
            
            # Create an image from the tile data
            tile_image = create_tile_image(tile_data, palette)
            
            # Save the tile image
            tile_filename = f"tile_{tile_index:02x}.png"
            tile_path = os.path.join(bank_dir, tile_filename)
            tile_image.save(tile_path)
            
            # Add to our list
            tiles.append({
                "index": tile_index,
                "image": tile_image,
                "path": tile_path
            })
        
        all_tiles[bank_name] = tiles
        print(f"Extracted {len(tiles)} tiles from {bank_name}")
    
    return all_tiles

def compose_background_tiles(tiles, output_dir, tile_mapping, bank_name):
    """
    Create composed background tiles using mapping data
    
    Args:
        tiles: List of extracted tiles for this bank
        output_dir: Directory to save composed tiles
        tile_mapping: Mapping data for this bank
        bank_name: Name of the bank being processed
    
    Returns:
        List of composed tile objects
    """
    # Create output directories
    if "ui" in bank_name or any(set_name.startswith("ui_") for set_name in tile_mapping.keys()):
        target_dir = os.path.join(output_dir, "ui_elements")
    else:
        target_dir = os.path.join(output_dir, "backgrounds")
    
    bank_dir = os.path.join(target_dir, bank_name)
    os.makedirs(bank_dir, exist_ok=True)
    
    # Metadata for this bank
    metadata = {
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
                print(f"Warning: Tile index {tile_index} not found in {bank_name}")
                continue
            
            # Save the individual tile
            tile_filename = f"{set_name}_{i:02d}.png"
            tile_path = os.path.join(set_dir, tile_filename)
            tile_data["image"].save(tile_path)
            
            # For UI elements, keep them as 8x8 tiles
            if any(tag in set_data["tags"] for tag in ["ui", "text", "font", "icon"]):
                composed_image = tile_data["image"]
                composed_size = TILE_SIZE
            else:
                # For background elements, create 16x16 composed tile
                composed_image = Image.new("RGB", (BACKGROUND_TILE_SIZE, BACKGROUND_TILE_SIZE))
                composed_size = BACKGROUND_TILE_SIZE
                
                # Paste the tile into all four quadrants
                composed_image.paste(tile_data["image"], (0, 0))
                composed_image.paste(tile_data["image"], (TILE_SIZE, 0))
                composed_image.paste(tile_data["image"], (0, TILE_SIZE))
                composed_image.paste(tile_data["image"], (TILE_SIZE, TILE_SIZE))
            
            # Save the composed tile
            composed_filename = f"{set_name}_composed_{i:02d}.png"
            composed_path = os.path.join(set_dir, composed_filename)
            composed_image.save(composed_path)
            
            # Add to metadata
            tile_metadata = {
                "index": tile_index,
                "file": tile_filename,
                "composed_file": composed_filename,
                "size": composed_size
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
        metadata["tiles"].append(set_metadata)
    
    # Save the complete metadata
    metadata_path = os.path.join(target_dir, f"{bank_name}_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return composed_tiles

def generate_preview_sheet(tiles, output_dir, bank_name, cols=16):
    """
    Generate a preview sheet of all extracted tiles
    
    Args:
        tiles: List of extracted tiles
        output_dir: Directory to save the preview sheet
        bank_name: Name of the bank being processed
        cols: Number of columns in the preview sheet
    """
    if not tiles:
        return
    
    # Calculate sheet dimensions
    rows = (len(tiles) + cols - 1) // cols
    width = cols * TILE_SIZE
    height = rows * TILE_SIZE
    
    # Create a new image for the sheet
    sheet = Image.new("RGB", (width, height), (0, 0, 0))
    
    # Place each tile on the sheet
    for i, tile in enumerate(tiles):
        row = i // cols
        col = i % cols
        x = col * TILE_SIZE
        y = row * TILE_SIZE
        sheet.paste(tile["image"], (x, y))
    
    # Save the sheet
    sheet_path = os.path.join(output_dir, f"{bank_name}_preview.png")
    sheet.save(sheet_path)
    print(f"Generated preview sheet: {sheet_path}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Extract background and UI tiles from Arkista's Ring ROM")
    parser.add_argument("--rom", default="assets/reference/arkistas_ring.nes", help="Path to the NES ROM file")
    parser.add_argument("--output", default="assets/extracted", help="Output directory")
    parser.add_argument("--banks", default="0,1,2,3", help="Comma-separated list of CHR banks to extract (0-based)")
    args = parser.parse_args()
    
    # Create output directories
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse bank numbers
    try:
        bank_numbers = [int(b.strip()) for b in args.banks.split(",")]
    except ValueError:
        print("Error: Bank numbers must be integers")
        return 1
    
    # Make sure the ROM file exists
    rom_path = args.rom
    if not os.path.exists(rom_path):
        print(f"Error: ROM file not found: {rom_path}")
        return 1
    
    # Extract tiles from the ROM
    print(f"Extracting tiles from {rom_path}")
    palettes = {
        "bank0": ARKISTA_UI_PALETTE,
        "bank1": ARKISTA_GRASS_PALETTE,
        "bank2": ARKISTA_UI_PALETTE,
        "bank3": ARKISTA_GRASS_PALETTE
    }
    
    # Extract tiles from each bank
    all_tiles = {}
    for bank_number in bank_numbers:
        bank_name = f"bank{bank_number}"
        palette = palettes.get(bank_name, DEFAULT_PALETTE)
        
        # Skip character banks - we're only interested in background and UI
        if bank_number not in [0, 1, 2, 3]:
            print(f"Skipping bank {bank_number} (likely character data)")
            continue
        
        print(f"Processing {bank_name} with {len(palette)} colors")
        bank_tiles = extract_tiles_from_rom(rom_path, output_dir, [bank_number], palette)
        all_tiles.update(bank_tiles)
    
    # Compose background and UI tiles for each bank
    for bank_name, tiles in all_tiles.items():
        # Check if we have mapping data for this bank
        if bank_name not in TILE_MAPPING:
            print(f"No mapping data for {bank_name}, skipping composition")
            continue
        
        # Generate a preview sheet
        generate_preview_sheet(tiles, output_dir, bank_name)
        
        # Compose tiles based on mapping data
        print(f"Composing tiles for {bank_name}")
        compose_background_tiles(tiles, output_dir, TILE_MAPPING[bank_name], bank_name)
    
    print(f"Extraction complete. Output saved to {output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
