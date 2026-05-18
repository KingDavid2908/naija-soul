import json
import logging

from fastapi import APIRouter

from agents.task_b_recommend import task_b_agent
from app.models.schemas import (
    RecommendRequest,
    RecommendResponse,
    Recommendation,
    SpokenExplanation,
)

router = APIRouter()
logger = logging.getLogger("naija-soul")


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest) -> RecommendResponse:
    input_msg = {
        "messages": [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "user_id": request.user_id,
                        "category": request.category,
                    }
                ),
            }
        ]
    }

    result = await task_b_agent.ainvoke(input_msg)
    last = result["messages"][-1]
    content = last.content if hasattr(last, "content") else str(last)
    data: dict = {}
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Agent output not valid JSON: %.200s", content)

    raw_recs = data.get("recommendations", [])
    recommendations = [
        Recommendation(
            name=r.get("name", ""),
            category=r.get("category", ""),
            score=float(r.get("score", 0)),
            reason=r.get("reason", ""),
        )
        for r in raw_recs
        if isinstance(r, dict)
    ]

    raw_spoken = data.get("spoken_explanation", {}) or {}
    spoken = SpokenExplanation(
        audio_base64=raw_spoken.get("audio_base64", ""),
        voice_used=raw_spoken.get("voice_used", "Idera"),
        language=raw_spoken.get("language", "english"),
        text_transcript=raw_spoken.get("text_transcript", ""),
    )

    return RecommendResponse(
        recommendations=recommendations,
        spoken_explanation=spoken,
    )
