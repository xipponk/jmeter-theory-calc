import os
import subprocess
import yaml
import csv # Import csv module for potentially more robust JTL parsing
from datetime import datetime # Not directly used in the provided snippet for analysis, but useful for timestamps if needed

# --- Global Constants (Good to keep these at the top) ---
JMETER_PATH = r"C:\JMeter\apache-jmeter-5.6.3\bin\jmeter.bat"
JMX_TEMPLATE = "jmx_template/test_template.jmx"
RESULTS_DIR = "results"
JMX_OUTPUT_PATH = os.path.join(RESULTS_DIR, "generated_test.jmx")
JTL_OUTPUT_PATH = os.path.join(RESULTS_DIR, "result.jtl")

# --- Utility Functions ---

def load_yaml(filepath):
    """Loads parameters from a YAML file."""
    with open(filepath, "r") as f:
        return yaml.safe_load(f)

def generate_jmx(template_path, output_path, params):
    """Generates a .jmx file from a template by replacing placeholders."""
    print(f"Generating .jmx file from {template_path} to {output_path}...")
    with open(template_path, "r") as f:
        template = f.read()
    for key, value in params.items():
        placeholder = f"${{{key.upper()}}}"
        template = template.replace(placeholder, str(value))
    with open(output_path, "w") as f:
        f.write(template)
    print("✅ .jmx file generated successfully.")

def run_jmeter(jmx_path, jtl_path):
    """Runs JMeter in non-GUI mode."""
    print("🚀 Running JMeter...")
    cmd = [JMETER_PATH, "-n", "-t", jmx_path, "-l", jtl_path]
    try:
        # Added check=True to raise an exception on non-zero exit code
        # Added text=True for string output
        # Added timeout to prevent indefinite hanging (e.g., 90 seconds for a 70-second test)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=90)
        print("✅ JMeter test executed successfully.")
        # Optional: Print stderr if there are warnings but no errors
        if result.stderr:
            print("JMeter stderr (warnings/info):")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ JMeter execution failed with error code {e.returncode}.")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        raise # Re-raise the exception after printing details
    except subprocess.TimeoutExpired:
        print(f"❌ JMeter test timed out after 90 seconds. The JMeter process might not have terminated.")
        print("Please check Task Manager for lingering 'java.exe' processes.")
        raise # Re-raise the exception
    except FileNotFoundError:
        print(f"❌ JMeter executable not found at {JMETER_PATH}. Please check the path.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during JMeter execution: {e}")
        raise


def analyze_jtl(jtl_path):
    """Analyzes the .jtl results file to calculate RPS, total requests, and duration."""
    if not os.path.exists(jtl_path) or os.path.getsize(jtl_path) == 0:
        print("⚠️ JTL file not found or is empty. Skipping analysis.")
        return None

    count = 0
    first_ts = None
    last_ts = None

    try:
        # Using csv.reader for more robust parsing of CSV data
        with open(jtl_path, "r", newline='') as f:
            reader = csv.reader(f)
            header = next(reader) # Skip header row
            ts_index = header.index("timeStamp") # Find index of timeStamp column

            for row in reader:
                if not row or len(row) <= ts_index: # Ensure row is not empty and has timeStamp
                    continue
                try:
                    ts = int(row[ts_index])
                    # Update first and last timestamps
                    if first_ts is None or ts < first_ts:
                        first_ts = ts
                    if last_ts is None or ts > last_ts:
                        last_ts = ts
                    count += 1
                except ValueError:
                    # Skip rows where timestamp is not a valid integer
                    continue
    except Exception as e:
        print(f"❌ Error reading JTL file: {e}")
        return None

    if first_ts is None or last_ts is None or count == 0:
        print("⚠️ No valid data found in JTL file for analysis.")
        return None

    duration_sec = (last_ts - first_ts) / 1000.0 # Ensure float division
    actual_rps = count / duration_sec if duration_sec > 0 else 0

    return {
        "actual_requests": count,
        "duration_sec": duration_sec,
        "actual_rps": actual_rps
    }

# --- Main Execution Logic ---

def main():
    print("=== Run JMeter Test and Compare with Calculator ===")
    yaml_file = input("Enter test case YAML (e.g. light.yaml): ").strip()
    yaml_path = os.path.join("testcases", yaml_file) # Assuming 'testcases' is a subdirectory

    if not os.path.exists(yaml_path):
        print(f"❌ YAML file not found at: {yaml_path}")
        return

    params = load_yaml(yaml_path)

    # Calculate theoretical values (assuming jmeter_calc is available)
    # from jmeter_calc import calculate_theoretical_values, plot_traffic_pattern
    try:
        from jmeter_calc import calculate_theoretical_values, plot_traffic_pattern
    except ImportError:
        print("❌ Error: jmeter_calc.py not found. Please ensure it's in the same directory or Python path.")
        return

    print("\n📊 Predicting theoretical values from calculator...\n")
    theory = calculate_theoretical_values(
        threads=params.get("THREADS", 1),
        ramp_up=params.get("RAMP_UP", 0),
        duration=params.get("DURATION", 60),
        think_time_ms=params.get("THINK_TIME", 0)
    )

    for key, val in theory.items():
        print(f"{key}: {val:.2f}")

    # Ensure RESULTS_DIR exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    # --- Crucial Fix: Delete old JTL file before running JMeter ---
    if os.path.exists(JTL_OUTPUT_PATH):
        try:
            os.remove(JTL_OUTPUT_PATH)
            print(f"🗑️ Removed old .jtl file: {JTL_OUTPUT_PATH}")
        except OSError as e:
            print(f"⚠️ Could not remove old .jtl file: {e}.")
            print("Please ensure the file is not open by another program and try again.")
            return # Exit if we can't clean up

    # Generate .jmx file
    generate_jmx(JMX_TEMPLATE, JMX_OUTPUT_PATH, params)

    # Run JMeter
    try:
        run_jmeter(JMX_OUTPUT_PATH, JTL_OUTPUT_PATH)
    except Exception as e:
        print(f"An error occurred during JMeter execution: {e}")
        return # Exit if JMeter failed to run

    # Analyze actual results
    print("\n📈 Analyzing actual results from .jtl...")
    actual = analyze_jtl(JTL_OUTPUT_PATH)

    if actual:
        print(f"\n✅ Actual RPS: {actual['actual_rps']:.2f}")
        print(f"📦 Actual Total Requests: {actual['actual_requests']}")
        print(f"⏱️ Actual Duration: {actual['duration_sec']:.2f} sec")

        efficiency = (actual["actual_rps"] / theory["max_rps"]) * 100 if theory["max_rps"] > 0 else 0
        print(f"\n🎯 Efficiency: {efficiency:.2f}% (Actual vs Theoretical)")
    else:
        print("Analysis could not be completed due to issues with the JTL file.")

    # Render traffic pattern graph
    print("\n📊 Rendering traffic pattern graph...")
    plot_traffic_pattern(
        threads=params.get("THREADS", 1),
        ramp_up=params.get("RAMP_UP", 0),
        duration=params.get("DURATION", 60),
        think_time_ms=params.get("THINK_TIME", 0)
    )

# --- Entry Point ---
if __name__ == "__main__":
    main()