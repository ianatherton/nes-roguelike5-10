; Arkista's Ring Gameplay Demo
; Demonstrates character movement and UI elements from Arkista's Ring

.segment "HEADER"
  .byte "NES", $1A      ; iNES header identifier
  .byte 2               ; 2x 16KB PRG-ROM banks
  .byte 1               ; 1x 8KB CHR-ROM bank
  .byte $01, $00        ; Mapper 0, vertical mirroring
  .byte $00, $00, $00, $00, $00, $00, $00, $00 ; Padding

.segment "CHARS"
; Import character data directly from Arkista's Ring
.incbin "assets/arkista_assets/chr_data/chr_bank_0.bin", 0, 8192  ; Read 8KB CHR data

.include "nes.inc"

; Game Variables
.segment "ZEROPAGE"
player_x:        .res 1  ; Player X position
player_y:        .res 1  ; Player Y position
player_dir:      .res 1  ; Player direction (0=right, 1=left, 2=down, 3=up)
player_frame:    .res 1  ; Player animation frame
controller1:     .res 1  ; Controller 1 state
prev_ctrl1:      .res 1  ; Previous controller state
frame_counter:   .res 1  ; Frame counter
game_state:      .res 1  ; 0=title, 1=game, 2=menu
menu_selection:  .res 1  ; Current menu selection
text_ptr:        .res 2  ; Pointer for text drawing
temp1:           .res 1  ; Temp variable
temp2:           .res 1  ; Temp variable
addr_lo:         .res 1  ; Low byte of address
addr_hi:         .res 1  ; High byte of address
item_count:      .res 1  ; Number of items collected
health:          .res 1  ; Player health
max_health:      .res 1  ; Maximum player health
enemy_x:         .res 4  ; Enemy X positions (4 enemies)
enemy_y:         .res 4  ; Enemy Y positions
enemy_type:      .res 4  ; Enemy types
enemy_dir:       .res 4  ; Enemy directions
enemy_active:    .res 4  ; Enemy active state (0=inactive)

; Sprite data stored in RAM at $0200-$02FF
.segment "OAM"
  .res 256

.segment "BSS"
row_counter:     .res 1  ; Used by draw_box
box_x:           .res 1  ; Used by draw_box
box_y:           .res 1  ; Used by draw_box

; Game constants
PLAYER_START_X = $80  ; Middle of screen X
PLAYER_START_Y = $A0  ; Middle of screen Y
PLAYER_SPEED   = $01  ; Player movement speed
SCREEN_WIDTH   = $F8  ; Maximum X coordinate
SCREEN_HEIGHT  = $E0  ; Maximum Y coordinate

; Main code segment
.segment "CODE"

; NMI handler (called during VBlank)
.proc nmi
    ; Save registers
    pha
    txa
    pha
    tya
    pha
    
    ; Increment frame counter
    inc frame_counter
    
    ; DMA sprite data from $0200-$02FF to OAM
    lda #$00
    sta PPU_OAM_ADDR
    lda #$02        ; High byte of sprite data ($0200)
    sta OAM_DMA     ; Start DMA transfer
    
    ; Reset PPU scrolling
    lda #$00
    sta PPU_SCROLL  ; X scroll = 0
    sta PPU_SCROLL  ; Y scroll = 0
    
    ; Restore registers and return
    pla
    tay
    pla
    tax
    pla
    rti
.endproc

; IRQ handler (not used)
.proc irq
    rti
.endproc

; Wait for vblank
.proc wait_vblank
    bit PPU_STATUS
@loop:
    bit PPU_STATUS
    bpl @loop
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Read controller
.proc read_controller
    ; Save previous state
    lda controller1
    sta prev_ctrl1
    
    ; Strobe controller
    lda #$01
    sta CONTROLLER1
    lda #$00
    sta CONTROLLER1
    
    ; Read 8 bits from controller
    ldx #$08
    lda #$00
    sta controller1
@loop:
    lda CONTROLLER1
    lsr a               ; Shift bit into carry
    rol controller1     ; Rotate carry into controller1
    dex
    bne @loop
    
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Update player sprite
.proc update_player_sprite
    ; Set player sprite position
    lda player_y
    sta $0200           ; Y position
    lda player_x
    sta $0203           ; X position
    
    ; Set tile index based on direction and animation frame
    lda player_dir
    cmp #0
    bne @not_right
    
    ; Player facing right
    lda player_frame
    and #$01            ; Only use lowest bit (0 or 1)
    clc
    adc #$4D            ; Tile indices 0x4D (idle) and 0x4E (walking)
    jmp @set_tile
    
@not_right:
    cmp #1
    bne @not_left
    
    ; Player facing left
    lda player_frame
    and #$01            ; Only use lowest bit (0 or 1)
    clc
    adc #$4F            ; Tile indices 0x4F (idle) and 0x50 (walking)
    jmp @set_tile
    
@not_left:
    cmp #2
    bne @not_down
    
    ; Player facing down
    lda player_frame
    and #$01            ; Only use lowest bit (0 or 1)
    clc
    adc #$26            ; Tile indices 0x26 (idle) and 0x27 (walking)
    jmp @set_tile
    
@not_down:
    ; Player facing up (default)
    lda player_frame
    and #$01            ; Only use lowest bit (0 or 1)
    clc
    adc #$28            ; Tile indices 0x28 (idle) and 0x29 (walking)
    
@set_tile:
    sta $0201           ; Tile index
    
    ; Set attributes (palette 0, no flip)
    lda #$00
    sta $0202           ; Attributes
    
    ; Update animation frame every 16 frames
    lda frame_counter
    and #$0F            ; Every 16 frames
    bne @done
    inc player_frame
    
@done:
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Update player position based on controller input
.proc update_player
    ; Check Right button
    lda controller1
    and #$01            ; Right
    beq @check_left     ; Not pressed
    
    ; Move player right
    lda #0              ; Direction = right
    sta player_dir
    
    lda player_x
    clc
    adc #PLAYER_SPEED
    cmp #SCREEN_WIDTH   ; Check if at right edge
    bcs @check_left     ; If greater or equal, don't move
    sta player_x        ; Store new position
    
@check_left:
    ; Check Left button
    lda controller1
    and #$02            ; Left
    beq @check_down     ; Not pressed
    
    ; Move player left
    lda #1              ; Direction = left
    sta player_dir
    
    lda player_x
    sec
    sbc #PLAYER_SPEED
    cmp #$08            ; Check if at left edge
    bcc @check_down     ; If less, don't move
    sta player_x        ; Store new position
    
@check_down:
    ; Check Down button
    lda controller1
    and #$04            ; Down
    beq @check_up       ; Not pressed
    
    ; Move player down
    lda #2              ; Direction = down
    sta player_dir
    
    lda player_y
    clc
    adc #PLAYER_SPEED
    cmp #SCREEN_HEIGHT  ; Check if at bottom edge
    bcs @check_up       ; If greater or equal, don't move
    sta player_y        ; Store new position
    
@check_up:
    ; Check Up button
    lda controller1
    and #$08            ; Up
    beq @check_buttons  ; Not pressed
    
    ; Move player up
    lda #3              ; Direction = up
    sta player_dir
    
    lda player_y
    sec
    sbc #PLAYER_SPEED
    cmp #$08            ; Check if at top edge
    bcc @check_buttons  ; If less, don't move
    sta player_y        ; Store new position
    
@check_buttons:
    ; Check A button (attack)
    lda controller1
    and #$80            ; A button
    beq @check_b        ; Not pressed
    
    ; Check if it was just pressed
    lda prev_ctrl1
    and #$80
    bne @check_b        ; Was already pressed
    
    ; A button just pressed - attack
    ; TODO: Implement attack

@check_b:
    ; Check B button (item use)
    lda controller1
    and #$40            ; B button
    beq @check_start    ; Not pressed
    
    ; Check if it was just pressed
    lda prev_ctrl1
    and #$40
    bne @check_start    ; Was already pressed
    
    ; B button just pressed - use item
    ; TODO: Implement item use

@check_start:
    ; Check Start button (menu)
    lda controller1
    and #$10            ; Start button
    beq @done           ; Not pressed
    
    ; Check if it was just pressed
    lda prev_ctrl1
    and #$10
    bne @done           ; Was already pressed
    
    ; Start button just pressed - open menu
    lda #2              ; Set game state to menu
    sta game_state
    lda #0              ; Reset menu selection
    sta menu_selection
    jsr draw_menu

@done:
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Set PPU address to (addr_hi, addr_lo)
.proc set_ppu_addr
    lda addr_hi
    sta PPU_ADDR
    lda addr_lo
    sta PPU_ADDR
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Draw text string
; X = x position (0-31)
; Y = y position (0-29)
; text_ptr points to null-terminated string
.proc draw_text
    ; Calculate nametable address: $2000 + (y * 32) + x
    tya                 ; A = Y
    asl a               ; Multiply by 2
    asl a               ; Multiply by 4
    asl a               ; Multiply by 8
    asl a               ; Multiply by 16
    asl a               ; Multiply by 32
    sta addr_lo         ; Store low byte
    
    lda #$20            ; High byte starts at $20
    sta addr_hi
    
    txa                 ; X position
    clc
    adc addr_lo         ; Add to low byte
    sta addr_lo
    
    ; Check for overflow to high byte
    bcc @no_carry
    inc addr_hi
@no_carry:
    
    ; Set PPU address
    jsr set_ppu_addr
    
    ; Write string data
    ldy #$00
@loop:
    lda (text_ptr), y   ; Get character
    beq @done           ; If null terminator, we're done
    
    ; Convert ASCII to tile index (assume ASCII starts at 32)
    sec
    sbc #32             ; ASCII to tile index
    clc
    adc #$C0            ; Offset tiles to proper range for UI font
    
    ; Write to PPU
    sta PPU_DATA
    
    ; Next character
    iny
    bne @loop
    
@done:
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Clear the screen (write 0 to all nametable entries)
.proc clear_screen
    ; Set PPU address to $2000 (start of nametable)
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Fill nametable with empty tile (0)
    ldx #$04            ; 4 pages (1024 bytes)
    lda #$00            ; Empty tile
@page_loop:
    ldy #$00            ; 256 bytes per page
@byte_loop:
    sta PPU_DATA
    dey
    bne @byte_loop      ; Loop for 256 bytes
    dex
    bne @page_loop      ; Loop for 4 pages
    
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Draw a box
; X = x position (0-31)
; Y = y position (0-29)
; temp1 = width
; temp2 = height
.proc draw_box
    ; Save X and Y
    stx box_x
    sty box_y
    
    ; Draw top-left corner
    jsr wait_vblank     ; Wait for vblank to ensure safe PPU access
    
    ; Calculate address for top-left corner
    lda box_y
    asl a               ; Multiply by 2
    asl a               ; Multiply by 4
    asl a               ; Multiply by 8
    asl a               ; Multiply by 16
    asl a               ; Multiply by 32
    sta addr_lo         ; Store low byte
    
    lda #$20            ; High byte starts at $20
    sta addr_hi
    
    lda box_x           ; X position
    clc
    adc addr_lo         ; Add to low byte
    sta addr_lo
    
    ; Check for overflow to high byte
    bcc @top_row_start
    inc addr_hi
    
@top_row_start:
    ; Set PPU address
    jsr set_ppu_addr
    
    ; Draw top-left corner
    lda #$C0            ; Box top-left corner tile
    sta PPU_DATA
    
    ; Draw top horizontal border
    lda #$C4            ; Box horizontal border tile
    ldx temp1           ; Width
    dex                 ; Minus 2 for corners
    dex
@top_horizontal:
    sta PPU_DATA
    dex
    bne @top_horizontal
    
    ; Draw top-right corner
    lda #$C1            ; Box top-right corner tile
    sta PPU_DATA
    
    ; Draw middle rows with vertical borders
    lda #0
    sta row_counter
    ldx temp2           ; Height
    dex                 ; Minus 2 for top and bottom
    dex
@row_loop:
    ; Calculate start of this row
    lda box_y
    clc
    adc #1              ; Start at row y+1 (after top row)
    clc
    adc row_counter     ; Add current row counter
    
    ; Multiply by 32 for row offset
    asl a               ; Multiply by 2
    asl a               ; Multiply by 4
    asl a               ; Multiply by 8
    asl a               ; Multiply by 16
    asl a               ; Multiply by 32
    sta addr_lo         ; Store low byte
    
    lda #$20            ; High byte starts at $20
    sta addr_hi
    
    lda box_x           ; X position
    clc
    adc addr_lo         ; Add to low byte
    sta addr_lo
    
    ; Check for overflow to high byte
    bcc @set_row_addr
    inc addr_hi
    
@set_row_addr:
    ; Set PPU address
    jsr set_ppu_addr
    
    ; Draw left vertical border
    lda #$C5            ; Box vertical border tile
    sta PPU_DATA
    
    ; Draw middle space
    lda #$00            ; Empty tile
    ldy temp1           ; Width
    dey                 ; Minus 2 for borders
    dey
@row_middle:
    sta PPU_DATA
    dey
    bne @row_middle
    
    ; Draw right vertical border
    lda #$C5            ; Box vertical border tile
    sta PPU_DATA
    
    ; Next row
    inc row_counter
    dex
    bne @row_loop
    
    ; Draw bottom row
    ; Calculate address for bottom row
    lda box_y
    clc
    adc temp2           ; Add height
    sec
    sbc #1              ; Bottom row is at y+height-1
    
    ; Multiply by 32 for row offset
    asl a               ; Multiply by 2
    asl a               ; Multiply by 4
    asl a               ; Multiply by 8
    asl a               ; Multiply by 16
    asl a               ; Multiply by 32
    sta addr_lo         ; Store low byte
    
    lda #$20            ; High byte starts at $20
    sta addr_hi
    
    lda box_x           ; X position
    clc
    adc addr_lo         ; Add to low byte
    sta addr_lo
    
    ; Check for overflow to high byte
    bcc @bottom_row_start
    inc addr_hi
    
@bottom_row_start:
    ; Set PPU address
    jsr set_ppu_addr
    
    ; Draw bottom-left corner
    lda #$C2            ; Box bottom-left corner tile
    sta PPU_DATA
    
    ; Draw bottom horizontal border
    lda #$C4            ; Box horizontal border tile
    ldx temp1           ; Width
    dex                 ; Minus 2 for corners
    dex
@bottom_horizontal:
    sta PPU_DATA
    dex
    bne @bottom_horizontal
    
    ; Draw bottom-right corner
    lda #$C3            ; Box bottom-right corner tile
    sta PPU_DATA
    
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Draw the title screen
.proc draw_title_screen
    ; Clear screen
    jsr clear_screen
    
    ; Draw title
    lda #<title_text
    sta text_ptr
    lda #>title_text
    sta text_ptr+1
    ldx #8              ; X = 8 (centered)
    ldy #8              ; Y = 8
    jsr draw_text
    
    ; Draw subtitle
    lda #<subtitle_text
    sta text_ptr
    lda #>subtitle_text
    sta text_ptr+1
    ldx #9              ; X = 9 (centered)
    ldy #10             ; Y = 10
    jsr draw_text
    
    ; Draw instruction
    lda #<press_start_text
    sta text_ptr
    lda #>press_start_text
    sta text_ptr+1
    ldx #10             ; X = 10 (centered)
    ldy #20             ; Y = 20
    jsr draw_text
    
    ; Draw decorative box
    ldx #6              ; X = 6
    ldy #6              ; Y = 6
    lda #20             ; Width = 20
    sta temp1
    lda #16             ; Height = 16
    sta temp2
    jsr draw_box
    
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Draw the menu
.proc draw_menu
    ; Clear screen
    jsr clear_screen
    
    ; Draw menu title
    lda #<menu_title_text
    sta text_ptr
    lda #>menu_title_text
    sta text_ptr+1
    ldx #11             ; X = 11 (centered)
    ldy #4              ; Y = 4
    jsr draw_text
    
    ; Draw menu box
    ldx #9              ; X = 9
    ldy #6              ; Y = 6
    lda #14             ; Width = 14
    sta temp1
    lda #12             ; Height = 12
    sta temp2
    jsr draw_box
    
    ; Draw menu items
    ldx #0              ; Start with first menu item
@menu_item_loop:
    cpx #4              ; Check if we've done 4 items
    beq @menu_done
    
    ; Calculate Y position based on item number
    txa
    clc
    adc #8              ; Start at Y = 8 (menu header is 7)
    tay                 ; Y = y position for item
    
    ; Select menu text pointer based on item number
    txa
    asl a               ; Multiply by 2 for pointer array indexing
    tay                 ; Y = index in pointer array
    lda menu_items, y   ; Load low byte of pointer
    sta text_ptr
    lda menu_items+1, y ; Load high byte of pointer
    sta text_ptr+1
    
    ; X position depends on current selection
    cpx menu_selection
    bne @not_selected
    
    ; For selected item, draw ">" selector
    pha                 ; Save A
    lda #<selector_text
    sta text_ptr
    lda #>selector_text
    sta text_ptr+1
    ldx #10             ; X = 10 (one position left of menu text)
    ; Y already set above
    jsr draw_text
    pla                 ; Restore A
    
@not_selected:
    ; Draw menu item text
    ldx #11             ; X = 11 (menu item text position)
    ; Y already set from earlier
    jsr draw_text
    
    ; Next menu item
    ldx temp1           ; Recover X counter
    inx
    stx temp1           ; Save updated counter
    jmp @menu_item_loop
    
@menu_done:
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Draw the game screen with player and environment
.proc draw_game_screen
    ; Clear screen
    jsr clear_screen
    
    ; Draw top status bar box
    ldx #0              ; X = 0
    ldy #0              ; Y = 0
    lda #32             ; Width = 32 (full width)
    sta temp1
    lda #3              ; Height = 3
    sta temp2
    jsr draw_box
    
    ; Draw health label
    lda #<health_text
    sta text_ptr
    lda #>health_text
    sta text_ptr+1
    ldx #1              ; X = 1
    ldy #1              ; Y = 1
    jsr draw_text
    
    ; Draw health value
    lda health
    sta temp1
    lda #<buffer
    sta text_ptr
    lda #>buffer
    sta text_ptr+1
    
    ; Convert health to ASCII
    lda temp1
    clc
    adc #'0'            ; Convert to ASCII
    sta buffer
    lda #0              ; Null terminator
    sta buffer+1
    
    ldx #8              ; X = 8
    ldy #1              ; Y = 1
    jsr draw_text
    
    ; Draw item count label
    lda #<items_text
    sta text_ptr
    lda #>items_text
    sta text_ptr+1
    ldx #18             ; X = 18
    ldy #1              ; Y = 1
    jsr draw_text
    
    ; Draw item count value
    lda item_count
    sta temp1
    lda #<buffer
    sta text_ptr
    lda #>buffer
    sta text_ptr+1
    
    ; Convert item count to ASCII
    lda temp1
    clc
    adc #'0'            ; Convert to ASCII
    sta buffer
    lda #0              ; Null terminator
    sta buffer+1
    
    ldx #25             ; X = 25
    ldy #1              ; Y = 1
    jsr draw_text
    
    ; Draw dungeon environment - simple room with walls
    ; Top wall
    lda #$20            ; Start at nametable address $2060 (row 3)
    sta addr_hi
    lda #$60
    sta addr_lo
    jsr set_ppu_addr
    
    ; Draw top wall
    lda #$A0            ; Wall tile
    ldx #32             ; Full width
@top_wall:
    sta PPU_DATA
    dex
    bne @top_wall
    
    ; Left and right walls for middle rows
    ldx #18             ; 18 rows for room (rows 4-21)
@room_row:
    ; Calculate next row address
    txa
    clc
    adc #3              ; Start at row 3
    
    ; Multiply by 32 for row address
    asl a               ; x2
    asl a               ; x4
    asl a               ; x8
    asl a               ; x16
    asl a               ; x32
    sta addr_lo
    
    lda #$20
    sta addr_hi
    jsr set_ppu_addr
    
    ; Left wall
    lda #$A1            ; Left wall tile
    sta PPU_DATA
    
    ; Empty floor
    lda #$A8            ; Floor tile
    ldy #30             ; 30 floor tiles
@floor:
    sta PPU_DATA
    dey
    bne @floor
    
    ; Right wall
    lda #$A2            ; Right wall tile
    sta PPU_DATA
    
    dex
    bne @room_row
    
    ; Bottom wall
    lda #$23            ; Start at row 22
    asl a               ; x2
    asl a               ; x4
    asl a               ; x8
    asl a               ; x16
    asl a               ; x32
    sta addr_lo
    
    lda #$20
    sta addr_hi
    jsr set_ppu_addr
    
    ; Draw bottom wall
    lda #$A3            ; Bottom wall tile
    ldx #32             ; Full width
@bottom_wall:
    sta PPU_DATA
    dex
    bne @bottom_wall
    
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Process title screen input
.proc handle_title_input
    ; Check Start button
    lda controller1
    and #$10            ; Start button
    beq @done           ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$10
    bne @done           ; Was already pressed
    
    ; Start button just pressed - go to game
    lda #1              ; game_state = GAME
    sta game_state
    jsr draw_game_screen
    
@done:
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq

; Process menu input
.proc handle_menu_input
    ; Check Up button
    lda controller1
    and #$08            ; Up
    beq @check_down     ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$08
    bne @check_down     ; Was already pressed
    
    ; Up button just pressed - move selection up
    lda menu_selection
    beq @check_down     ; Already at top
    dec menu_selection
    jsr draw_menu       ; Redraw menu with new selection
    
@check_down:
    ; Check Down button
    lda controller1
    and #$04            ; Down
    beq @check_select   ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$04
    bne @check_select   ; Was already pressed
    
    ; Down button just pressed - move selection down
    lda menu_selection
    cmp #3              ; 4 menu items (0-3)
    beq @check_select   ; Already at bottom
    inc menu_selection
    jsr draw_menu       ; Redraw menu with new selection
    
@check_select:
    ; Check Start button (select item)
    lda controller1
    and #$10            ; Start
    beq @check_b        ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$10
    bne @check_b        ; Was already pressed
    
    ; Start button just pressed - select item
    lda menu_selection
    cmp #3              ; Last item is "Exit"
    bne @not_exit
    
    ; Exit selected - go back to title
    lda #0
    sta game_state
    jsr draw_title_screen
    jmp @done
    
@not_exit:
    ; For now, all other selections go back to game
    lda #1
    sta game_state
    jsr draw_game_screen
    jmp @done

@check_b:
    ; Check B button (cancel/back)
    lda controller1
    and #$40            ; B button
    beq @done           ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$40
    bne @done           ; Was already pressed
    
    ; B button just pressed - go back to game
    lda #1
    sta game_state
    jsr draw_game_screen
    
@done:
    rts
.endproc

; Main entry point and initialization
.proc reset
    ; Disable IRQs and decimal mode
    sei
    cld
    
    ; Disable APU frame IRQ
    ldx #$40
    stx $4017
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable NMI, PPU rendering, and DMC IRQs
    inx                 ; X = 0
    stx PPU_CTRL
    stx PPU_MASK
    stx $4010
    
    ; Wait for first vblank
    bit PPU_STATUS
@wait_vblank1:
    bit PPU_STATUS
    bpl @wait_vblank1
    
    ; Clear RAM
    lda #$00
@clear_ram:
    sta $0000, x
    sta $0100, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @clear_ram
    
    ; Initialize sprite memory to move sprites off-screen initially
    lda #$FF
    ldx #$00
@init_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @init_sprites
    
    ; Wait for second vblank
    bit PPU_STATUS
@wait_vblank2:
    bit PPU_STATUS
    bpl @wait_vblank2
    
    ; Initialize palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Background palette (first entry is black)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$10            ; Gray
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    
    ; Second background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Third background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth background palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$26            ; Pink
    sta PPU_DATA
    
    ; Sprite palettes (4 palettes of 4 colors each)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$2A            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Second sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    lda #$27            ; Pink
    sta PPU_DATA
    
    ; Third sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Fourth sprite palette
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$06            ; Brown
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Initialize game variables
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    lda #0              ; Direction = right
    sta player_dir
    lda #0              ; Animation frame = 0
    sta player_frame
    lda #0              ; game_state = TITLE
    sta game_state
    lda #0              ; menu_selection = 0
    sta menu_selection
    lda #3              ; health = 3
    sta health
    lda #5              ; max_health = 5
    sta max_health
    lda #0              ; item_count = 0
    sta item_count
    
    ; Initialize other game variables
    lda #0
    ldx #0
@init_enemies:
    sta enemy_active, x ; All enemies inactive
    inx
    cpx #4
    bne @init_enemies
    
    ; Draw initial screen (title)
    jsr draw_title_screen
    
    ; Enable NMI and rendering
    lda #$90            ; Enable NMI, use 8x8 sprites from pattern table 0
    sta PPU_CTRL
    lda #$1E            ; Enable sprites and background
    sta PPU_MASK
    
    ; Enable interrupts
    cli
    
    ; Main game loop
@game_loop:
    ; Wait for vblank
    jsr wait_vblank
    
    ; Read controller
    jsr read_controller
    
    ; Process input and update game based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @game_state
    cmp #$02
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop_end
    
@game_state:
    jsr update_player
    jsr update_player_sprite
    jmp @game_loop_end
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop_end
    
@game_loop_end:
    jmp @game_loop
.endproc

; String and constant data
buffer: .res 16         ; Buffer for string building

; String constants
title_text:
    .byte "ARKISTAS RING DEMO", 0
    
subtitle_text:
    .byte "NES ROGUELIKE", 0
    
press_start_text:
    .byte "PRESS START", 0
    
menu_title_text:
    .byte "MENU", 0
    
menu1_text:
    .byte "CONTINUE", 0
    
menu2_text:
    .byte "INVENTORY", 0
    
menu3_text:
    .byte "SETTINGS", 0
    
menu4_text:
    .byte "EXIT", 0
    
selector_text:
    .byte ">", 0
    
health_text:
    .byte "HEALTH:", 0
    
items_text:
    .byte "ITEMS:", 0

; Menu item pointer table
menu_items:
    .word menu1_text, menu2_text, menu3_text, menu4_text

; Interrupt vectors
.segment "VECTORS"
    .word nmi
    .word reset
    .word irq
