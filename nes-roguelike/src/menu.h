#ifndef MENU_H
#define MENU_H

#include "game_defs.h"
#include "graphics.h"

// Menu Types
#define MENU_MAIN       0
#define MENU_INVENTORY  1
#define MENU_STATS      2
#define MENU_ITEM       3
#define MENU_DIALOG     4

// Menu constants
#define MAX_MENU_ITEMS  10
#define MAX_MENU_TEXT   16  // Max text length for menu items

// Menu item structure
typedef struct {
    char text[MAX_MENU_TEXT];
    unsigned char enabled;
    void (*action)(void);  // Function pointer for menu action
} MenuItem;

// Menu structure
typedef struct {
    unsigned char type;
    unsigned char x;
    unsigned char y;
    unsigned char width;
    unsigned char height;
    unsigned char num_items;
    unsigned char current_selection;
    unsigned char border_tile;
    unsigned char bg_tile;
    MenuItem items[MAX_MENU_ITEMS];
} Menu;

// Function prototypes
void menu_init(void);
void menu_create(Menu* menu, unsigned char type, unsigned char x, unsigned char y, 
                 unsigned char width, unsigned char height);
void menu_add_item(Menu* menu, const char* text, unsigned char enabled, void (*action)(void));
void menu_draw(Menu* menu);
void menu_update(Menu* menu);
void menu_handle_input(Menu* menu, unsigned char input);
void menu_close(Menu* menu);

// Pre-defined menu initializers
void init_main_menu(Menu* menu);
void init_inventory_menu(Menu* menu);
void init_stats_menu(Menu* menu);

// Active menu tracking
extern Menu* active_menu;

#endif // MENU_H
