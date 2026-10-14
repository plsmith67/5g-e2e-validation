"""Load lab settings.

configs/lab.yaml holds safe, public defaults and is committed to Git.
configs/lab.local.yaml (optional, never committed) holds your private lab values.
Anything in the local file overrides the same setting in lab.yaml, so it only needs
the values that differ. Set LAB_CONFIG=/path/to/file.yaml to use another file instead.
"""
import os
from pathlib import Path
from types import SimpleNamespace

import yaml

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO / "configs" / "lab.yaml"
LOCAL_CONFIG = REPO / "configs" / "lab.local.yaml"


def _ns(value):
    if isinstance(value, dict):
        return SimpleNamespace(**{k: _ns(v) for k, v in value.items()})
    return value


def _merge(base, override):
    out = dict(base)
    for k, v in (override or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _read(path):
    with open(path) as f:
        return yaml.safe_load(f) or {}


def sources():
    """The files that make up the active config, in the order they are applied."""
    files = [DEFAULT_CONFIG]
    override = os.environ.get("LAB_CONFIG")
    if override:
        files.append(Path(override).expanduser())
    elif LOCAL_CONFIG.exists():
        files.append(LOCAL_CONFIG)
    return files


def load():
    data = {}
    for path in sources():
        data = _merge(data, _read(path))
    cfg = _ns(data)
    cfg.lab.ueransim_dir = Path(cfg.lab.ueransim_dir).expanduser()
    return cfg


if __name__ == "__main__":
    # Lets shell scripts read one value, e.g.  python3 -m e2e.config subscriber.imsi
    import sys
    value = load()
    for part in sys.argv[1].split("."):
        value = getattr(value, part)
    print(value)
