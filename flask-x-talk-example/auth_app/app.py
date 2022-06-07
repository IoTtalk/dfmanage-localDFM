import datetime
import logging
import os

import pytz
from authlib.integrations.requests_client import OAuth2Session
from flask import (Blueprint, redirect, render_template, request, session,
                   url_for)
from flask_login import current_user, login_user, logout_user
from requests import exceptions as requests_exceptions

from ..const import UserGroup
from ..db import db
from ..db.models import AccessToken, Group, RefreshToken, User
from ..oauth2_client import oauth2_client

auth_app = Blueprint('auth', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


@auth_app.route('/auth', endpoint='auth_redirect_endpoint')
def auth_redirect():
    # url_for ref: https://flask.palletsprojects.com/en/1.1.x/api/#flask.url_for
    # Authlib doc: https://tinyurl.com/4fcyc7ap
    redirect_uri = url_for('auth.oauth2_redirect_endpoint', _external=True)

    # Redirect user-agent to the authorization endpoint
    return oauth2_client.iottalk.authorize_redirect(redirect_uri)


@auth_app.route('/auth/callback', endpoint='oauth2_redirect_endpoint')
def auth_callback():
    # Check whether the query parameters has one named `code`
    if not request.args.get('code'):
        if current_user.is_authenticated:
            # Redirect user-agent to the index page if a user is already authenticated
            return redirect(url_for('index'))

        redirect_uri = url_for('auth.oauth2_redirect_endpoint', _external=True)

        # Redirect user-agent to the authorization endpoint if a user is not authenticated
        return oauth2_client.iottalk.authorize_redirect(redirect_uri)

    try:
        # Exchange access token with an authorization code with token endpoint
        #
        # Ref: https://docs.authlib.org/en/stable/client/frameworks.html#id1
        token_response = oauth2_client.iottalk.authorize_access_token()
        # Parse the received ID token
        user_info = oauth2_client.iottalk.parse_id_token(token_response)
        print(token_response)
    except Exception:
        logger.exception('Get access token failed:')
        return render_template('auth_error.html', error_reason='Something is broken...')

    try:
        user_record = db.session.query(User).filter_by(sub=user_info.get('sub')).first()

        if not user_record:
            # Create a new user record if there does not exist an old one
            user_record = User(
                sub=user_info.get('sub'),
                username=user_info.get('preferred_username'),
                email=user_info.get('email')
            )
            user_record.group = db.session.query(Group)\
                .filter_by(name=UserGroup.Administrator).first() \
                if user_info['group'] == 'Administrator' \
                else db.session.query(Group).filter_by(name=UserGroup.User).first()
            db.session.add(user_record)
        else:
            user_record.username = \
                user_info.get('preferred_username') or user_record.username
            user_record.email = user_info.get('email') or user_record.email

        # Query the refresh token record
        refresh_token_record = \
            db.session.query(RefreshToken).filter_by(user_id=user_record.id).first()

        if not refresh_token_record:
            # Create a new refresh token record if there does not exist an old one
            refresh_token_record = RefreshToken(
                token=token_response.get('refresh_token'),
                user=user_record
            )
            db.session.add(refresh_token_record)
        elif token_response.get('refresh_token'):
            # If there is a refresh token in a token response, it indicates that
            # the old refresh token is expired, so we need to update the old refresh
            # token with a new one.
            refresh_token_record.token = token_response.get('refresh_token')

        # Create a new access token record
        access_token_record = AccessToken(
            token=token_response.get('access_token'),
            expires_at=(
                datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
                + datetime.timedelta(seconds=token_response.get('expires_in', 0))
            ),
            user=user_record,
            refresh_token=refresh_token_record
        )
        db.session.add(access_token_record)

        # Flush all the pending operations to the database so we can get the actual
        # id value.
        db.session.flush()

        # Store the access token ID to session
        session['access_token_id'] = access_token_record.id

        # Login user
        login_user(user_record)
        logger.info('User %r logs in', current_user.username)
    except Exception:
        db.session.rollback()
    else:
        db.session.commit()

    return redirect(url_for('index'))


@auth_app.route('/logout', methods=['POST', ], endpoint='logout_endpoint')
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))

    access_token_record = \
        (db.session
            .query(AccessToken)
            .filter_by(id=session.pop('access_token_id', 0))
            .first()
         )

    if not access_token_record:
        return redirect(url_for('index'))

    # Create an OAuth 2.0 client provided Authlib
    #
    # Ref: https://tinyurl.com/2rs2594h (OAuth2Session documentation)
    oauth2_client = OAuth2Session(
        client_id=os.getenv('XTALK_OAUTH2_CLIENT_ID'),
        client_secret=os.getenv('XTALK_OAUTH2_CLIENT_SECRET'),
        revocation_endpoint_auth_method='client_secret_basic'
    )

    try:
        # Revoke the access token
        response = oauth2_client.revoke_token(
            os.getenv('XTALK_OAUTH2_REVOCATION_ENDPOINT'),
            token=access_token_record.token,
            token_type_hint='access_token'
        )
        response.raise_for_status()
    except requests_exceptions.Timeout:
        logger.warning('Revoke an access token failed due to request timeout')
    except requests_exceptions.TooManyRedirects:
        logger.warning('Revoke an access token failed due to too many redirects')
    except (requests_exceptions.HTTPError, requests_exceptions.RequestException) as e:
        logger.warning('Revoke an access token failed, %s', e)
    finally:
        # Delete the access token record no matter whether access token revocation is
        # success or not
        db.session.delete(access_token_record)
        logger.info('User %r logs out', current_user.username)
        db.session.commit()

    logout_user()

    return redirect(url_for('index'))
