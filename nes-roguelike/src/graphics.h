#ifndef GRAPHICS_H
#define GRAPHICS_H

#include "nes.h"
#include "game_defs.h"

// Color constants for NES palette
#define COLOR_BLACK     0x0F
#define COLOR_WHITE     0x30
#define COLOR_RED       0x16
#define COLOR_GREEN     0x1A
#define COLOR_BLUE      0x12
#define COLOR_BROWN     0x17
#define COLOR_PURPLE    0x14
#define COLOR_CYAN      0x1C
#define COLOR_YELLOW    0x28

// Sprite indices - will be filled with actual data once assets are extracted
#define SPRITE_PLAYER_DOWN      0
#define SPRITE_PLAYER_UP        1
#define SPRITE_PLAYER_RIGHT     2
#define SPRITE_PLAYER_LEFT      3
#define SPRITE_ENEMY_BASE       4  // Enemy sprites 4-15
#define SPRITE_ITEM_BASE        16 // Item sprites 16-31
#define SPRITE_WALL             32
#define SPRITE_FLOOR            33
#define SPRITE_DOOR             34
#define SPRITE_STAIRS           35

// Sprite RAM buffer (located at 0x200-0x2FF)
#define OAM_BUF         ((unsigned char*)0x200)

// Function prototypes
void ppu_wait_vblank(void);
void ppu_init(void);
void ppu_update(void);
void set_palette(void);
void clear_screen(void);
void draw_tile(unsigned char x, unsigned char y, unsigned char tile);
void draw_string(const char* str, unsigned char x, unsigned char y);
void draw_sprites(void);
void update_sprites(void);
void load_background_tiles(void);
void draw_dungeon(Level* level);

#endif // GRAPHICS_H
