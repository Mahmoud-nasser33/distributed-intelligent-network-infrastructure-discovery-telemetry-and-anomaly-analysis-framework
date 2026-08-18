from flask import Blueprint, jsonify
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
