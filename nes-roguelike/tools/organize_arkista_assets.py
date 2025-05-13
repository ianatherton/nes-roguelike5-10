#!/usr/bin/env python3
"""
Arkista's Ring Asset Organizer for Craven Caverns
-------------------------------------------------
This tool extracts and organizes all graphical assets from Arkista's Ring
into a well-structured format for use in the Craven Caverns roguelike game.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import argparse
from PIL import Image
import json
import shutil

# Asset categories with descriptions
CATEGORIES = {
    "player": {
        "description": "Player character sprites",
        "tile_ranges": [(0x25, 0x29), (0x4A, 0x4F)]  # Example ranges, will be refined
    },
    "enemies": {
        "description": "Enemy sprites",
        "tile_ranges": [(0x30, 0x45), (0x50, 0x5F)]
    },
    "items": {
        "description": "Item sprites (weapons, armor, potions, etc.)",
        "tile_ranges": [(0x60, 0x7F)]
    },
    "environment": {
        "description": "Environment tiles (walls, floors, doors, stairs)",
        "tile_ranges": [(0xA0, 0xBF)]
    },
    "ui": {
        "description": "UI elements (fonts, indicators, etc.)",
        "tile_ranges": [(0xC0, 0xDF)]
    }
}

# Special environmental elements needed for roguelike games
ROGUELIKE_ELEMENTS = {
    "wall": {
        "description": "Wall tiles for dungeon generation",
        "potential_tiles": [0xA0, 0xA1, 0xA2, 0xA3]
    },
    "floor": {
        "description": "Floor tiles for dungeon rooms",
        "potential_tiles": [0xA4, 0xA5, 0xA6, 0xA7]
    },
    "door": {
        "description": "Door tiles connecting rooms",
        "potential_tiles": [0xA8, 0xA9]
    },
    "stairs": {
        "description": "Stairs to next dungeon level",
        "potential_tiles": [0xAA, 0xAB]
    },
    "chest": {
        "description": "Treasure chests",
        "potential_tiles": [0x60, 0x61]
    }
}

def extract_chr_banks(rom_path, output_dir):
    """Extract all CHR banks from a NES ROM"""
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
            print("This ROM uses CHR RAM rather than CHR ROM.")
            return False
        
        print(f"Found {chr_banks} CHR banks in the ROM.")
        
        # Calculate where the CHR data begins
        prg_banks = rom_data[4]
        chr_start = 16 + (prg_banks * 16384)  # 16KB per PRG bank
        
        # Extract each CHR bank
        for bank in range(chr_banks):
            bank_start = chr_start + (bank * 8192)
            bank_end = bank_start + 8192
            chr_data = rom_data[bank_start:bank_end]
            
            # Save the raw CHR data for reference
            with open(os.path.join(output_dir, f'chr_bank_{bank}.bin'), 'wb') as bin_file:
                bin_file.write(chr_data)
            
            # Convert to an image (16x16 tiles, each 8x8 pixels)
            img = Image.new('RGB', (128, 128), color='black')
            pixels = img.load()
            
            # NES color palette (simplified grayscale for now)
            palette = [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)]
            
            # Process each tile
            for tile_idx in range(256):
                tile_offset = tile_idx * 16
                
                # Calculate position in the output image
                tile_x = (tile_idx % 16) * 8
                tile_y = (tile_idx // 16) * 8
                
                # Process each row of the tile
                for row in range(8):
                    # Each row is defined by 2 bytes in the NES CHR format
                    byte1 = chr_data[tile_offset + row]
                    byte2 = chr_data[tile_offset + row + 8]
                    
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

def extract_individual_tiles(source_dir, output_dir, tile_size=8):
    """Extract individual 8x8 tiles from all CHR bank images"""
    # Create output directory for all tiles
    tiles_dir = os.path.join(output_dir, "all_tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    
    # Process each CHR bank PNG file
    for bank in range(4):  # Assuming 4 CHR banks
        source_path = os.path.join(source_dir, f'chr_bank_{bank}.png')
        if not os.path.exists(source_path):
            continue
        
        # Load the source image
        try:
            source_img = Image.open(source_path)
        except Exception as e:
            print(f"Error opening image {source_path}: {e}")
            continue
        
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
                
                # Calculate the tile index within this bank
                tile_idx = y * tiles_x + x
                
                # Calculate global tile index across all banks
                global_idx = (bank * 256) + tile_idx
                
                # Save the tile with its bank and index info
                tile_filename = f"tile_{bank}_{tile_idx:03d}_0x{global_idx:02X}.png"
                tile_path = os.path.join(tiles_dir, tile_filename)
                
                # Save the tile
                tile.save(tile_path)
    
    print(f"Extracted all individual tiles to {tiles_dir}")
    return True

def organize_by_category(source_dir, category_base_dir):
    """Organize tiles into categories based on predefined ranges"""
    # Create category directories
    for category in CATEGORIES:
        os.makedirs(os.path.join(category_base_dir, category), exist_ok=True)
    
    # Create roguelike element directories
    roguelike_dir = os.path.join(category_base_dir, "roguelike_elements")
    os.makedirs(roguelike_dir, exist_ok=True)
    for element in ROGUELIKE_ELEMENTS:
        os.makedirs(os.path.join(roguelike_dir, element), exist_ok=True)
    
    # Create fallback directory for missing assets
    fallback_dir = os.path.join(category_base_dir, "fallbacks")
    os.makedirs(fallback_dir, exist_ok=True)
    
    # Process all extracted tiles
    tiles_dir = os.path.join(source_dir, "all_tiles")
    if not os.path.exists(tiles_dir):
        print(f"Error: Tiles directory {tiles_dir} not found")
        return False
    
    # Mapping to keep track of where tiles are categorized
    tile_mapping = {}
    
    # Copy tiles to appropriate category directories
    for filename in os.listdir(tiles_dir):
        if not filename.endswith(".png"):
            continue
        
        # Parse the tile index from the filename
        # Format is tile_<bank>_<index>_0x<hex>.png
        try:
            parts = filename.split('_')
            bank = int(parts[1])
            tile_idx = int(parts[2])
            hex_idx = int(parts[3].split('.')[0][2:], 16)
            
            # Determine which category this tile belongs to
            assigned_category = None
            
            for category, info in CATEGORIES.items():
                for start, end in info["tile_ranges"]:
                    if start <= hex_idx <= end:
                        assigned_category = category
                        break
                if assigned_category:
                    break
            
            # If no category was assigned, place in "misc"
            if not assigned_category:
                assigned_category = "misc"
                os.makedirs(os.path.join(category_base_dir, "misc"), exist_ok=True)
            
            # Copy the tile to its category directory
            source_path = os.path.join(tiles_dir, filename)
            dest_path = os.path.join(category_base_dir, assigned_category, filename)
            shutil.copy(source_path, dest_path)
            
            # Add to mapping
            if assigned_category not in tile_mapping:
                tile_mapping[assigned_category] = []
            tile_mapping[assigned_category].append({
                "bank": bank,
                "tile_idx": tile_idx,
                "hex_idx": f"0x{hex_idx:02X}",
                "filename": filename
            })
            
            # Check if this is a potential roguelike element
            for element, info in ROGUELIKE_ELEMENTS.items():
                if hex_idx in info["potential_tiles"]:
                    element_path = os.path.join(roguelike_dir, element, filename)
                    shutil.copy(source_path, element_path)
                    
                    # Add to mapping
                    if "roguelike_elements" not in tile_mapping:
                        tile_mapping["roguelike_elements"] = {}
                    if element not in tile_mapping["roguelike_elements"]:
                        tile_mapping["roguelike_elements"][element] = []
                    tile_mapping["roguelike_elements"][element].append({
                        "bank": bank,
                        "tile_idx": tile_idx,
                        "hex_idx": f"0x{hex_idx:02X}",
                        "filename": filename
                    })
                    
        except (IndexError, ValueError) as e:
            print(f"Error parsing filename {filename}: {e}")
            continue
    
    # Create fallback sprites for essential elements
    create_fallback_sprites(fallback_dir)
    
    # Save the tile mapping as JSON
    mapping_path = os.path.join(category_base_dir, "tile_mapping.json")
    with open(mapping_path, 'w') as mapping_file:
        json.dump(tile_mapping, mapping_file, indent=2)
    
    print(f"Organized tiles by category in {category_base_dir}")
    print(f"Tile mapping saved to {mapping_path}")
    return True

def create_fallback_sprites(fallback_dir):
    """Create simple fallback sprites for essential game elements"""
    # Create a basic wall tile
    wall_img = Image.new('RGB', (8, 8), color='gray')
    pixels = wall_img.load()
    # Add some texture
    for i in range(8):
        for j in range(8):
            if (i + j) % 2 == 0:
                pixels[i, j] = (100, 100, 100)
    wall_img.save(os.path.join(fallback_dir, "wall.png"))
    
    # Create a basic floor tile
    floor_img = Image.new('RGB', (8, 8), color='brown')
    pixels = floor_img.load()
    # Add some texture
    for i in range(8):
        for j in range(8):
            if (i + j) % 3 == 0:
                pixels[i, j] = (120, 80, 40)
    floor_img.save(os.path.join(fallback_dir, "floor.png"))
    
    # Create a basic door tile
    door_img = Image.new('RGB', (8, 8), color='brown')
    pixels = door_img.load()
    # Draw a door shape
    for i in range(8):
        for j in range(8):
            if 2 <= i <= 5 and 1 <= j <= 6:
                pixels[i, j] = (150, 100, 50)
            if i == 5 and j == 4:  # doorknob
                pixels[i, j] = (200, 200, 100)
    door_img.save(os.path.join(fallback_dir, "door.png"))
    
    # Create a basic stairs tile
    stairs_img = Image.new('RGB', (8, 8), color='gray')
    pixels = stairs_img.load()
    # Draw stairs
    for i in range(8):
        for j in range(8):
            if j >= i:
                pixels[i, j] = (180, 180, 180)
    stairs_img.save(os.path.join(fallback_dir, "stairs.png"))
    
    # Create a basic item placeholder
    item_img = Image.new('RGB', (8, 8), color='black')
    pixels = item_img.load()
    # Draw a question mark
    for i in range(2, 6):
        pixels[i, 2] = (255, 255, 255)
    for i in range(5, 7):
        pixels[5, i] = (255, 255, 255)
    pixels[3, 5] = (255, 255, 255)
    item_img.save(os.path.join(fallback_dir, "unknown_item.png"))
    
    # Create a basic player placeholder
    player_img = Image.new('RGB', (8, 8), color='black')
    pixels = player_img.load()
    # Draw a simple character
    for i in range(2, 6):
        pixels[i, 2] = (255, 0, 0)  # head
    for i in range(1, 7):
        pixels[i, 4] = (255, 0, 0)  # body
    for i in range(3, 5):
        pixels[i, 3] = (255, 0, 0)  # neck
    for i in range(3, 6):
        pixels[i, 5] = (255, 0, 0)  # legs
        pixels[i, 6] = (255, 0, 0)  # feet
    player_img.save(os.path.join(fallback_dir, "player.png"))
    
    print(f"Created fallback sprites in {fallback_dir}")

def generate_documentation(base_dir, output_dir):
    """Generate documentation for all asset categories"""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load tile mapping
    mapping_path = os.path.join(base_dir, "tile_mapping.json")
    if not os.path.exists(mapping_path):
        print(f"Error: Tile mapping file {mapping_path} not found")
        return False
    
    with open(mapping_path, 'r') as mapping_file:
        tile_mapping = json.load(mapping_file)
    
    # Create main documentation file
    doc_path = os.path.join(output_dir, "asset_documentation.md")
    with open(doc_path, 'w') as doc_file:
        doc_file.write("# Craven Caverns Asset Documentation\n\n")
        doc_file.write("## Asset Categories\n\n")
        
        # Document each category
        for category, info in CATEGORIES.items():
            doc_file.write(f"### {category.title()}\n\n")
            doc_file.write(f"{info['description']}\n\n")
            
            if category in tile_mapping:
                doc_file.write("| Tile Index | Hex | Filename |\n")
                doc_file.write("|------------|-----|----------|\n")
                
                for tile in tile_mapping[category]:
                    doc_file.write(f"| {tile['tile_idx']} | {tile['hex_idx']} | {tile['filename']} |\n")
            
            doc_file.write("\n")
        
        # Document roguelike elements
        doc_file.write("## Roguelike Game Elements\n\n")
        
        if "roguelike_elements" in tile_mapping:
            for element, tiles in tile_mapping["roguelike_elements"].items():
                doc_file.write(f"### {element.title()}\n\n")
                doc_file.write(f"{ROGUELIKE_ELEMENTS[element]['description']}\n\n")
                
                doc_file.write("| Tile Index | Hex | Filename |\n")
                doc_file.write("|------------|-----|----------|\n")
                
                for tile in tiles:
                    doc_file.write(f"| {tile['tile_idx']} | {tile['hex_idx']} | {tile['filename']} |\n")
                
                doc_file.write("\n")
        
        # Document fallback sprites
        doc_file.write("## Fallback Sprites\n\n")
        doc_file.write("These simple sprites are used as fallbacks if assets are missing.\n\n")
        
        fallback_dir = os.path.join(base_dir, "fallbacks")
        if os.path.exists(fallback_dir):
            for filename in os.listdir(fallback_dir):
                if filename.endswith(".png"):
                    sprite_name = filename.split('.')[0]
                    doc_file.write(f"- {sprite_name}.png: Fallback for {sprite_name}\n")
    
    print(f"Generated documentation at {doc_path}")
    return True

def generate_c_header(base_dir, output_dir):
    """Generate C header files for using the assets in the NES game"""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load tile mapping
    mapping_path = os.path.join(base_dir, "tile_mapping.json")
    if not os.path.exists(mapping_path):
        print(f"Error: Tile mapping file {mapping_path} not found")
        return False
    
    with open(mapping_path, 'r') as mapping_file:
        tile_mapping = json.load(mapping_file)
    
    # Create main sprites header file
    header_path = os.path.join(output_dir, "arkista_sprites.h")
    with open(header_path, 'w') as header_file:
        header_file.write("/**\n")
        header_file.write(" * Arkista's Ring Sprite Definitions for Craven Caverns\n")
        header_file.write(" * Auto-generated by asset organization tool\n")
        header_file.write(" */\n\n")
        
        header_file.write("#ifndef ARKISTA_SPRITES_H\n")
        header_file.write("#define ARKISTA_SPRITES_H\n\n")
        
        # Define sprite groups
        for category, info in CATEGORIES.items():
            header_file.write(f"// {info['description']}\n")
            
            if category in tile_mapping:
                for i, tile in enumerate(tile_mapping[category]):
                    define_name = f"SPRITE_{category.upper()}_{i}"
                    header_file.write(f"#define {define_name.ljust(30)} {tile['hex_idx']}\n")
            
            header_file.write("\n")
        
        # Define roguelike elements
        header_file.write("// Roguelike game elements\n")
        
        if "roguelike_elements" in tile_mapping:
            for element, tiles in tile_mapping["roguelike_elements"].items():
                for i, tile in enumerate(tiles):
                    define_name = f"SPRITE_{element.upper()}_{i}"
                    header_file.write(f"#define {define_name.ljust(30)} {tile['hex_idx']}\n")
            
            header_file.write("\n")
        
        header_file.write("#endif // ARKISTA_SPRITES_H\n")
    
    print(f"Generated C header file at {header_path}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Extract and organize Arkista\'s Ring assets')
    parser.add_argument('rom_path', help='Path to the Arkista\'s Ring ROM file')
    parser.add_argument('--output', '-o', default='arkista_assets', 
                        help='Output directory for processed assets')
    
    args = parser.parse_args()
    
    # Check if ROM file exists
    if not os.path.isfile(args.rom_path):
        print(f"Error: ROM file {args.rom_path} does not exist")
        return False
    
    # Create output directories
    output_dir = os.path.abspath(args.output)
    chr_dir = os.path.join(output_dir, "chr_data")
    sprites_dir = os.path.join(output_dir, "sprites")
    docs_dir = os.path.join(output_dir, "docs")
    include_dir = os.path.join(output_dir, "include")
    
    # Extract CHR data
    print("Extracting CHR data from ROM...")
    if not extract_chr_banks(args.rom_path, chr_dir):
        return False
    
    # Extract individual tiles
    print("Extracting individual tiles...")
    if not extract_individual_tiles(chr_dir, chr_dir):
        return False
    
    # Organize by category
    print("Organizing tiles by category...")
    if not organize_by_category(chr_dir, sprites_dir):
        return False
    
    # Generate documentation
    print("Generating documentation...")
    if not generate_documentation(sprites_dir, docs_dir):
        return False
    
    # Generate C header files
    print("Generating C header files...")
    if not generate_c_header(sprites_dir, include_dir):
        return False
    
    print("\nAsset extraction and organization complete!")
    print(f"All assets organized in: {output_dir}")
    print("\nNext steps:")
    print("1. Check the documentation in the 'docs' directory")
    print("2. Include the generated header file in your game code")
    print("3. Use the categorized sprites for developing your roguelike game")
    print("4. Fallback sprites are available if needed")
    
    return True

if __name__ == '__main__':
    main()
