from datetime import datetime, timedelta

from app.config.database import db
from app.models.device import Device
from app.repositories.agent_repo import AgentRepository


def _register_agent(client, name="telemetry-agent"):
    response = client.post("/api/agents/register", json={
        "name": name,
        "agent_type": "telemetry",
        "network_scope": "192.168.1.0/24",
    })
    assert response.status_code == 201
    return response.get_json()["agent"]


def _telemetry_payload(ip="192.168.1.50", status="online"):
    return {
        "results": [{
            "ip_address": ip,
            "status": status,
            "metrics": [
                {"metric_type": "latency", "value": 12.5, "unit": "ms"},
                {"metric_type": "availability", "value": 1.0 if status == "online" else 0.0,
                 "unit": "ratio"},
            ],
        }],
    }


def test_agent_config_endpoint(client):
    agent = _register_agent(client)

    response = client.get(f"/api/agents/{agent['id']}/config")
    assert response.status_code == 200
    data = response.get_json()
    assert data["agent_id"] == agent["id"]
    assert data["name"] == "telemetry-agent"
    assert data["network_scope"] == "192.168.1.0/24"
    assert isinstance(data["heartbeat_interval"], int)
    assert isinstance(data["collect_interval"], int)


def test_agent_config_unknown_agent(client):
    response = client.get("/api/agents/nope/config")
    assert response.status_code == 404


def test_submit_telemetry_creates_device_and_metrics(client, db):
    agent = _register_agent(client)

    response = client.post(
        f"/api/agents/{agent['id']}/telemetry",
        json=_telemetry_payload(),
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["stored"] == 2
    assert data["skipped"] == 0
    assert data["devices"] == 1

    device = Device.query.filter_by(ip_address="192.168.1.50").first()
    assert device is not None
    assert device.status == "online"
    assert device.agent_id == agent["id"]

    from app.repositories.metric_repo import MetricRepository
    recorded = MetricRepository.find_by_device(device.id)
    assert len(recorded) == 2
    types = {m.metric_type for m in recorded}
    assert types == {"latency", "availability"}
    assert all(m.source == "agent" for m in recorded)
    assert all(m.agent_id == agent["id"] for m in recorded)


def test_submit_telemetry_reuses_existing_device(client, db):
    agent = _register_agent(client)
    device = Device(ip_address="192.168.1.60", hostname="printer",
                    status="unknown")
    db.session.add(device)
    db.session.commit()

    response = client.post(
        f"/api/agents/{agent['id']}/telemetry",
        json=_telemetry_payload(ip="192.168.1.60"),
    )
    assert response.status_code == 200

    same_ip = Device.query.filter_by(ip_address="192.168.1.60").all()
    assert len(same_ip) == 1
    assert same_ip[0].status == "online"


def test_submit_telemetry_marks_device_offline(client, db):
    agent = _register_agent(client)

    response = client.post(
        f"/api/agents/{agent['id']}/telemetry",
        json=_telemetry_payload(ip="192.168.1.70", status="offline"),
    )
    assert response.status_code == 200

    device = Device.query.filter_by(ip_address="192.168.1.70").first()
    assert device.status == "offline"


def test_submit_telemetry_updates_heartbeat(client, db):
    agent = _register_agent(client)
    old = datetime.utcnow() - timedelta(minutes=10)
    AgentRepository.find_by_id(agent["id"]).last_heartbeat = old
    db.session.commit()

    response = client.post(
        f"/api/agents/{agent['id']}/telemetry",
        json=_telemetry_payload(),
    )
    assert response.status_code == 200

    refreshed = AgentRepository.find_by_id(agent["id"])
    assert refreshed.last_heartbeat > old


def test_submit_telemetry_missing_results(client):
    agent = _register_agent(client)

    response = client.post(f"/api/agents/{agent['id']}/telemetry", json={})
    assert response.status_code == 400

    response = client.post(f"/api/agents/{agent['id']}/telemetry",
                           json={"results": "not-a-list"})
    assert response.status_code == 400


def test_submit_telemetry_unknown_agent(client):
    response = client.post("/api/agents/nope/telemetry",
                           json={"results": []})
    assert response.status_code == 404


def test_submit_telemetry_skips_invalid_metrics(client, db):
    agent = _register_agent(client)

    payload = {
        "results": [{
            "ip_address": "192.168.1.80",
            "status": "online",
            "metrics": [
                {"metric_type": "latency", "value": 5.0, "unit": "ms"},
                {"metric_type": "bogus_metric", "value": 1.0},
                {"metric_type": "latency", "value": "not-a-number"},
                "not-even-a-dict",
            ],
        }],
    }
    response = client.post(f"/api/agents/{agent['id']}/telemetry", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["stored"] == 1
    assert data["skipped"] == 3


def test_stale_agents_marked_offline(app, db):
    agent = AgentRepository.register(
        name="sleepy-agent",
        agent_type="telemetry",
        data={},
    )
    cutoff_backdate = datetime.utcnow() - timedelta(seconds=300)
    agent.last_heartbeat = cutoff_backdate
    db.session.commit()

    stale = AgentRepository.find_stale(timeout_seconds=90)
    assert [a.id for a in stale] == [agent.id]

    AgentRepository.mark_stale([agent.id])
    refreshed = AgentRepository.find_by_id(agent.id)
    assert refreshed.status == "stale"
