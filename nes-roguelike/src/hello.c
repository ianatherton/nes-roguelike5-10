#include <stdlib.h>
#include <string.h>

// NES hardware registers
#define PPU_CTRL      (*(volatile unsigned char*)0x2000)
#define PPU_MASK      (*(volatile unsigned char*)0x2001)
#define PPU_STATUS    (*(volatile unsigned char*)0x2002)
#define PPU_OAM_ADDR  (*(volatile unsigned char*)0x2003)
#define PPU_OAM_DATA  (*(volatile unsigned char*)0x2004)
#define PPU_SCROLL    (*(volatile unsigned char*)0x2005)
#define PPU_ADDR      (*(volatile unsigned char*)0x2006)
#define PPU_DATA      (*(volatile unsigned char*)0x2007)
#define OAM_DMA       (*(volatile unsigned char*)0x4014)

// Character data
extern const char TEXT_CHARS[];

// Function to wait for vblank
void wait_for_vblank(void) {
    // Wait for vblank flag to be set
    while (!(PPU_STATUS & 0x80));
}

// Write a string to the nametable
void write_string(unsigned int addr, const char* str) {
    PPU_ADDR = (addr >> 8) & 0xFF;
    PPU_ADDR = addr & 0xFF;
    
    while (*str) {
        PPU_DATA = *str++;
    }
}

// Write a string to the nametable with offset for ASCII values
void write_text(unsigned int addr, const char* str) {
    PPU_ADDR = (addr >> 8) & 0xFF;
    PPU_ADDR = addr & 0xFF;
    
    while (*str) {
        // Convert ASCII to CHR tile index (assuming standard ASCII layout)
        PPU_DATA = *str - 0x20; // ASCII space is 0x20, first tile is 0
        str++;
    }
}

// Main entry point
void main(void) {
    char i;
    
    // Initialize PPU
    PPU_CTRL = 0;
    PPU_MASK = 0;
    
    // Wait for PPU to stabilize
    wait_for_vblank();
    wait_for_vblank();
    
    // Clear the screen (first nametable)
    PPU_ADDR = 0x20;
    PPU_ADDR = 0x00;
    
    for (i = 0; i < 30; ++i) {
        unsigned char x;
        for (x = 0; x < 32; ++x) {
            PPU_DATA = 0; // Empty tile
        }
    }
    
    // Set up palette
    PPU_ADDR = 0x3F;
    PPU_ADDR = 0x00;
    
    // Background palette (black, white, red, green)
    PPU_DATA = 0x0F; // Black
    PPU_DATA = 0x30; // White
    PPU_DATA = 0x16; // Red
    PPU_DATA = 0x1A; // Green
    
    // Write text to the screen
    write_text(0x2000 + 11*32 + 10, "CRAVEN CAVERNS");
    write_text(0x2000 + 13*32 + 11, "NES ROGUELIKE");
    write_text(0x2000 + 16*32 + 11, "PRESS START");
    
    // Reset scroll position
    PPU_SCROLL = 0;
    PPU_SCROLL = 0;
    
    // Enable rendering
    PPU_CTRL = 0x90; // Enable NMI, pattern table 0
    PPU_MASK = 0x1E; // Show sprites and background
    
    // Main loop
    while (1) {
        // Wait for next frame
        wait_for_vblank();
        
        // Reset scroll position
        PPU_SCROLL = 0;
        PPU_SCROLL = 0;
    }
}

// Blank interrupt handlers
void __fastcall__ nmi_handler(void) {
    // Reset scroll position
    PPU_SCROLL = 0;
    PPU_SCROLL = 0;
}

void __fastcall__ irq_handler(void) {
    // Not used
}
