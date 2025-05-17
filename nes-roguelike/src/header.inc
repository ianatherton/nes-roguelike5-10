;
; iNES ROM Header for NES games
;

.segment "HEADER"
  .byte $4E, $45, $53, $1A  ; "NES" followed by MS-DOS EOF
  .byte $02                 ; Number of 16KB PRG-ROM banks
  .byte $01                 ; Number of 8KB CHR-ROM banks
  .byte %00000001           ; Vertical mirroring, no save RAM, no mapper
  .byte %00000000           ; No special-case flags set, no mapper
  .byte $00                 ; No PRG-RAM present
  .byte $00                 ; NTSC format
