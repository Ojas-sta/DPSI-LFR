#include <Wire.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>
#include <freertos/queue.h>

#include "Config.h"
#include "IMU_Task.h"
#include "PID_Control.h"
#include "MotorDriver.h"
#include "SerialComms.h"
#include "DisplayUI.h"

// ============================================================================
// GLOBAL SYNCHRONIZATION PRIMITIVES
// ============================================================================
SemaphoreHandle_t g_imu_mutex = NULL;
QueueHandle_t g_command_queue = NULL;

// ============================================================================
// GLOBAL STATE VARIABLES
// ============================================================================
float g_current_yaw = 0.0f;
uint8_t g_system_mode = MODE_STANDBY;
PIDGains g_pid_gains = {PID_KP_DEFAULT, PID_KI_DEFAULT, PID_KD_DEFAULT};
unsigned long g_last_packet_timer = 0;

// Turn state
uint8_t g_turn_target_direction = 0;
float g_turn_target_angle = 0.0f;
bool g_turn_in_progress = false;

// LED states
unsigned long g_green_led_timeout = 0;
bool g_red_led_active = false;

// ============================================================================
// SETUP
// ============================================================================

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    delay(100);

    g_imu_mutex = xSemaphoreCreateMutex();
    g_command_queue = xQueueCreate(10, sizeof(CommandPacket));

    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_FREQ_HZ);
    delay(100);

    initMotorDriver();
    initLineSensors();

    if (!initIMU(PIN_I2C_SDA, PIN_I2C_SCL)) {
        Serial.println(F("IMU Init Failed"));
    } else {
        delay(500);
        calibrateIMUGyro(IMU_CALIBRATION_SAMPLES);
        Serial.println(F("IMU Calibrated"));
    }

    if (!initDisplay(PIN_I2C_SDA, PIN_I2C_SCL)) {
        Serial.println(F("Display Init Failed"));
    }

    xTaskCreatePinnedToCore(Task_IMU_Polling, "IMU_Poll", 4096, NULL, 5, NULL, 0);
    xTaskCreatePinnedToCore(Task_LineFollow_PID, "LineFollow", 8192, NULL, 4, NULL, 1);
    xTaskCreatePinnedToCore(Task_Serial_Parser, "SerialParser", 4096, NULL, 3, NULL, 1);
    xTaskCreatePinnedToCore(Task_OLED_Display, "OLED", 3072, NULL, 1, NULL, 1);
    xTaskCreatePinnedToCore(Task_LED_Control, "LEDs", 2048, NULL, 1, NULL, 1);

    Serial.println(F("DPSI-LFR V2 Ready"));
}

void loop() {
    vTaskDelay(portMAX_DELAY);
}

// ============================================================================
// TASK: LINE FOLLOW & PID CONTROL
// ============================================================================

void Task_LineFollow_PID(void* pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xPeriod = pdMS_TO_TICKS(PID_LOOP_PERIOD_MS);
    const float dt = PID_LOOP_PERIOD_MS / 1000.0f;

    float last_error = 0.0f;
    uint16_t ir_bitmask = 0;
    float line_error = 0.0f;
    int16_t pid_output = 0;
    int16_t left_pwm = 0;
    int16_t right_pwm = 0;

    static unsigned long telemetry_timer = 0;

    while (true) {
        if ((millis() - g_last_packet_timer) > WATCHDOG_TIMEOUT_MS) {
            emergencyStopMotors();
            g_system_mode = MODE_STANDBY;
        }

        switch (g_system_mode) {
            case MODE_STANDBY:
                emergencyStopMotors();
                resetPIDState();
                break;

            case MODE_LINE_FOLLOW:
                ir_bitmask = readIRSensorBitmask();
                line_error = calculateLineError(ir_bitmask, last_error);
                pid_output = computePID(line_error, g_pid_gains, dt);

                left_pwm = BASE_SPEED - pid_output;
                right_pwm = BASE_SPEED + pid_output;

                setMotorSpeeds(left_pwm, right_pwm);

                if (millis() - telemetry_timer >= TELEMETRY_PERIOD_MS) {
                    sendTelemetryPacket(ir_bitmask, getIMUYaw(), (int16_t)line_error);
                    telemetry_timer = millis();
                }
                break;

            case MODE_IMU_TURN:
                if (g_turn_in_progress) {
                    float current_yaw = getIMUYaw();
                    float angle_error = g_turn_target_angle - current_yaw;

                    if (abs(angle_error) <= IMU_TURN_DEADBAND_DEG) {
                        setMotorSpeeds(-80, -80);
                        delay(IMU_TURN_BRAKE_MS);
                        emergencyStopMotors();

                        sendTurnComplete(g_turn_target_direction, 0x01);
                        g_turn_in_progress = false;
                        g_system_mode = MODE_LINE_FOLLOW;
                    } else {
                        int16_t turn_speed = 120;
                        if (g_turn_target_direction == TURN_LEFT) {
                            setMotorSpeeds(-turn_speed, turn_speed);
                        } else {
                            setMotorSpeeds(turn_speed, -turn_speed);
                        }
                    }
                }
                break;

            case MODE_MANUAL:
                break;
        }

        vTaskDelayUntil(&xLastWakeTime, xPeriod);
    }
}

// ============================================================================
// TASK: SERIAL COMMAND PARSER
// ============================================================================

void Task_Serial_Parser(void* pvParameters) {
    CommandPacket cmd_packet;

    while (true) {
        while (Serial.available() > 0) {
            uint8_t byte_in = Serial.read();

            if (parseIncomingByte(byte_in, cmd_packet)) {
                g_last_packet_timer = millis();

                switch (cmd_packet.opcode) {
                    case OPCODE_SET_MOTOR_SPEEDS: {
                        int16_t left_pwm = (int16_t)((cmd_packet.payload[0] << 8) | cmd_packet.payload[1]);
                        int16_t right_pwm = (int16_t)((cmd_packet.payload[2] << 8) | cmd_packet.payload[3]);
                        setMotorSpeeds(left_pwm, right_pwm);
                        break;
                    }

                    case OPCODE_EXECUTE_TURN_90: {
                        g_turn_target_direction = cmd_packet.payload[0];
                        resetIMUYaw();
                        if (g_turn_target_direction == TURN_LEFT) {
                            g_turn_target_angle = 90.0f;
                        } else {
                            g_turn_target_angle = -90.0f;
                        }
                        g_turn_in_progress = true;
                        g_system_mode = MODE_IMU_TURN;
                        break;
                    }

                    case OPCODE_EXECUTE_TURN_180: {
                        resetIMUYaw();
                        g_turn_target_angle = 180.0f;
                        g_turn_target_direction = TURN_RIGHT;
                        g_turn_in_progress = true;
                        g_system_mode = MODE_IMU_TURN;
                        break;
                    }

                    case OPCODE_SET_PID_GAINS: {
                        memcpy(&g_pid_gains.kp, &cmd_packet.payload[0], 4);
                        memcpy(&g_pid_gains.ki, &cmd_packet.payload[4], 4);
                        memcpy(&g_pid_gains.kd, &cmd_packet.payload[8], 4);
                        break;
                    }

                    case OPCODE_SET_MODE: {
                        g_system_mode = cmd_packet.payload[0];
                        if (g_system_mode == MODE_STANDBY) {
                            emergencyStopMotors();
                        } else if (g_system_mode == MODE_LINE_FOLLOW) {
                            g_red_led_active = false;
                            g_green_led_timeout = 0;
                        }
                        break;
                    }

                    case OPCODE_ACTION_GREEN_LED: {
                        g_green_led_timeout = millis() + 3000;
                        g_red_led_active = false;
                        break;
                    }

                    case OPCODE_ACTION_RED_LED: {
                        g_red_led_active = true;
                        g_green_led_timeout = 0;
                        g_system_mode = MODE_STANDBY;
                        emergencyStopMotors();
                        break;
                    }

                    case OPCODE_HEARTBEAT_PING: {
                        sendHeartbeatPong(millis() / 1000);
                        break;
                    }

                    case OPCODE_EMERGENCY_STOP: {
                        emergencyStopMotors();
                        g_system_mode = MODE_STANDBY;
                        break;
                    }
                }
            }
        }

        vTaskDelay(pdMS_TO_TICKS(5));
    }
}

// ============================================================================
// TASK: OLED DISPLAY UPDATE
// ============================================================================

void Task_OLED_Display(void* pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xPeriod = pdMS_TO_TICKS(OLED_UPDATE_PERIOD_MS);

    const char* mode_names[] = {"STANDBY", "LINE_FOLLOW", "MANUAL", "IMU_TURN"};

    while (true) {
        uint16_t ir_bitmask = readIRSensorBitmask();
        float yaw = getIMUYaw();

        const char* mode_str = (g_system_mode <= MODE_IMU_TURN) ? mode_names[g_system_mode] : "UNKNOWN";

        renderTelemetry(mode_str, ir_bitmask, yaw, 0, 0, 0);

        vTaskDelayUntil(&xLastWakeTime, xPeriod);
    }
}

// ============================================================================
// TASK: LED CONTROL
// ============================================================================

void Task_LED_Control(void* pvParameters) {
    bool led_state = false;
    while (true) {
        if (millis() < g_green_led_timeout) {
            digitalWrite(PIN_LED_GREEN, led_state ? HIGH : LOW);
        } else {
            digitalWrite(PIN_LED_GREEN, LOW);
        }

        if (g_red_led_active) {
            digitalWrite(PIN_LED_RED, led_state ? HIGH : LOW);
        } else {
            digitalWrite(PIN_LED_RED, LOW);
        }

        led_state = !led_state;
        vTaskDelay(pdMS_TO_TICKS(250));
    }
}
