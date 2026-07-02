#pragma once
#include <string>
#include <vector>
#include <sstream>
#include <iostream>
#include <map>
#include <cstring>
#include <cctype>

// Arduino constants
#define D1 1
#define D2 2
#define D3 3
#define D4 4
#define D5 5
#define D6 6
#define OUTPUT 1
#define INPUT 2
#define LOW 0
#define HIGH 1
#define PROGMEM

// Simulated clock
extern unsigned long simulated_time;
inline unsigned long millis() {
    return simulated_time;
}

inline int constrain(int amt, int low, int high) {
    return (amt < low) ? low : ((amt > high) ? high : amt);
}

// Mock Arduino I/O functions
inline void pinMode(int pin, int mode) {}
inline void digitalWrite(int pin, int val) {}
inline void analogWrite(int pin, int val) {}
inline void delay(int ms) {
    simulated_time += ms;
}

// Serial Mock
class SerialMock {
public:
    std::string rx_buffer;
    size_t rx_pos = 0;
    std::stringstream tx_buffer;

    void begin(unsigned long baud) {}
    int available() {
        return rx_buffer.length() - rx_pos;
    }
    char read() {
        if (rx_pos < rx_buffer.length()) {
            return rx_buffer[rx_pos++];
        }
        return -1;
    }
    void print(const char* s) { tx_buffer << s; }
    void print(int val) { tx_buffer << val; }
    void print(unsigned long val) { tx_buffer << val; }
    void print(float val) { tx_buffer << val; }
    void print(const std::string& s) { tx_buffer << s; }
    void println(const char* s) { tx_buffer << s << "\n"; }
    void println(int val) { tx_buffer << val << "\n"; }
    void println(unsigned long val) { tx_buffer << val << "\n"; }
    void println(float val) { tx_buffer << val << "\n"; }
    void println(const std::string& s) { tx_buffer << s << "\n"; }
    
    template<typename... Args>
    void printf(const char* format, Args... args) {
        char buf[256];
        snprintf(buf, sizeof(buf), format, args...);
        tx_buffer << buf;
    }

    void clear() {
        rx_buffer.clear();
        rx_pos = 0;
        tx_buffer.str("");
        tx_buffer.clear();
    }

    void feed(const std::string& data) {
        rx_buffer += data;
    }
};

extern SerialMock Serial;
