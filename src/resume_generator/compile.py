# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""XeLaTeX compilation.

Unlike the original script this never calls ``os.chdir`` -- the working
directory is passed to ``subprocess.run`` instead, so concurrent compilations
into different directories cannot corrupt each other.
"""

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


class LatexNotInstalledError(RuntimeError):
    pass


@dataclass
class CompileResult:
    ok: bool
    pdf_path: Path | None
    page_count: int | None
    log: str
    tex_path: Path
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.ok:
            pages = f"{self.page_count} page(s)" if self.page_count else "unknown length"
            return f"Compiled {self.pdf_path} ({pages})"
        return f"Compilation failed: {'; '.join(self.errors) or 'see log'}"


def compile_pdf(tex_path: Path | str, timeout: int = 180) -> CompileResult:
    """Run XeLaTeX twice over ``tex_path`` and report what happened.

    Two passes are required so that ``\\hfill`` alignment and page references
    settle; the first pass runs with ``-no-pdf`` to produce the .xdv only.
    """
    tex_path = Path(tex_path).resolve()
    if not tex_path.exists():
        raise FileNotFoundError(f"LaTeX source not found: {tex_path}")

    if shutil.which("xelatex") is None:
        raise LatexNotInstalledError(
            "xelatex not found on PATH. Install MacTeX/TeX Live to render PDFs."
        )

    work_dir = tex_path.parent
    basename = tex_path.name
    log_parts: list[str] = []
    errors: list[str] = []

    passes = [
        ("First pass", ["xelatex", "-no-pdf", "-interaction=nonstopmode",
                        "-file-line-error", basename]),
        ("Second pass", ["xelatex", "-interaction=nonstopmode",
                         "-file-line-error", basename]),
    ]

    for label, command in passes:
        try:
            result = subprocess.run(
                command, cwd=work_dir, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{label} timed out after {timeout}s")
            log_parts.append(f"=== {label} ===\n<timed out>")
            break

        log_parts.append(f"=== {label} ===\n{result.stdout}")
        if result.stderr:
            log_parts.append(f"=== {label} stderr ===\n{result.stderr}")
        if result.returncode != 0:
            errors.append(f"{label} exited with code {result.returncode}")
            errors.extend(_extract_latex_errors(result.stdout))
            break

    log = "\n".join(log_parts)
    (work_dir / "latex.log").write_text(log, encoding="utf-8", errors="replace")

    pdf_path = tex_path.with_suffix(".pdf")
    if not errors and not pdf_path.exists():
        errors.append(f"XeLaTeX reported success but {pdf_path.name} was not produced")

    if errors:
        return CompileResult(False, None, None, log, tex_path, errors)

    return CompileResult(
        ok=True,
        pdf_path=pdf_path,
        page_count=get_pdf_page_count(pdf_path),
        log=log,
        tex_path=tex_path,
    )


def _extract_latex_errors(stdout: str, limit: int = 5) -> list[str]:
    """Pull the `file:line: message` lines that -file-line-error emits."""
    found = [
        line.strip()
        for line in stdout.splitlines()
        if line.startswith("!") or (".tex:" in line and "error" in line.lower())
    ]
    return found[:limit]


def get_pdf_page_count(pdf_path: Path | str) -> int | None:
    """Page count via pdfinfo, or None when poppler is not installed."""
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return None

    result = subprocess.run(
        [pdfinfo, str(pdf_path)], capture_output=True, text=True
    )
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None
