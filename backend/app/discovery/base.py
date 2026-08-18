from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class DiscoveryResult:
    def __init__(self, ip_address: str, mac_address: str = None,
                 hostname: str = None, vendor: str = None,
                 os_detection: str = None, os_confidence: float = None,
                 device_type: str = None, classification_confidence: float = None,
                 services: List[Dict[str, Any]] = None,
                 interfaces: List[Dict[str, Any]] = None,
                 raw_data: Dict[str, Any] = None,
                 status: str = "online"):
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.hostname = hostname
        self.vendor = vendor
        self.os_detection = os_detection
        self.os_confidence = os_confidence
        self.device_type = device_type
        self.classification_confidence = classification_confidence
        self.services = services or []
        self.interfaces = interfaces or []
        self.raw_data = raw_data or {}
        self.status = status

    def to_dict(self):
        return {
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "os_detection": self.os_detection,
            "os_confidence": self.os_confidence,
            "device_type": self.device_type,
            "classification_confidence": self.classification_confidence,
            "services": self.services,
            "interfaces": self.interfaces,
            "status": self.status,
        }


class DiscoveryProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def discover_host(self, target: str, **kwargs) -> Optional[DiscoveryResult]:
        pass

    @abstractmethod
    def discover_network(self, network_range: str, **kwargs) -> List[DiscoveryResult]:
        pass
