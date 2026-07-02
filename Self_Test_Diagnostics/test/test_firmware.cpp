#include <iostream>
#include <cassert>
#include "mock_arduino.h"
#include "../src/Motors.h"
#include "../src/Config.h"

// Declare functions under test from main.cpp.
extern void handleSerialInput();

void run_test_safety_overrides() {
    std::cout << "[TEST] Running Safety Override (g_armed = false) Tests..." << std::endl;

    // Reset state
    g_armed = false;
    g_auto_mode = true;
    initMotors();
    Serial.clear();

    // 1. Direct call to setLeftMotor/setRightMotor
    setLeftMotor(200);
    setRightMotor(-150);
    if (getLeftMotorPWM() != 0 || getRightMotorPWM() != 0) {
        std::cerr << "  FAIL: setMotor direct call bypasses disarm check! Left: " 
                  << getLeftMotorPWM() << ", Right: " << getRightMotorPWM() << std::endl;
        exit(1);
    }
    std::cout << "  PASS: Direct speed commands forced to 0 when disarmed." << std::endl;

    // 2. UART command while disarmed
    g_armed = false;
    g_auto_mode = true;
    Serial.clear();
    Serial.feed("M:0.8,-0.5\n");
    handleSerialInput();
    if (getLeftMotorPWM() != 0 || getRightMotorPWM() != 0) {
        std::cerr << "  FAIL: UART command accepted while disarmed! Left: "
                  << getLeftMotorPWM() << ", Right: " << getRightMotorPWM() << std::endl;
        exit(1);
    }
    std::cout << "  PASS: UART commands forced to 0 when disarmed." << std::endl;

    // 3. UART arm command can re-arm the system.
    Serial.clear();
    Serial.feed("A:1\n");
    handleSerialInput();
    if (!g_armed) {
        std::cerr << "  FAIL: UART arm command did not arm the system." << std::endl;
        exit(1);
    }
    std::cout << "  PASS: UART arm command updates safety state." << std::endl;
}

void run_test_auto_mode() {
    std::cout << "[TEST] Running Auto/Manual Mode Toggling Tests..." << std::endl;

    // Reset state
    g_armed = true; // Armed for testing control logic routing
    g_auto_mode = false; // Manual mode
    initMotors();
    Serial.clear();

    // 1. In manual mode (g_auto_mode = false), UART command must be ignored
    Serial.feed("M:0.5,0.5\n");
    handleSerialInput();
    if (getLeftMotorPWM() != 0 || getRightMotorPWM() != 0) {
        std::cerr << "  FAIL: UART command processed in MANUAL mode! Left: "
                  << getLeftMotorPWM() << ", Right: " << getRightMotorPWM() << std::endl;
        exit(1);
    }
    std::cout << "  PASS: UART commands ignored in MANUAL mode." << std::endl;

    // 2. C:1 switches back to AUTO mode.
    Serial.clear();
    Serial.feed("C:1\n");
    handleSerialInput();
    if (!g_auto_mode) {
        std::cerr << "  FAIL: UART C:1 did not switch to AUTO mode." << std::endl;
        exit(1);
    }
    std::cout << "  PASS: UART mode command switches back to AUTO mode." << std::endl;

    // 3. In auto mode (g_auto_mode = true), UART command must be processed.
    Serial.clear();
    Serial.feed("M:0.6,-0.4\n");
    handleSerialInput();
    int expected_l = (int)(0.6f * 255.0f);
    int expected_r = (int)(-0.4f * 255.0f);
    if (getLeftMotorPWM() != expected_l || getRightMotorPWM() != expected_r) {
        std::cerr << "  FAIL: UART command ignored/incorrect in AUTO mode! Expected Left: "
                  << expected_l << ", got: " << getLeftMotorPWM() 
                  << ", Expected Right: " << expected_r << ", got: " << getRightMotorPWM() << std::endl;
        exit(1);
    }
    std::cout << "  PASS: UART commands processed in AUTO mode." << std::endl;
}

void run_test_uart_scaling_constraints() {
    std::cout << "[TEST] Running UART Scaling & Constraint Clamping Tests..." << std::endl;

    // Reset state
    g_armed = true;
    g_auto_mode = true;
    initMotors();

    struct TestCase {
        std::string command;
        int expected_left;
        int expected_right;
    };

    std::vector<TestCase> cases = {
        {"M:0.0,0.0\n", 0, 0},
        {"M:0.5,0.8\n", (int)(0.5f * 255.0f), (int)(0.8f * 255.0f)},
        {"M:-0.3,-0.75\n", (int)(-0.3f * 255.0f), (int)(-0.75f * 255.0f)},
        {"M:1.0,-1.0\n", 255, -255},
        // Out of range: must be constrained
        {"M:1.5,-2.0\n", 255, -255},
        {"M:-3.5,4.0\n", -255, 255}
    };

    for (size_t i = 0; i < cases.size(); ++i) {
        Serial.clear();
        Serial.feed(cases[i].command);
        handleSerialInput();
        if (getLeftMotorPWM() != cases[i].expected_left || getRightMotorPWM() != cases[i].expected_right) {
            std::cerr << "  FAIL: Case " << i << " (" << cases[i].command << ") failed! "
                      << "Expected Left: " << cases[i].expected_left << ", got: " << getLeftMotorPWM()
                      << "; Expected Right: " << cases[i].expected_right << ", got: " << getRightMotorPWM() << std::endl;
            exit(1);
        }
    }
    std::cout << "  PASS: Float commands correctly scaled by 255.0f and clamped to [-255, 255]." << std::endl;
}

void run_test_ping_pong() {
    std::cout << "[TEST] Running Ping-Pong Command Tests..." << std::endl;
    Serial.clear();
    Serial.feed("P\n");
    handleSerialInput();
    if (Serial.tx_buffer.str() != "P_ACK\n") {
        std::cerr << "  FAIL: Ping command did not respond with P_ACK\\n! Got: "
                  << Serial.tx_buffer.str() << std::endl;
        exit(1);
    }
    std::cout << "  PASS: Ping command correctly responded with P_ACK\\n." << std::endl;
}

int main() {
    std::cout << "=== ARDUINO UNO FIRMWARE VERIFICATION START ===" << std::endl;
    run_test_safety_overrides();
    run_test_auto_mode();
    run_test_uart_scaling_constraints();
    run_test_ping_pong();
    std::cout << "=== ALL TESTS PASSED SUCCESSFULLY ===" << std::endl;
    return 0;
}
