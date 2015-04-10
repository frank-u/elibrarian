from flask import Blueprint

api = Blueprint('api', __name__)

from . import authors


@api.route('/', methods=['GET'])
def index():
    return "REST API is not done yet!"
