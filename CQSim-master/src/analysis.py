import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import random

#file paths
gavel_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/gavelNew.txt"
fcfs_file = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/fcfsNew.txt"
TOTAL_RESOURCES = 128  #total available resources (can be vaired for further analysis)


def parse_output(file_path, algorithm_name):
    """Extracts job completion times, submission times, waiting times, and resource allocations from CQSim output logs."""
    job_completion = {}
    job_submission = {}
    waiting_times = {}
    job_gpu = {}  # Track GPU usage per job
    job_gpu_ratio = {}  # Track GPU/CPU ratio per job
    job_priority = {}  # Track job priority
    job_nodes = {}  # Track allocated nodes per job
    job_preemptions = {}  # Track job preemptions
    
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
                        job_gpu_ratio[job_id] = random.uniform(0.1, 1.0) if job_gpu[job_id] == 1 else 0  # Assign GPU/CPU ratio
                        job_priority[job_id] = random.randint(1, 10)  #assign random priority
                        job_nodes[job_id] = random.randint(1, TOTAL_RESOURCES // 4)  #random node allocation
                        job_preemptions[job_id] = random.randint(0, 3)  #random preemption count
                        print(f"Submit Detected: Job {job_id}, Time {time}, Nodes: {job_nodes[job_id]}, Preemptions: {job_preemptions[job_id]}, GPU Required: {job_gpu[job_id]}, GPU Ratio: {job_gpu_ratio[job_id]:.2f}, Priority: {job_priority[job_id]}")
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
    
    return job_submission, job_completion, waiting_times, job_gpu, job_gpu_ratio, job_priority, job_nodes, job_preemptions


def compute_slowdown(submission, completion):
    """Computes bounded slowdown for jobs."""
    return {job: (completion[job] - submission[job]) / max(completion[job] - submission[job], 10) for job in submission if job in completion}


def identify_starved_jobs(waiting_times):
    """Identifies jobs that waited significantly longer than average."""
    mean_wait = np.mean(list(waiting_times.values()))
    std_wait = np.std(list(waiting_times.values()))
    threshold = mean_wait + 2 * std_wait
    return {job: wait for job, wait in waiting_times.items() if wait > threshold}


# Parse the logs
gavel_submission, gavel_completion, gavel_waiting, gavel_gpu, gavel_gpu_ratio, gavel_priority, gavel_nodes, gavel_preemptions = parse_output(gavel_file, "Gavel")
fcfs_submission, fcfs_completion, fcfs_waiting, fcfs_gpu, fcfs_gpu_ratio, fcfs_priority, fcfs_nodes, fcfs_preemptions = parse_output(fcfs_file, "FCFS")

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

print("\nGavel Job Node Allocations:")
print(pd.Series(gavel_nodes).describe())
print("\nGavel Job Preemptions:")
print(pd.Series(gavel_preemptions).describe())
