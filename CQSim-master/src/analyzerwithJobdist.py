import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random

# File paths
gavel_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/gavelNew.txt"
fcfs_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/fcfsNew.txt"
TOTAL_RESOURCES = 128  #assumed total available resources (can be varied)


def parse_output(file_path, algorithm_name):
    """Extracts job completion times, submission times, and waiting times from CQSim output logs."""
    job_completion = {}
    job_submission = {}
    waiting_times = {}
    job_gpu = {}  #track GPU usage per job
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    print(f"\nProcessing {algorithm_name} Output\n" + "="*30)
    
    for i, line in enumerate(lines):
        if "[Submit]" in line:
            job_id = int(re.findall(r'\d+', line)[0])
            if job_id not in job_submission:  #prevent duplicate submissions
                for j in range(i-1, max(i-10, 0), -1):
                    time_matches = re.findall(r'Time:\s*(\d+\.\d+)', lines[j])
                    if time_matches:
                        time = float(time_matches[0])
                        job_submission[job_id] = time
                        job_gpu[job_id] = random.choice([0, 1])  #randomly assign GPU usage
                        print(f"Submit Detected: Job {job_id}, Time {time}, GPU Required: {job_gpu[job_id]}")
                        break  
        
        elif "[Finish]" in line:
            job_id = int(re.findall(r'\d+', line)[0])
            if job_id not in job_completion and job_id in job_submission:  #ensure valid finish
                for j in range(i-1, max(i-10, 0), -1):
                    time_matches = re.findall(r'Time:\s*(\d+\.\d+)', lines[j])
                    if time_matches:
                        time = float(time_matches[0])
                        job_completion[job_id] = time
                        waiting_times[job_id] = job_completion[job_id] - job_submission[job_id]
                        print(f"Finish Detected: Job {job_id}, Time {time}")
                        break  
    
    return job_submission, job_completion, waiting_times, job_gpu


def compute_utilization(submission, completion, job_gpu, total_resources, time_step=1000):
    """Computes resource utilization over time, including GPU usage."""
    time_range = np.arange(0, max(completion.values()), time_step)
    cpu_utilization = []
    gpu_utilization = []
    
    for t in time_range:
        active_jobs = [job for job in submission if submission[job] <= t < completion[job]]
        active_time = sum(completion[j] - submission[j] for j in active_jobs)
        active_gpu_time = sum(completion[j] - submission[j] for j in active_jobs if job_gpu[j] == 1)
        
        cpu_utilization.append(active_time / (total_resources * time_step))
        gpu_utilization.append(active_gpu_time / (total_resources * time_step))
    
    return time_range, cpu_utilization, gpu_utilization



# Parse the logs
gavel_submission, gavel_completion, gavel_waiting, gavel_gpu = parse_output(gavel_file, "Gavel")
fcfs_submission, fcfs_completion, fcfs_waiting, fcfs_gpu = parse_output(fcfs_file, "FCFS")

# Compute utilization
gavel_time, gavel_cpu_util, gavel_gpu_util = compute_utilization(gavel_submission, gavel_completion, gavel_gpu, TOTAL_RESOURCES)
fcfs_time, fcfs_cpu_util, fcfs_gpu_util = compute_utilization(fcfs_submission, fcfs_completion, fcfs_gpu, TOTAL_RESOURCES)

# Plot Resource Utilization
plt.figure(figsize=(12, 6))
plt.plot(gavel_time, gavel_cpu_util, label='Gavel CPU Utilization', linestyle='-', marker='o', color='blue')
plt.plot(gavel_time, gavel_gpu_util, label='Gavel GPU Utilization', linestyle='-', marker='s', color='cyan')
plt.plot(fcfs_time, fcfs_cpu_util, label='FCFS CPU Utilization', linestyle='-', marker='x', color='red')
plt.plot(fcfs_time, fcfs_gpu_util, label='FCFS GPU Utilization', linestyle='-', marker='^', color='orange')
plt.xlabel("Time")
plt.ylabel("Resource Utilization")
plt.title("CPU & GPU Resource Utilization Over Time: Gavel vs FCFS")
plt.legend()
plt.grid()
plt.show()

# Print Summary Stats
print("\nGavel Scheduling Statistics")
print(pd.DataFrame.from_dict(gavel_waiting, orient='index').describe())
print("\nFCFS Scheduling Statistics")
print(pd.DataFrame.from_dict(fcfs_waiting, orient='index').describe())
