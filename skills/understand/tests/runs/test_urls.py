# pyright: reportMissingImports=false
"""Unit tests for report URL generation and end message formatting."""

from understand_runs.urls import (
    DEFAULT_PARALLELS_IP,
    DEFAULT_TAILNET_IP,
    format_end_message,
    get_report_urls,
)


def test_get_report_urls_default_and_custom():
    urls = get_report_urls("my-repo", "full", "run-1")
    assert "parallels" in urls
    assert "tailnet" in urls
    assert urls["parallels"] == f"http://{DEFAULT_PARALLELS_IP}:8787/r/understand/my-repo/full/run-1/"
    assert urls["tailnet"] == f"http://{DEFAULT_TAILNET_IP}:8787/r/understand/my-repo/full/run-1/"

    custom = get_report_urls(
        "my-repo",
        "topic-auth",
        "run-2",
        port=9000,
        parallels_ip="10.211.55.10",
        tailnet_ip="100.99.83.10",
    )
    assert custom["parallels"] == "http://10.211.55.10:9000/r/understand/my-repo/topic-auth/run-2/"
    assert custom["tailnet"] == "http://100.99.83.10:9000/r/understand/my-repo/topic-auth/run-2/"


def test_format_end_message_length_and_content():
    urls = get_report_urls("my-repo", "full", "run-1")
    msg = format_end_message("my-repo", "full", urls, summary="Mapped structure across 5 files.")

    lines = msg.strip().splitlines()
    assert len(lines) <= 5, f"Message has more than 5 lines: {len(lines)}"

    # Must contain both network addresses
    assert urls["parallels"] in msg
    assert urls["tailnet"] in msg
