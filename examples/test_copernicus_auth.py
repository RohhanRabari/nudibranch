#!/usr/bin/env python3
"""Test Copernicus Marine authentication.

This verifies your credentials are set up correctly.
Run with: python examples/test_copernicus_auth.py
"""

import os

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    """Check if Copernicus credentials are configured."""
    print("Copernicus Marine - Credential Check")
    print("=" * 60)
    print()

    username = os.getenv("COPERNICUSMARINE_SERVICE_USERNAME")
    password = os.getenv("COPERNICUSMARINE_SERVICE_PASSWORD")

    print("Checking environment variables...")
    print()

    if username and username != "your_email@example.com":
        print(f"✓ Username found: {username}")
        username_ok = True
    else:
        print("✗ Username NOT set (or still has placeholder value)")
        print("  Edit .env and set: COPERNICUSMARINE_SERVICE_USERNAME=your_email@example.com")
        username_ok = False

    if password and password != "your_password":
        print(f"✓ Password found: {'*' * len(password)}")
        password_ok = True
    else:
        print("✗ Password NOT set (or still has placeholder value)")
        print("  Edit .env and set: COPERNICUSMARINE_SERVICE_PASSWORD=your_password")
        password_ok = False

    print()
    print("-" * 60)

    if username_ok and password_ok:
        print("✅ Credentials configured!")
        print()
        print("Next step: Test the connection")
        print("Run: copernicusmarine login --check-credentials-valid")
        print()
        print("Or test programmatically:")
        print("  import copernicusmarine")
        print("  copernicusmarine.login()")
    else:
        print("❌ Credentials NOT configured")
        print()
        print("Action needed:")
        print("1. Open .env file")
        print("2. Replace placeholder values with your actual credentials:")
        print("   COPERNICUSMARINE_SERVICE_USERNAME=your.email@example.com")
        print("   COPERNICUSMARINE_SERVICE_PASSWORD=YourActualPassword")
        print("3. Save the file")
        print("4. Run this script again")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
