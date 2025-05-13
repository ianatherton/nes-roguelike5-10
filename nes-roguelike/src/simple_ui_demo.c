#include "nes.h"

// Simple demo state
typedef enum {
    TITLE_SCREEN,
    MAIN_MENU,
    GAME_SCREEN
} GameState;

// Game state
GameState current_state = TITLE_SCREEN;
unsigned char frame_count = 0;
unsigned char selection = 0;

// Menu definitions
const char* menu_items[] = {
    "START GAME",
    "OPTIONS",
    "STATS",
    "INVENTORY",
    "EXIT"
};
#define NUM_MENU_ITEMS 5

// Tile constants
#define TILE_EMPTY      0x00
#define TILE_FULL       0x01
#define TILE_BOX_TL     0x0A
#define TILE_BOX_TR     0x0B
#define TILE_BOX_BL     0x0C
#define TILE_BOX_BR     0x0D
#define TILE_BOX_H      0x0E
#define TILE_BOX_V      0x0F

// PPU access functions
void ppu_wait_vblank(void) {
    // Wait for vblank bit to be set
    while ((PPU_STATUS & 0x80) == 0);
}

void ppu_reset_scroll(void) {
    PPU_SCROLL = 0;
    PPU_SCROLL = 0;
}

// Write a byte to PPU memory
void ppu_write(unsigned int addr, unsigned char value) {
    PPU_ADDRESS = (unsigned char)(addr >> 8);
    PPU_ADDRESS = (unsigned char)(addr & 0xFF);
    PPU_DATA = value;
}

// Write a string to PPU memory (nametable)
void write_string(unsigned int addr, const char* str) {
    PPU_ADDRESS = (unsigned char)(addr >> 8);
    PPU_ADDRESS = (unsigned char)(addr & 0xFF);
    
    while (*str) {
        // Convert ASCII to tile index (assuming ASCII chars start at tile 32)
        PPU_DATA = *str - 32 + 32; // -32 for ASCII, +32 for tile offset
        str++;
    }
}

// Write a centered string to PPU memory
void write_centered_string(unsigned char y, const char* str) {
    unsigned char len = 0;
    const char* s = str;
    
    // Calculate string length
    while (*s) {
        len++;
        s++;
    }
    
    // Center the string (assuming 32 tile width)
    unsigned char x = (32 - len) / 2;
    
    // Calculate nametable address
    unsigned int addr = 0x2000 + (y * 32) + x;
    
    // Write the string
    write_string(addr, str);
}

// Draw a box on the screen
void draw_box(unsigned char x, unsigned char y, unsigned char width, unsigned char height) {
    unsigned int addr;
    unsigned char i;
    
    // Top row
    addr = 0x2000 + (y * 32) + x;
    ppu_write(addr, TILE_BOX_TL);
    for (i = 1; i < width - 1; i++) {
        ppu_write(addr + i, TILE_BOX_H);
    }
    ppu_write(addr + width - 1, TILE_BOX_TR);
    
    // Middle rows
    for (i = 1; i < height - 1; i++) {
        addr = 0x2000 + ((y + i) * 32) + x;
        ppu_write(addr, TILE_BOX_V);
        ppu_write(addr + width - 1, TILE_BOX_V);
    }
    
    // Bottom row
    addr = 0x2000 + ((y + height - 1) * 32) + x;
    ppu_write(addr, TILE_BOX_BL);
    for (i = 1; i < width - 1; i++) {
        ppu_write(addr + i, TILE_BOX_H);
    }
    ppu_write(addr + width - 1, TILE_BOX_BR);
}

// Draw the title screen
void draw_title_screen(void) {
    // Clear screen first
    unsigned int i;
    PPU_ADDRESS = 0x20;
    PPU_ADDRESS = 0x00;
    for (i = 0; i < 0x400; i++) {
        PPU_DATA = TILE_EMPTY;
    }
    
    // Draw title
    write_centered_string(8, "CRAVEN CAVERNS");
    write_centered_string(10, "NES ROGUELIKE");
    
    // Draw subtitle
    write_centered_string(14, "PRESS START");
    
    // Draw a decorative box around the title
    draw_box(8, 6, 16, 11);
}

// Draw the main menu
void draw_main_menu(void) {
    // Clear screen first
    unsigned int i;
    PPU_ADDRESS = 0x20;
    PPU_ADDRESS = 0x00;
    for (i = 0; i < 0x400; i++) {
        PPU_DATA = TILE_EMPTY;
    }
    
    // Draw menu title
    write_centered_string(4, "MAIN MENU");
    
    // Draw menu box
    draw_box(9, 6, 14, 12);
    
    // Draw menu items
    for (i = 0; i < NUM_MENU_ITEMS; i++) {
        // Draw selector if this is the current selection
        unsigned int addr = 0x2000 + ((8 + i) * 32) + 11;
        if (i == selection) {
            ppu_write(addr - 1, '>');
        }
        
        // Draw menu item text
        write_string(addr, menu_items[i]);
    }
}

// Read controller input
unsigned char read_controller(void) {
    unsigned char result = 0;
    unsigned char i;
    
    // Strobe controller
    (*(volatile unsigned char*)0x4016) = 1;
    (*(volatile unsigned char*)0x4016) = 0;
    
    // Read 8 bits
    for (i = 0; i < 8; i++) {
        result |= ((*(volatile unsigned char*)0x4016) & 1) << i;
    }
    
    return result;
}

// Main function
void main(void) {
    unsigned char controller_state = 0;
    unsigned char prev_controller_state = 0;

    // Wait for PPU to stabilize
    ppu_wait_vblank();
    ppu_wait_vblank();
    
    // Set up palette (simple grayscale)
    PPU_ADDRESS = 0x3F;
    PPU_ADDRESS = 0x00;
    
    // Background palette
    PPU_DATA = 0x0F; // Black
    PPU_DATA = 0x30; // White
    PPU_DATA = 0x10; // Gray
    PPU_DATA = 0x00; // Black
    
    // Rest of palette (simple)
    unsigned char i;
    for (i = 1; i < 8; i++) {
        PPU_DATA = 0x0F; // Black
        PPU_DATA = 0x30; // White
        PPU_DATA = 0x10; // Gray
        PPU_DATA = 0x00; // Black
    }
    
    // Initial screen
    draw_title_screen();
    
    // Enable rendering
    PPU_CTRL = 0x90; // Enable NMI, use 8x8 sprites, background pattern table at 0x0000
    PPU_MASK = 0x1E; // Show background and sprites
    
    // Main game loop
    while (1) {
        // Wait for next frame
        ppu_wait_vblank();
        
        // Read controller
        prev_controller_state = controller_state;
        controller_state = read_controller();
        
        // Handle input based on current state
        switch (current_state) {
            case TITLE_SCREEN:
                // Press Start to go to main menu
                if ((controller_state & 0x10) && !(prev_controller_state & 0x10)) {
                    current_state = MAIN_MENU;
                    draw_main_menu();
                }
                break;
                
            case MAIN_MENU:
                // Handle menu navigation
                if ((controller_state & 0x08) && !(prev_controller_state & 0x08)) {
                    // Up pressed
                    if (selection > 0) {
                        selection--;
                        draw_main_menu();
                    }
                }
                else if ((controller_state & 0x04) && !(prev_controller_state & 0x04)) {
                    // Down pressed
                    if (selection < NUM_MENU_ITEMS - 1) {
                        selection++;
                        draw_main_menu();
                    }
                }
                else if ((controller_state & 0x10) && !(prev_controller_state & 0x10)) {
                    // Start pressed - select current item
                    if (selection == 0) {
                        // Start game
                        current_state = GAME_SCREEN;
                        // Draw game screen here
                    }
                    else if (selection == NUM_MENU_ITEMS - 1) {
                        // Exit back to title
                        current_state = TITLE_SCREEN;
                        draw_title_screen();
                    }
                }
                break;
                
            case GAME_SCREEN:
                // Press B to go back to menu
                if ((controller_state & 0x40) && !(prev_controller_state & 0x40)) {
                    current_state = MAIN_MENU;
                    draw_main_menu();
                }
                break;
        }
        
        // Reset scroll position
        ppu_reset_scroll();
        
        // Increment frame counter
        frame_count++;
    }
}
