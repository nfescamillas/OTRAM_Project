from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterable


class AlertState:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> set[str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return set()
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"cannot read alert state {self.path}: {error}") from error
        fingerprints = payload.get("active_fingerprints") if isinstance(payload, dict) else None
        if not isinstance(fingerprints, list) or not all(
            isinstance(item, str) for item in fingerprints
        ):
            raise RuntimeError(f"invalid alert state file: {self.path}")
        return set(fingerprints)

    def save(self, fingerprints: Iterable[str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {"active_fingerprints": sorted(set(fingerprints))}, indent=2
        ) + "\n"
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.path.parent, prefix=f".{self.path.name}.", suffix=".tmp", text=True
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
        finally:
            temporary_path.unlink(missing_ok=True)
