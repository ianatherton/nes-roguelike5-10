#ifndef GAME_DEFS_H
#define GAME_DEFS_H

// Game Constants
#define SCREEN_WIDTH    32
#define SCREEN_HEIGHT   30

#define MAX_ENTITIES    16
#define MAX_ITEMS       32
#define MAX_INVENTORY   8
#define MAX_LEVEL       20

// Game States
#define STATE_TITLE     0
#define STATE_PLAYING   1
#define STATE_INVENTORY 2
#define STATE_GAMEOVER  3

// Tile Types
#define TILE_EMPTY      0
#define TILE_WALL       1
#define TILE_FLOOR      2
#define TILE_DOOR       3
#define TILE_STAIRS     4

// Entity Types
#define ENTITY_PLAYER   0
#define ENTITY_ENEMY    1
#define ENTITY_ITEM     2

// Item Types
#define ITEM_WEAPON     0
#define ITEM_ARMOR      1
#define ITEM_POTION     2
#define ITEM_SCROLL     3
#define ITEM_FOOD       4
#define ITEM_KEY        5

// Directions
#define DIR_UP          0
#define DIR_RIGHT       1
#define DIR_DOWN        2
#define DIR_LEFT        3
#define DIR_UPRIGHT     4
#define DIR_DOWNRIGHT   5
#define DIR_DOWNLEFT    6
#define DIR_UPLEFT      7

// Game Structures

// Position structure
typedef struct {
    unsigned char x;
    unsigned char y;
} Position;

// Statistics structure
typedef struct {
    unsigned char hp;
    unsigned char max_hp;
    unsigned char attack;
    unsigned char defense;
    unsigned char level;
    unsigned int experience;
    unsigned char hunger;
} Stats;

// Entity structure
typedef struct {
    unsigned char type;
    unsigned char active;
    Position pos;
    Stats stats;
    unsigned char sprite_idx;
    unsigned char direction;
} Entity;

// Item structure
typedef struct {
    unsigned char type;
    unsigned char subtype;
    unsigned char value;
    Position pos;
    unsigned char in_world;   // 1 if in dungeon, 0 if in inventory
    unsigned char sprite_idx;
    char name[16];            // Short name
} Item;

// Room structure
typedef struct {
    unsigned char x;
    unsigned char y;
    unsigned char width;
    unsigned char height;
    unsigned char connected;
} Room;

// Level structure
typedef struct {
    unsigned char tiles[SCREEN_WIDTH * SCREEN_HEIGHT];
    unsigned char num_rooms;
    Room rooms[10];           // Max 10 rooms per level
    unsigned char level_num;
    unsigned char stairs_x;
    unsigned char stairs_y;
} Level;

// Game state structure
typedef struct {
    unsigned char state;      // Current game state
    Entity player;
    Entity entities[MAX_ENTITIES];
    Item items[MAX_ITEMS];
    unsigned char inventory[MAX_INVENTORY];
    Level current_level;
    unsigned long seed;       // Random seed for level generation
} GameState;

// Function prototypes
void init_game(void);
void update_game(void);
void render_game(void);

#endif // GAME_DEFS_H
