#!/bin/bash
set -e

# Ensure output directories exist
mkdir -p roms

# Assemble the hello world NES example
echo "Assembling Hello World NES example..."
ca65 -t nes hello_nes.s -o hello_nes.o

# Link the example
echo "Linking..."
ld65 -t nes -o roms/hello_nes.nes hello_nes.o

echo "Build complete! ROM is at roms/hello_nes.nes"
