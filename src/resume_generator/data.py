"""Loading the master resume from YAML."""

from pathlib import Path

import yaml

from .paths import default_data_file
from .schema import ResumeData

_ENCODINGS = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]


def load_raw(yaml_file: Path | str) -> dict:
    """Read a YAML file, trying several encodings before giving up.

    Kept from the original script: the source data has been through enough
    editors that a plain utf-8 read is not guaranteed to succeed.
    """
    path = Path(yaml_file)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    last_error: Exception | None = None
    for encoding in _ENCODINGS:
        try:
            content = path.read_text(encoding=encoding)
            if encoding != "utf-8":
                content = content.encode("utf-8", errors="replace").decode("utf-8")
            return yaml.safe_load(content)
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            last_error = exc
            continue

    # Last resort: lossy decode rather than failing outright.
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return yaml.safe_load(content)
    except Exception as exc:
        raise ValueError(
            f"Failed to load YAML file {path} after trying {_ENCODINGS}: {exc}"
        ) from last_error


def load_resume_data(yaml_file: Path | str | None = None) -> ResumeData:
    """Load and validate the master resume."""
    path = Path(yaml_file) if yaml_file else default_data_file()
    raw = load_raw(path)
    if not isinstance(raw, dict):
        raise ValueError(f"Expected a mapping at the top level of {path}")

    # The original script accepted `academic_projects` as an alias; the current
    # template renders neither, so only the documented keys are validated.
    return ResumeData.model_validate(raw)
