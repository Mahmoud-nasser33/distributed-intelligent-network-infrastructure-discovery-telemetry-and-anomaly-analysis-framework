from app.topology.discovery.base import TopologyDiscoveryProvider, TopologyEdgeResult
from app.topology.discovery.arp_neighbor import ARPNeighborProvider
from app.topology.discovery.subnet_adjacency import SubnetAdjacencyProvider
from app.topology.discovery.reachability import ReachabilityProvider
from app.topology.discovery.traceroute import TracerouteProvider
from app.topology.discovery.engine import TopologyDiscoveryEngine
from app.models.device import Device, NetworkInterface
from app.config.database import db


def test_arp_neighbor_provider_name():
    provider = ARPNeighborProvider()
    assert provider.name == "arp_neighbor"


def test_arp_neighbor_provider_edge_type():
    provider = ARPNeighborProvider()
    assert provider.edge_type == "arp_neighbor"


def test_arp_neighbor_provider_available():
    provider = ARPNeighborProvider()
    assert provider.is_available()


def test_arp_neighbor_provider_default_confidence():
    provider = ARPNeighborProvider()
    assert provider.default_confidence == 0.9


def test_subnet_adjacency_provider_name():
    provider = SubnetAdjacencyProvider()
    assert provider.name == "subnet_adjacency"


def test_subnet_adjacency_provider_edge_type():
    provider = SubnetAdjacencyProvider()
    assert provider.edge_type == "subnet_adjacent"


def test_subnet_adjacency_provider_available():
    provider = SubnetAdjacencyProvider()
    assert provider.is_available()


def test_reachability_provider_name():
    provider = ReachabilityProvider()
    assert provider.name == "reachability"


def test_reachability_provider_edge_type():
    provider = ReachabilityProvider()
    assert provider.edge_type == "reachable"


def test_reachability_provider_available():
    provider = ReachabilityProvider()
    assert provider.is_available()


def test_traceroute_provider_name():
    provider = TracerouteProvider()
    assert provider.name == "traceroute"


def test_traceroute_provider_edge_type():
    provider = TracerouteProvider()
    assert provider.edge_type == "traceroute_hop"


def test_traceroute_provider_available():
    provider = TracerouteProvider()
    assert provider.is_available()


def test_topology_edge_result_to_dict():
    edge = TopologyEdgeResult(
        source_ip="192.168.1.1",
        destination_ip="192.168.1.2",
        edge_type="arp_neighbor",
        confidence=0.9,
        evidence={"shared_mac": "AA:BB:CC:DD:EE:FF"},
        metadata={"provider": "arp_neighbor"},
    )
    d = edge.to_dict()
    assert d["source_ip"] == "192.168.1.1"
    assert d["destination_ip"] == "192.168.1.2"
    assert d["edge_type"] == "arp_neighbor"
    assert d["confidence"] == 0.9
    assert d["evidence"]["shared_mac"] == "AA:BB:CC:DD:EE:FF"


def test_engine_register_provider():
    engine = TopologyDiscoveryEngine()
    engine.register_provider(ARPNeighborProvider())
    engine.register_provider(SubnetAdjacencyProvider())
    available = engine.get_available_providers()
    assert len(available) >= 2


def test_engine_provider_status():
    engine = TopologyDiscoveryEngine()
    engine.register_provider(ARPNeighborProvider())
    engine.register_provider(ReachabilityProvider())
    status = engine.get_provider_status()
    assert "arp_neighbor" in status
    assert "reachability" in status
    assert status["arp_neighbor"] is True


def test_engine_deduplication():
    engine = TopologyDiscoveryEngine()
    edges = [
        TopologyEdgeResult("1.1.1.1", "2.2.2.2", "arp_neighbor", 0.9),
        TopologyEdgeResult("1.1.1.1", "2.2.2.2", "arp_neighbor", 0.7),
        TopologyEdgeResult("1.1.1.1", "2.2.2.2", "reachable", 0.8),
    ]
    deduped = engine._deduplicate_edges(edges)
    assert len(deduped) == 2
    arp_edge = [e for e in deduped if e.edge_type == "arp_neighbor"][0]
    assert arp_edge.confidence == 0.9


def test_engine_deduplication_merges_evidence():
    engine = TopologyDiscoveryEngine()
    edges = [
        TopologyEdgeResult("1.1.1.1", "2.2.2.2", "arp_neighbor", 0.9, evidence={"a": 1}),
        TopologyEdgeResult("1.1.1.1", "2.2.2.2", "arp_neighbor", 0.9, evidence={"b": 2}),
    ]
    deduped = engine._deduplicate_edges(edges)
    assert len(deduped) == 1
    assert deduped[0].evidence.get("a") == 1
    assert deduped[0].evidence.get("b") == 2


def test_subnet_adjacency_empty_devices(client):
    provider = SubnetAdjacencyProvider()
    edges = provider.discover([])
    assert edges == []


def test_topology_api_discover_endpoint(client):
    response = client.post("/api/topology/discover", json={})
    assert response.status_code == 200
    data = response.get_json()
    assert "nodes" in data
    assert "edges" in data
    assert "discovered_edges" in data
    assert "providers_used" in data


def test_topology_api_providers_endpoint(client):
    response = client.get("/api/topology/providers")
    assert response.status_code == 200
    data = response.get_json()
    assert "providers" in data
    assert "arp_neighbor" in data["providers"]
    assert "subnet_adjacency" in data["providers"]
    assert "reachability" in data["providers"]
    assert "traceroute" in data["providers"]


def test_topology_api_discover_with_providers(client):
    response = client.post("/api/topology/discover", json={
        "providers": ["arp_neighbor", "subnet_adjacency"],
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["providers_used"] == ["arp_neighbor", "subnet_adjacency"]


def test_subnet_calculate_subnet():
    provider = SubnetAdjacencyProvider()
    result = provider._calculate_subnet("192.168.1.100", "255.255.255.0")
    assert result == "192.168.1.0/24"


def test_subnet_calculate_subnet_class_a():
    provider = SubnetAdjacencyProvider()
    result = provider._calculate_subnet("10.0.5.100", "255.0.0.0")
    assert result == "10.0.0.0/8"


def test_subnet_calculate_subnet_invalid():
    provider = SubnetAdjacencyProvider()
    result = provider._calculate_subnet("not-an-ip", "bad-mask")
    assert result is None
