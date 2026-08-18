import subprocess
import platform
import logging
import time
from typing import Dict, Any, Optional
from app.config.database import db
from app.models.device import Device
from app.repositories.metric_repo import MetricRepository

logger = logging.getLogger(__name__)


class TelemetryCollector:

    def collect_ping_metrics(self, device_id: str, ip_address: str) -> Dict[str, Any]:
        metrics = {}

        latency_ms, packet_loss, success = self._ping(ip_address)
        if success:
            MetricRepository.record({
                "device_id": device_id,
                "metric_type": "latency",
                "value": latency_ms,
                "unit": "ms",
                "source": "ping",
            })
            metrics["latency"] = latency_ms

            MetricRepository.record({
                "device_id": device_id,
                "metric_type": "availability",
                "value": 1.0,
                "unit": "ratio",
                "source": "ping",
            })
            metrics["availability"] = 1.0

            MetricRepository.record({
                "device_id": device_id,
                "metric_type": "packet_loss",
                "value": packet_loss,
                "unit": "percent",
                "source": "ping",
            })
            metrics["packet_loss"] = packet_loss

            Device.query.get(device_id).status = "online"
        else:
            MetricRepository.record({
                "device_id": device_id,
                "metric_type": "availability",
                "value": 0.0,
                "unit": "ratio",
                "source": "ping",
            })
            metrics["availability"] = 0.0

            Device.query.get(device_id).status = "offline"

        db.session.commit()
        return metrics

    def collect_all_devices(self) -> Dict[str, Any]:
        devices = Device.query.filter(Device.status != "offline").all()
        results = {}
        for device in devices:
            try:
                results[device.id] = self.collect_ping_metrics(
                    device.id, device.ip_address
                )
            except Exception as e:
                logger.error("Telemetry collection failed for %s: %s",
                             device.ip_address, str(e))
                results[device.id] = {"error": str(e)}
        return results

    def _ping(self, target: str, count: int = 4) -> tuple:
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), "-w", "2000", target]
            else:
                cmd = ["ping", "-c", str(count), "-W", "2", target]

            creationflags = 0
            if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=creationflags
            )

            if result.returncode != 0:
                return 0, 100.0, False

            output = result.stdout
            if platform.system().lower() == "windows":
                import re
                times = re.findall(r"time[=<](\d+\.?\d*)ms", output)
                loss_match = re.search(r"(\d+)% loss", output)
                if times:
                    avg_time = sum(float(t) for t in times) / len(times)
                    loss = float(loss_match.group(1)) if loss_match else 0.0
                    return avg_time, loss, True
            else:
                import re
                avg_match = re.search(r"min/avg/max.*=\s*[\d.]+/([\d.]+)/", output)
                loss_match = re.search(r"(\d+\.?\d*)% packet loss", output)
                if avg_match:
                    avg_time = float(avg_match.group(1))
                    loss = float(loss_match.group(1)) if loss_match else 0.0
                    return avg_time, loss, True

            return 0, 100.0, False

        except Exception as e:
            logger.error("Ping failed for %s: %s", target, str(e))
            return 0, 100.0, False
