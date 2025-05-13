#!/usr/bin/env python3
"""
Arkista's Ring Sprite Extraction Tool
-------------------------------------
This tool specializes in extracting and analyzing sprites from Arkista's Ring
ROM data, identifying sprite patterns, and generating usable sprite sheets and
configuration data for a NES roguelike game.

Requirements:
- Python 3.6+
- Pillow (PIL) library
- (Optional) pyrominfo for ROM analysis
"""

import os
import sys
import argparse
import json
from PIL import Image, ImageDraw

# Constants for NES sprite properties
TILE_SIZE = 8  # Standard NES tile size is 8x8 pixels
SPRITE_SIZE = 16  # Most character sprites are 16x16 (2x2 tiles)

# Character definitions for Arkista's Ring
# This organizes all sprites by character, with explicit tile indices for each direction/animation
ARKISTA_CHARACTERS = {
    # Main player character (Dana from Arkista's Ring)
    "player": {
        "name": "Player (Dana)",
        "chr_bank": 0,  
        "sprites": {
            "down_1": 0x40,   # Tile index for down-facing animation frame 1
            "down_2": 0x44,   # Tile index for down-facing animation frame 2
            "up_1": 0x48,     # Tile index for up-facing animation frame 1
            "up_2": 0x4C,     # Tile index for up-facing animation frame 2
            "right_1": 0x50,  # Tile index for right-facing animation frame 1
            "right_2": 0x54,  # Tile index for right-facing animation frame 2
            # Left-facing sprites are not present for player - might be mirrored right sprites
        }
    },
    # Slime enemy (Green blob monster)
    "slime": {
        "name": "Slime Monster",
        "chr_bank": 0,
        "sprites": {
            "left_1": 0x58,   # What appeared as "player_left_1"
            "left_2": 0x5C,   # What appeared as "player_left_2"
            "right_1": 0x60,
            "right_2": 0x64
        }
    },
    # Skeleton enemy
    "skeleton": {
        "name": "Skeleton",
        "chr_bank": 0,
        "sprites": {
            "down_1": 0x68,
            "down_2": 0x6C,
            "left_1": 0x70,
            "left_2": 0x74
        }
    },
    # Bat enemy
    "bat": {
        "name": "Bat",
        "chr_bank": 0,
        "sprites": {
            "fly_1": 0x78,
            "fly_2": 0x7C
        }
    },
    # Spider enemy
    "spider": {
        "name": "Spider",
        "chr_bank": 0,
        "sprites": {
            "move_1": 0x80,
            "move_2": 0x84
        }
    },
    # Small fairy/pixie
    "fairy": {
        "name": "Fairy/Pixie",
        "chr_bank": 0,
        "sprites": {
            "idle_1": 0x88,
            "idle_2": 0x8C
        }
    },
    # Wizard/mage enemy
    "wizard": {
        "name": "Wizard",
        "chr_bank": 0,
        "sprites": {
            "cast_1": 0x90,
            "cast_2": 0x94
        }
    },
    # Chest/treasure
    "chest": {
        "name": "Treasure Chest",
        "chr_bank": 0,
        "sprites": {
            "closed": 0x98,
            "open": 0x9C
        }
    },
    # Heart item
    "heart": {
        "name": "Heart Item",
        "chr_bank": 0,
        "sprites": {
            "pickup": 0xA0
        }
    },
    # Key item
    "key": {
        "name": "Key Item",
        "chr_bank": 0,
        "sprites": {
            "pickup": 0xA4
        }
    },
    # Sword weapon
    "sword": {
        "name": "Sword Weapon",
        "chr_bank": 0,
        "sprites": {
            "pickup": 0xA8
        }
    }
    # Note: These definitions are based on analysis and may need adjustment
    # as we verify the actual sprites from the game
}

# Sprite arrangement pattern for Arkista's Ring (swapped top-right and bottom-left quadrants)
ARKISTA_ARRANGEMENT = [0, 2, 1, 3]

# Function to convert the character definitions into the format needed by the sprite extraction code
def generate_sprite_metadata():
    metadata = {}
    
    # Process each character
    for char_id, char_info in ARKISTA_CHARACTERS.items():
        # Process each sprite direction/animation
        for sprite_id, base_tile in char_info["sprites"].items():
            # Create a unique ID for this sprite
            full_id = f"{char_id}_{sprite_id}"
            
            # Add to metadata dictionary
            metadata[full_id] = {
                "base_tile": base_tile,
                "size": (2, 2),  # Standard 16x16 sprites (2x2 tiles)
                "arrangement": ARKISTA_ARRANGEMENT,
                "category": char_id,
                "name": f"{char_info['name']} - {sprite_id}"
            }
    
    return metadata

# Generate the complete sprite metadata
ARKISTA_SPRITE_METADATA = generate_sprite_metadata()

class ArkistaSprite:
    """Class representing a complete sprite from Arkista's Ring"""
    
    def __init__(self, name, base_tile, size, arrangement, category):
        self.name = name
        self.base_tile = base_tile  # Starting tile index
        self.width_tiles = size[0]
        self.height_tiles = size[1]
        self.arrangement = arrangement  # How tiles are arranged
        self.category = category
        self.width_px = size[0] * TILE_SIZE
        self.height_px = size[1] * TILE_SIZE
        self.image = None  # Will hold the composed sprite image
    
    def compose_from_tiles(self, tiles):
        """Create a complete sprite image from individual tiles"""
        self.image = Image.new('RGBA', (self.width_px, self.height_px), (0, 0, 0, 0))
        
        for i, rel_idx in enumerate(self.arrangement):
            # Calculate position in the composed image
            x = (i % self.width_tiles) * TILE_SIZE
            y = (i // self.width_tiles) * TILE_SIZE
            
            # Get the actual tile index
            tile_idx = self.base_tile + rel_idx
            
            # Ensure the tile exists
            if tile_idx < len(tiles):
                self.image.paste(tiles[tile_idx], (x, y))
            else:
                print(f"Warning: Tile index {tile_idx} not found for sprite {self.name}")
        
        return self.image
    
    def save(self, output_dir):
        """Save the composed sprite to a file"""
        if self.image:
            # Create category directory if needed
            category_dir = os.path.join(output_dir, self.category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Save the image
            filepath = os.path.join(category_dir, f"{self.name}.png")
            self.image.save(filepath)
            print(f"Saved sprite: {filepath}")
            return filepath
        else:
            print(f"Warning: No image data for sprite {self.name}")
            return None

def extract_chr_from_rom(rom_path, output_dir, bank_index=0):
    """Extract CHR data from a ROM file (simplified approach)"""
    print("ROM extraction not implemented yet. Please use a CHR viewer tool")
    print("to extract the CHR banks and provide them as PNG files.")
    return False

def extract_tiles_from_chr(chr_path, output_dir, palette=None):
    """Extract individual 8x8 tiles from a CHR bank image"""
    try:
        source_img = Image.open(chr_path)
    except Exception as e:
        print(f"Error opening CHR image {chr_path}: {e}")
        return []
    
    # Get image dimensions
    width, height = source_img.size
    
    # Calculate number of tiles in each dimension
    tiles_x = width // TILE_SIZE
    tiles_y = height // TILE_SIZE
    
    tiles = []
    
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
            
            # If we have color information, apply it
            if palette:
                # This would require more complex color processing
                pass
            
            # Save the individual tile
            tile_idx = y * tiles_x + x
            tile_filename = f"tile_{tile_idx:03d}.png"
            tile_path = os.path.join(output_dir, "tiles", tile_filename)
            
            # Create directory if needed
            os.makedirs(os.path.join(output_dir, "tiles"), exist_ok=True)
            
            # Save the tile
            tile.save(tile_path)
            
            # Add to the tiles list
            tiles.append(tile)
    
    print(f"Extracted {len(tiles)} tiles from {chr_path}")
    return tiles

def compose_sprites(tiles, output_dir, metadata=None):
    """Create complete sprites from individual tiles using metadata"""
    if metadata is None:
        metadata = ARKISTA_SPRITE_METADATA
    
    sprites = []
    sprite_data = {}  # For the config file
    
    for sprite_name, sprite_info in metadata.items():
        # Create and compose the sprite
        sprite = ArkistaSprite(
            sprite_name,
            sprite_info['base_tile'],
            sprite_info['size'],
            sprite_info['arrangement'],
            sprite_info['category']
        )
        
        sprite.compose_from_tiles(tiles)
        sprite_path = sprite.save(output_dir)
        
        if sprite_path:
            sprites.append(sprite)
            
            # Add to sprite data config
            sprite_data[sprite_name] = {
                "file": os.path.relpath(sprite_path, output_dir),
                "tile_width": sprite_info['size'][0],
                "tile_height": sprite_info['size'][1],
                "base_tile": sprite_info['base_tile'],
                "arrangement": sprite_info['arrangement']
            }
    
    # Save sprite configuration
    config_path = os.path.join(output_dir, "sprite_config.json")
    with open(config_path, 'w') as f:
        json.dump(sprite_data, f, indent=2)
    
    print(f"Composed {len(sprites)} sprites and saved config to {config_path}")
    return sprites

def create_sprite_sheet(sprites, output_dir, sheet_name="sprite_sheet"):
    """Create a consolidated sprite sheet from all sprites"""
    if not sprites:
        print("No sprites to create a sheet from")
        return None
    
    # Determine sprite sheet dimensions
    max_width = max(sprite.width_px for sprite in sprites)
    max_height = max(sprite.height_px for sprite in sprites)
    
    # Create a simple grid layout
    cols = min(8, len(sprites))  # Limit to 8 columns
    rows = (len(sprites) + cols - 1) // cols  # Ceiling division
    
    # Create the sprite sheet image
    sheet_width = cols * max_width
    sheet_height = rows * max_height
    sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Position and paste each sprite
    for i, sprite in enumerate(sprites):
        x = (i % cols) * max_width
        y = (i // cols) * max_height
        
        # Center the sprite in its grid cell
        x_offset = (max_width - sprite.width_px) // 2
        y_offset = (max_height - sprite.height_px) // 2
        
        sheet.paste(sprite.image, (x + x_offset, y + y_offset))
    
    # Save the sprite sheet
    sheet_path = os.path.join(output_dir, f"{sheet_name}.png")
    sheet.save(sheet_path)
    print(f"Created sprite sheet: {sheet_path}")
    
    return sheet_path

def analyze_chr_patterns(chr_path, output_dir):
    """Analyze CHR bank to attempt to automatically identify sprite patterns"""
    print("Analyzing CHR patterns...")
    print("This is an advanced feature that requires visual pattern recognition.")
    print("For now, use the manual sprite configuration in the metadata dictionary.")
    
    # Future enhancement: Use computer vision or pattern matching to identify
    # which tiles likely form complete sprites based on visual similarity
    return {}

def create_test_rom(sprites_dir, output_dir):
    """Create a simple NES test ROM that displays the extracted sprites"""
    print("Creating test ROM is not implemented yet.")
    print("You can use the extracted sprites with your existing game code.")
    return False

def main():
    parser = argparse.ArgumentParser(description='Extract and process sprites from Arkista\'s Ring')
    parser.add_argument('input', help='Path to CHR bank PNG file or ROM file')
    parser.add_argument('--output', '-o', default='arkista_sprites', 
                        help='Output directory for processed sprites')
    parser.add_argument('--analyze', '-a', action='store_true',
                        help='Attempt to automatically analyze sprite patterns')
    parser.add_argument('--rom', '-r', action='store_true',
                        help='Input is a ROM file (not implemented yet)')
    parser.add_argument('--test-rom', '-t', action='store_true',
                        help='Create a test ROM to visualize sprites (not implemented yet)')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Process input based on type
    if args.rom:
        print("ROM processing is not fully implemented yet.")
        if not extract_chr_from_rom(args.input, args.output):
            return False
    else:
        # Process CHR bank image
        if not os.path.isfile(args.input):
            print(f"Error: Input file {args.input} does not exist")
            return False
        
        print(f"Processing CHR bank image: {args.input}")
        
        # Extract individual tiles
        tiles = extract_tiles_from_chr(args.input, args.output)
        
        if not tiles:
            print("Failed to extract tiles")
            return False
        
        # Analyze patterns if requested
        sprite_metadata = ARKISTA_SPRITE_METADATA
        if args.analyze:
            detected_metadata = analyze_chr_patterns(args.input, args.output)
            if detected_metadata:
                # Merge with known metadata
                sprite_metadata.update(detected_metadata)
        
        # Compose sprites
        sprites = compose_sprites(tiles, args.output, sprite_metadata)
        
        # Create sprite sheet
        if sprites:
            create_sprite_sheet(sprites, args.output)
        
        # Create test ROM if requested
        if args.test_rom:
            create_test_rom(args.output, args.output)
    
    print(f"Sprite processing completed successfully!")
    print(f"Processed sprites are in: {args.output}")
    print("\nNext steps:")
    print("1. Review the extracted sprites in the output directory")
    print("2. Update the ARKISTA_SPRITE_METADATA dictionary with correct tile indices and arrangements")
    print("3. Run the tool again to generate updated sprites")
    print("4. Use the sprite_config.json file in your game code")
    
    return True

if __name__ == '__main__':
    main()
