import logging
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.config.database import db
from app.models.telemetry import Metric
from app.models.anomaly import Anomaly
from app.repositories.metric_repo import MetricRepository
from app.repositories.anomaly_repo import AnomalyRepository

logger = logging.getLogger(__name__)


class BehavioralBaseline:

    def __init__(self, min_samples: int = 10, z_threshold: float = 3.0):
        self.min_samples = min_samples
        self.z_threshold = z_threshold

    def compute_stats(self, values: List[float]) -> Dict[str, float]:
        if not values:
            return {}
        arr = np.array(values, dtype=float)
        return {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "p25": float(np.percentile(arr, 25)),
            "p75": float(np.percentile(arr, 75)),
            "p95": float(np.percentile(arr, 95)),
            "count": len(values),
        }


class AnomalyDetector:

    def __init__(self):
        self.baseline = BehavioralBaseline()
        self.z_threshold = 3.0

    def check_device_metrics(self, device_id: str) -> List[Dict[str, Any]]:
        anomalies = []

        metric_types = db.session.query(Metric.metric_type).filter_by(
            device_id=device_id
        ).distinct().all()

        for (metric_type,) in metric_types:
            metrics = Metric.query.filter_by(
                device_id=device_id, metric_type=metric_type
            ).order_by(Metric.timestamp.desc()).limit(100).all()

            if len(metrics) < self.baseline.min_samples:
                continue

            values = [m.value for m in metrics]
            stats = self.baseline.compute_stats(values[:-1])

            if not stats or stats.get("std", 0) == 0:
                continue

            latest = values[0]
            z_score = abs(latest - stats["mean"]) / stats["std"]

            if z_score > self.z_threshold:
                anomaly_data = {
                    "device_id": device_id,
                    "detector": "statistical_zscore",
                    "category": "behavioral",
                    "severity": self._compute_severity(z_score),
                    "metric_type": metric_type,
                    "observed_value": latest,
                    "expected_value": stats["mean"],
                    "threshold": stats["mean"] + self.z_threshold * stats["std"],
                    "confidence": min(0.99, 0.5 + (z_score - self.z_threshold) * 0.1),
                    "evidence": {
                        "z_score": round(z_score, 4),
                        "baseline_mean": round(stats["mean"], 4),
                        "baseline_std": round(stats["std"], 4),
                        "sample_count": stats["count"],
                        "recent_values": values[:5],
                    },
                    "explanation": (
                        f"Metric {metric_type} value {latest} deviates significantly "
                        f"from the baseline (mean={stats['mean']:.2f}, "
                        f"std={stats['std']:.2f}, z_score={z_score:.2f})"
                    ),
                }
                anomalies.append(anomaly_data)

        return anomalies

    def detect_and_store(self, device_id: str) -> List[Anomaly]:
        anomaly_data_list = self.check_device_metrics(device_id)
        stored = []
        for data in anomaly_data_list:
            anomaly = AnomalyRepository.create(data)
            stored.append(anomaly)
        return stored

    def _compute_severity(self, z_score: float) -> str:
        if z_score > 5.0:
            return "critical"
        elif z_score > 4.0:
            return "high"
        elif z_score > 3.5:
            return "medium"
        return "low"


class ThresholdDetector:

    def __init__(self):
        self.thresholds = {
            "latency": {"warning": 50, "critical": 200},
            "packet_loss": {"warning": 5, "critical": 20},
            "cpu_usage": {"warning": 80, "critical": 95},
            "memory_usage": {"warning": 85, "critical": 95},
        }

    def check_device(self, device_id: str) -> List[Dict[str, Any]]:
        anomalies = []
        for metric_type, limits in self.thresholds.items():
            latest = MetricRepository.get_latest(device_id, metric_type)
            if not latest:
                continue

            severity = None
            if latest.value >= limits["critical"]:
                severity = "critical"
            elif latest.value >= limits["warning"]:
                severity = "medium"

            if severity:
                anomalies.append({
                    "device_id": device_id,
                    "detector": "threshold",
                    "category": "threshold",
                    "severity": severity,
                    "metric_type": metric_type,
                    "observed_value": latest.value,
                    "expected_value": None,
                    "threshold": limits["critical"] if severity == "critical" else limits["warning"],
                    "confidence": 0.95,
                    "evidence": {
                        "threshold_config": limits,
                        "metric_value": latest.value,
                        "metric_timestamp": latest.timestamp.isoformat(),
                    },
                    "explanation": (
                        f"{metric_type} value {latest.value} exceeded "
                        f"{'critical' if severity == 'critical' else 'warning'} "
                        f"threshold of {limits['critical'] if severity == 'critical' else limits['warning']}"
                    ),
                })
        return anomalies
