import uuid
import enum
from datetime import datetime, timezone
from app.config.database import db


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class MetricType(enum.Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    PACKET_LOSS = "packet_loss"
    RESPONSE_TIME = "response_time"
    TRAFFIC_VOLUME = "traffic_volume"
    PACKET_RATE = "packet_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    UPTIME = "uptime"
    INTERFACE_STATE = "interface_state"


class Metric(db.Model):
    __tablename__ = "metrics"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    device_id = db.Column(db.String(36), db.ForeignKey("devices.id"), nullable=False, index=True)
    metric_type = db.Column(db.String(30), nullable=False, index=True)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=True)
    source = db.Column(db.String(50), nullable=True)
    agent_id = db.Column(db.String(36), db.ForeignKey("agents.id"), nullable=True)

    tags = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=_now, index=True)
    created_at = db.Column(db.DateTime, default=_now)

    __table_args__ = (
        db.Index("idx_metric_device_type_time", "device_id", "metric_type", "timestamp"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "agent_id": self.agent_id,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
