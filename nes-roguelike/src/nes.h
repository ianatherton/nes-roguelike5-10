#ifndef NES_H
#define NES_H

// NES hardware registers
#define PPU_CTRL        (*(volatile unsigned char*)0x2000)
#define PPU_MASK        (*(volatile unsigned char*)0x2001)
#define PPU_STATUS      (*(volatile unsigned char*)0x2002)
#define PPU_OAM_ADDR    (*(volatile unsigned char*)0x2003)
#define PPU_OAM_DATA    (*(volatile unsigned char*)0x2004)
#define PPU_SCROLL      (*(volatile unsigned char*)0x2005)
#define PPU_ADDRESS     (*(volatile unsigned char*)0x2006)
#define PPU_DATA        (*(volatile unsigned char*)0x2007)
#define OAM_DMA         (*(volatile unsigned char*)0x4014)

// NMI, Reset and IRQ vector addresses
extern void __fastcall__ nmi(void);
extern void __fastcall__ reset(void);
extern void __fastcall__ irq(void);

#endif // NES_H
