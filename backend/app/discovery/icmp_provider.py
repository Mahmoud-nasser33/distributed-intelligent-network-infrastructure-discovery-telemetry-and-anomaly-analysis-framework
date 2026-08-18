import logging
import platform
import subprocess
from typing import List, Optional
from app.discovery.base import DiscoveryProvider, DiscoveryResult
from app.services.classifier import DeviceClassifier

logger = logging.getLogger(__name__)


class ICMPDiscoveryProvider(DiscoveryProvider):

    def __init__(self):
        self.classifier = DeviceClassifier()

    @property
    def name(self) -> str:
        return "icmp"

    def is_available(self) -> bool:
        return True

    def discover_host(self, target: str, **kwargs) -> Optional[DiscoveryResult]:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        cmd = ["ping", param, "1", "-w", "2000", target]
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "2000", target]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            if result.returncode == 0:
                return DiscoveryResult(
                    ip_address=target,
                    status="online",
                    raw_data={"ping_output": result.stdout},
                )
            return None
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.debug("ICMP probe failed for %s: %s", target, str(e))
            return None

    def discover_network(self, network_range: str, **kwargs) -> List[DiscoveryResult]:
        logger.info("ICMP discovery not implemented for network ranges, use nmap or arp")
        return []
