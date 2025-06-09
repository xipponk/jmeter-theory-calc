import os
import subprocess
import yaml
from jmeter_calc import calculate_theoretical_values, plot_traffic_pattern

JMETER_PATH = r"C:\JMeter\apache-jmeter-5.6.3\bin\jmeter.bat"
JMX_TEMPLATE = "jmx_template/test_template2.jmx"
RESULTS_DIR = "results"
JMX_OUTPUT_PATH = os.path.join(RESULTS_DIR, "generated_test.jmx")
JTL_OUTPUT_PATH = os.path.join(RESULTS_DIR, "result.jtl")

def load_yaml(filepath):
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def generate_jmx(template_path, output_path, params):
    with open(template_path, "r") as f:
        template = f.read()
    for key, value in params.items():
        placeholder = f"${{{key.upper()}}}"
        template = template.replace(placeholder, str(value))
    with open(output_path, "w") as f:
        f.write(template)

def run_jmeter(jmx_path, jtl_path):
    cmd = [JMETER_PATH, "-n", "-t", jmx_path, "-l", jtl_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("⚠️  JMeter execution failed.")
        print(result.stderr)
    else:
        print("✅ JMeter test executed successfully.")

def analyze_jtl(jtl_path):
    if not os.path.exists(jtl_path):
        print("⚠️  JTL file not found. Skipping analysis.")
        return None

    count = 0
    first_ts = None
    last_ts = None

    with open(jtl_path, "r") as f:
        for line in f:
            if line.strip() == "" or line.startswith("timeStamp"):
                continue
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            ts = int(parts[0])
            first_ts = ts if first_ts is None else min(first_ts, ts)
            last_ts = ts if last_ts is None else max(last_ts, ts)
            count += 1

    duration_sec = (last_ts - first_ts) / 1000 if last_ts and first_ts else 1
    actual_rps = count / duration_sec if duration_sec > 0 else 0

    return {
        "actual_requests": count,
        "duration_sec": duration_sec,
        "actual_rps": actual_rps
    }

def main():
    print("=== Run JMeter Test and Compare with Calculator ===")
    yaml_file = input("Enter test case YAML (e.g. light.yaml): ").strip()
    yaml_path = os.path.join("testcases", yaml_file)

    if not os.path.exists(yaml_path):
        print("❌ YAML file not found.")
        return

    params = load_yaml(yaml_path)
    params = {k.upper(): v for k, v in params.items()}  # Normalize keys

    print("\n📊 Predicting theoretical values from calculator...\n")
    theory = calculate_theoretical_values(
        threads=params["THREADS"],
        ramp_up=params["RAMP_UP"],
        duration=params["LOOPS"],  # ใช้ LOOPS แทน duration
        think_time_ms=params["THINK_TIME"]
    )

    for key, val in theory.items():
        print(f"{key}: {val:.2f}")

    print("\n📁 Generating .jmx file...")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    generate_jmx(JMX_TEMPLATE, JMX_OUTPUT_PATH, params)

    print("\n🚀 Running JMeter...")
    run_jmeter(JMX_OUTPUT_PATH, JTL_OUTPUT_PATH)

    print("\n📈 Analyzing actual results from .jtl...")
    actual = analyze_jtl(JTL_OUTPUT_PATH)
    if actual:
        print(f"\n✅ Actual RPS: {actual['actual_rps']:.2f}")
        print(f"📦 Actual Total Requests: {actual['actual_requests']}")
        print(f"⏱️  Actual Duration: {actual['duration_sec']:.2f} sec")

        efficiency = (actual["actual_rps"] / theory["max_rps"]) * 100 if theory["max_rps"] > 0 else 0
        print(f"\n🎯 Efficiency: {efficiency:.2f}% (Actual vs Theoretical)")

    print("\n📊 Rendering traffic pattern graph...")
    plot_traffic_pattern(
        threads=params["THREADS"],
        ramp_up=params["RAMP_UP"],
        duration=params["LOOPS"],  # ใช้ LOOPS ตรงนี้ด้วย
        think_time_ms=params["THINK_TIME"]
    )

if __name__ == "__main__":
    main()