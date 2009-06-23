#include "comm-autopilot.h"

#include "rc.h"
#include "gps.h"
#include "booz2_imu.h"

bool_t
comm_autopilot_send ( CommChannel_t chan, uint8_t msgid )
{
    uint8_t ret = TRUE;

    switch (msgid)
    {
        case MESSAGE_ID_WASP_GPS:
            MESSAGE_SEND_WASP_GPS( chan, &booz_gps_state.fix, &booz_gps_state.num_sv );
            break;
        case MESSAGE_ID_IMU_GYRO_RAW:
            MESSAGE_SEND_IMU_GYRO_RAW(
                    chan,
                    &booz_imu.gyro_unscaled.p,
                    &booz_imu.gyro_unscaled.q,
                    &booz_imu.gyro_unscaled.r);
            break;
        case MESSAGE_ID_IMU_ACCEL_RAW:
            MESSAGE_SEND_IMU_ACCEL_RAW(
                    COMM_1,
                    &booz_imu.accel_unscaled.x,
			        &booz_imu.accel_unscaled.y,
			        &booz_imu.accel_unscaled.z);
            break;
        case MESSAGE_ID_IMU_MAG_RAW:
            MESSAGE_SEND_IMU_MAG_RAW(
                    chan,
                    &booz_imu.mag_unscaled.x,
			        &booz_imu.mag_unscaled.y,
			        &booz_imu.mag_unscaled.z);
            break;
        case MESSAGE_ID_WASP_GYRO:
            MESSAGE_SEND_WASP_GYRO(
                    chan,
                    &booz_imu.gyro.p,
                    &booz_imu.gyro.q,
                    &booz_imu.gyro.r);
            break;
        case MESSAGE_ID_WASP_ACCEL:
            MESSAGE_SEND_WASP_ACCEL(
                    chan,
                    &booz_imu.accel.x,
                    &booz_imu.accel.y,
                    &booz_imu.accel.z);
            break;
        case MESSAGE_ID_WASP_MAG:
            MESSAGE_SEND_WASP_MAG(
                    chan,
                    &booz_imu.mag.x,
			        &booz_imu.mag.y,
			        &booz_imu.mag.z);
            break;
        case MESSAGE_ID_STATUS:
            MESSAGE_SEND_STATUS(chan, &rc_status, &booz_gps_state.fix );
            break;
        default:
            ret = FALSE;
            break;
    }

    return ret;
}

