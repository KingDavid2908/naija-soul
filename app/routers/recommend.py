import json
import logging
import asyncio
import secrets

from fastapi import APIRouter

from agents.task_b_recommend import task_b_agent
from agents.yarngpt_voice import YarnGPTVoiceTool
from agents.translator import translate, LANGUAGES as TRANS_LANGS
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
    user_id = request.user_id or "user_" + secrets.token_hex(4)
    language = request.language

    content: dict = {"user_id": user_id}

    if request.user_persona:
        content["user_persona"] = request.user_persona
    if request.category:
        content["category"] = request.category

    input_msg = {"messages": [{"role": "user", "content": json.dumps(content)}]}

    result = await task_b_agent.ainvoke(input_msg)
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

    explanation_text = data.get("explanation_text", "")
    voice_used = data.get("voice_used", "Idera")
    VALID_VOICES = YarnGPTVoiceTool.VOICES
    if voice_used not in VALID_VOICES:
        voice_used = "Idera"

    translated_explanation = explanation_text
    if language in TRANS_LANGS and explanation_text:
        translated_explanation = await translate(explanation_text, language)

    audio_b64 = ""
    if translated_explanation:
        try:
            tts = YarnGPTVoiceTool()
            loop = asyncio.get_running_loop()
            result_dict = await loop.run_in_executor(
                None, tts.split_generate_and_combine, translated_explanation, voice_used
            )
            audio_b64 = result_dict.get("audio_base64", "")
            tts.close()
        except Exception as exc:
            logger.warning("YarnGPT audio generation failed: %s", exc)

    spoken = SpokenExplanation(
        audio_base64=audio_b64,
        voice_used=voice_used,
        language=language,
        text_transcript=translated_explanation,
    )

    return RecommendResponse(
        recommendations=recommendations,
        spoken_explanation=spoken,
        language=language,
        user_id=user_id,
    )
