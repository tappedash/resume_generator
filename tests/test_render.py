import shutil

import pytest

from resume_generator.render import render
from resume_generator.schema import Experience, Personal, ResumeData, Summary

needs_latex = pytest.mark.skipif(
    shutil.which("xelatex") is None, reason="xelatex is not installed"
)


def _render(resume):
    return render("faang_resume.tex.j2", resume.model_dump())


def test_master_resume_renders_a_complete_document(master):
    tex = _render(master)
    assert tex.startswith("\\documentclass")
    assert tex.rstrip().endswith("\\end{document}")
    assert master.personal.name in tex


def test_languages_come_from_data_not_the_template(master):
    tex = _render(master)
    for language in master.languages:
        assert language.name in tex
    # Arabic is in the YAML; the old template hardcoded only English + French.
    assert "Arabic" in tex


def test_summary_section_only_appears_when_present(master):
    assert "Professional Summary" not in _render(master)
    master.summary = Summary(content="Backend engineer.")
    assert "Professional Summary" in _render(master)


def test_special_characters_in_data_are_escaped():
    resume = ResumeData(
        personal=Personal(name="A & B"),
        experience=[
            Experience(position="Dev", company="C_o", details=["Cut costs 50%"])
        ],
    )
    tex = _render(resume)
    assert "A \\& B" in tex
    assert "C\\_o" in tex
    assert "50\\%" in tex


def test_empty_sections_are_omitted():
    tex = _render(ResumeData(personal=Personal(name="Solo")))
    assert "Work Experience" not in tex
    assert "Languages" not in tex


def test_shared_preamble_is_included():
    tex = _render(ResumeData(personal=Personal(name="X")))
    assert "\\newcommand{\\resumesection}" in tex
    assert "fontspec" in tex


@needs_latex
def test_master_resume_compiles_to_two_pages(master, tmp_path):
    from resume_generator.pipeline import render_resume

    result = render_resume(master, tmp_path / "resume.tex")
    assert result.ok, result.errors
    assert result.pdf_path.exists()
    assert result.page_count == 2


# --------------------------------------------------------------------------
# Cover letter
# --------------------------------------------------------------------------

def _letter_context(master):
    return {
        "personal": master.personal.model_dump(),
        "job": {"company": "Trend Micro", "title": "Senior Backend Developer"},
        "letter": {
            "greeting": "Dear Hiring Manager,",
            "paragraphs": [
                "First paragraph about the role & the team.",
                "Second paragraph with 100% concrete detail.",
                "Third paragraph.",
            ],
            "closing": "Sincerely,",
        },
        "date": "September 9, 2026",
    }


def test_cover_letter_renders_all_content(master):
    tex = render("cover_letter.tex.j2", _letter_context(master))
    assert "Dear Hiring Manager," in tex
    assert "Trend Micro" in tex
    assert "Re: Senior Backend Developer" in tex
    assert "September 9, 2026" in tex
    assert master.personal.name in tex
    assert "100\\%" in tex  # escaped, not raw


def test_cover_letter_shares_the_resume_preamble(master):
    letter = render("cover_letter.tex.j2", _letter_context(master))
    resume = _render(master)
    preamble = "\\newcommand{\\contactsep}"
    assert preamble in letter and preamble in resume
    assert "TeX Gyre Heros" in letter  # same font fallback as the resume


@needs_latex
def test_cover_letter_compiles_to_one_page(master, tmp_path):
    from resume_generator.compile import compile_pdf
    from resume_generator.render import write_tex

    tex = render("cover_letter.tex.j2", _letter_context(master))
    result = compile_pdf(write_tex(tex, tmp_path / "cover_letter.tex"))
    assert result.ok, result.errors
    assert result.page_count == 1
