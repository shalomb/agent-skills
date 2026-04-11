# /// script
# dependencies = [
#   "rich",
# ]
# ///

import subprocess
import argparse
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def run_git_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running git command:[/red] {e}")
        return ""

def high_churn(since="1 year ago", limit=20):
    console.print(Panel(f"High-Churn Files (Since: {since})", style="bold blue"))
    cmd = f'git log --format=format: --name-only --since="{since}" | sort | uniq -c | sort -nr | head -{limit}'
    output = run_git_command(cmd)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Commits", justify="right")
    table.add_column("File Path")
    
    for line in output.split("\n"):
        if line.strip():
            count, path = line.strip().split(None, 1)
            table.add_row(count, path)
    
    console.print(table)

def bus_factor(since=None, limit=20):
    title = "Contributor Distribution (Overall)"
    cmd = 'git shortlog -sn --no-merges'
    if since:
        title = f"Contributor Distribution (Since: {since})"
        cmd += f' --since="{since}"'
    
    console.print(Panel(title, style="bold blue"))
    output = run_git_command(cmd)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Commits", justify="right")
    table.add_column("Author")
    
    for i, line in enumerate(output.split("\n")):
        if line.strip() and i < limit:
            count, author = line.strip().split(None, 1)
            table.add_row(count, author)
    
    console.print(table)

def bug_hotspots(limit=20):
    console.print(Panel("Bug Hotspots (Fix-related keywords)", style="bold blue"))
    cmd = f'git log -i -E --grep="fix|bug|broken" --name-only --format=\'\' | sort | uniq -c | sort -nr | head -{limit}'
    output = run_git_command(cmd)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Fixes", justify="right")
    table.add_column("File Path")
    
    for line in output.split("\n"):
        if line.strip():
            count, path = line.strip().split(None, 1)
            table.add_row(count, path)
    
    console.print(table)

def project_velocity():
    console.print(Panel("Project Velocity (Commits per Month)", style="bold blue"))
    cmd = "git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c"
    output = run_git_command(cmd)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Commits", justify="right")
    table.add_column("Month (YYYY-MM)")
    
    for line in output.split("\n"):
        if line.strip():
            count, month = line.strip().split(None, 1)
            table.add_row(count, month)
    
    console.print(table)

def firefighting(since="1 year ago"):
    console.print(Panel(f"Firefighting Patterns (Since: {since})", style="bold blue"))
    cmd = f"git log --oneline --since=\"{since}\" | grep -iE 'revert|hotfix|emergency|rollback'"
    output = run_git_command(cmd)
    
    if not output:
        console.print("[green]No firefighting patterns found.[/green]")
        return

    table = Table(show_header=True, header_style="bold red")
    table.add_column("Hash", style="dim")
    table.add_column("Subject")
    
    for line in output.split("\n"):
        if line.strip():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                hash_val, subject = parts
                table.add_row(hash_val, subject)
            else:
                table.add_row("", line.strip())
    
    console.print(table)

def full_report():
    high_churn()
    bus_factor(since="6 months ago")
    bug_hotspots()
    project_velocity()
    firefighting()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Git Forensics: Analyze codebase health via git history.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("churn", help="Identify high-churn files")
    subparsers.add_parser("bus", help="Analyze contributor distribution (Bus Factor)")
    subparsers.add_parser("bugs", help="Locate bug hotspots")
    subparsers.add_parser("velocity", help="Track project velocity")
    subparsers.add_parser("fire", help="Detect firefighting patterns")
    subparsers.add_parser("report", help="Run full forensic report")

    args = parser.parse_args()

    if args.command == "churn":
        high_churn()
    elif args.command == "bus":
        bus_factor(since="6 months ago")
    elif args.command == "bugs":
        bug_hotspots()
    elif args.command == "velocity":
        project_velocity()
    elif args.command == "fire":
        firefighting()
    elif args.command == "report":
        full_report()
