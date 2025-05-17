;
; Grid Movement Demo for Craven Caverns
; Demonstrates roguelike grid movement with collision detection
;

; iNES header
.segment "HEADER"
  .byte $4E, $45, $53, $1A  ; "NES" followed by MS-DOS EOF
  .byte $02                 ; 2 x 16KB PRG ROM banks
  .byte $01                 ; 1 x 8KB CHR ROM bank
  .byte $01                 ; Mapper 0, vertical mirroring
  .byte $00, $00, $00, $00, $00, $00, $00, $00 ; Padding

; Constants
PPU_CTRL        = $2000
PPU_MASK        = $2001
PPU_STATUS      = $2002
PPU_OAM_ADDR    = $2003
PPU_OAM_DATA    = $2004
PPU_SCROLL      = $2005
PPU_ADDR        = $2006
PPU_DATA        = $2007
OAM_DMA         = $4014
APU_DMC         = $4010
APU_STATUS      = $4015
CONTROLLER1     = $4016
CONTROLLER2     = $4017

; Game constants
GRID_WIDTH      = 16        ; 16 cells across
GRID_HEIGHT     = 15        ; 15 cells down
TILE_SIZE       = 16        ; 16x16 pixels per tile (2x2 NES tiles)
SCREEN_WIDTH    = 256       ; 256 pixels wide (32 tiles)
SCREEN_HEIGHT   = 240       ; 240 pixels high (30 tiles)

SPRITE_PLAYER   = $00       ; Player sprite index in OAM
DIR_UP          = $00
DIR_RIGHT       = $01
DIR_DOWN        = $02
DIR_LEFT        = $03

; RAM variables
.segment "ZEROPAGE"
nmi_ready:      .res 1      ; Set to 1 when ready for NMI
ppu_address_lo: .res 1      ; Low byte of PPU address
ppu_address_hi: .res 1      ; High byte of PPU address
controller1:    .res 1      ; Controller 1 state
last_input:     .res 1      ; Last input state
player_x:       .res 1      ; Player's X position in grid (0-15)
player_y:       .res 1      ; Player's Y position in grid (0-14)
player_px_x:    .res 1      ; Player's X position in pixels
player_px_y:    .res 1      ; Player's Y position in pixels
player_dir:     .res 1      ; Player's facing direction
player_moving:  .res 1      ; 1 if player is moving between grid cells
player_anim:    .res 1      ; Animation frame
temp:           .res 2      ; Temporary variables
seed:           .res 2      ; RNG seed

; OAM buffer
.segment "OAM"
oam: .res 256               ; OAM (sprite) buffer

; VRAM buffer for tile updates
.segment "BSS"
vram_buffer:    .res 128    ; Buffer for VRAM updates
level_data:     .res 240    ; 16x15 grid of tiles

; Game code
.segment "CODE"

;
; Reset handler
;
reset:
  sei                 ; Disable IRQs
  cld                 ; Clear decimal mode
  ldx #$40
  stx APU_DMC        ; Disable DMC IRQs
  ldx #$ff
  txs                 ; Setup stack
  inx                 ; X = 0
  stx PPU_CTRL       ; Disable NMI
  stx PPU_MASK       ; Disable rendering
  stx APU_STATUS     ; Disable APU sound
  lda #$40
  sta APU_DMC        ; Disable DMC IRQ

  ; Wait for first vblank
  bit PPU_STATUS
wait_vblank1:
  bit PPU_STATUS
  bpl wait_vblank1

  ; Initialize RAM
  ldx #0
  lda #0
clear_ram:
  sta $0000, x
  sta $0100, x
  sta $0200, x
  sta $0300, x
  sta $0400, x
  sta $0500, x
  sta $0600, x
  sta $0700, x
  inx
  bne clear_ram

  ; Wait for second vblank
  bit PPU_STATUS
wait_vblank2:
  bit PPU_STATUS
  bpl wait_vblank2

  ; Initialize game state
  jsr init_game

  ; Enable NMI and rendering
  lda #%10010000      ; Enable NMI, sprites and background from Pattern Table 0
  sta PPU_CTRL
  lda #%00011110      ; Enable sprites, background
  sta PPU_MASK

  ; Game loop
game_loop:
  jsr read_controller
  jsr update_game
  jsr wait_for_nmi
  jmp game_loop

;
; Initialize the game
;
init_game:
  ; Initialize RNG seed
  lda #$42
  sta seed
  lda #$53
  sta seed+1

  ; Initialize player position (center of screen)
  lda #8
  sta player_x
  lda #7
  sta player_y
  lda #0
  sta player_dir
  sta player_moving
  sta player_anim

  ; Calculate pixel position
  lda player_x
  asl a
  asl a
  asl a
  asl a              ; x * 16
  sta player_px_x
  lda player_y
  asl a
  asl a
  asl a
  asl a              ; y * 16
  sta player_px_y

  ; Generate a simple dungeon layout
  jsr generate_level

  ; Load palettes
  jsr load_palettes

  ; Load tile data into PPU
  jsr load_background
  jsr load_sprites

  rts

;
; Generate a simple dungeon layout
;
generate_level:
  ldx #0
  ; First create walls all around the perimeter
gen_perimeter:
  ; Top row
  lda #1              ; Wall tile
  sta level_data, x
  ; Bottom row
  txa
  clc
  adc #(GRID_WIDTH * (GRID_HEIGHT-1))
  tay
  lda #1
  sta level_data, y
  ; Continue for all columns
  inx
  cpx #GRID_WIDTH
  bne gen_perimeter

  ; Now left and right edges
  ldx #0
gen_edges:
  ; Left edge
  txa
  asl a
  asl a
  asl a
  asl a              ; x * 16
  tay
  lda #1
  sta level_data, y
  ; Right edge
  tya
  clc
  adc #(GRID_WIDTH-1)
  tay
  lda #1
  sta level_data, y
  ; Move to next row
  inx
  cpx #GRID_HEIGHT
  bne gen_edges

  ; Fill the interior with floor tiles
  ldx #0
gen_interior:
  txa
  ; Skip if on the perimeter
  pha               ; Save X
  tay
  txa
  and #$0F          ; X % 16
  beq next_tile     ; Skip if left edge
  cmp #(GRID_WIDTH-1)
  beq next_tile     ; Skip if right edge
  txa
  cmp #GRID_WIDTH
  bcc next_tile     ; Skip if top row
  cmp #(GRID_WIDTH * (GRID_HEIGHT-1))
  bcs next_tile     ; Skip if bottom row

  ; Interior tile, set as floor
  lda #0            ; Floor tile
  sta level_data, x

next_tile:
  pla               ; Restore X
  tax
  inx
  cpx #(GRID_WIDTH * GRID_HEIGHT)
  bne gen_interior

  ; Add some random walls in the interior
  ldx #20           ; Number of random walls to add
add_random_walls:
  jsr random
  and #$0F          ; X position (0-15)
  sta temp
  jsr random
  and #$0F          ; Y position (0-15)
  sta temp+1

  ; Skip perimeter
  lda temp
  beq next_wall
  cmp #(GRID_WIDTH-1)
  beq next_wall
  lda temp+1
  beq next_wall
  cmp #(GRID_HEIGHT-1)
  beq next_wall

  ; Skip player position
  lda temp
  cmp player_x
  bne not_player_pos
  lda temp+1
  cmp player_y
  beq next_wall
not_player_pos:

  ; Convert to level_data index
  lda temp+1
  asl a
  asl a
  asl a
  asl a             ; y * 16
  ora temp          ; + x
  tay
  lda #1            ; Wall tile
  sta level_data, y

next_wall:
  dex
  bne add_random_walls
  rts

;
; Load palettes
;
load_palettes:
  lda PPU_STATUS    ; Reset PPU address latch
  lda #$3F
  sta PPU_ADDR      ; Set PPU address to $3F00 (palette memory)
  lda #$00
  sta PPU_ADDR

  ldx #0
load_palette_loop:
  lda palettes, x
  sta PPU_DATA
  inx
  cpx #32
  bne load_palette_loop
  rts

;
; Load background tiles
;
load_background:
  lda PPU_STATUS    ; Reset PPU address latch
  lda #$20
  sta PPU_ADDR      ; Set PPU address to $2000 (nametable)
  lda #$00
  sta PPU_ADDR

  ; Load nametable
  ldx #0
  ldy #0
load_bg_loop:
  ; Get the grid cell type
  sty temp
  lda level_data, y
  asl a             ; * 4 (each grid cell is 2x2 NES tiles)
  asl a
  sta temp+1

  ; Each grid cell is 2x2 tiles
  ; Load top-left tile
  lda temp+1
  sta PPU_DATA
  ; Load top-right tile
  lda temp+1
  clc
  adc #1
  sta PPU_DATA
  
  inx
  inx
  cpx #32          ; 32 tiles per row (16 grid cells * 2 tiles wide)
  bne load_bg_next_col
  
  ; Move to next row, same grid row
  ldx #0
  ; Load bottom-left tile
  lda temp+1
  clc
  adc #2
  sta PPU_DATA
  ; Load bottom-right tile
  lda temp+1
  clc
  adc #3
  sta PPU_DATA
  
  inx
  inx
  cpx #32
  bne load_bg_next_col
  
  ; Start a new grid row
  ldx #0
  iny
  cpy #(GRID_WIDTH * GRID_HEIGHT)
  bne load_bg_loop
  
  jmp load_bg_done
  
load_bg_next_col:
  ldy temp         ; Restore Y
  jmp load_bg_loop
  
load_bg_done:
  ; Load attribute table
  lda #$23
  sta PPU_ADDR
  lda #$C0
  sta PPU_ADDR
  
  ldx #0
load_attr_loop:
  lda #$00
  sta PPU_DATA
  inx
  cpx #64
  bne load_attr_loop
  
  rts

;
; Load sprites
;
load_sprites:
  ; Initialize OAM to be off-screen
  ldx #0
  lda #$FF        ; Y position offscreen
init_oam_loop:
  sta oam, x
  inx
  inx
  inx
  inx
  bne init_oam_loop
  
  ; Initialize player sprite
  lda player_px_y
  sta oam+SPRITE_PLAYER    ; Y position
  lda #$10                 ; Player sprite tile
  sta oam+SPRITE_PLAYER+1  ; Tile index
  lda #$00                 ; No flip, front palette
  sta oam+SPRITE_PLAYER+2  ; Attributes
  lda player_px_x
  sta oam+SPRITE_PLAYER+3  ; X position
  
  rts

;
; Read controller input
;
read_controller:
  ; Save previous state
  lda controller1
  sta last_input
  
  ; Strobe controller
  lda #$01
  sta CONTROLLER1
  lda #$00
  sta CONTROLLER1
  
  ; Read controller
  ldx #$08
  ldy #$00
read_controller_loop:
  lda CONTROLLER1
  lsr a
  rol temp
  dex
  bne read_controller_loop
  
  lda temp
  sta controller1
  rts

;
; Update game state
;
update_game:
  ; If player is moving, continue animation
  lda player_moving
  beq check_movement
  
  ; Player is moving, update position
  dec player_moving
  jsr update_player_position
  rts
  
check_movement:
  ; Check if player can move
  lda controller1
  and #%00001111   ; Check D-pad only
  beq no_movement
  
  ; D-pad pressed, try to move player
  lda controller1
  and #%00001000   ; Up
  beq not_up
  lda #DIR_UP
  sta player_dir
  
  ; Check if we can move up
  lda player_y
  beq up_blocked   ; At top edge
  tax
  dex              ; Y-1
  txa
  asl a
  asl a
  asl a
  asl a            ; * 16
  ora player_x
  tax
  lda level_data, x
  bne up_blocked   ; Wall tile
  
  ; Can move up
  dec player_y
  lda #7           ; Movement animation frames
  sta player_moving
  rts
  
up_blocked:
not_up:
  
  lda controller1
  and #%00000100   ; Down
  beq not_down
  lda #DIR_DOWN
  sta player_dir
  
  ; Check if we can move down
  lda player_y
  cmp #(GRID_HEIGHT-1)
  beq down_blocked  ; At bottom edge
  tax
  inx               ; Y+1
  txa
  asl a
  asl a
  asl a
  asl a             ; * 16
  ora player_x
  tax
  lda level_data, x
  bne down_blocked  ; Wall tile
  
  ; Can move down
  inc player_y
  lda #7            ; Movement animation frames
  sta player_moving
  rts
  
down_blocked:
not_down:
  
  lda controller1
  and #%00000010    ; Right
  beq not_right
  lda #DIR_RIGHT
  sta player_dir
  
  ; Check if we can move right
  lda player_x
  cmp #(GRID_WIDTH-1)
  beq right_blocked ; At right edge
  tax
  inx                ; X+1
  txa
  sta temp
  lda player_y
  asl a
  asl a
  asl a
  asl a              ; * 16
  ora temp
  tax
  lda level_data, x
  bne right_blocked  ; Wall tile
  
  ; Can move right
  inc player_x
  lda #7             ; Movement animation frames
  sta player_moving
  rts
  
right_blocked:
not_right:
  
  lda controller1
  and #%00000001     ; Left
  beq not_left
  lda #DIR_LEFT
  sta player_dir
  
  ; Check if we can move left
  lda player_x
  beq left_blocked   ; At left edge
  tax
  dex                 ; X-1
  txa
  sta temp
  lda player_y
  asl a
  asl a
  asl a
  asl a               ; * 16
  ora temp
  tax
  lda level_data, x
  bne left_blocked    ; Wall tile
  
  ; Can move left
  dec player_x
  lda #7              ; Movement animation frames
  sta player_moving
  rts
  
left_blocked:
not_left:
  
no_movement:
  rts

;
; Update player position based on animation
;
update_player_position:
  ; Calculate target position
  lda player_x
  asl a
  asl a
  asl a
  asl a              ; * 16
  sta temp           ; Target X
  
  lda player_y
  asl a
  asl a
  asl a
  asl a              ; * 16
  sta temp+1         ; Target Y
  
  ; Move towards target position based on direction
  lda player_dir
  cmp #DIR_RIGHT
  bne not_moving_right
  lda player_px_x
  clc
  adc #2             ; Move 2 pixels per frame
  sta player_px_x
  jmp position_updated
  
not_moving_right:
  cmp #DIR_LEFT
  bne not_moving_left
  lda player_px_x
  sec
  sbc #2             ; Move 2 pixels per frame
  sta player_px_x
  jmp position_updated
  
not_moving_left:
  cmp #DIR_DOWN
  bne not_moving_down
  lda player_px_y
  clc
  adc #2             ; Move 2 pixels per frame
  sta player_px_y
  jmp position_updated
  
not_moving_down:
  ; Must be moving up
  lda player_px_y
  sec
  sbc #2             ; Move 2 pixels per frame
  sta player_px_y
  
position_updated:
  ; If movement is done, snap to grid
  lda player_moving
  bne still_moving
  
  ; Snap to grid
  lda temp
  sta player_px_x
  lda temp+1
  sta player_px_y
  
still_moving:
  ; Update player sprite
  lda player_px_y
  sta oam+SPRITE_PLAYER    ; Y position
  
  ; Choose animation frame based on direction
  lda player_dir
  asl a              ; * 2 (2 frames per direction)
  asl a
  clc
  adc #$10           ; Base player sprite
  clc
  adc player_anim    ; Current animation frame
  sta oam+SPRITE_PLAYER+1  ; Tile index
  
  ; Set attributes based on direction
  lda player_dir
  cmp #DIR_LEFT
  bne not_facing_left
  lda #%01000000      ; Flip horizontally
  sta oam+SPRITE_PLAYER+2
  jmp attrs_set
  
not_facing_left:
  lda #%00000000      ; No flip
  sta oam+SPRITE_PLAYER+2
  
attrs_set:
  lda player_px_x
  sta oam+SPRITE_PLAYER+3  ; X position
  
  ; Update animation frame every 4 frames
  lda player_moving
  and #%00000011
  bne no_anim_update
  
  ; Toggle animation frame
  lda player_anim
  eor #$01
  sta player_anim
  
no_anim_update:
  rts

;
; Wait for NMI
;
wait_for_nmi:
  lda #$01
  sta nmi_ready
wait_nmi_loop:
  lda nmi_ready
  bne wait_nmi_loop
  rts

;
; NMI handler (runs once per frame)
;
nmi:
  ; Save registers
  pha
  txa
  pha
  tya
  pha
  
  ; Update OAM
  lda #$00
  sta PPU_OAM_ADDR
  lda #$02
  sta OAM_DMA
  
  ; Reset scroll position
  lda #$00
  sta PPU_SCROLL
  sta PPU_SCROLL
  
  ; Signal that NMI has run
  lda #$00
  sta nmi_ready
  
  ; Restore registers
  pla
  tay
  pla
  tax
  pla
  rti

;
; IRQ handler
;
irq:
  rti

;
; Simple random number generator
;
random:
  lda seed
  beq do_eor
  asl a
  beq no_eor
  bcc no_eor
do_eor:
  eor #$1D
no_eor:
  sta seed
  eor seed+1
  rts

; Palettes
palettes:
  ; Background palettes
  .byte $0F, $00, $10, $30  ; Black, gray, light blue (floor)
  .byte $0F, $07, $17, $27  ; Black, brown, light brown (walls)
  .byte $0F, $02, $12, $22  ; Black, blue, light blue (water)
  .byte $0F, $0A, $1A, $2A  ; Black, green, light green (grass)

  ; Sprite palettes
  .byte $0F, $16, $26, $20  ; Player
  .byte $0F, $14, $24, $34  ; Enemy 1
  .byte $0F, $1A, $2A, $3A  ; Enemy 2
  .byte $0F, $13, $23, $33  ; Item

; Interrupt vectors
.segment "VECTORS"
  .word nmi, reset, irq
