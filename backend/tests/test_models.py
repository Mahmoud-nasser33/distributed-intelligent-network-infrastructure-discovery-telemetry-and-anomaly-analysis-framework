import pytest
from app.config.database import db
from app.models.device import Device, Service, NetworkInterface
from app.models.observation import Observation
from app.models.agent import Agent
from app.models.telemetry import Metric
from app.models.anomaly import Anomaly
from app.models.discovery import ScanJob
from app.models.topology import TopologyNode, TopologyEdge


def test_create_device(app):
    with app.app_context():
        device = Device(ip_address="192.168.1.1", hostname="test-host", status="online")
        db.session.add(device)
        db.session.commit()
        assert device.id is not None
        assert device.ip_address == "192.168.1.1"


def test_create_service(app):
    with app.app_context():
        device = Device(ip_address="192.168.1.2", status="online")
        db.session.add(device)
        db.session.flush()
        service = Service(device_id=device.id, port=22, protocol="tcp", service_name="ssh")
        db.session.add(service)
        db.session.commit()
        assert service.id is not None
        assert service.device_id == device.id


def test_create_observation(app):
    with app.app_context():
        obs = Observation(
            source="nmap", target_ip="192.168.1.1",
            observation_type="discovery",
            raw_data={"test": True},
        )
        db.session.add(obs)
        db.session.commit()
        assert obs.id is not None


def test_create_agent(app):
    with app.app_context():
        agent = Agent(name="test-agent", agent_type="discovery", status="active")
        db.session.add(agent)
        db.session.commit()
        assert agent.id is not None


def test_create_metric(app):
    with app.app_context():
        device = Device(ip_address="192.168.1.3", status="online")
        db.session.add(device)
        db.session.flush()
        metric = Metric(device_id=device.id, metric_type="latency", value=5.5, unit="ms")
        db.session.add(metric)
        db.session.commit()
        assert metric.id is not None


def test_create_anomaly(app):
    with app.app_context():
        device = Device(ip_address="192.168.1.4", status="online")
        db.session.add(device)
        db.session.flush()
        anomaly = Anomaly(
            device_id=device.id, detector="test",
            category="test", severity="low",
            explanation="Test anomaly",
        )
        db.session.add(anomaly)
        db.session.commit()
        assert anomaly.id is not None


def test_create_scan_job(app):
    with app.app_context():
        job = ScanJob(target="192.168.1.0/24", scan_type="network")
        db.session.add(job)
        db.session.commit()
        assert job.id is not None
        assert job.status == "pending"


def test_create_topology_node(app):
    with app.app_context():
        node = TopologyNode(label="test-node", node_type="device")
        db.session.add(node)
        db.session.commit()
        assert node.id is not None


def test_create_topology_edge(app):
    with app.app_context():
        n1 = TopologyNode(label="node-a")
        n2 = TopologyNode(label="node-b")
        db.session.add_all([n1, n2])
        db.session.flush()
        edge = TopologyEdge(
            source_node_id=n1.id, destination_node_id=n2.id,
            edge_type="connected", confidence=0.8,
        )
        db.session.add(edge)
        db.session.commit()
        assert edge.id is not None
