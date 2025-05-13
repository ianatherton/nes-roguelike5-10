#ifndef TEXT_SYSTEM_H
#define TEXT_SYSTEM_H

#include "game_defs.h"

// Text formatting constants
#define TEXT_COLOR_DEFAULT      0
#define TEXT_COLOR_HIGHLIGHT    1
#define TEXT_COLOR_WARNING      2
#define TEXT_COLOR_SUCCESS      3
#define TEXT_COLOR_ITEM         4

// Text box size constants
#define TEXT_BOX_SMALL          0  // Single line messages
#define TEXT_BOX_MEDIUM         1  // 3-line dialog
#define TEXT_BOX_LARGE          2  // Full dialog box

// Message queue constants
#define MAX_MESSAGES            8
#define MAX_MESSAGE_LENGTH      32

// Message structure
typedef struct {
    char text[MAX_MESSAGE_LENGTH];
    unsigned char color;
    unsigned char duration; // In frames
} Message;

// Message queue
extern Message message_queue[MAX_MESSAGES];
extern unsigned char message_count;
extern unsigned char current_message;

// Function prototypes
void text_system_init(void);
void add_message(const char* text, unsigned char color);
void update_messages(void); // Call once per frame
void draw_messages(void);

// Dialog box functions
void show_dialog_box(unsigned char type, const char* title);
void add_dialog_text(const char* text);
void close_dialog_box(void);
unsigned char is_dialog_active(void);

// Text formatting functions
void draw_formatted_text(const char* text, unsigned char x, unsigned char y, unsigned char color);
void draw_centered_text(const char* text, unsigned char y, unsigned char color);
void draw_status_text(const char* text, unsigned char x, unsigned char y, unsigned char value);

#endif // TEXT_SYSTEM_H
