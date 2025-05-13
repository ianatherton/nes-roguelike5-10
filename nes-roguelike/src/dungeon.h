#ifndef DUNGEON_H
#define DUNGEON_H

#include "game_defs.h"

// Constants for dungeon generation
#define MIN_ROOM_WIDTH  4
#define MIN_ROOM_HEIGHT 4
#define MAX_ROOM_WIDTH  8
#define MAX_ROOM_HEIGHT 8
#define MAX_ROOMS      10

// Function prototypes
void init_level(Level* level, unsigned char level_num);
void generate_dungeon(Level* level, unsigned long seed);
void create_room(Level* level, unsigned char x, unsigned char y, unsigned char width, unsigned char height);
void connect_rooms(Level* level);
void place_stairs(Level* level);
void place_entities(GameState* game_state);
void place_items(GameState* game_state);
unsigned char is_walkable(Level* level, unsigned char x, unsigned char y);
unsigned char get_room_at(Level* level, unsigned char x, unsigned char y);

#endif // DUNGEON_H
