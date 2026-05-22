import secrets
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

LANGUAGE_CHOICES = {"english", "pidgin", "yoruba", "igbo", "hausa"}


class SimulateReviewRequest(BaseModel):
    user_id: str | None = Field(None, description="Existing user ID (auto-generated from persona if omitted)")
    user_persona: str | None = Field(None, description="Free-text persona description (e.g. 'A young Yoruba professional in Lagos who loves spicy food')")
    product_name: str
    product_category: str
    product_description: str
    business_name: str | None = None
    language: str = Field("pidgin", description="Output language: english, pidgin, yoruba, igbo, hausa")

    @model_validator(mode="after")
    def _check_user_identifier(self) -> "SimulateReviewRequest":
        if not self.user_id and not self.user_persona:
            raise ValueError("Either user_id or user_persona must be provided")
        if self.language not in LANGUAGE_CHOICES:
            raise ValueError(f"language must be one of {LANGUAGE_CHOICES}")
        return self


class SimulateReviewResponse(BaseModel):
    review_text: str
    rating: float
    confidence: float
    audio_base64: str
    voice_used: str
    persona_match_score: float
    language: str
    user_id: str


class RecommendRequest(BaseModel):
    user_id: str | None = Field(None, description="Existing user ID (auto-generated from persona if omitted)")
    user_persona: str | None = Field(None, description="Free-text persona description")
    category: str | None = None
    language: str = Field("pidgin", description="Output language: english, pidgin, yoruba, igbo, hausa")

    @model_validator(mode="after")
    def _check_user_identifier(self) -> "RecommendRequest":
        if not self.user_id and not self.user_persona:
            raise ValueError("Either user_id or user_persona must be provided")
        if self.language not in LANGUAGE_CHOICES:
            raise ValueError(f"language must be one of {LANGUAGE_CHOICES}")
        return self


class Recommendation(BaseModel):
    name: str
    category: str
    score: float
    reason: str
    link: str = ""


class SpokenExplanation(BaseModel):
    audio_base64: str
    voice_used: str
    language: str
    text_transcript: str


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]
    spoken_explanation: SpokenExplanation
    language: str
    user_id: str
