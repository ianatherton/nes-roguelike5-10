#!/bin/bash
# Build script for a simple NES test ROM

mkdir -p build

# Create a minimal assembly-only NES ROM
cat > build/test.s << 'EOF'
; Simple NES Test ROM

.segment "HEADER"
  .byte "NES", $1A       ; iNES header
  .byte 2                ; 2x 16KB PRG-ROM banks
  .byte 1                ; 1x 8KB CHR-ROM bank
  .byte $01, $00         ; Mapper 0, vertical mirroring
  .byte $00, $00, $00, $00, $00, $00, $00, $00 ; Padding

.segment "CHARS"
; Character data
; ASCII character set (starting with space at $20)
  .byte $00,$00,$00,$00,$00,$00,$00,$00 ; Space
  .byte $18,$18,$18,$18,$18,$00,$18,$00 ; !
  .byte $66,$66,$00,$00,$00,$00,$00,$00 ; "
  .byte $6C,$6C,$FE,$6C,$FE,$6C,$6C,$00 ; #
  ; ... more character data would go here

; A-Z characters
  .byte $3C,$66,$66,$7E,$66,$66,$66,$00 ; A
  .byte $7C,$66,$66,$7C,$66,$66,$7C,$00 ; B
  .byte $3C,$66,$60,$60,$60,$66,$3C,$00 ; C
  .byte $78,$6C,$66,$66,$66,$6C,$78,$00 ; D
  .byte $7E,$60,$60,$78,$60,$60,$7E,$00 ; E
  .byte $7E,$60,$60,$78,$60,$60,$60,$00 ; F
  .byte $3C,$66,$60,$6E,$66,$66,$3E,$00 ; G
  .byte $66,$66,$66,$7E,$66,$66,$66,$00 ; H
  .byte $3C,$18,$18,$18,$18,$18,$3C,$00 ; I
  .byte $06,$06,$06,$06,$66,$66,$3C,$00 ; J
  .byte $66,$6C,$78,$70,$78,$6C,$66,$00 ; K
  .byte $60,$60,$60,$60,$60,$60,$7E,$00 ; L
  .byte $63,$77,$7F,$6B,$63,$63,$63,$00 ; M
  .byte $66,$76,$7E,$7E,$6E,$66,$66,$00 ; N
  .byte $3C,$66,$66,$66,$66,$66,$3C,$00 ; O
  .byte $7C,$66,$66,$7C,$60,$60,$60,$00 ; P
  .byte $3C,$66,$66,$66,$6A,$6C,$36,$00 ; Q
  .byte $7C,$66,$66,$7C,$6C,$66,$66,$00 ; R
  .byte $3C,$66,$60,$3C,$06,$66,$3C,$00 ; S
  .byte $7E,$18,$18,$18,$18,$18,$18,$00 ; T
  .byte $66,$66,$66,$66,$66,$66,$3C,$00 ; U
  .byte $66,$66,$66,$66,$3C,$3C,$18,$00 ; V
  .byte $63,$63,$63,$6B,$7F,$77,$63,$00 ; W
  .byte $66,$66,$3C,$18,$3C,$66,$66,$00 ; X
  .byte $66,$66,$66,$3C,$18,$18,$18,$00 ; Y
  .byte $7E,$06,$0C,$18,$30,$60,$7E,$00 ; Z

; Some simple graphics tiles
  .byte $00,$00,$00,$00,$00,$00,$00,$00 ; Empty tile
  .byte $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF ; Full tile
  .byte $55,$AA,$55,$AA,$55,$AA,$55,$AA ; Checkerboard
  .byte $18,$3C,$7E,$FF,$FF,$7E,$3C,$18 ; Diamond

.segment "CODE"
reset:
  ; Initialize the NES
  SEI         ; Disable interrupts
  CLD         ; Clear decimal mode
  LDX #$40
  STX $4017   ; Disable APU frame IRQ
  LDX #$FF
  TXS         ; Set up stack
  INX         ; X = 0
  STX $2000   ; Disable NMI
  STX $2001   ; Disable rendering
  STX $4010   ; Disable DMC IRQs

  ; Wait for vblank to make sure PPU is ready
vblankwait1:
  BIT $2002
  BPL vblankwait1

  ; Clear RAM
  LDA #$00
clear_ram:
  STA $0000, X
  STA $0100, X
  STA $0300, X
  STA $0400, X
  STA $0500, X
  STA $0600, X
  STA $0700, X
  LDA #$FE
  STA $0200, X   ; Move all sprites off-screen
  LDA #$00
  INX
  BNE clear_ram

  ; Wait for vblank again
vblankwait2:
  BIT $2002
  BPL vblankwait2

  ; Set the palette
  LDA $2002     ; Reset PPU latch
  LDA #$3F
  STA $2006     ; PPU address = $3F00 (palette)
  LDA #$00
  STA $2006

  ; Background palette (black, white, red, green)
  LDA #$0F      ; Black
  STA $2007
  LDA #$30      ; White
  STA $2007
  LDA #$16      ; Red
  STA $2007
  LDA #$1A      ; Green
  STA $2007

  ; Write text to nametable
  LDA $2002     ; Reset PPU latch
  LDA #$20
  STA $2006     ; PPU address = $2000 (first nametable)
  LDA #$00
  STA $2006

  ; Clear nametable
  LDX #$00
  LDA #$00
clear_nametable:
  STA $2007
  INX
  BNE clear_nametable
  LDX #$00
clear_nametable2:
  STA $2007
  INX
  BNE clear_nametable2
  LDX #$00
clear_nametable3:
  STA $2007
  INX
  BNE clear_nametable3
  LDX #$00
clear_nametable4:
  STA $2007
  INX
  CPX #$C0      ; Clear remaining bytes to complete 960 bytes
  BNE clear_nametable4

  ; Draw "CRAVEN CAVERNS" at line 10, column 10
  LDA $2002     ; Reset PPU latch
  LDA #$21
  STA $2006
  LDA #$4A      ; Nametable address $214A (line 10, column 10)
  STA $2006

  LDX #$00
write_title:
  LDA title_text, X
  BEQ done_title
  STA $2007
  INX
  JMP write_title
done_title:

  ; Draw "TEST ROM" at line 12, column 12
  LDA $2002
  LDA #$21
  STA $2006
  LDA #$8C      ; Nametable address $218C (line 12, column 12)
  STA $2006

  LDX #$00
write_subtitle:
  LDA subtitle_text, X
  BEQ done_subtitle
  STA $2007
  INX
  JMP write_subtitle
done_subtitle:

  ; Enable rendering
  LDA #%10010000  ; Enable NMI, use first pattern table
  STA $2000
  LDA #%00011110  ; Enable sprites and background
  STA $2001

  ; Reset scroll position
  LDA #$00
  STA $2005
  STA $2005

forever:
  JMP forever     ; Infinite loop

nmi:
  ; Update scroll position during NMI
  LDA #$00
  STA $2005
  STA $2005
  RTI

; Title text data
title_text:
  .byte "CRAVEN CAVERNS", $00

; Subtitle text data
subtitle_text:
  .byte "TEST ROM", $00

.segment "VECTORS"
  .word nmi       ; NMI vector
  .word reset     ; Reset vector
  .word 0         ; IRQ vector (unused)
EOF

# Assemble the ROM
ca65 -t nes build/test.s -o build/test.o

# Create linker config file
cat > build/nes.cfg << 'EOF'
MEMORY {
    ZP:     start = $00,    size = $0100, type = rw;
    RAM:    start = $0200,  size = $0600, type = rw;
    HEADER: start = $0000,  size = $0010, type = ro, file = %O, fill = yes;
    PRG:    start = $8000,  size = $8000, type = ro, file = %O, fill = yes;
    CHR:    start = $0000,  size = $2000, type = ro, file = %O, fill = yes;
}

SEGMENTS {
    HEADER:   load = HEADER, type = ro;
    CODE:     load = PRG,    type = ro,  start = $8000;
    CHARS:    load = CHR,    type = ro;
    VECTORS:  load = PRG,    type = ro,  start = $FFFA;
}
EOF

# Link the ROM
ld65 -C build/nes.cfg build/test.o -o build/craven_test.nes

echo "ROM generated at build/craven_test.nes"
echo "Run with: fceux build/craven_test.nes"
