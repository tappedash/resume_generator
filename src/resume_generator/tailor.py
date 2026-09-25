# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""Claude API calls that produce tailored resume content and cover letters.

This module knows nothing about LaTeX or PDFs. It takes a master resume plus a
job posting and returns validated structured content.
"""

from __future__ import annotations

import functools

import yaml

from .schema import CoverLetterContent, JobPosting, ResumeData, TailoredResume

DEFAULT_MODEL = "claude-opus-5"
MAX_TOKENS = 16000

# The single most important instruction in this project. A resume that invents
# an employer or a metric is actively harmful to the person submitting it, so
# the boundary between "rewrite" and "invent" is spelled out explicitly and
# re-checked in code by pipeline.validate_grounding.
_GROUNDING_RULES = """\
You are tailoring a real person's resume for a real job application. Everything \
you write will be submitted to an employer under their name.

You MAY:
- Select which roles, bullets and skill categories to include, and drop the rest.
- Reorder anything so the most relevant material appears first.
- Reword and compress bullets to use the vocabulary of the job description.
- Merge two bullets that describe the same work into one tighter bullet.
- Write a short professional summary that synthesises facts already present.

You MUST NOT:
- Invent or alter an employer, job title, date range, location, degree or school.
- Add a technology, tool, language or framework the master resume does not list.
- Invent metrics, percentages, team sizes, dollar amounts or dates.
- Upgrade the level of a claim (e.g. "contributed to" -> "led", "used" -> "designed").
- Claim experience the master resume does not support, however well it fits the job.

The `company`, `position`, `period` and `location` fields of each experience \
entry must be copied CHARACTER-FOR-CHARACTER from the master resume. They are \
verified programmatically and a mismatch aborts the whole run."""


@functools.lru_cache(maxsize=1)
def _client():
    import anthropic

    return anthropic.Anthropic()


def _master_yaml(master: ResumeData) -> str:
    return yaml.safe_dump(
        master.model_dump(exclude_none=True), sort_keys=False, allow_unicode=True
    )


def _job_block(job: JobPosting) -> str:
    header = []
    if job.title:
        header.append(f"Title: {job.title}")
    if job.company:
        header.append(f"Company: {job.company}")
    if job.url:
        header.append(f"URL: {job.url}")
    prefix = "\n".join(header)
    return f"{prefix}\n\n{job.description}" if prefix else job.description


def tailor_resume(
    master: ResumeData,
    job: JobPosting,
    model: str = DEFAULT_MODEL,
    max_pages: int = 2,
    feedback: str | None = None,
) -> TailoredResume:
    """Ask Claude to select and reword master-resume content for ``job``.

    ``feedback`` carries the page-overflow message on retry attempts.
    """
    system = f"""{_GROUNDING_RULES}

Length target: the rendered PDF must fit on {max_pages} page(s) at 9.8pt. That is \
roughly {max_pages * 500} words total. Prefer fewer, stronger bullets over \
complete coverage -- 4-6 bullets for the most relevant role, 2-4 for older or \
less relevant ones, and drop roles that add nothing for this job.

Write `tailoring_notes` as 3-6 short lines telling the applicant what you \
changed and why, so they can review your edits. Mention anything the job asks \
for that the master resume does not cover."""

    user = f"""Here is the master resume:

<master_resume>
{_master_yaml(master)}
</master_resume>

Here is the job posting:

<job_posting>
{_job_block(job)}
</job_posting>

Produce the tailored resume content for {job.label()}."""

    if feedback:
        user += f"\n\n<revision_request>\n{feedback}\n</revision_request>"

    response = _client().messages.parse(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=TailoredResume,
    )
    return response.parsed_output


def write_cover_letter(
    master: ResumeData,
    job: JobPosting,
    model: str = DEFAULT_MODEL,
) -> CoverLetterContent:
    """Generate cover letter body text grounded in the master resume."""
    system = f"""{_GROUNDING_RULES}

You are writing a cover letter body. Produce 3-4 paragraphs, roughly 250-350 \
words total:
1. Why this role and this company, naming something concrete from the posting.
2. The single most relevant piece of experience, in specifics.
3. A second supporting thread -- a different skill area or a distinct project.
4. A short close.

Write plainly and in the first person. No bullet points, no markdown, no \
placeholders like [Company]. If you do not know the hiring manager's name, use \
"Dear Hiring Manager,". Do not restate the resume line by line, and do not open \
with "I am writing to apply for"."""

    user = f"""Here is the master resume:

<master_resume>
{_master_yaml(master)}
</master_resume>

Here is the job posting:

<job_posting>
{_job_block(job)}
</job_posting>

Write the cover letter for {job.label()}."""

    response = _client().messages.parse(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=CoverLetterContent,
    )
    return response.parsed_output
