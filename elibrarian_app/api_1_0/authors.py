from flask import current_app, jsonify, request, url_for
from . import api, make_json_response
from .authentication import permission_required
from ..models import Author, Permission


@api.route('/authors', methods=['GET'])
@permission_required(Permission.VIEW_LIBRARY_ITEMS)
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
@permission_required(Permission.VIEW_LIBRARY_ITEMS)
def get_author(author_id):
    """Author details"""
    author = Author.query.get_or_404(author_id)
    return jsonify(author.to_json())
