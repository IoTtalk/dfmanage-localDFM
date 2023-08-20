import logging
from pathlib import Path

from flask import Flask, render_template, url_for
from flask_login import LoginManager, current_user
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from libgravatar import Gravatar
from werkzeug.middleware.proxy_fix import ProxyFix

from account_app import account_app
from auth_app import auth_app
from db import db
from db.models import User
from oauth2_client import oauth2_client
import config

__all__ = [
    'create_app',
]

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


def create_app():
    config.read_config(str(BASE_DIR / '.env'))

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / 'templates')
    )
    app.register_blueprint(auth_app)
    app.register_blueprint(account_app)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    # Make WSGI use those X-Forwareded HTTP headers.
    # The following X-Forwareded HTTP headers must be by the front reverse proxy.
    #
    #     - `X-Forwarded-For`
    #     - `X-Forwarded-Proto`
    #     - `X-Forwarded-Host`
    #     - `X-Forwarded-Port`
    #
    # Ref: https://werkzeug.palletsprojects.com/en/1.0.x/middleware/proxy_fix/
    if bool(config.PROXY_USED):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    # Configure Flask-SQLAlchemy
    #
    # Ref: https://tinyurl.com/26dbers4
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/localdfm.db'.format(str(BASE_DIR))
    # Ref: https://tinyurl.com/9umn83fe
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Configure Flask-Session. We use database to store session.
    #
    # Ref: https://tinyurl.com/6sn9k699
    # Ref: https://flask-session.readthedocs.io/en/latest/
    app.config['SESSION_TYPE'] = 'sqlalchemy'
    app.config['SESSION_SQLALCHEMY'] = db
    Session(app)

    # Configure Flask-Login.
    #
    # Ref: https://flask-login.readthedocs.io/en/latest/
    login_manager = LoginManager()
    login_manager.init_app(app)
    oauth2_client.init_app(app)

    # Register OAuth2 Provider information
    #
    # Ref: https://tinyurl.com/j6cnk22s
    oauth2_client.register(
        name='nycu',
        client_id=config.OAUTH2_CLIENT_ID,
        client_secret=config.OAUTH2_CLIENT_SECRET,
        server_metadata_url=config.OIDC_DISCOVERY_ENDPOINT,
        client_kwargs={'scope': 'openid', }
    )

    # Initialize CSRFProtect app
    #
    # Ref: https://flask-wtf.readthedocs.io/en/stable/csrf.html
    CSRFProtect(app)

    with app.app_context():
        db.create_all()

    # Register custom context processor
    # Ref: https://flask.palletsprojects.com/en/1.1.x/templating/#context-processors
    @app.context_processor
    def custom_context_processor():
        def gravatar_url(email: str, **kwargs):
            return Gravatar(email).get_image(**kwargs)

        return {'gravatar_url': gravatar_url, }

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.filter_by(id=user_id).first()

    @app.before_first_request
    def init_database():
        db.create_all()

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            redirect_uri = url_for('auth.oauth2_redirect_endpoint', _external=True)
            return oauth2_client.iottalk.authorize_redirect(redirect_uri)
        return render_template('index.html')

    return app
