from . import webui


@webui.route('/', methods=['GET'])
def index():
    return "UI is not implemented yet!"
