/*
 * Copyright (C) 2005 Pascal Brisset, Antoine Drouin
 * Copyright (C) 2008 Antoine Drouin
 * Copyright (C) 2009 John Stowers
 *
 * This file is part of wasp, some code taken from paparazzi (GPL)
 *
 * wasp is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * wasp is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with paparazzi; see the file COPYING.  If not, write to
 * the Free Software Foundation, 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 *
 */

#include "std.h"
#include "init.h"

#include "LPC21xx.h"
#include "arm7/config.h"
#include "arm7/armVIC.h"

/* declare functions and values from crt0.S & the linker control file */
extern void reset(void);
/* extern void exit(void); */
extern void abort(void);

void hw_init(void) {
  /* set PLL multiplier & divisor. */
  /* values computed from config.h */
  PLLCFG = PLLCFG_MSEL | PLLCFG_PSEL;
  /* enable PLL                    */
  PLLCON = PLLCON_PLLE;
  /* commit changes                */
  PLLFEED = 0xAA;
  PLLFEED = 0x55;

  /* wait for PLL lock */
  while (!(PLLSTAT & PLLSTAT_LOCK))
    continue;
 
  /* enable & connect PLL */
  PLLCON = PLLCON_PLLE | PLLCON_PLLC;
  /* commit changes                */
  PLLFEED = 0xAA;
  PLLFEED = 0x55;

  /* setup & enable the MAM */
  MAMTIM = MAMTIM_CYCLES;
  MAMCR = MAMCR_FULL;
  
  /* setup & enable the MAM */
  MAMTIM = MAMTIM_CYCLES;
  MAMCR = MAMCR_FULL;
  
  /* set the peripheral bus speed */
  /* value computed from config.h */
  VPBDIV = VPBDIV_VALUE;
 
  /* set the interrupt controller defaults  */
  //#if defined(RAM_RUN)
  /* map interrupt vectors space into SRAM  */
  //  MEMMAP = MEMMAP_SRAM;
  //#elif defined(ROM_RUN)
  /* map interrupt vectors space into FLASH */
  MEMMAP = MEMMAP_FLASH;
  //#else
  //#error RUN_MODE not defined!
  //#endif

  /* clear all interrupts     */
  VICIntEnClear = 0xFFFFFFFF;
  /* clear all FIQ selections */
  VICIntSelect = 0x00000000;
  /* point unvectored IRQs to reset() */
  VICDefVectAddr = (uint32_t)reset;

}

void int_enable(void)
{
    enableIRQ();
}

void int_disable(void)
{
    disableIRQ();
}

