import logging
from typing import List, Optional, Dict, Any
from app.config.database import db
from app.models.topology import TopologyNode, TopologyEdge
from app.models.device import Device
from app.topology.discovery.engine import TopologyDiscoveryEngine
from app.topology.discovery.arp_neighbor import ARPNeighborProvider
from app.topology.discovery.subnet_adjacency import SubnetAdjacencyProvider
from app.topology.discovery.reachability import ReachabilityProvider
from app.topology.discovery.traceroute import TracerouteProvider

logger = logging.getLogger(__name__)


class TopologyService:

    def __init__(self):
        self._discovery_engine = None

    def _get_discovery_engine(self) -> TopologyDiscoveryEngine:
        if self._discovery_engine is None:
            self._discovery_engine = TopologyDiscoveryEngine()
            self._discovery_engine.register_provider(ARPNeighborProvider())
            self._discovery_engine.register_provider(SubnetAdjacencyProvider())
            self._discovery_engine.register_provider(ReachabilityProvider())
            self._discovery_engine.register_provider(TracerouteProvider())
        return self._discovery_engine

    def build_topology(self) -> Dict[str, Any]:
        devices = Device.query.filter(Device.status != "offline").all()
        nodes = []
        edges = []
        node_map = {}

        for device in devices:
            node = TopologyNode.query.filter_by(device_id=device.id).first()
            if not node:
                node = TopologyNode(
                    device_id=device.id,
                    label=device.hostname or device.ip_address,
                    node_type="device",
                )
                db.session.add(node)
                db.session.flush()
            node_map[device.id] = node.id
            nodes.append(node)

        for device in devices:
            for service in device.services.all():
                for other_device in devices:
                    if other_device.id == device.id:
                        continue
                    for other_service in other_device.services.all():
                        if (service.port == other_service.port and
                                service.service_name == other_service.service_name):
                            src_id = node_map.get(device.id)
                            dst_id = node_map.get(other_device.id)
                            if src_id and dst_id:
                                existing = TopologyEdge.query.filter_by(
                                    source_node_id=src_id,
                                    destination_node_id=dst_id,
                                    edge_type="service_match"
                                ).first()
                                if not existing:
                                    edge = TopologyEdge(
                                        source_node_id=src_id,
                                        destination_node_id=dst_id,
                                        edge_type="service_match",
                                        confidence=0.5,
                                        evidence={"shared_service": service.service_name, "port": service.port},
                                    )
                                    db.session.add(edge)
                                    edges.append(edge)

        db.session.commit()

        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }

    def discover_topology(self, device_ips: List[str] = None,
                          providers: List[str] = None) -> Dict[str, Any]:
        if device_ips is None:
            devices = Device.query.filter(Device.status != "offline").all()
            device_ips = [d.ip_address for d in devices]

        if len(device_ips) < 2:
            logger.info("Not enough devices for topology discovery (%d found)", len(device_ips))
            nodes = self._ensure_nodes_for_devices(device_ips)
            db.session.commit()
            return {
                "nodes": [n.to_dict() for n in nodes],
                "edges": [],
                "discovered_edges": 0,
                "providers_used": providers or ["all"],
            }

        engine = self._get_discovery_engine()
        edge_results = engine.discover(device_ips, provider_names=providers)

        nodes = self._ensure_nodes_for_devices(device_ips)
        node_ip_map = {}
        for node in nodes:
            if node.device_id:
                device = Device.query.get(node.device_id)
                if device:
                    node_ip_map[device.ip_address] = node.id

        new_edges = []
        for edge_result in edge_results:
            src_node_id = node_ip_map.get(edge_result.source_ip)
            dst_node_id = node_ip_map.get(edge_result.destination_ip)

            if not src_node_id or not dst_node_id:
                continue

            src_id, dst_id = sorted([src_node_id, dst_node_id])
            existing = TopologyEdge.query.filter_by(
                source_node_id=src_id,
                destination_node_id=dst_id,
                edge_type=edge_result.edge_type,
            ).first()

            if existing:
                existing.confidence = max(existing.confidence or 0, edge_result.confidence)
                existing.evidence = edge_result.evidence
                existing.metadata_json = edge_result.metadata
                existing.last_seen = db.func.now()
            else:
                edge = TopologyEdge(
                    source_node_id=src_id,
                    destination_node_id=dst_id,
                    edge_type=edge_result.edge_type,
                    confidence=edge_result.confidence,
                    evidence=edge_result.evidence,
                    metadata_json=edge_result.metadata,
                )
                db.session.add(edge)
                new_edges.append(edge)

        db.session.commit()

        all_edges = TopologyEdge.query.all()
        logger.info("Topology discovery complete: %d nodes, %d edges (%d new)",
                     len(nodes), len(all_edges), len(new_edges))

        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in all_edges],
            "discovered_edges": len(new_edges),
            "providers_used": providers or ["all"],
            "provider_status": engine.get_provider_status(),
        }

    def _ensure_nodes_for_devices(self, device_ips: List[str]) -> List[TopologyNode]:
        nodes = []
        for ip in device_ips:
            device = Device.query.filter_by(ip_address=ip).first()
            if not device:
                continue

            node = TopologyNode.query.filter_by(device_id=device.id).first()
            if not node:
                node = TopologyNode(
                    device_id=device.id,
                    label=device.hostname or device.ip_address,
                    node_type="device",
                )
                db.session.add(node)
                db.session.flush()
            else:
                node.last_seen = db.func.now()
            nodes.append(node)
        return nodes

    def get_topology(self) -> Dict[str, Any]:
        nodes = TopologyNode.query.all()
        edges = TopologyEdge.query.all()
        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }

    def get_provider_status(self) -> Dict[str, bool]:
        engine = self._get_discovery_engine()
        return engine.get_provider_status()
