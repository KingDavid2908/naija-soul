import json
import logging
import asyncio
import secrets

from fastapi import APIRouter

from agents.task_a_review import task_a_agent
from agents.yarngpt_voice import YarnGPTVoiceTool
from agents.translator import translate, LANGUAGES as TRANS_LANGS
from app.models.schemas import SimulateReviewRequest, SimulateReviewResponse

router = APIRouter()
logger = logging.getLogger("naija-soul")


@router.post("/simulate-review", response_model=SimulateReviewResponse)
async def simulate_review(request: SimulateReviewRequest) -> SimulateReviewResponse:
    user_id = request.user_id or "user_" + secrets.token_hex(4)

    content: dict = {
        "user_id": user_id,
        "product_name": request.product_name,
        "product_category": request.product_category,
        "product_description": request.product_description,
    }

    if request.business_name:
        content["business_name"] = request.business_name
    if request.user_persona:
        content["user_persona"] = request.user_persona

    input_msg = {"messages": [{"role": "user", "content": json.dumps(content)}]}

    result = await task_a_agent.ainvoke(input_msg)
    last = result["messages"][-1]
    content_str = last.content if hasattr(last, "content") else str(last)
    data: dict = {}
    if isinstance(content_str, str):
        text = content_str.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Agent output not valid JSON: %.200s", text)

    review_text = data.get("review_text", content_str if isinstance(content_str, str) else "")
    voice_used = data.get("voice_used", "Idera")
    VALID_VOICES = YarnGPTVoiceTool.VOICES
    if voice_used not in VALID_VOICES:
        voice_used = "Idera"

    language = request.language

    translated_text = review_text
    if language in TRANS_LANGS and review_text:
        translated_text = await translate(review_text, language)
        if translated_text == review_text:
            logger.warning("Translation returned unchanged text for %s", language)

    audio_b64 = ""
    if translated_text:
        try:
            tts = YarnGPTVoiceTool()
            loop = asyncio.get_running_loop()
            result_dict = await loop.run_in_executor(
                None, tts.split_generate_and_combine, translated_text, voice_used
            )
            audio_b64 = result_dict.get("audio_base64", "")
            tts.close()
        except Exception as exc:
            logger.warning("YarnGPT audio generation failed: %s", exc)

    return SimulateReviewResponse(
        review_text=translated_text,
        rating=float(data.get("rating", 0)),
        confidence=float(data.get("confidence", 0)),
        audio_base64=audio_b64,
        voice_used=voice_used,
        persona_match_score=float(data.get("persona_match_score", 0)),
        language=language,
        user_id=user_id,
    )
