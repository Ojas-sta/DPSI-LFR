import serial
import struct
import threading
import time
from typing import Optional, Dict, Any

# ============================================================================
# BINARY PROTOCOL OPCODES
# ============================================================================
OPCODE_SET_MOTOR_SPEEDS = 0x01
OPCODE_EXECUTE_TURN_90 = 0x02
OPCODE_EXECUTE_TURN_180 = 0x03
OPCODE_SET_PID_GAINS = 0x04
OPCODE_SET_MODE = 0x05
OPCODE_ACTION_GREEN_LED = 0x06
OPCODE_ACTION_RED_LED = 0x07
OPCODE_HEARTBEAT_PING = 0x0A
OPCODE_EMERGENCY_STOP = 0xFF

OPCODE_REPORT_TELEMETRY = 0x81
OPCODE_TURN_COMPLETE = 0x82
OPCODE_HEARTBEAT_PONG = 0x8A

TURN_LEFT = 0x01
TURN_RIGHT = 0x02

# ============================================================================
# CRC-16-CCITT CALCULATION
# ============================================================================

def calculate_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

# ============================================================================
# ESP32 BRIDGE CLASS
# ============================================================================

class ESPBridge:
    def __init__(self, port: str, baud_rate: int):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        self.seq_counter = 0

        self.telemetry_data: Dict[str, Any] = {
            'ir_bitmask': 0,
            'yaw': 0.0,
            'error': 0
        }

        self.turn_complete_flag = False
        self.running = False
        self.reader_thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        try:
            self.serial_conn = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=0.1,
                write_timeout=0.1
            )
            time.sleep(2)

            self.running = True
            self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.reader_thread.start()

            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def disconnect(self):
        self.running = False
        if self.reader_thread:
            self.reader_thread.join(timeout=1)
        if self.serial_conn:
            self.serial_conn.close()

    def _read_loop(self):
        parser_state = 0
        temp_packet = {}
        payload_buffer = bytearray()
        received_crc = 0

        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    byte_in = self.serial_conn.read(1)[0]

                    if parser_state == 0:  # WAIT_H1
                        if byte_in == 0xAA:
                            parser_state = 1
                    elif parser_state == 1:  # WAIT_H2
                        if byte_in == 0x55:
                            parser_state = 2
                            temp_packet = {}
                            payload_buffer = bytearray()
                        else:
                            parser_state = 0
                    elif parser_state == 2:  # READ_SEQ
                        temp_packet['seq_id'] = byte_in
                        parser_state = 3
                    elif parser_state == 3:  # READ_OPCODE
                        temp_packet['opcode'] = byte_in
                        parser_state = 4
                    elif parser_state == 4:  # READ_LEN
                        temp_packet['length'] = byte_in
                        if temp_packet['length'] == 0:
                            parser_state = 6
                        else:
                            parser_state = 5
                    elif parser_state == 5:  # READ_PAYLOAD
                        payload_buffer.append(byte_in)
                        if len(payload_buffer) >= temp_packet['length']:
                            temp_packet['payload'] = bytes(payload_buffer)
                            parser_state = 6
                    elif parser_state == 6:  # READ_CRC1
                        received_crc = byte_in
                        parser_state = 7
                    elif parser_state == 7:  # READ_CRC2
                        received_crc |= (byte_in << 8)

                        crc_data = bytearray([
                            temp_packet['seq_id'],
                            temp_packet['opcode'],
                            temp_packet['length']
                        ])
                        if temp_packet['length'] > 0:
                            crc_data.extend(temp_packet['payload'])

                        calculated_crc = calculate_crc16(bytes(crc_data))

                        if calculated_crc == received_crc:
                            self._process_packet(temp_packet)

                        parser_state = 0
                else:
                    time.sleep(0.001)
            except Exception as e:
                print(f"Read error: {e}")
                time.sleep(0.01)

    def _process_packet(self, packet: Dict[str, Any]):
        opcode = packet['opcode']

        if opcode == OPCODE_REPORT_TELEMETRY and packet['length'] == 10:
            payload = packet['payload']
            ir_bitmask = struct.unpack('>H', payload[0:2])[0]
            yaw = struct.unpack('<f', payload[2:6])[0]
            error = struct.unpack('>h', payload[6:8])[0]

            with self.lock:
                self.telemetry_data = {
                    'ir_bitmask': ir_bitmask,
                    'yaw': yaw,
                    'error': error
                }

        elif opcode == OPCODE_TURN_COMPLETE:
            with self.lock:
                self.turn_complete_flag = True

    def send_packet(self, opcode: int, payload: bytes = b''):
        with self.lock:
            seq = self.seq_counter
            self.seq_counter = (self.seq_counter + 1) % 256

        packet = bytearray([0xAA, 0x55, seq, opcode, len(payload)])
        packet.extend(payload)

        crc = calculate_crc16(bytes(packet[2:]))
        packet.extend([crc & 0xFF, (crc >> 8) & 0xFF])

        with self.lock:
            if self.serial_conn:
                self.serial_conn.write(bytes(packet))

    def send_motor_speeds(self, left_pwm: int, right_pwm: int):
        payload = struct.pack('>hh', left_pwm, right_pwm)
        self.send_packet(OPCODE_SET_MOTOR_SPEEDS, payload)

    def execute_turn_90(self, direction: str):
        dir_byte = TURN_LEFT if direction == "LEFT" else TURN_RIGHT
        with self.lock:
            self.turn_complete_flag = False
        self.send_packet(OPCODE_EXECUTE_TURN_90, bytes([dir_byte]))

    def execute_turn_180(self):
        with self.lock:
            self.turn_complete_flag = False
        self.send_packet(OPCODE_EXECUTE_TURN_180)

    def send_heartbeat(self):
        self.send_packet(OPCODE_HEARTBEAT_PING, bytes([0x01]))

    def set_mode(self, mode: int):
        self.send_packet(OPCODE_SET_MODE, bytes([mode]))

    def emergency_stop(self):
        self.send_packet(OPCODE_EMERGENCY_STOP)

    def action_green_led(self):
        self.send_packet(OPCODE_ACTION_GREEN_LED)

    def action_red_led(self):
        self.send_packet(OPCODE_ACTION_RED_LED)

    def read_telemetry(self) -> Dict[str, Any]:
        with self.lock:
            return self.telemetry_data.copy()

    def check_turn_complete(self) -> bool:
        with self.lock:
            flag = self.turn_complete_flag
            self.turn_complete_flag = False
            return flag
