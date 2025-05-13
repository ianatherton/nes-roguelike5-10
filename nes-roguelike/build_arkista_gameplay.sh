#!/bin/bash
set -e

# Script to build the Arkista's Ring gameplay demo ROM

# Ensure output directories exist
mkdir -p build
mkdir -p roms

# Create the NES header file
echo "Creating NES header file..."
cat > build/arkista_gameplay_header.s << EOF
.segment "HEADER"
.byte "NES", \$1a
.byte 2               ; 2 * 16KB PRG ROM
.byte 1               ; 1 * 8KB CHR ROM
.byte \$01, \$00        ; mapper 0, vertical mirroring
EOF

# Compile the source code
echo "Assembling files..."
ca65 -t nes src/arkista_gameplay_demo.s -o build/arkista_gameplay_demo.o
ca65 -t nes build/arkista_gameplay_header.s -o build/arkista_gameplay_header.o

# Link everything together
echo "Linking..."
ld65 -o roms/arkista_gameplay_demo.nes \
    build/arkista_gameplay_demo.o \
    build/arkista_gameplay_header.o \
    -C nes.cfg

echo "Build complete! ROM is at roms/arkista_gameplay_demo.nes"
