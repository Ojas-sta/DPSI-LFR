#include "Display.h"
#include "Config.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(DISPLAY_WIDTH, DISPLAY_HEIGHT, &Wire, -1);
bool display_ok = false;

void initDisplay() {
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println(F("[DISP] SSD1306 allocation failed"));
        display_ok = false;
        return;
    }
    display_ok = true;
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("RC POST CONTROLLER");
    display.println("Diagnostics AP");
    display.println("------------------");
    display.print("IP: ");
    display.println("192.168.4.1");
    display.display();
}

void updateDisplay(int clientCount, uint16_t irBitmask, int leftPWM, int rightPWM, bool watchdogOk) {
    if (!display_ok) return;

    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    
    display.print("AP: ");
    display.println(AP_SSID);
    display.print("IP: 192.168.4.1  C:");
    display.println(clientCount);
    
    display.println("---------------------");
    
    display.print("IR(HEX): 0x");
    if (irBitmask < 0x100) display.print("0");
    if (irBitmask < 0x10) display.print("0");
    display.println(irBitmask, HEX);
    
    display.print("MOT L: ");
    display.print(leftPWM);
    display.print("  R: ");
    display.println(rightPWM);

    display.print("WDG: ");
    if(watchdogOk) {
        display.println("OK");
    } else {
        display.println("FAULT!");
    }
    
    display.display();
}
