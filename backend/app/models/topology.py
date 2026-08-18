import uuid
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class TopologyNode(db.Model):
    __tablename__ = "topology_nodes"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id"), nullable=True, index=True)
    label = db.Column(db.String(255), nullable=True)
    node_type = db.Column(db.String(50), default="device")
    x_position = db.Column(db.Float, nullable=True)
    y_position = db.Column(db.Float, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)

    first_seen = db.Column(db.DateTime, default=_now)
    last_seen = db.Column(db.DateTime, default=_now)
    created_at = db.Column(db.DateTime, default=_now)

    out_edges = db.relationship("TopologyEdge", foreign_keys="TopologyEdge.source_node_id", backref="source_node", lazy="dynamic")
    in_edges = db.relationship("TopologyEdge", foreign_keys="TopologyEdge.destination_node_id", backref="destination_node", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "label": self.label,
            "node_type": self.node_type,
            "x_position": self.x_position,
            "y_position": self.y_position,
            "metadata": self.metadata_json,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class TopologyEdge(db.Model):
    __tablename__ = "topology_edges"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    source_node_id = db.Column(db.String(36), db.ForeignKey("topology_nodes.id"), nullable=False, index=True)
    destination_node_id = db.Column(db.String(36), db.ForeignKey("topology_nodes.id"), nullable=False, index=True)

    edge_type = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    evidence = db.Column(db.JSON, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)

    first_seen = db.Column(db.DateTime, default=_now)
    last_seen = db.Column(db.DateTime, default=_now)
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "edge_type": self.edge_type,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata_json,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
