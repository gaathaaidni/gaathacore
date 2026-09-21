import os

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is required to sign application tokens")
signer = URLSafeTimedSerializer(SECRET_KEY)

def generate_token(payload: dict):
    """Generates a signed token for a given payload."""
    return signer.dumps(payload)

def verify_token(token: str, max_age: int = 3600):
    """Verifies the token and returns the payload."""
    try:
        return signer.loads(token, max_age=max_age)
    except SignatureExpired:
        # Token is valid but expired
        return None
    except BadSignature:
        # Token is tampered with or invalid
        return None