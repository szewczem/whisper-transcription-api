from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.transcriptions import router as transcriptions_router

app = FastAPI(
    title="Whisper Transcription API",
    version="0.1.0",
    description="Asynchronous speech-to-text API using Whisper Small.",
)

app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(
    transcriptions_router,
    prefix="/api/v1",
)
