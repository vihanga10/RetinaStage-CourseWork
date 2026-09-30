"""Small inference API for the frozen Colab model; no images are persisted."""

import os
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from guide import answer
from model_service import ModelService

MAX_BYTES = 10 * 1024 * 1024
TTL_SECONDS = 30 * 60
model_dir = Path(os.environ.get("RETINASTAGE_MODEL_DIR", Path(__file__).resolve().parent.parent / "models"))
service = ModelService(model_dir)
conversations: dict[str, tuple[float, dict]] = {}

app = FastAPI(title="RetinaStage Showcase", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Question(BaseModel):
    analysis_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=1, max_length=500)


@app.get("/api/health")
def health():
    return {"ready": service.ready, "message": (
        "Model files found. Their hash is checked before inference." if service.ready
        else "Install the Colab model and calibration record in models/.")}


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(400, "Choose a JPEG or PNG retinal photograph.")
    data = await file.read(MAX_BYTES + 1)
    await file.close()
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(400, "Choose a nonempty image no larger than 10 MB.")
    if not service.ready:
        raise HTTPException(503, "Install the saved Colab model and calibration file first.")
    try:
        result = service.analyze(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    now = time.monotonic()
    for key, (created, _) in list(conversations.items()):
        if now - created > TTL_SECONDS:
            conversations.pop(key, None)
    if len(conversations) >= 100:
        conversations.pop(next(iter(conversations)))
    analysis_id = uuid4().hex
    conversations[analysis_id] = (now, {
        key: value for key, value in result.items()
        if key not in {"processed_image", "heatmap_overlay"}
    })
    return {"analysis_id": analysis_id, **result}


@app.post("/api/ask")
def ask(payload: Question):
    saved = conversations.get(payload.analysis_id)
    if saved is None or time.monotonic() - saved[0] > TTL_SECONDS:
        conversations.pop(payload.analysis_id, None)
        raise HTTPException(404, "The analysis has expired. Analyze the image again.")
    return {"answer": answer(payload.question, saved[1])}
