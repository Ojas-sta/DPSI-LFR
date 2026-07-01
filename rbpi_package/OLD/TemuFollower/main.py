import time
import cv2
from vision import VisionAgent
from control import ControlAgent
from hardware import RobotHardware

def main():
    print("Initializing Robot Modules...")
    
    # Initialize Hardware
    hw = RobotHardware(left_pin=17, right_pin=27)
    
    # Initialize Vision
    # target_x_center is half of resolution width (320 / 2 = 160)
    vision = VisionAgent(resolution=(320, 240))
    
    # Initialize Control
    # base_speed is 1.0 to maximize speed (punish for being slow)
    control = ControlAgent(target_x_center=160, base_speed=1.0)
    
    print("Robot initialized. Starting main loop.")
    
    try:
        # Give camera time to warm up
        time.sleep(1.0)
        
        print("[Main] Starting continuous camera feed...")
        for frame in vision.get_frame():
            # 1. Process visual input
            vision_data = vision.process_frame(frame)
            
            # 2. Compute non-linear PID control / state machine
            left_speed, right_speed = control.calculate_speeds(vision_data)
            
            # 3. Actuate hardware
            print(f"[Main] Sending to Hardware -> Left Speed: {left_speed:.2f}, Right Speed: {right_speed:.2f}")
            hw.set_speeds(left_speed, right_speed)
            
            # 4. Display for debugging
            cv2.imshow("Robot Vision Live", frame)
            
            if vision_data["cnn_layers"] is not None:
                if "Black_Mask" in vision_data["cnn_layers"]:
                    cv2.imshow("Vision Layer: Black Line Isolation", vision_data["cnn_layers"]["Black_Mask"])
                if "Mask_Closed" in vision_data["cnn_layers"]:
                    cv2.imshow("Vision Layer: Mask Closed (Morphology)", vision_data["cnn_layers"]["Mask_Closed"])
            
            # Exit on 'q' press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Main] 'q' pressed. Exiting loop.")
                break
            
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # 4. Cleanup
        hw.stop()
        cv2.destroyAllWindows()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
