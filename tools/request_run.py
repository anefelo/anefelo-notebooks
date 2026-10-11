#!/usr/bin/env python3
"""Ask GitHub Actions to execute a notebook folder.

Usage:
    python tools/request_run.py notebooks/<folder> [<notebook>.ipynb] [--timeout 1500]

Writes notebooks/<folder>/_request.json with a fresh request_id and prints that id.
Commit and push the folder to main; the "Execute notebooks" workflow picks it up.
Then wait with:  python tools/await_run.py notebooks/<folder> <request_id>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import uuid
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("notebook", nargs="?")
    parser.add_argument("--timeout", type=int, default=1500, help="per-cell timeout in seconds")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"No such folder: {folder}", file=sys.stderr)
        return 1
    notebook = args.notebook
    if not notebook:
        candidates = sorted(p.name for p in folder.glob("*.ipynb"))
        if len(candidates) != 1:
            print(f"Name the notebook; found {candidates}", file=sys.stderr)
            return 1
        notebook = candidates[0]
    if not (folder / notebook).exists():
        print(f"No such notebook: {folder / notebook}", file=sys.stderr)
        return 1

    request = {
        "request_id": uuid.uuid4().hex,
        "notebook": notebook,
        "requested_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "timeout_s": args.timeout,
    }
    (folder / "_request.json").write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    print(request["request_id"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
