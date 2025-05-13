.segment "HEADER"
.byte "NES", $1a
.byte 1               ; 1 * 16KB PRG ROM
.byte 1               ; 1 * 8KB CHR ROM
.byte $01, $00        ; mapper 0, vertical mirroring

; ---- Hardware registers ----
PPU_CTRL    = $2000
PPU_MASK    = $2001
PPU_STATUS  = $2002
PPU_SCROLL  = $2005
PPU_ADDR    = $2006
PPU_DATA    = $2007
CONTROLLER1 = $4016

; ---- Zero page variables ----
.segment "ZEROPAGE" 
game_state:     .res 1  ; 0 = title, 1 = menu
menu_selection: .res 1  ; Selected menu item

; ---- Main code ----
.segment "CODE"

; NMI handler
.proc nmi
    rti
.endproc

; IRQ handler
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

; Main entry point
.proc reset
    ; Disable interrupts and decimal mode
    sei
    cld
    
    ; Initialize stack
    ldx #$FF
    txs
    
    ; Disable rendering
    lda #$00
    sta PPU_CTRL
    sta PPU_MASK
    
    ; Wait for first vblank
    jsr wait_vblank
    
    ; Clear RAM (zero page, stack page, and RAM)
    lda #$00
    tax
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
    
    ; Initialize variables
    lda #$00
    sta game_state
    sta menu_selection
    
    ; Wait for second vblank
    jsr wait_vblank
    
    ; Draw title screen
    jsr draw_title
    
    ; Set palette
    jsr set_palette
    
    ; Enable rendering
    lda #$90    ; Enable NMI and use Pattern Table 0
    sta PPU_CTRL
    lda #$1E    ; Enable sprites and background
    sta PPU_MASK
    
    ; Reset scroll position
    lda #$00
    sta PPU_SCROLL
    sta PPU_SCROLL
    
    ; Main loop
@loop:
    jmp @loop
.endproc

; Set the palette
.proc set_palette
    ; Set PPU address to palette
    lda #$3F
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Load palette data
    ldx #$00
@loop:
    lda palette, x
    sta PPU_DATA
    inx
    cpx #$20    ; 32 bytes (8 palettes)
    bne @loop
    
    rts
    
palette:
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
.endproc

; Draw the title screen
.proc draw_title
    ; Set PPU address to nametable start
    lda #$20
    sta PPU_ADDR
    lda #$00
    sta PPU_ADDR
    
    ; Clear nametable
    lda #$00    ; Empty tile
    ldx #$00
    ldy #$04    ; 4 pages (1024 bytes)
@clear_loop:
    sta PPU_DATA
    inx
    bne @clear_loop
    dey
    bne @clear_loop
    
    ; Draw title "CRAVEN CAVERNS"
    ; Set PPU address for title (centered on row 10)
    lda #$20
    sta PPU_ADDR
    lda #$CA    ; 10 * 32 + 10
    sta PPU_ADDR
    
    ; Write title
    ldx #$00
@title_loop:
    lda title_text, x
    beq @done_title
    sec
    sbc #$20    ; Convert ASCII to tile index
    sta PPU_DATA
    inx
    bne @title_loop
@done_title:
    
    ; Draw "PRESS START" message
    ; Set PPU address for message (centered on row 20)
    lda #$21
    sta PPU_ADDR
    lda #$4A    ; 20 * 32 + 10
    sta PPU_ADDR
    
    ; Write message
    ldx #$00
@message_loop:
    lda press_start_text, x
    beq @done_message
    sec
    sbc #$20    ; Convert ASCII to tile index
    sta PPU_DATA
    inx
    bne @message_loop
@done_message:
    
    ; Draw a box around the title
    jsr draw_box
    
    rts

title_text:      .byte "CRAVEN CAVERNS", $00
press_start_text: .byte "PRESS START", $00
.endproc

; Draw a decorative box
.proc draw_box
    ; Set PPU address for top-left corner
    lda #$20
    sta PPU_ADDR
    lda #$88    ; 8 * 32 + 8
    sta PPU_ADDR
    
    ; Draw top border
    lda #$0A    ; Top-left corner
    sta PPU_DATA
    lda #$0E    ; Top border
    ldx #$12    ; Width - 2
@top_loop:
    sta PPU_DATA
    dex
    bne @top_loop
    lda #$0B    ; Top-right corner
    sta PPU_DATA
    
    ; Draw sides (10 rows)
    ldx #$0A    ; Height - 2
@side_loop:
    ; Set address for left side
    pha         ; Save A
    txa         ; X to A
    pha         ; Save X
    clc
    adc #$09    ; Row offset (starting at row 9)
    
    ; Multiply by 32 for row offset
    asl a       ; * 2
    asl a       ; * 4
    asl a       ; * 8
    asl a       ; * 16
    asl a       ; * 32
    
    ; Add column offset
    clc
    adc #$08    ; Column 8
    
    ; Set PPU address
    tax         ; Save low byte in X
    lda #$20    ; High byte
    sta PPU_ADDR
    txa         ; Low byte
    sta PPU_ADDR
    
    ; Draw left border
    lda #$0F    ; Left border
    sta PPU_DATA
    
    ; Draw empty space
    lda #$00    ; Empty tile
    ldx #$12    ; Width - 2
@empty_loop:
    sta PPU_DATA
    dex
    bne @empty_loop
    
    ; Draw right border
    lda #$0F    ; Right border
    sta PPU_DATA
    
    ; Restore registers and continue loop
    pla         ; Restore X
    tax
    pla         ; Restore A
    
    dex
    bne @side_loop
    
    ; Draw bottom border
    ; Set PPU address for bottom-left corner
    lda #$21
    sta PPU_ADDR
    lda #$08    ; 19 * 32 + 8
    sta PPU_ADDR
    
    ; Draw bottom border
    lda #$0C    ; Bottom-left corner
    sta PPU_DATA
    lda #$0E    ; Bottom border
    ldx #$12    ; Width - 2
@bottom_loop:
    sta PPU_DATA
    dex
    bne @bottom_loop
    lda #$0D    ; Bottom-right corner
    sta PPU_DATA
    
    rts
.endproc

; Interrupt vectors
.segment "VECTORS"
.word nmi
.word reset
.word irq

; Character data
.segment "CHARS"
; Basic tiles (0-15)
.byte $00,$00,$00,$00,$00,$00,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; Empty tile (0)
.byte $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF, $00,$00,$00,$00,$00,$00,$00,$00 ; Solid tile (1)
.byte $F0,$F0,$F0,$F0,$F0,$F0,$F0,$F0, $00,$00,$00,$00,$00,$00,$00,$00 ; Half tile (2)
.byte $FF,$81,$81,$81,$81,$81,$81,$FF, $00,$00,$00,$00,$00,$00,$00,$00 ; Box outline (3)
.byte $3C,$42,$A5,$81,$A5,$99,$42,$3C, $00,$00,$00,$00,$00,$00,$00,$00 ; Smiley face (4)
.byte $3C,$42,$A5,$81,$99,$A5,$42,$3C, $00,$00,$00,$00,$00,$00,$00,$00 ; Sad face (5)
.byte $18,$3C,$66,$7E,$18,$18,$18,$18, $00,$00,$00,$00,$00,$00,$00,$00 ; Up arrow (6)
.byte $18,$18,$18,$18,$7E,$66,$3C,$18, $00,$00,$00,$00,$00,$00,$00,$00 ; Down arrow (7)
.byte $18,$1C,$1E,$18,$18,$18,$18,$18, $00,$00,$00,$00,$00,$00,$00,$00 ; Right arrow (8)
.byte $18,$18,$18,$18,$18,$78,$38,$18, $00,$00,$00,$00,$00,$00,$00,$00 ; Left arrow (9)

; Box elements (10-15)
; Box top-left
.byte $3C,$7E,$E7,$CF,$CF,$CF,$CF,$CF, $00,$00,$00,$00,$00,$00,$00,$00
; Box top-right
.byte $3C,$7E,$E7,$F3,$F3,$F3,$F3,$F3, $00,$00,$00,$00,$00,$00,$00,$00
; Box bottom-left
.byte $CF,$CF,$CF,$CF,$CF,$E7,$7E,$3C, $00,$00,$00,$00,$00,$00,$00,$00
; Box bottom-right
.byte $F3,$F3,$F3,$F3,$F3,$E7,$7E,$3C, $00,$00,$00,$00,$00,$00,$00,$00
; Box horizontal
.byte $FF,$FF,$00,$00,$00,$00,$FF,$FF, $00,$00,$00,$00,$00,$00,$00,$00
; Box vertical
.byte $C3,$C3,$C3,$C3,$C3,$C3,$C3,$C3, $00,$00,$00,$00,$00,$00,$00,$00

; Skip some tiles to get to ASCII offset (32-127)
.res 16*16, $00

; ASCII character set (starts at tile 32)
; Space
.byte $00,$00,$00,$00,$00,$00,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; !
.byte $18,$18,$18,$18,$18,$00,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00
; "
.byte $6C,$6C,$6C,$00,$00,$00,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; #
.byte $6C,$6C,$FE,$6C,$FE,$6C,$6C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; $
.byte $18,$3E,$60,$3C,$06,$7C,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00
; %
.byte $00,$C6,$CC,$18,$30,$66,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00
; &
.byte $38,$6C,$38,$76,$DC,$CC,$76,$00, $00,$00,$00,$00,$00,$00,$00,$00
; '
.byte $30,$30,$60,$00,$00,$00,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; (
.byte $0C,$18,$30,$30,$30,$18,$0C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; )
.byte $30,$18,$0C,$0C,$0C,$18,$30,$00, $00,$00,$00,$00,$00,$00,$00,$00
; *
.byte $00,$66,$3C,$FF,$3C,$66,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; +
.byte $00,$18,$18,$7E,$18,$18,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; ,
.byte $00,$00,$00,$00,$00,$18,$18,$30, $00,$00,$00,$00,$00,$00,$00,$00
; -
.byte $00,$00,$00,$7E,$00,$00,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; .
.byte $00,$00,$00,$00,$00,$18,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00
; /
.byte $06,$0C,$18,$30,$60,$C0,$80,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 0
.byte $7C,$C6,$CE,$DE,$F6,$E6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 1
.byte $18,$38,$18,$18,$18,$18,$7E,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 2
.byte $7C,$C6,$06,$1C,$30,$60,$FE,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 3
.byte $7C,$C6,$06,$3C,$06,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 4
.byte $1C,$3C,$6C,$CC,$FE,$0C,$1E,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 5
.byte $FE,$C0,$FC,$06,$06,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 6
.byte $3C,$60,$C0,$FC,$C6,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 7
.byte $FE,$C6,$0C,$18,$30,$30,$30,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 8
.byte $7C,$C6,$C6,$7C,$C6,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00
; 9
.byte $7C,$C6,$C6,$7E,$06,$0C,$78,$00, $00,$00,$00,$00,$00,$00,$00,$00
; :
.byte $00,$18,$18,$00,$00,$18,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00
; ;
.byte $00,$18,$18,$00,$00,$18,$18,$30, $00,$00,$00,$00,$00,$00,$00,$00
; <
.byte $0E,$18,$30,$60,$30,$18,$0E,$00, $00,$00,$00,$00,$00,$00,$00,$00
; =
.byte $00,$00,$7E,$00,$7E,$00,$00,$00, $00,$00,$00,$00,$00,$00,$00,$00
; >
.byte $70,$18,$0C,$06,$0C,$18,$70,$00, $00,$00,$00,$00,$00,$00,$00,$00
; ?
.byte $7C,$C6,$0C,$18,$18,$00,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00
; @
.byte $7C,$C6,$DE,$DE,$DE,$C0,$7E,$00, $00,$00,$00,$00,$00,$00,$00,$00
; A-Z letters (uppercase)
.byte $38,$6C,$C6,$C6,$FE,$C6,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; A
.byte $FC,$C6,$C6,$FC,$C6,$C6,$FC,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; B
.byte $3C,$66,$C0,$C0,$C0,$66,$3C,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; C
.byte $F8,$CC,$C6,$C6,$C6,$CC,$F8,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; D
.byte $FE,$C0,$C0,$FC,$C0,$C0,$FE,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; E
.byte $FE,$C0,$C0,$FC,$C0,$C0,$C0,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; F
.byte $3E,$60,$C0,$CE,$C6,$66,$3E,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; G
.byte $C6,$C6,$C6,$FE,$C6,$C6,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; H
.byte $7E,$18,$18,$18,$18,$18,$7E,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; I
.byte $06,$06,$06,$06,$06,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; J
.byte $C6,$CC,$D8,$F0,$D8,$CC,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; K
.byte $C0,$C0,$C0,$C0,$C0,$C0,$FE,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; L
.byte $C6,$EE,$FE,$FE,$D6,$C6,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; M
.byte $C6,$E6,$F6,$DE,$CE,$C6,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; N
.byte $7C,$C6,$C6,$C6,$C6,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; O
.byte $FC,$C6,$C6,$FC,$C0,$C0,$C0,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; P
.byte $7C,$C6,$C6,$C6,$D6,$DE,$7C,$06, $00,$00,$00,$00,$00,$00,$00,$00 ; Q
.byte $FC,$C6,$C6,$FC,$D8,$CC,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; R
.byte $7C,$C6,$C0,$7C,$06,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; S
.byte $7E,$18,$18,$18,$18,$18,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; T
.byte $C6,$C6,$C6,$C6,$C6,$C6,$7C,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; U
.byte $C6,$C6,$C6,$C6,$C6,$6C,$38,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; V
.byte $C6,$C6,$C6,$D6,$FE,$EE,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; W
.byte $C6,$C6,$6C,$38,$6C,$C6,$C6,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; X
.byte $66,$66,$66,$3C,$18,$18,$18,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; Y
.byte $FE,$06,$0C,$18,$30,$60,$FE,$00, $00,$00,$00,$00,$00,$00,$00,$00 ; Z
