#!/usr/bin/env python3
"""
Arkista's Ring Pre-Pulled Spritesheet Extractor
-----------------------------------------------
Extracts sprites from pre-pulled spritesheets in the arspritesheets folder.
Handles character, enemy, and UI sprites while preserving the original palette.

Requirements:
- Python 3.6+
- Pillow (PIL) library
"""

import os
import sys
import json
import argparse
from PIL import Image, ImageDraw, ImagePalette

# Constants
DEFAULT_SPRITE_SIZE = 16  # Default sprite size (most characters/enemies)
TILE_SIZE = 8             # Base NES tile size
TRANSPARENT_COLOR = (0, 0, 0, 0)  # Transparent color for output sprites

def detect_sprites(image_path, output_dir, sprite_size=(16, 16), 
                   transparent_color=(0, 0, 0)):
    """
    Detect sprites in a spritesheet by looking for non-transparent/non-background areas
    
    Args:
        image_path: Path to the spritesheet image
        output_dir: Directory to save extracted sprites
        sprite_size: Tuple (width, height) for sprite dimensions
        transparent_color: RGB color to treat as transparent (usually black for NES)
    
    Returns:
        List of extracted sprite info dictionaries
    """
    try:
        source_img = Image.open(image_path)
        # Convert to RGBA to handle transparency
        if source_img.mode != 'RGBA':
            source_img = source_img.convert('RGBA')
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return []
    
    # Get image dimensions
    width, height = source_img.size
    sprite_width, sprite_height = sprite_size
    
    # Create output directory for this spritesheet
    sheet_name = os.path.splitext(os.path.basename(image_path))[0]
    sheet_output_dir = os.path.join(output_dir, sheet_name)
    os.makedirs(sheet_output_dir, exist_ok=True)
    
    extracted_sprites = []
    sprite_count = 0
    
    # Scan the image for sprites
    for y in range(0, height - sprite_height + 1, sprite_height):
        for x in range(0, width - sprite_width + 1, sprite_width):
            # Crop the potential sprite
            sprite = source_img.crop((x, y, x + sprite_width, y + sprite_height))
            
            # Check if the sprite has any non-transparent pixels
            sprite_data = sprite.getdata()
            non_transparent_pixels = sum(1 for pixel in sprite_data 
                                        if pixel[:3] != transparent_color)
            
            # If we found a sprite with content
            if non_transparent_pixels > 5:  # Threshold to avoid empty sprites
                sprite_count += 1
                sprite_id = f"{sheet_name}_{sprite_count:03d}"
                
                # Create a new image with transparency
                new_sprite = Image.new('RGBA', sprite_size, (0, 0, 0, 0))
                
                # Copy the sprite with transparency
                for py in range(sprite_height):
                    for px in range(sprite_width):
                        pixel = sprite.getpixel((px, py))
                        if pixel[:3] != transparent_color:
                            new_sprite.putpixel((px, py), pixel)
                
                # Save the sprite
                sprite_filename = f"{sprite_id}.png"
                sprite_path = os.path.join(sheet_output_dir, sprite_filename)
                new_sprite.save(sprite_path)
                
                # Store sprite info
                extracted_sprites.append({
                    "id": sprite_id,
                    "source": sheet_name,
                    "position": (x, y),
                    "path": sprite_path,
                    "size": sprite_size
                })
    
    print(f"Extracted {len(extracted_sprites)} sprites from {sheet_name} to {sheet_output_dir}")
    return extracted_sprites

def detect_sprites_with_palette(image_path, output_dir, sprite_size=(16, 16)):
    """
    Detect sprites in a spritesheet and preserve the palette information
    """
    try:
        source_img = Image.open(image_path)
        # Check if image has a palette
        has_palette = source_img.mode == 'P'
        palette_data = None
        
        if has_palette:
            palette_data = source_img.getpalette()
            # Convert to RGBA for processing but keep palette data
            source_img = source_img.convert('RGBA')
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return []
    
    # Rest of the sprite detection is similar to detect_sprites
    sprites = detect_sprites(image_path, output_dir, sprite_size)
    
    # If we have palette data, create a palette file
    if palette_data and sprites:
        sheet_name = os.path.splitext(os.path.basename(image_path))[0]
        sheet_output_dir = os.path.join(output_dir, sheet_name)
        
        # Save palette information
        palette_info = {
            "source": sheet_name,
            "palette_data": [palette_data[i:i+3] for i in range(0, len(palette_data), 3)]
        }
        
        palette_path = os.path.join(sheet_output_dir, "palette.json")
        with open(palette_path, 'w') as f:
            json.dump(palette_info, f, indent=2)
        
        print(f"Saved palette information to {palette_path}")
    
    return sprites

def create_spritesheet(sprites, output_dir, sprite_size=(16, 16), columns=16):
    """
    Create a combined spritesheet from extracted sprites
    """
    if not sprites:
        return None
    
    # Get sprite images
    sprite_images = []
    for sprite in sprites:
        try:
            img = Image.open(sprite["path"])
            sprite_images.append((sprite["id"], img))
        except Exception as e:
            print(f"Error opening sprite {sprite['path']}: {e}")
    
    if not sprite_images:
        return None
    
    # Determine spritesheet dimensions
    sprite_width, sprite_height = sprite_size
    cols = min(columns, len(sprite_images))
    rows = (len(sprite_images) + cols - 1) // cols
    
    # Create spritesheet image
    sheet_width = cols * sprite_width
    sheet_height = rows * sprite_height
    sheet_img = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    # Add sprites to sheet
    for i, (sprite_id, img) in enumerate(sprite_images):
        x = (i % cols) * sprite_width
        y = (i // cols) * sprite_height
        sheet_img.paste(img, (x, y))
    
    # Save spritesheet
    sheet_path = os.path.join(output_dir, "combined_spritesheet.png")
    sheet_img.save(sheet_path)
    print(f"Created combined spritesheet with {len(sprite_images)} sprites: {sheet_path}")
    
    return sheet_path

def create_config_file(sprites, output_dir):
    """
    Create a configuration file mapping sprite IDs to their properties
    """
    config = {
        "sprites": {}
    }
    
    for sprite in sprites:
        config["sprites"][sprite["id"]] = {
            "source": sprite["source"],
            "position": sprite["position"],
            "size": sprite["size"],
            "relative_path": os.path.relpath(sprite["path"], output_dir)
        }
    
    config_path = os.path.join(output_dir, "ar_sprite_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created sprite configuration file: {config_path}")
    return config_path

def process_spritesheets(directory, output_dir, sprite_size=(16, 16)):
    """
    Process all PNG spritesheets in a directory
    """
    if not os.path.isdir(directory):
        print(f"Error: Input directory {directory} does not exist")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    all_sprites = []
    
    # Process each PNG file
    for filename in os.listdir(directory):
        if filename.lower().endswith('.png') and "Map" not in filename:
            file_path = os.path.join(directory, filename)
            print(f"Processing {filename}...")
            
            # Detect sprites with palette preservation
            sprites = detect_sprites_with_palette(file_path, output_dir, sprite_size)
            all_sprites.extend(sprites)
    
    # Create combined spritesheet and config
    if all_sprites:
        create_spritesheet(all_sprites, output_dir, sprite_size)
        create_config_file(all_sprites, output_dir)
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Arkista\'s Ring Pre-Pulled Spritesheet Extractor')
    parser.add_argument('--input', '-i', default='../arspritesheets',
                        help='Directory containing spritesheet PNGs')
    parser.add_argument('--output', '-o', default='../assets/extracted_arsprites',
                        help='Output directory for extracted sprites')
    parser.add_argument('--width', '-w', type=int, default=16,
                        help='Width of sprites to extract')
    parser.add_argument('--height', '-H', type=int, default=16,
                        help='Height of sprites to extract')
    
    args = parser.parse_args()
    
    # Use provided or default sprite size
    sprite_size = (args.width, args.height)
    
    # Process all spritesheets
    success = process_spritesheets(args.input, args.output, sprite_size)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
