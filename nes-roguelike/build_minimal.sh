#!/bin/bash
set -e

# Ensure output directories exist
mkdir -p roms

# Assemble the minimal NES example
echo "Assembling minimal NES example..."
ca65 -t nes minimal_nes.s -o minimal_nes.o

# Link the example
echo "Linking..."
ld65 -t nes -o roms/minimal_nes.nes minimal_nes.o

echo "Build complete! ROM is at roms/minimal_nes.nes"
