import matplotlib.pyplot as plt

def calculate_theoretical_values(threads, ramp_up, duration, think_time_ms):
    think_time = think_time_ms / 1000.0 if think_time_ms > 0 else 0.001

    total_requests = threads * duration
    max_rps = threads / think_time
    interval_per_user = think_time
    load_intensity = max_rps / threads
    ramp_up_gradient = threads / ramp_up
    total_duration = ramp_up + (duration * think_time)

    return {
        "max_rps": max_rps,
        "total_requests": total_requests,
        "interval_per_user": interval_per_user,
        "load_intensity": load_intensity,
        "ramp_up_gradient": ramp_up_gradient,
        "total_duration": total_duration
    }


def plot_traffic_pattern(threads, ramp_up, loops, think_time_ms):
    think_time = think_time_ms / 1000.0 if think_time_ms > 0 else 0.001
    user_lifetime = loops * think_time
    total_duration = ramp_up + user_lifetime

    time_series = []
    rps_series = []
    user_series = []

    time_resolution = 0.5
    total_steps = int(total_duration / time_resolution) + 1

    for t in range(total_steps):
        current_time = t * time_resolution
        active_users = 0

        for i in range(threads):
            start_time = (i / threads) * ramp_up
            end_time = start_time + user_lifetime
            if start_time <= current_time <= end_time:
                active_users += 1

        rps = active_users / think_time
        time_series.append(current_time)
        rps_series.append(rps)
        user_series.append(active_users)

    # Plot RPS
    plt.figure(figsize=(10, 5))
    plt.plot(time_series, rps_series, label="Estimated Req/sec", linewidth=2)
    plt.xlabel("Time (sec)")
    plt.ylabel("Requests/sec")
    plt.title("JMeter Theoretical Traffic Pattern")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Plot Active Users
    plt.figure(figsize=(10, 5))
    plt.plot(time_series, user_series, label="Active Users", color='orange', linewidth=2)
    plt.xlabel("Time (sec)")
    plt.ylabel("Active Users")
    plt.title("JMeter Concurrency Curve (Users Over Time)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

def main():
    print("=== JMeter Traffic Pattern Calculator ===")

    threads = int(input("Number of Threads (Users): "))
    ramp_up = float(input("Ramp-up Time (seconds): "))
    loops = int(input("Loop Count per Thread: "))
    think_time_ms = float(input("Think Time per request (ms): "))

    result = calculate_theoretical_values(
        threads=threads,
        ramp_up=ramp_up,
        duration=loops,
        think_time_ms=think_time_ms
    )

    print("\n=== Theoretical Load Summary ===")
    for k, v in result.items():
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}")

    plot_traffic_pattern(
        threads=threads,
        ramp_up=ramp_up,
        duration=loops,
        think_time_ms=think_time_ms
    )


if __name__ == "__main__":
    main()