from flask import current_app, jsonify, request, url_for
from . import api
from ..models import Author, LiteraryWork


def make_json_response(page, pages, per_page, href, href_parent,
                       items, next_page, prev):
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


@api.route('/authors', methods=['GET'])
def get_authors():
    """List of authors"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ELIBRARIAN_ITEMS_PER_PAGE']
    pagination = Author.query.paginate(page, per_page=per_page, error_out=False)
    authors_list = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_authors', page=page - 1, _external=True)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_authors', page=page + 1, _external=True)
    return make_json_response(page=page, pages=pagination.total,
                              per_page=per_page,
                              href=url_for('api.get_authors', _external=True),
                              href_parent=url_for('api.index', _external=True),
                              items=[author.to_json() for author in
                                     authors_list],
                              next_page=next_page,
                              prev=prev_page)


@api.route('/authors/<int:author_id>', methods=['GET'])
def get_author(author_id):
    """Author details"""
    author = Author.query.get_or_404(author_id)
    return jsonify(author.to_json())


@api.route('/literary-works', methods=['GET'])
def get_literary_works():
    """List of literary-works"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ELIBRARIAN_ITEMS_PER_PAGE']
    pagination = LiteraryWork.query.paginate(page, per_page=per_page,
                                             error_out=False)
    works_list = pagination.items
    prev_page = None
    if pagination.has_prev:
        prev_page = url_for('api.get_literary_works', page=page - 1,
                            _external=True)
    next_page = None
    if pagination.has_next:
        next_page = url_for('api.get_literary_works', page=page + 1,
                            _external=True)
    return make_json_response(page=page, pages=pagination.total,
                              per_page=per_page,
                              href=url_for('api.get_literary_works',
                                           _external=True),
                              href_parent=url_for('api.index', _external=True),
                              items=[work.to_json() for work in
                                     works_list],
                              next_page=next_page,
                              prev=prev_page)


@api.route('/literary-works/<int:work_id>', methods=['GET'])
def get_literary_work(work_id):
    """Literary work"""
    work = LiteraryWork.query.get_or_404(work_id)
    return jsonify(work.to_json())
