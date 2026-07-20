from prometheus_client import Gauge, Counter, Histogram, Summary
import psutil
import os # Ensure os is imported
import logging

logger = logging.getLogger(__name__)

# System metrics
SYSTEM_MEMORY = Gauge("system_memory_bytes", "System memory usage")
SYSTEM_CPU = Gauge("system_cpu_usage", "System CPU usage")
DISK_USAGE = Gauge("disk_usage_bytes", "Disk usage")

# Application metrics
ACTIVE_USERS = Gauge("active_users", "Number of active users")
TOTAL_MEMORIES = Gauge("total_memories", "Total memories stored")
PENDING_AUDITS = Gauge("pending_audits", "Pending audit entries")
CACHE_HIT_RATE = Gauge("cache_hit_rate", "Cache hit rate")

# Pipeline metrics
PIPELINE_LATENCY = Histogram("pipeline_latency_seconds", "Pipeline execution time")
JUDGE_REJECTION_RATE = Counter("judge_rejections_total", "Total judge rejections")
PATTERN_GRADUATION_RATE = Counter("pattern_graduations_total", "Total pattern graduations")
CRYSTALLIZATION_VELOCITY = Gauge("crystallization_rate", "Patterns graduated per 100 interactions")
EVAPORATION_COUNT = Counter("evaporations_total", "Total memories faded from Layer 2 to the void")
CONDENSATION_VELOCITY = Gauge("condensation_rate", "Telemetry condensed into episodic memory")
SUBLIMATION_COUNT = Counter("sublimations_total", "Total brittle patterns returned to liquid/gas state")
PLASMA_ACTIVE = Gauge("plasma_active", "Binary flag indicating if high-complexity reasoning is active")

# API specific metrics
API_REQUEST_COUNT = Counter("api_requests_total", "Total count of API requests", ["method", "endpoint", "status"])
API_REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Latency of API requests in seconds", ["method", "endpoint"])

def update_system_metrics():
    """Update system level metrics."""
    try:
        SYSTEM_MEMORY.set(psutil.virtual_memory().used)
        SYSTEM_CPU.set(psutil.cpu_percent())
        DISK_USAGE.set(psutil.disk_usage(os.getcwd()).used)
    except Exception as e:
        logger.error(f"Failed to update system metrics: {e}")