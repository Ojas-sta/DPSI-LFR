import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure the mock is set up before importing hardware
mock_serial_mod = MagicMock()
mock_serial_mod.SerialException = Exception
sys.modules['serial'] = mock_serial_mod

from hardware import RobotHardware

class TestRobotHardware(unittest.TestCase):
    def setUp(self):
        # Reset the mock serial calls before each test
        mock_serial_mod.Serial.reset_mock()
        mock_serial_mod.Serial.side_effect = None
        mock_serial_mod.Serial.return_value = MagicMock()

    @patch('builtins.print')
    def test_serial_init_success_first(self, mock_print):
        # Test case where /dev/serial0 succeeds
        hw = RobotHardware()
        mock_serial_mod.Serial.assert_any_call(port='/dev/serial0', baudrate=115200, timeout=0.1)
        self.assertIsNotNone(hw.serial_port)

    @patch('builtins.print')
    def test_serial_init_fallback(self, mock_print):
        # Setup mock: /dev/serial0 raises Exception, /dev/ttyUSB0 succeeds
        def side_effect(port, **kwargs):
            if port == '/dev/serial0':
                raise Exception("Port busy")
            return MagicMock()
        
        mock_serial_mod.Serial.side_effect = side_effect
        hw = RobotHardware()
        self.assertIsNotNone(hw.serial_port)
        mock_serial_mod.Serial.assert_any_call(port='/dev/serial0', baudrate=115200, timeout=0.1)
        mock_serial_mod.Serial.assert_any_call(port='/dev/ttyUSB0', baudrate=115200, timeout=0.1)

    @patch('builtins.print')
    def test_speed_formatting_and_clamping(self, mock_print):
        mock_port = MagicMock()
        mock_port.is_open = True
        mock_serial_mod.Serial.return_value = mock_port
        
        hw = RobotHardware()
        
        # Test normal speed formatting (4 decimal places)
        hw.set_speeds(0.51234, -0.67891)
        mock_port.write.assert_called_with(b"M:0.5123,-0.6789\n")
        
        # Test clamped speed
        hw.set_speeds(1.5, -2.3)
        mock_port.write.assert_called_with(b"M:1.0000,-1.0000\n")

if __name__ == '__main__':
    unittest.main()
