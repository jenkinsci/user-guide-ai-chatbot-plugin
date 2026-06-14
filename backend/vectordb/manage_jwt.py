import jwt
import time
from manage_env import get_env
from dotenv import load_dotenv


def generate_token(payload: dict, secret_key: str) -> str:
    """
    Generate a jwt token with a specific payload. Use HS256 algorithm
    """
    return jwt.encode(payload=payload, key=secret_key, algorithm="HS256")


def generate_admin_token(secret_key: str):
    """
    Generate a jwt admin token for Qdrant. Expires after 1 hour.
    """
    token_admin = generate_token(
        {
            "exp": int(time.time()) + 3600,
            "access": "m",
        },
        secret_key=secret_key,
    )

    return token_admin
