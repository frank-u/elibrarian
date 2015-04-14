from collections import defaultdict
from flask import jsonify

error_types = defaultdict(lambda: "unknown error")
error_types[400] = "bad request"
error_types[401] = "unauthorized"
error_types[403] = "forbidden"


def error(code, message):
    response = jsonify({'error': error_types[code], 'message': message})
    response.status_code = code
    return response


def bad_request(message):
    return error(400, message)


def unauthorized(message):
    return error(401, message)


def forbidden(message):
    return error(403, message)
