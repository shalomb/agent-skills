#!/usr/bin/env python3
"""
Pre-warm: seed OS DNS cache via TLS connects before the 23:57 booking job.

Runs at 23:51 — gives the OS resolver 6 minutes to cache all target domains.
Chrome's DNS resolver picks up the OS cache on its first lookup, so this
reduces cold-start DNS latency for the booking script.
"""

import sys
import ssl
import socket
import time

DOMAINS = [
    "login.agilquest.com",
    "auth.agilquest.com",
    "login.microsoftonline.com",
    "launcher.myapps.microsoft.com",
]


def seed_dns(domains: list[str]):
    ctx = ssl.create_default_context()
    for domain in domains:
        for attempt in range(1, 4):
            try:
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with ctx.wrap_socket(sock, server_hostname=domain):
                        print(f"  seeded: {domain}", file=sys.stderr)
                        break
            except Exception as e:
                if attempt == 3:
                    print(f"  warning: could not seed {domain}: {e}", file=sys.stderr)
                else:
                    time.sleep(3)


if __name__ == "__main__":
    print("Seeding OS DNS cache...", file=sys.stderr)
    seed_dns(DOMAINS)
    print("Pre-warm complete.", file=sys.stderr)
