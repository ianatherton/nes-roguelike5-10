#!/bin/bash
set -e

# Script to build the minimal Arkista's Ring demo ROM

# Ensure output directories exist
mkdir -p build
mkdir -p roms

# Compile the source code
echo "Assembling files..."
ca65 -t nes src/arkista_minimal_demo.s -o build/arkista_minimal_demo.o

# Link everything together
echo "Linking..."
ld65 -o roms/arkista_minimal_demo.nes \
    build/arkista_minimal_demo.o \
    -C nes_minimal.cfg

echo "Build complete! ROM is at roms/arkista_minimal_demo.nes"
