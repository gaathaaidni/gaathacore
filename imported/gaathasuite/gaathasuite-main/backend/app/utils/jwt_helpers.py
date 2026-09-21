import base64
import json
import hmac
import hashlib
import time
from typing import Any, Dict
from fastapi import HTTPException, status
from app.config import Config


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _base64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def _sign(msg: bytes) -> str:
    secret = Config.SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret, msg, hashlib.sha256).digest()
    return _base64url_encode(signature)


def create_access_token(payload: Dict[str, Any], expires_minutes: int | None = None) -> str:
    header = {"alg": Config.JWT_ALGORITHM, "typ": "JWT"}
    now = int(time.time())
    payload = payload.copy()
    payload.setdefault("iat", now)
    payload.setdefault("exp", now + ((expires_minutes or Config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES) * 60))

    encoded_header = _base64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    encoded_payload = _base64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signed = _sign(f"{encoded_header}.{encoded_payload}".encode("utf-8"))
    return f"{encoded_header}.{encoded_payload}.{signed}"


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split('.')
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed authentication token.")

    expected_sig = _sign(f"{header_b64}.{payload_b64}".encode("utf-8"))
    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature.")

    try:
        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to decode token payload.")

    if "exp" not in payload or int(payload["exp"]) < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")

    return payload
