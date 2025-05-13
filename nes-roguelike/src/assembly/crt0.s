.segment "HEADER"
  ; iNES header
  .byte $4E,$45,$53,$1A  ; "NES" followed by MS-DOS EOF
  .byte 2                ; 2 PRG banks (32kb)
  .byte 1                ; 1 CHR bank (8kb)
  .byte $01,$00          ; Mapper 0, vertical mirroring
  .byte $00,$00,$00,$00,$00,$00,$00,$00  ; Padding

.segment "ZEROPAGE"
  ; Zero page variables

.segment "BSS"
  ; Variables in RAM

.segment "VECTORS"
  ; CPU interrupt vectors
  .addr nmi_handler
  .addr reset_handler
  .addr irq_handler

.segment "CODE"
  .export _ppu_wait_vblank

  ; External interrupt handlers
  .import _nmi_handler
  .import _irq_handler
  .import _main

; Reset handler (called at power-on)
reset_handler:
  SEI           ; Disable IRQs
  CLD           ; Clear decimal mode (not used on NES)
  LDX #$40
  STX $4017     ; Disable APU frame IRQ
  LDX #$FF
  TXS           ; Set up stack
  INX           ; X = 0
  STX $2000     ; Disable NMI
  STX $2001     ; Disable rendering
  STX $4010     ; Disable DMC IRQs

  ; Wait for first vblank
wait_vblank1:
  BIT $2002
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
  LDA #$FE
  STA $0200, X  ; Reserve $0200-$02FF for sprite OAM
  INX
  BNE clear_ram

  ; Wait for second vblank
wait_vblank2:
  BIT $2002
  BPL wait_vblank2

  ; Initialize hardware
  LDA #0
  STA $2000     ; Disable NMI
  STA $2001     ; Disable rendering
  STA $4015     ; Disable APU sound
  STA $4010     ; Disable DMC IRQs

  ; Initialize other hardware registers

  ; Call C main()
  JSR _main

  ; If main() returns, enter an infinite loop
loop:
  JMP loop

; NMI handler
nmi_handler:
  ; Save registers
  PHA
  TXA
  PHA
  TYA
  PHA

  ; Call C NMI handler
  JSR _nmi_handler

  ; Restore registers
  PLA
  TAY
  PLA
  TAX
  PLA
  RTI

; IRQ handler
irq_handler:
  ; Save registers
  PHA
  TXA
  PHA
  TYA
  PHA

  ; Call C IRQ handler
  JSR _irq_handler

  ; Restore registers
  PLA
  TAY
  PLA
  TAX
  PLA
  RTI

; C-callable PPU wait for vblank
_ppu_wait_vblank:
@loop:
  BIT $2002
  BPL @loop
  RTS
