# gunicorn.conf.py — production WSGI server configuration
# Used by: Procfile (Heroku / Railway), Elastic Beanstalk, Docker, EC2
import os
import multiprocessing

# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

# ---------------------------------------------------------------------------
# Worker processes
# On AWS the recommended formula is: (2 x vCPUs) + 1
# We fall back to 2 workers on small instances / single-vCPU free-tier.
# ---------------------------------------------------------------------------
workers = int(os.environ.get("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count() * 2 + 1)))
worker_class = "sync"
threads = 1

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
timeout = 60          # worker is killed and restarted if silent for 60 s
keepalive = 5         # seconds to wait for next request on a Keep-Alive connection
graceful_timeout = 30 # seconds to finish pending requests on SIGTERM

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Use "-" to send access / error logs to stdout/stderr so AWS CloudWatch,
# Elastic Beanstalk, and ECS can capture them without extra config.
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ---------------------------------------------------------------------------
# Process naming (visible in `ps aux` on EC2)
# ---------------------------------------------------------------------------
proc_name = "secret-scanner"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Do not expose gunicorn version in Server header.
forwarded_allow_ips = "*"          # trust X-Forwarded-For from ALB / ELB
secure_scheme_headers = {"X-Forwarded-Proto": "https"}
