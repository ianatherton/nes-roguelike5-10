#!/usr/bin/env python3
"""
NES Asset Wizard - Core Module
-----------------------------
Provides core functions for the NES sprite asset wizard system.
This module focuses on data structures and helper functions.
"""

import os
import json
import uuid
import datetime
from pathlib import Path

# Animation type definitions
ANIMATION_TYPES = [
    "idle",
    "walk",
    "run",
    "attack",
    "jump",
    "fall",
    "hit",
    "death",
    "spawn",
    "open",  # For chests, doors, etc.
    "closed",
    "special"  # For custom animations
]

# Direction types for character animations
DIRECTION_TYPES = [
    "",       # No direction (single orientation)
    "up",
    "down",
    "left",
    "right",
    "up_left",
    "up_right",
    "down_left",
    "down_right"
]

# Asset type definitions
ASSET_TYPES = {
    "Player": "Player character sprites and animations",
    "Enemy": "Enemy sprites and animations",
    "Item": "Collectible items and power-ups",
    "UI": "User interface elements",
    "Background": "Background tiles and decorations",
    "Effect": "Visual effects like explosions",
    "Prop": "Static game world objects"
}

# Default metadata structure
def create_default_metadata(asset_type="Player", name="New Asset"):
    """Create default metadata for a new asset"""
    asset_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    
    # Set default size based on asset type
    if asset_type in ["Player", "Enemy", "Effect"]:
        size = (16, 16)  # Standard 16x16 sprite for characters and effects
    else:
        size = (8, 8)    # 8x8 for items, UI elements, etc.
    
    # Set default palette
    palette = [0, 1, 2, 3]  # Default NES palette indices
    
    # Get the description from asset types
    description = ASSET_TYPES.get(asset_type, "Custom asset")
    
    return {
        "id": asset_id,
        "name": name,
        "type": asset_type,
        "description": description,
        "created_at": now,
        "updated_at": now,
        "size": size,
        "chr_bank": 0,
        "palette": palette,
        "animations": [],
        "sprites": [],
        "export_configs": {
            "nes_asm": {
                "label_prefix": f"{name.lower().replace(' ', '_')}",
                "include_palette": True
            },
            "json": {
                "include_sprites": True,
                "organize_by_type": True
            }
        },
        "tags": []
    }

# Animation frame management
def create_animation_definition(asset_id, name, animation_type="idle", direction="down", frame_duration=10, loop=True):
    """Create a new animation definition for an asset"""
    return {
        "id": str(uuid.uuid4()),
        "asset_id": asset_id,
        "name": name,
        "type": animation_type,
        "direction": direction,
        "frames": [],
        "frame_duration": frame_duration,
        "loop": loop,
        "created_at": datetime.datetime.now().isoformat()
    }

# Sprite frame management
def create_sprite_definition(asset_id, name, file_path=None, animation_type=None, direction=None, frame_number=0):
    """Create a new sprite frame definition"""
    return {
        "id": str(uuid.uuid4()),
        "asset_id": asset_id,
        "name": name,
        "file_path": file_path,
        "animation_type": animation_type,
        "direction": direction,
        "frame_number": frame_number,
        "tile_arrangement": [0, 1, 2, 3],  # Default NES 2x2 tile arrangement
        "created_at": datetime.datetime.now().isoformat()
    }

# File management
def ensure_asset_directory(base_dir, asset_id=None):
    """Ensure the directory structure exists for an asset"""
    if asset_id:
        asset_dir = os.path.join(base_dir, "assets", asset_id)
    else:
        asset_dir = os.path.join(base_dir, "assets")
    
    # Create directories
    os.makedirs(asset_dir, exist_ok=True)
    os.makedirs(os.path.join(asset_dir, "sprites"), exist_ok=True)
    os.makedirs(os.path.join(asset_dir, "exports"), exist_ok=True)
    
    return asset_dir

def save_asset_metadata(base_dir, asset_data):
    """Save asset metadata to file"""
    asset_id = asset_data["id"]
    asset_dir = ensure_asset_directory(base_dir, asset_id)
    metadata_file = os.path.join(asset_dir, "metadata.json")
    
    # Update the updated_at timestamp
    asset_data["updated_at"] = datetime.datetime.now().isoformat()
    
    # Save to file
    with open(metadata_file, 'w') as f:
        json.dump(asset_data, f, indent=2)
    
    return metadata_file

def load_asset_metadata(base_dir, asset_id):
    """Load asset metadata from file"""
    asset_dir = os.path.join(base_dir, "assets", asset_id)
    metadata_file = os.path.join(asset_dir, "metadata.json")
    
    if not os.path.exists(metadata_file):
        return None
    
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    
    return data

def generate_sprite_filename(asset_id, name, animation_type=None, direction=None, frame=None):
    """Generate a standardized filename for a sprite"""
    base_name = name.lower().replace(' ', '_')
    
    if animation_type and direction and frame is not None:
        return f"{base_name}_{animation_type}_{direction}_{frame:02d}.png"
    elif animation_type and direction:
        return f"{base_name}_{animation_type}_{direction}.png"
    elif animation_type:
        return f"{base_name}_{animation_type}.png"
    else:
        return f"{base_name}.png"

# Asset list management
def get_asset_list(base_dir):
    """Get a list of all assets in the assets directory"""
    assets_dir = os.path.join(base_dir, "assets")
    if not os.path.exists(assets_dir):
        return []
    
    asset_list = []
    for asset_id in os.listdir(assets_dir):
        asset_dir = os.path.join(assets_dir, asset_id)
        if os.path.isdir(asset_dir):
            metadata_file = os.path.join(asset_dir, "metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    try:
                        metadata = json.load(f)
                        asset_list.append(metadata)
                    except json.JSONDecodeError:
                        print(f"Error reading metadata for asset {asset_id}")
    
    # Sort by updated_at
    asset_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return asset_list

# Conversion utilities
def convert_to_nes_palette(rgb_color):
    """Find the closest NES palette color to the given RGB color"""
    # Import at function level to avoid circular imports
    try:
        from .nes_palette import NES_PALETTE
    except ImportError:
        # Fallback to a minimal palette if module not found
        NES_PALETTE = [
            (0, 0, 0),        # Black
            (255, 255, 255),  # White
            (255, 0, 0),      # Red
            (0, 255, 0),      # Green
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
            (0, 255, 255)     # Cyan
        ]
    
    # Find the closest color by Euclidean distance
    min_distance = float('inf')
    closest_index = 0
    
    for i, nes_color in enumerate(NES_PALETTE):
        # Calculate Euclidean distance
        distance = sum((c1 - c2)**2 for c1, c2 in zip(rgb_color, nes_color))
        
        if distance < min_distance:
            min_distance = distance
            closest_index = i
    
    return closest_index

# Generate JSON export data for use with C/assembly code
def generate_game_json_data(asset_data):
    """Generate a game-ready JSON representation for this asset"""
    asset_type = asset_data["type"]
    
    # Create a simplified, cleaned version of the asset data
    game_data = {
        "id": asset_data["id"],
        "name": asset_data["name"],
        "type": asset_type,
        "description": asset_data["description"],
        "size": asset_data["size"],
        "chr_bank": asset_data["chr_bank"],
        "palette": asset_data["palette"],
        "sprites": [],
        "animations": [],
        "metadata": {
            "created": asset_data.get("created_at", ""),
            "updated": asset_data.get("updated_at", ""),
            "generator": "NES Asset Wizard",
            "version": "1.0"
        }
    }
    
    # Process sprites - creating a cleaned list with only needed fields
    for sprite in asset_data.get("sprites", []):
        # Extract relative path from file_path to make it portable
        file_path = sprite.get("file_path", "")
        rel_path = os.path.basename(file_path) if file_path else ""
        
        game_data["sprites"].append({
            "id": sprite.get("id", ""),
            "name": sprite.get("name", ""),
            "file": rel_path,
            "animation_type": sprite.get("animation_type", ""),
            "direction": sprite.get("direction", ""),
            "frame": sprite.get("frame_number", 0),
            "arrangement": sprite.get("tile_arrangement", [0, 1, 2, 3])
        })
    
    # Process animations
    for anim in asset_data.get("animations", []):
        game_data["animations"].append({
            "id": anim.get("id", ""),
            "name": anim.get("name", ""),
            "type": anim.get("type", ""),
            "direction": anim.get("direction", ""),
            "frames": anim.get("frames", []),
            "frame_duration": anim.get("frame_duration", 10),
            "loop": anim.get("loop", True)
        })
    
    return game_data

# Export asset in game-ready format
def get_asset_dir(base_dir, asset_data):
    """Get the directory for an asset, ensuring it exists"""
    asset_id = asset_data["id"]
    asset_dir = os.path.join(base_dir, "assets", asset_id)
    os.makedirs(asset_dir, exist_ok=True)
    return asset_dir

def save_frame_image(frame_image, asset_dir, filename):
    """Save a frame image to the asset's sprites directory"""
    # Ensure the sprites directory exists
    sprites_dir = os.path.join(asset_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    
    # Save the image
    file_path = os.path.join(sprites_dir, filename)
    frame_image.save(file_path)
    return file_path

def save_asset(base_dir, asset_data):
    """Save an asset, including its metadata"""
    # Ensure the asset directory exists
    asset_dir = get_asset_dir(base_dir, asset_data)
    
    # Save the metadata file
    metadata_file = os.path.join(asset_dir, "metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(asset_data, f, indent=2)
    
    return metadata_file

def export_asset_for_game(base_dir, asset_data, export_dir=None):
    """Export asset in a format ready for game integration"""
    asset_id = asset_data["id"]
    asset_name = asset_data["name"].lower().replace(" ", "_")
    
    # If no export directory is specified, use the assets/export directory
    if not export_dir:
        export_dir = os.path.join(base_dir, "export")
    
    # Ensure the export directory exists
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate the game-ready JSON data
    game_data = generate_game_json_data(asset_data)
    
    # Save JSON file
    json_file = os.path.join(export_dir, f"{asset_name}.json")
    with open(json_file, 'w') as f:
        json.dump(game_data, f, indent=2)
    
    # Export sprite files if they exist
    if "sprites" in asset_data and asset_data["sprites"]:
        # Create a sprites directory for this asset
        sprites_dir = os.path.join(export_dir, f"{asset_name}_sprites")
        os.makedirs(sprites_dir, exist_ok=True)
        
        # Copy each sprite file
        for sprite in asset_data["sprites"]:
            if "file_path" in sprite and os.path.exists(sprite["file_path"]):
                # Get sprite information
                anim_type = sprite.get("animation_type", "idle")
                direction = sprite.get("direction", "")
                frame = sprite.get("frame", 0)
                
                # Generate output filename
                if direction:
                    out_file = f"{anim_type}_{direction}_{frame:02d}.png"
                else:
                    out_file = f"{anim_type}_{frame:02d}.png"
                
                # Copy the file
                import shutil
                shutil.copy2(sprite["file_path"], os.path.join(sprites_dir, out_file))
    
    return json_file

# Simple example usage
if __name__ == "__main__":
    # Create a new player asset
    player_metadata = create_default_metadata("PLAYER", "Hero")
    
    # Set up a base directory
    base_dir = "./nes_assets"
    
    # Ensure directories exist
    ensure_asset_directory(base_dir, player_metadata["id"])
    
    # Add an animation
    idle_anim = create_animation_definition(
        player_metadata["id"], 
        "Idle Animation", 
        animation_type="idle",
        direction="down"
    )
    
    # Add the animation to the asset
    player_metadata["animations"].append(idle_anim)
    
    # Save the metadata
    save_asset_metadata(base_dir, player_metadata)
    
    print(f"Created new player asset: {player_metadata['name']}")
    print(f"Asset ID: {player_metadata['id']}")
