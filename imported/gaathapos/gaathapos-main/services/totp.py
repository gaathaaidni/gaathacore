"""Two-Factor Authentication (TOTP) Service using Time-based One-Time Passwords"""
import pyotp
import qrcode
from io import BytesIO
import base64
import json
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string


def generate_totp_secret(username, issuer='Gaatha POS'):
    """Generate a new TOTP secret for a user.
    
    Args:
        username: The user's username
        issuer: Organization/app name (shown in authenticator apps)
    
    Returns:
        dict with 'secret', 'qr_code_data_uri', and 'backup_codes'
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=username,
        issuer_name=issuer
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to data URI
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    qr_code_data_uri = f"data:image/png;base64,{img_str}"
    
    # Generate backup codes (10 codes, 8 chars each)
    backup_codes = [generate_backup_code() for _ in range(10)]
    hashed_codes = [generate_password_hash(code) for code in backup_codes]
    
    return {
        'secret': secret,
        'qr_code_data_uri': qr_code_data_uri,
        'backup_codes': backup_codes,  # Return plaintext to user ONCE
        'backup_codes_hashed': json.dumps(hashed_codes)  # Store hashed version in DB
    }


def generate_backup_code():
    """Generate a single backup code (8 uppercase alphanumeric characters)"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


def verify_totp_token(secret, token, valid_window=1):
    """Verify a TOTP token.
    
    Args:
        secret: The TOTP secret (base32)
        token: The 6-digit token from the authenticator app
        valid_window: Number of time windows to check (30-sec windows)
    
    Returns:
        bool: True if token is valid
    """
    if not secret or not token:
        return False
    
    try:
        totp = pyotp.TOTP(secret)
        # Check current time window and adjacent windows for clock skew
        return totp.verify(token, valid_window=valid_window)
    except Exception:
        return False


def use_backup_code(backup_codes_json, code):
    """Consume a backup code.
    
    Args:
        backup_codes_json: JSON array of hashed backup codes stored in DB
        code: The plaintext backup code provided by user
    
    Returns:
        dict with 'valid' (bool), 'codes_remaining' (int), 'remaining_codes_json' (str or None)
    """
    if not backup_codes_json or not code:
        return {'valid': False, 'codes_remaining': 0, 'remaining_codes_json': None}
    
    try:
        hashed_codes = json.loads(backup_codes_json)
    except (json.JSONDecodeError, TypeError):
        return {'valid': False, 'codes_remaining': 0, 'remaining_codes_json': None}
    
    # Find matching code
    matched_idx = None
    for idx, hashed_code in enumerate(hashed_codes):
        if check_password_hash(hashed_code, code):
            matched_idx = idx
            break
    
    if matched_idx is None:
        return {'valid': False, 'codes_remaining': len(hashed_codes), 'remaining_codes_json': backup_codes_json}
    
    # Remove used code
    remaining_codes = hashed_codes[:matched_idx] + hashed_codes[matched_idx+1:]
    remaining_json = json.dumps(remaining_codes) if remaining_codes else None
    
    return {
        'valid': True,
        'codes_remaining': len(remaining_codes),
        'remaining_codes_json': remaining_json
    }


def get_totp_current_token(secret):
    """Get the current valid TOTP token (for testing/debugging only).
    
    Args:
        secret: The TOTP secret (base32)
    
    Returns:
        str: Current 6-digit token
    """
    if not secret:
        return None
    totp = pyotp.TOTP(secret)
    return totp.now()
