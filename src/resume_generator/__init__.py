"""Generate tailored resumes and cover letters from a master YAML resume."""

from .data import load_resume_data
from .pipeline import (
    GenerationResult,
    GroundingError,
    generate_cover_letter,
    generate_tailored_resume,
    render_resume,
    validate_grounding,
)
from .schema import JobPosting, ResumeData, TailoredResume

__version__ = "0.1.0"

__all__ = [
    "GenerationResult",
    "GroundingError",
    "JobPosting",
    "ResumeData",
    "TailoredResume",
    "generate_cover_letter",
    "generate_tailored_resume",
    "load_resume_data",
    "render_resume",
    "validate_grounding",
]
