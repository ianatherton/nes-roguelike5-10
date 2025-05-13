; Arkista's Ring Sprite Test ROM
; Displays sprites extracted from Arkista's Ring

.segment "HEADER"
  .byte "NES", $1A       ; iNES header identifier
  .byte 2                ; 2x 16KB PRG-ROM banks
  .byte 1                ; 1x 8KB CHR-ROM bank
  .byte $01, $00         ; Mapper 0, vertical mirroring
  .byte $00, $00, $00, $00, $00, $00, $00, $00 ; Padding

.segment "CHARS"
; Import character data directly from Arkista's Ring
; We'll use the first bank for this test
.incbin "assets/reference/arkistas_ring.nes", 16, 8192  ; Skip 16-byte header, read 8KB

.segment "CODE"
; NES Hardware Registers
PPU_CTRL        = $2000
PPU_MASK        = $2001
PPU_STATUS      = $2002
PPU_OAM_ADDR    = $2003
PPU_OAM_DATA    = $2004
PPU_SCROLL      = $2005
PPU_ADDR        = $2006
PPU_DATA        = $2007
OAM_DMA         = $4014

; Game Variables
.segment "ZEROPAGE"
frame_counter:  .res 1  ; Frame counter for animation

; Sprite data stored in RAM at $0200-$02FF
.segment "OAM"
  .res 256

.segment "BSS"
game_state:     .res 1  ; Current game state

.segment "CODE"
reset:
  SEI           ; Disable interrupts
  CLD           ; Clear decimal mode
  LDX #$40
  STX $4017     ; Disable APU frame IRQ
  LDX #$FF
  TXS           ; Set up stack
  INX           ; X = 0
  STX PPU_CTRL  ; Disable NMI
  STX PPU_MASK  ; Disable rendering
  STX $4010     ; Disable DMC IRQs

  ; Wait for first vblank
wait_vblank1:
  BIT PPU_STATUS
  BPL wait_vblank1

  ; Clear RAM
  LDA #0
clear_ram:
  STA $0000, X
  STA $0100, X
  STA $0300, X
  STA $0400, X
  STA $0500, X
  STA $0600, X
  STA $0700, X
  STA $0200, X  ; Also clear sprite memory
  INX
  BNE clear_ram

  ; Wait for second vblank
wait_vblank2:
  BIT PPU_STATUS
  BPL wait_vblank2

  ; Initialize game variables
  LDA #0
  STA frame_counter
  STA game_state

  ; Set up sprite data - player character and some items
  
  ; Sprite 0 - Player (X position, Y position, Tile index, Attributes)
  ; X and Y positions should be in the middle of the screen
  LDA #$80      ; X position (center of screen)
  STA $0200
  LDA #$80      ; Y position (center of screen)
  STA $0201
  LDA #$25      ; Tile index - a character sprite from Arkista's Ring
  STA $0202
  LDA #$00      ; Attributes - no flip, palette 0
  STA $0203
  
  ; Sprite 1 - Another sprite
  LDA #$60      ; X position
  STA $0204
  LDA #$80      ; Y position
  STA $0205
  LDA #$26      ; Tile index - another character sprite
  STA $0206
  LDA #$00      ; Attributes
  STA $0207
  
  ; Sprite 2 - Another sprite
  LDA #$A0      ; X position
  STA $0208
  LDA #$80      ; Y position
  STA $0209
  LDA #$27      ; Tile index - another sprite
  STA $020A
  LDA #$00      ; Attributes
  STA $020B
  
  ; Sprite 3 - Item
  LDA #$80      ; X position
  STA $020C
  LDA #$A0      ; Y position
  STA $020D
  LDA #$60      ; Tile index - likely an item sprite
  STA $020E
  LDA #$01      ; Attributes - palette 1
  STA $020F

  ; Set up palette
  LDA PPU_STATUS   ; Reset PPU latch
  LDA #$3F
  STA PPU_ADDR
  LDA #$00
  STA PPU_ADDR
  
  ; Background palettes (4 palettes of 4 colors each)
  LDA #$0F        ; Black
  STA PPU_DATA
  LDA #$30        ; White
  STA PPU_DATA
  LDA #$16        ; Red
  STA PPU_DATA
  LDA #$1A        ; Green
  STA PPU_DATA
  
  ; Second palette
  LDA #$0F
  STA PPU_DATA
  LDA #$11        ; Blue
  STA PPU_DATA
  LDA #$2A        ; Yellow
  STA PPU_DATA
  LDA #$17        ; Brown
  STA PPU_DATA
  
  ; Third and fourth background palettes
  LDX #8
fill_bg_palette:
  LDA #$0F
  STA PPU_DATA
  DEX
  BNE fill_bg_palette
  
  ; Sprite palettes (4 palettes of 4 colors each)
  LDA #$0F        ; Black (transparent)
  STA PPU_DATA
  LDA #$16        ; Red
  STA PPU_DATA
  LDA #$2A        ; Yellow
  STA PPU_DATA
  LDA #$30        ; White
  STA PPU_DATA
  
  ; Second sprite palette
  LDA #$0F
  STA PPU_DATA
  LDA #$11        ; Blue
  STA PPU_DATA
  LDA #$30        ; White
  STA PPU_DATA
  LDA #$27        ; Pink
  STA PPU_DATA
  
  ; Fill remaining sprite palettes
  LDX #8
fill_sprite_palette:
  LDA #$0F
  STA PPU_DATA
  DEX
  BNE fill_sprite_palette

  ; Clear nametable
  LDA PPU_STATUS   ; Reset PPU latch
  LDA #$20
  STA PPU_ADDR
  LDA #$00
  STA PPU_ADDR
  
  LDX #$00
  LDA #$00
clear_nametable:
  STA PPU_DATA
  INX
  BNE clear_nametable
  LDX #$00
clear_nametable2:
  STA PPU_DATA
  INX
  BNE clear_nametable2
  LDX #$00
clear_nametable3:
  STA PPU_DATA
  INX
  BNE clear_nametable3
  LDX #$00
clear_nametable4:
  STA PPU_DATA
  INX
  CPX #$C0        ; Clear remaining bytes to complete nametable
  BNE clear_nametable4
  
  ; Write title text
  LDA PPU_STATUS   ; Reset PPU latch
  LDA #$21
  STA PPU_ADDR
  LDA #$4A         ; Position (line ~10, column ~10)
  STA PPU_ADDR
  
  LDX #$00
write_title:
  LDA title_text, X
  BEQ done_title
  STA PPU_DATA
  INX
  JMP write_title
done_title:

  ; Write subtitle
  LDA PPU_STATUS   ; Reset PPU latch
  LDA #$21
  STA PPU_ADDR
  LDA #$8C         ; Position (line ~12, column ~12)
  STA PPU_ADDR
  
  LDX #$00
write_subtitle:
  LDA subtitle_text, X
  BEQ done_subtitle
  STA PPU_DATA
  INX
  JMP write_subtitle
done_subtitle:

  ; Enable rendering
  LDA #%10010000   ; Enable NMI, use first pattern table for sprites
  STA PPU_CTRL
  LDA #%00011110   ; Enable sprites and background
  STA PPU_MASK
  
  ; Reset scroll position
  LDA #$00
  STA PPU_SCROLL
  STA PPU_SCROLL
  
  ; Enable NMI
  LDA #%10010000
  STA PPU_CTRL

; Main loop
forever:
  JMP forever

; NMI interrupt handler
nmi:
  ; Save registers
  PHA
  TXA
  PHA
  TYA
  PHA
  
  ; Sprite DMA transfer from $0200-$02FF to PPU OAM
  LDA #$00
  STA PPU_OAM_ADDR
  LDA #$02    ; OAM data starts at $0200
  STA OAM_DMA
  
  ; Increment frame counter
  INC frame_counter
  
  ; Animate sprite based on frame
  LDA frame_counter
  AND #$10      ; Change every 16 frames
  BEQ use_alt_sprite

  LDA #$25
  JMP set_sprite
  
use_alt_sprite:
  LDA #$26
  
set_sprite:
  STA $0202     ; Update player sprite tile

  ; Reset scroll position
  LDA #$00
  STA PPU_SCROLL
  STA PPU_SCROLL
  
  ; Restore registers
  PLA
  TAY
  PLA
  TAX
  PLA
  
  RTI

; Title text data
title_text:
  .byte "CRAVEN CAVERNS", $00

; Subtitle text data
subtitle_text:
  .byte "ARKISTA SPRITES", $00

; Interrupt vectors
.segment "VECTORS"
  .word nmi      ; NMI vector
  .word reset    ; Reset vector
  .word 0        ; IRQ vector (unused)
