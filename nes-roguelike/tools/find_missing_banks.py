#!/usr/bin/env python3
"""
Arkista's Ring ROM Scanner
--------------------------
This tool scans an Arkista's Ring ROM to identify potential CHR banks 
that haven't been extracted yet, particularly focusing on UI elements and text.
"""

import os
import sys
import argparse
from PIL import Image
import numpy as np

def extract_chr_bank(rom_data, bank_offset, bank_size=8192):
    """Extract a CHR bank from ROM data"""
    return rom_data[bank_offset:bank_offset + bank_size]

def chr_to_pattern_table(chr_data):
    """Convert CHR data to pattern table (8x8 tiles)"""
    tiles = []
    for tile_index in range(len(chr_data) // 16):
        offset = tile_index * 16
        tile = np.zeros((8, 8), dtype=np.uint8)
        
        # Each tile is 16 bytes - 8 bytes for low bit plane, 8 bytes for high bit plane
        for y in range(8):
            low_byte = chr_data[offset + y]
            high_byte = chr_data[offset + y + 8]
            
            for x in range(8):
                bit_index = 7 - x
                low_bit = (low_byte >> bit_index) & 1
                high_bit = (high_byte >> bit_index) & 1
                tile[y, x] = (high_bit << 1) | low_bit
        
        tiles.append(tile)
    
    return tiles

def save_pattern_table_as_image(tiles, output_file, palette=None):
    """Save pattern table as image"""
    if palette is None:
        # Use a default grayscale palette
        palette = [
            (0, 0, 0),      # 0 - Black
            (85, 85, 85),   # 1 - Dark Gray
            (170, 170, 170),# 2 - Light Gray
            (255, 255, 255) # 3 - White
        ]
    
    # Each tile is 8x8 pixels, arrange in a 16x16 grid (256 tiles per bank)
    img_width = 16 * 8
    img_height = ((len(tiles) + 15) // 16) * 8  # Round up to nearest multiple of 16
    
    img = Image.new('RGB', (img_width, img_height), color=palette[0])
    pixels = img.load()
    
    for tile_index, tile in enumerate(tiles):
        grid_x = (tile_index % 16) * 8
        grid_y = (tile_index // 16) * 8
        
        for y in range(8):
            for x in range(8):
                color_index = tile[y, x]
                if 0 <= color_index < len(palette):
                    pixels[grid_x + x, grid_y + y] = palette[color_index]
    
    img.save(output_file)
    return img

def analyze_bank_contents(tiles):
    """Analyze bank contents to determine if it might contain UI/text elements"""
    # Simple heuristics to identify UI/text banks:
    # 1. Count tiles with very few pixels set (text tends to have sparse patterns)
    # 2. Check for repetitive patterns that might indicate UI frames
    
    sparse_tiles = 0
    repetitive_tiles = 0
    total_tiles = len(tiles)
    
    for tile in tiles:
        # Count set pixels
        set_pixels = np.sum(tile > 0)
        if 1 <= set_pixels <= 16:  # Text typically has fewer set pixels
            sparse_tiles += 1
        
        # Check for patterns that might be UI frames (horizontal/vertical lines)
        horizontal_lines = 0
        vertical_lines = 0
        
        for y in range(8):
            if np.sum(tile[y, :] > 0) >= 6:  # Mostly filled horizontal line
                horizontal_lines += 1
        
        for x in range(8):
            if np.sum(tile[:, x] > 0) >= 6:  # Mostly filled vertical line
                vertical_lines += 1
        
        if horizontal_lines >= 2 or vertical_lines >= 2:
            repetitive_tiles += 1
    
    # Calculate percentages
    sparse_percent = (sparse_tiles / total_tiles) * 100
    repetitive_percent = (repetitive_tiles / total_tiles) * 100
    
    results = {
        "total_tiles": total_tiles,
        "sparse_tiles": sparse_tiles,
        "sparse_percent": sparse_percent,
        "repetitive_tiles": repetitive_tiles,
        "repetitive_percent": repetitive_percent,
        "likely_text": sparse_percent > 20,
        "likely_ui": repetitive_percent > 15,
        "confidence": (sparse_percent + repetitive_percent) / 2
    }
    
    return results

def find_chr_banks(rom_path, output_dir):
    """Find and analyze all potential CHR banks in the ROM"""
    with open(rom_path, 'rb') as f:
        rom_data = f.read()
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # NES ROM header is 16 bytes
    header_size = 16
    
    # Start scanning after header, typically CHR banks are in the second half of the ROM
    potential_banks = []
    
    # Scan every 8KB boundary for potential CHR banks
    for offset in range(header_size, len(rom_data) - 8192, 8192):
        bank_data = extract_chr_bank(rom_data, offset)
        tiles = chr_to_pattern_table(bank_data)
        
        # Skip empty banks
        if all(np.sum(tile) == 0 for tile in tiles):
            continue
        
        analysis = analyze_bank_contents(tiles)
        bank_info = {
            "offset": offset,
            "analysis": analysis,
            "likely_ui_or_text": analysis["likely_text"] or analysis["likely_ui"]
        }
        
        # Save an image of this bank
        output_file = os.path.join(output_dir, f"bank_{offset:06x}.png")
        save_pattern_table_as_image(tiles, output_file)
        bank_info["image_path"] = output_file
        
        potential_banks.append(bank_info)
        
        print(f"Bank at 0x{offset:06X}:")
        print(f"  Likely contains text: {analysis['likely_text']}")
        print(f"  Likely contains UI elements: {analysis['likely_ui']}")
        print(f"  Confidence: {analysis['confidence']:.2f}%")
        print(f"  Saved to: {output_file}")
        print()
    
    # Sort banks by likelihood of containing UI/text
    potential_banks.sort(key=lambda b: b["analysis"]["confidence"], reverse=True)
    
    # Generate a report
    report_path = os.path.join(output_dir, "bank_analysis_report.txt")
    with open(report_path, 'w') as f:
        f.write("Arkista's Ring - CHR Bank Analysis Report\n")
        f.write("======================================\n\n")
        
        f.write("Banks likely containing UI or text elements:\n")
        f.write("--------------------------------------------\n")
        for bank in [b for b in potential_banks if b["likely_ui_or_text"]]:
            f.write(f"Bank at 0x{bank['offset']:06X}:\n")
            f.write(f"  Text probability: {bank['analysis']['sparse_percent']:.2f}%\n")
            f.write(f"  UI probability: {bank['analysis']['repetitive_percent']:.2f}%\n")
            f.write(f"  Overall confidence: {bank['analysis']['confidence']:.2f}%\n")
            f.write(f"  Image: {os.path.basename(bank['image_path'])}\n\n")
        
        f.write("\nOther potential CHR banks:\n")
        f.write("-------------------------\n")
        for bank in [b for b in potential_banks if not b["likely_ui_or_text"]]:
            f.write(f"Bank at 0x{bank['offset']:06X}:\n")
            f.write(f"  Text probability: {bank['analysis']['sparse_percent']:.2f}%\n")
            f.write(f"  UI probability: {bank['analysis']['repetitive_percent']:.2f}%\n")
            f.write(f"  Image: {os.path.basename(bank['image_path'])}\n\n")
    
    print(f"Analysis report saved to: {report_path}")
    return potential_banks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find and analyze CHR banks in Arkista's Ring ROM")
    parser.add_argument("rom_path", help="Path to the Arkista's Ring ROM file")
    parser.add_argument("--output-dir", default="extracted_banks", help="Directory to save extracted banks")
    
    args = parser.parse_args()
    find_chr_banks(args.rom_path, args.output_dir)
