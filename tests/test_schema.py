import pytest

from resume_generator.data import load_resume_data
from resume_generator.schema import Education, JobPosting, ResumeData


def test_master_resume_validates(master):
    assert master.personal.name
    assert master.experience and master.skills and master.education
    assert master.languages


def test_unquoted_year_is_coerced_to_text():
    # data/resume_data_en_faang.yaml has `period: 2021` unquoted -> int.
    edu = Education(degree="MSc", institution="Somewhere", period=2021)
    assert edu.period == "2021"


def test_float_year_does_not_gain_a_decimal():
    assert Education(degree="d", institution="i", period=2019.0).period == "2019"


def test_missing_required_field_is_rejected():
    with pytest.raises(Exception):
        ResumeData.model_validate({"personal": {}})


def test_unknown_top_level_keys_are_ignored():
    # The YAML carries `target_role`, which nothing renders.
    resume = ResumeData.model_validate(
        {"personal": {"name": "A"}, "target_role": {"title": "x"}}
    )
    assert resume.personal.name == "A"


def test_missing_data_file_raises():
    with pytest.raises(FileNotFoundError):
        load_resume_data("does/not/exist.yaml")


def test_default_data_file_can_be_configured_per_user(monkeypatch, tmp_path):
    data_file = tmp_path / "resume.yaml"
    data_file.write_text(
        """
personal:
  name: Ada Lovelace
skills: []
experience: []
education: []
languages: []
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("RESUME_GENERATOR_DATA_FILE", str(data_file))

    assert load_resume_data().personal.name == "Ada Lovelace"


def test_job_label():
    assert JobPosting(description="d", title="Dev", company="Acme").label() == "Dev at Acme"
    assert JobPosting(description="d").label() == "this role"
