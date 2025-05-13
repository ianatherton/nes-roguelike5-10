#!/bin/bash
set -e

# Simple build script for our basic Arkista-style UI demo

# Ensure output directories exist
mkdir -p roms

# Assemble our basic UI demo
echo "Assembling basic UI demo..."
ca65 -t nes basic_ui_demo.s -o basic_ui_demo.o

# Link the demo
echo "Linking..."
ld65 -t nes -o roms/basic_ui_demo.nes basic_ui_demo.o

echo "Build complete! ROM is at roms/basic_ui_demo.nes"
