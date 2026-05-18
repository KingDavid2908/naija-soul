# Naija Soul

**DSN × BCT Hackathon 3.0 — LLM Agent Challenge**

A culturally-grounded multi-agent behavioral intelligence platform for user modeling (Task A) and personalized recommendation (Task B), powered by Groq, LangGraph, and YarnGPT.

---

## Architecture

```
Frontend (Next.js / TypeScript) — Vercel
        │
        │  HTTP
        ▼
AI Backend (Python / FastAPI)   — Render
        │
        ├── Groq (gpt-oss-120b)       — LLM reasoning
        ├── YarnGPT API               — Nigerian TTS
        ├── Geoapify Geocoding + Places  — Dynamic city resolution + business data
        ├── Calendarific API          — Nigerian holidays + cultural festivals
        └── Open-Meteo                — Weather context (past, present, future)
```

---

## Prerequisites

- Python 3.11+
- [Groq API key](https://console.groq.com)
- [YarnGPT API key](https://yarngpt.ai)
- [Calendarific API key](https://calendarific.com)
- [Geoapify API key](https://myprojects.geoapify.com)

---

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/KingDavid2908/naija-soul.git
cd naija-soul

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file with your keys
cat > .env << EOF
GROQ_API_KEY=your_groq_key_here
YARNGPT_API_KEY=your_yarngpt_key_here
CALENDARIFIC_API_KEY=your_calendarific_key_here
GEOAPIFY_API_KEY=your_geoapify_key_here
EOF

# 6. Run the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{ "status": "ok" }
```

### POST /simulate-review — Task A: User Modeling

Simulates a realistic user review for a given product or business.

```bash
curl -X POST http://localhost:8000/simulate-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "business_name": "Bukka Hut, VI",
    "product_details": {
      "name": "Ofe Onugbu",
      "category": "food",
      "price_range": "mid",
      "description": "Traditional Nigerian bitter leaf soup"
    }
  }'
```

Response:
```json
{
  "review_text": "Guy this place no dey disappoint! The ofe onugbu hit different...",
  "rating": 4.0,
  "confidence": 0.87,
  "audio_base64": "base64-encoded-wav",
  "voice_used": "Tayo",
  "persona_match_score": 9.1
}
```

### POST /recommend — Task B: Recommendation

Generates personalized recommendations with spoken explanation.

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```

Response:
```json
{
  "recommendations": [
    {
      "name": "Terra Kulture",
      "category": "restaurant",
      "score": 0.92,
      "reason": "Great jollof rice and live music every Friday"
    }
  ],
  "spoken_explanation": {
    "audio_base64": "base64-encoded-wav",
    "voice_used": "Tayo",
    "language": "english",
    "text_transcript": "For where una dey tonight, I recommend Terra Kulture..."
  }
}
```

---

## Docker

```bash
# Build
docker build -t naija-soul .

# Run
docker run -p 8000:10000 \
  -e GROQ_API_KEY=your_key \
  -e YARNGPT_API_KEY=your_key \
  -e CALENDARIFIC_API_KEY=your_key \
  -e GEOAPIFY_API_KEY=your_key \
  naija-soul
```

---

## Deploy to Render

1. Create a **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `GROQ_API_KEY`
   - `YARNGPT_API_KEY`
   - `CALENDARIFIC_API_KEY`
   - `GEOAPIFY_API_KEY`
5. Deploy (Render Free spins down when idle)

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI (Python) |
| LLM | Groq — `openai/gpt-oss-120b` |
| Agent Runtime | LangGraph (`create_agent`) |
| Memory | LangMem (semantic memory store) |
| TTS | YarnGPT API |
| Places Data | Geoapify Geocoding + Places API |
| Holidays & Festivals | Calendarific API (national, local, observance) |
| Weather | Open-Meteo |
| Deployment | Render |

---

## Project Structure

```
naija-soul-ai/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── core/config.py           # Environment config
│   ├── core/logging.py          # Logger setup
│   ├── models/schemas.py        # Pydantic models
│   └── routers/                 # API route handlers
├── agents/                      # LangGraph agents + tools
├── tools/                       # External API wrappers (Geoapify, Calendarific)
├── memory/                      # User profile store
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Deliverables

- **Task A (User Modeling):** `POST /simulate-review` — generates review text + star rating + audio narration
- **Task B (Recommendation):** `POST /recommend` — returns ranked recommendations + spoken explanation
- **Solution Paper:** 4-8 pages covering architecture, experiments, and YarnGPT integration rationale
- **Code Repository:** Clean, documented, reproducible with a single `docker run`

---

## License

MIT
