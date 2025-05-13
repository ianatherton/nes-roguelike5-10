.include "nes.inc"

;
; Arkista's Ring UI Demo - Shows menu and dialog boxes in the style of Arkista's Ring
;

; Game state variables use the memory addresses defined in nes.inc

; Game state variables
.segment "ZEROPAGE"
game_state:     .res 1  ; 0 = title, 1 = menu, 2 = gameplay
frame_counter:  .res 1  ; Count frames
selection:      .res 1  ; Current menu selection
controller1:    .res 1  ; Current controller state
prev_ctrl1:     .res 1  ; Previous controller state
temp1:          .res 1  ; Temporary variable
temp2:          .res 1  ; Temporary variable
addr_lo:        .res 1  ; Low byte of PPU address
addr_hi:        .res 1  ; High byte of PPU address

; Main code segment
.segment "CODE"

; NMI handler (called on vblank)
.proc nmi
    ; Save registers
    pha
    txa
    pha
    tya
    pha
    
    ; Increment frame counter
    inc frame_counter
    
    ; Reset PPU scrolling
    lda #$00
    sta PPU_SCROLL
    sta PPU_SCROLL
    
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

; Wait for vblank (busy wait on PPU_STATUS bit 7)
.proc wait_vblank
    bit PPU_STATUS
@loop:
    bit PPU_STATUS
    bpl @loop
    rts
.endproc

; Set PPU address to (addr_hi, addr_lo)
.proc set_ppu_addr
    lda addr_hi
    sta PPU_ADDR
    lda addr_lo
    sta PPU_ADDR
    rts
.endproc

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
    adc #32             ; Offset tiles to proper range
    
    ; Write to PPU
    sta PPU_DATA
    
    ; Next character
    iny
    bne @loop
    
@done:
    rts
.endproc

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
    lda #$0A            ; Box top-left corner tile
    sta PPU_DATA
    
    ; Draw top horizontal border
    lda #$0E            ; Box horizontal border tile
    ldx temp1           ; Width
    dex                 ; Minus 2 for corners
    dex
@top_horizontal:
    sta PPU_DATA
    dex
    bne @top_horizontal
    
    ; Draw top-right corner
    lda #$0B            ; Box top-right corner tile
    sta PPU_DATA
    
    ; Draw middle rows with vertical borders
    ldx temp2           ; Height
    dex                 ; Minus 2 for top and bottom
    dex
@row_loop:
    ; Calculate start of this row
    lda box_y
    clc
    adc #1              ; Start at row y+1 (after top row)
    clc
    adc temp2           ; Add current row offset
    sec
    sbc #2              ; Adjust for loop count
    sec
    sbc row_counter    ; Subtract counter
    
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
    lda #$0F            ; Box vertical border tile
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
    lda #$0F            ; Box vertical border tile
    sta PPU_DATA
    
    ; Next row
    inc row_counter
    dex
    bne @row_loop
    lda #$00
    sta row_counter
    
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
    lda #$0C            ; Box bottom-left corner tile
    sta PPU_DATA
    
    ; Draw bottom horizontal border
    lda #$0E            ; Box horizontal border tile
    ldx temp1           ; Width
    dex                 ; Minus 2 for corners
    dex
@bottom_horizontal:
    sta PPU_DATA
    dex
    bne @bottom_horizontal
    
    ; Draw bottom-right corner
    lda #$0D            ; Box bottom-right corner tile
    sta PPU_DATA
    
    rts

; Variables used by draw_box (outside the procedure)
.endproc
row_counter: .byte 0
box_x: .byte 0
box_y: .byte 0

; Draw the title screen
.proc draw_title_screen
    ; Clear screen
    jsr clear_screen
    
    ; Draw title
    lda #<title_text
    sta text_ptr
    lda #>title_text
    sta text_ptr+1
    ldx #10             ; X = 10 (centered)
    ldy #8              ; Y = 8
    jsr draw_text
    
    ; Draw subtitle
    lda #<subtitle_text
    sta text_ptr
    lda #>subtitle_text
    sta text_ptr+1
    ldx #11             ; X = 11 (centered)
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
    ldx #8              ; X = 8
    ldy #6              ; Y = 6
    lda #16             ; Width = 16
    sta temp1
    lda #16             ; Height = 16
    sta temp2
    jsr draw_box
    
    rts
.endproc

; Draw the main menu
.proc draw_main_menu
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
    cpx #5              ; Check if we've done 5 items
    beq @menu_done
    
    ; Calculate address based on menu position
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
    cpx selection
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
    inx
    bne @menu_item_loop ; Branch always (X will never be 0)
    
@menu_done:
    rts
.endproc

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
    
    ; Start button just pressed - go to menu
    lda #1
    sta game_state
    jsr draw_main_menu
    
@done:
    rts
.endproc

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
    lda selection
    beq @check_down     ; Already at top
    dec selection
    jsr draw_main_menu  ; Redraw menu with new selection
    
@check_down:
    ; Check Down button
    lda controller1
    and #$04            ; Down
    beq @check_start    ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$04
    bne @check_start    ; Was already pressed
    
    ; Down button just pressed - move selection down
    lda selection
    cmp #4              ; 5 menu items (0-4)
    beq @check_start    ; Already at bottom
    inc selection
    jsr draw_main_menu  ; Redraw menu with new selection
    
@check_start:
    ; Check Start button (select item)
    lda controller1
    and #$10            ; Start
    beq @done           ; Not pressed
    
    ; Check if it was just pressed (not held)
    lda prev_ctrl1
    and #$10
    bne @done           ; Was already pressed
    
    ; Start button just pressed - select item
    lda selection
    cmp #4              ; Last item is "Exit"
    bne @not_exit
    
    ; Exit selected - go back to title
    lda #0
    sta game_state
    jsr draw_title_screen
    jmp @done
    
@not_exit:
    ; TODO: Handle other menu selections
    
@done:
    rts
.endproc

; Main entry point
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
    
    ; Initialize sprite memory
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
    
    ; Background palette (all grayscale for simplicity)
    ldx #$00
@palette_loop:
    lda palette_data, x
    sta PPU_DATA
    inx
    cpx #$20            ; 32 bytes (8 palettes of 4 colors)
    bne @palette_loop
    
    ; Initialize game state
    lda #$00            ; Start in title screen
    sta game_state
    sta selection       ; Start with first menu item
    
    ; Draw initial screen
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
    
    ; Process input based on state
    lda game_state
    beq @title_state
    cmp #$01
    beq @menu_state
    jmp @game_loop      ; If any other state, just loop
    
@title_state:
    jsr handle_title_input
    jmp @game_loop
    
@menu_state:
    jsr handle_menu_input
    jmp @game_loop
.endproc

; Strings and data
text_ptr: .word $0000   ; Pointer for text drawing

title_text:
.byte "CRAVEN CAVERNS", 0

subtitle_text:
.byte "NES ROGUELIKE", 0

press_start_text:
.byte "PRESS START", 0

menu_title_text:
.byte "MAIN MENU", 0

menu1_text:
.byte "START GAME", 0

menu2_text:
.byte "OPTIONS", 0

menu3_text:
.byte "STATS", 0

menu4_text:
.byte "INVENTORY", 0

menu5_text:
.byte "EXIT", 0

selector_text:
.byte ">", 0

menu_items:
.word menu1_text, menu2_text, menu3_text, menu4_text, menu5_text

; Palette data
palette_data:
; Background palette
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
; Sprite palette
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black
.byte $0F, $30, $10, $00   ; Black, White, Gray, Black

; Interrupt vectors
.segment "VECTORS"
.word nmi
.word reset
.word irq

; Character data (in the CHR segment)
