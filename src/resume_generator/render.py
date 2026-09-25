"""Jinja2 -> LaTeX source rendering.

Pure: takes data, returns a LaTeX string. Nothing here touches the filesystem
beyond reading templates, and nothing here knows about PDFs or Claude.
"""

from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .latex import escape_latex
from .paths import template_dir


@lru_cache(maxsize=8)
def _environment(directory: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(directory),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=StrictUndefined,
    )
    env.filters["escape_latex"] = escape_latex
    return env


def render(template_name: str, context: dict, style: str = "faang") -> str:
    """Render ``template_name`` from the given template style directory.

    ``context`` is exposed to the template under the name ``context`` -- the
    templates read everything through ``context.get(...)``.
    """
    directory = template_dir(style)
    if not directory.is_dir():
        raise FileNotFoundError(f"Template directory not found: {directory}")

    template = _environment(str(directory)).get_template(template_name)
    return template.render(context=context)


def write_tex(source: str, destination: Path | str) -> Path:
    """Write rendered LaTeX to disk, creating parent directories."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", errors="replace")
    return path
