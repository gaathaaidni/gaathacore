import base64
import hashlib
import os
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring

WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
WSU = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
PASSWORD_DIGEST = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-UsernameToken-Profile-1.1#PasswordDigest"
PASSWORD_TEXT = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-UsernameToken-Profile-1.1#PasswordText"


def utc_created() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def password_digest(nonce: bytes, created: str, password: str) -> str:
    return base64.b64encode(hashlib.sha1(nonce + created.encode() + password.encode()).digest()).decode()


def username_token(username: str, password: str, digest: bool = True) -> bytes:
    nonce = os.urandom(16)
    created = utc_created()
    security = Element(f"{{{WSSE}}}Security")
    token = SubElement(security, f"{{{WSSE}}}UsernameToken")
    SubElement(token, f"{{{WSSE}}}Username").text = username
    password_element = SubElement(token, f"{{{WSSE}}}Password")
    password_element.set("Type", PASSWORD_DIGEST if digest else PASSWORD_TEXT)
    password_element.text = password_digest(nonce, created, password) if digest else password
    nonce_element = SubElement(token, f"{{{WSSE}}}Nonce")
    nonce_element.set("EncodingType", "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary")
    nonce_element.text = base64.b64encode(nonce).decode()
    SubElement(token, f"{{{WSU}}}Created").text = created
    return tostring(security, encoding="utf-8")
