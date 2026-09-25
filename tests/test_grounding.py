import pytest

from resume_generator.pipeline import (
    GroundingError,
    merge_tailored,
    slugify,
    validate_grounding,
)
from resume_generator.schema import JobPosting, TailoredExperience, TailoredSkillCategory


def test_grounded_output_passes(master, grounded_tailored):
    validate_grounding(master, grounded_tailored)


def test_invented_employer_is_rejected(master, grounded_tailored):
    grounded_tailored.experience[0].company = "Google"
    with pytest.raises(GroundingError, match="Google"):
        validate_grounding(master, grounded_tailored)


def test_promoted_job_title_is_rejected(master, grounded_tailored):
    grounded_tailored.experience[0].position = "Principal Engineer"
    with pytest.raises(GroundingError, match="Principal Engineer"):
        validate_grounding(master, grounded_tailored)


def test_altered_dates_are_rejected(master, grounded_tailored):
    grounded_tailored.experience[0].period = "01/2019 - Present"
    with pytest.raises(GroundingError):
        validate_grounding(master, grounded_tailored)


def test_invented_skill_is_rejected(master, grounded_tailored):
    grounded_tailored.skills.append(
        TailoredSkillCategory(category="Backend", items=["Rust"])
    )
    with pytest.raises(GroundingError, match="Rust"):
        validate_grounding(master, grounded_tailored)


def test_skill_matching_ignores_case_and_spacing(master, grounded_tailored):
    grounded_tailored.skills[0].items = ["  java   spring boot ", "AWS"]
    validate_grounding(master, grounded_tailored)


def test_regrouping_skills_under_a_new_category_is_allowed(master, grounded_tailored):
    grounded_tailored.skills = [
        TailoredSkillCategory(category="What This Job Asked For", items=["Java", "AWS"])
    ]
    validate_grounding(master, grounded_tailored)


def test_rewording_bullets_is_allowed(master, grounded_tailored):
    grounded_tailored.experience[0].details = ["A completely different sentence."]
    validate_grounding(master, grounded_tailored)


def test_merge_carries_master_facts_and_model_content(master, grounded_tailored):
    merged = merge_tailored(master, grounded_tailored)
    # Never model-generated:
    assert merged.personal == master.personal
    assert merged.education == master.education
    assert merged.languages == master.languages
    # Model-generated:
    assert merged.summary.content == grounded_tailored.summary
    assert len(merged.experience) == 1


def test_empty_summary_stays_absent(master, grounded_tailored):
    grounded_tailored.summary = ""
    assert merge_tailored(master, grounded_tailored).summary is None


@pytest.mark.parametrize(
    "value,expected",
    [("Trend Micro", "trend-micro"), ("AI/ML Eng.", "ai-ml-eng"), ("", "job")],
)
def test_slugify(value, expected):
    assert slugify(value) == expected
