"""
    Root entry for api and helper functions
"""
from flask import Blueprint, jsonify

api = Blueprint('api', __name__)


def make_json_response(page, pages, per_page, href, href_parent,
                       items, next_page, prev):
    """
        Default response skeleton
    :param page:
    :param pages:
    :param per_page:
    :param href:
    :param href_parent:
    :param items:
    :param next_page:
    :param prev:
    :return:
    """
    # TODO: Print in response current page and total pages in result set
    json_response_body = {
        "_meta": {
            "page": page,
            "max_results": per_page,
            "total": pages
        },
        "_items": items,
        "_links": {
            "self": {
                "href": href,
                "title": "Authors"
            },
            "parent": {
                "href": href_parent,
                "title": "API root"
            }
        }
    }
    if items:
        json_response_body['_items'] = items
    if prev:
        json_response_body['_links']['prev'] = prev
    if next_page:
        json_response_body['_links']['next'] = next_page
    return jsonify(json_response_body)


@api.route('/', methods=['GET'])
def index():
    """
        Root entry for api endpoint
    :return:
    """
    # TODO: Present to user links for all api sections
    return "REST API is not done yet!"


from . import authentication, authors, errors, literary_works
