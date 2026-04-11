# /// script
# dependencies = [
#   "rich",
# ]
# ///

import subprocess
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def run_git_command(command):
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
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
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                count, path = parts
                table.add_row(count, path)
            else:
                continue

    console.print(table)


def bus_factor(since=None, limit=20):
    title = "Contributor Distribution (Overall)"
    cmd = "git shortlog -sn --no-merges"
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
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                count, author = parts
                table.add_row(count, author)
            else:
                continue

    console.print(table)


def bug_hotspots(limit=20):
    console.print(Panel("Bug Hotspots (Fix-related keywords)", style="bold blue"))
    cmd = f"git log -i -E --grep=\"fix|bug|broken\" --name-only --format='' | sort | uniq -c | sort -nr | head -{limit}"
    output = run_git_command(cmd)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Fixes", justify="right")
    table.add_column("File Path")

    for line in output.split("\n"):
        if line.strip():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                count, path = parts
                table.add_row(count, path)
            else:
                continue

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
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                count, month = parts
                table.add_row(count, month)
            else:
                continue

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


# --- Code Archaeology Commands ---


def pickaxe(query, use_regex=False):
    console.print(
        Panel(f"Pickaxe Search: '{query}' (Regex: {use_regex})", style="bold blue")
    )
    flag = "-G" if use_regex else "-S"
    cmd = f"git log {flag} '{query}' --oneline --all"
    output = run_git_command(cmd)

    if not output:
        console.print("[green]No commits found containing this string/pattern.[/green]")
        return

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Commit Hash", style="dim")
    table.add_column("Commit Message")

    for line in output.split("\n"):
        if line.strip():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                hash_val, subject = parts
                table.add_row(hash_val, subject)
            else:
                table.add_row("", line.strip())

    console.print(table)
    console.print("[dim]Tip: Use `git show <hash>` to see the exact changes.[/dim]")


def xblame(file_path):
    console.print(Panel(f"X-Ray Blame: {file_path}", style="bold blue"))
    cmd = f"git blame -w -M -C {file_path}"
    output = run_git_command(cmd)

    if not output:
        console.print(f"[red]Could not blame {file_path}. Does it exist?[/red]")
        return

    print(output)


def find_deleted(limit=20):
    console.print(Panel("Recently Deleted Files", style="bold blue"))
    cmd = f"git log --diff-filter=D --summary | grep delete | head -{limit}"
    output = run_git_command(cmd)

    if not output:
        console.print("[green]No deleted files found.[/green]")
        return

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Action", style="dim")
    table.add_column("File Path")

    for line in output.split("\n"):
        if line.strip():
            # Format is typically: " delete mode 100644 path/to/file"
            parts = line.strip().split()
            if len(parts) >= 4:
                action = parts[0]
                path = " ".join(parts[3:])
                table.add_row(action, path)
            else:
                table.add_row("", line.strip())

    console.print(table)


def trace_function(function_name, file_path):
    console.print(
        Panel(f"Tracing Function '{function_name}' in {file_path}", style="bold blue")
    )
    cmd = f"git log -L :{function_name}:{file_path}"

    try:
        # We don't use run_git_command here because git log -L produces pager output and can be very long
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running git log -L:[/red] {e}")
        console.print(
            "[dim]Ensure the function name exists and the file path is correct.[/dim]"
        )


def stale_code(limit=20):
    console.print(Panel("Stale Code (Untouched Files)", style="bold blue"))
    # Lists all tracked files, gets their last commit date, sorts them (oldest first)
    cmd = (
        'for f in $(git ls-files); do if [ -f "$f" ]; then echo "$(git log -1 --format="%ai" -- "$f") $f"; fi; done | sort | head -'
        + str(limit)
    )
    output = run_git_command(cmd)

    if not output:
        console.print("[red]Could not analyze stale code.[/red]")
        return

    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Last Modified", justify="left")
    table.add_column("File Path")

    for line in output.split("\n"):
        if line.strip():
            # Format: "2023-01-01 12:00:00 +0000 path/to/file"
            parts = line.strip().split(" ", 3)
            if len(parts) == 4:
                date = parts[0]
                path = parts[3]
                table.add_row(date, path)
            else:
                table.add_row("", line.strip())

    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Git Forensics: Analyze codebase health and perform code archaeology via git history."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Health Commands
    subparsers.add_parser("churn", help="Identify high-churn files")
    subparsers.add_parser("bus", help="Analyze contributor distribution (Bus Factor)")
    subparsers.add_parser("bugs", help="Locate bug hotspots")
    subparsers.add_parser("velocity", help="Track project velocity")
    subparsers.add_parser("fire", help="Detect firefighting patterns")
    subparsers.add_parser("report", help="Run full forensic report")

    # Archaeology Commands
    pickaxe_parser = subparsers.add_parser(
        "pickaxe", help="Find commits that added/removed a string or regex"
    )
    pickaxe_parser.add_argument("query", help="The string or regex to search for")
    pickaxe_parser.add_argument(
        "-r",
        "--regex",
        action="store_true",
        help="Treat the query as a regular expression",
    )

    xblame_parser = subparsers.add_parser(
        "xblame", help="X-Ray Blame: ignore whitespace and detect moved/copied lines"
    )
    xblame_parser.add_argument("file", help="The file to blame")

    deleted_parser = subparsers.add_parser(
        "deleted", help="List recently deleted files"
    )
    deleted_parser.add_argument(
        "-n", "--limit", type=int, default=20, help="Number of files to show"
    )

    trace_parser = subparsers.add_parser(
        "trace", help="Trace the history of a specific function or class"
    )
    trace_parser.add_argument("name", help="The function or class name")
    trace_parser.add_argument("file", help="The file containing the function")

    stale_parser = subparsers.add_parser(
        "stale", help="Find the oldest untouched files (stale code)"
    )
    stale_parser.add_argument(
        "-n", "--limit", type=int, default=20, help="Number of files to show"
    )

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
    elif args.command == "pickaxe":
        pickaxe(args.query, args.regex)
    elif args.command == "xblame":
        xblame(args.file)
    elif args.command == "deleted":
        find_deleted(args.limit)
    elif args.command == "trace":
        trace_function(args.name, args.file)
    elif args.command == "stale":
        stale_code(args.limit)
