import logging
import subprocess
import re
from typing import List, Optional
from app.discovery.base import DiscoveryProvider, DiscoveryResult

logger = logging.getLogger(__name__)


class ARPDiscoveryProvider(DiscoveryProvider):

    @property
    def name(self) -> str:
        return "arp"

    def is_available(self) -> bool:
        return True

    def discover_host(self, target: str, **kwargs) -> Optional[DiscoveryResult]:
        entries = self._get_arp_table()
        for entry in entries:
            if entry.get("ip") == target:
                return DiscoveryResult(
                    ip_address=target,
                    mac_address=entry.get("mac"),
                    vendor=None,
                    raw_data={"arp_entry": entry},
                )
        return None

    def discover_network(self, network_range: str, **kwargs) -> List[DiscoveryResult]:
        results = []
        entries = self._get_arp_table()
        for entry in entries:
            if entry.get("mac") and entry.get("ip"):
                results.append(DiscoveryResult(
                    ip_address=entry["ip"],
                    mac_address=entry["mac"],
                    raw_data={"arp_entry": entry},
                ))
        return results

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
