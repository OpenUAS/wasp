/*
 * Copyright (C) 2006 Pascal Brisset, Antoine Drouin, Michel Gorraz
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

/** \file usb_serial.h
 *  \brief arch independant USB API
 *
 */

#ifndef USB_S_H
#define USB_S_H

#include "std.h"

void VCOM_init(void);
int  VCOM_putchar(int c);
int  VCOM_getchar(void);
bool_t VCOM_check_free_space(uint8_t len);
int VCOM_check_available(void);

#define UsbSInit() VCOM_init()
#define UsbSCheckFreeSpace(_x) VCOM_check_free_space(_x)
#define UsbSTransmit(_x) VCOM_putchar(_x)
#define UsbSSendMessage() {}
#define UsbSGetch() VCOM_getchar()
#define UsbSChAvailable() VCOM_check_available()

#endif /* USB_S_H */
