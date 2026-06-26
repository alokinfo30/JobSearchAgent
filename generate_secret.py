#!/usr/bin/env python
"""
Generate a secure secret key
Run: python generate_secret.py
"""

import secrets
import string

def generate_secure_key(length=32):
    """Generate a cryptographically secure secret key"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    key = generate_secure_key(32)
    print("=" * 60)
    print("🔐 Your Secure SECRET_KEY:")
    print("=" * 60)
    print(key)
    print("=" * 60)
    print("\nCopy this key and paste it in your .env file as:")
    print(f"SECRET_KEY={key}")