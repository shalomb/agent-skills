---
name: video-transcript
description: Extract full transcripts from video content for analysis, summarization, note-taking, or research. Use when the user wants a written version of video content, asks to "transcribe this", "get the text from this video", "convert video to text", or shares a video URL for content extraction. Supports standard YouTube videos, Shorts, and bare video IDs.
---

# Video Transcript

Extract transcripts from videos via [TranscriptAPI.com](https://transcriptapi.com).

## Setup

If `TRANSCRIPT_API_KEY` is not found in the `.env` file within the skill directory, help the user create an account (100 free credits, no card):

**Step 1 — Register:** Ask the user for their email.

```bash
uv run scripts/auth.py register --email USER_EMAIL
```

→ OTP sent to email. Ask user: _"Check your email for a 6-digit verification code."_

**Step 2 — Verify:** Once the user provides the OTP:

```bash
uv run scripts/auth.py verify --token TOKEN_FROM_STEP_1 --otp CODE
```

> API key saved to `.env` in the skill directory. Ready to use.

Manual option: [transcriptapi.com/signup](https://transcriptapi.com/signup) → Dashboard → API Keys.

## Usage

Use `scripts/transcribe.py` to get transcripts.

```bash
uv run scripts/transcribe.py VIDEO_URL --format [json|text]
```

### Options

| Param | Description | Default |
| --- | --- | --- |
| `video_url` | YouTube URL or 11-char video ID | — |
| `--format` | `json` (structured) or `text` (readable) | `json` |
| `--no-timestamps`| Exclude timestamps from text output | `true` |
| `--no-metadata` | Exclude metadata from response | `true` |

Accepted URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://youtube.com/shorts/VIDEO_ID`
- Bare video ID: `dQw4w9WgXcQ`

### Example Response (`--format text`)

```json
{
  "video_id": "dQw4w9WgXcQ",
  "language": "en",
  "transcript": "[00:00:18] We're no strangers to love\n[00:00:21] You know the rules...",
  "metadata": {
    "title": "Rick Astley - Never Gonna Give You Up",
    "author_name": "Rick Astley",
    "author_url": "https://www.youtube.com/@RickAstley",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
  }
}
```

## Tips

- Summarize long transcripts into key points first, offer full text on request.
- Use `json` format when you need precise timestamps for quoting specific moments.
- Metadata includes video title and channel for additional context.
- Works with YouTube Shorts too.

## Errors

| Status | Meaning | Action |
| --- | --- | --- |
| 401 | Bad API key | Check key or re-setup |
| 402 | No credits | Top up at transcriptapi.com/billing |
| 404 | No transcript | Video may not have captions enabled |
| 408 | Timeout | Retry once after 2s |

1 credit per successful request. Errors don't consume credits. Free tier: 100 credits, 300 req/min.
