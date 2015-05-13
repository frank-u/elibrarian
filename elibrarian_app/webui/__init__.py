from flask import Blueprint

webui = Blueprint('webui', __name__,
                  template_folder='templates',
                  static_folder='static')

from . import views
