#include "graphics.h"

// Wait for vertical blank
void ppu_wait_vblank(void) {
    // Wait for vblank bit to be set
    while ((PPU_STATUS & 0x80) == 0);
}

// Initialize the PPU
void ppu_init(void) {
    // Disable rendering
    PPU_CTRL = 0x00;
    PPU_MASK = 0x00;
    
    // Wait for PPU to stabilize
    ppu_wait_vblank();
    ppu_wait_vblank();
}

// Update the PPU state at the end of a frame
void ppu_update(void) {
    // Reset scroll position
    PPU_SCROLL = 0;
    PPU_SCROLL = 0;
    
    // Update sprite data using OAM DMA
    OAM_DMA = 0x02;  // Copy from 0x0200-0x02FF
}

// Set up the NES color palette
void set_palette(void) {
    unsigned char i;
    
    // Set PPU address to palette memory
    PPU_ADDRESS = 0x3F;
    PPU_ADDRESS = 0x00;
    
    // Background palette (4 sets of 4 colors)
    // Palette 0: Default UI/text
    PPU_DATA = COLOR_BLACK;  // Background color
    PPU_DATA = COLOR_WHITE;  // Text color
    PPU_DATA = COLOR_BLUE;   // Highlight
    PPU_DATA = COLOR_RED;    // Accent
    
    // Palette 1: Dungeon walls/floors
    PPU_DATA = COLOR_BLACK;  // Background
    PPU_DATA = COLOR_BROWN;  // Walls
    PPU_DATA = COLOR_GREEN;  // Floors
    PPU_DATA = COLOR_YELLOW; // Doors
    
    // Palette 2: Player character
    PPU_DATA = COLOR_BLACK;  // Background
    PPU_DATA = COLOR_BLUE;   // Main color
    PPU_DATA = COLOR_WHITE;  // Highlight
    PPU_DATA = COLOR_RED;    // Accent
    
    // Palette 3: Items
    PPU_DATA = COLOR_BLACK;  // Background
    PPU_DATA = COLOR_YELLOW; // Treasure
    PPU_DATA = COLOR_PURPLE; // Magic items
    PPU_DATA = COLOR_CYAN;   // Special items
    
    // Sprite palette (4 sets of 4 colors)
    // Similar to background but for sprites
    for (i = 0; i < 16; i++) {
        if (i % 4 == 0) {
            PPU_DATA = COLOR_BLACK;  // Transparent color
        } else if (i < 4) {
            PPU_DATA = COLOR_WHITE;  // Player colors
        } else if (i < 8) {
            PPU_DATA = COLOR_RED;    // Enemy colors
        } else if (i < 12) {
            PPU_DATA = COLOR_YELLOW; // Item colors
        } else {
            PPU_DATA = COLOR_CYAN;   // Special effect colors
        }
    }
}

// Clear the entire screen
void clear_screen(void) {
    unsigned int i;
    
    // Set PPU address to beginning of nametable 0
    PPU_ADDRESS = 0x20;
    PPU_ADDRESS = 0x00;
    
    // Fill with empty tiles
    for (i = 0; i < 0x3C0; i++) {
        PPU_DATA = 0;  // Empty tile
    }
    
    // Clear attribute table
    for (i = 0; i < 0x40; i++) {
        PPU_DATA = 0;
    }
}

// Draw a tile at a specific position on the screen
void draw_tile(unsigned char x, unsigned char y, unsigned char tile) {
    unsigned int addr = 0x2000 + (y * 32) + x;
    
    // Set PPU address
    PPU_ADDRESS = addr >> 8;
    PPU_ADDRESS = addr & 0xFF;
    
    // Write the tile
    PPU_DATA = tile;
}

// Draw a text string at a specific position
void draw_string(const char* str, unsigned char x, unsigned char y) {
    unsigned int addr = 0x2000 + (y * 32) + x;
    const char* ptr = str;
    
    // Set PPU address
    PPU_ADDRESS = addr >> 8;
    PPU_ADDRESS = addr & 0xFF;
    
    // Write each character
    while (*ptr) {
        // Convert ASCII to tile index (assuming ASCII chars start at tile 32)
        PPU_DATA = *ptr - 32;
        ptr++;
    }
}

// Prepare sprite data for rendering
void update_sprites(void) {
    // Clear OAM buffer
    unsigned char i;
    for (i = 0; i < 256; i++) {
        OAM_BUF[i] = 0xFF;  // Move sprites off-screen
    }
    
    // This would be expanded to update sprite positions based on game state
    // For now, just a placeholder
}

// Load background tiles into the pattern table
void load_background_tiles(void) {
    // This would load tile data into the PPU
    // For now, we'll rely on the chars.s file that contains the character set
    
    // Note: In a full implementation, you would extract tiles from Arkista's Ring
    // and load them here
}

// Draw the current dungeon level
void draw_dungeon(Level* level) {
    unsigned char x, y;
    unsigned char tile_index;
    
    // Loop through each tile position
    for (y = 0; y < SCREEN_HEIGHT; y++) {
        for (x = 0; x < SCREEN_WIDTH; x++) {
            // Get the tile type at this position
            tile_index = level->tiles[y * SCREEN_WIDTH + x];
            
            // Convert game tile type to sprite index
            switch (tile_index) {
                case TILE_WALL:
                    draw_tile(x, y, SPRITE_WALL);
                    break;
                case TILE_FLOOR:
                    draw_tile(x, y, SPRITE_FLOOR);
                    break;
                case TILE_DOOR:
                    draw_tile(x, y, SPRITE_DOOR);
                    break;
                case TILE_STAIRS:
                    draw_tile(x, y, SPRITE_STAIRS);
                    break;
                default:
                    draw_tile(x, y, 0);  // Empty
                    break;
            }
        }
    }
    
    // Set attributes for proper coloring
    // This is a placeholder - would need to be expanded
}
