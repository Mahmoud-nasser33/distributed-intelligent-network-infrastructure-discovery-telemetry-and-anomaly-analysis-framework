import uuid
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    mac_address = db.Column(db.String(17), nullable=True, index=True)
    hostname = db.Column(db.String(255), nullable=True)
    vendor = db.Column(db.String(255), nullable=True)
    device_type = db.Column(db.String(50), nullable=True, index=True)
    os_detection = db.Column(db.String(255), nullable=True)
    os_confidence = db.Column(db.Float, nullable=True)
    classification_confidence = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default="unknown", index=True)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True)

    first_seen = db.Column(db.DateTime, default=_now)
    last_seen = db.Column(db.DateTime, default=_now, onupdate=_now)

    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    interfaces = db.relationship("NetworkInterface", backref="device", lazy="dynamic", cascade="all, delete-orphan")
    services = db.relationship("Service", backref="device", lazy="dynamic", cascade="all, delete-orphan")
    metrics = db.relationship("Metric", backref="device", lazy="dynamic", cascade="all, delete-orphan")
    anomalies = db.relationship("Anomaly", backref="device", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint("ip_address", "agent_id", name="uq_device_ip_agent"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "os_detection": self.os_detection,
            "os_confidence": self.os_confidence,
            "classification_confidence": self.classification_confidence,
            "status": self.status,
            "agent_id": self.agent_id,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "services": [s.to_dict() for s in self.services.all()],
            "interfaces": [i.to_dict() for i in self.interfaces.all()],
        }


class NetworkInterface(db.Model):
    __tablename__ = "network_interfaces"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id"), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=True)
    mac_address = db.Column(db.String(17), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    subnet_mask = db.Column(db.String(15), nullable=True)
    interface_type = db.Column(db.String(50), nullable=True)
    speed = db.Column(db.Integer, nullable=True)
    is_up = db.Column(db.Boolean, default=False)
    mtu = db.Column(db.Integer, nullable=True)
    first_seen = db.Column(db.DateTime, default=_now)
    last_seen = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "name": self.name,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "subnet_mask": self.subnet_mask,
            "interface_type": self.interface_type,
            "speed": self.speed,
            "is_up": self.is_up,
            "mtu": self.mtu,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id"), nullable=False, index=True)
    port = db.Column(db.Integer, nullable=False)
    protocol = db.Column(db.String(10), default="tcp")
    service_name = db.Column(db.String(100), nullable=True)
    version = db.Column(db.String(255), nullable=True)
    banner = db.Column(db.Text, nullable=True)
    state = db.Column(db.String(20), default="open")
    confidence = db.Column(db.Float, nullable=True)
    first_seen = db.Column(db.DateTime, default=_now)
    last_seen = db.Column(db.DateTime, default=_now)

    __table_args__ = (
        db.UniqueConstraint("device_id", "port", "protocol", name="uq_service_device_port"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "port": self.port,
            "protocol": self.protocol,
            "service_name": self.service_name,
            "version": self.version,
            "banner": self.banner,
            "state": self.state,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }
