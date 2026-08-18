def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_api_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "dinas-api"
    assert data["database"] == "connected"


def test_list_devices_empty(client):
    response = client.get("/api/devices")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 0
    assert data["devices"] == []


def test_list_agents_empty(client):
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 0


def test_register_agent(client):
    response = client.post("/api/agents/register", json={
        "name": "test-agent",
        "agent_type": "discovery",
        "network_scope": "192.168.1.0/24",
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["agent"]["name"] == "test-agent"
    assert data["agent"]["status"] == "active"


def test_register_agent_missing_name(client):
    response = client.post("/api/agents/register", json={})
    assert response.status_code == 400


def test_agent_heartbeat(client):
    reg = client.post("/api/agents/register", json={
        "name": "heartbeat-test",
        "agent_type": "discovery",
    })
    agent_id = reg.get_json()["agent"]["id"]

    response = client.post(f"/api/agents/{agent_id}/heartbeat", json={
        "ip_address": "10.0.0.1",
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["agent"]["status"] == "active"


def test_list_anomalies_empty(client):
    response = client.get("/api/anomalies")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 0


def test_create_discovery_job(client):
    response = client.post("/api/discovery/jobs", json={
        "target": "127.0.0.1",
        "scan_type": "host",
    })
    assert response.status_code in (200, 202)
    data = response.get_json()
    assert "job" in data


def test_create_discovery_job_missing_target(client):
    response = client.post("/api/discovery/jobs", json={})
    assert response.status_code == 400


def test_list_discovery_jobs(client):
    response = client.get("/api/discovery/jobs")
    assert response.status_code == 200
    data = response.get_json()
    assert "jobs" in data


def test_device_stats(client):
    response = client.get("/api/devices/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total"] == 0


def test_anomaly_stats(client):
    response = client.get("/api/anomalies/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert data["open_count"] == 0


def test_topology_empty(client):
    response = client.get("/api/topology")
    assert response.status_code == 200
    data = response.get_json()
    assert data["nodes"] == []
    assert data["edges"] == []


def test_nonexistent_device(client):
    response = client.get("/api/devices/nonexistent-id")
    assert response.status_code == 404
