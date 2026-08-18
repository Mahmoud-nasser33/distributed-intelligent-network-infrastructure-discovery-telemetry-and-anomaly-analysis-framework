from flask import Blueprint, jsonify, request
from app.topology.service import TopologyService
from app.config.database import db

topology_bp = Blueprint("topology", __name__)


@topology_bp.route("/topology", methods=["GET"])
def get_topology():
    service = TopologyService()
    topology = service.get_topology()
    return jsonify(topology)


@topology_bp.route("/topology/build", methods=["POST"])
def build_topology():
    service = TopologyService()
    topology = service.build_topology()
    return jsonify(topology)


@topology_bp.route("/topology/discover", methods=["POST"])
def discover_topology():
    data = request.get_json() or {}
    device_ips = data.get("device_ips")
    providers = data.get("providers")

    service = TopologyService()
    topology = service.discover_topology(
        device_ips=device_ips,
        providers=providers,
    )
    return jsonify(topology)


@topology_bp.route("/topology/providers", methods=["GET"])
def topology_providers():
    service = TopologyService()
    status = service.get_provider_status()
    return jsonify({"providers": status})
