from flask import current_app, jsonify, request, url_for
from . import api, make_json_response
from ..models import LiteraryWork


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
