import os

from dotenv import load_dotenv

# A flag indicates if proxy is used, leave it empty if you do not use proxy.
# Fill in any value if you use proxy.
PROXY_USED = ""

# The Secret key must be unpredictable and it should not be exposed
SECRET_KEY = ""

# OAuth 2.0 Client ID
OAUTH2_CLIENT_ID = ""
# OAuth 2.0 Client Secret
OAUTH2_CLIENT_SECRET = ""
# OAuth 2.0 Redirect URI
OAUTH2_REDIRECT_URI = "http://localhost:5000/auth/callback"
# Base URL of Account System
ACCOUNT_HOST = "https://localhost:8000"
# OpenID Connect Discovery Endpoint
OIDC_DISCOVERY_ENDPOINT = ""
# OAuth 2.0 Authorization Endpoint
OAUTH2_AUTHORIZATION_ENDPOINT = ""
# OAuth 2.0 token endpoint
OAUTH2_TOKEN_ENDPOINT = ""
# OAuth 2.0 Revocation Endpoint
OAUTH2_REVOCATION_ENDPOINT = ""


def read_config(path: str):
    if not path or not os.path.isfile(path):
        raise OSError('ini file not found: {}'.format(path))

    mod = globals()

    load_dotenv(path)

    def set_(name, parser=str):
        if name not in mod:
            raise ('variable `%s` unknown', name)

        mod[name] = parser(os.getenv(name))

    set_('PROXY_USED')

    set_('SECRET_KEY')

    set_('OAUTH2_CLIENT_ID')
    set_('OAUTH2_CLIENT_SECRET')
    set_('OAUTH2_REDIRECT_URI')
    set_('ACCOUNT_HOST')
    set_('OIDC_DISCOVERY_ENDPOINT')
    set_('OAUTH2_AUTHORIZATION_ENDPOINT')
    set_('OAUTH2_TOKEN_ENDPOINT')
    set_('OAUTH2_REVOCATION_ENDPOINT')
