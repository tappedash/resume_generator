"""Command line interface: resume-gen <command>."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .data import load_resume_data
from .paths import build_dir
from .pipeline import (
    GenerationResult,
    generate_cover_letter,
    generate_tailored_resume,
    output_dir_for,
    render_resume,
)
from .schema import JobPosting


def _read_job(args) -> JobPosting:
    if args.job:
        text = Path(args.job).read_text(encoding="utf-8", errors="replace")
    else:
        if sys.stdin.isatty():
            raise SystemExit("Provide --job FILE or pipe the description on stdin.")
        text = sys.stdin.read()

    if not text.strip():
        raise SystemExit("The job description is empty.")

    return JobPosting(
        description=text.strip(),
        title=args.title or "",
        company=args.company or "",
        url=args.url or "",
    )


def _report(result: GenerationResult) -> int:
    for note in result.tailoring_notes:
        print(f"  · {note}")
    for warning in result.warnings:
        print(f"  ! {warning}", file=sys.stderr)
    for error in result.errors:
        print(f"  ✗ {error}", file=sys.stderr)

    if result.ok and result.pdf_path:
        pages = f" ({result.page_count} pages)" if result.page_count else ""
        print(f"\n→ {result.pdf_path}{pages}")
        print(f"  output dir: {result.output_dir}")
        return 0

    print("\nFailed. See the errors above and latex.log in the output directory.",
          file=sys.stderr)
    return 1


def _cmd_render(args) -> int:
    resume = load_resume_data(args.data_file)
    destination = Path(args.out) if args.out else build_dir() / "resume.tex"
    result = render_resume(resume, destination)
    print(result.summary())
    return 0 if result.ok else 1


def _cmd_tailor(args) -> int:
    job = _read_job(args)
    print(f"Tailoring resume for {job.label()} …")
    return _report(
        generate_tailored_resume(
            job,
            data_file=args.data_file,
            out_dir=args.out,
            max_pages=args.max_pages,
            model=args.model,
        )
    )


def _cmd_cover_letter(args) -> int:
    job = _read_job(args)
    print(f"Writing cover letter for {job.label()} …")
    return _report(
        generate_cover_letter(
            job, data_file=args.data_file, out_dir=args.out, model=args.model
        )
    )


def _cmd_apply(args) -> int:
    """Resume and cover letter for the same job, into one directory."""
    job = _read_job(args)
    target = Path(args.out) if args.out else output_dir_for(job)
    print(f"Preparing application for {job.label()} …")

    resume = generate_tailored_resume(
        job, data_file=args.data_file, out_dir=target,
        max_pages=args.max_pages, model=args.model,
    )
    code = _report(resume)
    if code != 0:
        return code

    print("\nCover letter …")
    return _report(
        generate_cover_letter(job, data_file=args.data_file, out_dir=target,
                              model=args.model)
    )


def _cmd_serve(args) -> int:
    from .mcp_server import main as serve

    serve()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-gen",
        description="Generate tailored resumes and cover letters from a master YAML.",
    )
    parser.add_argument("--data-file", default=None,
                        help="Master resume YAML (default: data/resume_data_en_faang.yaml)")
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="Render the master resume as-is (no API call)")
    render.add_argument("--out", default=None, help="Output .tex path")
    render.set_defaults(func=_cmd_render)

    def add_job_args(p, with_pages=False):
        p.add_argument("--job", default=None, help="File holding the job description")
        p.add_argument("--title", default=None)
        p.add_argument("--company", default=None)
        p.add_argument("--url", default=None)
        p.add_argument("--out", default=None, help="Output directory")
        p.add_argument("--model", default="claude-opus-5")
        if with_pages:
            p.add_argument("--max-pages", type=int, default=2)

    tailor = sub.add_parser("tailor", help="Tailor the resume to a job description")
    add_job_args(tailor, with_pages=True)
    tailor.set_defaults(func=_cmd_tailor)

    letter = sub.add_parser("cover-letter", help="Write a cover letter for a job")
    add_job_args(letter)
    letter.set_defaults(func=_cmd_cover_letter)

    apply_cmd = sub.add_parser("apply", help="Tailored resume + cover letter together")
    add_job_args(apply_cmd, with_pages=True)
    apply_cmd.set_defaults(func=_cmd_apply)

    serve = sub.add_parser("serve", help="Run the MCP server over stdio")
    serve.set_defaults(func=_cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
