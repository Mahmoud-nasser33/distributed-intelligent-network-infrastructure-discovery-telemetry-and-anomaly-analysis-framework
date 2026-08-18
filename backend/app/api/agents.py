from flask import Blueprint, jsonify, request
from app.repositories.agent_repo import AgentRepository
from app.utils.errors import NotFoundError, ValidationError

agents_bp = Blueprint("agents", __name__)


@agents_bp.route("/agents", methods=["GET"])
def list_agents():
    status = request.args.get("status")
    agents = AgentRepository.find_all(status=status)
    return jsonify({
        "agents": [a.to_dict() for a in agents],
        "count": len(agents),
    })


@agents_bp.route("/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    agent = AgentRepository.find_by_id(agent_id)
    if not agent:
        raise NotFoundError(f"Agent {agent_id} not found")
    return jsonify({"agent": agent.to_dict()})


@agents_bp.route("/agents/register", methods=["POST"])
def register_agent():
    data = request.get_json()
    if not data or not data.get("name"):
        raise ValidationError("Agent name is required")

    agent = AgentRepository.register(
        name=data["name"],
        agent_type=data.get("agent_type", "discovery"),
        data=data,
    )
    return jsonify({"agent": agent.to_dict()}), 201


@agents_bp.route("/agents/<agent_id>/heartbeat", methods=["POST"])
def agent_heartbeat(agent_id):
    data = request.get_json() or {}
    agent = AgentRepository.heartbeat(agent_id, data)
    if not agent:
        raise NotFoundError(f"Agent {agent_id} not found")
    return jsonify({"agent": agent.to_dict()})
