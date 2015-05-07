from flask import current_app, g, jsonify, request, url_for
from . import api, make_json_response
from .authentication import permission_required
from ..models import LiteraryWork, Permission


@api.route('/literary-works', methods=['GET'])
@permission_required(Permission.VIEW_LIBRARY_ITEMS)
def get_literary_works():
    """List of literary-works"""
    # TODO: Check pagination bounds
    page = request.args.get('page', 1, type=int)
    lang = request.args.get('lang', g.current_user.preferred_lang, type=str)
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
                              items=[
                                  work.to_json(lang=lang)
                                  for work
                                  in works_list
                              ],
                              next_page=next_page,
                              prev=prev_page)


@api.route('/literary-works/<int:work_id>', methods=['GET'])
@permission_required(Permission.VIEW_LIBRARY_ITEMS)
def get_literary_work(work_id):
    """Literary work"""
    lang = request.args.get('lang', g.current_user.preferred_lang, type=str)
    work = LiteraryWork.query.get_or_404(work_id)
    return jsonify(work.to_json(lang=lang, verbose=True))
