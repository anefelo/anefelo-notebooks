#!/usr/bin/env python3
"""Wait for GitHub Actions to finish executing a notebook request, then pull the results.

Usage:
    python tools/await_run.py notebooks/<folder> <request_id> [--timeout 540] [--interval 30]

Polls origin/main for notebooks/<folder>/_execution.json carrying <request_id>.
Exit codes: 0 executed OK (results pulled), 1 executed with errors (results pulled, see the
printed record), 2 still waiting when --timeout ran out (call again), 3 git problem.
Keep --timeout under the shell tool's own limit and call again on exit code 2.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("request_id")
    parser.add_argument("--timeout", type=int, default=540)
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()

    folder = args.folder.rstrip("/")
    deadline = time.time() + args.timeout
    while True:
        # Explicit refspec: clones of an empty or single-branch repo may not track origin/main on their own
        fetch = git("fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main")
        if fetch.returncode != 0:
            print(fetch.stderr.strip(), file=sys.stderr)
        shown = git("show", f"origin/main:{folder}/_execution.json")
        if shown.returncode == 0:
            try:
                record = json.loads(shown.stdout)
            except json.JSONDecodeError:
                record = {}
            if record.get("request_id") == args.request_id:
                pull = git("pull", "-q", "--rebase", "--autostash", "origin", "main")
                if pull.returncode != 0:
                    print(pull.stderr.strip(), file=sys.stderr)
                    print(json.dumps(record, indent=2))
                    return 3
                print(json.dumps(record, indent=2))
                return 0 if record.get("status") == "ok" else 1
        if time.time() + args.interval > deadline:
            print(f"Still waiting for request {args.request_id} in {folder}", file=sys.stderr)
            return 2
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
