import logging
from datetime import datetime, timezone
from typing import List, Optional
from app.config.database import db
from app.discovery.engine import CompositeDiscoveryEngine
from app.discovery.nmap_provider import NmapDiscoveryProvider
from app.discovery.icmp_provider import ICMPDiscoveryProvider
from app.discovery.arp_provider import ARPDiscoveryProvider
from app.services.normalizer import ObservationNormalizer
from app.repositories.scan_job_repo import ScanJobRepository
from app.repositories.agent_repo import AgentRepository
from app.repositories.device_repo import DeviceRepository

logger = logging.getLogger(__name__)


class DiscoveryOrchestrator:

    def __init__(self, nmap_path: str = "nmap"):
        self.engine = CompositeDiscoveryEngine()
        self.normalizer = ObservationNormalizer()

        nmap_provider = NmapDiscoveryProvider(nmap_path)
        icmp_provider = ICMPDiscoveryProvider()
        arp_provider = ARPDiscoveryProvider()

        self.engine.register_provider(nmap_provider)
        self.engine.register_provider(icmp_provider)
        self.engine.register_provider(arp_provider)

    def run_discovery(self, scan_job_id: str, target: str,
                      agent_id: str = None,
                      scan_type: str = "host",
                      providers: List[str] = None,
                      arguments: str = None) -> dict:
        ScanJobRepository.update_status(scan_job_id, "running")

        try:
            if scan_type == "network":
                results = self.engine.discover_network(
                    target, providers=providers,
                    arguments=arguments or "-sn -T4"
                )
            else:
                results = self.engine.discover_host(
                    target, providers=providers,
                    arguments=arguments or "-sV -O -T4"
                )
                if not results:
                    results = []

            processed = self.normalizer.process_discovery_results(
                results, agent_id=agent_id, scan_job_id=scan_job_id
            )

            devices_found = len(processed)
            status = "completed" if results else "completed"

            ScanJobRepository.update_status(
                scan_job_id, status,
                observations_count=len(results),
                devices_found=devices_found,
                result_summary={
                    "targets_scanned": 1 if scan_type == "host" else 0,
                    "devices_discovered": devices_found,
                    "providers_used": providers or ["all"],
                },
            )

            return {
                "status": status,
                "devices_found": devices_found,
                "observations": len(results),
                "processed": processed,
            }

        except Exception as e:
            logger.error("Discovery failed for job %s: %s", scan_job_id, str(e))
            ScanJobRepository.update_status(
                scan_job_id, "failed",
                error_message=str(e),
            )
            return {
                "status": "failed",
                "error": str(e),
            }

    def get_provider_status(self) -> dict:
        status = {}
        for provider in self.engine._providers:
            status[provider.name] = provider.is_available()
        return status
