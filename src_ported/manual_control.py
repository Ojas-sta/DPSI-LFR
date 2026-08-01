import sys
import tty
import termios
import time
from hal.motor import IBT2Motor, DriveBase

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    print("Initializing Manual Mode...")
    left_motor = IBT2Motor(rpwm_pin=12, lpwm_pin=13, r_en_pin=5, l_en_pin=6)
    right_motor = IBT2Motor(rpwm_pin=18, lpwm_pin=19, r_en_pin=20, l_en_pin=21)
    drive_base = DriveBase(left_motor, right_motor)
    
    speed = 0.5
    print("Manual Control Active. Use W/A/S/D to drive, Space to stop. Q to quit.")
    print("Press 1 for 30% speed, 2 for 60% speed, 3 for 100% speed.")
    
    try:
        while True:
            ch = getch().lower()
            if ch == 'q':
                break
            elif ch == '1':
                speed = 0.3
                print("\r\nSpeed set to 30%")
            elif ch == '2':
                speed = 0.6
                print("\r\nSpeed set to 60%")
            elif ch == '3':
                speed = 1.0
                print("\r\nSpeed set to 100%")
            elif ch == 'w':
                drive_base.drive(speed, speed)
            elif ch == 's':
                drive_base.drive(-speed, -speed)
            elif ch == 'a':
                drive_base.drive(-speed, speed)
            elif ch == 'd':
                drive_base.drive(speed, -speed)
            elif ch == ' ':
                drive_base.stop()
    finally:
        drive_base.stop()
        print("\r\nExiting Manual Mode.")

if __name__ == "__main__":
    main()
