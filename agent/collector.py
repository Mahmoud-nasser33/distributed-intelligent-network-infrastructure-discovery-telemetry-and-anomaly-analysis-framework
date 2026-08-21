import ipaddress
import logging
import platform
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

logger = logging.getLogger(__name__)


class PingCollector:
    """Collects ping-based telemetry for a set of targets."""

    def __init__(self, ping_count: int = 2, timeout_ms: int = 2000,
                 max_workers: int = 20):
        self.ping_count = ping_count
        self.timeout_ms = timeout_ms
        self.max_workers = max_workers
        self._is_windows = platform.system().lower() == "windows"

    def scope_targets(self, network_scope: str) -> List[str]:
        """Expand a CIDR range (or single IP / comma-separated list) to host IPs."""
        targets = []
        for part in [p.strip() for p in network_scope.split(",") if p.strip()]:
            try:
                if "/" in part:
                    network = ipaddress.ip_network(part, strict=False)
                    targets.extend(str(h) for h in network.hosts())
                else:
                    ipaddress.ip_address(part)
                    targets.append(part)
            except ValueError:
                logger.warning("Invalid target in scope, skipping: %s", part)
        return targets

    def collect(self, targets: List[str]) -> List[Dict]:
        """Collect metrics for all targets concurrently."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self.collect_target, t): t for t in targets}
            for future in as_completed(futures):
                target = futures[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error("Collection failed for %s: %s", target, str(e))
                    results.append({
                        "ip_address": target,
                        "status": "offline",
                        "metrics": [],
                    })
        return results

    def collect_target(self, target: str) -> Dict:
        latency_ms, packet_loss, success = self._ping(target)
        metrics = []

        if success:
            metrics.append({"metric_type": "latency", "value": round(latency_ms, 2), "unit": "ms"})
            metrics.append({"metric_type": "availability", "value": 1.0, "unit": "ratio"})
            metrics.append({"metric_type": "packet_loss", "value": packet_loss, "unit": "percent"})
            status = "online"
        else:
            metrics.append({"metric_type": "availability", "value": 0.0, "unit": "ratio"})
            status = "offline"

        return {
            "ip_address": target,
            "status": status,
            "metrics": metrics,
        }

    def _ping(self, target: str):
        try:
            if self._is_windows:
                cmd = ["ping", "-n", str(self.ping_count),
                       "-w", str(self.timeout_ms), target]
            else:
                cmd = ["ping", "-c", str(self.ping_count),
                       "-W", str(max(1, self.timeout_ms // 1000)), target]

            creationflags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                creationflags=creationflags,
            )

            if result.returncode != 0:
                return 0, 100.0, False

            output = result.stdout
            times = re.findall(r"time[=<](\d+\.?\d*)\s*ms", output)
            loss_match = re.search(r"(\d+\.?\d*)%(?:\s+packet)?\s+loss", output)
            loss = float(loss_match.group(1)) if loss_match else 0.0

            if not times:
                return 0, 100.0, False

            avg_time = sum(float(t) for t in times) / len(times)
            return avg_time, loss, True

        except Exception as e:
            logger.error("Ping failed for %s: %s", target, str(e))
            return 0, 100.0, False
