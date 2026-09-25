# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""Orchestration: master resume + job posting -> reviewed PDF on disk.

This is the only module that composes the deterministic core (render, compile)
with the model-driven step (tailor).
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import tailor as _tailor
from .compile import CompileResult, compile_pdf
from .data import load_resume_data
from .paths import output_dir as default_output_root
from .render import render, write_tex
from .schema import (
    CoverLetterContent,
    Education,
    Experience,
    JobPosting,
    ResumeData,
    SkillCategory,
    Summary,
    TailoredResume,
)

RESUME_TEMPLATE = "faang_resume.tex.j2"
COVER_LETTER_TEMPLATE = "cover_letter.tex.j2"
MAX_ATTEMPTS = 3


class GroundingError(ValueError):
    """Raised when model output contains facts absent from the master resume."""


@dataclass
class GenerationResult:
    ok: bool
    output_dir: Path
    pdf_path: Path | None = None
    tex_path: Path | None = None
    page_count: int | None = None
    attempts: int = 0
    tailoring_notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "output_dir": str(self.output_dir),
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "tex_path": str(self.tex_path) if self.tex_path else None,
            "page_count": self.page_count,
            "attempts": self.attempts,
            "tailoring_notes": self.tailoring_notes,
            "warnings": self.warnings,
            "errors": self.errors,
        }


# --------------------------------------------------------------------------
# Grounding
# --------------------------------------------------------------------------

def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"\s+", " ", text).strip()


def validate_grounding(master: ResumeData, tailored: TailoredResume) -> None:
    """Reject tailored content that introduces facts the master lacks.

    Identity fields (company/position/period) must match a master role exactly.
    Skill items must already appear somewhere in the master's skill lists.
    Bullet *wording* is deliberately not checked -- rewording is the point --
    which is why the tailored data is persisted for human review.
    """
    problems: list[str] = []

    known_roles = {
        (_normalize(e.company), _normalize(e.position), _normalize(e.period))
        for e in master.experience
    }
    for entry in tailored.experience:
        key = (
            _normalize(entry.company),
            _normalize(entry.position),
            _normalize(entry.period),
        )
        if key not in known_roles:
            problems.append(
                f"experience entry '{entry.position} @ {entry.company} "
                f"({entry.period})' does not match any role in the master resume"
            )

    known_skills = {
        _normalize(item)
        for category in master.skills
        for item in category.items
    }
    for category in tailored.skills:
        for item in category.items:
            if _normalize(item) not in known_skills:
                problems.append(
                    f"skill '{item}' (in '{category.category}') is not listed "
                    f"in the master resume"
                )

    if problems:
        raise GroundingError(
            "Tailored content is not grounded in the master resume:\n  - "
            + "\n  - ".join(problems)
        )


def merge_tailored(master: ResumeData, tailored: TailoredResume) -> ResumeData:
    """Build the renderable resume: model content plus untouched master facts.

    Personal details, education and languages are never model-generated.
    """
    return ResumeData(
        personal=master.personal,
        summary=Summary(content=tailored.summary) if tailored.summary else None,
        skills=[
            SkillCategory(category=c.category, items=list(c.items))
            for c in tailored.skills
        ],
        experience=[
            Experience(
                position=e.position,
                company=e.company,
                period=e.period,
                location=e.location,
                details=list(e.details),
            )
            for e in tailored.experience
        ],
        education=[Education(**e.model_dump()) for e in master.education],
        languages=list(master.languages),
    )


# --------------------------------------------------------------------------
# Output locations
# --------------------------------------------------------------------------

def slugify(value: str, fallback: str = "job") -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:48] or fallback


def output_dir_for(job: JobPosting, root: Path | None = None) -> Path:
    root = Path(root) if root else default_output_root()
    parts = [slugify(job.company, "")] if job.company else []
    if job.title:
        parts.append(slugify(job.title, ""))
    stem = "-".join(p for p in parts if p) or "application"
    date = _dt.date.today().isoformat()
    return root / f"{stem}-{date}"


# --------------------------------------------------------------------------
# Render + compile
# --------------------------------------------------------------------------

def render_resume(resume: ResumeData, destination: Path | str) -> CompileResult:
    """Render and compile a resume with no model involvement."""
    tex_source = render(RESUME_TEMPLATE, resume.model_dump())
    tex_path = write_tex(tex_source, destination)
    return compile_pdf(tex_path)


def _persist(out_dir: Path, job: JobPosting, resume: ResumeData,
             notes: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "job.txt").write_text(_tailor._job_block(job), encoding="utf-8")
    payload = resume.model_dump(exclude_none=True)
    payload["_tailoring_notes"] = notes
    (out_dir / "tailored.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------
# Public entry points
# --------------------------------------------------------------------------

def generate_tailored_resume(
    job: JobPosting,
    data_file: Path | str | None = None,
    out_dir: Path | str | None = None,
    max_pages: int = 2,
    model: str = _tailor.DEFAULT_MODEL,
    max_attempts: int = MAX_ATTEMPTS,
) -> GenerationResult:
    """Tailor, render, and compile -- retrying when the PDF runs long.

    The original script hard-failed at >2 pages. Because tailoring makes
    overflow likely, overflow is fed back to the model as a revision request
    instead, and only becomes a warning once the attempts are exhausted.
    """
    master = load_resume_data(data_file)
    target = Path(out_dir) if out_dir else output_dir_for(job)
    target.mkdir(parents=True, exist_ok=True)

    result = GenerationResult(ok=False, output_dir=target)
    feedback: str | None = None

    for attempt in range(1, max_attempts + 1):
        result.attempts = attempt

        tailored = _tailor.tailor_resume(
            master, job, model=model, max_pages=max_pages, feedback=feedback
        )

        try:
            validate_grounding(master, tailored)
        except GroundingError as exc:
            if attempt == max_attempts:
                result.errors.append(str(exc))
                return result
            feedback = (
                f"{exc}\n\nRegenerate using ONLY facts from the master resume. "
                f"Copy company, position and period fields character-for-character."
            )
            result.warnings.append(f"Attempt {attempt}: ungrounded output, retrying")
            continue

        resume = merge_tailored(master, tailored)
        result.tailoring_notes = list(tailored.tailoring_notes)
        _persist(target, job, resume, result.tailoring_notes)

        compiled = render_resume(resume, target / "resume.tex")
        if not compiled.ok:
            result.errors.extend(compiled.errors)
            result.tex_path = compiled.tex_path
            return result

        result.pdf_path = compiled.pdf_path
        result.tex_path = compiled.tex_path
        result.page_count = compiled.page_count

        if compiled.page_count is None or compiled.page_count <= max_pages:
            result.ok = True
            return result

        if attempt == max_attempts:
            result.ok = True
            result.warnings.append(
                f"Resume is {compiled.page_count} pages after {attempt} attempts "
                f"(target was {max_pages}). PDF kept -- trim it by hand or rerun."
            )
            return result

        feedback = (
            f"Your previous version rendered to {compiled.page_count} pages, but it "
            f"must fit {max_pages}. Cut roughly "
            f"{int(100 * (compiled.page_count - max_pages) / compiled.page_count)}% "
            f"of the total text: drop the least relevant bullets entirely rather "
            f"than shortening every bullet a little."
        )
        result.warnings.append(
            f"Attempt {attempt}: {compiled.page_count} pages, retrying with less content"
        )

    return result


def render_tailored_resume(
    tailored: TailoredResume,
    job: JobPosting,
    data_file: Path | str | None = None,
    out_dir: Path | str | None = None,
    max_pages: int = 2,
) -> GenerationResult:
    """Validate host-agent tailored content and render it to PDF.

    This path contains no model call. It is intended for MCP hosts such as
    Codex or Claude Code: the host agent reads the master resume, writes the
    tailored structured content with its own model access, and this function
    enforces grounding before rendering.
    """
    master = load_resume_data(data_file)
    target = Path(out_dir) if out_dir else output_dir_for(job)
    target.mkdir(parents=True, exist_ok=True)

    result = GenerationResult(
        ok=False,
        output_dir=target,
        attempts=1,
        tailoring_notes=list(tailored.tailoring_notes),
    )

    try:
        validate_grounding(master, tailored)
    except GroundingError as exc:
        result.errors.append(str(exc))
        return result

    resume = merge_tailored(master, tailored)
    _persist(target, job, resume, result.tailoring_notes)

    compiled = render_resume(resume, target / "resume.tex")
    result.tex_path = compiled.tex_path
    if not compiled.ok:
        result.errors.extend(compiled.errors)
        return result

    result.ok = True
    result.pdf_path = compiled.pdf_path
    result.page_count = compiled.page_count
    if compiled.page_count is not None and compiled.page_count > max_pages:
        result.warnings.append(
            f"Resume is {compiled.page_count} pages (target was {max_pages}). "
            "Ask the host agent to trim tailored content and call this tool again."
        )
    return result


def generate_cover_letter(
    job: JobPosting,
    data_file: Path | str | None = None,
    out_dir: Path | str | None = None,
    model: str = _tailor.DEFAULT_MODEL,
) -> GenerationResult:
    """Generate and compile a cover letter matching the resume's styling."""
    master = load_resume_data(data_file)
    target = Path(out_dir) if out_dir else output_dir_for(job)
    target.mkdir(parents=True, exist_ok=True)

    result = GenerationResult(ok=False, output_dir=target, attempts=1)
    letter: CoverLetterContent = _tailor.write_cover_letter(master, job, model=model)

    context = {
        "personal": master.personal.model_dump(),
        "job": job.model_dump(),
        "letter": letter.model_dump(),
        "date": _dt.date.today().strftime("%B %-d, %Y"),
    }
    tex_source = render(COVER_LETTER_TEMPLATE, context)
    tex_path = write_tex(tex_source, target / "cover_letter.tex")
    compiled = compile_pdf(tex_path)

    result.tex_path = compiled.tex_path
    if not compiled.ok:
        result.errors.extend(compiled.errors)
        return result

    (target / "cover_letter.txt").write_text(
        "\n\n".join([letter.greeting, *letter.paragraphs, letter.closing,
                     master.personal.name]),
        encoding="utf-8",
    )
    result.ok = True
    result.pdf_path = compiled.pdf_path
    result.page_count = compiled.page_count
    return result
