import os
import subprocess
import yaml
import csv
# from datetime import datetime # Not strictly needed for the current analysis, but useful for timestamps if needed

# Ensure jmeter_calc.py is in the same directory or accessible via Python path
try:
    from jmeter_calc import calculate_theoretical_values, plot_traffic_pattern
except ImportError:
    print("❌ Error: jmeter_calc.py not found. Please ensure it's in the same directory or Python path.")
    print("This script requires jmeter_calc.py for theoretical calculations and plotting.")
    exit(1) # Exit if essential module is missing

# --- Global Constants ---
JMETER_BAT_PATH = r"C:\JMeter\apache-jmeter-5.6.3\bin\jmeter.bat"
JMX_TEMPLATE = "jmx_template/test_template.jmx"
RESULTS_DIR = "results"
JMX_OUTPUT_PATH = os.path.join(RESULTS_DIR, "generated_test.jmx")
JTL_OUTPUT_PATH = os.path.join(RESULTS_DIR, "result.jtl")
YAML_TESTCASES_DIR = "testcases"

# --- Utility Functions (unchanged from your last version) ---

def load_yaml(filepath):
    """Loads parameters from a YAML file."""
    print(f"Loading test parameters from {filepath}...")
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def generate_jmx(template_path, output_path, params):
    """Generates a .jmx file from a template by replacing placeholders."""
    print(f"📁 Generating .jmx file from {template_path} to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(template_path, "r") as f:
        template = f.read()
    for key, value in params.items():
        placeholder = f"${{{key.upper()}}}"
        template = template.replace(placeholder, str(value))
    with open(output_path, "w") as f:
        f.write(template)
    print("✅ .jmx file generated successfully.")

def run_jmeter(jmx_path, jtl_path, timeout_seconds): # Removed default value here to ensure it's always passed dynamically
    """
    Runs JMeter in non-GUI mode with robust error handling and timeout.
    :param jmx_path: Path to the .jmx test plan.
    :param jtl_path: Path to the .jtl results file.
    :param timeout_seconds: Maximum seconds to wait for JMeter to complete.
    """
    print(f"🚀 Running JMeter test plan: {jmx_path}")
    print(f"Results will be saved to: {jtl_path}")

    cmd = [
        JMETER_BAT_PATH,
        "-n",
        "-t", jmx_path,
        "-l", jtl_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout_seconds)
        print("✅ JMeter test executed successfully.")
        if result.stderr:
            print("JMeter stderr (warnings/info):")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ JMeter execution failed with error code {e.returncode}.")
        print("--- JMeter STDOUT ---")
        print(e.stdout)
        print("--- JMeter STDERR ---")
        print(e.stderr)
        raise
    except subprocess.TimeoutExpired:
        print(f"❌ JMeter test timed out after {timeout_seconds} seconds.")
        print("This often means the JMeter process did not terminate as expected.")
        print("Please check Task Manager for lingering 'java.exe' processes.")
        raise
    except FileNotFoundError:
        print(f"❌ JMeter executable not found at {JMETER_BAT_PATH}.")
        print("Please verify the JMETER_BAT_PATH in the script.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during JMeter execution: {e}")
        raise

def analyze_jtl(jtl_path):
    """Analyzes the .jtl results file."""
    print(f"📈 Analyzing actual results from {jtl_path}...")
    if not os.path.exists(jtl_path) or os.path.getsize(jtl_path) == 0:
        print("⚠️ JTL file not found or is empty. Skipping analysis.")
        return None

    count = 0
    first_ts = None
    last_ts = None

    try:
        with open(jtl_path, "r", newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            try:
                ts_col_index = header.index("timeStamp")
            except ValueError:
                print("❌ 'timeStamp' column not found in JTL header. Cannot analyze.")
                return None

            for row in reader:
                if not row or len(row) <= ts_col_index:
                    continue
                try:
                    ts = int(row[ts_col_index])
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts
                    count += 1
                except ValueError:
                    print(f"⚠️ Skipping invalid timestamp in row: {row}")
                    continue
    except Exception as e:
        print(f"❌ Error reading or parsing JTL file: {e}")
        return None

    if first_ts is None or last_ts is None or count == 0:
        print("⚠️ No valid test data found in JTL file for analysis.")
        return {
            "actual_requests": 0,
            "duration_sec": 0.0,
            "actual_rps": 0.0
        }

    duration_ms = last_ts - first_ts
    duration_sec = duration_ms / 1000.0 if duration_ms > 0 else 0.001

    actual_rps = count / duration_sec if duration_sec > 0 else 0.0

    return {
        "actual_requests": count,
        "duration_sec": duration_sec,
        "actual_rps": actual_rps
    }

# --- Main Execution Flow ---

def main():
    print("=== JMeter Calculator & Test Runner ===")
    
    yaml_file = input(f"Enter test case YAML (e.g. light.yaml, from '{YAML_TESTCASES_DIR}' directory): ").strip()
    yaml_path = os.path.join(YAML_TESTCASES_DIR, yaml_file)

    if not os.path.exists(yaml_path):
        print(f"❌ YAML file not found at: {yaml_path}")
        print("Please ensure the YAML file exists in the 'testcases' directory.")
        return

    try:
        params = load_yaml(yaml_path)
    except Exception as e:
        print(f"❌ Error loading YAML file: {e}")
        return

    print("\n📊 Predicting theoretical values from calculator...\n")
    theory = calculate_theoretical_values(
        threads=params.get("THREADS", 1),
        ramp_up=params.get("RAMP_UP", 0),
        duration=params.get("DURATION", 60),
        think_time_ms=params.get("THINK_TIME", 0)
    )

    for key, val in theory.items():
        print(f"{key.replace('_', ' ').title()}: {val:.2f}")

    os.makedirs(RESULTS_DIR, exist_ok=True)

    if os.path.exists(JTL_OUTPUT_PATH):
        try:
            os.remove(JTL_OUTPUT_PATH)
            print(f"🗑️ Removed old .jtl file: {JTL_OUTPUT_PATH}")
        except OSError as e:
            print(f"⚠️ Could not remove old .jtl file: {e}.")
            print("Please ensure the file is not open by another program and try again.")
            return

    generate_jmx(JMX_TEMPLATE, JMX_OUTPUT_PATH, params)

    try:
        # --- Adjusted Dynamic Timeout Calculation ---
        # Increased multiplier and buffer to account for potential delays under stress
        # For a 150-second test, 2.5x buffer + 20s = 375 + 20 = 395 seconds
        # This will be sufficient for your 400-second target.
        jmeter_timeout = theory['total_simulation_time'] * 2.5 # Multiplier increased from 1.5 to 2.5
        calculated_timeout_seconds = int(jmeter_timeout) + 20   # Buffer increased from 10 to 20
        
        # Ensure minimum timeout is reasonable even for very short theoretical durations
        # This prevents extremely short timeouts for very small tests.
        if calculated_timeout_seconds < 100: # Ensure minimum timeout is at least 100s
             calculated_timeout_seconds = 100

        print(f"Calculated JMeter execution timeout: {calculated_timeout_seconds} seconds.")

        run_jmeter(JMX_OUTPUT_PATH, JTL_OUTPUT_PATH, timeout_seconds=calculated_timeout_seconds)
    except Exception as e:
        print(f"An error occurred during JMeter execution: {e}")
        return

    actual = analyze_jtl(JTL_OUTPUT_PATH)

    if actual:
        print(f"\n✅ Actual RPS: {actual['actual_rps']:.2f}")
        print(f"📦 Actual Total Requests: {actual['actual_requests']}")
        print(f"⏱️ Actual Duration: {actual['duration_sec']:.2f} sec")

        efficiency = (actual["actual_rps"] / theory["max_rps"]) * 100 if theory["max_rps"] > 0 else 0
        print(f"\n🎯 Efficiency: {efficiency:.2f}% (Actual vs Theoretical)")
    else:
        print("\nAnalysis could not be completed.")

    print("\n📊 Rendering traffic pattern graph...")
    try:
        plot_traffic_pattern(
            threads=params.get("THREADS", 1),
            ramp_up=params.get("RAMP_UP", 0),
            duration=params.get("DURATION", 60),
            think_time_ms=params.get("THINK_TIME", 0)
        )
    except Exception as e:
        print(f"❌ Error rendering traffic pattern graph: {e}")


if __name__ == "__main__":
    main()