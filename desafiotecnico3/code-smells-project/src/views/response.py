from flask import jsonify


def to_response(result):
    payload, status = result
    return jsonify(payload), status
