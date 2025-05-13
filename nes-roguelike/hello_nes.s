;
; Simple "Hello World" demo for NES
; guaranteed to display something visible
;

.segment "HEADER"
  .byte $4E,$45,$53,$1A  ; "NES" followed by EOF
  .byte $01              ; 1 x 16k PRG
  .byte $01              ; 1 x 8k CHR
  .byte $00              ; mapper 0, horizontal mirroring
  .byte $00,$00,$00,$00,$00,$00,$00,$00

.segment "ZEROPAGE"
nmi_ready:       .res 1
nmi_count:       .res 1

.segment "CODE"
RESET:
  SEI             ; disable IRQs
  CLD             ; disable decimal mode
  LDX #$40
  STX $4017       ; disable APU frame IRQ
  LDX #$FF
  TXS             ; setup stack
  INX             ; X = 0
  STX $2000       ; disable NMI
  STX $2001       ; disable rendering
  STX $4010       ; disable DMC IRQs

  ; wait for first vblank
vblankwait1:
  BIT $2002
  BPL vblankwait1

  ; clear all RAM to 0
  LDA #$00
clear_memory:
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

  ; wait for second vblank
vblankwait2:
  BIT $2002
  BPL vblankwait2

  ; VRAM address increment per CPU read/write = 1
  ; Sprite pattern table = 0 ($0000)
  ; Background pattern table = 1 ($1000)
  ; Sprite size = 8x8
  ; NMI enable
  LDA #%10010000
  STA $2000

  ; Set palette colors
  LDX #$3F
  STX $2006
  LDX #$00
  STX $2006
load_palettes:
  LDA palettes, X
  STA $2007
  INX
  CPX #$20        ; 32 palette entries
  BNE load_palettes

  ; Write a message to the first nametable
  LDA #$20    ; nametable 0 begins at PPU $2000
  STA $2006
  LDA #$61    ; offset for 2nd row, 1st column
  STA $2006

  ; Write "HELLO, WORLD!" text
  LDX #$00
write_text:
  LDA hello_text, X
  BEQ done_text   ; if we hit the null terminator
  STA $2007
  INX
  JMP write_text
done_text:

  ; Turn on screen
  LDA #%00011110  ; enable sprites, enable background, no clipping on left side
  STA $2001

  ; Set scroll
  LDA #$00
  STA $2005
  STA $2005

  ; Initialize NMI handling
  LDA #$00
  STA nmi_ready
  STA nmi_count

forever:
  ; Main loop that does nothing but wait for NMIs
  JMP forever

NMI:
  ; Save registers
  PHA
  TXA
  PHA
  TYA
  PHA

  ; Increment NMI counter
  INC nmi_count

  ; Set scroll and PPU base address
  LDA #$00
  STA $2003  ; OAM address = 0
  STA $2005  ; X scroll = 0
  STA $2005  ; Y scroll = 0
  LDA #%10010000  ; enable NMI, sprites from Pattern Table 0, background from Pattern Table 1
  STA $2000

  ; Set NMI as handled
  LDA #$01
  STA nmi_ready

  ; Restore registers and return
  PLA
  TAY
  PLA
  TAX
  PLA
  RTI

IRQ:
  RTI  ; Not used

; Data
hello_text:
  .byte "HELLO, WORLD!", $00  ; Null-terminated string

; Palettes
palettes:
  ; Background palettes
  .byte $0F,$31,$32,$33,$0F,$35,$36,$37,$0F,$39,$3A,$3B,$0F,$3D,$3E,$3F
  ; Sprite palettes
  .byte $0F,$1C,$15,$14,$0F,$02,$38,$3C,$0F,$1C,$15,$14,$0F,$02,$38,$3C

.segment "CHARS"
  ; Character data
  ; First 16 8x8 tiles
  ; 0: Blank/space
  .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
  
  ; 1-26: English alphabet (A-Z)
  ; A
  .byte $00,$00,$18,$24,$42,$7E,$42,$42,$00,$00,$00,$00,$00,$00,$00,$00
  ; B
  .byte $00,$00,$7C,$42,$7C,$42,$42,$7C,$00,$00,$00,$00,$00,$00,$00,$00
  ; C
  .byte $00,$00,$3C,$42,$40,$40,$42,$3C,$00,$00,$00,$00,$00,$00,$00,$00
  ; D
  .byte $00,$00,$78,$44,$42,$42,$44,$78,$00,$00,$00,$00,$00,$00,$00,$00
  ; E
  .byte $00,$00,$7E,$40,$7C,$40,$40,$7E,$00,$00,$00,$00,$00,$00,$00,$00
  ; F
  .byte $00,$00,$7E,$40,$7C,$40,$40,$40,$00,$00,$00,$00,$00,$00,$00,$00
  ; G
  .byte $00,$00,$3C,$42,$40,$4E,$42,$3C,$00,$00,$00,$00,$00,$00,$00,$00
  ; H
  .byte $00,$00,$42,$42,$7E,$42,$42,$42,$00,$00,$00,$00,$00,$00,$00,$00
  ; I
  .byte $00,$00,$3E,$08,$08,$08,$08,$3E,$00,$00,$00,$00,$00,$00,$00,$00
  ; J
  .byte $00,$00,$02,$02,$02,$42,$42,$3C,$00,$00,$00,$00,$00,$00,$00,$00
  ; K
  .byte $00,$00,$44,$48,$70,$48,$44,$42,$00,$00,$00,$00,$00,$00,$00,$00
  ; L
  .byte $00,$00,$40,$40,$40,$40,$40,$7E,$00,$00,$00,$00,$00,$00,$00,$00
  ; M
  .byte $00,$00,$42,$66,$5A,$42,$42,$42,$00,$00,$00,$00,$00,$00,$00,$00
  ; N
  .byte $00,$00,$42,$62,$52,$4A,$46,$42,$00,$00,$00,$00,$00,$00,$00,$00
  ; O
  .byte $00,$00,$3C,$42,$42,$42,$42,$3C,$00,$00,$00,$00,$00,$00,$00,$00
  ; P
  .byte $00,$00,$7C,$42,$42,$7C,$40,$40,$00,$00,$00,$00,$00,$00,$00,$00
  ; Q
  .byte $00,$00,$3C,$42,$42,$42,$52,$3C,$04,$00,$00,$00,$00,$00,$00,$00
  ; R
  .byte $00,$00,$7C,$42,$42,$7C,$48,$44,$00,$00,$00,$00,$00,$00,$00,$00
  ; S
  .byte $00,$00,$3C,$40,$3C,$02,$42,$3C,$00,$00,$00,$00,$00,$00,$00,$00
  ; T
  .byte $00,$00,$7F,$08,$08,$08,$08,$08,$00,$00,$00,$00,$00,$00,$00,$00
  ; U
  .byte $00,$00,$42,$42,$42,$42,$42,$3C,$00,$00,$00,$00,$00,$00,$00,$00
  ; V
  .byte $00,$00,$42,$42,$42,$42,$24,$18,$00,$00,$00,$00,$00,$00,$00,$00
  ; W
  .byte $00,$00,$42,$42,$42,$42,$5A,$24,$00,$00,$00,$00,$00,$00,$00,$00
  ; X
  .byte $00,$00,$42,$24,$18,$18,$24,$42,$00,$00,$00,$00,$00,$00,$00,$00
  ; Y
  .byte $00,$00,$22,$22,$14,$08,$08,$08,$00,$00,$00,$00,$00,$00,$00,$00
  ; Z
  .byte $00,$00,$7E,$04,$08,$10,$20,$7E,$00,$00,$00,$00,$00,$00,$00,$00
  
  ; 27-31: Special characters
  ; ,
  .byte $00,$00,$00,$00,$00,$00,$10,$10,$20,$00,$00,$00,$00,$00,$00,$00
  ; .
  .byte $00,$00,$00,$00,$00,$00,$00,$18,$18,$00,$00,$00,$00,$00,$00,$00
  ; !
  .byte $00,$00,$10,$10,$10,$10,$00,$10,$00,$00,$00,$00,$00,$00,$00,$00
  ; ?
  .byte $00,$00,$3C,$42,$02,$04,$08,$00,$08,$00,$00,$00,$00,$00,$00,$00
  ; (blank)
  .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
  
  ; Fill the remainder with a pattern (reduced to fit within 8KB)
  .res 7680, $FF

.segment "VECTORS"
  .word NMI
  .word RESET
  .word IRQ
