#include "dungeon.h"
#include <stdlib.h>

// Simple pseudo-random number generator for NES (limited ROM space)
static unsigned long next_rand = 1;

// Set the random seed
void set_seed(unsigned long seed) {
    next_rand = seed;
}

// Get next random number
unsigned char rand8(void) {
    next_rand = next_rand * 1103515245 + 12345;
    return (unsigned char)(next_rand >> 16) & 0xFF;
}

// Generate a random number in range [min, max]
unsigned char rand_range(unsigned char min, unsigned char max) {
    return min + (rand8() % (max - min + 1));
}

// Initialize a new level
void init_level(Level* level, unsigned char level_num) {
    unsigned char x, y;
    
    // Set level number
    level->level_num = level_num;
    
    // Clear all tiles to empty
    for (y = 0; y < SCREEN_HEIGHT; y++) {
        for (x = 0; x < SCREEN_WIDTH; x++) {
            level->tiles[y * SCREEN_WIDTH + x] = TILE_EMPTY;
        }
    }
    
    // Reset room count
    level->num_rooms = 0;
}

// Generate a new dungeon level
void generate_dungeon(Level* level, unsigned long seed) {
    unsigned char i;
    unsigned char max_attempts = 50;
    unsigned char attempts;
    unsigned char room_x, room_y, room_w, room_h;
    unsigned char overlap;
    
    // Initialize level
    init_level(level, level->level_num);
    
    // Set random seed
    set_seed(seed);
    
    // Create rooms
    attempts = 0;
    while (level->num_rooms < MAX_ROOMS && attempts < max_attempts) {
        // Generate random room dimensions
        room_w = rand_range(MIN_ROOM_WIDTH, MAX_ROOM_WIDTH);
        room_h = rand_range(MIN_ROOM_HEIGHT, MAX_ROOM_HEIGHT);
        
        // Generate random position (ensure room fits on screen)
        room_x = rand_range(1, SCREEN_WIDTH - room_w - 1);
        room_y = rand_range(1, SCREEN_HEIGHT - room_h - 1);
        
        // Check for overlap with existing rooms
        overlap = 0;
        for (i = 0; i < level->num_rooms; i++) {
            if (room_x + room_w + 1 > level->rooms[i].x && 
                room_x < level->rooms[i].x + level->rooms[i].width + 1 &&
                room_y + room_h + 1 > level->rooms[i].y && 
                room_y < level->rooms[i].y + level->rooms[i].height + 1) {
                overlap = 1;
                break;
            }
        }
        
        // If no overlap, create the room
        if (!overlap) {
            create_room(level, room_x, room_y, room_w, room_h);
            
            // Store room in level data
            level->rooms[level->num_rooms].x = room_x;
            level->rooms[level->num_rooms].y = room_y;
            level->rooms[level->num_rooms].width = room_w;
            level->rooms[level->num_rooms].height = room_h;
            level->rooms[level->num_rooms].connected = 0;
            
            level->num_rooms++;
        }
        
        attempts++;
    }
    
    // Connect rooms with corridors
    connect_rooms(level);
    
    // Place stairs to next level
    place_stairs(level);
}

// Create a room at specified position
void create_room(Level* level, unsigned char x, unsigned char y, unsigned char width, unsigned char height) {
    unsigned char i, j;
    
    // Fill room interior with floor tiles
    for (j = y; j < y + height; j++) {
        for (i = x; i < x + width; i++) {
            level->tiles[j * SCREEN_WIDTH + i] = TILE_FLOOR;
        }
    }
    
    // Add walls around the room
    for (i = x - 1; i <= x + width; i++) {
        level->tiles[(y - 1) * SCREEN_WIDTH + i] = TILE_WALL;
        level->tiles[(y + height) * SCREEN_WIDTH + i] = TILE_WALL;
    }
    
    for (j = y; j < y + height; j++) {
        level->tiles[j * SCREEN_WIDTH + x - 1] = TILE_WALL;
        level->tiles[j * SCREEN_WIDTH + x + width] = TILE_WALL;
    }
}

// Connect rooms with corridors
void connect_rooms(Level* level) {
    unsigned char i, j;
    unsigned char start_room, end_room;
    unsigned char start_x, start_y, end_x, end_y;
    unsigned char current_x, current_y;
    
    // Connect each room to the next one
    for (i = 0; i < level->num_rooms - 1; i++) {
        start_room = i;
        end_room = i + 1;
        
        // Mark rooms as connected
        level->rooms[start_room].connected = 1;
        level->rooms[end_room].connected = 1;
        
        // Choose random points in each room
        start_x = rand_range(level->rooms[start_room].x, 
                            level->rooms[start_room].x + level->rooms[start_room].width - 1);
        start_y = rand_range(level->rooms[start_room].y, 
                            level->rooms[start_room].y + level->rooms[start_room].height - 1);
        
        end_x = rand_range(level->rooms[end_room].x, 
                          level->rooms[end_room].x + level->rooms[end_room].width - 1);
        end_y = rand_range(level->rooms[end_room].y, 
                          level->rooms[end_room].y + level->rooms[end_room].height - 1);
        
        // Create corridor using L-shape approach
        current_x = start_x;
        current_y = start_y;
        
        // First move horizontally
        while (current_x != end_x) {
            if (current_x < end_x) {
                current_x++;
            } else {
                current_x--;
            }
            
            // If the current tile is a wall, replace it with a door or floor
            if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_WALL) {
                level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_DOOR;
            } else if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_FLOOR;
                
                // Add walls around the corridor
                if (level->tiles[(current_y - 1) * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                    level->tiles[(current_y - 1) * SCREEN_WIDTH + current_x] = TILE_WALL;
                }
                if (level->tiles[(current_y + 1) * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                    level->tiles[(current_y + 1) * SCREEN_WIDTH + current_x] = TILE_WALL;
                }
            }
        }
        
        // Then move vertically
        while (current_y != end_y) {
            if (current_y < end_y) {
                current_y++;
            } else {
                current_y--;
            }
            
            // If the current tile is a wall, replace it with a door or floor
            if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_WALL) {
                level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_DOOR;
            } else if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_FLOOR;
                
                // Add walls around the corridor
                if (level->tiles[current_y * SCREEN_WIDTH + current_x - 1] == TILE_EMPTY) {
                    level->tiles[current_y * SCREEN_WIDTH + current_x - 1] = TILE_WALL;
                }
                if (level->tiles[current_y * SCREEN_WIDTH + current_x + 1] == TILE_EMPTY) {
                    level->tiles[current_y * SCREEN_WIDTH + current_x + 1] = TILE_WALL;
                }
            }
        }
    }
    
    // Ensure all rooms are connected by joining any unconnected rooms to the nearest connected one
    for (i = 0; i < level->num_rooms; i++) {
        if (!level->rooms[i].connected) {
            // Find the nearest connected room
            unsigned char nearest_room = 0;
            unsigned int min_distance = 0xFFFF;
            unsigned int distance;
            
            for (j = 0; j < level->num_rooms; j++) {
                if (level->rooms[j].connected && i != j) {
                    // Calculate Manhattan distance between room centers
                    unsigned char room_i_center_x = level->rooms[i].x + level->rooms[i].width / 2;
                    unsigned char room_i_center_y = level->rooms[i].y + level->rooms[i].height / 2;
                    unsigned char room_j_center_x = level->rooms[j].x + level->rooms[j].width / 2;
                    unsigned char room_j_center_y = level->rooms[j].y + level->rooms[j].height / 2;
                    
                    distance = abs(room_i_center_x - room_j_center_x) + 
                              abs(room_i_center_y - room_j_center_y);
                    
                    if (distance < min_distance) {
                        min_distance = distance;
                        nearest_room = j;
                    }
                }
            }
            
            // Connect this room to the nearest connected room
            start_room = i;
            end_room = nearest_room;
            
            // Mark room as connected
            level->rooms[start_room].connected = 1;
            
            // Connect the rooms using the same method as above
            start_x = rand_range(level->rooms[start_room].x, 
                                level->rooms[start_room].x + level->rooms[start_room].width - 1);
            start_y = rand_range(level->rooms[start_room].y, 
                                level->rooms[start_room].y + level->rooms[start_room].height - 1);
            
            end_x = rand_range(level->rooms[end_room].x, 
                              level->rooms[end_room].x + level->rooms[end_room].width - 1);
            end_y = rand_range(level->rooms[end_room].y, 
                              level->rooms[end_room].y + level->rooms[end_room].height - 1);
            
            // Create corridor using L-shape approach (similar to above)
            current_x = start_x;
            current_y = start_y;
            
            // First move horizontally
            while (current_x != end_x) {
                if (current_x < end_x) {
                    current_x++;
                } else {
                    current_x--;
                }
                
                // If the current tile is a wall, replace it with a door or floor
                if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_WALL) {
                    level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_DOOR;
                } else if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                    level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_FLOOR;
                    
                    // Add walls around the corridor
                    if (level->tiles[(current_y - 1) * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                        level->tiles[(current_y - 1) * SCREEN_WIDTH + current_x] = TILE_WALL;
                    }
                    if (level->tiles[(current_y + 1) * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                        level->tiles[(current_y + 1) * SCREEN_WIDTH + current_x] = TILE_WALL;
                    }
                }
            }
            
            // Then move vertically
            while (current_y != end_y) {
                if (current_y < end_y) {
                    current_y++;
                } else {
                    current_y--;
                }
                
                // If the current tile is a wall, replace it with a door or floor
                if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_WALL) {
                    level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_DOOR;
                } else if (level->tiles[current_y * SCREEN_WIDTH + current_x] == TILE_EMPTY) {
                    level->tiles[current_y * SCREEN_WIDTH + current_x] = TILE_FLOOR;
                    
                    // Add walls around the corridor
                    if (level->tiles[current_y * SCREEN_WIDTH + current_x - 1] == TILE_EMPTY) {
                        level->tiles[current_y * SCREEN_WIDTH + current_x - 1] = TILE_WALL;
                    }
                    if (level->tiles[current_y * SCREEN_WIDTH + current_x + 1] == TILE_EMPTY) {
                        level->tiles[current_y * SCREEN_WIDTH + current_x + 1] = TILE_WALL;
                    }
                }
            }
        }
    }
}

// Place stairs to the next level
void place_stairs(Level* level) {
    unsigned char room_idx;
    
    // Place stairs in a random room (not the first one)
    if (level->num_rooms > 1) {
        room_idx = rand_range(1, level->num_rooms - 1);
    } else {
        room_idx = 0;
    }
    
    // Place stairs in a random position within the room
    level->stairs_x = rand_range(level->rooms[room_idx].x, 
                               level->rooms[room_idx].x + level->rooms[room_idx].width - 1);
    level->stairs_y = rand_range(level->rooms[room_idx].y, 
                               level->rooms[room_idx].y + level->rooms[room_idx].height - 1);
    
    // Set stairs tile
    level->tiles[level->stairs_y * SCREEN_WIDTH + level->stairs_x] = TILE_STAIRS;
}

// Place entities (player and enemies) in the level
void place_entities(GameState* game_state) {
    unsigned char i;
    unsigned char room_idx;
    unsigned char pos_x, pos_y;
    
    // Place player in the first room
    room_idx = 0;
    
    // Find a random position in the room for the player
    pos_x = rand_range(game_state->current_level.rooms[room_idx].x, 
                      game_state->current_level.rooms[room_idx].x + game_state->current_level.rooms[room_idx].width - 1);
    pos_y = rand_range(game_state->current_level.rooms[room_idx].y, 
                      game_state->current_level.rooms[room_idx].y + game_state->current_level.rooms[room_idx].height - 1);
    
    // Set player position
    game_state->player.pos.x = pos_x;
    game_state->player.pos.y = pos_y;
    
    // Place enemies in random rooms (not the first one)
    for (i = 0; i < MAX_ENTITIES; i++) {
        // Determine how many enemies to spawn based on level number
        if (i < game_state->current_level.level_num + 2) {
            // Choose a random room (not the first one with the player)
            if (game_state->current_level.num_rooms > 1) {
                room_idx = rand_range(1, game_state->current_level.num_rooms - 1);
            } else {
                // If only one room, place enemies far from player
                room_idx = 0;
            }
            
            // Find a random position in the room
            pos_x = rand_range(game_state->current_level.rooms[room_idx].x, 
                              game_state->current_level.rooms[room_idx].x + game_state->current_level.rooms[room_idx].width - 1);
            pos_y = rand_range(game_state->current_level.rooms[room_idx].y, 
                              game_state->current_level.rooms[room_idx].y + game_state->current_level.rooms[room_idx].height - 1);
            
            // Make sure not to place enemy on top of player or stairs
            if ((pos_x == game_state->player.pos.x && pos_y == game_state->player.pos.y) ||
                (pos_x == game_state->current_level.stairs_x && pos_y == game_state->current_level.stairs_y)) {
                // Try a different position
                continue;
            }
            
            // Set enemy properties
            game_state->entities[i].type = ENTITY_ENEMY;
            game_state->entities[i].active = 1;
            game_state->entities[i].pos.x = pos_x;
            game_state->entities[i].pos.y = pos_y;
            game_state->entities[i].sprite_idx = 4 + (i % 4); // Cycle through enemy sprites (4-7)
            
            // Set enemy stats based on level
            game_state->entities[i].stats.hp = 3 + (game_state->current_level.level_num / 3);
            game_state->entities[i].stats.attack = 1 + (game_state->current_level.level_num / 4);
            game_state->entities[i].stats.defense = game_state->current_level.level_num / 5;
        } else {
            // No more enemies to place
            game_state->entities[i].active = 0;
        }
    }
}

// Place items in the level
void place_items(GameState* game_state) {
    unsigned char i;
    unsigned char room_idx;
    unsigned char pos_x, pos_y;
    unsigned char item_type;
    
    // Determine how many items to place based on level
    unsigned char num_items = 3 + (game_state->current_level.level_num / 2);
    
    // Cap at maximum items
    if (num_items > MAX_ITEMS) {
        num_items = MAX_ITEMS;
    }
    
    // Place items in random rooms
    for (i = 0; i < num_items; i++) {
        // Choose a random room
        room_idx = rand_range(0, game_state->current_level.num_rooms - 1);
        
        // Find a random position in the room
        pos_x = rand_range(game_state->current_level.rooms[room_idx].x, 
                          game_state->current_level.rooms[room_idx].x + game_state->current_level.rooms[room_idx].width - 1);
        pos_y = rand_range(game_state->current_level.rooms[room_idx].y, 
                          game_state->current_level.rooms[room_idx].y + game_state->current_level.rooms[room_idx].height - 1);
        
        // Make sure not to place item on top of player, enemy, or stairs
        if ((pos_x == game_state->player.pos.x && pos_y == game_state->player.pos.y) ||
            (pos_x == game_state->current_level.stairs_x && pos_y == game_state->current_level.stairs_y)) {
            // Try a different position
            i--;
            continue;
        }
        
        // Check for entities at this position
        {
            unsigned char j;
            unsigned char entity_present = 0;
            for (j = 0; j < MAX_ENTITIES; j++) {
                if (game_state->entities[j].active && 
                    game_state->entities[j].pos.x == pos_x && 
                    game_state->entities[j].pos.y == pos_y) {
                    entity_present = 1;
                    break;
                }
            }
            
            if (entity_present) {
                // Try a different position
                i--;
                continue;
            }
        }
        
        // Also check for other items
        {
            unsigned char j;
            unsigned char item_present = 0;
            for (j = 0; j < i; j++) {
                if (game_state->items[j].in_world && 
                    game_state->items[j].pos.x == pos_x && 
                    game_state->items[j].pos.y == pos_y) {
                    item_present = 1;
                    break;
                }
            }
            
            if (item_present) {
                // Try a different position
                i--;
                continue;
            }
        }
        
        // Randomize item type
        item_type = rand_range(0, 5);
        
        // Set item properties
        game_state->items[i].type = item_type;
        game_state->items[i].subtype = rand_range(0, 3); // Random subtype
        game_state->items[i].value = 1 + (game_state->current_level.level_num / 3); // Value increases with level
        game_state->items[i].pos.x = pos_x;
        game_state->items[i].pos.y = pos_y;
        game_state->items[i].in_world = 1;
        game_state->items[i].sprite_idx = 16 + item_type; // Item sprites start at 16
        
        // Set default item names (would be expanded in a full game)
        switch (item_type) {
            case ITEM_WEAPON:
                game_state->items[i].name[0] = 'S';
                game_state->items[i].name[1] = 'w';
                game_state->items[i].name[2] = 'o';
                game_state->items[i].name[3] = 'r';
                game_state->items[i].name[4] = 'd';
                game_state->items[i].name[5] = '\0';
                break;
            case ITEM_ARMOR:
                game_state->items[i].name[0] = 'A';
                game_state->items[i].name[1] = 'r';
                game_state->items[i].name[2] = 'm';
                game_state->items[i].name[3] = 'o';
                game_state->items[i].name[4] = 'r';
                game_state->items[i].name[5] = '\0';
                break;
            case ITEM_POTION:
                game_state->items[i].name[0] = 'P';
                game_state->items[i].name[1] = 'o';
                game_state->items[i].name[2] = 't';
                game_state->items[i].name[3] = 'i';
                game_state->items[i].name[4] = 'o';
                game_state->items[i].name[5] = 'n';
                game_state->items[i].name[6] = '\0';
                break;
            case ITEM_SCROLL:
                game_state->items[i].name[0] = 'S';
                game_state->items[i].name[1] = 'c';
                game_state->items[i].name[2] = 'r';
                game_state->items[i].name[3] = 'o';
                game_state->items[i].name[4] = 'l';
                game_state->items[i].name[5] = 'l';
                game_state->items[i].name[6] = '\0';
                break;
            case ITEM_FOOD:
                game_state->items[i].name[0] = 'F';
                game_state->items[i].name[1] = 'o';
                game_state->items[i].name[2] = 'o';
                game_state->items[i].name[3] = 'd';
                game_state->items[i].name[4] = '\0';
                break;
            case ITEM_KEY:
                game_state->items[i].name[0] = 'K';
                game_state->items[i].name[1] = 'e';
                game_state->items[i].name[2] = 'y';
                game_state->items[i].name[3] = '\0';
                break;
        }
    }
    
    // Clear remaining items
    for (; i < MAX_ITEMS; i++) {
        game_state->items[i].in_world = 0;
    }
}

// Check if a tile is walkable
unsigned char is_walkable(Level* level, unsigned char x, unsigned char y) {
    // Check bounds
    if (x >= SCREEN_WIDTH || y >= SCREEN_HEIGHT) {
        return 0;
    }
    
    // Check tile type
    unsigned char tile = level->tiles[y * SCREEN_WIDTH + x];
    return (tile == TILE_FLOOR || tile == TILE_DOOR || tile == TILE_STAIRS);
}

// Get the room index at a given position, or -1 if not in a room
unsigned char get_room_at(Level* level, unsigned char x, unsigned char y) {
    unsigned char i;
    
    for (i = 0; i < level->num_rooms; i++) {
        if (x >= level->rooms[i].x && x < level->rooms[i].x + level->rooms[i].width &&
            y >= level->rooms[i].y && y < level->rooms[i].y + level->rooms[i].height) {
            return i;
        }
    }
    
    return 0xFF; // Not in any room
}
