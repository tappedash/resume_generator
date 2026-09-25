# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""Retry-loop and orchestration behaviour, with the API call stubbed out.

No test in this file spends API credits.
"""

from pathlib import Path

import pytest
import yaml

from resume_generator import pipeline
from resume_generator.compile import CompileResult
from resume_generator.schema import TailoredSkillCategory


@pytest.fixture
def stub(monkeypatch, grounded_tailored):
    """Stub the model call and the LaTeX compile; record what each attempt saw."""

    calls = {"tailor": [], "render": 0}
    state = {"tailored": grounded_tailored, "pages": [2]}

    def fake_tailor(master, job, model=None, max_pages=2, feedback=None):
        calls["tailor"].append(feedback)
        return state["tailored"]

    def fake_render(resume, destination):
        index = min(calls["render"], len(state["pages"]) - 1)
        pages = state["pages"][index]
        calls["render"] += 1
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("stub")
        pdf = path.with_suffix(".pdf")
        pdf.write_bytes(b"%PDF-stub")
        return CompileResult(True, pdf, pages, "log", path)

    monkeypatch.setattr(pipeline._tailor, "tailor_resume", fake_tailor)
    monkeypatch.setattr(pipeline, "render_resume", fake_render)
    return calls, state


def test_fitting_resume_succeeds_on_first_attempt(stub, job, tmp_path):
    calls, _ = stub
    result = pipeline.generate_tailored_resume(job, out_dir=tmp_path)

    assert result.ok
    assert result.attempts == 1
    assert result.page_count == 2
    assert calls["tailor"] == [None]  # no revision feedback needed
    assert result.tailoring_notes


def test_overflowing_resume_is_retried_with_feedback(stub, job, tmp_path):
    calls, state = stub
    state["pages"] = [4, 2]  # too long, then fixed

    result = pipeline.generate_tailored_resume(job, out_dir=tmp_path)

    assert result.ok
    assert result.attempts == 2
    assert result.page_count == 2
    assert calls["tailor"][0] is None
    assert "4 pages" in calls["tailor"][1]
    assert any("retrying" in w for w in result.warnings)


def test_persistent_overflow_keeps_the_pdf_and_warns(stub, job, tmp_path):
    _, state = stub
    state["pages"] = [5]

    result = pipeline.generate_tailored_resume(job, out_dir=tmp_path, max_attempts=2)

    assert result.ok  # a long PDF beats no PDF
    assert result.page_count == 5
    assert any("after 2 attempts" in w for w in result.warnings)


def test_max_pages_is_respected(stub, job, tmp_path):
    _, state = stub
    state["pages"] = [3]

    assert pipeline.generate_tailored_resume(
        job, out_dir=tmp_path, max_pages=3
    ).attempts == 1


def test_ungrounded_output_is_retried_then_fails(stub, job, tmp_path):
    calls, state = stub
    state["tailored"].skills.append(
        TailoredSkillCategory(category="X", items=["Fortran"])
    )

    result = pipeline.generate_tailored_resume(job, out_dir=tmp_path, max_attempts=2)

    assert not result.ok
    assert "Fortran" in " ".join(result.errors)
    assert calls["render"] == 0  # never rendered ungrounded content
    assert "Fortran" in calls["tailor"][1]  # the violation was fed back


def test_run_writes_a_reviewable_audit_trail(stub, job, tmp_path):
    pipeline.generate_tailored_resume(job, out_dir=tmp_path)

    assert (tmp_path / "job.txt").read_text().strip().endswith("AWS.")
    saved = yaml.safe_load((tmp_path / "tailored.yaml").read_text())
    assert saved["_tailoring_notes"]
    assert saved["personal"]["name"]
    assert saved["experience"][0]["company"]


def test_default_output_dir_is_named_for_the_job(job):
    target = pipeline.output_dir_for(job)
    assert target.name.startswith("example-corp-backend-engineer-")
    assert target.parent.name == "output"
