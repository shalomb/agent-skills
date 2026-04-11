# /// script
# dependencies = [
#   "httpx",
#   "python-dotenv",
# ]
# ///

import sys
import argparse
import httpx
from pathlib import Path
from dotenv import set_key

API_BASE = "https://transcriptapi.com/api/v2"
DOTENV_PATH = Path(__file__).parent.parent / ".env"


def register(email: str):
    print(f"Registering {email}...")
    try:
        response = httpx.post(f"{API_BASE}/auth/register", json={"email": email})
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if not token:
            print("Error: No token received from API.")
            sys.exit(1)

        # We don't necessarily need to store the token in .env yet,
        # but let's keep it in memory or print it for the verify step.
        print(f"OTP sent to {email}. Verification token: {token}")
        print(
            f"Please run: python3 {sys.argv[0]} verify --token {token} --otp <6-digit-code>"
        )
    except httpx.HTTPStatusError as e:
        print(f"Registration failed: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


def verify(token: str, otp: str):
    print("Verifying OTP...")
    try:
        response = httpx.post(
            f"{API_BASE}/auth/verify", json={"token": token, "otp": otp}
        )
        response.raise_for_status()
        data = response.json()
        api_key = data.get("api_key")
        if not api_key:
            print("Error: No API key received from API.")
            sys.exit(1)

        # Save to .env
        DOTENV_PATH.parent.mkdir(parents=True, exist_ok=True)
        set_key(str(DOTENV_PATH), "TRANSCRIPT_API_KEY", api_key)
        print(f"Success! API key saved to {DOTENV_PATH}")
    except httpx.HTTPStatusError as e:
        print(f"Verification failed: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Authenticate with TranscriptAPI.com")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reg_parser = subparsers.add_parser("register", help="Register your email")
    reg_parser.add_argument("--email", required=True, help="Email address to register")

    ver_parser = subparsers.add_parser("verify", help="Verify with OTP")
    ver_parser.add_argument(
        "--token", required=True, help="Token from registration step"
    )
    ver_parser.add_argument("--otp", required=True, help="6-digit OTP from email")

    args = parser.parse_args()

    if args.command == "register":
        register(args.email)
    elif args.command == "verify":
        verify(args.token, args.otp)
