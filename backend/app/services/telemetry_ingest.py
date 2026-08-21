import logging
from datetime import datetime
from typing import Dict, List, Tuple

from app.models.agent import Agent
from app.repositories.device_repo import DeviceRepository
from app.repositories.metric_repo import MetricRepository

logger = logging.getLogger(__name__)

ALLOWED_METRIC_TYPES = {
    "availability", "latency", "packet_loss", "response_time",
    "traffic_volume", "packet_rate", "cpu_usage", "memory_usage",
    "uptime", "interface_state",
}


def ingest_agent_results(agent: Agent, results: List[Dict]) -> Dict:
    """Store telemetry results pushed by a distributed agent.

    Each result targets one device by IP; unknown devices are created and
    attributed to the agent. Returns counts of what was stored/skipped.
    """
    stored = 0
    skipped = 0
    devices_touched = set()

    for result in results:
        if not isinstance(result, dict):
            skipped += 1
            continue

        ip_address = result.get("ip_address")
        metrics = result.get("metrics")
        if not ip_address or not isinstance(metrics, list):
            logger.warning("Agent %s sent malformed result, skipping: %r",
                           agent.name, result)
            skipped += 1
            continue

        device = DeviceRepository.find_by_ip(ip_address)
        if device is None:
            device = DeviceRepository.create_or_update(
                ip_address,
                agent.id,
                {"hostname": result.get("hostname"), "status": result.get("status", "online")},
            )

        for metric in metrics:
            if not isinstance(metric, dict):
                skipped += 1
                continue
            metric_type = metric.get("metric_type")
            value = metric.get("value")
            if metric_type not in ALLOWED_METRIC_TYPES or not isinstance(value, (int, float)):
                logger.warning("Agent %s sent invalid metric %r, skipping",
                               agent.name, metric)
                skipped += 1
                continue

            MetricRepository.record({
                "device_id": device.id,
                "metric_type": metric_type,
                "value": float(value),
                "unit": metric.get("unit"),
                "source": "agent",
                "agent_id": agent.id,
                "timestamp": _parse_timestamp(metric.get("timestamp")),
            })
            stored += 1

        status = result.get("status") or _status_from_metrics(metrics)
        if status in ("online", "offline"):
            DeviceRepository.update_status(device.id, status)
        devices_touched.add(device.id)

    return {
        "stored": stored,
        "skipped": skipped,
        "devices": len(devices_touched),
    }


def _status_from_metrics(metrics: List[Dict]) -> str:
    for metric in metrics:
        if isinstance(metric, dict) and metric.get("metric_type") == "availability":
            value = metric.get("value")
            if isinstance(value, (int, float)):
                return "online" if value > 0 else "offline"
    return "unknown"


def _parse_timestamp(raw) -> datetime:
    if not raw or isinstance(raw, datetime):
        return raw
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
