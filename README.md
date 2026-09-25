# Resume Generator

Tailors a master YAML resume to a specific job description and renders it to PDF
through LaTeX. Usable three ways: as an **MCP server** (call it from Codex,
Claude Code, or another MCP host), as a **CLI**, or as a **Python package**.

```
data/resume_data_en_faang.yaml   master resume — the single source of truth
templates/faang/                 LaTeX/Jinja2 templates (resume + cover letter)
src/resume_generator/            the package
output/<company>-<role>-<date>/  generated applications (gitignored)
```

## Setup

Requires Python 3.10+ and a LaTeX distribution providing `xelatex` (MacTeX on macOS).
`pdfinfo` (poppler) is optional and enables page-count checking.

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

## CLI

```bash
resume-gen render                                   # master resume as-is, no API call
resume-gen tailor --job posting.txt --company "Trend Micro" --title "Backend Dev"
resume-gen cover-letter --job posting.txt --company "Trend Micro"
resume-gen apply --job posting.txt --company "Trend Micro"   # both, one folder
resume-gen serve                                    # MCP server over stdio
```

The job description can also be piped: `pbpaste | resume-gen tailor --company Acme`.

## MCP server

`.mcp.json` in this repo registers the server for Claude Code. Restart Claude Code,
then just paste a job description and ask for a tailored resume.

| Tool | API call? | Does |
|---|---|---|
| `get_master_resume` | no | Returns the master resume as JSON |
| `tailor_resume` | no | Returns the master resume, job posting, and instructions for the host agent |
| `render_tailored_resume` | no | Validates host-agent tailored content and renders the resume PDF |
| `generate_cover_letter` | yes | Job description → cover letter PDF + `.txt` |
| `render_resume` | no | Renders resume data you supply directly |

Normal MCP resume tailoring does not need an API key inside this server. Codex,
Claude Code, or another host uses its own model access to write the tailored
structured content, then calls `render_tailored_resume`. Each render writes
`resume.pdf`, `tailored.yaml` (what the host agent produced), `job.txt`, and
`latex.log` into the output folder.

## How tailoring is kept honest

The model may select, reorder, compress and reword material that is already in the
master resume. It may not invent anything. Two things enforce this:

1. A system prompt that spells out the boundary explicitly.
2. `validate_grounding()` — every employer, job title, date range and skill in the
   output is checked against the master resume before anything is rendered. A
   mismatch is fed back to the model as a revision request, and aborts the run if it
   repeats.

Bullet *wording* is deliberately not checked, since rewording is the point. That is
why `tailored.yaml` is written on every run: **read it before you send the PDF.**

If the rendered PDF exceeds `--max-pages` (default 2), the page count is fed back to
the model to cut content, up to 3 attempts. If it still overflows the PDF is kept and
a warning is printed rather than failing outright.

To correct a tailored resume by hand, edit `tailored.yaml` and re-render it with the
`render_resume` MCP tool — no API call, no re-tailoring.

## Editing your resume

`data/resume_data_en_faang.yaml` is the only file to edit for content. Top-level keys:
`personal`, `summary` (optional), `skills`, `experience`, `education`, `languages`.
Anything not listed there can never appear in a generated resume.

For another user, create a YAML file with the same shape and either:

```bash
export RESUME_GENERATOR_DATA_FILE=/absolute/path/to/my-resume.yaml
```

or replace `data/resume_data_en_faang.yaml` in your local checkout. The first
option is better when several people share the same codebase or when you want
your personal data outside the repository. The YAML should contain their name,
email, phone, location, LinkedIn, GitHub, work authorization, skills, work
experience, education, and languages.

## Development

```bash
.venv/bin/pytest              # LaTeX-dependent tests skip if xelatex is absent
```

No test spends API credits — the Claude calls are stubbed.

## Troubleshooting

- **Compilation fails** — read `latex.log` in the output directory.
- **`xelatex not found`** — install MacTeX, or add `/Library/TeX/texbin` to `PATH`.
- **Missing page counts** — install poppler (`brew install poppler`).
- **Running the package from outside the repo** — set `RESUME_GENERATOR_ROOT` to the
  repo path so templates and data resolve.
