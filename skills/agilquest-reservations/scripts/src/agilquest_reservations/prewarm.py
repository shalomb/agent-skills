#!/usr/bin/env python3
"""
Pre-warm: seed OS DNS cache and warm Chrome's network stack via the
MS app launcher before the 23:57 booking job.

Runs at 23:51 — gives Chrome 6 minutes with warm TCP/TLS connections
and a proven launcher→samlsuccess redirect path before booking fires.
"""

import sys
import ssl
import socket
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Error: playwright not installed. Run: uv sync", file=sys.stderr)
    sys.exit(1)

from agilquest_reservations.lib.browser import APP_LAUNCHER, launch_headless, establish_session

DOMAINS = [
    "login.agilquest.com",
    "auth.agilquest.com",
    "login.microsoftonline.com",
    "launcher.myapps.microsoft.com",
]


def seed_dns(domains: list[str]):
    print("Step 1: Seeding OS DNS cache via TLS connects...", file=sys.stderr)
    ctx = ssl.create_default_context()
    for domain in domains:
        for attempt in range(1, 4):
            try:
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=domain):
                        print(f"  DNS/TLS seeded: {domain}", file=sys.stderr)
                        break
            except Exception as e:
                if attempt == 3:
                    print(f"  warning: could not seed {domain}: {e}", file=sys.stderr)
                else:
                    time.sleep(3)


def warm_chrome():
    """Go through the full launcher→samlsuccess flow headlessly to warm
    Chrome's network stack and confirm the MS SSO path works before booking."""
    print("Step 2: Warming Chrome via MS app launcher...", file=sys.stderr)
    with sync_playwright() as p:
        ctx = launch_headless(p)
        try:
            page = ctx.new_page()
            ok = establish_session(page)
            if ok:
                print("  Chrome warm — launcher→Agilquest session confirmed.", file=sys.stderr)
            else:
                print(
                    "  WARNING: launcher landed on MS login — MS tokens may have expired. "
                    "Run: aq setup-auth",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"  WARNING: Chrome warm failed: {str(e).splitlines()[0]}", file=sys.stderr)
        finally:
            ctx.close()


if __name__ == "__main__":
    seed_dns(DOMAINS)
    warm_chrome()
    print("Pre-warm complete.", file=sys.stderr)
