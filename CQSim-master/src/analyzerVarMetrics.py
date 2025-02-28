import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random

# File paths
gavel_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/gavelNew.txt"
fcfs_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/fcfsNew.txt"
TOTAL_RESOURCES = 128  # Assumed total available resources


def parse_output(file_path, algorithm_name):
    """Extracts job completion times, submission times, and waiting times from CQSim output logs."""
    job_completion = {}
    job_submission = {}
    waiting_times = {}
    job_gpu = {}  # Track GPU usage per job
    job_gpu_ratio = {}  # Track GPU/CPU ratio per job
    job_priority = {}  # Track job priority
    
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
                        job_gpu[job_id] = random.choice([0, 1])  # Randomly assign GPU usage
                        job_gpu_ratio[job_id] = random.uniform(0.1, 1.0) if job_gpu[job_id] == 1 else 0  # Assign GPU/CPU ratio
                        job_priority[job_id] = random.randint(1, 10)  # Assign random priority
                        print(f"Submit Detected: Job {job_id}, Time {time}, GPU Required: {job_gpu[job_id]}, GPU Ratio: {job_gpu_ratio[job_id]:.2f}, Priority: {job_priority[job_id]}")
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
    
    return job_submission, job_completion, waiting_times, job_gpu, job_gpu_ratio, job_priority


def compute_slowdown(submission, completion):
    """Computes bounded slowdown for jobs."""
    return {job: (completion[job] - submission[job]) / max(completion[job] - submission[job], 10) for job in submission if job in completion}


def identify_starved_jobs(waiting_times):
    """Identifies jobs that waited significantly longer than average."""
    mean_wait = np.mean(list(waiting_times.values()))
    std_wait = np.std(list(waiting_times.values()))
    threshold = mean_wait + 2 * std_wait
    return {job: wait for job, wait in waiting_times.items() if wait > threshold}


def compute_utilization(submission, completion, job_gpu, job_gpu_ratio, total_resources, time_step=1000):
    """Computes resource utilization over time, including GPU usage with different ratios."""
    time_range = np.arange(0, max(completion.values()), time_step)
    cpu_utilization = []
    gpu_utilization = []
    
    for t in time_range:
        active_jobs = [job for job in submission if submission[job] <= t < completion[job]]
        active_time = sum(completion[j] - submission[j] for j in active_jobs)
        active_gpu_time = sum((completion[j] - submission[j]) * job_gpu_ratio[j] for j in active_jobs if job_gpu[j] == 1)
        
        cpu_utilization.append(active_time / (total_resources * time_step))
        gpu_utilization.append(active_gpu_time / (total_resources * time_step))
    
    return time_range, cpu_utilization, gpu_utilization


# Parse the logs
gavel_submission, gavel_completion, gavel_waiting, gavel_gpu, gavel_gpu_ratio, gavel_priority = parse_output(gavel_file, "Gavel")
fcfs_submission, fcfs_completion, fcfs_waiting, fcfs_gpu, fcfs_gpu_ratio, fcfs_priority = parse_output(fcfs_file, "FCFS")

# Compute additional metrics
gavel_slowdown = compute_slowdown(gavel_submission, gavel_completion)
fcfs_slowdown = compute_slowdown(fcfs_submission, fcfs_completion)
gavel_starved = identify_starved_jobs(gavel_waiting)
fcfs_starved = identify_starved_jobs(fcfs_waiting)

# Print results
print("\nGavel Bounded Slowdown Statistics")
print(pd.DataFrame.from_dict(gavel_slowdown, orient='index').describe())
print("\nFCFS Bounded Slowdown Statistics")
print(pd.DataFrame.from_dict(fcfs_slowdown, orient='index').describe())
print("\nGavel Starved Jobs:", gavel_starved)
print("\nFCFS Starved Jobs:", fcfs_starved)

print("\nGavel Job Priority Distribution:")
print(pd.Series(gavel_priority).value_counts().sort_index())
print("\nFCFS Job Priority Distribution:")
print(pd.Series(fcfs_priority).value_counts().sort_index())
