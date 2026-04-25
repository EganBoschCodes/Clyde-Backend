import os

from home_assistant_lib.utils import load_env
from pydantic import BaseModel


class AuthConfig(BaseModel):
    model_config = {"frozen": True}

    google_client_id: str
    google_client_secret: str
    allowed_emails: frozenset[str]


def load_auth_config() -> AuthConfig:
    load_env()
    return AuthConfig(
        google_client_id=os.environ["GOOGLE_CLIENT_ID"],
        google_client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        allowed_emails=frozenset(
            email.strip().lower()
            for email in os.environ["ALLOWED_EMAILS"].split(",")
            if email.strip()
        ),
    )


AUTH_CONFIG = load_auth_config()
