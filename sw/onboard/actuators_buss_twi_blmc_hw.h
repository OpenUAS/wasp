#ifndef ACTUATORS_BUSS_TWI_BLMC_HW_H
#define ACTUATORS_BUSS_TWI_BLMC_HW_H

#include <string.h>
#include "std.h"
#include "config.h"
#include "i2c.h"

#include "airframe.h"
#include "booz2_supervision.h"

#ifdef KILL_MOTORS
#define SetActuatorsFromCommands(_motors_on) {		      \
    Actuator(SERVO_FRONT) = 0;				      \
    Actuator(SERVO_BACK)  = 0;				      \
    Actuator(SERVO_RIGHT) = 0;				      \
    Actuator(SERVO_LEFT)  = 0;				      \
    ActuatorsCommit();					      \
  }
#else
#define SetActuatorsFromCommands(_motors_on) {				\
    pprz_t mixed_commands[SERVOS_NB];					\
    BOOZ2_SUPERVISION_RUN(mixed_commands, booz2_commands, _motors_on);	\
    Actuator(SERVO_FRONT) = (uint8_t)mixed_commands[SERVO_FRONT];	\
    Actuator(SERVO_BACK)  = (uint8_t)mixed_commands[SERVO_BACK];	\
    Actuator(SERVO_RIGHT) = (uint8_t)mixed_commands[SERVO_RIGHT];	\
    Actuator(SERVO_LEFT)  = (uint8_t)mixed_commands[SERVO_LEFT];	\
    ActuatorsCommit();							\
  }
#endif /* KILL_MOTORS              */

#define ChopServo(x,a,b) ((x)>(b)?(b):(x))
#define Actuator(i) buss_twi_blmc_motor_power[i]
#define ActuatorsCommit() {			                \
    if ( buss_twi_blmc_status == BUSS_TWI_BLMC_STATUS_IDLE) {	\
      buss_twi_blmc_idx = 0;					\
      buss_twi_blmc_status = BUSS_TWI_BLMC_STATUS_BUSY;		\
      ActuatorsBussTwiBlmcSend();				\
    }								\
    else							\
      twi_blmc_nb_err++;					\
  }

#define SERVOS_TICS_OF_USEC(s) ((uint8_t)(s)) 

#define BUSS_TWI_BLMC_STATUS_IDLE 0
#define BUSS_TWI_BLMC_STATUS_BUSY 1
#define BUSS_TWI_BLMC_NB 4
extern uint8_t buss_twi_blmc_motor_power[BUSS_TWI_BLMC_NB];
extern volatile bool_t  buss_twi_blmc_status;
extern uint8_t twi_blmc_nb_err;
extern volatile bool_t  buss_twi_blmc_i2c_done;
extern volatile uint8_t buss_twi_blmc_idx;
extern const uint8_t buss_twi_blmc_addr[];

#define ActuatorsBussTwiBlmcNext() {			\
    buss_twi_blmc_idx++;				\
    if (buss_twi_blmc_idx < BUSS_TWI_BLMC_NB) {		\
      ActuatorsBussTwiBlmcSend();			\
    }							\
    else						\
      buss_twi_blmc_status = BUSS_TWI_BLMC_STATUS_IDLE;	\
  }

#define ActuatorsBussTwiBlmcSend() {					             \
    i2c_buf[0] = buss_twi_blmc_motor_power[buss_twi_blmc_idx];		             \
    i2c_transmit(buss_twi_blmc_addr[buss_twi_blmc_idx], 1, &buss_twi_blmc_i2c_done); \
  }


#endif /* ACTUATORS_BUSS_TWI_BLMC_HW_H */
