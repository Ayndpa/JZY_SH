from flask import Blueprint, jsonify

test_bp = Blueprint('test', __name__)

@test_bp.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "success",
        "message": "Test endpoint is working!"
    })