from flask import Blueprint, jsonify
from app.config.database import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy",
        "service": "dinas-api",
        "database": db_status,
        "version": "0.1.0",
    })
