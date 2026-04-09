#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ $# -eq 0 ]]; then
  cat <<'USAGE'
Usage:
  scripts/gen_results.sh <run_dir> [<run_dir> ...]

Example:
  scripts/gen_results.sh \
    logs/ds-chat/humanevalplus_stagewise_fragility_20260325_142855__balanced \
    logs/qwen_plus/humanevalplus_stagewise_fragility_20260326_214221
USAGE
  exit 1
fi

for run_dir in "$@"; do
  if [[ ! -d "$run_dir" ]]; then
    echo "[skip] run dir not found: $run_dir" >&2
    continue
  fi

  rel="${run_dir#logs/}"
  if [[ "$rel" == "$run_dir" ]]; then
    rel="$(basename "$run_dir")"
  fi

  uv run python -m stagewise_coding_agent_fragility.cli.summarize_results \
    --log-dir "$run_dir" \
    --output-dir "results/$rel"

  uv run python -m stagewise_coding_agent_fragility.cli.generate_figures \
    --log-dir "$run_dir" \
    --output-dir "results/$rel/figures"
done
