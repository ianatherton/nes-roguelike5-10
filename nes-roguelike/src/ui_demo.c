#include <string.h>
#include "nes.h"
#include "graphics.h"
#include "menu.h"
#include "text_system.h"
#include "game_defs.h"

// Demo state
#define STATE_TITLE      0
#define STATE_MAIN_MENU  1
#define STATE_STATS      2
#define STATE_INVENTORY  3
#define STATE_DIALOG     4
#define STATE_MESSAGES   5

// Current demo state
unsigned char demo_state = STATE_TITLE;

// Controller state
unsigned char prev_controller = 0;
unsigned char controller = 0;

// Demo functions
void handle_title_screen(void);
void handle_main_menu(void);
void handle_stats_menu(void);
void handle_inventory_menu(void);
void handle_dialog_demo(void);
void handle_message_demo(void);

// Menu action functions
void action_start_game(void);
void action_show_stats(void);
void action_show_inventory(void);
void action_show_dialog(void);
void action_show_messages(void);
void action_return_to_title(void);

// Demo menus
Menu main_menu;
Menu stats_menu;
Menu inventory_menu;

// Read controller input
void read_controller(void) {
    prev_controller = controller;
    
    // Read controller 1
    (*(volatile unsigned char*)0x4016) = 1;
    (*(volatile unsigned char*)0x4016) = 0;
    
    controller = 0;
    unsigned char i;
    for (i = 0; i < 8; i++) {
        // Read controller bit by bit
        controller |= ((*(volatile unsigned char*)0x4016) & 1) << i;
    }
}

// Check if a button was just pressed
unsigned char button_pressed(unsigned char button) {
    return (controller & button) && !(prev_controller & button);
}

// Convert controller input to direction
unsigned char get_direction_input(void) {
    if (button_pressed(0x08)) return DIR_UP;     // Up
    if (button_pressed(0x04)) return DIR_DOWN;   // Down
    if (button_pressed(0x02)) return DIR_LEFT;   // Left
    if (button_pressed(0x01)) return DIR_RIGHT;  // Right
    if (button_pressed(0x80)) return 'A';        // A button
    if (button_pressed(0x40)) return 'B';        // B button
    return 0xFF; // No input
}

// Main entry point
void main(void) {
    // Initialize PPU
    ppu_init();
    
    // Clear screen
    clear_screen();
    
    // Set up palette
    set_palette();
    
    // Initialize menu and text systems
    menu_init();
    text_system_init();
    
    // Set up menus
    // Main menu setup
    menu_create(&main_menu, MENU_MAIN, 10, 8, 12, 10);
    menu_add_item(&main_menu, "PLAY GAME", 1, action_start_game);
    menu_add_item(&main_menu, "STATS", 1, action_show_stats);
    menu_add_item(&main_menu, "INVENTORY", 1, action_show_inventory);
    menu_add_item(&main_menu, "DIALOG", 1, action_show_dialog);
    menu_add_item(&main_menu, "MESSAGES", 1, action_show_messages);
    menu_add_item(&main_menu, "EXIT", 1, action_return_to_title);
    
    // Stats menu setup
    menu_create(&stats_menu, MENU_STATS, 6, 6, 20, 12);
    menu_add_item(&stats_menu, "PLAYER STATS", 0, 0);
    menu_add_item(&stats_menu, "LEVEL: 5", 0, 0);
    menu_add_item(&stats_menu, "HP: 25/30", 0, 0);
    menu_add_item(&stats_menu, "ATTACK: 8", 0, 0);
    menu_add_item(&stats_menu, "DEFENSE: 6", 0, 0);
    menu_add_item(&stats_menu, "EXP: 120/150", 0, 0);
    menu_add_item(&stats_menu, "HUNGER: FULL", 0, 0);
    menu_add_item(&stats_menu, "BACK", 1, action_return_to_title);
    
    // Inventory menu setup
    menu_create(&inventory_menu, MENU_INVENTORY, 5, 5, 22, 14);
    menu_add_item(&inventory_menu, "INVENTORY", 0, 0);
    menu_add_item(&inventory_menu, "SWORD +1", 1, 0);
    menu_add_item(&inventory_menu, "LEATHER ARMOR", 1, 0);
    menu_add_item(&inventory_menu, "HEALING POTION", 1, 0);
    menu_add_item(&inventory_menu, "MAGIC SCROLL", 1, 0);
    menu_add_item(&inventory_menu, "GOLD COIN x15", 1, 0);
    menu_add_item(&inventory_menu, "DUNGEON KEY", 1, 0);
    menu_add_item(&inventory_menu, "BACK", 1, action_return_to_title);
    
    // Start in title screen state
    demo_state = STATE_TITLE;
    
    // Enable rendering
    PPU_CTRL = 0x90; // Enable NMI, use 8x8 sprites, background pattern table at 0x0000
    PPU_MASK = 0x1E; // Show background and sprites
    
    // Main game loop
    while (1) {
        // Wait for next frame
        ppu_wait_vblank();
        
        // Read controller input
        read_controller();
        
        // Handle current state
        switch (demo_state) {
            case STATE_TITLE:
                handle_title_screen();
                break;
            case STATE_MAIN_MENU:
                handle_main_menu();
                break;
            case STATE_STATS:
                handle_stats_menu();
                break;
            case STATE_INVENTORY:
                handle_inventory_menu();
                break;
            case STATE_DIALOG:
                handle_dialog_demo();
                break;
            case STATE_MESSAGES:
                handle_message_demo();
                break;
        }
        
        // Update PPU
        ppu_update();
    }
}

// Handle title screen
void handle_title_screen(void) {
    static unsigned char initialized = 0;
    
    if (!initialized) {
        // Clear screen and draw title
        clear_screen();
        
        // Draw title using Arkista-inspired formatting
        draw_centered_text("CRAVEN CAVERNS", 8, TEXT_COLOR_HIGHLIGHT);
        draw_centered_text("NES ROGUELIKE", 10, TEXT_COLOR_DEFAULT);
        draw_centered_text("UI DEMO", 12, TEXT_COLOR_DEFAULT);
        
        // Instruction
        draw_centered_text("PRESS START", 20, TEXT_COLOR_SUCCESS);
        
        initialized = 1;
    }
    
    // Wait for start button
    if (button_pressed(0x10)) { // Start button
        demo_state = STATE_MAIN_MENU;
        initialized = 0;
    }
}

// Handle main menu
void handle_main_menu(void) {
    static unsigned char initialized = 0;
    
    if (!initialized) {
        // Clear screen and draw menu
        clear_screen();
        
        // Draw title
        draw_centered_text("MAIN MENU", 2, TEXT_COLOR_HIGHLIGHT);
        
        // Draw menu
        menu_draw(&main_menu);
        
        initialized = 1;
    }
    
    // Handle menu input
    unsigned char input = get_direction_input();
    if (input != 0xFF) {
        menu_handle_input(&main_menu, input);
        
        // Redraw menu to update selection
        menu_draw(&main_menu);
    }
}

// Handle stats menu
void handle_stats_menu(void) {
    static unsigned char initialized = 0;
    
    if (!initialized) {
        // Clear screen and draw menu
        clear_screen();
        
        // Draw title
        draw_centered_text("CHARACTER STATS", 2, TEXT_COLOR_HIGHLIGHT);
        
        // Draw menu
        menu_draw(&stats_menu);
        
        initialized = 1;
    }
    
    // Handle menu input
    unsigned char input = get_direction_input();
    if (input != 0xFF) {
        menu_handle_input(&stats_menu, input);
        
        // Redraw menu to update selection
        menu_draw(&stats_menu);
    }
}

// Handle inventory menu
void handle_inventory_menu(void) {
    static unsigned char initialized = 0;
    
    if (!initialized) {
        // Clear screen and draw menu
        clear_screen();
        
        // Draw menu
        menu_draw(&inventory_menu);
        
        initialized = 1;
    }
    
    // Handle menu input
    unsigned char input = get_direction_input();
    if (input != 0xFF) {
        menu_handle_input(&inventory_menu, input);
        
        // Redraw menu to update selection
        menu_draw(&inventory_menu);
    }
}

// Handle dialog demo
void handle_dialog_demo(void) {
    static unsigned char initialized = 0;
    static unsigned char dialog_step = 0;
    
    if (!initialized) {
        // Clear screen and draw background
        clear_screen();
        
        // Draw title
        draw_centered_text("DIALOG DEMO", 2, TEXT_COLOR_HIGHLIGHT);
        
        // Show dialog
        show_dialog_box(TEXT_BOX_MEDIUM, "ARKISTA SPEAKS:");
        add_dialog_text("WELCOME BRAVE WARRIOR!");
        add_dialog_text("YOUR QUEST AWAITS...");
        
        initialized = 1;
    }
    
    // Handle input to advance dialog
    if (button_pressed(0x80)) { // A button
        dialog_step++;
        
        if (dialog_step == 1) {
            // Close first dialog
            close_dialog_box();
            
            // Show second dialog
            show_dialog_box(TEXT_BOX_LARGE, "GAME STORY:");
            add_dialog_text("THE DUNGEON OF CRAVEN");
            add_dialog_text("HOLDS MANY TREASURES");
            add_dialog_text("AND GREAT DANGERS...");
        }
        else if (dialog_step == 2) {
            // Return to main menu
            close_dialog_box();
            demo_state = STATE_MAIN_MENU;
            initialized = 0;
            dialog_step = 0;
        }
    }
    
    // B button to skip
    if (button_pressed(0x40)) { // B button
        close_dialog_box();
        demo_state = STATE_MAIN_MENU;
        initialized = 0;
        dialog_step = 0;
    }
}

// Handle message demo
void handle_message_demo(void) {
    static unsigned char initialized = 0;
    static unsigned char message_timer = 0;
    static unsigned char message_count = 0;
    
    if (!initialized) {
        // Clear screen and draw background
        clear_screen();
        
        // Draw title
        draw_centered_text("MESSAGE DEMO", 2, TEXT_COLOR_HIGHLIGHT);
        draw_centered_text("PRESS A FOR MORE MESSAGES", 4, TEXT_COLOR_DEFAULT);
        draw_centered_text("PRESS B TO RETURN", 6, TEXT_COLOR_DEFAULT);
        
        // Add initial message
        add_message("Welcome to message demo!", TEXT_COLOR_SUCCESS);
        
        initialized = 1;
    }
    
    // Update message system
    update_messages();
    draw_messages();
    
    // Add a new message when A is pressed
    if (button_pressed(0x80)) { // A button
        message_count++;
        
        switch (message_count % 5) {
            case 0:
                add_message("Found a healing potion!", TEXT_COLOR_SUCCESS);
                break;
            case 1:
                add_message("Enemy spotted nearby!", TEXT_COLOR_WARNING);
                break;
            case 2:
                add_message("Gained 25 experience points", TEXT_COLOR_DEFAULT);
                break;
            case 3:
                add_message("Critical hit! 15 damage!", TEXT_COLOR_HIGHLIGHT);
                break;
            case 4:
                add_message("Reached dungeon level 2", TEXT_COLOR_ITEM);
                break;
        }
    }
    
    // Return to main menu when B is pressed
    if (button_pressed(0x40)) { // B button
        demo_state = STATE_MAIN_MENU;
        initialized = 0;
    }
}

// Menu action functions
void action_start_game(void) {
    // In a real game, this would start the game
    // For the demo, just add a message
    add_message("Starting new game...", TEXT_COLOR_SUCCESS);
}

void action_show_stats(void) {
    demo_state = STATE_STATS;
}

void action_show_inventory(void) {
    demo_state = STATE_INVENTORY;
}

void action_show_dialog(void) {
    demo_state = STATE_DIALOG;
}

void action_show_messages(void) {
    demo_state = STATE_MESSAGES;
}

void action_return_to_title(void) {
    demo_state = STATE_TITLE;
}
