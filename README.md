# Anefelo notebooks

Companion notebooks for [Anefelo](https://anefelo.substack.com), a newsletter on what satellite data says about the physical economy and its prices. Each notebook reproduces a post's figures and numbers from open data and opens in Google Colab.

## Open a notebook in Colab

Use the **Open in Colab** badge at the top of each notebook. No account or key is needed unless the notebook says so.

Notebooks are added while a post is being written, so a folder can appear here before its post is published.

## How notebooks are executed

Drafting sessions run behind a network allowlist that blocks satellite-data hosts, so execution happens here on GitHub Actions, where the internet is open:

1. A post's notebook lives in `notebooks/YYYY-MM-DD-<slug>/<slug>.ipynb`, started from `templates/article_notebook_template.ipynb`.
2. `python tools/request_run.py notebooks/<folder>` writes `_request.json` and prints a request id. Commit and push to `main`.
3. The **Execute notebooks** workflow runs the notebook in place and commits back to `main`: the executed notebook, `figures/`, `results/summary.json` and `_execution.json` (status, run time, errors, files).
4. `python tools/await_run.py notebooks/<folder> <request_id>` waits for that commit and pulls it. Exit codes: 0 ok, 1 executed with errors, 2 still running (call again).

`notebooks/0000-pipeline-check/` is a one-minute test of the whole loop on a Sentinel-2 chip over Thessaloniki port.

## Conventions

| Path | What |
|---|---|
| `figures/figN_<name>.png` | Figures for the post, data credit printed on the image |
| `results/summary.json` | Every number the post cites, with units and notes |
| `_execution.json` | Written by the workflow; the post may only use outputs from a run with `"status": "ok"` |

## Optional secrets

If a notebook needs a key, add it under Settings → Secrets and variables → Actions, using one of the names the workflow passes through: `FRED_API_KEY`, `EIA_API_KEY`, `EARTHDATA_TOKEN`, `HF_TOKEN`. In Colab, put the same name in the Secrets panel. Keys never go into a notebook.

## Data credits

Each notebook lists its sources, licences and credit lines in its provenance table, and prints the credit on every figure.
