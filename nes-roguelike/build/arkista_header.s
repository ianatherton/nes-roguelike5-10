.segment "HEADER"
.byte "NES", $1a
.byte 1               ; 1 * 16KB PRG ROM
.byte 1               ; 1 * 8KB CHR ROM
.byte $01, $00        ; mapper 0, vertical mirroring
