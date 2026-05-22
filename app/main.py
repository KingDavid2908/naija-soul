from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import logger
from app.routers import simulate_review, recommend, users

app = FastAPI(title="Naija Soul API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulate_review.router)
app.include_router(recommend.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
