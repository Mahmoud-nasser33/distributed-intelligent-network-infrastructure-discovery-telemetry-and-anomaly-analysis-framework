from app.services.classifier import DeviceClassifier


def test_classify_router_by_vendor():
    classifier = DeviceClassifier()
    result = classifier.classify(vendor="Cisco Systems")
    assert result["device_type"] == "router"
    assert result["confidence"] > 0


def test_classify_server_by_hostname():
    classifier = DeviceClassifier()
    result = classifier.classify(hostname="web-server-01")
    assert result["device_type"] == "server"
    assert result["confidence"] > 0


def test_classify_printer_by_port():
    classifier = DeviceClassifier()
    result = classifier.classify(services=[{"port": 9100, "service_name": "printer"}])
    assert result["device_type"] == "printer"
    assert result["confidence"] > 0


def test_classify_firewall_by_hostname():
    classifier = DeviceClassifier()
    result = classifier.classify(hostname="fw-main")
    assert result["device_type"] == "firewall"
    assert result["confidence"] > 0


def test_classify_unknown():
    classifier = DeviceClassifier()
    result = classifier.classify()
    assert result["device_type"] == "unknown"
    assert result["confidence"] == 0.0


def test_classify_ap_by_vendor():
    classifier = DeviceClassifier()
    result = classifier.classify(vendor="Ubiquiti Networks")
    assert result["device_type"] == "access_point"


def test_classify_switch_by_vendor():
    classifier = DeviceClassifier()
    result = classifier.classify(vendor="Netgear Inc")
    assert result["device_type"] == "switch"
