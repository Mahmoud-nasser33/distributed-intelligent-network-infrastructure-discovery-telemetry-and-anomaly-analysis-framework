from flask import jsonify


class DINASError(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = {"error": self.message}
        if self.payload:
            rv["details"] = self.payload
        return rv


class NotFoundError(DINASError):
    status_code = 404


class ValidationError(DINASError):
    status_code = 400


class ConflictError(DINASError):
    status_code = 409


class AgentError(DINASError):
    status_code = 502


def register_error_handlers(app):
    @app.errorhandler(DINASError)
    def handle_dinas_error(error):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
