#include "text_system.h"
#include "graphics.h"

// Define text-related tiles
#define TILE_TEXT_BOX_TL    0x90  // Text box top-left corner
#define TILE_TEXT_BOX_TR    0x91  // Text box top-right corner
#define TILE_TEXT_BOX_BL    0x92  // Text box bottom-left corner
#define TILE_TEXT_BOX_BR    0x93  // Text box bottom-right corner
#define TILE_TEXT_BOX_H     0x94  // Text box horizontal border
#define TILE_TEXT_BOX_V     0x95  // Text box vertical border
#define TILE_TEXT_BG        0x00  // Text background

// Global message queue
Message message_queue[MAX_MESSAGES];
unsigned char message_count = 0;
unsigned char current_message = 0;

// Dialog box state
static unsigned char dialog_active = 0;
static unsigned char dialog_type = 0;
static char dialog_title[MAX_MESSAGE_LENGTH];
static char dialog_lines[3][MAX_MESSAGE_LENGTH];
static unsigned char dialog_line_count = 0;

// Initialize text system
void text_system_init(void) {
    message_count = 0;
    current_message = 0;
    dialog_active = 0;
}

// Add a message to the queue
void add_message(const char* text, unsigned char color) {
    // Don't add if queue is full
    if (message_count >= MAX_MESSAGES) {
        // Replace oldest message
        unsigned char i;
        for (i = 0; i < MAX_MESSAGES - 1; i++) {
            // Move messages up in queue
            unsigned char j;
            for (j = 0; j < MAX_MESSAGE_LENGTH; j++) {
                message_queue[i].text[j] = message_queue[i+1].text[j];
            }
            message_queue[i].color = message_queue[i+1].color;
            message_queue[i].duration = message_queue[i+1].duration;
        }
        message_count--;
    }
    
    // Copy message text (with bounds checking)
    unsigned char i;
    for (i = 0; i < MAX_MESSAGE_LENGTH - 1 && text[i]; i++) {
        message_queue[message_count].text[i] = text[i];
    }
    message_queue[message_count].text[i] = 0; // Null terminator
    
    // Set color and duration
    message_queue[message_count].color = color;
    message_queue[message_count].duration = 120; // 2 seconds at 60fps
    
    // Increment message count
    message_count++;
}

// Update message timers
void update_messages(void) {
    unsigned char i;
    
    // Update dialog first (no messages shown when dialog is active)
    if (dialog_active) return;
    
    // Decrement duration of all messages
    for (i = 0; i < message_count; i++) {
        if (message_queue[i].duration > 0) {
            message_queue[i].duration--;
        }
    }
    
    // Remove expired messages
    while (message_count > 0 && message_queue[0].duration == 0) {
        // Shift all messages down
        for (i = 0; i < message_count - 1; i++) {
            unsigned char j;
            for (j = 0; j < MAX_MESSAGE_LENGTH; j++) {
                message_queue[i].text[j] = message_queue[i+1].text[j];
            }
            message_queue[i].color = message_queue[i+1].color;
            message_queue[i].duration = message_queue[i+1].duration;
        }
        message_count--;
    }
}

// Draw messages in message area
void draw_messages(void) {
    unsigned char i;
    
    // Don't draw messages if dialog is active
    if (dialog_active) return;
    
    // Draw message area background (bottom of screen)
    for (i = 0; i < SCREEN_WIDTH; i++) {
        draw_tile(i, SCREEN_HEIGHT - 2, TILE_TEXT_BOX_H);
    }
    
    // Draw most recent message (or "No messages" if none)
    if (message_count > 0) {
        draw_formatted_text(message_queue[message_count - 1].text, 
                           1, SCREEN_HEIGHT - 1, 
                           message_queue[message_count - 1].color);
    } else {
        draw_formatted_text("Ready", 1, SCREEN_HEIGHT - 1, TEXT_COLOR_DEFAULT);
    }
}

// Show a dialog box
void show_dialog_box(unsigned char type, const char* title) {
    unsigned char i, x, y, width, height;
    
    // Set dialog state
    dialog_active = 1;
    dialog_type = type;
    dialog_line_count = 0;
    
    // Copy title (with bounds checking)
    for (i = 0; i < MAX_MESSAGE_LENGTH - 1 && title[i]; i++) {
        dialog_title[i] = title[i];
    }
    dialog_title[i] = 0; // Null terminator
    
    // Determine size based on type
    switch (type) {
        case TEXT_BOX_SMALL:
            width = 22;
            height = 3;
            x = (SCREEN_WIDTH - width) / 2;
            y = SCREEN_HEIGHT - 5;
            break;
        case TEXT_BOX_MEDIUM:
            width = 26;
            height = 5;
            x = (SCREEN_WIDTH - width) / 2;
            y = SCREEN_HEIGHT - 8;
            break;
        case TEXT_BOX_LARGE:
        default:
            width = 28;
            height = 10;
            x = (SCREEN_WIDTH - width) / 2;
            y = SCREEN_HEIGHT - 15;
            break;
    }
    
    // Draw dialog box frame
    // Top border
    draw_tile(x, y, TILE_TEXT_BOX_TL);
    for (i = 1; i < width - 1; i++) {
        draw_tile(x + i, y, TILE_TEXT_BOX_H);
    }
    draw_tile(x + width - 1, y, TILE_TEXT_BOX_TR);
    
    // Side borders and background
    for (i = 1; i < height - 1; i++) {
        draw_tile(x, y + i, TILE_TEXT_BOX_V);
        
        // Background
        unsigned char j;
        for (j = 1; j < width - 1; j++) {
            draw_tile(x + j, y + i, TILE_TEXT_BG);
        }
        
        draw_tile(x + width - 1, y + i, TILE_TEXT_BOX_V);
    }
    
    // Bottom border
    draw_tile(x, y + height - 1, TILE_TEXT_BOX_BL);
    for (i = 1; i < width - 1; i++) {
        draw_tile(x + i, y + height - 1, TILE_TEXT_BOX_H);
    }
    draw_tile(x + width - 1, y + height - 1, TILE_TEXT_BOX_BR);
    
    // Draw title
    draw_centered_text(dialog_title, y + 1, TEXT_COLOR_HIGHLIGHT);
}

// Add text to dialog box
void add_dialog_text(const char* text) {
    unsigned char i;
    
    // Don't add if dialog is full
    if (dialog_line_count >= 3) return;
    
    // Copy text (with bounds checking)
    for (i = 0; i < MAX_MESSAGE_LENGTH - 1 && text[i]; i++) {
        dialog_lines[dialog_line_count][i] = text[i];
    }
    dialog_lines[dialog_line_count][i] = 0; // Null terminator
    
    // Increment line count
    dialog_line_count++;
    
    // Draw the line
    unsigned char x = (SCREEN_WIDTH - 26) / 2 + 1;
    unsigned char y;
    
    switch (dialog_type) {
        case TEXT_BOX_SMALL:
            y = SCREEN_HEIGHT - 4 + dialog_line_count;
            break;
        case TEXT_BOX_MEDIUM:
            y = SCREEN_HEIGHT - 7 + dialog_line_count;
            break;
        case TEXT_BOX_LARGE:
        default:
            y = SCREEN_HEIGHT - 14 + dialog_line_count + 2; // +2 for title spacing
            break;
    }
    
    draw_formatted_text(dialog_lines[dialog_line_count - 1], x, y, TEXT_COLOR_DEFAULT);
}

// Close dialog box
void close_dialog_box(void) {
    dialog_active = 0;
    
    // Redraw screen (will be implemented by game loop)
    // For now, just clear the dialog area
    unsigned char x, y, width, height;
    
    // Determine size based on type
    switch (dialog_type) {
        case TEXT_BOX_SMALL:
            width = 22;
            height = 3;
            x = (SCREEN_WIDTH - width) / 2;
            y = SCREEN_HEIGHT - 5;
            break;
        case TEXT_BOX_MEDIUM:
            width = 26;
            height = 5;
            x = (SCREEN_WIDTH - width) / 2;
            y = SCREEN_HEIGHT - 8;
            break;
        case TEXT_BOX_LARGE:
        default:
            width = 28;
            height = 10;
            x = (SCREEN_WIDTH - width) / 2;
            y = SCREEN_HEIGHT - 15;
            break;
    }
    
    // Clear dialog area
    unsigned char i, j;
    for (j = 0; j < height; j++) {
        for (i = 0; i < width; i++) {
            draw_tile(x + i, y + j, TILE_TEXT_BG);
        }
    }
}

// Check if dialog is active
unsigned char is_dialog_active(void) {
    return dialog_active;
}

// Draw formatted text with color
void draw_formatted_text(const char* text, unsigned char x, unsigned char y, unsigned char color) {
    // For NES, we'll implement color by setting PPU attribute table
    // For now, just draw text normally
    draw_string(text, x, y);
}

// Draw centered text
void draw_centered_text(const char* text, unsigned char y, unsigned char color) {
    unsigned char length = 0;
    const char* ptr = text;
    
    // Calculate string length
    while (*ptr) {
        length++;
        ptr++;
    }
    
    // Calculate starting position
    unsigned char x = (SCREEN_WIDTH - length) / 2;
    
    // Draw the text
    draw_formatted_text(text, x, y, color);
}

// Draw status text with value
void draw_status_text(const char* text, unsigned char x, unsigned char y, unsigned char value) {
    // Draw the text label
    draw_formatted_text(text, x, y, TEXT_COLOR_DEFAULT);
    
    // Convert value to string (simple for 0-99)
    char value_str[4];
    if (value < 10) {
        value_str[0] = '0' + value;
        value_str[1] = 0;
    } else if (value < 100) {
        value_str[0] = '0' + (value / 10);
        value_str[1] = '0' + (value % 10);
        value_str[2] = 0;
    } else {
        value_str[0] = '9';
        value_str[1] = '9';
        value_str[2] = '+';
        value_str[3] = 0;
    }
    
    // Draw value after label (+ length of text + 1 space)
    unsigned char text_len = 0;
    const char* ptr = text;
    while (*ptr) {
        text_len++;
        ptr++;
    }
    
    draw_formatted_text(value_str, x + text_len + 1, y, TEXT_COLOR_HIGHLIGHT);
}
