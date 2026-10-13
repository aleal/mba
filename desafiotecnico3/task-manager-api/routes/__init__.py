from flask import jsonify


def respond(result):
    body, status = result
    return jsonify(body), status
