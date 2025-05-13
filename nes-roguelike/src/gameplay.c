#include "gameplay.h"
#include "dungeon.h"
#include "graphics.h"
#include <string.h>

// Current controller state
static unsigned char controller_state = 0;
// Previous controller state for edge detection
static unsigned char prev_controller_state = 0;

// Initialize the game state
void init_game_state(GameState* game_state) {
    unsigned char i;
    
    // Set initial game state
    game_state->state = STATE_TITLE;
    
    // Initialize player
    game_state->player.type = ENTITY_PLAYER;
    game_state->player.active = 1;
    game_state->player.sprite_idx = SPRITE_PLAYER_DOWN;
    game_state->player.direction = DIR_DOWN;
    
    // Set player stats
    game_state->player.stats.hp = 10;
    game_state->player.stats.max_hp = 10;
    game_state->player.stats.attack = 2;
    game_state->player.stats.defense = 0;
    game_state->player.stats.level = 1;
    game_state->player.stats.experience = 0;
    game_state->player.stats.hunger = 100;  // Full hunger meter
    
    // Clear entities
    for (i = 0; i < MAX_ENTITIES; i++) {
        game_state->entities[i].active = 0;
    }
    
    // Clear items
    for (i = 0; i < MAX_ITEMS; i++) {
        game_state->items[i].in_world = 0;
    }
    
    // Clear inventory
    for (i = 0; i < MAX_INVENTORY; i++) {
        game_state->inventory[i] = 0xFF;  // 0xFF means empty slot
    }
    
    // Set up first level
    game_state->current_level.level_num = 1;
    game_state->seed = 0x12345678;  // Initial seed
    
    // Generate the first dungeon level
    generate_dungeon(&game_state->current_level, game_state->seed);
    
    // Place entities and items
    place_entities(game_state);
    place_items(game_state);
}

// Read NES controller input
unsigned char read_controller(void) {
    unsigned char i;
    unsigned char result = 0;
    
    // Strobe the controller
    CONTROLLER_1 = 1;
    CONTROLLER_1 = 0;
    
    // Read each button (D0-D7)
    for (i = 0; i < 8; i++) {
        // Shift result right, adding new bit from controller in D7
        result = (result >> 1) | ((CONTROLLER_1 & 1) << 7);
        
        // Due to how the NES controller works, we need to invert the bits
        // so that pressed buttons return 1
        result ^= 0x80;
    }
    
    return result;
}

// Handle player input
void handle_input(GameState* game_state) {
    // Read current controller state
    controller_state = read_controller();
    
    // Edge detection - only trigger once per button press
    unsigned char pressed = controller_state & ~prev_controller_state;
    
    // Update previous state for next frame
    prev_controller_state = controller_state;
    
    if (game_state->state == STATE_TITLE) {
        // Title screen input
        if (pressed & BUTTON_START) {
            // Start new game
            game_state->state = STATE_PLAYING;
        }
    } else if (game_state->state == STATE_PLAYING) {
        // Gameplay input
        
        // Movement
        if (pressed & BUTTON_UP) {
            game_state->player.direction = DIR_UP;
            game_state->player.sprite_idx = SPRITE_PLAYER_UP;
            move_player(game_state, 0, -1);
        } else if (pressed & BUTTON_DOWN) {
            game_state->player.direction = DIR_DOWN;
            game_state->player.sprite_idx = SPRITE_PLAYER_DOWN;
            move_player(game_state, 0, 1);
        } else if (pressed & BUTTON_LEFT) {
            game_state->player.direction = DIR_LEFT;
            game_state->player.sprite_idx = SPRITE_PLAYER_LEFT;
            move_player(game_state, -1, 0);
        } else if (pressed & BUTTON_RIGHT) {
            game_state->player.direction = DIR_RIGHT;
            game_state->player.sprite_idx = SPRITE_PLAYER_RIGHT;
            move_player(game_state, 1, 0);
        }
        
        // Diagonal movement (similar to Fatal Labyrinth's 8-way movement)
        else if (pressed & (BUTTON_UP | BUTTON_RIGHT)) {
            game_state->player.direction = DIR_UPRIGHT;
            game_state->player.sprite_idx = SPRITE_PLAYER_RIGHT;
            move_player(game_state, 1, -1);
        } else if (pressed & (BUTTON_DOWN | BUTTON_RIGHT)) {
            game_state->player.direction = DIR_DOWNRIGHT;
            game_state->player.sprite_idx = SPRITE_PLAYER_RIGHT;
            move_player(game_state, 1, 1);
        } else if (pressed & (BUTTON_DOWN | BUTTON_LEFT)) {
            game_state->player.direction = DIR_DOWNLEFT;
            game_state->player.sprite_idx = SPRITE_PLAYER_LEFT;
            move_player(game_state, -1, 1);
        } else if (pressed & (BUTTON_UP | BUTTON_LEFT)) {
            game_state->player.direction = DIR_UPLEFT;
            game_state->player.sprite_idx = SPRITE_PLAYER_LEFT;
            move_player(game_state, -1, -1);
        }
        
        // A button - interact/pickup
        if (pressed & BUTTON_A) {
            pickup_item(game_state);
        }
        
        // B button - use equipped item
        if (pressed & BUTTON_B) {
            // Use first inventory item as equipped item
            if (game_state->inventory[0] != 0xFF) {
                use_item(game_state, 0);
            }
        }
        
        // START button - open inventory
        if (pressed & BUTTON_START) {
            game_state->state = STATE_INVENTORY;
        }
    } else if (game_state->state == STATE_INVENTORY) {
        // Inventory screen input
        if (pressed & BUTTON_START) {
            // Return to gameplay
            game_state->state = STATE_PLAYING;
        }
        
        // Use A button to use selected item
        if (pressed & BUTTON_A) {
            // Use currently selected inventory item
            // (Implementation would track selected item)
        }
        
        // Navigate inventory
        if (pressed & BUTTON_UP) {
            // Move cursor up
        } else if (pressed & BUTTON_DOWN) {
            // Move cursor down
        }
    } else if (game_state->state == STATE_GAMEOVER) {
        // Game over screen input
        if (pressed & BUTTON_START) {
            // Return to title screen
            game_state->state = STATE_TITLE;
        }
    }
}

// Move the player
void move_player(GameState* game_state, signed char dx, signed char dy) {
    unsigned char new_x = game_state->player.pos.x + dx;
    unsigned char new_y = game_state->player.pos.y + dy;
    unsigned char i;
    
    // Check for level boundaries
    if (new_x >= SCREEN_WIDTH || new_y >= SCREEN_HEIGHT) {
        return;
    }
    
    // Check if destination is walkable
    if (!is_walkable(&game_state->current_level, new_x, new_y)) {
        return;
    }
    
    // Check for enemy at destination
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (game_state->entities[i].active && 
            game_state->entities[i].pos.x == new_x && 
            game_state->entities[i].pos.y == new_y) {
            
            // Enemy found, perform combat
            perform_combat(&game_state->player, &game_state->entities[i]);
            
            // Enemy may have been defeated, check active status
            if (game_state->entities[i].active) {
                // Enemy still alive, don't move
                return;
            }
        }
    }
    
    // Check for stairs
    if (game_state->current_level.tiles[new_y * SCREEN_WIDTH + new_x] == TILE_STAIRS) {
        // Move to next level
        change_level(game_state, game_state->current_level.level_num + 1);
        return;
    }
    
    // Update player position
    game_state->player.pos.x = new_x;
    game_state->player.pos.y = new_y;
    
    // Update hunger when moving
    update_hunger(game_state);
    
    // After player's turn, update enemies
    update_enemies(game_state);
}

// Update all active enemies
void update_enemies(GameState* game_state) {
    unsigned char i;
    signed char dx, dy;
    unsigned char new_x, new_y;
    unsigned char move_dir;
    unsigned char can_move;
    
    for (i = 0; i < MAX_ENTITIES; i++) {
        if (game_state->entities[i].active) {
            // Simple AI - move toward player if in same room, otherwise random movement
            unsigned char player_room = get_room_at(&game_state->current_level, 
                                                  game_state->player.pos.x, 
                                                  game_state->player.pos.y);
            unsigned char enemy_room = get_room_at(&game_state->current_level, 
                                                 game_state->entities[i].pos.x, 
                                                 game_state->entities[i].pos.y);
            
            if (player_room != 0xFF && player_room == enemy_room) {
                // In same room, move toward player
                if (game_state->entities[i].pos.x < game_state->player.pos.x) {
                    dx = 1;
                } else if (game_state->entities[i].pos.x > game_state->player.pos.x) {
                    dx = -1;
                } else {
                    dx = 0;
                }
                
                if (game_state->entities[i].pos.y < game_state->player.pos.y) {
                    dy = 1;
                } else if (game_state->entities[i].pos.y > game_state->player.pos.y) {
                    dy = -1;
                } else {
                    dy = 0;
                }
            } else {
                // Random movement
                move_dir = rand8() % 4;
                
                dx = 0;
                dy = 0;
                
                switch (move_dir) {
                    case 0: dy = -1; break; // Up
                    case 1: dy = 1; break;  // Down
                    case 2: dx = -1; break; // Left
                    case 3: dx = 1; break;  // Right
                }
            }
            
            // Calculate new position
            new_x = game_state->entities[i].pos.x + dx;
            new_y = game_state->entities[i].pos.y + dy;
            
            // Check if movement is possible
            can_move = 1;
            
            // Check boundary
            if (new_x >= SCREEN_WIDTH || new_y >= SCREEN_HEIGHT) {
                can_move = 0;
            }
            
            // Check if destination is walkable
            if (can_move && !is_walkable(&game_state->current_level, new_x, new_y)) {
                can_move = 0;
            }
            
            // Check for player at destination
            if (can_move && 
                game_state->player.pos.x == new_x && 
                game_state->player.pos.y == new_y) {
                
                // Player found, perform combat
                perform_combat(&game_state->entities[i], &game_state->player);
                
                // Check if player died
                if (game_state->player.stats.hp == 0) {
                    // Game over
                    game_over(game_state);
                }
                
                can_move = 0;
            }
            
            // Check for other entities at destination
            if (can_move) {
                unsigned char j;
                for (j = 0; j < MAX_ENTITIES; j++) {
                    if (j != i && game_state->entities[j].active && 
                        game_state->entities[j].pos.x == new_x && 
                        game_state->entities[j].pos.y == new_y) {
                        can_move = 0;
                        break;
                    }
                }
            }
            
            // Move enemy if possible
            if (can_move) {
                game_state->entities[i].pos.x = new_x;
                game_state->entities[i].pos.y = new_y;
            }
        }
    }
}

// Perform combat between attacker and defender
void perform_combat(Entity* attacker, Entity* defender) {
    unsigned char damage;
    
    // Calculate base damage
    damage = attacker->stats.attack;
    
    // Reduce by defender's defense
    if (damage > defender->stats.defense) {
        damage -= defender->stats.defense;
    } else {
        damage = 1; // Minimum damage
    }
    
    // Apply damage
    if (defender->stats.hp <= damage) {
        defender->stats.hp = 0;
        defender->active = 0; // Entity is defeated
        
        // If player defeated an enemy, gain experience
        if (attacker->type == ENTITY_PLAYER && defender->type == ENTITY_ENEMY) {
            // Grant experience based on enemy level
            attacker->stats.experience += 10 + (defender->stats.level * 5);
            
            // Check for level up
            if (attacker->stats.experience >= attacker->stats.level * 20) {
                attacker->stats.level++;
                attacker->stats.max_hp += 2;
                attacker->stats.hp = attacker->stats.max_hp;
                attacker->stats.attack++;
                
                if (attacker->stats.level % 3 == 0) {
                    attacker->stats.defense++;
                }
            }
        }
    } else {
        defender->stats.hp -= damage;
    }
}

// Pick up item at player's position
void pickup_item(GameState* game_state) {
    unsigned char i, j;
    
    // Check for items at player position
    for (i = 0; i < MAX_ITEMS; i++) {
        if (game_state->items[i].in_world && 
            game_state->items[i].pos.x == game_state->player.pos.x && 
            game_state->items[i].pos.y == game_state->player.pos.y) {
            
            // Find empty inventory slot
            for (j = 0; j < MAX_INVENTORY; j++) {
                if (game_state->inventory[j] == 0xFF) {
                    // Add to inventory
                    game_state->inventory[j] = i;
                    game_state->items[i].in_world = 0; // Remove from world
                    return;
                }
            }
            
            // Inventory full, can't pick up
            return;
        }
    }
}

// Use an item from inventory
void use_item(GameState* game_state, unsigned char item_idx) {
    // Ensure index is valid
    if (item_idx >= MAX_INVENTORY || game_state->inventory[item_idx] == 0xFF) {
        return;
    }
    
    // Get the actual item
    unsigned char item_id = game_state->inventory[item_idx];
    Item* item = &game_state->items[item_id];
    
    // Apply item effect based on type
    switch (item->type) {
        case ITEM_WEAPON:
            // Equip weapon (would normally swap with current weapon)
            game_state->player.stats.attack = item->value;
            break;
            
        case ITEM_ARMOR:
            // Equip armor (would normally swap with current armor)
            game_state->player.stats.defense = item->value;
            break;
            
        case ITEM_POTION:
            // Heal player
            game_state->player.stats.hp += item->value;
            if (game_state->player.stats.hp > game_state->player.stats.max_hp) {
                game_state->player.stats.hp = game_state->player.stats.max_hp;
            }
            // Remove from inventory after use
            game_state->inventory[item_idx] = 0xFF;
            break;
            
        case ITEM_SCROLL:
            // Various scroll effects would go here
            // For now, just a simple attack scroll that damages all enemies in the room
            {
                unsigned char player_room = get_room_at(&game_state->current_level, 
                                                      game_state->player.pos.x, 
                                                      game_state->player.pos.y);
                unsigned char i;
                
                for (i = 0; i < MAX_ENTITIES; i++) {
                    if (game_state->entities[i].active) {
                        unsigned char enemy_room = get_room_at(&game_state->current_level, 
                                                             game_state->entities[i].pos.x, 
                                                             game_state->entities[i].pos.y);
                        
                        if (player_room != 0xFF && player_room == enemy_room) {
                            // Damage enemy
                            if (game_state->entities[i].stats.hp <= item->value) {
                                game_state->entities[i].stats.hp = 0;
                                game_state->entities[i].active = 0;
                            } else {
                                game_state->entities[i].stats.hp -= item->value;
                            }
                        }
                    }
                }
                
                // Remove from inventory after use
                game_state->inventory[item_idx] = 0xFF;
            }
            break;
            
        case ITEM_FOOD:
            // Restore hunger
            game_state->player.stats.hunger += item->value * 10;
            if (game_state->player.stats.hunger > 100) {
                game_state->player.stats.hunger = 100;
            }
            // Remove from inventory after use
            game_state->inventory[item_idx] = 0xFF;
            break;
            
        case ITEM_KEY:
            // Would be used to unlock doors, not implemented here
            break;
    }
}

// Update player hunger
void update_hunger(GameState* game_state) {
    // Decrease hunger with movement
    if (game_state->player.stats.hunger > 0) {
        game_state->player.stats.hunger--;
    }
    
    // Effects of hunger
    if (game_state->player.stats.hunger == 0) {
        // Player is starving, take damage
        if (game_state->player.stats.hp > 0) {
            game_state->player.stats.hp--;
            
            // Check if player died from starvation
            if (game_state->player.stats.hp == 0) {
                game_over(game_state);
            }
        }
    }
}

// Change to a new dungeon level
void change_level(GameState* game_state, unsigned char new_level) {
    // Update level number
    game_state->current_level.level_num = new_level;
    
    // Generate a new seed for this level
    game_state->seed = game_state->seed * 1664525 + 1013904223;
    
    // Generate new dungeon
    generate_dungeon(&game_state->current_level, game_state->seed);
    
    // Place entities and items
    place_entities(game_state);
    place_items(game_state);
}

// Handle game over state
void game_over(GameState* game_state) {
    // Set game state to game over
    game_state->state = STATE_GAMEOVER;
}

// Main game update function
void update_game(GameState* game_state) {
    // Handle player input
    handle_input(game_state);
    
    // Update game based on current state
    if (game_state->state == STATE_PLAYING) {
        // Additional gameplay updates would go here
    }
}

// Render the current game state
void render_game_state(GameState* game_state) {
    unsigned char i;
    
    if (game_state->state == STATE_TITLE) {
        // Render title screen
        clear_screen();
        draw_string("CRAVEN CAVERNS", 9, 10);
        draw_string("A ROGUELIKE ADVENTURE", 5, 12);
        draw_string("PRESS START", 10, 16);
    } else if (game_state->state == STATE_PLAYING) {
        // Render dungeon
        draw_dungeon(&game_state->current_level);
        
        // Render items
        for (i = 0; i < MAX_ITEMS; i++) {
            if (game_state->items[i].in_world) {
                // In actual implementation, items would be drawn as sprites
                draw_tile(game_state->items[i].pos.x, game_state->items[i].pos.y, 
                        game_state->items[i].sprite_idx);
            }
        }
        
        // Render entities
        for (i = 0; i < MAX_ENTITIES; i++) {
            if (game_state->entities[i].active) {
                // In actual implementation, entities would be drawn as sprites
                draw_tile(game_state->entities[i].pos.x, game_state->entities[i].pos.y, 
                        game_state->entities[i].sprite_idx);
            }
        }
        
        // Render player
        draw_tile(game_state->player.pos.x, game_state->player.pos.y, 
                game_state->player.sprite_idx);
        
        // Render UI
        render_ui(game_state);
    } else if (game_state->state == STATE_INVENTORY) {
        // Render inventory screen
        clear_screen();
        draw_string("INVENTORY", 11, 2);
        
        // Display inventory items
        for (i = 0; i < MAX_INVENTORY; i++) {
            if (game_state->inventory[i] != 0xFF) {
                // Draw item name
                draw_string(game_state->items[game_state->inventory[i]].name, 5, 4 + i);
            } else {
                // Empty slot
                draw_string("-", 5, 4 + i);
            }
        }
        
        draw_string("PRESS START TO RETURN", 5, 20);
    } else if (game_state->state == STATE_GAMEOVER) {
        // Render game over screen
        clear_screen();
        draw_string("GAME OVER", 11, 10);
        draw_string("PRESS START TO CONTINUE", 4, 14);
    }
}

// Render the UI elements
void render_ui(GameState* game_state) {
    char buffer[16];
    unsigned char i;
    
    // Display player stats at the bottom of the screen
    
    // HP display
    draw_string("HP:", 1, 28);
    
    // Convert HP to string
    buffer[0] = '0' + game_state->player.stats.hp / 10;
    buffer[1] = '0' + game_state->player.stats.hp % 10;
    buffer[2] = '/';
    buffer[3] = '0' + game_state->player.stats.max_hp / 10;
    buffer[4] = '0' + game_state->player.stats.max_hp % 10;
    buffer[5] = '\0';
    
    draw_string(buffer, 4, 28);
    
    // Level display
    draw_string("LVL:", 11, 28);
    
    // Convert level to string
    buffer[0] = '0' + game_state->player.stats.level / 10;
    buffer[1] = '0' + game_state->player.stats.level % 10;
    buffer[2] = '\0';
    
    draw_string(buffer, 15, 28);
    
    // Dungeon level display
    draw_string("FLOOR:", 19, 28);
    
    // Convert dungeon level to string
    buffer[0] = '0' + game_state->current_level.level_num / 10;
    buffer[1] = '0' + game_state->current_level.level_num % 10;
    buffer[2] = '\0';
    
    draw_string(buffer, 25, 28);
    
    // Hunger bar (would be represented with a visual bar in full implementation)
    draw_string("HUNGER:", 1, 29);
    
    // Display hunger as a simple bar
    for (i = 0; i < 10; i++) {
        if (i < game_state->player.stats.hunger / 10) {
            // Filled part of hunger bar
            draw_tile(8 + i, 29, 254);  // Full block character
        } else {
            // Empty part of hunger bar
            draw_tile(8 + i, 29, 255);  // Empty block character
        }
    }
}
