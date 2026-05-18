from pydantic import BaseModel


class SimulateReviewRequest(BaseModel):
    user_id: str
    product_name: str
    product_category: str
    product_description: str
    business_name: str | None = None


class SimulateReviewResponse(BaseModel):
    review_text: str
    rating: float
    confidence: float
    audio_base64: str
    voice_used: str
    persona_match_score: float


class RecommendRequest(BaseModel):
    user_id: str
    category: str | None = None


class Recommendation(BaseModel):
    name: str
    category: str
    score: float
    reason: str


class SpokenExplanation(BaseModel):
    audio_base64: str
    voice_used: str
    language: str
    text_transcript: str


class RecommendResponse(BaseModel):
    recommendations: list[Recommendation]
    spoken_explanation: SpokenExplanation
