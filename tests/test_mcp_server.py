# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""The MCP surface. Only the tools that need no API key are executed here."""

import asyncio
import shutil

import pytest

from mcp.server.mcpserver.exceptions import ToolError

from resume_generator.mcp_server import mcp

needs_latex = pytest.mark.skipif(
    shutil.which("xelatex") is None, reason="xelatex is not installed"
)

EXPECTED_TOOLS = {
    "get_master_resume",
    "tailor_resume",
    "generate_cover_letter",
    "render_tailored_resume",
    "render_resume",
}


@pytest.fixture(scope="module")
def tools():
    return {t.name: t for t in asyncio.run(mcp.list_tools())}


def test_all_tools_are_registered(tools):
    assert set(tools) == EXPECTED_TOOLS


def test_job_description_is_the_only_required_argument(tools):
    for name in ("tailor_resume", "generate_cover_letter"):
        assert tools[name].input_schema["required"] == ["job_description"]


def test_every_tool_documents_itself(tools):
    # These descriptions are the entire contract a calling model sees.
    for tool in tools.values():
        assert tool.description and len(tool.description) > 80


def test_tailor_resume_documents_agent_orchestration(tools):
    description = tools["tailor_resume"].description

    assert "no API key" in description
    assert "get_master_resume" in description
    assert "render_tailored_resume" in description


def call(name, arguments=None):
    """Invoke a tool the way a client would, returning its structured result."""
    return asyncio.run(mcp.call_tool(name, arguments or {}))


def test_get_master_resume_returns_the_real_data():
    result = call("get_master_resume").structured_content
    resume = result["resume"]
    assert resume["personal"]["name"]
    assert resume["experience"] and resume["skills"]
    assert result["source_file"].endswith(".yaml")


def test_empty_job_description_is_rejected():
    # A blank description must fail before any API call is made, and the
    # caller must be told why rather than getting a generic tool error.
    with pytest.raises(ToolError, match="job_description is required"):
        call("tailor_resume", {"job_description": "   "})


def test_tailor_resume_prepares_agent_orchestrated_flow_without_api_key():
    result = call(
        "tailor_resume",
        {
            "job_description": "We need Java, Spring Boot, AWS and reliable APIs.",
            "company": "Example Corp",
            "job_title": "Backend Engineer",
        },
    ).structured_content

    assert result["ok"] is False
    assert result["needs_agent_tailoring"] is True
    assert result["next_tool"] == "render_tailored_resume"
    assert result["master_resume"]["personal"]["name"]
    assert result["job"]["company"] == "Example Corp"


@needs_latex
def test_render_tailored_resume_round_trips_agent_output(tmp_path):
    master = call("get_master_resume").structured_content["resume"]
    first = master["experience"][0]
    tailored = {
        "summary": "Backend engineer focused on secure Java services.",
        "skills": [
            {
                "category": "Backend",
                "items": ["Java", "Java Spring Boot", "REST APIs"],
            }
        ],
        "experience": [
            {
                "company": first["company"],
                "position": first["position"],
                "period": first["period"],
                "location": first["location"],
                "details": [
                    "Reworded but grounded bullet about Spring Boot services."
                ],
            }
        ],
        "tailoring_notes": ["Kept the most relevant backend experience."],
    }

    result = call(
        "render_tailored_resume",
        {
            "tailored": tailored,
            "job_description": "We need Java, Spring Boot, AWS and reliable APIs.",
            "company": "Example Corp",
            "job_title": "Backend Engineer",
            "output_dir": str(tmp_path),
        },
    ).structured_content

    assert result["ok"], result["errors"]
    assert result["page_count"] <= 2
    assert (tmp_path / "resume.pdf").exists()
    assert (tmp_path / "tailored.yaml").exists()
    assert (tmp_path / "job.txt").read_text().strip().endswith("reliable APIs.")


@needs_latex
def test_render_tailored_resume_rejects_ungrounded_agent_output(tmp_path):
    master = call("get_master_resume").structured_content["resume"]
    first = master["experience"][0]
    tailored = {
        "summary": "Backend engineer focused on secure Java services.",
        "skills": [{"category": "Backend", "items": ["Rust"]}],
        "experience": [
            {
                "company": first["company"],
                "position": first["position"],
                "period": first["period"],
                "location": first["location"],
                "details": ["This should not render."],
            }
        ],
        "tailoring_notes": ["Invented a skill."],
    }

    result = call(
        "render_tailored_resume",
        {
            "tailored": tailored,
            "job_description": "We need backend engineering.",
            "output_dir": str(tmp_path),
        },
    ).structured_content

    assert not result["ok"]
    assert "Rust" in " ".join(result["errors"])
    assert not (tmp_path / "resume.pdf").exists()


@needs_latex
def test_render_resume_round_trips_without_an_api_call(tmp_path):
    master = call("get_master_resume").structured_content
    result = call(
        "render_resume",
        {"resume": master["resume"], "output_dir": str(tmp_path)},
    ).structured_content
    assert result["ok"], result["errors"]
    assert result["page_count"] == 2
    assert (tmp_path / "resume.pdf").exists()


@needs_latex
def test_render_resume_rejects_malformed_data():
    with pytest.raises(ToolError, match="does not match the expected shape"):
        call("render_resume", {"resume": {"personal": {}}})
