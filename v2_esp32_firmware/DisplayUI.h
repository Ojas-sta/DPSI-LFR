#ifndef DISPLAY_UI_H_
#define DISPLAY_UI_H_

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "Config.h"

// ============================================================================
// DISPLAY OBJECT
// ============================================================================
static Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ============================================================================
// DISPLAY INITIALIZATION
// ============================================================================

bool initDisplay(uint8_t sda, uint8_t scl) {
    if (!display.begin(SSD1306_SWITCHCAPVCC, SSD1306_I2C_ADDR)) {
        return false;
    }

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println(F("DPSI-LFR V2"));
    display.println(F("Initializing..."));
    display.display();

    return true;
}

// ============================================================================
// TELEMETRY RENDERING
// ============================================================================

void renderTelemetry(const char* mode_str, uint16_t bitmask, float yaw, int16_t err, int16_t pwm_l, int16_t pwm_r) {
    display.clearDisplay();

    // Row 0-15: Mode & Status
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("Mode: "));
    display.println(mode_str);

    // Row 16-31: IR Sensor Array (10 boxes)
    uint8_t box_y = 16;
    uint8_t box_width = 10;
    uint8_t box_height = 12;
    uint8_t box_spacing = 2;

    for (int i = 0; i < 10; i++) {
        uint8_t x = i * (box_width + box_spacing) + 4;

        if (bitmask & (1 << (9 - i))) {
            display.fillRect(x, box_y, box_width, box_height, SSD1306_WHITE);
        } else {
            display.drawRect(x, box_y, box_width, box_height, SSD1306_WHITE);
        }
    }

    // Row 32-47: Yaw & Error
    display.setCursor(0, 32);
    display.print(F("Yaw:"));
    display.print(yaw, 1);
    display.print(F(" Err:"));
    display.println(err);

    // Row 48-63: Motor PWM
    display.setCursor(0, 48);
    display.print(F("L:"));
    display.print(pwm_l);
    display.print(F(" R:"));
    display.print(pwm_r);

    display.display();
}

#endif // DISPLAY_UI_H_
