import matplotlib.pyplot as plt

# Defining the job schedule data
jobs = [
    (11, 566129, 28826),
    (12, 566290, 26171),
    (13, 567314, 8071),
    (14, 571164, 64832),
    (15, 574294, 64384),
    (16, 576100, 19000),
    (17, 577685, 118561),
    (18, 578846, 24861),
    (19, 580157, 6900),
    (20, 581034, 10979),
    (21, 581434, 16674),
    (22, 582841, 8385),
    (23, 583532, 16793),
    (24, 584165, 3634),
    (25, 584785, 1229),
    (26, 584801, 2207),
    (27, 584826, 40)
]

# Setting up the figure
fig, ax = plt.subplots(figsize=(12, 6))

# Assigning colors
colors = plt.cm.get_cmap("tab20", len(jobs))

# Plotting the jobs as horizontal bars
for i, (job_id, start, duration) in enumerate(jobs):
    ax.barh(y=i, width=duration, left=start, height=0.5, color=colors(i))

# Formatting the plot
ax.set_xlabel("Time")
ax.set_ylabel("Jobs")
ax.set_yticks(range(len(jobs)))
ax.set_yticklabels([f"Job {job_id}" for job_id, _, _ in jobs])
ax.set_title("Gantt Chart for Gavel Scheduling")
ax.invert_yaxis()

# Displaying the chart
plt.show()
