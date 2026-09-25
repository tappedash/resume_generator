"""Typed models for resume data, job postings, and model-generated content.

Two families live here:

* ``ResumeData`` and friends mirror ``data/resume_data_en_faang.yaml`` and are
  what the templates render.
* ``TailoredResume`` and ``CoverLetterContent`` are the structured-output
  contracts for the Claude API. Every field on those is required and has no
  default, because the structured-output schema marks all properties required
  and forbids additional ones.
"""

from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


def _as_text(value):
    """Coerce YAML scalars to text.

    Unquoted years (`period: 2021`) and phone numbers parse as ints or floats,
    and every one of these fields is rendered as text.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


Text = Annotated[str, BeforeValidator(_as_text)]


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


# --------------------------------------------------------------------------
# Master resume (source of truth, loaded from YAML)
# --------------------------------------------------------------------------

class Personal(_Base):
    name: Text
    email: Text = ""
    phone: Text = ""
    location: Text = ""
    linkedin: Text = ""
    github: Text = ""
    work_authorization: Text = ""


class SkillCategory(_Base):
    category: Text
    items: list[Text] = Field(default_factory=list)


class Experience(_Base):
    position: Text
    company: Text
    period: Text = ""
    location: Text = ""
    details: list[Text] = Field(default_factory=list)


class Education(_Base):
    degree: Text
    institution: Text
    period: Text = ""
    location: Text = ""


class Language(_Base):
    name: Text
    level: Text = ""


class Summary(_Base):
    content: Text = ""


class ResumeData(_Base):
    personal: Personal
    summary: Optional[Summary] = None
    skills: list[SkillCategory] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)


# --------------------------------------------------------------------------
# Job input
# --------------------------------------------------------------------------

class JobPosting(_Base):
    description: str
    title: str = ""
    company: str = ""
    url: str = ""

    def label(self) -> str:
        """Human-readable one-liner used in prompts."""
        parts = [p for p in (self.title, self.company) if p]
        return " at ".join(parts) if parts else "this role"


# --------------------------------------------------------------------------
# Claude structured outputs
# --------------------------------------------------------------------------

class TailoredExperience(BaseModel):
    """One role, reworded for the target job. Identity fields are copied
    verbatim from the master resume and are checked by ``validate_grounding``."""

    model_config = ConfigDict(extra="forbid")

    company: str
    position: str
    period: str
    location: str
    details: list[str]


class TailoredSkillCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    items: list[str]


class TailoredResume(BaseModel):
    """What the model returns. Personal details, education and languages are
    never model-generated -- they are carried across from the master resume."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    skills: list[TailoredSkillCategory]
    experience: list[TailoredExperience]
    tailoring_notes: list[str]


class CoverLetterContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    greeting: str
    paragraphs: list[str]
    closing: str
