import sys
import time
import threading

sys.path.append("/Users/roopalisingh/Downloads/TemuFollower")

from feedback import FeedbackController

def run_test_case(name, num_iterations, action_func_generator):
    controller = FeedbackController()
    target_dt = 1.0 / 30.0  # 33.3ms
    stats = []
    
    # Let the controller initialize
    time.sleep(0.1)
    
    print(f"\n--- Running Test Case: {name} ---")
    for i in range(num_iterations):
        start_time = time.time()
        
        # Get the action function to call this iteration
        action = action_func_generator(controller, i)
        if action:
            action()
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Sleep remaining time
        elapsed = time.time() - start_time
        sleep_time = target_dt - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
            
        total_cycle_time = time.time() - start_time
        stats.append({
            "iteration": i,
            "api_call_duration": duration,
            "total_cycle_time": total_cycle_time
        })
        
    controller.cleanup()
    
    max_api_call = max(s["api_call_duration"] for s in stats)
    avg_api_call = sum(s["api_call_duration"] for s in stats) / len(stats)
    max_cycle = max(s["total_cycle_time"] for s in stats)
    avg_cycle = sum(s["total_cycle_time"] for s in stats) / len(stats)
    slow_calls = [s for s in stats if s["api_call_duration"] > 0.001] # >1ms
    
    print(f"Max API call: {max_api_call*1000:.2f} ms")
    print(f"Avg API call: {avg_api_call*1000:.2f} ms")
    print(f"Max cycle: {max_cycle*1000:.2f} ms")
    print(f"Avg cycle: {avg_cycle*1000:.2f} ms")
    print(f"Effective average frequency: {1.0/avg_cycle:.2f} FPS")
    print(f"Cycles with API call > 1ms: {len(slow_calls)} / {num_iterations}")
    return {
        "max_api": max_api_call * 1000,
        "avg_api": avg_api_call * 1000,
        "max_cycle": max_cycle * 1000,
        "avg_cycle": avg_cycle * 1000,
        "fps": 1.0 / avg_cycle,
        "slow_calls_count": len(slow_calls)
    }

def main():
    results = {}
    
    # Case 1: Idempotent calls (always calling green dot)
    # Expected: Fast, no blocking, close to 30 FPS.
    def case1_gen(controller, i):
        return controller.action_green_dot
        
    results["Case 1: Idempotent Calls"] = run_test_case(
        "Idempotent Calls (Green Dot Repeatedly)", 
        100, 
        case1_gen
    )
    
    # Case 2: Intermittent state changes (state changes every 10 frames)
    # Expected: Small occasional blips when joining, but mostly fast.
    def case2_gen(controller, i):
        if (i // 10) % 3 == 0:
            return controller.action_green_dot
        elif (i // 10) % 3 == 1:
            return controller.action_red_dot
        else:
            return controller.indicate_stuck_alarm
            
    results["Case 2: Intermittent State Changes"] = run_test_case(
        "Intermittent State Changes (Every 10 frames)", 
        100, 
        case2_gen
    )
    
    # Case 3: Rapid state changes (alternating states every frame)
    # Expected: High blocking overhead, significant loop frequency degradation.
    def case3_gen(controller, i):
        if i % 3 == 0:
            return controller.action_green_dot
        elif i % 3 == 1:
            return controller.action_red_dot
        else:
            return controller.indicate_stuck_alarm
            
    results["Case 3: Rapid State Changes"] = run_test_case(
        "Rapid State Changes (Every frame)", 
        100, 
        case3_gen
    )
    
    print("\n================ SUMMARY ================")
    for k, v in results.items():
        print(f"\n{k}:")
        print(f"  Avg API Call Duration: {v['avg_api']:.2f} ms (Max: {v['max_api']:.2f} ms)")
        print(f"  Avg Cycle Duration: {v['avg_cycle']:.2f} ms (Max: {v['max_cycle']:.2f} ms)")
        print(f"  Effective Frequency: {v['fps']:.2f} FPS")
        print(f"  Cycles with API call > 1ms: {v['slow_calls_count']}")

if __name__ == "__main__":
    main()
