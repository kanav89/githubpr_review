# Gunicorn configuration file
import multiprocessing

# Number of workers
workers = multiprocessing.cpu_count() * 2 + 1
# Timeout
timeout = 300

