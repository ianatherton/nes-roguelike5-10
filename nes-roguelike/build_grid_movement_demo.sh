#!/bin/bash
set -e

# Build script for the grid movement demo

# Create build directory if it doesn't exist
mkdir -p build

# Assemble the grid movement demo
echo "Assembling grid movement demo..."
ca65 src/grid_movement_demo.s -o build/grid_movement_demo.o

# Link the object file to create the NES ROM
echo "Linking to create NES ROM..."
ld65 -o build/grid_movement_demo.nes -C nes.cfg build/grid_movement_demo.o

echo "Build complete! ROM is at build/grid_movement_demo.nes"
echo "Run with: fceux build/grid_movement_demo.nes"
