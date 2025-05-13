; NES Demo with Arkista's Ring-style UI elements
.segment "HEADER"
  .byte $4E, $45, $53, $1A  ; "NES" followed by MS-DOS EOF
  .byte 1                    ; 1 x 16KB PRG ROM
  .byte 1                    ; 1 x 8KB CHR ROM
  .byte $01                  ; Mapper 0, vertical mirroring
  .byte $00                  ; Mapper 0, playchoice, etc.
  .byte $00                  ; No PRG RAM
  .byte $00                  ; NTSC format
  .byte $00
  .byte $00, $00, $00, $00, $00  ; Filler bytes

; Constants
PPU_CTRL   = $2000
PPU_MASK   = $2001
PPU_STATUS = $2002
PPU_ADDR   = $2006
PPU_DATA   = $2007
PPU_SCROLL = $2005

; Define variables in zero page
.segment "ZEROPAGE"
temp1:         .res 1
temp2:         .res 1
frame_counter: .res 1
ppu_ctrl_val:  .res 1  ; Current PPU_CTRL value

; Main code
.segment "CODE"
reset:
  sei        ; Disable IRQs
  cld        ; Disable decimal mode
  
  ; Setup stack
  ldx #$FF
  txs
  
  ; Disable PPU
  ldx #$00
  stx PPU_CTRL
  stx PPU_MASK
  stx ppu_ctrl_val
  
  ; Initialize frame counter
  stx frame_counter
  
  ; First wait for vblank
  bit PPU_STATUS
vblank_wait1:
  bit PPU_STATUS
  bpl vblank_wait1
  
  ; Clear RAM
  ldx #$00
clear_ram:
  lda #$00
  sta $0000, x
  sta $0100, x
  sta $0300, x
  sta $0400, x
  sta $0500, x
  sta $0600, x
  sta $0700, x
  lda #$FE
  sta $0200, x
  inx
  bne clear_ram
  
  ; Second wait for vblank
  bit PPU_STATUS
vblank_wait2:
  bit PPU_STATUS
  bpl vblank_wait2
  
  ; Initial setup complete
  
  ; Setup palettes
  lda #$3F
  sta PPU_ADDR
  lda #$00
  sta PPU_ADDR
  
  ; Background palette (simple grayscale for now)
  ldx #$00
load_palettes:
  lda palettes, x
  sta PPU_DATA
  inx
  cpx #$20
  bne load_palettes
  
  ; Clear the nametable
  lda #$20
  sta PPU_ADDR
  lda #$00
  sta PPU_ADDR
  
  ldx #$00
  ldy #$04      ; 4 pages (1024 bytes)
clear_nametable:
  lda #$00      ; Empty tile
  sta PPU_DATA
  inx
  bne clear_nametable
  dey
  bne clear_nametable
  
  ; Draw a title
  lda #$21
  sta PPU_ADDR
  lda #$4B      ; Position for centered title (approx middle)
  sta PPU_ADDR
  
  ldx #$00
draw_title:
  lda title_text, x
  beq title_done
  sta PPU_DATA
  inx
  bne draw_title
title_done:
  
  ; Draw a box border (Arkista-style)
  jsr draw_box
  
  ; Reset scroll
  lda #$00
  sta PPU_SCROLL
  sta PPU_SCROLL
  
  ; Enable rendering
  lda #%10010000  ; Enable NMI, use background pattern table 0
  sta ppu_ctrl_val
  sta PPU_CTRL
  lda #%00011110  ; Show background and sprites
  sta PPU_MASK
  
forever:
  ; Main loop - do nothing for now, just wait for NMI
  jmp forever

; Draw a decorative box
draw_box:
  ; Top-left corner at X=8, Y=8, width=16, height=8
  
  ; Top-left corner
  lda #$20
  sta PPU_ADDR
  lda #$88  ; Y=8, X=8
  sta PPU_ADDR
  lda #$0A  ; Top-left corner tile
  sta PPU_DATA
  
  ; Top edge
  ldx #14   ; Width-2
top_edge:
  lda #$0E  ; Horizontal edge tile
  sta PPU_DATA
  dex
  bne top_edge
  
  ; Top-right corner
  lda #$0B  ; Top-right corner tile
  sta PPU_DATA
  
  ; Left and right edges + middle (6 rows)
  ldx #6    ; Height-2
  ldy #$A8  ; Starting position for 2nd row
draw_row:
  lda #$20
  sta PPU_ADDR
  tya       ; Y position
  sta PPU_ADDR
  
  ; Left edge
  lda #$0F  ; Vertical edge tile
  sta PPU_DATA
  
  ; Middle (empty)
  lda #$00  ; Empty tile
  stx temp1 ; Save X
  ldx #14   ; Width-2
middle:
  sta PPU_DATA
  dex
  bne middle
  ldx temp1 ; Restore X
  
  ; Right edge
  lda #$0F  ; Vertical edge tile
  sta PPU_DATA
  
  ; Next row
  tya
  clc
  adc #$20  ; Add 32 to move to next row
  tay
  
  dex
  bne draw_row
  
  ; Bottom-left corner
  lda #$20
  sta PPU_ADDR
  lda #$E8  ; Bottom row position
  sta PPU_ADDR
  lda #$0C  ; Bottom-left corner tile
  sta PPU_DATA
  
  ; Bottom edge
  ldx #14   ; Width-2
bottom_edge:
  lda #$0E  ; Horizontal edge tile
  sta PPU_DATA
  dex
  bne bottom_edge
  
  ; Bottom-right corner
  lda #$0D  ; Bottom-right corner tile
  sta PPU_DATA
  
  rts

; NMI handler - called on vblank
nmi:
  ; Save registers
  pha
  txa
  pha
  tya
  pha
  
  ; Increment frame counter
  inc frame_counter
  
  ; Copy sprites from RAM to PPU OAM
  lda #$00
  sta $2003
  lda #$02
  sta $4014
  
  ; Reset scroll
  lda #$00
  sta PPU_SCROLL
  sta PPU_SCROLL
  
  ; Set PPU_CTRL from our variable
  lda ppu_ctrl_val
  sta PPU_CTRL
  
  ; Restore registers
  pla
  tay
  pla
  tax
  pla
  
  rti

; IRQ handler (not used)
irq:
  rti

; Data
palettes:
  ; Background palettes
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  ; Sprite palettes
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black
  .byte $0F, $30, $10, $00   ; Black, White, Gray, Black

title_text:
  ; Simple "CRAVEN CAVERNS" title - using raw tile indices
  .byte $0C, $12, $01, $16, $05, $0E, $00, $03, $01, $16, $05, $12, $0E, $13, $00
  
; Interrupt vectors
.segment "VECTORS"
  .word nmi
  .word reset
  .word irq

; Character graphics data
.segment "CHARS"
  ; Tile 0: Empty
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tiles 1-9: Letters (A-I)
  ; A
  .byte $18, $24, $42, $42, $7E, $42, $42, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; B
  .byte $7C, $42, $42, $7C, $42, $42, $7C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; C
  .byte $3C, $42, $40, $40, $40, $42, $3C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; D
  .byte $78, $44, $42, $42, $42, $44, $78, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; E
  .byte $7E, $40, $40, $7C, $40, $40, $7E, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; F
  .byte $7E, $40, $40, $7C, $40, $40, $40, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; G
  .byte $3C, $42, $40, $4E, $42, $42, $3C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; H
  .byte $42, $42, $42, $7E, $42, $42, $42, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; I
  .byte $3E, $08, $08, $08, $08, $08, $3E, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tiles 10-15: Box elements (Arkista-style)
  ; Tile 10: Top-left corner
  .byte $3C, $7E, $E7, $CF, $CF, $CF, $CF, $CF
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Tile 11: Top-right corner
  .byte $3C, $7E, $E7, $F3, $F3, $F3, $F3, $F3
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Tile 12: Bottom-left corner
  .byte $CF, $CF, $CF, $CF, $CF, $E7, $7E, $3C
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Tile 13: Bottom-right corner
  .byte $F3, $F3, $F3, $F3, $F3, $E7, $7E, $3C
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Tile 14: Horizontal border
  .byte $FF, $FF, $00, $00, $00, $00, $FF, $FF
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Tile 15: Vertical border
  .byte $C3, $C3, $C3, $C3, $C3, $C3, $C3, $C3
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tiles 16-27: More Letters (J-U)
  ; J
  .byte $02, $02, $02, $02, $42, $42, $3C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; K
  .byte $44, $48, $50, $60, $50, $48, $44, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; L
  .byte $40, $40, $40, $40, $40, $40, $7E, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; M
  .byte $82, $C6, $AA, $92, $82, $82, $82, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; N
  .byte $42, $62, $52, $4A, $46, $42, $42, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; O
  .byte $3C, $42, $42, $42, $42, $42, $3C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; P
  .byte $7C, $42, $42, $7C, $40, $40, $40, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Q
  .byte $3C, $42, $42, $42, $5A, $66, $3D, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; R
  .byte $7C, $42, $42, $7C, $50, $48, $44, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; S
  .byte $3C, $42, $40, $3C, $02, $42, $3C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; T
  .byte $7F, $08, $08, $08, $08, $08, $08, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; U
  .byte $42, $42, $42, $42, $42, $42, $3C, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tiles 26-31: More Letters (V-Z) and special characters
  ; V
  .byte $41, $41, $41, $41, $22, $14, $08, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; W
  .byte $82, $82, $82, $82, $92, $AA, $44, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; X
  .byte $41, $22, $14, $08, $14, $22, $41, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Y
  .byte $41, $22, $14, $08, $08, $08, $08, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Z
  .byte $7F, $02, $04, $08, $10, $20, $7F, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  ; Space
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Fill the rest of CHR ROM with zeros (reduced to avoid overflow)
  .res 7648, $00
