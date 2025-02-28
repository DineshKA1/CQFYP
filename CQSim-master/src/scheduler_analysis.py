import matplotlib.pyplot as plt
import numpy as np

def parse_gavel_log(file_path, default_runtime=100, max_jobs=100):
    """
    Parses the Gavel log file to extract job submission, start, and finish times.
    Limits analysis to the first `max_jobs` jobs.
    """
    job_details = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        current_time = None

        for i, line in enumerate(lines):
            if len(job_details) >= max_jobs:  # Stop after 100 jobs
                break

            # Extract current simulation time
            if "Time:" in line:
                try:
                    current_time = float(line.split(":")[-1].strip())
                except ValueError:
                    current_time = None
            
            # Detect job submission
            if "[Submit]" in line:
                try:
                    job_id = int(line.split()[-1])
                except ValueError:
                    continue
                
                submission_time = current_time
                start_time = None
                finish_time = None

                # Look ahead to find start and finish times
                for j in range(i + 1, len(lines)):
                    if "[Start]" in lines[j] and str(job_id) in lines[j]:
                        try:
                            start_time = float(lines[j - 3].split(":")[-1].strip())
                        except ValueError:
                            start_time = None
                    if "[Finish]" in lines[j] and str(job_id) in lines[j]:
                        try:
                            finish_time = float(lines[j - 3].split(":")[-1].strip())
                        except ValueError:
                            finish_time = None
                        break

                # Assign default finish time if missing
                if finish_time is None and start_time is not None:
                    finish_time = start_time + default_runtime

                job_details.append({
                    "job_id": job_id,
                    "submission_time": submission_time,
                    "start_time": start_time,
                    "finish_time": finish_time,
                })

    print(f"Parsed {len(job_details)} jobs from {file_path}. Sample: {job_details[:5]}")
    return job_details


def analyze_timestamps(job_details):
    """
    compute and print mean, median, and max for submission, start, and finish times.
    """
    submission_times = [job["submission_time"] for job in job_details if job["submission_time"] is not None]
    start_times = [job["start_time"] for job in job_details if job["start_time"] is not None]
    finish_times = [job["finish_time"] for job in job_details if job["finish_time"] is not None]

    def print_stats(label, times):
        if times:
            print(f"{label} - Mean: {np.mean(times):.2f}, Median: {np.median(times):.2f}, Max: {np.max(times):.2f}")
        else:
            print(f"{label} - No valid data available.")

    print_stats("Submission Times", submission_times)
    print_stats("Start Times", start_times)
    print_stats("Finish Times", finish_times)


def plot_gantt_chart(job_details, algorithm_name):
    """
    Generates a Gantt chart for job execution.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    for job in job_details:
        start = job["start_time"]
        end = job["finish_time"]
        if start is not None and end is not None:
            ax.barh(job["job_id"], end - start, left=start, color='skyblue', edgecolor='black')

    ax.set_xlabel("Time")
    ax.set_ylabel("Jobs")
    ax.set_title(f"Gantt Chart for {algorithm_name}")
    plt.show()

def plot_job_execution_time_distribution(job_details):
    """
    Plots the distribution of job execution times (finish_time - start_time).
    """
    execution_times = [
        job["finish_time"] - job["start_time"]
        for job in job_details
        if job["finish_time"] is not None and job["start_time"] is not None
    ]

    if not execution_times:
        print("No valid execution times found! Check the input data.")
        return

    plt.figure(figsize=(8, 5))
    plt.hist(execution_times, bins=20, color='skyblue', edgecolor='black')
    plt.xlabel("Job Execution Time")
    plt.ylabel("Frequency")
    plt.title("Job Execution Time Distribution")
    plt.show()

def plot_concurrency_levels(job_details, time_interval=1.0):
    """
    Plots the concurrency levels over time.
    """
    #create a list of all timestamps (start and finish times)
    times = []
    for job in job_details:
        if job["start_time"] is not None:
            times.append(job["start_time"])
        if job["finish_time"] is not None:
            times.append(job["finish_time"])
    
    if not times:
        print("No valid timestamps found! Check the input data.")
        return
    
    #create a list of times at regular intervals (time_interval)
    time_points = np.arange(min(times), max(times), time_interval)
    
    concurrency_levels = []
    for t in time_points:
        running_jobs = sum(1 for job in job_details if job["start_time"] <= t < job["finish_time"])
        concurrency_levels.append(running_jobs)
    
    plt.figure(figsize=(10, 6))
    plt.plot(time_points, concurrency_levels, color='orange', label="Concurrency Level")
    plt.xlabel("Time")
    plt.ylabel("Number of Jobs Running")
    plt.title("Concurrency Levels Over Time")
    plt.legend()
    plt.show()

def calculate_average_turnaround_time(job_details):
    """
    Calculates the average turnaround time for the given jobs.
    """
    turnaround_times = [
        job["finish_time"] - job["submission_time"]
        for job in job_details
        if job["finish_time"] is not None and job["submission_time"] is not None
    ]
    if not turnaround_times:
        print("No valid turnaround times found! Check the input data.")
    else:
        print("Turnaround times:", turnaround_times)
    
    return sum(turnaround_times) / len(turnaround_times) if turnaround_times else 0

def plot_average_turnaround(fcfs_file, gavel_file):
    """
    Plots a bar chart comparing average turnaround time between FCFS and GavelScheduling.
    """
    fcfs_jobs = parse_gavel_log(fcfs_file)
    gavel_jobs = parse_gavel_log(gavel_file)

    avg_turnaround_fcfs = calculate_average_turnaround_time(fcfs_jobs)
    avg_turnaround_gavel = calculate_average_turnaround_time(gavel_jobs)

    if avg_turnaround_fcfs == 0 or avg_turnaround_gavel == 0:
        print("Warning: One or both algorithms have no valid turnaround times. Skipping plot.")
        return

    algorithms = ["FCFS", "GavelScheduling"]
    avg_turnarounds = [avg_turnaround_fcfs, avg_turnaround_gavel]

    plt.figure(figsize=(8, 5))
    plt.bar(algorithms, avg_turnarounds, color=['skyblue', 'orange'], edgecolor='black')
    plt.xlabel("Algorithms")
    plt.ylabel("Average Turnaround Time")
    plt.title("Comparison of Average Turnaround Time")
    plt.show()


#paths to algo log files
fcfs_file_path = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/fcfsNew.txt"
gavel_file_path = "/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/gavelNew.txt"
#priority_scheduling_file_path = '/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/PriorityScheduling.txt'
#round_robin_file_path = '/Users/dinesh/Documents/GitHub/CQFYP/CQSim-master/src/RoundRobin.txt'


#generate the Gantt chart for GavelScheduling
gavel_jobs = parse_gavel_log(gavel_file_path)
#fcfs_jobs = parse_gavel_log(fcfs_file_path)[:100]
#rr_jobs = parse_gavel_log(round_robin_file_path)[:100]
#ps_jobs = parse_gavel_log(priority_scheduling_file_path)[:100]

#analyze_timestamps(gavel_jobs)
#analyze_timestamps(fcfs_jobs)
#analyze_timestamps(rr_jobs)
#analyze_timestamps(ps_jobs)
plot_gantt_chart(gavel_jobs, "Gavel")
#plot_gantt_chart(fcfs_jobs, "FCFS")
#plot_gantt_chart(rr_jobs, 'RoundRobin')

# Example usage:
# For the GavelScheduling jobs
#plot_job_execution_time_distribution(gavel_jobs)
#plot_concurrency_levels(gavel_jobs)

#compare average turnaround times for FCFS and GavelScheduling
#plot_average_turnaround(fcfs_file_path, gavel_file_path)
