from functools import wraps

from flask import abort, redirect, request, url_for
from flask_login import current_user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('index', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def allows_to(groups=[]):
    if groups is None:
        groups = []

    def decorator(func):
        def check_group(*args, **kwargs):
            for group in groups:
                if current_user.group.name == group:
                    return func(*args, **kwargs)
            abort(403)
        check_group.__name__ = func.__name__
        return check_group
    return decorator
