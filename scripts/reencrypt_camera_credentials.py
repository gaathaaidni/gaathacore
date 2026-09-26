"""Camera Credential Re-encryption & Safety Proof Tool.

Used to inspect existing camera credential state in Sentira database and safely
re-encrypt records when rotating SENTIRA_CAMERA_CREDENTIAL_ENCRYPTION_KEY.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from urllib.parse import urlparse

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None


def derive_key(secret: str) -> bytes:
    """Derive 32-byte key using SHA-256 matching NestJS EncryptionService."""
    if len(secret) < 32:
        raise ValueError("Encryption key must be at least 32 characters long.")
    return hashlib.sha256(secret.encode("utf-8")).digest()


def decrypt_credential(key_bytes: bytes, encrypted_hex: str) -> str:
    """Decrypts AES-256-GCM payload formatted as IV (16B) + Tag (16B) + Ciphertext."""
    if not AESGCM:
        raise RuntimeError("cryptography library required for AES-GCM operations")
    raw = bytes.fromhex(encrypted_hex)
    if len(raw) < 32:
        raise ValueError("Encrypted data too short")
    iv = raw[:16]
    tag = raw[16:32]
    ciphertext = raw[32:]

    # In Python cryptography AESGCM, tag is appended to ciphertext
    aesgcm = AESGCM(key_bytes)
    decrypted_bytes = aesgcm.decrypt(iv, ciphertext + tag, None)
    return decrypted_bytes.decode("utf-8")


def encrypt_credential(key_bytes: bytes, plaintext: str) -> str:
    """Encrypts plaintext into IV (16B) + Tag (16B) + Ciphertext in hex matching NestJS."""
    if not AESGCM:
        raise RuntimeError("cryptography library required for AES-GCM operations")
    iv = os.urandom(16)
    aesgcm = AESGCM(key_bytes)
    # aesgcm.encrypt returns ciphertext + 16-byte tag at the end
    ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    ciphertext = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return (iv + tag + ciphertext).hex()


def inspect_camera_state(db_url: str) -> dict:
    """Inspects the Sentira database for camera count and encrypted password presence."""
    if not psycopg2:
        raise RuntimeError("psycopg2 library is required")
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) AS total_cameras,
                    COUNT("passwordEncrypted") AS encrypted_pw_count,
                    COUNT(CASE WHEN "passwordEncrypted" IS NULL OR "passwordEncrypted" = '' THEN 1 END) AS unencrypted_or_empty
                FROM cameras;
            """)
            row = cur.fetchone()
            return dict(row)
    finally:
        conn.close()


def reencrypt_all_cameras(db_url: str, old_secret: str, new_secret: str, dry_run: bool = True) -> int:
    """Re-encrypts all camera passwords from old key to new key in a single transaction."""
    if not psycopg2:
        raise RuntimeError("psycopg2 library is required")
    old_key = derive_key(old_secret)
    new_key = derive_key(new_secret)

    conn = psycopg2.connect(db_url)
    updated_count = 0
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT id, name, "passwordEncrypted" FROM cameras WHERE "passwordEncrypted" IS NOT NULL;')
                rows = cur.fetchall()
                print(f"Found {len(rows)} camera(s) with encrypted credentials.")

                for row in rows:
                    cam_id = row["id"]
                    enc_old = row["passwordEncrypted"]
                    # Decrypt with old key
                    plaintext = decrypt_credential(old_key, enc_old)
                    # Re-encrypt with new key
                    enc_new = encrypt_credential(new_key, plaintext)
                    # Verify immediately with new key
                    verify_plain = decrypt_credential(new_key, enc_new)
                    assert verify_plain == plaintext, f"Integrity check failed for camera {cam_id}"

                    if not dry_run:
                        cur.execute(
                            'UPDATE cameras SET "passwordEncrypted" = %s, "updatedAt" = NOW() WHERE id = %s;',
                            (enc_new, cam_id)
                        )
                    updated_count += 1

            if dry_run:
                print(f"DRY RUN: Successfully verified decryption and re-encryption for {updated_count} camera(s). No DB changes made.")
                conn.rollback()
            else:
                print(f"COMMITTED: Successfully re-encrypted {updated_count} camera(s) with new key.")
        return updated_count
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Sentira Camera Credential Re-encryption & Verification Tool")
    parser.add_argument("--db-url", default=os.environ.get("SENTIRA_DATABASE_URL"), help="PostgreSQL connection URL for sentira database")
    parser.add_argument("--inspect-only", action="store_true", help="Inspect camera table counts only")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Test re-encryption without committing")
    parser.add_argument("--commit", action="store_true", help="Execute and commit re-encryption")
    args = parser.parse_args()

    if not args.db_url:
        print("Error: --db-url or SENTIRA_DATABASE_URL environment variable is required.")
        sys.exit(1)

    if args.inspect_only:
        state = inspect_camera_state(args.db_url)
        print("Camera Table Inspection Results:")
        print(f"  Total Cameras: {state['total_cameras']}")
        print(f"  Cameras with Encrypted Passwords: {state['encrypted_pw_count']}")
        print(f"  Cameras without Encrypted Passwords: {state['unencrypted_or_empty']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
