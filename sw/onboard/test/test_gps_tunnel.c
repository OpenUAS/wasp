/*
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
#include "sys_time.h"
#include "led.h"
#include "comm.h"
#include "generated/messages.h"
#include "generated/settings.h"

/* FIXME: BREAKS ABSTRACTION */
#include "arm7/uart_hw.h"
 
static inline void main_init( void );
static inline void main_periodic_task( void );
static inline void main_event_task( void );
 
int main( void ) {
    main_init();
    while(1) {
        if (sys_time_periodic())
            main_periodic_task();
        main_event_task();
    }
    return 0;
}
 
static inline void main_init( void ) {
    hw_init();
    sys_time_init();
    led_init();
    uart0_init_tx();
    uart1_init_tx();
    int_enable();
}
 
static inline void main_periodic_task( void ) {
    led_periodic_task();
    RunOnceEvery(100, {
        led_toggle(LED_GPS);
    });
}
 
static inline void main_event_task( void ) {
    while (Uart1ChAvailable())
        uart0_transmit(Uart1Getch());
 
    while (Uart0ChAvailable())
        uart1_transmit(Uart0Getch());
}
