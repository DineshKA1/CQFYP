import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# File paths
gavel_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/gavelNew.txt"
fcfs_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/fcfsNew.txt"
TOTAL_RESOURCES = 128  # Assumed total available resources

def parse_output(file_path, algorithm_name):
    """Extracts job completion times, submission times, arrival times, and waiting times from CQSim output logs."""
    job_completion = {}
    job_submission = {}
    job_arrival = {}
    waiting_times = {}
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    print(f"\nProcessing {algorithm_name} Output\n" + "="*30)
    
    for i, line in enumerate(lines):
        if "[Submit]" in line:
            job_id = int(re.findall(r'\d+', line)[0])
            if job_id not in job_submission:  # Prevent duplicate submissions
                for j in range(i-1, max(i-10, 0), -1):
                    time_matches = re.findall(r'Time:\s*(\d+\.\d+)', lines[j])
                    if time_matches:
                        time = float(time_matches[0])
                        job_submission[job_id] = time
                        job_arrival[job_id] = time  # Arrival time is the same as submission time
                        print(f"Submit Detected: Job {job_id}, Time {time}")
                        break  
        
        elif "[Finish]" in line:
            job_id = int(re.findall(r'\d+', line)[0])
            if job_id not in job_completion and job_id in job_submission:  # Ensure valid finish
                for j in range(i-1, max(i-10, 0), -1):
                    time_matches = re.findall(r'Time:\s*(\d+\.\d+)', lines[j])
                    if time_matches:
                        time = float(time_matches[0])
                        job_completion[job_id] = time
                        waiting_times[job_id] = job_completion[job_id] - job_submission[job_id]
                        print(f"Finish Detected: Job {job_id}, Time {time}")
                        break  
    
    return job_submission, job_completion, job_arrival, waiting_times


def compute_utilization(submission, completion, total_resources, time_step=1000):
    """Computes resource utilization over time."""
    time_range = np.arange(0, max(completion.values()), time_step)
    utilization = []
    
    for t in time_range:
        active_jobs = [job for job in submission if submission[job] <= t < completion[job]]
        active_time = sum(completion[j] - submission[j] for j in active_jobs)
        utilization.append(active_time / (total_resources * time_step))
    
    return time_range, utilization

# Parse the logs and include arrival times
gavel_submission, gavel_completion, gavel_arrival, gavel_waiting = parse_output(gavel_file, "Gavel")
fcfs_submission, fcfs_completion, fcfs_arrival, fcfs_waiting = parse_output(fcfs_file, "FCFS")

# Filter only jobs that exist in both submission and completion
gavel_common_jobs = set(gavel_submission.keys()) & set(gavel_completion.keys())
gavel_df = pd.DataFrame({
    'Job ID': list(gavel_common_jobs),
    'Submission Time': [gavel_submission[j] for j in gavel_common_jobs],
    'Arrival Time': [gavel_arrival[j] for j in gavel_common_jobs],  # Add arrival time
    'Completion Time': [gavel_completion[j] for j in gavel_common_jobs]
})
gavel_df['Duration'] = gavel_df['Completion Time'] - gavel_df['Submission Time']

gavel_df = gavel_df[gavel_df['Duration'] > 0]  # Ensure no zero or negative durations

fcfs_common_jobs = set(fcfs_submission.keys()) & set(fcfs_completion.keys())
fcfs_df = pd.DataFrame({
    'Job ID': list(fcfs_common_jobs),
    'Submission Time': [fcfs_submission[j] for j in fcfs_common_jobs],
    'Arrival Time': [fcfs_arrival[j] for j in fcfs_common_jobs],  # Add arrival time
    'Completion Time': [fcfs_completion[j] for j in fcfs_common_jobs]
})
fcfs_df['Duration'] = fcfs_df['Completion Time'] - fcfs_df['Submission Time']

fcfs_df = fcfs_df[fcfs_df['Duration'] > 0]  # Ensure no zero or negative durations


# Compute additional metrics
def fairness_index(durations):
    return (sum(durations) ** 2) / (len(durations) * sum([d ** 2 for d in durations]))

print("\nJob Arrival Times for Gavel Scheduling:")
print(gavel_df[['Job ID', 'Arrival Time']])

print("\nJob Arrival Times for FCFS Scheduling:")
print(fcfs_df[['Job ID', 'Arrival Time']])

# You can also update other metrics to include arrival times if necessary.
print("\nMean Arrival Time:")
print("Gavel:", gavel_df['Arrival Time'].mean())
print("FCFS:", fcfs_df['Arrival Time'].mean())


print("\nAdditional Metrics:")
print("\nMean Waiting Time:")
print("Gavel:", gavel_df['Duration'].mean())
print("FCFS:", fcfs_df['Duration'].mean())

print("\nThroughput (Jobs Completed Per Unit Time):")
print("Gavel:", len(gavel_df) / gavel_df['Completion Time'].max())
print("FCFS:", len(fcfs_df) / fcfs_df['Completion Time'].max())

print("\nFairness Index:")
print("Gavel:", fairness_index(gavel_df['Duration']))
print("FCFS:", fairness_index(fcfs_df['Duration']))

# Compute utilization
gavel_time, gavel_utilization = compute_utilization(gavel_submission, gavel_completion, TOTAL_RESOURCES)
fcfs_time, fcfs_utilization = compute_utilization(fcfs_submission, fcfs_completion, TOTAL_RESOURCES)

# Gavel Gantt Chart with Arrival Time
fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

# Gavel Gantt Chart with Arrival Time indicated by vertical lines
ax[0].barh(gavel_df['Job ID'], gavel_df['Duration'], left=gavel_df['Submission Time'], color='blue', alpha=0.6)
ax[0].vlines(gavel_df['Arrival Time'], ymin=gavel_df['Job ID'] - 0.4, ymax=gavel_df['Job ID'] + 0.4, color='green', linestyles='dashed', label='Arrival Time')
ax[0].set_ylabel("Job ID")
ax[0].set_title("Gavel Scheduling Gantt Chart")
ax[0].invert_yaxis()
ax[0].grid(True)
ax[0].legend()

# FCFS Gantt Chart with Arrival Time indicated by vertical lines
ax[1].barh(fcfs_df['Job ID'], fcfs_df['Duration'], left=fcfs_df['Submission Time'], color='red', alpha=0.6)
ax[1].vlines(fcfs_df['Arrival Time'], ymin=fcfs_df['Job ID'] - 0.4, ymax=fcfs_df['Job ID'] + 0.4, color='green', linestyles='dashed', label='Arrival Time')
ax[1].set_xlabel("Time")
ax[1].set_ylabel("Job ID")
ax[1].set_title("FCFS Scheduling Gantt Chart")
ax[1].invert_yaxis()
ax[1].grid(True)
ax[1].legend()

plt.tight_layout()
plt.show()


plt.figure(figsize=(12, 6))
plt.plot(gavel_time, gavel_utilization, label='Gavel Utilization', linestyle='-', marker='o', color='blue')
plt.plot(fcfs_time, fcfs_utilization, label='FCFS Utilization', linestyle='-', marker='x', color='red')
plt.xlabel("Time")
plt.ylabel("Resource Utilization")
plt.title("Resource Utilization Over Time: Gavel vs FCFS")
plt.legend()
plt.grid()
plt.show()

# Print Summary Stats
print("\nGavel Scheduling Statistics")
print(gavel_df.describe())
print("\nFCFS Scheduling Statistics")
print(fcfs_df.describe())