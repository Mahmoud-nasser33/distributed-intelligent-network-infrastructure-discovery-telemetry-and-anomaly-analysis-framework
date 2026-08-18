import logging
import platform
import subprocess
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.topology.discovery.base import TopologyDiscoveryProvider, TopologyEdgeResult

logger = logging.getLogger(__name__)


class ReachabilityProvider(TopologyDiscoveryProvider):

    def __init__(self, ping_timeout: int = 2, max_workers: int = 10):
        self.ping_timeout = ping_timeout
        self.max_workers = max_workers

    @property
    def name(self) -> str:
        return "reachability"

    @property
    def edge_type(self) -> str:
        return "reachable"

    @property
    def default_confidence(self) -> float:
        return 0.85

    def is_available(self) -> bool:
        return True

    def discover(self, device_ips: List[str], **kwargs) -> List[TopologyEdgeResult]:
        if len(device_ips) < 2:
            return []

        reachable_map = {}
        pairs = []
        for i in range(len(device_ips)):
            for j in range(i + 1, len(device_ips)):
                pairs.append((device_ips[i], device_ips[j]))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pair = {
                executor.submit(self._check_reachability, ip_a, ip_b): (ip_a, ip_b)
                for ip_a, ip_b in pairs
            }
            for future in as_completed(future_to_pair):
                ip_a, ip_b = future_to_pair[future]
                try:
                    reachable = future.result()
                    if reachable:
                        key = tuple(sorted([ip_a, ip_b]))
                        reachable_map[key] = True
                except Exception as e:
                    logger.debug("Reachability check failed for %s -> %s: %s",
                                 ip_a, ip_b, str(e))

        edges = []
        for (ip_a, ip_b) in reachable_map:
            evidence = {
                "source_ip": ip_a,
                "destination_ip": ip_b,
                "method": "ping",
            }
            edges.append(TopologyEdgeResult(
                source_ip=ip_a,
                destination_ip=ip_b,
                edge_type=self.edge_type,
                confidence=self.default_confidence,
                evidence=evidence,
                metadata={"provider": self.name, "timeout": self.ping_timeout},
            ))

        logger.info("Reachability discovery found %d edges from %d devices",
                     len(edges), len(device_ips))
        return edges

    def _check_reachability(self, source_ip: str, dest_ip: str) -> bool:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        count_param = "-w" if platform.system().lower() == "windows" else "-W"
        cmd = ["ping", param, "1", count_param, str(self.ping_timeout), dest_ip]
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", str(self.ping_timeout * 1000), dest_ip]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=self.ping_timeout + 5,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
