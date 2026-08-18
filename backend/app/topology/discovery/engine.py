import logging
from typing import List, Optional, Dict, Any
from app.topology.discovery.base import TopologyDiscoveryProvider, TopologyEdgeResult
from app.topology.discovery.arp_neighbor import ARPNeighborProvider
from app.topology.discovery.subnet_adjacency import SubnetAdjacencyProvider
from app.topology.discovery.reachability import ReachabilityProvider
from app.topology.discovery.traceroute import TracerouteProvider

logger = logging.getLogger(__name__)


class TopologyDiscoveryEngine:

    def __init__(self):
        self._providers: List[TopologyDiscoveryProvider] = []

    def register_provider(self, provider: TopologyDiscoveryProvider):
        self._providers.append(provider)
        logger.info("Registered topology provider: %s (available=%s, edge_type=%s)",
                     provider.name, provider.is_available(), provider.edge_type)

    def get_available_providers(self) -> List[TopologyDiscoveryProvider]:
        return [p for p in self._providers if p.is_available()]

    def discover(self, device_ips: List[str],
                 provider_names: List[str] = None,
                 **kwargs) -> List[TopologyEdgeResult]:
        active = self._get_providers(provider_names)
        all_edges = []

        for provider in active:
            try:
                edges = provider.discover(device_ips, **kwargs)
                for edge in edges:
                    edge.metadata["provider"] = provider.name
                all_edges.extend(edges)
                logger.info("Provider %s found %d edges", provider.name, len(edges))
            except Exception as e:
                logger.error("Provider %s failed: %s", provider.name, str(e))

        deduped = self._deduplicate_edges(all_edges)
        logger.info("Topology discovery: %d raw edges -> %d deduplicated edges",
                     len(all_edges), len(deduped))
        return deduped

    def _get_providers(self, provider_names: List[str] = None) -> List[TopologyDiscoveryProvider]:
        available = self.get_available_providers()
        if provider_names:
            return [p for p in available if p.name in provider_names]
        return available

    def _deduplicate_edges(self, edges: List[TopologyEdgeResult]) -> List[TopologyEdgeResult]:
        edge_map: Dict[tuple, TopologyEdgeResult] = {}

        for edge in edges:
            pair = tuple(sorted([edge.source_ip, edge.destination_ip]))
            composite_key = (pair[0], pair[1], edge.edge_type)

            if composite_key in edge_map:
                existing = edge_map[composite_key]
                if edge.confidence > existing.confidence:
                    edge_map[composite_key] = edge
                elif edge.confidence == existing.confidence:
                    existing.evidence.update(edge.evidence)
            else:
                edge_map[composite_key] = edge

        return list(edge_map.values())

    def get_provider_status(self) -> Dict[str, bool]:
        return {p.name: p.is_available() for p in self._providers}
