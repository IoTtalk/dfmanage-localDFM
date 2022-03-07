import logging

from flask import Blueprint, abort, jsonify, render_template
from flask_login import current_user

from ..const import UserGroup
from ..db import db
from ..db.models import Group, User
from .utils import allows_to, login_required

account_app = Blueprint('account', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


@account_app.route('/account', strict_slashes=False)
def index():
    """
    A placeholder for url_for
    """
    abort(403)


@account_app.route('/account/user_list', methods=['GET', ],
                   strict_slashes=False, endpoint="user_list")
@login_required
@allows_to([UserGroup.Administrator])
def user_list():
    return render_template('user_list.html',
                           users=User.query.all(),
                           groups=Group.query.all())


@account_app.route('/account/user/<int:uid>', methods=['DELETE'], strict_slashes=False)
@login_required
@allows_to([UserGroup.Administrator])
def delete(uid):
    target = User.query.get(uid)
    if target is None:
        return 'User id {} not found'.format(uid), 404
    if target.is_administrator:
        return 'Cannot delete Administrator', 403

    db.session.delete(target)
    db.session.commit()
    return jsonify({'state': 'ok'})


@account_app.route('/account/user/<int:uid>/chgrp/<int:gid>', methods=['POST'],
                   strict_slashes=False)
@login_required
@allows_to([UserGroup.Administrator])
def chgrp(uid, gid):
    target = User.query.get(uid)
    if target is None:
        return 'User id {} not found'.format(uid), 404
    if target.id == current_user.id:
        return 'Cannot change your own group', 403

    g = Group.query.get(gid)
    if g is None:
        return 'Group id {} not found'.format(gid), 404

    target.group = g
    db.session.commit()
    return jsonify({'state': 'ok'})
