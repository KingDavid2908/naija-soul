# Naija Soul

**DSN × BCT Hackathon 3.0 — LLM Agent Challenge**

A culturally-grounded multi-agent behavioral intelligence platform for user modeling (Task A) and personalized recommendation (Task B), powered by Groq, LangGraph, YarnGPT, and Google Gemini.

---

## Architecture

```
Frontend (Next.js / TypeScript) — Vercel
        │
        │  HTTP
        ▼
AI Backend (Python / FastAPI)   — Render
        │
        ├── Groq (gpt-oss-120b)              — LLM reasoning
        ├── Google Gemini (gemini-embedding-2) — Embeddings (memory + product search)
        ├── YarnGPT API                      — Nigerian TTS
        ├── Geoapify Geocoding + Places      — Dynamic city resolution + business data
        ├── Calendarific API                 — Nigerian holidays + cultural festivals
        └── Open-Meteo                       — Weather context (past, present, future)
```

---

## Prerequisites

- Python 3.11+
- [Groq API key](https://console.groq.com)
- [YarnGPT API key](https://yarngpt.ai)
- [Calendarific API key](https://calendarific.com)
- [Geoapify API key](https://myprojects.geoapify.com)
- [Google Gemini API key](https://aistudio.google.com) (free tier)

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

# 5. Create .env file with your keys (copy from .env.example)
cp .env.example .env
# then edit .env with your API keys

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
    "product_name": "Ofe Onugbu",
    "product_category": "food",
    "product_description": "Traditional Nigerian bitter leaf soup",
    "business_name": "Bukka Hut, VI"
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
    "user_id": "user_123",
    "category": "food"
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
  -e GOOGLE_API_KEY=your_key \
  naija-soul
```

---

## Deploy to Render

1. Create a **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port \$PORT`
4. Add environment variables:
   - `GROQ_API_KEY`
   - `YARNGPT_API_KEY`
   - `CALENDARIFIC_API_KEY`
   - `GEOAPIFY_API_KEY`
   - `GOOGLE_API_KEY`
5. Deploy (Render Free spins down when idle)

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI (Python) |
| LLM | Groq — `openai/gpt-oss-120b` |
| Agent Runtime | LangGraph (`create_react_agent`) |
| Memory | LangMem (InMemoryStore + Gemini embeddings) |
| Embeddings | Google Gemini `gemini-embedding-2` (3072d) |
| TTS | YarnGPT API (16 Nigerian voices) |
| Product Search | SQLite FTS5 → Gemini rerank (hybrid) |
| Places Data | Geoapify Geocoding + Places API |
| Holidays & Festivals | Calendarific API (national, local, observance) |
| Weather | Open-Meteo (free, no key) |
| Datasets | Yelp (10K), Amazon Reviews (15K), Goodreads (7.9K) |
| Deployment | Render |

---

## Project Structure

```
naija-soul-ai/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── core/config.py           # Environment config (5 API keys)
│   ├── core/logging.py          # Logger setup
│   └── routers/                 # API route handlers
├── agents/
│   ├── prompts.py               # System prompts for all agents
│   ├── llm.py                   # Groq LLM (lazy singleton)
│   ├── embeddings.py            # Google Gemini embeddings
│   ├── memory.py                # InMemoryStore + langmem tools
│   ├── task_a_review.py         # Task A: Review Simulator agent
│   ├── task_b_recommend.py      # Task B: Recommendation agent
│   ├── yarngpt_voice.py         # YarnGPT TTS tool
│   ├── weather_context.py       # Open-Meteo weather tool
│   └── culture_context.py       # Nigerian culture tool
├── tools/
│   ├── geoapify_places.py       # Geocoding + business search
│   ├── calendarific_holidays.py # Holiday lookup
│   ├── download_datasets.py     # One-time dataset downloader
│   ├── product_loader.py        # JSON fallback loader
│   ├── product_store.py         # SQLite FTS5 index
│   └── product_search.py        # FTS5 → Gemini rerank @tool
├── data/
│   ├── yelp/                    # 10K businesses, 20K reviews, 2K users
│   ├── amazon/                  # 15K video game reviews
│   └── goodreads/               # 7.9K books with genres
├── memory/                      # User profile store
├── .env.example                 # Template (committed)
├── .gitignore
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
