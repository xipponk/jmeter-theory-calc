import matplotlib.pyplot as plt

def calculate_theoretical_values(threads, ramp_up, duration, think_time_ms):
    # ปรับปรุงการจัดการ think_time:
    # ถ้า think_time_ms เป็น 0, เราจะใช้ค่าขั้นต่ำที่สมเหตุสมผลสำหรับเวลาประมวลผลต่อ Request
    # เพราะ JMeter ไม่สามารถส่ง Request ได้เร็วกว่า Overhead ของตัวเอง
    if think_time_ms > 0:
        interval_per_user = think_time_ms / 1000.0 # แปลง ms เป็นวินาที
    else:
        # เมื่อ think_time_ms เป็น 0 (Stress Test Mode)
        # กำหนดเวลาขั้นต่ำที่ JMeter ใช้ในการประมวลผล 1 Request (เช่น 10ms หรือ 5ms)
        # ค่านี้จะสะท้อนถึง Overhead ของ JMeter และการตอบสนองที่เร็วที่สุดจาก Server
        min_processing_time_ms = 10 # 10 ms = 0.01 seconds
        interval_per_user = min_processing_time_ms / 1000.0

    # RPS สูงสุดที่ทำได้ (เมื่อมีผู้ใช้งานเต็มจำนวนและไม่มีเวลาคิดเพิ่มเติม)
    max_rps = threads / interval_per_user
    
    # จำนวน requests ในช่วง ramp-up (โดยประมาณ)
    # ใช้ค่าเฉลี่ยของ user ในช่วง ramp-up (threads / 2)
    requests_during_ramp_up = (threads / 2) / interval_per_user * ramp_up
    
    # จำนวน requests ในช่วง duration
    requests_during_duration = (threads / interval_per_user) * duration
    
    total_requests = requests_during_ramp_up + requests_during_duration

    # ค่าอื่นๆ ที่เกี่ยวข้อง
    load_intensity = max_rps # อัตราโหลดสูงสุด (RPS)
    ramp_up_gradient = threads / ramp_up if ramp_up > 0 else threads # อัตราการเพิ่มผู้ใช้งานต่อวินาที
    total_simulation_time = ramp_up + duration # ระยะเวลารวมของ Test (ramp-up + duration)

    return {
        "max_rps": max_rps,
        "total_requests_approx": total_requests,
        "interval_per_user": interval_per_user,
        "load_intensity": load_intensity,
        "ramp_up_gradient": ramp_up_gradient,
        "total_simulation_time": total_simulation_time
    }


def plot_traffic_pattern(threads, ramp_up, duration, think_time_ms):
    # ใช้ Logic เดียวกันกับ calculate_theoretical_values สำหรับ think_time
    if think_time_ms > 0:
        think_time_sec_for_plot = think_time_ms / 1000.0
    else:
        min_processing_time_ms = 10 # ต้องสอดคล้องกับ calculate_theoretical_values
        think_time_sec_for_plot = min_processing_time_ms / 1000.0
    
    # กำหนดช่วงเวลาที่การทดสอบทำงาน (รวม ramp-up และ duration)
    # และเพิ่มเวลาสำหรับช่วง tear-down เพื่อให้กราฟลดลงถึง 0
    tear_down_time = ramp_up # กำหนด tear-down time ให้เท่ากับ ramp-up time เพื่อให้สมมาตร
    total_simulation_time_for_plot = ramp_up + duration + tear_down_time

    time_series = []
    rps_series = []
    user_series = []

    time_resolution = 0.5 # ความละเอียดของเวลาในการพล็อต (วินาที)
    total_steps = int(total_simulation_time_for_plot / time_resolution) + 1

    for t in range(total_steps):
        current_time = t * time_resolution

        active_users = 0
        if current_time <= ramp_up:
            # ช่วง Ramp-up: ผู้ใช้งานเพิ่มขึ้นจาก 0 ถึง Threads
            active_users = int(threads * (current_time / ramp_up)) if ramp_up > 0 else threads
        elif current_time <= ramp_up + duration:
            # ช่วงคงที่: ผู้ใช้งานคงที่ที่จำนวน Threads สูงสุด
            active_users = threads
        elif current_time <= ramp_up + duration + tear_down_time:
            # ช่วง Tear-down: ผู้ใช้งานลดลงจาก Threads ถึง 0
            time_in_tear_down = current_time - (ramp_up + duration)
            active_users = int(threads * (1 - (time_in_tear_down / tear_down_time))) if tear_down_time > 0 else 0
            active_users = max(0, active_users) # ให้แน่ใจว่าไม่ติดลบ
        else:
            # หลังจากการทดสอบสิ้นสุด: ผู้ใช้งานเป็น 0
            active_users = 0

        # คำนวณ RPS จาก Active Users และ Think Time ที่ปรับปรุงแล้ว
        rps = active_users / think_time_sec_for_plot
        
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