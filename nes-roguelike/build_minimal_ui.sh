#!/bin/bash
set -e

# Script to build the minimal Arkista-style UI demo ROM

# Ensure output directories exist
mkdir -p roms

# Assemble our minimal demo
echo "Assembling minimal UI demo..."
ca65 -t nes arkista_minimal.s -o arkista_minimal.o

# Link everything together
echo "Linking..."
ld65 -o roms/arkista_minimal.nes \
    arkista_minimal.o \
    -C nes-simple.cfg

echo "Build complete! ROM is at roms/arkista_minimal.nes"
