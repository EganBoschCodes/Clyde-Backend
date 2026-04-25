from . import authorize, oauth_metadata, token  # noqa: F401 — registers HTTP routes
from .config import AUTH_CONFIG, AuthConfig
from .middleware import AuthMiddleware
