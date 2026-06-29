#ifndef SERIAL_COMMS_H_
#define SERIAL_COMMS_H_

#include <Arduino.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include "Config.h"

// ============================================================================
// PACKET STRUCTURES
// ============================================================================

#pragma pack(push, 1)

struct CommandPacket {
    uint8_t seq_id;
    uint8_t opcode;
    uint8_t payload_length;
    uint8_t payload[32];
};

#pragma pack(pop)

// ============================================================================
// GLOBAL VARIABLES
// ============================================================================
extern QueueHandle_t g_command_queue;

// Parser state machine
enum ParserState {
    WAIT_H1,
    WAIT_H2,
    READ_SEQ,
    READ_OPCODE,
    READ_LEN,
    READ_PAYLOAD,
    READ_CRC1,
    READ_CRC2
};

static ParserState parser_state = WAIT_H1;
static CommandPacket temp_packet;
static uint8_t payload_index = 0;
static uint16_t received_crc = 0;

// ============================================================================
// CRC-16-CCITT CALCULATION
// ============================================================================

uint16_t calculateCRC16(const uint8_t* data, uint16_t length) {
    uint16_t crc = 0xFFFF;

    for (uint16_t i = 0; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }

    return crc;
}

// ============================================================================
// SERIAL PACKET PARSER
// ============================================================================

bool parseIncomingByte(uint8_t byte_in, CommandPacket& out_packet) {
    switch (parser_state) {
        case WAIT_H1:
            if (byte_in == 0xAA) {
                parser_state = WAIT_H2;
            }
            break;

        case WAIT_H2:
            if (byte_in == 0x55) {
                parser_state = READ_SEQ;
            } else {
                parser_state = WAIT_H1;
            }
            break;

        case READ_SEQ:
            temp_packet.seq_id = byte_in;
            parser_state = READ_OPCODE;
            break;

        case READ_OPCODE:
            temp_packet.opcode = byte_in;
            parser_state = READ_LEN;
            break;

        case READ_LEN:
            temp_packet.payload_length = byte_in;
            if (temp_packet.payload_length > 32) {
                parser_state = WAIT_H1;
            } else if (temp_packet.payload_length == 0) {
                parser_state = READ_CRC1;
            } else {
                payload_index = 0;
                parser_state = READ_PAYLOAD;
            }
            break;

        case READ_PAYLOAD:
            temp_packet.payload[payload_index++] = byte_in;
            if (payload_index >= temp_packet.payload_length) {
                parser_state = READ_CRC1;
            }
            break;

        case READ_CRC1:
            received_crc = byte_in;
            parser_state = READ_CRC2;
            break;

        case READ_CRC2:
            received_crc |= ((uint16_t)byte_in << 8);

            uint8_t crc_buffer[35];
            crc_buffer[0] = temp_packet.seq_id;
            crc_buffer[1] = temp_packet.opcode;
            crc_buffer[2] = temp_packet.payload_length;
            for (uint8_t i = 0; i < temp_packet.payload_length; i++) {
                crc_buffer[3 + i] = temp_packet.payload[i];
            }

            uint16_t calculated_crc = calculateCRC16(crc_buffer, 3 + temp_packet.payload_length);

            parser_state = WAIT_H1;

            if (calculated_crc == received_crc) {
                out_packet = temp_packet;
                return true;
            }
            break;
    }

    return false;
}

// ============================================================================
// TELEMETRY TRANSMISSION
// ============================================================================

void sendTelemetryPacket(uint16_t bitmask, float yaw, int16_t error) {
    static uint8_t seq = 0;

    uint8_t packet[17];
    packet[0] = 0xAA;
    packet[1] = 0x55;
    packet[2] = seq++;
    packet[3] = OPCODE_REPORT_TELEMETRY;
    packet[4] = 10;

    packet[5] = (bitmask >> 8) & 0xFF;
    packet[6] = bitmask & 0xFF;

    memcpy(&packet[7], &yaw, 4);

    packet[11] = (error >> 8) & 0xFF;
    packet[12] = error & 0xFF;

    packet[13] = 0;
    packet[14] = 0;

    uint16_t crc = calculateCRC16(&packet[2], 11);
    packet[15] = crc & 0xFF;
    packet[16] = (crc >> 8) & 0xFF;

    Serial.write(packet, 17);
}

void sendTurnComplete(uint8_t turn_type, uint8_t status) {
    static uint8_t seq = 0;

    uint8_t packet[11];
    packet[0] = 0xAA;
    packet[1] = 0x55;
    packet[2] = seq++;
    packet[3] = OPCODE_TURN_COMPLETE;
    packet[4] = 2;
    packet[5] = turn_type;
    packet[6] = status;

    uint16_t crc = calculateCRC16(&packet[2], 5);
    packet[7] = crc & 0xFF;
    packet[8] = (crc >> 8) & 0xFF;

    Serial.write(packet, 9);
}

void sendHeartbeatPong(uint16_t uptime_sec) {
    static uint8_t seq = 0;

    uint8_t packet[11];
    packet[0] = 0xAA;
    packet[1] = 0x55;
    packet[2] = seq++;
    packet[3] = OPCODE_HEARTBEAT_PONG;
    packet[4] = 2;
    packet[5] = (uptime_sec >> 8) & 0xFF;
    packet[6] = uptime_sec & 0xFF;

    uint16_t crc = calculateCRC16(&packet[2], 5);
    packet[7] = crc & 0xFF;
    packet[8] = (crc >> 8) & 0xFF;

    Serial.write(packet, 9);
}

#endif // SERIAL_COMMS_H_
