import logging
import platform
import subprocess
import re
from typing import List, Optional
from app.topology.discovery.base import TopologyDiscoveryProvider, TopologyEdgeResult

logger = logging.getLogger(__name__)


class ARPNeighborProvider(TopologyDiscoveryProvider):

    @property
    def name(self) -> str:
        return "arp_neighbor"

    @property
    def edge_type(self) -> str:
        return "arp_neighbor"

    @property
    def default_confidence(self) -> float:
        return 0.9

    def is_available(self) -> bool:
        return True

    def discover(self, device_ips: List[str], **kwargs) -> List[TopologyEdgeResult]:
        arp_table = self._get_arp_table()
        if not arp_table:
            logger.warning("Failed to retrieve ARP table")
            return []

        ip_set = set(device_ips)
        tracked_entries = [
            entry for entry in arp_table
            if entry.get("ip") in ip_set and entry.get("mac")
        ]

        edges = []
        mac_to_ips = {}
        for entry in tracked_entries:
            mac = entry["mac"].upper()
            ip = entry["ip"]
            if mac not in mac_to_ips:
                mac_to_ips[mac] = []
            mac_to_ips[mac].append(ip)

        for mac, ips in mac_to_ips.items():
            if len(ips) < 2:
                continue
            for i in range(len(ips)):
                for j in range(i + 1, len(ips)):
                    evidence = {
                        "shared_mac": mac,
                        "arp_type": self._get_arp_type(mac, arp_table),
                    }
                    edges.append(TopologyEdgeResult(
                        source_ip=ips[i],
                        destination_ip=ips[j],
                        edge_type=self.edge_type,
                        confidence=self.default_confidence,
                        evidence=evidence,
                        metadata={"provider": self.name},
                    ))

        logger.info("ARP neighbor discovery found %d edges from %d devices",
                     len(edges), len(device_ips))
        return edges

    def _get_arp_table(self) -> List[dict]:
        entries = []
        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    match = re.match(
                        r'\s*(\d+\.\d+\.\d+\.\d+)\s+([\w:-]+)\s+(\S+)',
                        line
                    )
                    if match:
                        entries.append({
                            "ip": match.group(1),
                            "mac": match.group(2),
                            "type": match.group(3),
                        })
        except Exception as e:
            logger.error("ARP table retrieval failed: %s", str(e))

        return entries

    def _get_arp_type(self, mac: str, arp_table: List[dict]) -> str:
        for entry in arp_table:
            if entry.get("mac", "").upper() == mac:
                return entry.get("type", "dynamic")
        return "dynamic"
