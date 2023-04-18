from typing import Dict

metrics: Dict[str, Dict[str, float]] = {}


def update_metrics(endpoint: str, request_time: float, error: bool, incoming_bytes: int) -> None:
    if endpoint not in metrics:
        metrics[endpoint] = {
            "request_count": 0,
            "error_count": 0,
            "incoming_bytes": 0,
            "avg_response_time": 0.0
        }

    metrics[endpoint]["request_count"] += 1
    metrics[endpoint]["error_count"] += int(error)
    metrics[endpoint]["incoming_bytes"] += incoming_bytes

    # Update average response time using exponential moving average
    alpha = 0.2
    if metrics[endpoint]["avg_response_time"] == 0.0:
        metrics[endpoint]["avg_response_time"] = request_time
    else:
        metrics[endpoint]["avg_response_time"] = alpha * request_time + (1 - alpha) * metrics[endpoint][
            "avg_response_time"]


def get_stats() -> Dict[str, Dict[str, float]]:
    return metrics
