from flask import Blueprint

webui = Blueprint('webui', __name__)

from . import views