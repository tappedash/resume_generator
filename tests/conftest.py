import pytest

from resume_generator.data import load_resume_data
from resume_generator.schema import (
    JobPosting,
    TailoredExperience,
    TailoredResume,
    TailoredSkillCategory,
)

@pytest.fixture
def master():
    return load_resume_data()


@pytest.fixture
def job():
    return JobPosting(
        description="We need a backend engineer with Java, Spring Boot and AWS.",
        title="Backend Engineer",
        company="Example Corp",
    )


@pytest.fixture
def grounded_tailored(master):
    """A tailored resume that copies identity fields from the master."""
    first = master.experience[0]
    return TailoredResume(
        summary="Backend engineer focused on secure Java services.",
        skills=[
            TailoredSkillCategory(
                category="Backend", items=["Java", "Java Spring Boot", "REST APIs"]
            )
        ],
        experience=[
            TailoredExperience(
                company=first.company,
                position=first.position,
                period=first.period,
                location=first.location,
                details=["Reworded but grounded bullet about Spring Boot services."],
            )
        ],
        tailoring_notes=["Kept the most recent role only."],
    )
