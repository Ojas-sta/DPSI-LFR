import curses
import os
import subprocess
import time
import sys
from hardware import RobotHardware

def check_for_updates(stdscr):
    """Self-Updating Mechanism checking GitHub for new commits."""
    stdscr.clear()
    stdscr.addstr(1, 2, "Checking for updates from GitHub...")
    stdscr.refresh()
    
    try:
        # Check if there are updates
        subprocess.check_call(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.check_output(["git", "status", "-uno"]).decode("utf-8")
        
        if "Your branch is behind" in status:
            stdscr.addstr(3, 2, "Updates found! Pulling latest code...", curses.color_pair(1))
            stdscr.refresh()
            subprocess.check_call(["git", "pull"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            stdscr.addstr(5, 2, "Installing updated dependencies...", curses.color_pair(1))
            stdscr.refresh()
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            stdscr.addstr(7, 2, "Update complete! Press any key to restart.", curses.color_pair(2))
            stdscr.refresh()
            stdscr.getch()
            
            # Restart the script
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            stdscr.addstr(3, 2, "Up to date.", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.5)
    except Exception as e:
        stdscr.addstr(3, 2, f"Failed to check for updates (Are you in the Git repo?): {e}", curses.color_pair(3))
        stdscr.refresh()
        time.sleep(1)

def run_tui(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    
    check_for_updates(stdscr)
    
    stdscr.nodelay(True)
    robot = RobotHardware()
    
    mode = "AUTO"
    armed = False
    status_msg = "Initialized"
    
    while True:
        stdscr.clear()
        
        # Header
        stdscr.addstr(1, 2, "DPSI LFR Master Setup & Control (CLI)", curses.A_BOLD | curses.color_pair(1))
        
        # Connection
        port_name = robot.serial_port.port if robot.serial_port else 'MOCK (No Device Found)'
        stdscr.addstr(3, 2, f"Connection: {port_name}")
        
        # Status
        mode_color = curses.color_pair(2) if mode == "AUTO" else curses.color_pair(1)
        arm_color = curses.color_pair(2) if armed else curses.color_pair(3)
        
        stdscr.addstr(4, 2, f"Mode: {mode}", mode_color)
        stdscr.addstr(5, 2, f"Status: {'ARMED' if armed else 'DISARMED'}", arm_color)
        
        # Controls
        stdscr.addstr(7, 2, "Controls:", curses.A_UNDERLINE)
        stdscr.addstr(8, 2, "[E] Arm Robot   [Q] Disarm Robot")
        stdscr.addstr(9, 2, "[M] Toggle Auto/Manual Mode")
        stdscr.addstr(10, 2, "[W,A,S,D] Drive (Manual Mode only)")
        stdscr.addstr(11, 2, "[Space] Emergency Stop")
        stdscr.addstr(12, 2, "[X] Exit CLI")
        
        # Messages
        stdscr.addstr(14, 2, f"Log: {status_msg}")
        
        stdscr.refresh()
        
        c = stdscr.getch()
        
        if c != -1:
            if c in (ord('x'), ord('X')):
                break
            elif c in (ord('e'), ord('E')):
                armed = True
                robot.send_arm(True)
                status_msg = "Sent ARM command."
            elif c in (ord('q'), ord('Q')):
                armed = False
                robot.send_arm(False)
                status_msg = "Sent DISARM command."
            elif c in (ord('m'), ord('M')):
                mode = "MANUAL" if mode == "AUTO" else "AUTO"
                robot.send_mode(mode == "AUTO")
                status_msg = f"Switched to {mode} mode."
            elif c == ord(' '):
                robot.stop()
                status_msg = "Emergency Stop!"
            elif mode == "MANUAL" and armed:
                # Drive controls
                if c in (ord('w'), ord('W')):
                    robot.set_speeds(0.8, 0.8)
                    status_msg = "Driving Forward"
                elif c in (ord('s'), ord('S')):
                    robot.set_speeds(-0.8, -0.8)
                    status_msg = "Driving Backward"
                elif c in (ord('a'), ord('A')):
                    robot.set_speeds(-0.6, 0.6)
                    status_msg = "Turning Left"
                elif c in (ord('d'), ord('D')):
                    robot.set_speeds(0.6, -0.6)
                    status_msg = "Turning Right"
        
        time.sleep(0.05)

def main():
    curses.wrapper(run_tui)

if __name__ == "__main__":
    main()
