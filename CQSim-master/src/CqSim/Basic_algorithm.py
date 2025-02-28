__metaclass__ = type

class Basic_algorithm:
    def __init__(self, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None):
        self.myInfo = "Basic Algorithm"
        self.ad_mode = ad_mode
        self.element = element
        self.debug = debug
        self.paralist = para_list
        self.ad_paralist = ad_para_list
        
        if self.debug:
            self.debug.line(4, " ")
            self.debug.line(4, "#")
            self.debug.debug(f"# {self.myInfo}", 1)
            self.debug.line(4, "#")
        
        self.algStr = ""
        self.scoreList = []
        i = 0
        temp_num = len(self.element[0]) if self.element else 0
        while i < temp_num:
            self.algStr += self.element[0][i]
            i += 1
    
    def reset(self, ad_mode=None, element=None, debug=None, para_list=None, ad_para_list=None):
        if ad_mode:
            self.ad_mode = ad_mode 
        if element:
            self.element = element
        if debug:
            self.debug = debug
        if para_list:
            self.paralist = para_list
            
        self.algStr = ""
        self.scoreList = []
        i = 0
        temp_num = len(self.element[0]) if self.element else 0
        while i < temp_num:
            self.algStr += self.element[0][i]
            i += 1
            
    def get_score(self, wait_job, currentTime, para_list=None):
        self.scoreList = []
        waitNum = len(wait_job)
        if waitNum <= 0:
            return []
        else:
            i = 0
            z = currentTime - wait_job[0]['submit']
            l = wait_job[0]['reqTime']
            while i < waitNum:
                temp_w = currentTime - wait_job[i]['submit']
                if temp_w > z:
                    z = temp_w
                if wait_job[i]['reqTime'] < l:
                    l = wait_job[i]['reqTime']
                i += 1
            i = 0
            if z == 0:
                z = 1
            while i < waitNum:
                s = float(wait_job[i]['submit'])
                t = float(wait_job[i]['reqTime'])
                n = float(wait_job[i]['reqProc'])
                w = int(currentTime - s)
                self.scoreList.append(float(eval(self.algStr)))
                i += 1
        print("scores:", self.scoreList)
        return self.scoreList
            
    def log_analysis(self):
        if self.debug:
            self.debug.debug(f"* {self.myInfo} -- log_analysis", 5)
        return 1
            
    def alg_adapt(self, para_in):
        if self.debug:
            self.debug.debug(f"* {self.myInfo} -- alg_adapt", 5)
        return 1

# Fixed GavelScheduling
class GavelScheduling(Basic_algorithm):
    def __init__(self, workload_data=None, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum
        self.workload_data = workload_data
        self.algStr = "wait_time / (reqProc + 1)"  # Simplified formula
        self.hybrid_scheduler = HybridScheduling(workload_data=workload_data, ad_mode=ad_mode, element=element, debug=debug)

    def set_workload_data(self, workload_data):
        self.workload_data = workload_data

    def get_score(self, wait_job, currentTime, para_list=None):
        """Calculates scores based on the Gavel formula."""
        self.scoreList = []
        if not wait_job:
            return []

        for job in wait_job:
            waited_time = max(0, currentTime - job['submit'])
            remaining_time = job['reqProc']
        
            # Incorporate GPU consideration in the score calculation
            gpu_weight = 2 if job.get('gpu_required', 0) > 0 else 1  # Example: give higher weight to GPU jobs
            score = (waited_time / (remaining_time + 1)) * gpu_weight  # Adjusted score formula
            self.scoreList.append(score)

        print("scores:", self.scoreList)
        return self.scoreList


    def schedule(self, wait_job, currentTime):
        if not wait_job:
            return

        self.hybrid_scheduler.hybrid_schedule(wait_job, currentTime)
        
        scores = self.get_score(wait_job, currentTime)
        sorted_jobs = sorted(zip(wait_job, scores), key=lambda x: x[1], reverse=True)

        for job, _ in sorted_jobs:
            # Check if the node has enough resources
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):  # GPU check
            
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                run_time = min(job['reqProc'], self.time_quantum)
                job['reqProc'] -= run_time
                currentTime += run_time

                if job['reqProc'] <= 0:
                    self.release_resources(job)
                    self.job_finish(job['id'], currentTime)

    def release_resources(self, job):
        """Release resources including GPUs."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']
        self.available_gpus += job.get('gpu_required', 0)


    def job_finish(self, job_id, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job_id} finished at time {finish_time}", 1)


# Fixed FCFS
class FCFS(Basic_algorithm): 
    def __init__(self):
        super().__init__()
        self.completed_jobs = []
        self.myInfo = "FCFS"
        self.algStr = "0"
        self.hybrid_scheduler = HybridScheduling()
        
    def schedule_jobs(self, jobs, currentTime):
        self.hybrid_scheduler.hybrid_schedule(jobs, currentTime)
        jobs.sort(key=lambda x: x['submit'])  # Sort jobs by submission time
        
    
        # Separate GPU and CPU-only jobs
        gpu_jobs = [job for job in jobs if job.get('gpu_required', 0) > 0]
        cpu_jobs = [job for job in jobs if job.get('gpu_required', 0) == 0]
    
        # Prioritize GPU jobs first
        for job in gpu_jobs + cpu_jobs:
            if job['submit'] > currentTime:
                currentTime = job['submit']  # Wait until job arrival

            # Check if resources are available (including GPUs)
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):  # GPU check
        
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                self.completed_jobs.append(job)
                currentTime += job['reqProc']
        
                # Release resources after execution
                self.release_resources(job)
                self.job_finish(job, currentTime)


    def release_resources(self, job):
        """Release CPU, memory, and GPUs when a job finishes."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']            
        self.available_gpus += job.get('gpu_required', 0)


    def get_score(self, jobs, currentTime):
        """Assigns scores based on job arrival order."""
        self.scoreList = []
        if not jobs:
            return []
        
        sorted_jobs = sorted(jobs, key=lambda x: x['submit'])  # Sort jobs by submission time
        print("job submission times:", [job['submit'] for job in sorted_jobs])
        
        for i, job in enumerate(sorted_jobs):
            self.scoreList.append(len(jobs) - i)  # Earlier jobs get higher priority
        
        print("scores:", self.scoreList)
        return self.scoreList

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


class HybridScheduling(Basic_algorithm):
    def __init__(self, workload_data=None, ad_mode=0, element=None, debug=None, para_list=None, ad_para_list=None, time_quantum=1):
        super().__init__(ad_mode, element, debug, para_list, ad_para_list)
        self.time_quantum = time_quantum
        self.workload_data = workload_data
        self.algStr = "Hybrid Scheduling"
    
    def hybrid_schedule(self, jobs, currentTime):
        # Separate jobs based on GPU requirements
        cpu_jobs = [job for job in jobs if job.get('gpu_required', 0) == 0]
        gpu_jobs = [job for job in jobs if job.get('gpu_required', 0) > 0]
        
        # Sort jobs based on Gavel or FCFS logic
        cpu_jobs = self.sort_jobs(cpu_jobs, currentTime)
        gpu_jobs = self.sort_jobs(gpu_jobs, currentTime)
        
        # Prioritize GPU jobs first
        self.schedule_jobs(gpu_jobs, currentTime)
        self.schedule_jobs(cpu_jobs, currentTime)
        
    def sort_jobs(self, jobs, currentTime):
        # Sort jobs by the scheduling policy: Gavel (wait time) or FCFS (submission time)
        if isinstance(self, GavelScheduling):
            return sorted(jobs, key=lambda job: (currentTime - job['submit']) / (job['reqProc'] + 1), reverse=True)
        elif isinstance(self, FCFS):
            return sorted(jobs, key=lambda job: job['submit'])
        return jobs  # Default: no sorting

    def schedule_jobs(self, jobs, currentTime):
        for job in jobs:
            if job['submit'] > currentTime:
                currentTime = job['submit']  # Wait until job arrival
                if self.debug:
                    self.debug.debug(f"Waiting for job {job['id']} to arrive at time {job['submit']}", 1)
        
            # Log resource availability
            if self.debug:
                self.debug.debug(f"Available resources - Procs: {self.available_procs}, Mem: {self.available_mem}, GPUs: {self.available_gpus}", 1)

            # Check if resources are available (including GPUs)
            if (self.available_procs >= job['reqProc'] and 
                self.available_mem >= job['reqMem'] and 
                self.available_gpus >= job.get('gpu_required', 0)):
            
                # Allocate resources
                self.available_procs -= job['reqProc']
                self.available_mem -= job['reqMem']
                self.available_gpus -= job.get('gpu_required', 0)

                self.completed_jobs.append(job)
                currentTime += job['reqProc']
            
                # Log job allocation
                if self.debug:
                    self.debug.debug(f"Allocating resources to job {job['id']}: Procs: {job['reqProc']}, Mem: {job['reqMem']}, GPUs: {job.get('gpu_required', 0)}", 1)

                # Release resources after execution
                self.release_resources(job)
                self.job_finish(job, currentTime)


    def release_resources(self, job):
        """Release resources including CPUs, memory, and GPUs."""
        self.available_procs += job['reqProc']
        self.available_mem += job['reqMem']
        self.available_gpus += job.get('gpu_required', 0)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)


# Round Robin (RR) Scheduling working
class RoundRobin(Basic_algorithm):
    def __init__(self, time_quantum):
        self.time_quantum = time_quantum
        self.myInfo = "RoundRobin Scheduling Algorithm"
        self.algStr = "0"

    def schedule_jobs(self, jobs, currentTime):
        queue = jobs[:]
        while queue:
            job = queue.pop(0)
            if job['reqProc'] > self.time_quantum:
                job['reqProc'] -= self.time_quantum
                currentTime += self.time_quantum
                queue.append(job)
            else:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
    
    def get_score(self, jobs, currentTime):
        """Override to prevent CQSim from using eval(self.algStr)."""
        return [0] * len(jobs)  # Assign equal priority to all jobs in Round Robin

'''
# Shortest Job First (SJF) Scheduling
class SJF(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['reqProc'])
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                self.job_finish(job, currentTime)
                currentTime += job['reqProc']

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
'''

'''
# Shortest Remaining Time First (SRTF) Scheduling
class SRTF(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        while jobs:
            job = min(jobs, key=lambda x: x['reqProc'])
            if job['submit'] <= currentTime:
                if job['reqProc'] > 0:
                    currentTime += job['reqProc']
                    job['reqProc'] = 0
                    self.job_finish(job, currentTime)
                jobs.remove(job)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
'''

# Priority Scheduling working
class PriorityScheduling(Basic_algorithm):
    def __init__(self, priority=None):
        super().__init__()  # Call parent constructor
        self.priority = priority  # Store priority if needed
        self.myInfo = "Priority Scheduling Algorithm"  # Required for CQSim
        self.algStr = "0"  # Default value to avoid eval error


    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['priority'], reverse=True)
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)

    def get_score(self, jobs, currentTime):
        """Override to prevent CQSim from using eval(self.algStr)."""
        return [job.get('priority', 0) for job in jobs]  # Assign job priorities


'''
# Multilevel Feedback Queue Scheduling
class MultilevelFeedbackQueue(Basic_algorithm):
    def __init__(self, queues):
        self.queues = queues

    def schedule_jobs(self, jobs, currentTime):
        for queue in self.queues:
            queue_jobs = [job for job in jobs if job['priority'] == queue]
            RoundRobin(time_quantum=2).schedule_jobs(queue_jobs, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
'''
'''
# Earliest Deadline First (EDF) Scheduling
class EDF(Basic_algorithm):
    def schedule_jobs(self, jobs, currentTime):
        sorted_jobs = sorted(jobs, key=lambda x: x['deadline'])
        for job in sorted_jobs:
            if job['submit'] <= currentTime:
                currentTime += job['reqProc']
                self.job_finish(job, currentTime)

    def job_finish(self, job, finish_time):
        if self.debug:
            self.debug.debug(f"Job {job['id']} finished at time {finish_time}", 1)
'''