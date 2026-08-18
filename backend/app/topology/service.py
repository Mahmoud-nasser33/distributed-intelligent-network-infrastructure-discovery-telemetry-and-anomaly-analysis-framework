import logging
from typing import List, Optional, Dict, Any
from app.config.database import db
from app.models.topology import TopologyNode, TopologyEdge
from app.models.device import Device

logger = logging.getLogger(__name__)


class TopologyService:

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

    def get_topology(self) -> Dict[str, Any]:
        nodes = TopologyNode.query.all()
        edges = TopologyEdge.query.all()
        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }
