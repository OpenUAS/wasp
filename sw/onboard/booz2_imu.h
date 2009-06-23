#ifndef BOOZ2_IMU_H
#define BOOZ2_IMU_H

/* FIXME: Include these as config/airframe.h
 * For IMU_XXX scale constants */
#include "airframe.h"

#include "pprz_algebra_int.h"
#include "booz2_imu_b2.h"

struct BoozImu {
  struct Int32Rates gyro;
  struct Int32Vect3 accel;
  struct Int32Vect3 mag;
  struct Int32Rates gyro_prev;
  struct Int32Vect3 accel_prev;
  struct Int32Rates gyro_neutral;
  struct Int32Vect3 accel_neutral;
  struct Int32Vect3 mag_neutral;
  struct Int32Rates gyro_unscaled;
  struct Int32Vect3 accel_unscaled;
  struct Int32Vect3 mag_unscaled;
  struct Int32Quat  body_to_imu_quat;
  struct Int32RMat  body_to_imu_rmat;
};

extern struct BoozImu booz_imu;

extern void booz2_imu_init(void);

#define Booz2ImuScaleGyro() {						\
    RATES_COPY(booz_imu.gyro_prev, booz_imu.gyro);			\
    booz_imu.gyro.p = ((booz_imu.gyro_unscaled.p - booz_imu.gyro_neutral.p)*IMU_GYRO_P_SENS_NUM)/IMU_GYRO_P_SENS_DEN; \
    booz_imu.gyro.q = ((booz_imu.gyro_unscaled.q - booz_imu.gyro_neutral.q)*IMU_GYRO_Q_SENS_NUM)/IMU_GYRO_Q_SENS_DEN; \
    booz_imu.gyro.r = ((booz_imu.gyro_unscaled.r - booz_imu.gyro_neutral.r)*IMU_GYRO_R_SENS_NUM)/IMU_GYRO_R_SENS_DEN; \
  }


#define Booz2ImuScaleAccel() {						\
    VECT3_COPY(booz_imu.accel_prev, booz_imu.accel);			\
    booz_imu.accel.x = ((booz_imu.accel_unscaled.x - booz_imu.accel_neutral.x)*IMU_ACCEL_X_SENS_NUM)/IMU_ACCEL_X_SENS_DEN; \
    booz_imu.accel.y = ((booz_imu.accel_unscaled.y - booz_imu.accel_neutral.y)*IMU_ACCEL_Y_SENS_NUM)/IMU_ACCEL_Y_SENS_DEN; \
    booz_imu.accel.z = ((booz_imu.accel_unscaled.z - booz_imu.accel_neutral.z)*IMU_ACCEL_Z_SENS_NUM)/IMU_ACCEL_Z_SENS_DEN; \
  }

#define Booz2ImuScaleMag() {					\
    booz_imu.mag.x = ((booz_imu.mag_unscaled.x - booz_imu.mag_neutral.x) * IMU_MAG_X_SENS_NUM) / IMU_MAG_X_SENS_DEN; \
    booz_imu.mag.y = ((booz_imu.mag_unscaled.y - booz_imu.mag_neutral.y) * IMU_MAG_Y_SENS_NUM) / IMU_MAG_Y_SENS_DEN; \
    booz_imu.mag.z = ((booz_imu.mag_unscaled.z - booz_imu.mag_neutral.z) * IMU_MAG_Z_SENS_NUM) / IMU_MAG_Z_SENS_DEN; \
  }

#endif /* BOOZ2_IMU_H */
