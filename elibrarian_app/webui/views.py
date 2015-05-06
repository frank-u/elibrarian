from flask import render_template
from . import webui


@webui.route('/', methods=['GET'])
def index():
    return render_template("ui_head.html")
