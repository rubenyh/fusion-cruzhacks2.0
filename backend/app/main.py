import asyncio, uuid, os, json
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from DetectService import read_image_bytes, detect_ingredients
from json_to_pdf import json_to_pdf

# IMPORT the SAME DetectionInput model used in agents.py
from agents import DetectionInput   # adjust import to your filename

app = FastAPI(title="Image -> Agents -> PDF")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

DETECT_AGENT_SUBMIT = os.getenv("DETECT_AGENT_SUBMIT", "http://127.0.0.1:8001/submit")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8080")

RESULTS_DIR = "report_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

PENDING: dict[str, asyncio.Future] = {}


@app.post("/report/webhook/{request_id}")
async def report_webhook(request_id: str, payload: dict):
    fut = PENDING.get(request_id)
    if fut and not fut.done():
        fut.set_result(payload)
    return {"ok": True}


@app.post("/report")
async def report(image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Upload must be an image")

    # 1) Run DetectService (Gemini vision) locally in FastAPI
    img_bytes = read_image_bytes(image)
    detection = detect_ingredients(img_bytes)
    if hasattr(detection, "model_dump"):
        detection = detection.model_dump()

    # 2) Prepare request_id + callback_url
    request_id = uuid.uuid4().hex
    callback_url = f"{PUBLIC_BASE_URL}/report/webhook/{request_id}"
    detection["request_id"] = request_id
    detection["callback_url"] = callback_url

    # 3) Create Future to wait for writer webhook
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    PENDING[request_id] = fut

    # 4) Send to detect_agent using the REQUIRED uAgents envelope
    msg = {"detection_result": detection}

    # depending on uagents version, schema digest method might differ
    try:
        digest = DetectionInput.schema_digest()
    except Exception:
        digest = DetectionInput.digest()

    envelope = {
        "sender": "fastapi",
        "schema_digest": digest,
        "message": msg
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(DETECT_AGENT_SUBMIT, json=envelope)
        if r.status_code >= 300:
            PENDING.pop(request_id, None)
            raise HTTPException(500, f"detect_agent submit failed: {r.status_code} {r.text[:200]}")

    # 5) Wait for webhook payload
    try:
        payload = await asyncio.wait_for(fut, timeout=90.0)
    except asyncio.TimeoutError:
        PENDING.pop(request_id, None)
        raise HTTPException(504, "Timed out waiting for writer webhook")

    final_report = payload.get("final_report")
    if not isinstance(final_report, dict):
        raise HTTPException(500, "Webhook did not return final_report")

    # 6) Render PDF and return it
    pdf_path = os.path.join(RESULTS_DIR, f"{request_id}.pdf")
    json_to_pdf(final_report, pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename="risk_report.pdf")
