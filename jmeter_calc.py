import matplotlib.pyplot as plt

def main():
    print("=== JMeter Traffic Pattern Calculator ===")
    
    threads = int(input("Number of Threads (Users): "))
    ramp_up = float(input("Ramp-up Time (seconds): "))
    
    mode = input("Choose mode (1 = loop count, 2 = duration in sec): ")
    
    if mode == '1':
        loop_count = int(input("Loop Count per Thread: "))
        test_duration = None
    else:
        test_duration = float(input("Test Duration (seconds): "))
        loop_count = None
    
    think_time = float(input("Think Time per request (ms): ")) / 1000.0
    request_time = float(input("Time to complete one request (ms): ")) / 1000.0
    
    time_per_request = think_time + request_time

    if loop_count:
        total_requests = threads * loop_count
        estimated_total_time = ramp_up + (loop_count * time_per_request)
        max_rps = total_requests / estimated_total_time
        duration = estimated_total_time
    else:
        max_rps = threads / time_per_request
        total_requests = max_rps * test_duration
        duration = ramp_up + test_duration

    interval_per_user = time_per_request
    load_intensity = max_rps / threads
    ramp_up_gradient = threads / ramp_up

    print("\n=== Theoretical Load Summary ===")
    print(f"Estimated max requests/sec: {max_rps:.2f}")
    print(f"Total estimated requests: {total_requests:.0f}")
    print(f"Average interval per request (per user): {interval_per_user:.2f} sec")
    print(f"Total load generation duration: {duration:.2f} sec")
    print(f"Load intensity (req/sec/user): {load_intensity:.2f}")
    print(f"Ramp-up gradient: {ramp_up_gradient:.2f} threads/sec")

    # Generate traffic pattern over time
    time_series = []
    rps_series = []
    user_series = []

    time_resolution = 0.5
    total_steps = int(duration / time_resolution)

    for t in range(total_steps):
        current_time = t * time_resolution
        if current_time <= ramp_up:
            active_users = int(threads * (current_time / ramp_up))
        else:
            active_users = threads
        rps = active_users / time_per_request
        time_series.append(current_time)
        rps_series.append(rps)
        user_series.append(active_users)

    # Plot traffic pattern
    plt.figure(figsize=(10, 5))
    plt.plot(time_series, rps_series, label="Estimated Req/sec", linewidth=2)
    plt.xlabel("Time (sec)")
    plt.ylabel("Requests/sec")
    plt.title("JMeter Theoretical Traffic Pattern")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot concurrency curve
    plt.figure(figsize=(10, 5))
    plt.plot(time_series, user_series, label="Active Users", color='orange', linewidth=2)
    plt.xlabel("Time (sec)")
    plt.ylabel("Active Users")
    plt.title("JMeter Concurrency Curve (Users Over Time)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()