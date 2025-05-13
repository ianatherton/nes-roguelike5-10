#include <nes.h>
#include <string.h>

// Basic colors
#define COLOR_BLACK     0x0F
#define COLOR_WHITE     0x30
#define COLOR_RED       0x16
#define COLOR_GREEN     0x1A
#define COLOR_BLUE      0x12

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
}

// Simple function to write text to the screen
void write_text(const char* text, unsigned char x, unsigned char y) {
    unsigned int addr = 0x2000 + (y * 32) + x;
    
    // Set the PPU address to write to
    PPU_ADDRESS = addr >> 8;
    PPU_ADDRESS = addr & 0xFF;
    
    // Write the text to the nametable
    while (*text) {
        PPU_DATA = *text - 32; // Convert ASCII to tile index
        text++;
    }
}

// Set up palette
void set_palette(void) {
    PPU_ADDRESS = 0x3F;
    PPU_ADDRESS = 0x00;
    
    // Background palette
    PPU_DATA = COLOR_BLACK;
    PPU_DATA = COLOR_WHITE;
    PPU_DATA = COLOR_RED;
    PPU_DATA = COLOR_GREEN;
    
    // Sprite palette
    PPU_DATA = COLOR_BLACK;
    PPU_DATA = COLOR_BLUE;
    PPU_DATA = COLOR_RED;
    PPU_DATA = COLOR_WHITE;
}

// NMI (vertical blank) interrupt handler
void __fastcall__ nmi_handler(void) {
    // Reset scroll and other frame-specific updates
    ppu_update();
}

// IRQ interrupt handler (unused for now)
void __fastcall__ irq_handler(void) {
    // Not used in this simple example
}

// Main game loop
void main(void) {
    // Initialize PPU
    ppu_init();
    
    // Clear nametable
    PPU_ADDRESS = 0x20;
    PPU_ADDRESS = 0x00;
    {
        unsigned int i;
        for (i = 0; i < 0x400; i++) {
            PPU_DATA = 0;
        }
    }
    
    // Set up palette
    set_palette();
    
    // Write title text
    write_text("CRAVEN CAVERNS", 9, 10);
    write_text("NES ROGUELIKE", 10, 12);
    write_text("TEST ROM", 11, 14);
    write_text("PRESS START", 10, 16);
    
    // Enable rendering
    PPU_CTRL = 0x90; // Enable NMI, use 8x8 sprites, background pattern table at 0x0000
    PPU_MASK = 0x1E; // Show background and sprites
    
    // Main game loop
    while (1) {
        // Wait for next frame
        ppu_wait_vblank();
        
        // Update PPU
        ppu_update();
    }
}
