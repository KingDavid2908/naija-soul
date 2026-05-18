import io
import re
import time
import wave
import base64
import logging
import httpx
from langchain.tools import tool

from app.core.config import YARNGPT_API_KEY

logger = logging.getLogger("naija-soul")

API_URL = "https://yarngpt.ai/api/v1/tts"
MAX_CHARS = 2000
MAX_RETRIES = 3
TIMEOUT = 60.0


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

    @staticmethod
    def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
        text = text.strip()
        if not text:
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        buffer = ""
        for sentence in sentences:
            if len(sentence) > max_chars:
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i : i + max_chars].strip())
            elif len(buffer) + len(sentence) + 1 <= max_chars:
                buffer = (buffer + " " + sentence).strip()
            else:
                chunks.append(buffer)
                buffer = sentence

        if buffer:
            chunks.append(buffer)

        return [c for c in chunks if c]

    @staticmethod
    def combine_wavs(wav_chunks: list[bytes]) -> bytes:
        if not wav_chunks:
            raise ValueError("No WAV chunks to combine")

        if len(wav_chunks) == 1:
            with wave.open(io.BytesIO(wav_chunks[0])) as w:
                pass
            return wav_chunks[0]

        streams = []
        total_frames = 0
        params = None

        for chunk in wav_chunks:
            with wave.open(io.BytesIO(chunk)) as w:
                p = w.getparams()
                if params is None:
                    params = p
                else:
                    if (p.nchannels != params.nchannels
                            or p.sampwidth != params.sampwidth
                            or p.framerate != params.framerate):
                        raise ValueError(
                            f"WAV format mismatch: {params} vs nchannels={p.nchannels}, "
                            f"sampwidth={p.sampwidth}, framerate={p.framerate}"
                        )
                frames = w.readframes(p.nframes)
                streams.append(frames)
                total_frames += p.nframes

        out = io.BytesIO()
        with wave.open(out, "wb") as w:
            w.setnchannels(params.nchannels)
            w.setsampwidth(params.sampwidth)
            w.setframerate(params.framerate)
            for frames in streams:
                w.writeframes(frames)

        return out.getvalue()

    def _call_api(self, text: str, voice: str, fmt: str) -> bytes:
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

    def generate(self, text: str, voice: str = "Idera", fmt: str = "wav") -> bytes:
        if voice not in self.VOICES:
            raise ValueError(f"Unknown voice '{voice}'. Available: {', '.join(self.VOICES)}")

        if len(text) <= MAX_CHARS:
            return self._call_api(text, voice, fmt)

        chunks = self.split_text(text)
        wavs = [self._call_api(t, voice, "wav") for t in chunks]
        return self.combine_wavs(wavs)

    def generate_batch(self, texts: list[str], voice: str = "Idera", fmt: str = "wav") -> list[bytes]:
        return [self.generate(t, voice=voice, fmt=fmt) for t in texts]

    def split_generate_and_combine(self, full_text: str, voice: str = "Idera") -> dict:
        audio_bytes = self.generate(full_text, voice=voice, fmt="wav")

        duration = 0.0
        try:
            with wave.open(io.BytesIO(audio_bytes)) as w:
                duration = w.getnframes() / w.getframerate() if w.getframerate() > 0 else 0.0
        except Exception:
            pass

        return {
            "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
            "voice_used": voice,
            "format": "wav",
            "duration_estimate": round(duration, 2),
        }

    def close(self):
        self._client.close()


@tool
def yarngpt_generate_audio(text: str, voice: str = "Idera") -> dict:
    """Generate Nigerian-accented audio from text using YarnGPT TTS.

    Automatically handles long text by splitting at sentence boundaries,
    generating audio for each segment, and combining into a single WAV file.

    Args:
        text: The text to convert to speech.
        voice: One of the YarnGPT voice names — Idera, Emma, Zainab, Osagie,
               Wura, Jude, Chinenye, Tayo, Regina, Femi, Adaora, Umar,
               Mary, Nonso, Remi, Adam.

    Returns:
        A dict with keys: audio_base64 (str), voice_used (str),
        format (str), duration_estimate (float, seconds).
    """
    try:
        return YarnGPTVoiceTool().split_generate_and_combine(text, voice)
    except Exception as exc:
        logger.warning("YarnGPT audio generation failed: %s", exc)
        return {
            "audio_base64": "",
            "voice_used": voice,
            "format": "wav",
            "duration_estimate": 0.0,
        }
