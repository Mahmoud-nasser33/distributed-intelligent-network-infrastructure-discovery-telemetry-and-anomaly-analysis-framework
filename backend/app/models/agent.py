import uuid
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Agent(db.Model):
    __tablename__ = "agents"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    name = db.Column(db.String(100), nullable=False)
    agent_type = db.Column(db.String(50), nullable=False, default="discovery")
    description = db.Column(db.Text, nullable=True)
    network_scope = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), default="registered", index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    version = db.Column(db.String(20), nullable=True)

    last_heartbeat = db.Column(db.DateTime, nullable=True)
    heartbeat_interval = db.Column(db.Integer, default=30)

    registered_at = db.Column(db.DateTime, default=_now)
    last_seen = db.Column(db.DateTime, default=_now)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    devices = db.relationship("Device", backref="agent", lazy="dynamic")
    observations = db.relationship("Observation", backref="agent", lazy="dynamic")
    scan_jobs = db.relationship("ScanJob", backref="agent", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type,
            "description": self.description,
            "network_scope": self.network_scope,
            "status": self.status,
            "ip_address": self.ip_address,
            "version": self.version,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "heartbeat_interval": self.heartbeat_interval,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
