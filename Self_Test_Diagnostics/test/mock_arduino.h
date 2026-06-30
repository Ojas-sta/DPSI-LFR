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
#define WIFI_AP 1
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
inline void analogWriteRange(int range) {}
inline void analogWriteFreq(int freq) {}
inline void delay(int ms) {
    simulated_time += ms;
}

// IPAddress Mock
class IPAddress {
public:
    uint8_t bytes[4];
    IPAddress() { bytes[0] = bytes[1] = bytes[2] = bytes[3] = 0; }
    IPAddress(uint8_t b1, uint8_t b2, uint8_t b3, uint8_t b4) {
        bytes[0] = b1; bytes[1] = b2; bytes[2] = b3; bytes[3] = b4;
    }
    std::string toString() const {
        return std::to_string(bytes[0]) + "." + std::to_string(bytes[1]) + "." +
               std::to_string(bytes[2]) + "." + std::to_string(bytes[3]);
    }
};

inline std::ostream& operator<<(std::ostream& os, const IPAddress& ip) {
    os << ip.toString();
    return os;
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
    void print(float val) { tx_buffer << val; }
    void print(const IPAddress& ip) { tx_buffer << ip.toString(); }
    void print(const std::string& s) { tx_buffer << s; }
    void println(const char* s) { tx_buffer << s << "\n"; }
    void println(int val) { tx_buffer << val << "\n"; }
    void println(float val) { tx_buffer << val << "\n"; }
    void println(const IPAddress& ip) { tx_buffer << ip.toString() << "\n"; }
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

// WiFi Mock
class WiFiMock {
public:
    void mode(int m) {}
    void softAP(const char* ssid, const char* pass) {}
    void softAPConfig(IPAddress ip, IPAddress gateway, IPAddress subnet) {}
    IPAddress softAPIP() { return IPAddress(192, 168, 4, 1); }
};
extern WiFiMock WiFi;

// ESPAsyncWebServer and TCP Mock
class AsyncWebServerRequest {
public:
    void send_P(int code, const char* type, const char* content) {}
};

class AsyncWebSocketClient {
private:
    uint32_t _id;
public:
    AsyncWebSocketClient(uint32_t id) : _id(id) {}
    uint32_t id() const { return _id; }
};

enum AwsEventType {
    WS_EVT_CONNECT,
    WS_EVT_DISCONNECT,
    WS_EVT_DATA
};

struct AwsFrameInfo {
    bool final;
    int index;
    size_t len;
    int opcode;
};

#define WS_TEXT 1
#define HTTP_GET 1

class AsyncWebSocket {
public:
    const char* _url;
    void (*_eventHandler)(AsyncWebSocket*, AsyncWebSocketClient*, AwsEventType, void*, uint8_t*, size_t) = nullptr;
    std::vector<std::string> sent_messages;
    int _client_count = 0;

    AsyncWebSocket(const char* url) : _url(url) {}

    void onEvent(void (*handler)(AsyncWebSocket*, AsyncWebSocketClient*, AwsEventType, void*, uint8_t*, size_t)) {
        _eventHandler = handler;
    }

    void cleanupClients() {}
    int count() { return _client_count; }

    void textAll(const char* buffer, size_t len) {
        sent_messages.push_back(std::string(buffer, len));
    }
};

class AsyncWebServer {
public:
    int _port;
    AsyncWebServer(int port) : _port(port) {}
    void addHandler(AsyncWebSocket* ws) {}
    void on(const char* path, int method, void (*handler)(AsyncWebServerRequest*)) {}
    void begin() {}
};

// ArduinoJson Mock
class JsonVariant {
private:
    std::string _val;
    bool _is_null = true;
public:
    JsonVariant() : _val(""), _is_null(true) {}
    JsonVariant(const std::string& v) : _val(v), _is_null(false) {}

    operator const char*() const {
        if (_is_null) return nullptr;
        return _val.c_str();
    }

    operator int() const {
        if (_is_null) return 0;
        try {
            return std::stoi(_val);
        } catch (...) {
            return 0;
        }
    }

    operator bool() const {
        if (_is_null) return false;
        return (_val == "true" || _val == "1");
    }

    JsonVariant& operator=(const std::string& s) {
        _val = s;
        _is_null = false;
        return *this;
    }

    JsonVariant& operator=(int val) {
        _val = std::to_string(val);
        _is_null = false;
        return *this;
    }

    JsonVariant& operator=(unsigned long val) {
        _val = std::to_string(val);
        _is_null = false;
        return *this;
    }

    JsonVariant& operator=(bool val) {
        _val = val ? "true" : "false";
        _is_null = false;
        return *this;
    }
};

class JsonObject {
public:
    std::map<std::string, JsonVariant> _map;
    std::map<std::string, JsonObject> _nested;

    JsonVariant& operator[](const std::string& key) {
        return _map[key];
    }

    JsonObject& createNestedObject(const std::string& key) {
        return _nested[key];
    }
};

template<size_t Capacity>
class StaticJsonDocument {
public:
    std::map<std::string, JsonVariant> _map;
    std::map<std::string, JsonObject> _nested;

    JsonVariant& operator[](const std::string& key) {
        return _map[key];
    }

    JsonObject& createNestedObject(const std::string& key) {
        return _nested[key];
    }
};

enum DeserializationError {
    Ok,
    Invalid
};

inline bool operator!(DeserializationError err) {
    return err == Ok;
}

template<size_t Capacity>
inline DeserializationError deserializeJson(StaticJsonDocument<Capacity>& doc, const uint8_t* data, size_t len) {
    std::string s((const char*)data, len);
    std::string clean;
    for (char c : s) {
        if (c != ' ' && c != '{' && c != '}' && c != '\n' && c != '\r' && c != '\t') {
            clean += c;
        }
    }
    std::stringstream ss(clean);
    std::string item;
    while (std::getline(ss, item, ',')) {
        size_t colon = item.find(':');
        if (colon == std::string::npos) continue;
        std::string key = item.substr(0, colon);
        std::string val = item.substr(colon + 1);
        if (key.front() == '"') key = key.substr(1);
        if (key.back() == '"') key = key.substr(0, key.length() - 1);
        if (val.front() == '"') val = val.substr(1);
        if (val.back() == '"') val = val.substr(0, val.length() - 1);
        doc._map[key] = val;
    }
    return Ok;
}

template<size_t Capacity>
inline size_t serializeJson(const StaticJsonDocument<Capacity>& doc, char* buffer) {
    std::stringstream ss;
    ss << "{";
    bool first = true;
    for (auto const& [key, val] : doc._map) {
        if (!first) ss << ",";
        first = false;
        ss << "\"" << key << "\":";
        const char* str = val;
        std::string s_val(str ? str : "");
        if (s_val == "true" || s_val == "false" || (!s_val.empty() && std::isdigit(s_val[0])) || (!s_val.empty() && s_val[0] == '-' && std::isdigit(s_val[1]))) {
            ss << s_val;
        } else {
            ss << "\"" << s_val << "\"";
        }
    }
    for (auto const& [key, nested_obj] : doc._nested) {
        if (!first) ss << ",";
        first = false;
        ss << "\"" << key << "\":{";
        bool nested_first = true;
        for (auto const& [nkey, nval] : nested_obj._map) {
            if (!nested_first) ss << ",";
            nested_first = false;
            ss << "\"" << nkey << "\":";
            const char* str = nval;
            std::string s_val(str ? str : "");
            if (s_val == "true" || s_val == "false" || (!s_val.empty() && std::isdigit(s_val[0])) || (!s_val.empty() && s_val[0] == '-' && std::isdigit(s_val[1]))) {
                ss << s_val;
            } else {
                ss << "\"" << s_val << "\"";
            }
        }
        ss << "}";
    }
    ss << "}";
    std::string out = ss.str();
    strcpy(buffer, out.c_str());
    return out.length();
}
