# Resume Generator

AI-assisted resume generator for tailoring a YAML master resume to job
descriptions and rendering ATS-friendly PDF resumes and cover letters with
LaTeX. It can run as a command-line tool, a Python package, or a local MCP
server for Codex, Claude Code, and other MCP-compatible agents.

Keywords: AI resume generator, ATS resume builder, tailored resume PDF, YAML
resume, LaTeX resume generator, MCP server, Codex MCP, Claude Code MCP,
cover letter generator.

## What It Does

- Keeps resume facts in one structured YAML file.
- Tailors resumes to job descriptions while grounding output in the master
  resume.
- Renders clean PDF resumes and cover letters through XeLaTeX.
- Exposes MCP tools so coding agents can generate resumes from chat.
- Supports no-API host-agent tailoring: Codex or Claude Code can write the
  tailored content, then this server validates and renders it.
- Writes audit files such as `tailored.yaml`, `job.txt`, and LaTeX logs so you
  can review what was generated before sending a resume.

## Repository Layout

```text
data/resume_data_en_faang.yaml   Sample master resume data
templates/faang/                 LaTeX/Jinja2 resume and cover letter templates
src/resume_generator/            Python package, CLI, pipeline, and MCP server
tests/                           Unit and integration tests
output/                          Generated applications, gitignored by default
```

## Requirements

- Python 3.10+
- A LaTeX distribution that provides `xelatex`
  - macOS: MacTeX or BasicTeX
  - Linux: TeX Live packages that include XeLaTeX
  - Windows: MiKTeX or TeX Live
- Optional: `pdfinfo` from Poppler for page-count checks
- Optional for provider-backed CLI tailoring: `ANTHROPIC_API_KEY`

The MCP workflow does not require an API key inside this server when the host
agent, such as Codex or Claude Code, performs the tailoring.

## Quick Start

Clone the project:

```bash
git clone https://github.com/tappedash/resume_generator.git
cd resume_generator
```

Create a virtual environment and install the package:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Verify the install:

```bash
.venv/bin/resume-gen --help
.venv/bin/pytest
```

Render the sample master resume:

```bash
.venv/bin/resume-gen render --out output/sample-resume.tex
```

The render command writes a `.tex` file and compiles a sibling `.pdf`.

## Add Your Resume Data

The default data file is:

```text
data/resume_data_en_faang.yaml
```

For public or shared repositories, keep personal data outside the repo and point
the tool to your private YAML:

```bash
cp data/resume_data_en_faang.yaml ~/my-resume.yaml
export RESUME_GENERATOR_DATA_FILE="$HOME/my-resume.yaml"
```

You can also pass a data file per command:

```bash
.venv/bin/resume-gen --data-file ~/my-resume.yaml render --out output/resume.tex
```

The YAML supports:

- `personal`
- `summary` (optional)
- `skills`
- `experience`
- `education`
- `languages`

Anything absent from the master YAML cannot appear in validated tailored
resumes.

## CLI Usage

### Render the Master Resume

```bash
.venv/bin/resume-gen render --out output/master-resume.tex
```

### Tailor a Resume From a Job Posting File

```bash
.venv/bin/resume-gen tailor \
  --job job-posting.txt \
  --company "Example Corp" \
  --title "Backend Engineer" \
  --out output/example-corp-backend-engineer
```

### Tailor a Resume From Stdin

```bash
pbpaste | .venv/bin/resume-gen tailor \
  --company "Example Corp" \
  --title "Backend Engineer"
```

On Linux, replace `pbpaste` with your clipboard or pipe source.

### Generate a Cover Letter

```bash
.venv/bin/resume-gen cover-letter \
  --job job-posting.txt \
  --company "Example Corp" \
  --title "Backend Engineer" \
  --out output/example-corp-cover-letter
```

### Generate Both Resume and Cover Letter

```bash
.venv/bin/resume-gen apply \
  --job job-posting.txt \
  --company "Example Corp" \
  --title "Backend Engineer" \
  --out output/example-corp-application
```

### Useful CLI Flags

```text
--data-file PATH     Use a custom master resume YAML
--job PATH           Read the job description from a file
--company TEXT       Hiring company
--title TEXT         Role title
--url URL            Job posting URL
--out PATH           Output directory, or .tex path for render
--max-pages N        Resume page target for tailoring, default 2
--model TEXT         Model name for provider-backed CLI tailoring
```

## MCP Server Usage

Run the local MCP server over stdio:

```bash
.venv/bin/resume-gen serve
```

The MCP server exposes these tools:

| Tool | API call inside server? | Purpose |
|---|---:|---|
| `get_master_resume` | No | Return the master resume as JSON |
| `tailor_resume` | No | Return the job, master facts, and next-step instructions for host-agent tailoring |
| `render_tailored_resume` | No | Validate host-agent tailored content and render a PDF |
| `render_resume` | No | Render supplied resume-shaped data directly to PDF |
| `generate_cover_letter` | Yes | Generate and render a cover letter |

The common MCP flow is:

1. The host agent calls `get_master_resume` or `tailor_resume`.
2. The host agent writes a `TailoredResume` object using only master-resume
   facts.
3. The host agent calls `render_tailored_resume`.
4. The MCP server validates grounding and renders the PDF.

## Codex Setup

OpenAI documentation says Codex can connect to MCP servers through the CLI or
IDE extension and verify them with `codex mcp list`. See the OpenAI Docs MCP
guide for current Codex MCP configuration details:
https://developers.openai.com/learn/docs-mcp

From this repository, install the package first:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Add the local MCP server to Codex:

```bash
codex mcp add resume-generator -- "$(pwd)/.venv/bin/resume-gen" serve
```

Verify it:

```bash
codex mcp list
codex mcp get resume-generator
```

Example Codex prompt:

```text
Use the resume-generator MCP server. Tailor my resume for this job description,
render a 2-page PDF, and use only facts present in the master resume.

<paste job description>
```

If you use a private resume YAML outside the repo, configure the MCP server with
that environment variable in Codex:

```toml
[mcp_servers.resume-generator]
command = "/absolute/path/to/resume_generator/.venv/bin/resume-gen"
args = ["serve"]

[mcp_servers.resume-generator.env]
RESUME_GENERATOR_DATA_FILE = "/absolute/path/to/my-resume.yaml"
```

## Claude Code Setup

Claude Code supports MCP servers. Anthropic's Claude Code docs cover
installation, `claude doctor`, and MCP commands:

- Setup: https://docs.anthropic.com/en/docs/claude-code/getting-started
- MCP overview: https://docs.anthropic.com/en/docs/mcp
- CLI reference: https://docs.anthropic.com/en/docs/claude-code/cli-usage

Install this project:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

Add the MCP server to Claude Code:

```bash
claude mcp add resume-generator -- "$(pwd)/.venv/bin/resume-gen" serve
```

Verify it:

```bash
claude mcp list
```

Inside Claude Code, you can also run:

```text
/mcp
```

Example Claude Code prompt:

```text
Use the resume-generator MCP tools to tailor my resume for this posting.
First inspect the master resume facts, then render a PDF. Do not invent
employers, dates, schools, or skills.

<paste job description>
```

### Project `.mcp.json`

This repository includes a `.mcp.json` for project-level MCP configuration:

```json
{
  "mcpServers": {
    "resume-generator": {
      "command": "resume-gen",
      "args": ["serve"]
    }
  }
}
```

This works when `resume-gen` is available on the host process PATH. For the most
predictable setup, use the explicit `.venv/bin/resume-gen` command shown above.

## Output Files

Generated application folders usually contain:

```text
resume.pdf          Final resume PDF
resume.tex          Rendered LaTeX source
tailored.yaml       Tailored resume content for review
job.txt             Job posting audit copy
latex.log           Short compile log
*.aux, *.out, *.xdv LaTeX build artifacts
```

`output/` is gitignored by default. If you want only final PDFs in another
folder, copy or move `resume.pdf` after generation.

## Grounding and Safety

The project is intentionally conservative:

- Employer, position, and period fields must match the master resume.
- Skills must already exist in the master resume.
- Education, languages, and personal details are copied from the master resume,
  not generated by the model.
- Reworded bullets are allowed because tailoring is the point.

This reduces hallucinated credentials while still letting the model reorder,
compress, and emphasize relevant experience.

Always review `tailored.yaml` and the final PDF before sending an application.

## Development

Run the tests:

```bash
.venv/bin/pytest
```

Run a single test file:

```bash
.venv/bin/pytest tests/test_mcp_server.py
```

No test spends API credits. Model calls are stubbed in tests.

## Troubleshooting

### `xelatex not found`

Install a LaTeX distribution and make sure `xelatex` is on PATH.

macOS examples:

```bash
brew install --cask mactex
```

or install BasicTeX and the required packages manually.

### Page count is missing

Install Poppler so `pdfinfo` is available:

```bash
brew install poppler
```

### MCP server starts but tools cannot find your resume

Use an absolute data-file path:

```bash
export RESUME_GENERATOR_DATA_FILE=/absolute/path/to/my-resume.yaml
```

For Codex or Claude Code MCP configs, add that variable to the MCP server
environment.

### Claude Code or Codex cannot find `resume-gen`

Use the absolute virtualenv executable:

```bash
/absolute/path/to/resume_generator/.venv/bin/resume-gen serve
```

### The tailored resume contains something wrong

Edit `tailored.yaml` by hand and call `render_resume`, or ask your MCP host to
produce a corrected `TailoredResume` object and call `render_tailored_resume`
again.

## GitHub Discoverability

Suggested repository description:

```text
AI-assisted resume generator that tailors a YAML master resume to job descriptions and renders ATS-friendly PDFs via LaTeX, with CLI and MCP server support.
```

Suggested GitHub topics:

```text
ai-resume-generator
ats-resume
resume-builder
resume-generator
cover-letter-generator
yaml-resume
latex-resume
mcp-server
codex
claude-code
python
jinja2
xelatex
job-search
career-tools
```

## License

MIT License. See [LICENSE](LICENSE).
