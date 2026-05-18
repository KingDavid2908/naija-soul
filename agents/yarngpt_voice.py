import time
import httpx
from langchain.tools import tool

from app.core.config import YARNGPT_API_KEY
from app.core.logging import logger

API_URL = "https://yarngpt.ai/api/v1/tts"
MAX_CHARS = 2000
MAX_RETRIES = 3
TIMEOUT = 30.0


class YarnGPTVoiceTool:
    VOICES = {
        "Idera": "Melodic, gentle.",
        "Emma": "Authoritative, deep.",
        "Zainab": "Soothing, gentle.",
        "Osagie": "Smooth, calm.",
        "Wura": "Young, sweet.",
        "Jude": "Warm, confident.",
        "Chinenye": "Engaging, warm.",
        "Tayo": "Upbeat, energetic.",
        "Regina": "Mature, warm.",
        "Femi": "Rich, reassuring.",
        "Adaora": "Warm, engaging.",
        "Umar": "Calm, smooth.",
        "Mary": "Energetic, youthful.",
        "Nonso": "Bold, resonant.",
        "Remi": "Melodious, warm.",
        "Adam": "Deep, clear.",
    }

    def __init__(self):
        self._client = httpx.Client(timeout=TIMEOUT)
        self._headers = {
            "Authorization": f"Bearer {YARNGPT_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, text: str, voice: str = "Idera", fmt: str = "mp3") -> bytes:
        if voice not in self.VOICES:
            raise ValueError(f"Unknown voice '{voice}'. Available: {', '.join(self.VOICES)}")
        if len(text) > MAX_CHARS:
            raise ValueError(f"Text exceeds {MAX_CHARS} characters ({len(text)} given)")

        payload = {
            "text": text,
            "voice": voice,
            "response_format": fmt,
        }

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.post(API_URL, headers=self._headers, json=payload)
                if response.status_code == 200:
                    return response.content
                if response.status_code in (429,) or 500 <= response.status_code < 600:
                    if attempt < MAX_RETRIES:
                        wait = 2 ** attempt
                        logger.warning("YarnGPT API %s (attempt %d/%d), retrying in %ds",
                                       response.status_code, attempt, MAX_RETRIES, wait)
                        time.sleep(wait)
                        continue
                response.raise_for_status()
            except httpx.TimeoutException:
                if attempt < MAX_RETRIES:
                    wait = 2 ** attempt
                    logger.warning("YarnGPT API timeout (attempt %d/%d), retrying in %ds",
                                   attempt, MAX_RETRIES, wait)
                    time.sleep(wait)
                    continue
                raise

        raise RuntimeError(f"YarnGPT API failed after {MAX_RETRIES} retries")

    def generate_batch(self, texts: list[str], voice: str = "Idera", fmt: str = "mp3") -> list[bytes]:
        return [self.generate(t, voice=voice, fmt=fmt) for t in texts]

    def close(self):
        self._client.close()


@tool
def yarngpt_generate_audio(text: str, voice: str = "Idera", fmt: str = "mp3") -> dict:
    """Generate Nigerian-accented audio from text using YarnGPT TTS.

    Args:
        text: The text to convert to speech (max 2000 characters).
        voice: One of the YarnGPT voice names. See yarngpt_voice.VOICES for descriptions.
        fmt: Audio format — "mp3", "wav", "opus", or "flac". Defaults to "mp3".

    Returns:
        A dict with keys: audio_base64, voice_used, format.
    """
    import base64
    tool_instance = YarnGPTVoiceTool()
    try:
        audio_bytes = tool_instance.generate(text, voice=voice, fmt=fmt)
        return {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "voice_used": voice,
            "format": fmt,
        }
    finally:
        tool_instance.close()
