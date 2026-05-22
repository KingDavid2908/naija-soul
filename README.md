# Naija Soul

**DSN × BCT Hackathon 3.0 — LLM Agent Challenge**

A culturally-grounded multi-agent behavioral intelligence platform for user modeling (Task A) and personalized recommendation (Task B), powered by Mistral, LangGraph, YarnGPT, and Google Gemini.

---

## Architecture

```
Frontend (Next.js / TypeScript) — Vercel
        │
        │  HTTP
        ▼
AI Backend (Python / FastAPI)   — Render
        │
        ├── Mistral (mistral-large-latest)   — LLM reasoning
        ├── Google Gemini (gemini-embedding-2) — Embeddings (memory + product search)
        ├── YarnGPT API                      — Nigerian TTS
        ├── Geoapify Geocoding + Places      — Dynamic city resolution + business data
        ├── Calendarific API                 — Nigerian holidays + cultural festivals
        └── Open-Meteo                       — Weather context (past, present, future)
```

---

## Prerequisites

- Python 3.11+
- [Mistral API key](https://console.mistral.ai)
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
uvicorn app.main:app --reload --port 10000
```

The API will be available at `http://localhost:10000`. Visit `http://localhost:10000/docs` for the interactive Swagger UI.

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

Simulates a realistic user review in Nigerian English/Pidgin/Yoruba/Igbo/Hausa, with optional audio narration.

**Request fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | string | No* | Existing user ID (auto-generated from persona if omitted) |
| `user_persona` | string | No* | Free-text persona (e.g. "A young Yoruba professional in Lagos") |
| `product_name` | string | Yes | Name of the product, book, or dish |
| `product_category` | string | Yes | Category — `"food"`, `"book"`, `"movie"`, or `"business"` |
| `product_description` | string | Yes | Description of the product |
| `business_name` | string | No | Restaurant/store name (for food/business categories) |
| `language` | string | No | Output language: `english`, `pidgin` (default), `yoruba`, `igbo`, `hausa` |

*Either `user_id` or `user_persona` must be provided (or both — they merge).

**How `user_id` works:** Any name string. The agent infers ethnicity from the first name using built-in Yoruba/Hausa/Igbo name lists. Embed a city with underscore suffix (e.g. `chidi_onitsha`) for location detection. When omitted, a random `user_<hex>` ID is auto-generated and returned in the response — the frontend should save it for subsequent requests.

Valid `user_id` examples: `tunde`, `chidi`, `amina`, `tayo_lagos`, `emeka_enugu`, `musa_kano`.

**Yelp user_id lookup:** Pass a real Yelp user ID (from our Yelp dataset, e.g. `qVc8ODYU5SZjKXVBgXdI7w`) as `user_id`. The agent fetches that user's past reviews from the local dataset and mimics their writing style. Yelp dataset contains 2K users and 20K reviews.

**Language support:** When `language` is `yoruba`, `igbo`, or `hausa`, the English/Pidgin review text is translated using Google Gemini post-generation. Yarngpt then reads the translated text in the target language.

```bash
# Example 1: Existing user by ID
curl -X POST http://localhost:10000/simulate-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "tunde",
    "product_name": "Jollof Rice",
    "product_category": "food",
    "product_description": "Classic Nigerian jollof rice with fried plantain",
    "business_name": "Bukka Hut, VI"
  }'

# Example 2: Cold-start with persona description
curl -X POST http://localhost:10000/simulate-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": "An Igbo student at UNN who loves African literature",
    "product_name": "Half of a Yellow Sun",
    "product_category": "book",
    "product_description": "Chimamanda Adichie'\''s novel about the Biafran War"
  }'
```

Response:
```json
{
  "review_text": "Omo, Bukka Hut Jollof Rice na the real deal! The rice get that perfect smoky, peppery vibe...",
  "rating": 5.0,
  "confidence": 0.96,
  "audio_base64": "base64-encoded-wav-or-empty-string",
  "voice_used": "Osagie",
  "persona_match_score": 0.92
}
```

**Notes for frontend:**
- `audio_base64` may be an empty string `""` if TTS generation fails — play only if non-empty
- Play audio as: `new Audio(`data:audio/wav;base64,${data.audio_base64}`).play()`
- `voice_used` is one of 16 YarnGPT Nigerian voices (Idera, Emma, Zainab, Osagie, Tayo, etc.)
- `rating` ranges 1.0–5.0, `confidence` and `persona_match_score` range 0.0–1.0
- `user_id` is auto-generated if not provided — save it for session continuity
- `language` in response reflects the requested output language

### POST /recommend — Task B: Recommendation

Generates personalized recommendations across food, books, movies, and local Nigerian businesses.

**Request fields:**

| Field | Type | Required | Description |
|---|---|---|---|---|
| `user_id` | string | No* | Existing user ID (auto-generated from persona if omitted) |
| `user_persona` | string | No* | Free-text persona (e.g. "A Hausa trader in Kano") |
| `category` | string | No | Filter — `"food"`, `"book"`, `"movie"`, `"business"`, or omit for all |
| `language` | string | No | Output language: `english`, `pidgin` (default), `yoruba`, `igbo`, `hausa` |

*Either `user_id` or `user_persona` must be provided (or both).

**How `user_id` works:** Any name string. The agent infers ethnicity from the first name using built-in Yoruba/Hausa/Igbo name lists. See `/simulate-review` section for details and examples.

```bash
# Example 1: Recommend food for existing user
curl -X POST http://localhost:10000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "tunde",
    "category": "food"
  }'

# Example 2: Recommend books for a persona
curl -X POST http://localhost:10000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": "A Hausa student in Kano who enjoys history",
    "category": "book"
  }'

# Example 3: General recommendation (all categories)
curl -X POST http://localhost:10000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": "An Igbo businessman in Enugu who likes action movies"
  }'
```
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

### GET /users/{user_id}/reviews — User History

Returns metadata about a previously created user profile.

```bash
curl http://localhost:10000/users/user_abc123/reviews
```

---

## Docker

```bash
# Build
docker build -t naija-soul-ai .

# Run (mount .env to inject API keys)
docker run -p 10000:10000 -v .env:/app/.env naija-soul-ai

# Or with environment variables:
docker run -p 10000:10000 \
  -e MISTRAL_API_KEY=your_key \
  -e YARNGPT_API_KEY=your_key \
  -e CALENDARIFIC_API_KEY=your_key \
  -e GEOAPIFY_API_KEY=your_key \
  -e GOOGLE_API_KEY=your_key \
  -e GROQ_API_KEY=your_key \
  # Optional: fallback keys
  -e MISTRAL_API_KEY_2=backup_key \
  -e GOOGLE_API_KEY_2=backup_key \
  -e GROQ_API_KEY_2=backup_key \
  naija-soul-ai
```

---

## Deploy to Render

1. Create a **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port \$PORT`
4. Add environment variables (required):
   - `MISTRAL_API_KEY`
   - `YARNGPT_API_KEY`
   - `CALENDARIFIC_API_KEY`
   - `GEOAPIFY_API_KEY`
   - `GOOGLE_API_KEY`
   - `GROQ_API_KEY`
   
   Optional fallback keys (for auto-retry on rate limits):
   - `MISTRAL_API_KEY_2`, `MISTRAL_API_KEY_3`
   - `GOOGLE_API_KEY_2`
   - `GROQ_API_KEY_2`
5. Deploy (Render Free spins down when idle)

---

## Tech Stack

| Component | Technology |
|---|---|
| Framework | FastAPI (Python) |
| LLM | Mistral → Gemini → Groq (fallback chain with multiple keys) |
| Translation | Google Gemini (post-generation: English → Yoruba/Igbo/Hausa) |
| Agent Runtime | LangGraph (`create_react_agent`) |
| Memory | PersistedInMemoryStore (JSON file, survives container restarts) |
| Embeddings | Google Gemini `gemini-embedding-2` (3072d) |
| TTS | YarnGPT API (16 Nigerian voices) |
| Product Search | SQLite FTS5 → Gemini rerank (hybrid) |
| Places Data | Geoapify Geocoding + Places API |
| Holidays & Festivals | Calendarific API (national, local, observance) |
| Weather | Open-Meteo (free, no key) |
| Datasets | Yelp (10K businesses, 20K reviews, 2K users), Amazon Reviews (15K), Goodreads (7.9K) |
| Deployment | Render |

---

## Project Structure

```
naija-soul-ai/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── core/config.py           # Environment config (5 API keys)
│   ├── core/logging.py          # Logger setup
│   ├── models/schemas.py        # Pydantic request/response models
│   └── routers/                 # API route handlers
├── agents/
│   ├── prompts.py               # System prompts for all agents
│   ├── llm.py                   # Fallback chain: Mistral → Gemini → Groq
│   ├── embeddings.py            # Google Gemini embeddings
│   ├── memory.py                # PersistedInMemoryStore + langmem tools
│   ├── translator.py            # Gemini-based translation (Yoruba/Igbo/Hausa)
│   ├── task_a_review.py         # Task A: Review Simulator agent
│   ├── task_b_recommend.py      # Task B: Recommendation agent
│   ├── yarngpt_voice.py         # YarnGPT TTS tool
│   ├── weather_context.py       # Open-Meteo weather tool
│   └── culture_context.py       # Nigerian culture tool
├── tools/
│   ├── geoapify_places.py       # Geocoding + business search
│   ├── calendarific_holidays.py # Holiday lookup
│   ├── product_loader.py        # JSON fallback loader
│   ├── product_store.py         # SQLite FTS5 index
│   └── product_search.py        # FTS5 → Gemini rerank @tool
├── data/
│   ├── yelp/                    # 10K businesses, 20K reviews, 2K users
│   ├── amazon/                  # 15K video game reviews
│   └── goodreads/               # 7.9K books with genres
├── memory/
│   └── user_profiles.py         # Profile inference logic
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
