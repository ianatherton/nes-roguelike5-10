#!/bin/bash
# Build script for Arkista's Ring sprite test ROM

mkdir -p build

# Assemble the sprite test ROM
ca65 -t nes src/sprite_test.s -o build/sprite_test.o

# Create a simple linker config file
cat > build/test.cfg << 'EOF'
MEMORY {
    ZP:     start = $00,    size = $0100, type = rw;
    RAM:    start = $0200,  size = $0600, type = rw;
    OAM:    start = $0200,  size = $0100, type = rw;
    HEADER: start = $0000,  size = $0010, type = ro, file = %O, fill = yes;
    PRG:    start = $8000,  size = $8000, type = ro, file = %O, fill = yes;
    CHR:    start = $0000,  size = $2000, type = ro, file = %O, fill = yes;
}

SEGMENTS {
    ZEROPAGE: load = ZP,     type = zp;
    BSS:      load = RAM,    type = bss, define = yes;
    OAM:      load = OAM,    type = bss;
    HEADER:   load = HEADER, type = ro;
    CODE:     load = PRG,    type = ro,  start = $8000;
    CHARS:    load = CHR,    type = ro;
    VECTORS:  load = PRG,    type = ro,  start = $FFFA;
}
EOF

# Link the ROM
ld65 -C build/test.cfg build/sprite_test.o -o build/arkista_sprites.nes

echo "ROM generated at build/arkista_sprites.nes"
echo "Run with: fceux build/arkista_sprites.nes"
