#!/usr/bin/env python3
"""Execute every notebook folder that carries a _request.json, then record the outcome.

Run by .github/workflows/execute-notebooks.yml on GitHub Actions, where the internet is open.
For each notebooks/<folder>/_request.json:
  1. executes the requested notebook in place (errors are kept in the outputs, not fatal),
  2. writes notebooks/<folder>/_execution.json with the request_id, status and file list,
  3. deletes the _request.json.
Always exits 0 so the workflow can commit whatever happened, failures included.
"""
from __future__ import annotations

import datetime as dt
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"
DEFAULT_TIMEOUT_S = 1500  # per cell


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def error_outputs(nb_path: Path) -> list[dict]:
    """Return the error outputs left in an executed notebook (nbconvert --allow-errors keeps them)."""
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    errors = []
    for index, cell in enumerate(nb.get("cells", [])):
        for out in cell.get("outputs", []) or []:
            if out.get("output_type") == "error":
                errors.append(
                    {
                        "cell_index": index,
                        "ename": out.get("ename"),
                        "evalue": str(out.get("evalue", ""))[:2000],
                        "traceback_tail": [str(line)[-400:] for line in (out.get("traceback") or [])[-6:]],
                    }
                )
    return errors


def execute(folder: Path) -> None:
    request_path = folder / "_request.json"
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except Exception as exc:  # malformed request: record and move on
        request = {"request_id": None, "parse_error": repr(exc)}

    notebook_name = request.get("notebook")
    if not notebook_name:
        candidates = sorted(p.name for p in folder.glob("*.ipynb"))
        notebook_name = candidates[0] if candidates else None

    record = {
        "request_id": request.get("request_id"),
        "notebook": notebook_name,
        "folder": str(folder.relative_to(ROOT)),
        "started_at": now(),
        "runner": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
    }

    if not notebook_name or not (folder / notebook_name).exists():
        record.update(status="error", error="Notebook not found in folder", finished_at=now())
    else:
        timeout = int(request.get("timeout_s") or DEFAULT_TIMEOUT_S)
        started = time.time()
        proc = subprocess.run(
            [
                sys.executable, "-m", "jupyter", "nbconvert",
                "--to", "notebook", "--execute", "--inplace", "--allow-errors",
                f"--ExecutePreprocessor.timeout={timeout}",
                "--ExecutePreprocessor.kernel_name=python3",
                notebook_name,
            ],
            cwd=folder,
            capture_output=True,
            text=True,
        )
        record["duration_s"] = round(time.time() - started, 1)
        record["nbconvert_returncode"] = proc.returncode
        errors = error_outputs(folder / notebook_name) if proc.returncode == 0 else []
        if proc.returncode != 0:
            record.update(status="error", error="nbconvert failed", stderr_tail=proc.stderr[-4000:])
        elif errors:
            record.update(status="error", error="One or more cells raised an exception", cell_errors=errors)
        else:
            record["status"] = "ok"
        record["finished_at"] = now()

    record["files"] = sorted(
        str(p.relative_to(folder))
        for p in folder.rglob("*")
        if p.is_file() and p.name not in {"_request.json", "_execution.json"}
    )
    summary = folder / "results" / "summary.json"
    if summary.exists():
        try:
            record["summary"] = json.loads(summary.read_text(encoding="utf-8"))
        except Exception as exc:
            record["summary_error"] = repr(exc)

    (folder / "_execution.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    request_path.unlink(missing_ok=True)
    print(f"{record['folder']}: {record.get('status')} ({record.get('duration_s', 0)} s)")


def main() -> int:
    requests = sorted(NOTEBOOKS.glob("*/_request.json"))
    if not requests:
        print("No _request.json found; nothing to execute.")
        return 0
    for request_path in requests:
        execute(request_path.parent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
