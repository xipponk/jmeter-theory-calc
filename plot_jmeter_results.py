import pandas as pd
import matplotlib.pyplot as plt
import os

# --- Configuration ---
CSV_FILE_PATH = 'Jmeter_Experiment_Results.csv'
OUTPUT_DIR = 'graphs'

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load Data ---
try:
    df = pd.read_csv(CSV_FILE_PATH)
    print(f"Data loaded successfully from {CSV_FILE_PATH}")
    print(df.head())
except FileNotFoundError:
    print(f"Error: {CSV_FILE_PATH} not found. Please ensure the CSV file is in the correct directory.")
    exit()
except Exception as e:
    print(f"Error loading CSV file: {e}")
    exit()

# --- Plotting Functions ---

def plot_rps_comparison(data_frame, output_path, use_log_scale=True): # add parameter use_log_scale
    """
    กราฟเปรียบเทียบ RPS (Actual vs. Theoretical) เป็น Bar Chart
    พร้อมตัวเลือกใช้ Logarithmic Scale สำหรับแกน Y
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    test_cases = data_frame['TestCase']
    theoretical_rps = data_frame['TheoreticalMaxRPS']
    actual_rps = data_frame['ActualRPS']

    bar_width = 0.35
    index = range(len(test_cases))

    bar1 = ax.bar([i - bar_width/2 for i in index], theoretical_rps, bar_width, label='Theoretical Max RPS', color='skyblue')
    bar2 = ax.bar([i + bar_width/2 for i in index], actual_rps, bar_width, label='Actual RPS', color='lightcoral')

    ax.set_xlabel('Test Case', fontsize=12)
    ax.set_ylabel('Requests per Second (RPS)', fontsize=12)
    ax.set_title('Comparison of Theoretical vs. Actual RPS', fontsize=14)
    ax.set_xticks(index)
    ax.set_xticklabels(test_cases)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # --- Used Logarithmic Scale ---
    if use_log_scale:
        ax.set_yscale('log')
        #for bar_group in [bar1, bar2]:
            #for bar in bar_group:
                #height = bar.get_height()
                #if height > 0: # ป้องกันค่า 0 ถ้ามี
                    #ax.text(bar.get_x() + bar.get_width()/2, height, f'{height:.0f}', 
                            #ha='center', va='bottom', fontsize=8, rotation=45) # ปรับ rotation ให้พอดี

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, 'rps_comparison_bar_chart_log_scale.png')) # Change File Name
    plt.show()

def plot_actual_rps_trend(data_frame, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_df = data_frame.sort_values(by='Threads')
    ax.plot(sorted_df['TestCase'], sorted_df['ActualRPS'], marker='o', linestyle='-', color='green', label='Actual RPS')
    ax.set_xlabel('Test Case (Increasing Load)', fontsize=12)
    ax.set_ylabel('Actual Requests per Second (RPS)', fontsize=12)
    ax.set_title('Actual RPS Trend Across Different Load Levels', fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, 'actual_rps_trend_line_chart.png'))
    plt.show()

def plot_duration_comparison(data_frame, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    test_cases = data_frame['TestCase']
    theoretical_duration = data_frame['TheoreticalDuration_s']
    actual_duration = data_frame['ActualDuration_s']
    bar_width = 0.35
    index = range(len(test_cases))
    bar1 = ax.bar([i - bar_width/2 for i in index], theoretical_duration, bar_width, label='Theoretical Duration', color='lightgreen')
    bar2 = ax.bar([i + bar_width/2 for i in index], actual_duration, bar_width, label='Actual Duration', color='salmon')
    ax.set_xlabel('Test Case', fontsize=12)
    ax.set_ylabel('Duration (Seconds)', fontsize=12)
    ax.set_title('Comparison of Theoretical vs. Actual Test Duration', fontsize=14)
    ax.set_xticks(index)
    ax.set_xticklabels(test_cases)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, 'duration_comparison_bar_chart.png'))
    plt.show()

def plot_efficiency_by_test_case(data_frame, output_path):
    fig, ax = plt.subplots(figsize=(10, 6))
    test_cases = data_frame['TestCase']
    efficiency = data_frame['Efficiency_pct']
    bars = ax.bar(test_cases, efficiency, color=['blue', 'orange', 'red'])
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, round(yval, 2), ha='center', va='bottom', fontsize=9)
    ax.set_xlabel('Test Case', fontsize=12)
    ax.set_ylabel('Efficiency (%)', fontsize=12)
    ax.set_title('Efficiency Across Different Test Cases', fontsize=14)
    ax.set_ylim(0, 105)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_path, 'efficiency_bar_chart.png'))
    plt.show()

# --- Run Plotting ---
if __name__ == "__main__":
    print(f"\nGenerating graphs and saving to '{OUTPUT_DIR}' directory...")
    plot_rps_comparison(df, OUTPUT_DIR, use_log_scale=True) 
    plot_actual_rps_trend(df, OUTPUT_DIR)
    plot_duration_comparison(df, OUTPUT_DIR)
    plot_efficiency_by_test_case(df, OUTPUT_DIR)
    print("All graphs generated and saved.")