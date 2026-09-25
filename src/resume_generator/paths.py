"""Project path resolution.

Paths are resolved relative to the repository root so the package keeps working
when installed in editable mode and invoked from any working directory.
"""

import os
from pathlib import Path

_ENV_ROOT = "RESUME_GENERATOR_ROOT"
_ENV_DATA_FILE = "RESUME_GENERATOR_DATA_FILE"


def project_root() -> Path:
    """Repository root holding ``templates/``, ``data/`` and ``output/``."""
    override = os.environ.get(_ENV_ROOT)
    if override:
        return Path(override).expanduser().resolve()
    # src/resume_generator/paths.py -> src/resume_generator -> src -> root
    return Path(__file__).resolve().parents[2]


def templates_dir() -> Path:
    return project_root() / "templates"


def template_dir(style: str = "faang") -> Path:
    return templates_dir() / style


def data_dir() -> Path:
    return project_root() / "data"


def default_data_file() -> Path:
    override = os.environ.get(_ENV_DATA_FILE)
    if override:
        return Path(override).expanduser().resolve()
    return data_dir() / "resume_data_en_faang.yaml"


def output_dir() -> Path:
    return project_root() / "output"


def build_dir() -> Path:
    return project_root() / "build"
