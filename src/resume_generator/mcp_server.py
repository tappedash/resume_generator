# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""MCP server exposing the resume generator to Codex, Claude Code, and peers.

Run with ``resume-gen serve`` (stdio transport).

The normal MCP flow needs no model API key in this process. The host agent
uses its own model access to tailor content, then calls this server to validate
and render the PDF. Legacy CLI code can still perform provider-backed tailoring
outside this MCP handoff.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import pipeline
from .data import load_resume_data
from .paths import default_data_file
from .schema import JobPosting, ResumeData, TailoredResume

mcp = MCPServer("resume-generator")


def _job(description: str, company: str, job_title: str, url: str) -> JobPosting:
    # ToolError text reaches the caller; other exceptions are replaced by a
    # generic message, so every expected failure is raised as a ToolError.
    if not description or not description.strip():
        raise ToolError("job_description is required and must not be empty.")
    return JobPosting(
        description=description.strip(),
        title=job_title or "",
        company=company or "",
        url=url or "",
    )


@mcp.tool()
def get_master_resume() -> dict[str, Any]:
    """Return the master resume as JSON.

    Use this first to see which employers, roles, skills and dates actually
    exist before asking for a tailored version -- the tailoring tools refuse
    any content that is not grounded in this data.
    """
    resume = load_resume_data()
    return {
        "source_file": str(default_data_file()),
        "resume": resume.model_dump(exclude_none=True),
    }


@mcp.tool()
def tailor_resume(
    job_description: str,
    company: str = "",
    job_title: str = "",
    url: str = "",
    max_pages: int = 2,
    output_dir: str = "",
) -> dict[str, Any]:
    """Prepare a no API key, host-agent tailored resume workflow.

    Codex, Claude Code, or another MCP host should use its own model access to
    tailor the resume. This tool returns the same master facts as
    get_master_resume, the job posting, and the exact next tool name. The host
    should:

    1. read the returned master_resume facts,
    2. produce a TailoredResume-shaped object using only those facts,
    3. call render_tailored_resume with that object.

    render_tailored_resume validates grounding before rendering, so invented
    employers, dates, and skills are rejected before a PDF is produced.

    Args:
        job_description: The full text of the job posting. Required.
        company: Hiring company, used for the output folder name and the prompt.
        job_title: Role title, used for the output folder name and the prompt.
        url: Link to the posting, recorded alongside the output.
        max_pages: Page ceiling to pass to render_tailored_resume.
        output_dir: Output directory to pass to render_tailored_resume.
    """
    job = _job(job_description, company, job_title, url)
    resume = load_resume_data()
    return {
        "ok": False,
        "needs_agent_tailoring": True,
        "next_tool": "render_tailored_resume",
        "instructions": [
            "Tailor the returned master_resume using the host model, not an API key inside this MCP server.",
            "Use only facts present in master_resume; do not invent employers, dates, schools, metrics, or skills.",
            "Copy company, position, period, and location fields character-for-character for each included role.",
            "Call render_tailored_resume with the tailored object, the same job fields, max_pages, and output_dir.",
        ],
        "job": job.model_dump(),
        "master_resume": resume.model_dump(exclude_none=True),
        "max_pages": max_pages,
        "output_dir": output_dir,
        "tailored_schema": {
            "summary": "string",
            "skills": [{"category": "string", "items": ["existing skill"]}],
            "experience": [
                {
                    "company": "copy from master_resume",
                    "position": "copy from master_resume",
                    "period": "copy from master_resume",
                    "location": "copy from master_resume",
                    "details": ["reworded bullets grounded in the role"],
                }
            ],
            "tailoring_notes": ["short review note"],
        },
    }


@mcp.tool()
def render_tailored_resume(
    tailored: dict[str, Any],
    job_description: str,
    company: str = "",
    job_title: str = "",
    url: str = "",
    max_pages: int = 2,
    output_dir: str = "",
) -> dict[str, Any]:
    """Validate host-agent tailored content and render the resume PDF.

    This tool makes no model/API call. Use it after Codex, Claude Code, or
    another MCP host has written a tailored resume from get_master_resume or
    tailor_resume output. The tailored data must match TailoredResume shape:
    summary, skills, experience, and tailoring_notes. Before rendering, the
    content is checked against the master resume so invented employers, altered
    role identity fields, and skills absent from the master resume are rejected.

    Args:
        tailored: Host-agent produced TailoredResume-shaped data.
        job_description: The full text of the job posting. Required.
        company: Hiring company, used for the output folder name and job audit.
        job_title: Role title, used for the output folder name and job audit.
        url: Link to the posting, recorded alongside the output.
        max_pages: Page ceiling for warnings. Defaults to 2.
        output_dir: Where to write. Defaults to output/<company>-<role>-<date>/.
    """
    try:
        data = TailoredResume.model_validate(tailored)
    except ValidationError as exc:
        raise ToolError(
            "The tailored data does not match the expected shape "
            "(see tailor_resume for the schema):\n"
            f"{exc}"
        ) from exc

    result = pipeline.render_tailored_resume(
        data,
        _job(job_description, company, job_title, url),
        out_dir=Path(output_dir) if output_dir else None,
        max_pages=max_pages,
    )
    return result.as_dict()


@mcp.tool()
def generate_cover_letter(
    job_description: str,
    company: str = "",
    job_title: str = "",
    url: str = "",
    output_dir: str = "",
) -> dict[str, Any]:
    """Write a cover letter for a job and render it to PDF.

    Uses the same typography as the resume. The letter body is also written as
    plain text (cover_letter.txt) for pasting into application forms.

    Args:
        job_description: The full text of the job posting. Required.
        company: Hiring company, addressed in the letter.
        job_title: Role title, referenced in the letter.
        url: Link to the posting, recorded alongside the output.
        output_dir: Where to write. Defaults to output/<company>-<role>-<date>/.
    """
    result = pipeline.generate_cover_letter(
        _job(job_description, company, job_title, url),
        out_dir=Path(output_dir) if output_dir else None,
    )
    return result.as_dict()


@mcp.tool()
def render_resume(resume: dict[str, Any], output_dir: str = "") -> dict[str, Any]:
    """Render resume data you supply directly to PDF -- no API call, no tailoring.

    Use this to correct a tailored resume by hand: read tailored.yaml, edit the
    parts you disagree with, and pass the result here. The data must match the
    shape returned by get_master_resume (personal, summary, skills, experience,
    education, languages).

    Args:
        resume: Resume data in master-resume shape.
        output_dir: Where to write. Defaults to output/manual-render/.
    """
    try:
        data = ResumeData.model_validate(resume)
    except ValidationError as exc:
        raise ToolError(
            "The resume data does not match the expected shape "
            f"(see get_master_resume for a valid example):\n{exc}"
        ) from exc

    target = Path(output_dir) if output_dir else pipeline.default_output_root() / "manual-render"
    target.mkdir(parents=True, exist_ok=True)

    compiled = pipeline.render_resume(data, target / "resume.tex")
    return {
        "ok": compiled.ok,
        "pdf_path": str(compiled.pdf_path) if compiled.pdf_path else None,
        "tex_path": str(compiled.tex_path),
        "page_count": compiled.page_count,
        "errors": compiled.errors,
        "output_dir": str(target),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
