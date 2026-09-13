from prometheus_client import Counter, Histogram, Gauge

# --- Crystallization Metrics ---
crystallization_events = Counter(
    'personavault_crystallization_events_total',
    'Total number of crystallization events triggered',
    ['environment_id', 'source_type', 'status']  # status: success, failed
)

crystallization_duration = Histogram(
    'personavault_crystallization_duration_seconds',
    'Time taken to crystallize a pattern',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# --- Prediction Metrics ---
prediction_requests = Counter(
    'personavault_prediction_requests_total',
    'Total number of prediction requests',
    ['environment_id', 'status']  # status: success, error
)

prediction_latency = Histogram(
    'personavault_prediction_latency_seconds',
    'Time taken to generate a prediction',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# --- Runtime Health ---
environment_health = Gauge(
    'personavault_environment_health',
    'Health status of an environment (1=healthy, 0=unhealthy)',
    ['environment_id']
)

# --- Compression Metrics ---
compression_ratio = Gauge(
    'personavault_compression_ratio',
    'Current intelligence compression ratio',
    ['environment_id']
)

compression_events = Counter(
    'personavault_compression_events_total',
    'Total number of meta-pattern synthesis events',
    ['environment_id', 'input_count', 'output_count']
)

# --- Helper Functions ---
def track_compression(environment_id: str, input_count: int, output_count: int, ratio: int):
    """Track a compression/synthesis event."""
    compression_ratio.labels(environment_id=environment_id).set(ratio)
    compression_events.labels(environment_id=environment_id, input_count=input_count, output_count=output_count).inc()

def track_crystallization(environment_id: str, source_type: str, duration: float, status: str = "success"):
    """Track a crystallization event."""
    crystallization_events.labels(environment_id=environment_id, source_type=source_type, status=status).inc()
    crystallization_duration.observe(duration)

def track_prediction(environment_id: str, duration: float, status: str = "success"):
    """Track a prediction request."""
    prediction_requests.labels(environment_id=environment_id, status=status).inc()
    prediction_latency.observe(duration)
