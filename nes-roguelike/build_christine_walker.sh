#!/bin/bash
# Build script for Christine Walker demo

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p build/chr

# Convert PNG sprites to CHR format
echo "Converting sprites to CHR format..."
python3 tools/png2chr.py \
    --input_dir ~/.nes_asset_wizard/exports/playertest1/player/christine_sprites/ \
    --output_file build/chr/christine_chr.bin \
    --sprite_mode

# Copy the CHR file to the expected location for the assembler
mkdir -p ~/.nes_asset_wizard/exports/playertest1/player/
cp build/chr/christine_chr.bin ~/.nes_asset_wizard/exports/playertest1/player/

# Assemble the ROM
echo "Building Christine Walker ROM..."
ca65 src/christine_walker.s -o build/christine_walker.o
ld65 -o build/christine_walker.nes -C nes.cfg build/christine_walker.o

echo "Done! ROM file is at build/christine_walker.nes"
