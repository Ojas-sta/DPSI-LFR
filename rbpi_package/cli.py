import curses
import os
import subprocess
import time
import sys
import threading
from hardware import RobotHardware
from feedback import FeedbackController

def load_ascii_art():
    """Safely loads and trims ascii-art.txt for the header."""
    paths = ["ascii-art.txt", "../ascii-art.txt", "/Users/roopalisingh/DPSI-LFR/ascii-art.txt"]
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    # Strip trailing newlines and carriage returns
                    return [line.rstrip("\r\n") for line in f]
        except Exception:
            pass
    return []

def draw_compass(stdscr, y, x, yaw, color_blue, color_purple):
    """Renders a beautiful dynamic 8-way compass based on the IMU yaw heading."""
    try:
        # Normalize yaw to 0-360 degrees
        angle = yaw
        if angle < 0:
            angle += 360
            
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        dir_idx = int(((angle + 22.5) % 360) / 45)
        cardinal = dirs[dir_idx]
        
        # Arrows pointing to heading
        pointers = [" ↑ ", " ↗ ", " → ", " ↘ ", " ↓ ", " ↙ ", " ← ", " ↖ "]
        ptr_char = pointers[dir_idx]
        
        stdscr.addstr(y,     x, "    N    ", color_blue)
        stdscr.addstr(y + 1, x, " NW | NE ", color_purple)
        stdscr.addstr(y + 2, x, f"W -{ptr_char}- E", color_purple | curses.A_BOLD)
        stdscr.addstr(y + 3, x, " SW | SE ", color_purple)
        stdscr.addstr(y + 4, x, "    S    ", color_blue)
        
        # Display raw heading below the compass disc
        stdscr.addstr(y + 5, x - 2, f" Heading: {yaw:+.1f}° ", color_blue | curses.A_REVERSE | curses.A_BOLD)
    except Exception:
        pass


def draw_box(stdscr, y, x, height, width, title="", color_pair=0):
    """Draws a themed bordered box in curses with an optional title."""
    try:
        # Draw horizontal lines
        stdscr.hline(y, x, curses.ACS_HLINE, width, color_pair)
        stdscr.hline(y + height - 1, x, curses.ACS_HLINE, width, color_pair)
        # Draw vertical lines
        stdscr.vline(y, x, curses.ACS_VLINE, height, color_pair)
        stdscr.vline(y, x + width - 1, curses.ACS_VLINE, height, color_pair)
        # Draw corner characters
        stdscr.addch(y, x, curses.ACS_ULCORNER, color_pair)
        stdscr.addch(y, x + width - 1, curses.ACS_URCORNER, color_pair)
        stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER, color_pair)
        stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER, color_pair)
        
        # Add title text if provided
        if title:
            stdscr.addstr(y, x + 2, f" {title} ", curses.A_BOLD | color_pair)
    except Exception:
        pass

def draw_chassis(stdscr, y, x, left_speed, right_speed, color_blue, color_purple, color_green, color_red):
    """
    Renders a detailed 3-wheel differential ASCII chassis with:
    - 2 rear wheels + 1 front caster
    - Real-time speeds directly next to the rear wheels, color-coded:
      * Green for forward (positive values)
      * Red for reverse (negative values)
    """
    try:
        # 1. Front Caster
        stdscr.addstr(y,     x + 18, "[ Caster ]", color_blue)
        stdscr.addstr(y + 1, x + 22, "||", color_blue)
        
        # 2. Chassis body frame
        stdscr.addstr(y + 2, x + 17, "+-----------+", color_purple)
        stdscr.addstr(y + 3, x + 17, "|           |", color_purple)
        stdscr.addstr(y + 4, x + 17, "|  CHASSIS  |", color_purple)
        stdscr.addstr(y + 5, x + 17, "|           |", color_purple)
        stdscr.addstr(y + 6, x + 17, "+-----------+", color_purple)
        
        # 3. Axle Links
        stdscr.addstr(y + 4, x + 14, "===", color_purple)
        stdscr.addstr(y + 4, x + 30, "===", color_purple)
        
        # 4. Rear Wheels
        # Left Wheel
        stdscr.addstr(y + 3, x + 7, "+-----+", color_blue)
        stdscr.addstr(y + 4, x + 7, "|L-WHL|", color_blue)
        stdscr.addstr(y + 5, x + 7, "+-----+", color_blue)
        
        # Right Wheel
        stdscr.addstr(y + 3, x + 33, "+-----+", color_blue)
        stdscr.addstr(y + 4, x + 33, "|R-WHL|", color_blue)
        stdscr.addstr(y + 5, x + 33, "+-----+", color_blue)
        
        # 5. Speeds directly next to wheels (color-coded)
        left_color = color_green if left_speed >= 0 else color_red
        right_color = color_green if right_speed >= 0 else color_red
        
        left_str = f"{left_speed:+.2f}"
        right_str = f"{right_speed:+.2f}"
        
        # Draw left speed on the left side of Left Wheel
        stdscr.addstr(y + 4, x, f" {left_str} ", left_color | curses.A_BOLD)
        
        # Draw right speed on the right side of Right Wheel
        stdscr.addstr(y + 4, x + 41, f" {right_str} ", right_color | curses.A_BOLD)
    except Exception:
        pass

def check_for_updates(stdscr):
    """Self-Updating Mechanism checking GitHub for new commits, styled for theme."""
    stdscr.clear()
    stdscr.addstr(1, 2, "Checking for updates from GitHub...", curses.color_pair(5) | curses.A_BOLD)
    stdscr.refresh()
    
    try:
        # Check if there are updates
        subprocess.check_call(["git", "fetch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        status = subprocess.check_output(["git", "status", "-uno"]).decode("utf-8")
        
        if "Your branch is behind" in status:
            stdscr.addstr(3, 2, "Updates found! Pulling latest code...", curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            subprocess.check_call(["git", "pull"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            stdscr.addstr(5, 2, "Installing updated dependencies...", curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".", "--break-system-packages"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            stdscr.addstr(7, 2, "Update complete! Press any key to restart.", curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()
            stdscr.getch()
            
            # Restart the script
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            stdscr.addstr(3, 2, "Up to date.", curses.color_pair(3) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(0.5)
    except Exception as e:
        stdscr.addstr(3, 2, f"Failed to check for updates: {e}", curses.color_pair(4) | curses.A_BOLD)
        stdscr.refresh()
        time.sleep(1.0)

def run_tui(stdscr):
    # Initialize Color Pairs for Blue/Purple theme
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)       # Blue borders & accents
    curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)    # Purple/Magenta chassis & headers
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)      # Green forward/connected/active
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)        # Red reverse/disconnected/muted
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)       # Cyan fallback
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLACK)      # White standard text
    
    # Force the window background to be solid black
    stdscr.bkgd(' ', curses.color_pair(6))
    
    # Run self-updater on startup
    check_for_updates(stdscr)
    
    # Enable non-blocking keyboard input
    stdscr.nodelay(True)
    curses.curs_set(0) # Hide cursor
    
    # Initialize hardware and feedback controller
    robot = RobotHardware()
    feedback = FeedbackController()
    
    # Preload ASCII art
    art_lines = load_ascii_art()
    
    # Interactive variables
    mode = "AUTO"
    armed = False
    status_msg = "Initialized"
    speed_cap = 1.0        # Default 100% speed cap
    turn_speed_cap = 1.0   # Default 100% turn speed cap (customizable)
    led_enabled = True     # LEDs enabled by default
    buzzer_enabled = True  # Buzzer enabled by default
    
    # Boot feedback indicator (red solid indicating disarmed initially)
    feedback.indicate_disarmed()
    
    key_timestamps = {}

    while True:
        # Read terminal dimensions dynamically
        max_y, max_x = stdscr.getmaxyx()
        
        # Ensure screen buffer is cleared
        stdscr.clear()
        
        # Check for active calibration progress screen
        if robot.is_calibrating:
            box_h = 8
            box_w = 60
            box_y = max(0, (max_y - box_h) // 2)
            box_x = max(0, (max_x - box_w) // 2)
            
            draw_box(stdscr, box_y, box_x, box_h, box_w, "IMU GYROSCOPE CALIBRATION", curses.color_pair(1))
            
            stdscr.addstr(box_y + 2, box_x + 4, "Calibrating MPU6050 sensor. Keep robot still!", curses.color_pair(6) | curses.A_BOLD)
            stdscr.addstr(box_y + 3, box_x + 4, "Press [S] to skip calibration...", curses.color_pair(5) | curses.A_BOLD)
            
            progress = robot.calibration_progress
            bar_len = 48
            filled_len = int(progress * bar_len)
            bar = "█" * filled_len + "░" * (bar_len - filled_len)
            
            stdscr.addstr(box_y + 4, box_x + 5, f"[{bar}] {progress*100:3.0f}%", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(box_y + 5, box_x + 5, f"Time remaining: {robot.calibration_duration * (1.0 - progress):2.0f}s", curses.color_pair(6))
            
            stdscr.refresh()
            
            # Listen for skip key
            c_cal = stdscr.getch()
            if c_cal != -1:
                try:
                    k_cal = chr(c_cal).lower()
                    if k_cal == 's':
                        robot.skip_calibration()
                except Exception:
                    pass
                    
            time.sleep(0.1)
            continue
        
        # 1. RENDER HEADER BANNERS
        y_ptr = 1
        # If terminal is big enough, draw full centered ascii-art.txt
        if max_y >= 38 and max_x >= 188 and art_lines:
            for line in art_lines:
                if y_ptr >= max_y - 2:
                    break
                x_offset = max((max_x - 185) // 2, 0)
                try:
                    stdscr.addstr(y_ptr, x_offset, line[:max_x - x_offset], curses.color_pair(1))
                except Exception:
                    pass
                y_ptr += 1
            y_ptr += 1
        # Else draw a compact, clean banner
        elif max_y >= 20 and max_x >= 45:
            banner = [
                "  ___  ___  ___ ___   _    ___ ___  ",
                " |   \\| _ \\/ __|_ _| | |  | __| _ \\ ",
                " | |) |  _/\\__ \\| |  | |__| _||   / ",
                " |___/|_|  |___/___| |____|_| |_|_\\ ",
                " ================================== "
            ]
            x_offset = max((max_x - 36) // 2, 0)
            for line in banner:
                try:
                    stdscr.addstr(y_ptr, x_offset, line, curses.color_pair(2) | curses.A_BOLD)
                except Exception:
                    pass
                y_ptr += 1
            y_ptr += 1
        else:
            # Simple text header for very small screens
            title = "DPSI LFR Master Setup & Control"
            x_offset = max((max_x - len(title)) // 2, 0)
            try:
                stdscr.addstr(y_ptr, x_offset, title, curses.color_pair(1) | curses.A_BOLD)
            except Exception:
                pass
            y_ptr += 2

        # Check if we should use side-by-side or stacked layout
        is_side_by_side = (max_x >= 110)
        
        if is_side_by_side:
            # --- SIDE-BY-SIDE LAYOUT ---
            left_x = 2
            
            # Connection badge: Green [ CONNECTED ] or Red [ DISCONNECTED ]
            badge_text = " [ CONNECTED ] " if robot.is_connected else " [ DISCONNECTED ] "
            badge_color = curses.color_pair(3) if robot.is_connected else curses.color_pair(4)
            stdscr.addstr(y_ptr, left_x, "Connection: ", curses.color_pair(6) | curses.A_BOLD)
            stdscr.addstr(y_ptr, left_x + 12, badge_text, badge_color | curses.A_REVERSE | curses.A_BOLD)
            
            # Port Info
            port_mode = "MOCK MODE" if robot.is_mock else "ACTIVE"
            port_color = curses.color_pair(4) if robot.is_mock else curses.color_pair(3)
            stdscr.addstr(y_ptr + 1, left_x, f"Port: {robot.port_name} ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 1, left_x + len(robot.port_name) + 7, f"[{port_mode}]", port_color | curses.A_BOLD)
            
            # Speed Cap Visual Progress Bar
            cap_val = int(speed_cap * 10)
            bar = "█" * cap_val + "░" * (10 - cap_val)
            stdscr.addstr(y_ptr + 2, left_x, f"Speed Cap: {speed_cap*100:3.0f}%  [{bar}]", curses.color_pair(2) | curses.A_BOLD)
            
            # Turn Speed Scale Visual Progress Bar
            t_cap_val = int(turn_speed_cap * 10)
            t_bar = "█" * t_cap_val + "░" * (10 - t_cap_val)
            stdscr.addstr(y_ptr + 3, left_x, f"Turn Scale: {turn_speed_cap*100:3.0f}%  [{t_bar}]", curses.color_pair(2) | curses.A_BOLD)
            
            # Trim Bias Slider (Range -0.3 to 0.3 mapped to 13 chars)
            trim_val = int(robot.trim_bias * 20) # scale to -6 to +6
            slider_idx = 6 + trim_val
            bar_chars = ["-"] * 13
            bar_chars[6] = "|"
            bar_chars[max(0, min(12, slider_idx))] = "*"
            bar_str = "".join(bar_chars)
            stdscr.addstr(y_ptr + 4, left_x, f"Trim Bias: {robot.trim_bias:+.2f}  [L < {bar_str} > R]", curses.color_pair(2) | curses.A_BOLD)
            
            # Mode & Arm states
            m_color = curses.color_pair(3) if mode == "AUTO" else curses.color_pair(2)
            a_color = curses.color_pair(3) if armed else curses.color_pair(4)
            stdscr.addstr(y_ptr + 5, left_x, f"Mode: {mode}", m_color | curses.A_BOLD)
            stdscr.addstr(y_ptr + 5, left_x + 20, f"Status: {'ARMED' if armed else 'DISARMED'}", a_color | curses.A_BOLD)
            
            # LED & Buzzer status
            led_str = "[ ON ]" if led_enabled else "[ OFF ]"
            buz_str = "[ ON ]" if buzzer_enabled else "[ OFF ]"
            led_col = curses.color_pair(3) if led_enabled else curses.color_pair(4)
            buz_col = curses.color_pair(3) if buzzer_enabled else curses.color_pair(4)
            stdscr.addstr(y_ptr + 6, left_x, "LEDs:   ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 6, left_x + 8, led_str, led_col | curses.A_BOLD)
            stdscr.addstr(y_ptr + 6, left_x + 18, "Buzzer: ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 6, left_x + 26, buz_str, buz_col | curses.A_BOLD)
            
            # Steer Correction & Assist status
            sc_str = "[ ON ]" if robot.steer_correction_enabled else "[ OFF ]"
            sa_str = "[ ON ]" if robot.steer_assist_enabled else "[ OFF ]"
            sc_col = curses.color_pair(3) if robot.steer_correction_enabled else curses.color_pair(4)
            sa_col = curses.color_pair(3) if robot.steer_assist_enabled else curses.color_pair(4)
            stdscr.addstr(y_ptr + 7, left_x, "Steer Corr:   ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 7, left_x + 12, sc_str, sc_col | curses.A_BOLD)
            stdscr.addstr(y_ptr + 7, left_x + 22, "Steer Assist: ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 7, left_x + 36, sa_str, sa_col | curses.A_BOLD)
            
            # Draw ASCII Chassis Diagram
            chassis_y = y_ptr + 9
            draw_chassis(stdscr, chassis_y, left_x, robot.left_speed, robot.right_speed, 
                         curses.color_pair(1), curses.color_pair(2), curses.color_pair(3), curses.color_pair(4))
            
            # Draw dynamic IMU Compass right next to the Chassis
            draw_compass(stdscr, chassis_y, left_x + 47, robot.yaw, curses.color_pair(1), curses.color_pair(2))
            
            # Draw Keyboard Controls Guide
            help_y = chassis_y + 8
            stdscr.addstr(help_y, left_x, "Controls Guide:", curses.color_pair(1) | curses.A_BOLD | curses.A_UNDERLINE)
            stdscr.addstr(help_y + 1, left_x, "[E] Arm           [Q] Disarm         [Space] ESTOP", curses.color_pair(6))
            stdscr.addstr(help_y + 2, left_x, "[M] Toggle Auto/Manual Mode          [/] Reset Yaw", curses.color_pair(6))
            stdscr.addstr(help_y + 3, left_x, "[W,S] Drive Fwd/Rev   [A,D] Turn L/R (Manual only)", curses.color_pair(6))
            stdscr.addstr(help_y + 4, left_x, "[ [ ] Dec Fwd Cap     [ ] ] Inc Fwd Cap", curses.color_pair(6))
            stdscr.addstr(help_y + 5, left_x, "[ { ] Dec Turn Cap    [ } ] Inc Turn Cap", curses.color_pair(6))
            stdscr.addstr(help_y + 6, left_x, "[ , ] Trim Left       [ . ] Trim Right", curses.color_pair(6))
            stdscr.addstr(help_y + 7, left_x, "[C] Steer Correction  [V] Steer Assist", curses.color_pair(6))
            stdscr.addstr(help_y + 8, left_x, "[L] Toggle LEDs       [B] Toggle Buzzer", curses.color_pair(6))
            stdscr.addstr(help_y + 9, left_x, "[P] Switch Serial Port   [X] Exit CLI", curses.color_pair(6))
            
            # Display recent System Log
            stdscr.addstr(help_y + 11, left_x, f"System Log: {status_msg}", curses.color_pair(2) | curses.A_BOLD)
            
            # --- Serial Monitor Bordered Box ---
            mon_x = 65
            mon_w = max_x - mon_x - 2
            mon_h = (help_y + 12) - y_ptr
            
            draw_box(stdscr, y_ptr, mon_x, mon_h, mon_w, "Serial Telemetry Monitor (Last 10 lines)", curses.color_pair(1))
            
            # Display incoming telemetry lines inside the box
            with robot.telemetry_lock:
                log_lines = list(robot.telemetry_log)
                
            for idx, line in enumerate(log_lines):
                truncated = line[:mon_w - 4]
                try:
                    stdscr.addstr(y_ptr + 1 + idx, mon_x + 2, truncated, curses.color_pair(6))
                except Exception:
                    pass
        else:
            # --- STACKED RESPONSIVE LAYOUT (Smaller Screens) ---
            left_x = 2
            
            badge_text = " [ CONNECTED ] " if robot.is_connected else " [ DISCONNECTED ] "
            badge_color = curses.color_pair(3) if robot.is_connected else curses.color_pair(4)
            stdscr.addstr(y_ptr, left_x, "Connection: ", curses.color_pair(6) | curses.A_BOLD)
            stdscr.addstr(y_ptr, left_x + 12, badge_text, badge_color | curses.A_REVERSE | curses.A_BOLD)
            
            port_mode = "MOCK MODE" if robot.is_mock else "ACTIVE"
            port_color = curses.color_pair(4) if robot.is_mock else curses.color_pair(3)
            stdscr.addstr(y_ptr + 1, left_x, f"Port: {robot.port_name} ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 1, left_x + len(robot.port_name) + 7, f"[{port_mode}]", port_color | curses.A_BOLD)
            
            cap_val = int(speed_cap * 10)
            bar = "█" * cap_val + "░" * (10 - cap_val)
            stdscr.addstr(y_ptr + 2, left_x, f"Speed Cap: {speed_cap*100:3.0f}%  [{bar}]", curses.color_pair(2) | curses.A_BOLD)
            
            # Turn Speed Scale Visual Progress Bar
            t_cap_val = int(turn_speed_cap * 10)
            t_bar = "█" * t_cap_val + "░" * (10 - t_cap_val)
            stdscr.addstr(y_ptr + 3, left_x, f"Turn Cap:  {turn_speed_cap*100:3.0f}%  [{t_bar}]", curses.color_pair(2) | curses.A_BOLD)
            
            # Trim Bias Slider
            trim_val = int(robot.trim_bias * 20)
            slider_idx = 6 + trim_val
            bar_chars = ["-"] * 13
            bar_chars[6] = "|"
            bar_chars[max(0, min(12, slider_idx))] = "*"
            bar_str = "".join(bar_chars)
            stdscr.addstr(y_ptr + 4, left_x, f"Trim Bias: {robot.trim_bias:+.2f}  [L < {bar_str} > R]", curses.color_pair(2) | curses.A_BOLD)
            
            m_color = curses.color_pair(3) if mode == "AUTO" else curses.color_pair(2)
            a_color = curses.color_pair(3) if armed else curses.color_pair(4)
            stdscr.addstr(y_ptr + 5, left_x, f"Mode: {mode}", m_color | curses.A_BOLD)
            stdscr.addstr(y_ptr + 5, left_x + 20, f"Status: {'ARMED' if armed else 'DISARMED'}", a_color | curses.A_BOLD)
            
            # Steer Correction & Assist status
            sc_str = "[ ON ]" if robot.steer_correction_enabled else "[ OFF ]"
            sa_str = "[ ON ]" if robot.steer_assist_enabled else "[ OFF ]"
            sc_col = curses.color_pair(3) if robot.steer_correction_enabled else curses.color_pair(4)
            sa_col = curses.color_pair(3) if robot.steer_assist_enabled else curses.color_pair(4)
            stdscr.addstr(y_ptr + 6, left_x, "Steer: ", curses.color_pair(6))
            stdscr.addstr(y_ptr + 6, left_x + 7, f"Corr:{sc_str}", sc_col | curses.A_BOLD)
            stdscr.addstr(y_ptr + 6, left_x + 20, f"Assist:{sa_str}", sa_col | curses.A_BOLD)
            
            # Chassis (Row y_ptr + 8)
            chassis_y = y_ptr + 8
            draw_chassis(stdscr, chassis_y, left_x, robot.left_speed, robot.right_speed, 
                         curses.color_pair(1), curses.color_pair(2), curses.color_pair(3), curses.color_pair(4))
            
            # Compass next to it if screen is wide enough, else stack it below
            if max_x >= 70:
                draw_compass(stdscr, chassis_y, left_x + 47, robot.yaw, curses.color_pair(1), curses.color_pair(2))
                mon_y = chassis_y + 8
            else:
                draw_compass(stdscr, chassis_y + 7, left_x + 15, robot.yaw, curses.color_pair(1), curses.color_pair(2))
                mon_y = chassis_y + 15
            
            # Serial Telemetry Box below Chassis/Compass
            mon_h = max_y - mon_y - 2
            
            if mon_h > 4:
                draw_box(stdscr, mon_y, left_x, mon_h, max_x - 4, "Serial Telemetry Monitor (Last 10 lines)", curses.color_pair(1))
                with robot.telemetry_lock:
                    log_lines = list(robot.telemetry_log)
                
                # Display lines that fit inside the box
                display_count = min(mon_h - 2, len(log_lines), 10)
                start_log_idx = max(0, len(log_lines) - display_count)
                for idx in range(display_count):
                    line = log_lines[start_log_idx + idx]
                    truncated = line[:max_x - 8]
                    try:
                        stdscr.addstr(mon_y + 1 + idx, left_x + 2, truncated, curses.color_pair(6))
                    except Exception:
                        pass
            
            # Draw compact control guide line at the bottom
            if max_y > 2:
                help_msg = "[E] Arm [Q] Disarm [Space] Stop [,] Trim L [.] Trim R [C] Corr [V] Assist [{,}] Turn [X] Exit"
                try:
                    stdscr.addstr(max_y - 1, left_x, help_msg[:max_x - 4], curses.color_pair(1) | curses.A_BOLD)
                except Exception:
                    pass

        # 3. REFRESH AND HANDLE KEY INPUTS
        stdscr.refresh()
        
        c = stdscr.getch()
        now = time.time()
        if c != -1:
            try:
                k = chr(c).lower()
                if k in ['w', 's', 'a', 'd']:
                    key_timestamps[k] = now
            except Exception:
                pass

            if c in (ord('x'), ord('X')):
                break
            
            # Arm/Disarm Keyboard Controls
            elif c in (ord('e'), ord('E')):
                armed = True
                robot.send_arm(True)
                if led_enabled:
                    feedback.indicate_armed()
                status_msg = "Sent ARM command."
                
            elif c in (ord('q'), ord('Q')):
                armed = False
                robot.send_arm(False)
                if led_enabled:
                    feedback.indicate_disarmed()
                status_msg = "Sent DISARM command."
                
            # Mode Control
            elif c in (ord('m'), ord('M')):
                mode = "MANUAL" if mode == "AUTO" else "AUTO"
                robot.set_speeds(0, 0)
                status_msg = f"Switched to Pi {mode} mode."
                
            # Emergency Stop
            elif c == ord(' '):
                robot.stop()
                key_timestamps.clear()
                status_msg = "Emergency Stop executed!"
                
            # Speed Cap Tuning using `[` and `]` (10% increments, clamped between 10% and 100%)
            elif c == ord('['):
                speed_cap = max(0.1, speed_cap - 0.1)
                status_msg = f"Speed Cap set to {speed_cap*100:.0f}%"
                
            elif c == ord(']'):
                speed_cap = min(1.0, speed_cap + 0.1)
                status_msg = f"Speed Cap set to {speed_cap*100:.0f}%"
                
            # Turn Speed Cap Tuning using `{` and `}` (Shift + [ and ])
            elif c == ord('{'):
                turn_speed_cap = max(0.1, turn_speed_cap - 0.1)
                status_msg = f"Turn Speed Cap set to {turn_speed_cap*100:.0f}%"
                
            elif c == ord('}'):
                turn_speed_cap = min(1.0, turn_speed_cap + 0.1)
                status_msg = f"Turn Speed Cap set to {turn_speed_cap*100:.0f}%"
                
            # Drift Trim Bias Adjustments
            elif c == ord(','):
                robot.adjust_trim(-0.01)
                status_msg = f"Trim Bias shifted Left: {robot.trim_bias:+.2f}"
                
            elif c == ord('.'):
                robot.adjust_trim(0.01)
                status_msg = f"Trim Bias shifted Right: {robot.trim_bias:+.2f}"
                
            # Steer Correction Toggle
            elif c in (ord('c'), ord('C')):
                robot.toggle_steer_correction()
                status_msg = f"Steer Correction {'Enabled' if robot.steer_correction_enabled else 'Disabled'}."
                
            # Steer Assist Toggle
            elif c in (ord('v'), ord('V')):
                robot.toggle_steer_assist()
                status_msg = f"Steer Assist {'Enabled' if robot.steer_assist_enabled else 'Disabled'}."
                
            # Yaw Reset
            elif c == ord('/'):
                robot.reset_yaw()
                status_msg = "IMU Yaw reset to 0.0° and re-calibrated bias."
                
            # LEDs Toggle Control
            elif c in (ord('l'), ord('L')):
                led_enabled = not led_enabled
                if not led_enabled:
                    feedback.red_led.off()
                    feedback.green_led.off()
                    status_msg = "LEDs Disabled/Muted."
                else:
                    if armed:
                        feedback.indicate_armed()
                    else:
                        feedback.indicate_disarmed()
                    status_msg = "LEDs Enabled."
                    
            # Buzzer Toggle Control
            elif c in (ord('b'), ord('B')):
                buzzer_enabled = not buzzer_enabled
                status_msg = f"Buzzer {'Enabled' if buzzer_enabled else 'Muted'}."
                if buzzer_enabled and feedback.has_buzzer:
                    try:
                        feedback.buzzer.on()
                        def stop_beep():
                            time.sleep(0.1)
                            try:
                                feedback.buzzer.off()
                            except Exception:
                                pass
                        threading.Thread(target=stop_beep, daemon=True).start()
                    except Exception:
                        pass
                else:
                    if feedback.has_buzzer:
                        try:
                            feedback.buzzer.off()
                        except Exception:
                            pass
                            
            # Serial Port Switching Control
            elif c in (ord('p'), ord('P')):
                new_port = '/dev/ttyUSB0' if robot.port_name == '/dev/serial0' else '/dev/serial0'
                robot.switch_port(new_port)
                status_msg = f"Switched port to {new_port}."
                
        # Manual Drive Controls (Only works if in MANUAL mode and ARMED)
        if mode == "MANUAL" and armed:
            # Determine active movement keys based on 0.15s decay
            # Standard terminals don't have keyup events; this decay tracks if keys are held
            active_w = (now - key_timestamps.get('w', 0)) < 0.15
            active_s = (now - key_timestamps.get('s', 0)) < 0.15
            active_a = (now - key_timestamps.get('a', 0)) < 0.15
            active_d = (now - key_timestamps.get('d', 0)) < 0.15
            
            # Base speeds scaled separately by their respective caps
            base_speed_fw = 1.0 * speed_cap
            base_speed_turn = 1.0 * turn_speed_cap
            
            if active_w and active_a:
                # W+A Combination: Curve Left (outer wheel full speed, inner wheel scaled to 40%)
                robot.set_speeds(base_speed_fw * 0.4, base_speed_fw)
                status_msg = f"Curving Left (W+A) at speed: {base_speed_fw:.2f}"
            elif active_w and active_d:
                # W+D Combination: Curve Right (inner wheel scaled to 40%, outer wheel full speed)
                robot.set_speeds(base_speed_fw, base_speed_fw * 0.4)
                status_msg = f"Curving Right (W+D) at speed: {base_speed_fw:.2f}"
            elif active_s and active_a:
                # S+A Combination: Curve Backwards Left (inner wheel scaled to 40%, outer wheel full speed)
                robot.set_speeds(-base_speed_fw * 0.4, -base_speed_fw)
                status_msg = f"Curving Back-Left (S+A) at speed: {base_speed_fw:.2f}"
            elif active_s and active_d:
                # S+D Combination: Curve Backwards Right (inner wheel full speed, outer wheel scaled to 40%)
                robot.set_speeds(-base_speed_fw, -base_speed_fw * 0.4)
                status_msg = f"Curving Back-Right (S+D) at speed: {base_speed_fw:.2f}"
            elif active_w:
                # W: Drive Forward at max speed
                robot.set_speeds(base_speed_fw, base_speed_fw)
                status_msg = f"Driving Forward at speed: {base_speed_fw:.2f}"
            elif active_s:
                # S: Drive Backward at max speed
                robot.set_speeds(-base_speed_fw, -base_speed_fw)
                status_msg = f"Driving Backward at speed: {base_speed_fw:.2f}"
            elif active_a:
                # A: Spin Left on the spot (uses custom turn scale)
                robot.set_speeds(-base_speed_turn, base_speed_turn)
                status_msg = f"Turning Left at speed: {base_speed_turn:.2f}"
            elif active_d:
                # D: Spin Right on the spot (uses custom turn scale)
                robot.set_speeds(base_speed_turn, -base_speed_turn)
                status_msg = f"Turning Right at speed: {base_speed_turn:.2f}"
            else:
                # No keys active: Auto-stop safety override
                robot.set_speeds(0.0, 0.0)
                    
        time.sleep(0.05)

def main():
    curses.wrapper(run_tui)

if __name__ == "__main__":
    main()

