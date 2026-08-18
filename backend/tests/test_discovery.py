from app.discovery.nmap_provider import NmapDiscoveryProvider
from app.discovery.icmp_provider import ICMPDiscoveryProvider
from app.discovery.arp_provider import ARPDiscoveryProvider
from app.discovery.engine import CompositeDiscoveryEngine


def test_nmap_provider_name():
    provider = NmapDiscoveryProvider()
    assert provider.name == "nmap"


def test_icmp_provider_available():
    provider = ICMPDiscoveryProvider()
    assert provider.is_available()


def test_arp_provider_name():
    provider = ARPDiscoveryProvider()
    assert provider.name == "arp"


def test_composite_engine_register():
    engine = CompositeDiscoveryEngine()
    engine.register_provider(ICMPDiscoveryProvider())
    engine.register_provider(ARPDiscoveryProvider())
    available = engine.get_available_providers()
    assert len(available) >= 2


def test_composite_engine_provider_names():
    engine = CompositeDiscoveryEngine()
    engine.register_provider(NmapDiscoveryProvider())
    engine.register_provider(ICMPDiscoveryProvider())
    names = [p.name for p in engine._providers]
    assert "nmap" in names
    assert "icmp" in names
