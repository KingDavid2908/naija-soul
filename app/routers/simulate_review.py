import json
import logging

from fastapi import APIRouter

from agents.task_a_review import task_a_agent
from app.models.schemas import SimulateReviewRequest, SimulateReviewResponse

router = APIRouter()
logger = logging.getLogger("naija-soul")


@router.post("/simulate-review", response_model=SimulateReviewResponse)
async def simulate_review(request: SimulateReviewRequest) -> SimulateReviewResponse:
    input_msg = {
        "messages": [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "user_id": request.user_id,
                        "product_name": request.product_name,
                        "product_category": request.product_category,
                        "product_description": request.product_description,
                        "business_name": request.business_name,
                    }
                ),
            }
        ]
    }

    result = await task_a_agent.ainvoke(input_msg)
    last = result["messages"][-1]
    content = last.content if hasattr(last, "content") else str(last)
    data: dict = {}
    if isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Agent output not valid JSON: %.200s", content)

    return SimulateReviewResponse(
        review_text=data.get("review_text", content if isinstance(content, str) else ""),
        rating=float(data.get("rating", 0)),
        confidence=float(data.get("confidence", 0)),
        audio_base64=data.get("audio_base64", ""),
        voice_used=data.get("voice_used", "Idera"),
        persona_match_score=float(data.get("persona_match_score", 0)),
    )
