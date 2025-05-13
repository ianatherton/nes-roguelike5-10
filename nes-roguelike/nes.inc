; NES Hardware Registers

; PPU registers
PPUCTRL     = $2000
PPUMASK     = $2001
PPUSTATUS   = $2002
OAMADDR     = $2003
OAMDATA     = $2004
PPUSCROLL   = $2005
PPUADDR     = $2006
PPUDATA     = $2007

; APU and I/O registers
SQ1_VOL     = $4000
SQ1_SWEEP   = $4001
SQ1_LO      = $4002
SQ1_HI      = $4003
SQ2_VOL     = $4004
SQ2_SWEEP   = $4005
SQ2_LO      = $4006
SQ2_HI      = $4007
TRI_LINEAR  = $4008
TRI_LO      = $400A
TRI_HI      = $400B
NOISE_VOL   = $400C
NOISE_LO    = $400E
NOISE_HI    = $400F
DMC_FREQ    = $4010
DMC_RAW     = $4011
DMC_START   = $4012
DMC_LEN     = $4013
OAMDMA      = $4014
SND_CHN     = $4015
JOY1        = $4016
JOY2        = $4017

; NMI_ENABLE  = %10000000   ; Enable NMI
; SPRITE_PT0  = %00000000   ; Use pattern table 0 for sprites
; SPRITE_PT1  = %00001000   ; Use pattern table 1 for sprites
; SPRITE_SIZE = %00100000   ; 8x16 sprites
; BG_PT0      = %00000000   ; Use pattern table 0 for background
; BG_PT1      = %00010000   ; Use pattern table 1 for background

; Common memory locations
OAM_BUF     = $0200        ; 256 bytes for sprite OAM data
