from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class TopologyEdgeResult:
    source_ip: str
    destination_ip: str
    edge_type: str
    confidence: float
    evidence: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "edge_type": self.edge_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }


class TopologyDiscoveryProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def edge_type(self) -> str:
        pass

    @property
    @abstractmethod
    def default_confidence(self) -> float:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def discover(self, device_ips: List[str], **kwargs) -> List[TopologyEdgeResult]:
        pass
