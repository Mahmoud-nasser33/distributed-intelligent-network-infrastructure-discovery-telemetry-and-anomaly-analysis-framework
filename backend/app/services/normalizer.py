import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.config.database import db
from app.discovery.base import DiscoveryResult
from app.repositories.device_repo import DeviceRepository, ServiceRepository, InterfaceRepository
from app.repositories.observation_repo import ObservationRepository

logger = logging.getLogger(__name__)


class ObservationNormalizer:

    def process_discovery_results(self, results: List[DiscoveryResult],
                                  agent_id: str = None,
                                  scan_job_id: str = None) -> List[Dict[str, Any]]:
        processed = []
        for result in results:
            try:
                observation = self._create_observation(result, agent_id, scan_job_id)
                device = self._upsert_device(result, agent_id)
                self._upsert_services(device.id, result.services)
                self._upsert_interfaces(device.id, result.interfaces)

                ObservationRepository.update_device_id(observation.id, device.id)

                processed.append({
                    "observation_id": observation.id,
                    "device_id": device.id,
                    "ip_address": result.ip_address,
                })
                logger.info("Processed observation for %s -> device %s",
                            result.ip_address, device.id)

            except Exception as e:
                logger.error("Failed to process observation for %s: %s",
                             result.ip_address, str(e))
                db.session.rollback()

        return processed

    def _create_observation(self, result: DiscoveryResult,
                            agent_id: str, scan_job_id: str):
        return ObservationRepository.create({
            "agent_id": agent_id,
            "scan_job_id": scan_job_id,
            "source": result.raw_data.get("provider", "unknown"),
            "target_ip": result.ip_address,
            "target_mac": result.mac_address,
            "observation_type": "discovery",
            "raw_data": result.raw_data,
            "normalized_data": result.to_dict(),
            "confidence": result.os_confidence,
        })

    def _upsert_device(self, result: DiscoveryResult, agent_id: str):
        return DeviceRepository.create_or_update(
            ip_address=result.ip_address,
            agent_id=agent_id,
            data={
                "mac_address": result.mac_address,
                "hostname": result.hostname,
                "vendor": result.vendor,
                "device_type": result.device_type,
                "os_detection": result.os_detection,
                "os_confidence": result.os_confidence,
                "classification_confidence": result.classification_confidence,
                "status": result.status,
            }
        )

    def _upsert_services(self, device_id: str, services: List[Dict]):
        for svc in services:
            ServiceRepository.upsert(
                device_id=device_id,
                port=svc["port"],
                protocol=svc.get("protocol", "tcp"),
                data=svc,
            )

    def _upsert_interfaces(self, device_id: str, interfaces: List[Dict]):
        for iface in interfaces:
            InterfaceRepository.upsert(
                device_id=device_id,
                name=iface.get("name", "unknown"),
                data=iface,
            )
