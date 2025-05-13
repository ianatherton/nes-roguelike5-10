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
nmi_ready:       .res 1  ; Flag to indicate NMI processing is ready
seed:            .res 2  ; Random seed

; Sprite data stored in RAM at $0200-$02FF
.segment "OAM"
  .res 256

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
    
    ; Only process if we're ready for an NMI
    lda nmi_ready
    beq @done
    
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
    
    ; Set NMI as processed
    lda #$00
    sta nmi_ready

@done:
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

; Read controller input
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

; Update player position based on controller input
.proc update_player
    ; Check Right button
    lda controller1
    and #$01            ; Right
    beq @check_left     ; Not pressed
    
    ; Move player right
    lda player_x
    clc
    adc #PLAYER_SPEED
    cmp #SCREEN_WIDTH
    bcs @check_left     ; If beyond screen edge, don't update
    sta player_x
    
    ; Set player direction to right
    lda #$00
    sta player_dir
    
@check_left:
    lda controller1
    and #$02            ; Left
    beq @check_down     ; Not pressed
    
    ; Move player left
    lda player_x
    sec
    sbc #PLAYER_SPEED
    bcc @check_down     ; If wrapped around (negative), don't update
    sta player_x
    
    ; Set player direction to left
    lda #$01
    sta player_dir
    
@check_down:
    lda controller1
    and #$04            ; Down
    beq @check_up       ; Not pressed
    
    ; Move player down
    lda player_y
    clc
    adc #PLAYER_SPEED
    cmp #SCREEN_HEIGHT
    bcs @check_up       ; If beyond screen edge, don't update
    sta player_y
    
    ; Set player direction to down
    lda #$02
    sta player_dir
    
@check_up:
    lda controller1
    and #$08            ; Up
    beq @done           ; Not pressed
    
    ; Move player up
    lda player_y
    sec
    sbc #PLAYER_SPEED
    bcc @done           ; If wrapped around (negative), don't update
    sta player_y
    
    ; Set player direction to up
    lda #$03
    sta player_dir
    
@done:
    ; Update player animation frame every 8 frames
    lda frame_counter
    and #$07
    bne @exit
    
    ; Toggle between animation frames (0 and 1)
    lda player_frame
    eor #$01
    sta player_frame
    
@exit:
    rts
.endproc

; Update sprite data for rendering
.proc update_sprites
    ; Clear sprite memory first (move all sprites off screen)
    ldx #$00
    lda #$FF
@clear_sprites:
    sta $0200, x        ; Y position off-screen
    inx
    inx
    inx
    inx
    bne @clear_sprites
    
    ; Calculate player sprite attributes based on direction
    ldx #$00            ; Sprite index
    
    ; Determine base tile index based on direction
    lda player_dir
    asl a               ; Multiply by 2 (2 frames per direction)
    asl a               ; Multiply by 2 again (4 sprites per frame)
    asl a               ; Multiply by 2 again (8 bytes per sprite)
    clc
    adc #$40            ; Base tile index (64 = first character tile)
    sta $02             ; Store in temp variable
    
    ; Add frame offset
    lda player_frame
    asl a               ; Multiply by 2 (2 frames)
    asl a               ; Multiply by 2 again (4 sprites per frame)
    clc
    adc $02
    sta $02             ; Updated tile index in temp var
    
    ; Player sprite 1 (top left)
    lda player_y
    sta $0200, x        ; Y position
    inx
    
    lda $02             ; Base tile from calculation
    sta $0200, x        ; Tile index
    inx
    
    lda #$00            ; Attributes (no flip, palette 0)
    sta $0200, x
    inx
    
    lda player_x
    sta $0200, x        ; X position
    inx
    
    ; Player sprite 2 (top right)
    lda player_y
    sta $0200, x        ; Y position
    inx
    
    lda $02
    clc
    adc #$01            ; Next tile
    sta $0200, x        ; Tile index
    inx
    
    lda #$00            ; Attributes
    sta $0200, x
    inx
    
    lda player_x
    clc
    adc #$08            ; 8 pixels to the right
    sta $0200, x        ; X position
    inx
    
    ; Player sprite 3 (bottom left)
    lda player_y
    clc
    adc #$08            ; 8 pixels down
    sta $0200, x        ; Y position
    inx
    
    lda $02
    clc
    adc #$02            ; Next row of tiles
    sta $0200, x        ; Tile index
    inx
    
    lda #$00            ; Attributes
    sta $0200, x
    inx
    
    lda player_x
    sta $0200, x        ; X position
    inx
    
    ; Player sprite 4 (bottom right)
    lda player_y
    clc
    adc #$08            ; 8 pixels down
    sta $0200, x        ; Y position
    inx
    
    lda $02
    clc
    adc #$03            ; Next tile
    sta $0200, x        ; Tile index
    inx
    
    lda #$00            ; Attributes
    sta $0200, x
    inx
    
    lda player_x
    clc
    adc #$08            ; 8 pixels to the right
    sta $0200, x        ; X position
    
    rts
.endproc

; Wait for vblank
.proc wait_vblank
    bit PPU_STATUS
@loop:
    bit PPU_STATUS
    bpl @loop
    rts
.endproc

; Draw a simple background
.proc draw_background
    ; Set PPU address to $2000 (start of nametable)
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Fill with a simple pattern
    ldx #$00        ; X counter (0-255)
    ldy #$00        ; Y counter (0-3)
@fill_loop:
    txa             ; Get X counter
    and #$03        ; Mod 4 to repeat pattern
    clc
    adc #$01        ; Tiles 1-4
    sta PPU_DATA
    
    inx
    bne @fill_loop  ; Loop for 256 bytes
    
    iny
    cpy #$04        ; 4 * 256 = 1024 tiles
    bne @fill_loop
    
    ; Update attribute table to set colors
    lda #$23
    sta PPU_ADDR
    lda #$C0
    sta PPU_ADDR
    
    lda #$55        ; Checkerboard pattern of palettes
    ldx #$40        ; 64 attribute bytes
@attr_loop:
    sta PPU_DATA
    dex
    bne @attr_loop
    
    rts
.endproc

; Initialize the palette
.proc init_palette
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
    lda #$14            ; Purple
    sta PPU_DATA
    lda #$24            ; Pink
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Sprite palette 1 (player)
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$16            ; Red
    sta PPU_DATA
    lda #$27            ; Brown
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Sprite palette 2
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$19            ; Green
    sta PPU_DATA
    lda #$29            ; Yellow
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Sprite palette 3
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$11            ; Blue
    sta PPU_DATA
    lda #$21            ; Cyan
    sta PPU_DATA
    lda #$30            ; White
    sta PPU_DATA
    
    ; Sprite palette 4
    lda #$0F            ; Black
    sta PPU_DATA
    lda #$14            ; Purple
    sta PPU_DATA
    lda #$24            ; Pink
    sta PPU_DATA
    lda #$30            ; White
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
    
    ; Initialize the game state
    jsr init_game
    
    ; Enable NMI and set sprite size to 8x8
    lda #%10000000
    sta PPU_CTRL
    
    ; Enable sprites and background
    lda #%00011110
    sta PPU_MASK
    
    ; Main game loop
game_loop:
    ; Set NMI ready flag
    lda #$01
    sta nmi_ready
    
    ; Wait for NMI to process before continuing
@wait_nmi:
    lda nmi_ready
    bne @wait_nmi
    
    ; Process game logic
    jsr read_controller
    jsr update_player
    jsr update_sprites
    
    ; Loop forever
    jmp game_loop
.endproc

; Initialize game state
.proc init_game
    ; Set initial player position
    lda #PLAYER_START_X
    sta player_x
    lda #PLAYER_START_Y
    sta player_y
    
    ; Set initial player direction and frame
    lda #$00
    sta player_dir
    sta player_frame
    
    ; Initialize controller state
    lda #$00
    sta controller1
    sta prev_ctrl1
    
    ; Initialize NMI ready flag
    lda #$00
    sta nmi_ready
    
    ; Draw the background
    jsr draw_background
    
    ; Initialize the palette
    jsr init_palette
    
    rts
.endproc

; Vectors
.segment "VECTORS"
.word nmi
.word reset
.word irq
