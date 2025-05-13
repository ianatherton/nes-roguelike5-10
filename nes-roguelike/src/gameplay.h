#ifndef GAMEPLAY_H
#define GAMEPLAY_H

#include "game_defs.h"

// Controller input flags
#define BUTTON_A        0x01
#define BUTTON_B        0x02
#define BUTTON_SELECT   0x04
#define BUTTON_START    0x08
#define BUTTON_UP       0x10
#define BUTTON_DOWN     0x20
#define BUTTON_LEFT     0x40
#define BUTTON_RIGHT    0x80

// Controller registers
#define CONTROLLER_1    *((unsigned char*)0x4016)
#define CONTROLLER_2    *((unsigned char*)0x4017)

// Function prototypes
void init_game_state(GameState* game_state);
void update_game(GameState* game_state);
void handle_input(GameState* game_state);
void move_player(GameState* game_state, signed char dx, signed char dy);
void update_enemies(GameState* game_state);
void perform_combat(Entity* attacker, Entity* defender);
void pickup_item(GameState* game_state);
void use_item(GameState* game_state, unsigned char item_idx);
void update_hunger(GameState* game_state);
void change_level(GameState* game_state, unsigned char new_level);
unsigned char read_controller(void);
void game_over(GameState* game_state);
void render_game_state(GameState* game_state);
void render_ui(GameState* game_state);

#endif // GAMEPLAY_H
