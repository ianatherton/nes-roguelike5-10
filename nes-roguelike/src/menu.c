#include "menu.h"
#include "graphics.h"
#include "game_defs.h"

// Define border tiles based on Arkista's Ring UI elements
#define TILE_BORDER_TL  0x80  // Top-left corner
#define TILE_BORDER_TR  0x81  // Top-right corner
#define TILE_BORDER_BL  0x82  // Bottom-left corner
#define TILE_BORDER_BR  0x83  // Bottom-right corner
#define TILE_BORDER_H   0x84  // Horizontal border
#define TILE_BORDER_V   0x85  // Vertical border
#define TILE_BG         0x00  // Background tile

// Global active menu pointer
Menu* active_menu = 0;

// Buffer for menu memory
Menu menu_buffer;

// Initialize the menu system
void menu_init(void) {
    // No menu active initially
    active_menu = 0;
}

// Create a new menu
void menu_create(Menu* menu, unsigned char type, unsigned char x, unsigned char y, 
                 unsigned char width, unsigned char height) {
    // Initialize menu structure
    menu->type = type;
    menu->x = x;
    menu->y = y;
    menu->width = width;
    menu->height = height;
    menu->num_items = 0;
    menu->current_selection = 0;
    menu->border_tile = TILE_BORDER_H;
    menu->bg_tile = TILE_BG;
    
    // Make this the active menu
    active_menu = menu;
}

// Add an item to a menu
void menu_add_item(Menu* menu, const char* text, unsigned char enabled, void (*action)(void)) {
    // Don't add if menu is full
    if (menu->num_items >= MAX_MENU_ITEMS) return;
    
    // Copy text (with bounds checking)
    unsigned char i;
    for (i = 0; i < MAX_MENU_TEXT - 1 && text[i]; i++) {
        menu->items[menu->num_items].text[i] = text[i];
    }
    menu->items[menu->num_items].text[i] = 0; // Null terminator
    
    // Set other properties
    menu->items[menu->num_items].enabled = enabled;
    menu->items[menu->num_items].action = action;
    
    // Increment item count
    menu->num_items++;
}

// Draw the menu
void menu_draw(Menu* menu) {
    unsigned char x, y, i;
    
    // Draw border
    // Top border
    draw_tile(menu->x, menu->y, TILE_BORDER_TL);
    for (x = 1; x < menu->width - 1; x++) {
        draw_tile(menu->x + x, menu->y, TILE_BORDER_H);
    }
    draw_tile(menu->x + menu->width - 1, menu->y, TILE_BORDER_TR);
    
    // Side borders and background
    for (y = 1; y < menu->height - 1; y++) {
        draw_tile(menu->x, menu->y + y, TILE_BORDER_V);
        
        // Background
        for (x = 1; x < menu->width - 1; x++) {
            draw_tile(menu->x + x, menu->y + y, menu->bg_tile);
        }
        
        draw_tile(menu->x + menu->width - 1, menu->y + y, TILE_BORDER_V);
    }
    
    // Bottom border
    draw_tile(menu->x, menu->y + menu->height - 1, TILE_BORDER_BL);
    for (x = 1; x < menu->width - 1; x++) {
        draw_tile(menu->x + x, menu->y + menu->height - 1, TILE_BORDER_H);
    }
    draw_tile(menu->x + menu->width - 1, menu->y + menu->height - 1, TILE_BORDER_BR);
    
    // Draw menu items
    for (i = 0; i < menu->num_items; i++) {
        // Highlight current selection
        if (i == menu->current_selection) {
            // Draw selection indicator (arrow)
            draw_tile(menu->x + 1, menu->y + 1 + i, '>');
        }
        
        // Draw item text
        draw_string(menu->items[i].text, menu->x + 3, menu->y + 1 + i);
        
        // If disabled, draw in different color (will be implemented in text_system)
    }
}

// Update menu (animation, etc)
void menu_update(Menu* menu) {
    // For animation effects or timers
    // Currently nothing to update
}

// Handle input for menu navigation
void menu_handle_input(Menu* menu, unsigned char input) {
    // Up/Down navigation
    if (input == DIR_UP) {
        if (menu->current_selection > 0) {
            menu->current_selection--;
        } else {
            // Wrap to bottom
            menu->current_selection = menu->num_items - 1;
        }
    } else if (input == DIR_DOWN) {
        if (menu->current_selection < menu->num_items - 1) {
            menu->current_selection++;
        } else {
            // Wrap to top
            menu->current_selection = 0;
        }
    }
    
    // Select current item
    else if (input == 'A') { // 'A' button
        if (menu->items[menu->current_selection].enabled && 
            menu->items[menu->current_selection].action) {
            menu->items[menu->current_selection].action();
        }
    }
    
    // Cancel/close menu
    else if (input == 'B') { // 'B' button
        menu_close(menu);
    }
}

// Close the menu
void menu_close(Menu* menu) {
    // Clear active menu
    active_menu = 0;
}

// Initialize main menu
void init_main_menu(Menu* menu) {
    menu_create(menu, MENU_MAIN, 10, 10, 12, 8);
    menu_add_item(menu, "START", 1, 0);
    menu_add_item(menu, "OPTIONS", 1, 0);
    menu_add_item(menu, "QUIT", 1, 0);
}

// Initialize inventory menu
void init_inventory_menu(Menu* menu) {
    menu_create(menu, MENU_INVENTORY, 5, 5, 20, 15);
    menu_add_item(menu, "ITEMS", 1, 0);
    menu_add_item(menu, "EQUIPMENT", 1, 0);
    menu_add_item(menu, "STATUS", 1, 0);
    menu_add_item(menu, "CLOSE", 1, 0);
}

// Initialize stats menu
void init_stats_menu(Menu* menu) {
    menu_create(menu, MENU_STATS, 5, 5, 20, 15);
    menu_add_item(menu, "STATS", 0, 0); // Header, not selectable
    menu_add_item(menu, "LEVEL: 1", 0, 0);
    menu_add_item(menu, "HP: 10/10", 0, 0);
    menu_add_item(menu, "ATK: 5", 0, 0);
    menu_add_item(menu, "DEF: 3", 0, 0);
    menu_add_item(menu, "EXP: 0", 0, 0);
    menu_add_item(menu, "BACK", 1, 0);
}
