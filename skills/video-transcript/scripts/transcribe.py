# /// script
# dependencies = [
#   "httpx",
#   "python-dotenv",
# ]
# ///

import os
import sys
import argparse
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

API_URL = "https://transcriptapi.com/api/v2/youtube/transcript"
DOTENV_PATH = Path(__file__).parent.parent / ".env"


def transcribe(
    video_url: str,
    fmt: str = "json",
    include_timestamp: bool = True,
    send_metadata: bool = True,
):
    load_dotenv(DOTENV_PATH)
    api_key = os.getenv("TRANSCRIPT_API_KEY")

    if not api_key:
        print("Error: TRANSCRIPT_API_KEY not found in environment or .env file.")
        print("Please run the registration and verification steps first.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {api_key}"}

    params = {
        "video_url": video_url,
        "format": fmt,
        "include_timestamp": str(include_timestamp).lower(),
        "send_metadata": str(send_metadata).lower(),
    }

    try:
        response = httpx.get(API_URL, headers=headers, params=params, timeout=60.0)
        response.raise_for_status()

        # Output the response
        if fmt == "json":
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)

    except httpx.HTTPStatusError as e:
        print(
            f"Transcription failed (Status {e.response.status_code}): {e.response.text}"
        )
        sys.exit(1)
    except httpx.TimeoutException:
        print("Transcription request timed out.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube videos via TranscriptAPI.com"
    )
    parser.add_argument("video_url", help="YouTube URL or 11-char video ID")
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_false",
        dest="include_timestamp",
        help="Exclude timestamps from text output",
    )
    parser.add_argument(
        "--no-metadata",
        action="store_false",
        dest="send_metadata",
        help="Exclude metadata from response",
    )

    args = parser.parse_args()

    transcribe(args.video_url, args.format, args.include_timestamp, args.send_metadata)
