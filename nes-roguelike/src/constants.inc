;
; NES Hardware Constants
;

; PPU (Picture Processing Unit) Registers
PPUCTRL   = $2000  ; PPU Control Register 1
PPUMASK   = $2001  ; PPU Control Register 2
PPUSTATUS = $2002  ; PPU Status Register
OAMADDR   = $2003  ; SPR-RAM Address Register
OAMDATA   = $2004  ; SPR-RAM Data Register
PPUSCROLL = $2005  ; Background Scroll Offset
PPUADDR   = $2006  ; VRAM Address Register
PPUDATA   = $2007  ; VRAM Data Register
OAMDMA    = $4014  ; DMA Register for OAM Data

; Controller Registers
CONTROLLER1 = $4016
CONTROLLER2 = $4017

; Controller Button Masks
BUTTON_A      = %10000000
BUTTON_B      = %01000000
BUTTON_SELECT = %00100000
BUTTON_START  = %00010000
BUTTON_UP     = %00001000
BUTTON_DOWN   = %00000100
BUTTON_LEFT   = %00000010
BUTTON_RIGHT  = %00000001
