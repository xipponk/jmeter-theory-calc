import matplotlib.pyplot as plt

def calculate_theoretical_values(threads, ramp_up, duration, think_time_ms):
    # ป้องกัน think_time เป็น 0 เพื่อหลีกเลี่ยงการหารด้วยศูนย์
    think_time = think_time_ms / 1000.0 if think_time_ms > 0 else 0.001

    # RPS สูงสุดที่ทำได้ (เมื่อมีผู้ใช้งานเต็มจำนวนและไม่มีเวลาคิด)
    max_rps = threads / think_time
    # จำนวน requests ในช่วง ramp-up (โดยประมาณ)
    requests_during_ramp_up = (0.5 * threads / think_time) * ramp_up
    
    # จำนวน requests ในช่วง duration
    requests_during_duration = (threads / think_time) * duration
    
    total_requests = requests_during_ramp_up + requests_during_duration

    interval_per_user = think_time # เวลาที่แต่ละ user ใช้ในการทำ 1 request (รวมคิดเวลา)
    load_intensity = max_rps # อัตราโหลดสูงสุด (RPS)
    ramp_up_gradient = threads / ramp_up if ramp_up > 0 else threads # อัตราการเพิ่มผู้ใช้งานต่อวินาที
    total_simulation_time = ramp_up + duration

    return {
        "max_rps": max_rps,
        "total_requests_approx": total_requests, # เปลี่ยนชื่อให้ชัดเจนว่าเป็นค่าประมาณ
        "interval_per_user": interval_per_user,
        "load_intensity": load_intensity,
        "ramp_up_gradient": ramp_up_gradient,
        "total_simulation_time": total_simulation_time
    }


def plot_traffic_pattern(threads, ramp_up, duration, think_time_ms):
    think_time = think_time_ms / 1000.0 if think_time_ms > 0 else 0.001
    
    # กำหนดช่วงเวลาที่การทดสอบทำงาน (รวม ramp-up และ duration)
    # และเพิ่มเวลาสำหรับช่วง tear-down เพื่อให้กราฟลดลงถึง 0
    # กำหนด tear-down time ให้เท่ากับ ramp-up time เพื่อให้สมมาตร
    tear_down_time = ramp_up 
    total_simulation_time = ramp_up + duration + tear_down_time

    time_series = []
    rps_series = []
    user_series = []

    time_resolution = 0.5 # ความละเอียดของเวลาในการพล็อต (วินาที)
    # คำนวณจำนวนขั้นตอนทั้งหมด
    total_steps = int(total_simulation_time / time_resolution) + 1

    for t in range(total_steps):
        current_time = t * time_resolution

        active_users = 0
        if current_time <= ramp_up:
            # ช่วง Ramp-up: ผู้ใช้งานเพิ่มขึ้นจาก 0 ถึง Threads
            active_users = int(threads * (current_time / ramp_up))
        elif current_time <= ramp_up + duration:
            # ช่วงคงที่: ผู้ใช้งานคงที่ที่จำนวน Threads สูงสุด
            active_users = threads
        elif current_time <= ramp_up + duration + tear_down_time:
            # ช่วง Tear-down: ผู้ใช้งานลดลงจาก Threads ถึง 0
            # คำนวณสัดส่วนการลดลง
            time_in_tear_down = current_time - (ramp_up + duration)
            active_users = int(threads * (1 - (time_in_tear_down / tear_down_time)))
            active_users = max(0, active_users) # ให้แน่ใจว่าไม่ติดลบ
        else:
            # หลังจากการทดสอบสิ้นสุด: ผู้ใช้งานเป็น 0
            active_users = 0

        # คำนวณ RPS จาก Active Users และ Think Time
        rps = active_users / think_time
        
        time_series.append(current_time)
        rps_series.append(rps)
        user_series.append(active_users)

    # Plot traffic pattern (Requests per second)
    plt.figure(figsize=(12, 6))
    plt.plot(time_series, rps_series, label="Estimated Req/sec", linewidth=2, color='blue')
    plt.xlabel("Time (seconds)", fontsize=12)
    plt.ylabel("Requests/sec", fontsize=12)
    plt.title("JMeter Theoretical Traffic Pattern (RPS Over Time)", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    plt.axvline(x=ramp_up, color='r', linestyle=':', label='End Ramp-up')
    plt.axvline(x=ramp_up + duration, color='g', linestyle=':', label='End Duration')
    plt.tight_layout()
    plt.show()

    # Plot concurrency curve (Active Users)
    plt.figure(figsize=(12, 6))
    plt.plot(time_series, user_series, label="Active Users", color='orange', linewidth=2)
    plt.xlabel("Time (seconds)", fontsize=12)
    plt.ylabel("Active Users", fontsize=12)
    plt.title("JMeter Concurrency Curve (Users Over Time)", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    plt.axvline(x=ramp_up, color='r', linestyle=':', label='End Ramp-up')
    plt.axvline(x=ramp_up + duration, color='g', linestyle=':', label='End Duration')
    plt.tight_layout()
    plt.show()


def main():
    print("=== JMeter Traffic Pattern Calculator ===")

    threads = int(input("Number of Threads (Users): "))
    ramp_up = float(input("Ramp-up Time (seconds): "))
    mode = input("Choose mode (1 = loop count, 2 = duration in sec): ")

    test_duration = 0
    if mode == '1':
        loop_count = int(input("Loop Count per Thread: "))
        print("Note: For 'Loop Count' mode, actual duration can vary. Please provide an estimated duration for plotting.")
        test_duration = float(input("Estimated Test Duration (seconds) for plotting: "))
    else:
        test_duration = float(input("Test Duration (seconds): "))

    think_time_ms = float(input("Think Time per request (ms): "))
    if think_time_ms <= 0:
        print("⚠️ No think time specified. Interpreted as 0 ms (stress test mode).")

    result = calculate_theoretical_values(
        threads=threads,
        ramp_up=ramp_up,
        duration=test_duration,
        think_time_ms=think_time_ms
    )

    print("\n=== Theoretical Load Summary ===")
    for k, v in result.items():
        # ปรับการแสดงผลสำหรับ float ให้เป็น 2 ตำแหน่ง
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}")

    plot_traffic_pattern(
        threads=threads,
        ramp_up=ramp_up,
        duration=test_duration,
        think_time_ms=think_time_ms
    )


if __name__ == "__main__":
    main()