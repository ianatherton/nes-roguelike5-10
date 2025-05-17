;
; Christine Walker Demo
; Based on the sprite_showcase demo
; Uses character data exported from NES Asset Wizard
;
; A simple demo that displays the Christine character
; and allows movement with the controller
;

.include "constants.inc"
.include "header.inc"

; Variables
.segment "ZEROPAGE"
player_x:       .res 1  ; Player X position
player_y:       .res 1  ; Player Y position
player_dir:     .res 1  ; Player direction (0=down, 1=up, 2=right, 3=left)
player_frame:   .res 1  ; Animation frame counter
player_anim:    .res 1  ; Current animation type (0=idle, 1=walk, 2=attack)
controller1:    .res 1  ; Controller 1 input
last_controller: .res 1 ; Previous frame's controller input
frame_counter:  .res 1  ; Global frame counter
temp:           .res 1  ; Temporary variable

; Constants
.segment "RODATA"
; Direction constants
DIR_DOWN  = 0
DIR_UP    = 1
DIR_RIGHT = 2
DIR_LEFT  = 3

; Animation type constants
ANIM_IDLE   = 0
ANIM_WALK   = 1
ANIM_ATTACK = 2

; Sprite data - these will be arrays of tile indexes into our CHR data
; Format: Walking animations for each direction (2 frames each)
sprite_walk_down:  .byte $00, $01
sprite_walk_up:    .byte $02, $03
sprite_walk_right: .byte $04, $05
sprite_walk_left:  .byte $04, $05  ; We'll flip these horizontally

; Attack animations for each direction (1 frame each)
sprite_attack_down:  .byte $06
sprite_attack_up:    .byte $07
sprite_attack_right: .byte $08
sprite_attack_left:  .byte $08     ; We'll flip this horizontally

; Death animation (1 frame)
sprite_death: .byte $09

; Palette data
palette_data:
  ; Background palette
  .byte $0F, $2C, $21, $30  ; BG0 - Dark blue, light blue, white
  .byte $0F, $2C, $21, $30  ; BG1
  .byte $0F, $2C, $21, $30  ; BG2 
  .byte $0F, $2C, $21, $30  ; BG3
  ; Sprite palette
  .byte $0F, $16, $26, $37  ; SP0 - Christine (red dress, flesh, blonde hair)
  .byte $0F, $19, $29, $38  ; SP1 - Alternative palette
  .byte $0F, $1C, $2C, $3C  ; SP2
  .byte $0F, $14, $24, $34  ; SP3

; Main code
.segment "CODE"
.proc irq_handler
  RTI
.endproc

.proc nmi_handler
  ; Save registers
  PHP
  PHA
  TXA
  PHA
  TYA
  PHA

  ; Update sprites
  JSR update_sprites

  ; Update the PPU
  LDA #$00
  STA OAMADDR
  LDA #$02
  STA OAMDMA

  ; Update the PPU scroll position
  LDA #$00
  STA PPUSCROLL
  STA PPUSCROLL

  ; Increment the frame counter
  INC frame_counter
  
  ; Restore registers
  PLA
  TAY
  PLA
  TAX
  PLA
  PLP
  
  RTI
.endproc

.proc reset_handler
  SEI         ; Disable IRQs
  CLD         ; Clear decimal mode
  LDX #$40
  STX $4017   ; Disable APU frame IRQ
  LDX #$FF
  TXS         ; Set up stack
  INX         ; X = 0
  STX PPUCTRL ; Disable NMI
  STX PPUMASK ; Disable rendering
  STX $4010   ; Disable DMC IRQs

  ; Wait for first vblank
vblankwait1:
  BIT PPUSTATUS
  BPL vblankwait1

  ; Clear RAM
clear_memory:
  LDA #$00
  STA $0000, X
  STA $0100, X
  STA $0200, X
  STA $0300, X
  STA $0400, X
  STA $0500, X
  STA $0600, X
  STA $0700, X
  INX
  BNE clear_memory

  ; Wait for second vblank
vblankwait2:
  BIT PPUSTATUS
  BPL vblankwait2

  ; Initialize variables
  LDA #$80
  STA player_x
  LDA #$80
  STA player_y
  LDA #DIR_DOWN
  STA player_dir
  LDA #$00
  STA player_frame
  LDA #ANIM_IDLE
  STA player_anim
  LDA #$00
  STA frame_counter

  ; Load palette
  JSR load_palette
  
  ; Enable sprites and background
  LDA #%10010000  ; Enable NMI, sprites use first pattern table 
  STA PPUCTRL
  LDA #%00011110  ; Enable sprites, enable background
  STA PPUMASK

  ; Main loop
forever:
  JSR read_controller
  JSR update_player
  
  ; Wait for next frame
  LDA #$01
@wait_for_vblank:
  CMP frame_counter
  BNE @wait_for_vblank
  LDA #$00
  STA frame_counter
  
  JMP forever
.endproc

; Load the palette data
.proc load_palette
  ; Reset PPU address to palette start
  LDA PPUSTATUS   ; Read PPU status to reset the high/low latch
  LDA #$3F
  STA PPUADDR     ; Write high byte of $3F00 address
  LDA #$00
  STA PPUADDR     ; Write low byte of $3F00 address
  
  ; Load palette data
  LDX #$00
@loop:
  LDA palette_data, X
  STA PPUDATA
  INX
  CPX #$20        ; 32 bytes = 8 palettes × 4 colors
  BNE @loop
  
  RTS
.endproc

; Read controller input
.proc read_controller
  ; Store the previous frame's input
  LDA controller1
  STA last_controller

  ; Read new controller input
  LDA #$01
  STA CONTROLLER1
  LDA #$00
  STA CONTROLLER1
  
  LDX #$08
@loop:
  LDA CONTROLLER1
  LSR A           ; Bit 0 -> Carry
  ROL controller1 ; Carry -> Bit 0, Bit 7 -> Carry
  DEX
  BNE @loop
  
  RTS
.endproc

; Update player position and animation based on controller
.proc update_player
  ; Check if attack button pressed (A)
  LDA controller1
  AND #BUTTON_A
  BEQ @check_movement
  
  ; Start attack animation
  LDA #ANIM_ATTACK
  STA player_anim
  JMP @done_input

@check_movement:
  ; Reset to idle by default
  LDA #ANIM_IDLE
  STA player_anim

  ; Check D-pad input
  LDA controller1
  
  ; Check up
  AND #BUTTON_UP
  BEQ @check_down
  DEC player_y
  LDA #DIR_UP
  STA player_dir
  LDA #ANIM_WALK
  STA player_anim

@check_down:
  LDA controller1
  AND #BUTTON_DOWN
  BEQ @check_left
  INC player_y
  LDA #DIR_DOWN
  STA player_dir
  LDA #ANIM_WALK
  STA player_anim

@check_left:
  LDA controller1
  AND #BUTTON_LEFT
  BEQ @check_right
  DEC player_x
  LDA #DIR_LEFT
  STA player_dir
  LDA #ANIM_WALK
  STA player_anim

@check_right:
  LDA controller1
  AND #BUTTON_RIGHT
  BEQ @done_input
  INC player_x
  LDA #DIR_RIGHT
  STA player_dir
  LDA #ANIM_WALK
  STA player_anim

@done_input:
  ; Slow down animations - update frame every 8 frames
  LDA frame_counter
  AND #$07
  BNE @done
  
  ; Update animation frame
  LDA player_frame
  EOR #$01        ; Toggle between 0 and 1
  STA player_frame
  
@done:
  RTS
.endproc

; Update sprite positions and tiles
.proc update_sprites
  ; Player sprite (2×2 metasprite using 4 hardware sprites)
  
  ; Calculate the tile number based on direction and animation
  LDX player_dir
  LDA player_anim
  
  ; If idle, use first frame of walk animation
  CMP #ANIM_IDLE
  BNE @not_idle
  
  ; Idle animation - use first frame of walk cycle
  CPX #DIR_DOWN
  BNE @not_down_idle
  LDA sprite_walk_down
  JMP @store_tile
@not_down_idle:
  CPX #DIR_UP
  BNE @not_up_idle
  LDA sprite_walk_up
  JMP @store_tile
@not_up_idle:
  CPX #DIR_RIGHT
  BNE @not_right_idle
  LDA sprite_walk_right
  JMP @store_tile
@not_right_idle:
  ; Must be left
  LDA sprite_walk_left
  JMP @store_tile
  
@not_idle:
  CMP #ANIM_WALK
  BNE @not_walk
  
  ; Walk animation - use correct frame based on frame counter
  LDY player_frame  ; 0 or 1
  
  CPX #DIR_DOWN
  BNE @not_down_walk
  LDA sprite_walk_down, Y
  JMP @store_tile
@not_down_walk:
  CPX #DIR_UP
  BNE @not_up_walk
  LDA sprite_walk_up, Y
  JMP @store_tile
@not_up_walk:
  CPX #DIR_RIGHT
  BNE @not_right_walk
  LDA sprite_walk_right, Y
  JMP @store_tile
@not_right_walk:
  ; Must be left
  LDA sprite_walk_left, Y
  JMP @store_tile
  
@not_walk:
  ; Attack animation
  CPX #DIR_DOWN
  BNE @not_down_attack
  LDA sprite_attack_down
  JMP @store_tile
@not_down_attack:
  CPX #DIR_UP
  BNE @not_up_attack
  LDA sprite_attack_up
  JMP @store_tile
@not_up_attack:
  CPX #DIR_RIGHT
  BNE @not_right_attack
  LDA sprite_attack_right
  JMP @store_tile
@not_right_attack:
  ; Must be left
  LDA sprite_attack_left
  
@store_tile:
  ; A now contains the tile index
  STA temp
  
  ; Calculate the actual CHR tile numbers (each frame is 4 tiles in a 2x2 arrangement)
  ; The tiles go in this layout for each character sprite:
  ; [0][1]
  ; [2][3]
  
  ; Calculate base tile = tile_index * 4
  LDA temp
  ASL A           ; × 2
  ASL A           ; × 4
  STA temp
  
  ; Top-left sprite
  LDY #$00
  LDA player_y    ; Y position
  STA $0200, Y
  INY
  LDA temp        ; Tile number
  STA $0200, Y
  INY
  LDA #$00        ; Attributes
  ; Flip horizontally if facing left
  LDX player_dir
  CPX #DIR_LEFT
  BNE @no_flip_1
  ORA #%01000000  ; Flip horizontally
@no_flip_1:
  STA $0200, Y
  INY
  LDA player_x    ; X position
  STA $0200, Y
  INY
  
  ; Top-right sprite
  LDA player_y    ; Y position
  STA $0200, Y
  INY
  LDA temp        ; Tile number
  CLC
  ADC #$01        ; Next tile
  STA $0200, Y
  INY
  LDA #$00        ; Attributes
  ; Flip horizontally if facing left
  CPX #DIR_LEFT
  BNE @no_flip_2
  ORA #%01000000  ; Flip horizontally
@no_flip_2:
  STA $0200, Y
  INY
  LDA player_x    ; X position
  CLC
  ADC #$08        ; Move 8 pixels right
  STA $0200, Y
  INY
  
  ; Bottom-left sprite
  LDA player_y    ; Y position
  CLC
  ADC #$08        ; Move 8 pixels down
  STA $0200, Y
  INY
  LDA temp        ; Tile number
  CLC
  ADC #$02        ; Move to row below
  STA $0200, Y
  INY
  LDA #$00        ; Attributes
  ; Flip horizontally if facing left
  CPX #DIR_LEFT
  BNE @no_flip_3
  ORA #%01000000  ; Flip horizontally
@no_flip_3:
  STA $0200, Y
  INY
  LDA player_x    ; X position
  STA $0200, Y
  INY
  
  ; Bottom-right sprite
  LDA player_y    ; Y position
  CLC
  ADC #$08        ; Move 8 pixels down
  STA $0200, Y
  INY
  LDA temp        ; Tile number
  CLC
  ADC #$03        ; Next tile
  STA $0200, Y
  INY
  LDA #$00        ; Attributes
  ; Flip horizontally if facing left
  CPX #DIR_LEFT
  BNE @no_flip_4
  ORA #%01000000  ; Flip horizontally
@no_flip_4:
  STA $0200, Y
  INY
  LDA player_x    ; X position
  CLC
  ADC #$08        ; Move 8 pixels right
  STA $0200, Y
  
  ; Hide the rest of the sprites
  LDX #$10        ; Start at sprite 4 (byte 16)
@hide_loop:
  TXA
  TAY
  LDA #$FE        ; Y position offscreen
  STA $0200, Y
  INX
  INX
  INX
  INX
  CPX #$00        ; Stop when we've wrapped around (256 bytes)
  BNE @hide_loop
  
  RTS
.endproc

; Interrupt vectors
.segment "VECTORS"
.addr nmi_handler, reset_handler, irq_handler

; CHR-ROM data - Include the Christine sprites
.segment "CHARS"
.incbin "/home/sparkydev/.nes_asset_wizard/exports/playertest1/player/christine_chr.bin"
