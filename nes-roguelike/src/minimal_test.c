/**
 * Minimal NES Test ROM
 * Based on example from CC65 documentation
 */

// NES hardware registers
#define PPU_CTRL      (*(unsigned char*)0x2000)
#define PPU_MASK      (*(unsigned char*)0x2001)
#define PPU_STATUS    (*(unsigned char*)0x2002)
#define PPU_SCROLL    (*(unsigned char*)0x2005)
#define PPU_ADDRESS   (*(unsigned char*)0x2006)
#define PPU_DATA      (*(unsigned char*)0x2007)

// Basic colors
#define COLOR_BLACK    0x0F
#define COLOR_WHITE    0x30
#define COLOR_RED      0x16

// Wait for vertical blank
void wait_vblank(void) {
    while ((PPU_STATUS & 0x80) == 0);
}

// Write a text string to the screen
void write_text(const char* text, unsigned char x, unsigned char y) {
    unsigned int addr = 0x2000 + (y * 32) + x;
    unsigned char i = 0;
    
    PPU_ADDRESS = (addr >> 8) & 0xFF;
    PPU_ADDRESS = addr & 0xFF;
    
    while (text[i]) {
        PPU_DATA = text[i] - 32;  // Convert ASCII to tile index
        ++i;
    }
}

// Game entry point
void main(void) {
    // Disable rendering
    PPU_CTRL = 0;
    PPU_MASK = 0;
    
    // Wait for vblank
    wait_vblank();
    wait_vblank();
    
    // Clear the screen
    PPU_ADDRESS = 0x20;
    PPU_ADDRESS = 0x00;
    
    {
        unsigned int i;
        for (i = 0; i < 0x400; i++) {
            PPU_DATA = 0;
        }
    }
    
    // Set up a simple palette
    PPU_ADDRESS = 0x3F;
    PPU_ADDRESS = 0x00;
    PPU_DATA = COLOR_BLACK;
    PPU_DATA = COLOR_WHITE;
    PPU_DATA = COLOR_RED;
    
    // Write text
    write_text("CRAVEN CAVERNS", 9, 10);
    write_text("TEST ROM", 11, 12);
    
    // Enable rendering
    PPU_CTRL = 0x90;  // Enable NMI, use first pattern table
    PPU_MASK = 0x1E;  // Enable sprites and background
    
    // Reset scroll position
    PPU_SCROLL = 0;
    PPU_SCROLL = 0;
    
    // Loop forever
    while (1) {
        // Just wait for the next frame
        wait_vblank();
        
        // Reset scroll position each frame
        PPU_SCROLL = 0;
        PPU_SCROLL = 0;
    }
}

// NMI handler - called during vblank
void __fastcall__ nmi_handler(void) {
    // Reset scroll position each frame
    PPU_SCROLL = 0;
    PPU_SCROLL = 0;
}

// IRQ handler - not used
void __fastcall__ irq_handler(void) {
    // Not used
}
