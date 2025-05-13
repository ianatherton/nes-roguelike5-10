.include "nes.inc"

.segment "HEADER"
  .byte "NES", $1A
  .byte 1            ; 1 x 16KB PRG ROM
  .byte 1            ; 1 x 8KB CHR ROM
  .byte $00          ; mapper 0, vertical mirroring
  .byte $00
  .byte $00
  .byte $00
  .byte $00
  .byte $00, $00, $00, $00, $00  ; filler bytes

.segment "CODE"

; Set up the CPU and PPU
.proc reset
  sei           ; Disable IRQs
  cld           ; Clear decimal mode
  ldx #$40
  stx $4017     ; Disable APU frame IRQ
  ldx #$ff      ; Set up stack pointer
  txs
  inx           ; X = 0
  stx PPUCTRL   ; Disable NMI
  stx PPUMASK   ; Disable rendering
  stx $4010     ; Disable DMC IRQs

  ; First wait for vblank to make sure PPU is ready
vblankwait1:
  bit PPUSTATUS
  bpl vblankwait1

  ; Initialize RAM to 0
  ldx #0
clear_ram:
  lda #$00
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
vblankwait2:
  bit PPUSTATUS
  bpl vblankwait2

  ; Set palette colors
  lda PPUSTATUS   ; Clear the status register
  lda #$3F
  sta PPUADDR
  lda #$00
  sta PPUADDR

  ; Load all 32 palette entries
  ldx #$00
load_palettes:
  lda palettes, x
  sta PPUDATA
  inx
  cpx #$20
  bne load_palettes

  ; Write a simple nametable
  lda PPUSTATUS   ; Reset PPU address latch
  lda #$20        ; Set PPU address to $2000 (start of nametable)
  sta PPUADDR
  lda #$00
  sta PPUADDR

  ; Fill the first few rows with a pattern
  ldx #$00
  ldy #$00
fill_nametable:
  txa             ; Use X as the tile number
  and #$0F        ; Keep it in range 0-15
  sta PPUDATA
  inx
  iny
  cpy #128        ; Just fill the first 4 rows
  bne fill_nametable

  ; Draw a simple box
  jsr draw_box

  ; Enable rendering
  lda #%10010000  ; Enable NMI, sprites from pattern table 0, background from pattern table 0
  sta PPUCTRL
  lda #%00011110  ; Enable sprites, enable background, no clipping on left side
  sta PPUMASK

  ; Set scroll registers
  lda #$00
  sta PPUSCROLL
  sta PPUSCROLL

  ; Initialize done, enter an infinite loop
forever:
  jmp forever
.endproc

; Draw a simple box
.proc draw_box
  ; Set PPU address to position (3,3) on nametable
  lda PPUSTATUS
  lda #$20
  sta PPUADDR
  lda #$63      ; 3 rows down, 3 tiles in
  sta PPUADDR

  ; Draw top of box
  lda #$01      ; Top-left corner
  sta PPUDATA
  ldx #8        ; Width of box - 2 (for corners)
  lda #$02      ; Horizontal line
top_line:
  sta PPUDATA
  dex
  bne top_line
  lda #$03      ; Top-right corner
  sta PPUDATA

  ; Set PPU address to next row
  lda PPUSTATUS
  lda #$20
  sta PPUADDR
  lda #$83      ; 4 rows down, 3 tiles in
  sta PPUADDR

  ; Draw middle of box
  ldx #5        ; Height of box - 2 (for top and bottom)
draw_row:
  lda #$04      ; Vertical line
  sta PPUDATA
  
  ; Draw spaces for the interior
  ldy #8        ; Width of box - 2 (for sides)
  lda #$00      ; Empty tile
interior:
  sta PPUDATA
  dey
  bne interior
  
  lda #$04      ; Vertical line
  sta PPUDATA
  
  ; Move to next row (add 32 = width of nametable)
  txa
  pha           ; Save X
  
  lda PPUSTATUS
  lda #$20
  sta PPUADDR
  pla           ; Restore X
  pha           ; And save again
  
  ; Calculate row: $83 + X * $20
  tay
  lda #$83
row_calc:
  cpy #0
  beq row_done
  clc
  adc #$20
  dey
  jmp row_calc
row_done:
  sta PPUADDR
  
  pla           ; Restore X
  dex
  bne draw_row
  
  ; Set PPU address for bottom row
  lda PPUSTATUS
  lda #$20
  sta PPUADDR
  lda #$E3      ; 7 rows down, 3 tiles in
  sta PPUADDR
  
  ; Draw bottom of box
  lda #$05      ; Bottom-left corner
  sta PPUDATA
  ldx #8        ; Width of box - 2 (for corners)
  lda #$02      ; Horizontal line
bottom_line:
  sta PPUDATA
  dex
  bne bottom_line
  lda #$06      ; Bottom-right corner
  sta PPUDATA
  
  rts
.endproc

; NMI handler
.proc nmi
  ; Save registers
  pha
  txa
  pha
  tya
  pha

  ; Update game state here
  
  ; Reset scroll
  lda #$00
  sta PPUSCROLL
  sta PPUSCROLL

  ; Restore registers and return
  pla
  tay
  pla
  tax
  pla
  rti
.endproc

; Data section
.segment "RODATA"
palettes:
  ; Background palettes
  .byte $0F, $30, $32, $33  ; Black, White, Light green, Light blue
  .byte $0F, $04, $14, $24  ; Black, Pink, Light pink, Light gray
  .byte $0F, $09, $19, $29  ; Black, Green, Light green, White
  .byte $0F, $02, $12, $22  ; Black, Blue, Light blue, Gray
  
  ; Sprite palettes
  .byte $0F, $16, $26, $36  ; Black, Red, Light red, White 
  .byte $0F, $18, $28, $38  ; Black, Yellow, Light yellow, White
  .byte $0F, $1A, $2A, $3A  ; Black, Green, Light green, White
  .byte $0F, $1C, $2C, $3C  ; Black, Light blue, Light cyan, White

; Character ROM data
.segment "CHARS"
; First 16 tiles are for the UI
  ; Tile 0: Empty/space
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 1: Top-left corner
  .byte $3C, $7E, $E7, $C3, $C3, $C3, $C3, $C3
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 2: Horizontal line
  .byte $FF, $FF, $00, $00, $00, $00, $FF, $FF
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 3: Top-right corner
  .byte $3C, $7E, $E7, $C3, $C3, $C3, $C3, $C3
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 4: Vertical line
  .byte $C3, $C3, $C3, $C3, $C3, $C3, $C3, $C3
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 5: Bottom-left corner
  .byte $C3, $C3, $C3, $C3, $C3, $E7, $7E, $3C
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 6: Bottom-right corner
  .byte $C3, $C3, $C3, $C3, $C3, $E7, $7E, $3C
  .byte $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Tile 7-15: Unused blank tiles
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  .byte $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00, $00
  
  ; Patterns for tiles 16-255
  ; Fill remaining space with a test pattern
  .byte $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00, $FF, $00
  ; Fill the remainder with a repeating pattern
  .res 7904, $FF

; Set interrupt vectors
.segment "VECTORS"
  .word nmi
  .word reset
  .word 0
