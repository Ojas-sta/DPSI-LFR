#ifndef IMU_TASK_H_
#define IMU_TASK_H_

#include <Wire.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include "Config.h"

// ============================================================================
// IMU DATA STRUCTURE
// ============================================================================
struct IMUData {
    float yaw;
    float gyro_z_rad;
    bool is_calibrated;
};

// ============================================================================
// MPU6050 REGISTER ADDRESSES
// ============================================================================
#define MPU6050_PWR_MGMT_1      0x6B
#define MPU6050_GYRO_CONFIG     0x1B
#define MPU6050_GYRO_ZOUT_H     0x47

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================
extern SemaphoreHandle_t g_imu_mutex;
extern float g_current_yaw;

// Internal state
static float gz_offset = 0.0f;
static bool imu_initialized = false;

// ============================================================================
// FUNCTION DECLARATIONS
// ============================================================================

bool initIMU(uint8_t sda, uint8_t scl) {
    Wire.begin(sda, scl, I2C_FREQ_HZ);
    delay(100);

    Wire.beginTransmission(MPU6050_I2C_ADDR);
    Wire.write(MPU6050_PWR_MGMT_1);
    Wire.write(0x00);
    if (Wire.endTransmission() != 0) {
        return false;
    }
    delay(100);

    Wire.beginTransmission(MPU6050_I2C_ADDR);
    Wire.write(MPU6050_GYRO_CONFIG);
    Wire.write(0x00);
    if (Wire.endTransmission() != 0) {
        return false;
    }

    imu_initialized = true;
    return true;
}

void calibrateIMUGyro(uint16_t samples) {
    if (!imu_initialized) return;

    long sum = 0;
    for (uint16_t i = 0; i < samples; i++) {
        Wire.beginTransmission(MPU6050_I2C_ADDR);
        Wire.write(MPU6050_GYRO_ZOUT_H);
        Wire.endTransmission(false);
        Wire.requestFrom(MPU6050_I2C_ADDR, 2);

        if (Wire.available() == 2) {
            int16_t gz_raw = (Wire.read() << 8) | Wire.read();
            sum += gz_raw;
        }
        delay(2);
    }

    gz_offset = (float)sum / samples;
}

void Task_IMU_Polling(void* pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xPeriod = pdMS_TO_TICKS(IMU_POLL_PERIOD_MS);
    const float dt = IMU_POLL_PERIOD_MS / 1000.0f;

    while (true) {
        if (imu_initialized) {
            Wire.beginTransmission(MPU6050_I2C_ADDR);
            Wire.write(MPU6050_GYRO_ZOUT_H);
            Wire.endTransmission(false);
            Wire.requestFrom(MPU6050_I2C_ADDR, 2);

            if (Wire.available() == 2) {
                int16_t gz_raw = (Wire.read() << 8) | Wire.read();
                float gz_dps = (gz_raw - gz_offset) / IMU_GYRO_SCALE_250DPS;
                float gz_rad = gz_dps * DEG_TO_RAD;

                if (xSemaphoreTake(g_imu_mutex, portMAX_DELAY) == pdTRUE) {
                    g_current_yaw += gz_rad * dt * RAD_TO_DEG;

                    if (g_current_yaw > 180.0f) g_current_yaw -= 360.0f;
                    if (g_current_yaw < -180.0f) g_current_yaw += 360.0f;

                    xSemaphoreGive(g_imu_mutex);
                }
            }
        }

        vTaskDelayUntil(&xLastWakeTime, xPeriod);
    }
}

float getIMUYaw() {
    float yaw = 0.0f;
    if (xSemaphoreTake(g_imu_mutex, pdMS_TO_TICKS(10)) == pdTRUE) {
        yaw = g_current_yaw;
        xSemaphoreGive(g_imu_mutex);
    }
    return yaw;
}

void resetIMUYaw() {
    if (xSemaphoreTake(g_imu_mutex, portMAX_DELAY) == pdTRUE) {
        g_current_yaw = 0.0f;
        xSemaphoreGive(g_imu_mutex);
    }
}

#endif // IMU_TASK_H_
