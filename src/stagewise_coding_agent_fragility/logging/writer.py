"""Write RunLog objects to JSON files on disk."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from stagewise_coding_agent_fragility.logging.schema import RunLog


def write_run_log(log: RunLog, output_dir: str | Path) -> Path:
    """Serialize a RunLog to a JSON file in output_dir.

    The file is named ``{log.run_id}.json``.  The output directory is
    created if it does not already exist.

    Args:
        log: The completed run log to persist.
        output_dir: Directory where the JSON file will be written.

    Returns:
        Path to the written JSON file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    target = out / f"{log.run_id}.json"
    payload = dataclasses.asdict(log)

    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return target

