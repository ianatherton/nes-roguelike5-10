/**
 * Craven Caverns - NES Roguelike
 * Based on visual assets from Arkista's Ring and gameplay mechanics from Fatal Labyrinth
 */

#include <nes.h>
#include <string.h>
#include "game_defs.h"
#include "graphics.h"
#include "dungeon.h"
#include "gameplay.h"

// Game state data
GameState game_state;

// Flag for when a frame is ready to process
static unsigned char frame_ready = 0;

// Main game loop
void main(void) {
    // Initialize PPU
    ppu_init();
    
    // Clear screen
    clear_screen();
    
    // Set up color palettes
    set_palette();
    
    // Initialize game state
    init_game_state(&game_state);
    
    // Load background tiles
    load_background_tiles();
    
    // Initial render
    render_game_state(&game_state);
    
    // Enable rendering and NMI
    PPU_CTRL = 0x90; // Enable NMI, use 8x8 sprites, background pattern table at 0x0000
    PPU_MASK = 0x1E; // Show background and sprites
    
    // Main game loop
    while (1) {
        // Wait for NMI / vblank
        while (!frame_ready) {}
        frame_ready = 0;
        
        // Update sprites for rendering
        update_sprites();
        
        // Game update
        update_game(&game_state);
        
        // Render game state if needed
        if (game_state.state != STATE_PLAYING) {
            // Non-gameplay states need full screen redraws
            render_game_state(&game_state);
        } else {
            // During gameplay, UI updates happen here
            render_ui(&game_state);
        }
    }
}

// NMI (vertical blank) interrupt handler
void __fastcall__ nmi_handler(void) {
    // OAM DMA transfer for sprites
    // Copy sprite data from RAM buffer to PPU OAM
    PPU_OAM_ADDR = 0;
    OAM_DMA = 0x02; // Copy from 0x0200-0x02FF
    
    // Reset scroll and other frame-specific updates
    ppu_update();
    
    // Mark frame as ready for processing
    frame_ready = 1;
}

// IRQ interrupt handler (unused for now)
void __fastcall__ irq_handler(void) {
    // Not used in this simple example
}
