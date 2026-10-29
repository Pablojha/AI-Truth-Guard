import logging
import uuid
import time
import json
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RequestContext:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self.start_time = time.time()
        self.events: list[Dict[str, Any]] = []

    def add_event(self, event_type: str, data: Dict[str, Any] = None):
        event = {
            "timestamp": time.time() - self.start_time,
            "type": event_type,
            "data": data or {}
        }
        self.events.append(event)
        logger.info(f"[{self.request_id}] {event_type}: {data}")

    def get_latency_ms(self) -> float:
        return (time.time() - self.start_time) * 1000


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log_event(self, event_type: str, request_id: str, **kwargs):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "event": event_type,
            **kwargs
        }
        self.logger.info(json.dumps(entry))


# Global metrics
metrics = {
    "total_requests": 0,
    "total_claims_processed": 0,
    "verdict_counts": {
        "SUPPORTED": 0,
        "REFUTED": 0,
        "NOT_ENOUGH_EVIDENCE": 0,
        "ABSTAIN": 0,
    },
    "model_failures": 0,
    "latencies": [],
}


def record_verdict(verdict: str):
    if verdict in metrics["verdict_counts"]:
        metrics["verdict_counts"][verdict] += 1


def record_latency(latency_ms: float):
    metrics["latencies"].append(latency_ms)


def get_metrics_summary() -> Dict[str, Any]:
    latencies = metrics["latencies"]
    return {
        "total_requests": metrics["total_requests"],
        "total_claims_processed": metrics["total_claims_processed"],
        "verdict_distribution": metrics["verdict_counts"],
        "model_failures": metrics["model_failures"],
        "latency_p50_ms": sorted(latencies)[len(latencies) // 2] if latencies else 0,
        "latency_p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
        "latency_avg_ms": sum(latencies) / len(latencies) if latencies else 0,
    }
