"""
    Helper functions to support authentication on API:
    - verifying passwords
    - generating authorization token
    - checking permissions
"""
from flask import current_app, g, jsonify
from flask_httpauth import HTTPBasicAuth
from functools import wraps
from . import api
from .errors import unauthorized, forbidden
from ..models import AnonymousUser, AuthUser

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    """Verifying password or token in request's authorization field"""
    if email_or_token == "":
        g.current_user = AnonymousUser()
        return True
    if password == "":
        g.current_user = AuthUser.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = AuthUser.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    """Handler for authentication errors"""
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    """
        We check, that user is confirmed at every request to API endpoint.
        We pass here for anonymous user. It will be checked when checking
    permissions.
    """
    if not g.current_user.is_anonymous() and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/token')
def get_token():
    """
    :return: authorization token in JSON format for current logged user with
    default expiration time in seconds.
    """
    if g.current_user.is_anonymous() or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({
        'token': g.current_user.generate_auth_token(
            expiration=current_app.config['ELIBRARIAN_TOKEN_EXPIRATION_TIME']),
        'expiration': current_app.config['ELIBRARIAN_TOKEN_EXPIRATION_TIME']
    })


def permission_required(permission):
    """Decorator for checking permissions on protected API endpoints"""

    def decorator(func):
        """actual decorator function"""

        @wraps(func)
        def decorated_function(*args, **kwargs):
            """
                Check that current user have all permissions given in
            permission variable
            """
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return func(*args, **kwargs)

        return decorated_function

    return decorator
