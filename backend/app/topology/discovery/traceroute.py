import logging
import platform
import subprocess
import re
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.topology.discovery.base import TopologyDiscoveryProvider, TopologyEdgeResult

logger = logging.getLogger(__name__)


class TracerouteProvider(TopologyDiscoveryProvider):

    def __init__(self, max_hops: int = 15, timeout: int = 5, max_workers: int = 5):
        self.max_hops = max_hops
        self.timeout = timeout
        self.max_workers = max_workers

    @property
    def name(self) -> str:
        return "traceroute"

    @property
    def edge_type(self) -> str:
        return "traceroute_hop"

    @property
    def default_confidence(self) -> float:
        return 0.5

    def is_available(self) -> bool:
        return True

    def discover(self, device_ips: List[str], **kwargs) -> List[TopologyEdgeResult]:
        if len(device_ips) < 2:
            return []

        edges = []
        seen_triples = set()

        pairs = []
        for i in range(len(device_ips)):
            for j in range(i + 1, len(device_ips)):
                pairs.append((device_ips[i], device_ips[j]))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pair = {
                executor.submit(self._run_traceroute, ip_a, ip_b): (ip_a, ip_b)
                for ip_a, ip_b in pairs
            }
            for future in as_completed(future_to_pair):
                ip_a, ip_b = future_to_pair[future]
                try:
                    hops = future.result()
                    hop_edges = self._process_hops(ip_a, ip_b, hops, device_ips, seen_triples)
                    edges.extend(hop_edges)
                except Exception as e:
                    logger.debug("Traceroute failed for %s -> %s: %s",
                                 ip_a, ip_b, str(e))

        logger.info("Traceroute discovery found %d edges from %d devices",
                     len(edges), len(device_ips))
        return edges

    def _run_traceroute(self, source_ip: str, dest_ip: str) -> List[Optional[str]]:
        if platform.system().lower() == "windows":
            cmd = ["tracert", "-d", "-h", str(self.max_hops), "-w", str(self.timeout * 1000), dest_ip]
        else:
            cmd = ["traceroute", "-n", "-m", str(self.max_hops), "-w", str(self.timeout), dest_ip]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=self.timeout * self.max_hops + 10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return self._parse_traceroute(result.stdout)
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug("Traceroute command failed: %s", str(e))
            return []

    def _parse_traceroute(self, output: str) -> List[Optional[str]]:
        hops = []
        ip_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')

        for line in output.splitlines():
            match = ip_pattern.search(line)
            if match:
                ip = match.group(1)
                if ip != "*":
                    hops.append(ip)
                else:
                    hops.append(None)
            elif "*" in line:
                hops.append(None)

        return hops

    def _process_hops(self, source_ip: str, dest_ip: str, hops: List[Optional[str]],
                      device_ips: List[str], seen_triples: set) -> List[TopologyEdgeResult]:
        edges = []
        device_set = set(device_ips)

        known_hops = [h for h in hops if h and h in device_set]

        if len(known_hops) >= 2:
            for i in range(len(known_hops) - 1):
                hop_a = known_hops[i]
                hop_b = known_hops[i + 1]
                triple = (hop_a, hop_b, "traceroute_hop")
                if triple not in seen_triples:
                    seen_triples.add(triple)
                    confidence = self.default_confidence
                    if i == 0:
                        confidence = min(confidence + 0.1, 0.7)

                    evidence = {
                        "source_ip": source_ip,
                        "destination_ip": dest_ip,
                        "hop_position": i + 1,
                        "total_hops": len(known_hops),
                    }
                    edges.append(TopologyEdgeResult(
                        source_ip=hop_a,
                        destination_ip=hop_b,
                        edge_type=self.edge_type,
                        confidence=confidence,
                        evidence=evidence,
                        metadata={"provider": self.name, "max_hops": self.max_hops},
                    ))

        return edges
