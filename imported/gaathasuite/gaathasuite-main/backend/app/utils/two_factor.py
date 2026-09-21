import pyotp
import qrcode
import io
import base64

def generate_totp_secret():
    """Generates a new random base32 OTP secret."""
    return pyotp.random_base32()

def get_totp_uri(secret, user_email, issuer_name="Gaatha Suite"):
    """Generates a provisioning URI for QR code scanning."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name=issuer_name)

def verify_totp_code(secret, code):
    """Verifies a 6-digit TOTP code against the secret."""
    totp = pyotp.totp.TOTP(secret)
    return totp.verify(code)

def generate_qr_base64(uri):
    """Generates a base64 encoded QR code image string."""
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()