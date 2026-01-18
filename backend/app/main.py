import asyncio, uuid, os, json, base64
import httpx
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.auth import verify_jwt, require_scopes
from .DetectService import read_image_bytes, detect_ingredients
from .json_to_pdf import json_to_pdf
from .db import client
from datetime import datetime

# IMPORT the SAME DetectionInput model used in agents.py
from .agents import DetectionInput, detect_agent   # adjust import to your filename

from uagents_core.models import Model as UA_Model

# Try to load a signing identity for the FastAPI client (private_keys.json)
_CLIENT_IDENTITY: Identity | None = None
try:
    keys_path = os.path.join(os.path.dirname(__file__), "private_keys.json")
    with open(keys_path, "r", encoding="utf8") as _kf:
        _keys = json.load(_kf)
        _test_key = _keys.get("test_client", {}).get("identity_key")
        if _test_key:
            _CLIENT_IDENTITY = Identity.from_string(_test_key)
except Exception:
    _CLIENT_IDENTITY = None

app = FastAPI(title="Image -> Agents -> PDF")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.get("/public")
def public():
    return {"ok": True}

@app.get("/private")
def private(user=Depends(verify_jwt)):
    # user contains JWT claims (sub, permissions/scopes, etc.)
    return {"ok": True, "sub": user.get("sub")}

DETECT_AGENT_SUBMIT = os.getenv("DETECT_AGENT_SUBMIT", "http://127.0.0.1:8000/submit")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8080")

RESULTS_DIR = "report_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

PENDING: dict[str, asyncio.Future] = {}

@app.post("/report/webhook/{request_id}")
async def report_webhook(request_id: str, request: Request):
    payload = await request.json()
    fut = PENDING.get(request_id)
    if fut and not fut.done():
        fut.set_result(payload)
    return {"ok": True}


@app.post("/report")
async def report(image: UploadFile = File(...), user=Depends(verify_jwt)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Upload must be an image")

    # 1) Run DetectService (Gemini vision) locally in FastAPI
    img_bytes = read_image_bytes(image)
    detection = detect_ingredients(img_bytes)
    if hasattr(detection, "model_dump"):
        original_detection = detection.model_dump()
    else:
        original_detection = detection


    # 2) Prepare request_id + callback_url
    request_id = uuid.uuid4().hex
    callback_url = f"{PUBLIC_BASE_URL}/report/webhook/{request_id}"

    # Save detection data to MongoDB before calling agent (to avoid duplicate API cost)
    try:
        db_name = os.environ.get("MONGO_DB", "cruzhack")
        coll_name = os.environ.get("MONGO_COLLECTION", "reports")
        coll = client[db_name][coll_name]
        doc = {
            "request_id": request_id,
            "detection": original_detection,
            "image_info": {"filename": image.filename, "content_type": image.content_type},
            "status": "pending",
            "created_at": datetime.utcnow(),
        }
        # run blocking pymongo in threadpool
        await run_in_threadpool(coll.insert_one, doc)
    except Exception:
        # Don't fail the request if DB write fails; log could be added
        pass

    # 3) Create Future to wait for writer webhook
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    PENDING[request_id] = fut

    # 4) Send to detect_agent using the REQUIRED uAgents envelope
    # Try to get schema digest if available, else fallback to None or a static string
    digest = None
    if hasattr(DetectionInput, "schema"):
        schema = DetectionInput.schema()
        digest = schema.get("digest") if isinstance(schema, dict) else None
    # If still None, fallback to a static string or leave as None
    if not digest:
        digest = "detectioninput-v1"  # fallback static string

    # Create the DetectionInput message
    message = DetectionInput(
        detection_result=original_detection,
        request_id=request_id,
        callback_url=callback_url,
    )

    # Try to compute an exact schema digest using uagents_core helper
    try:
        digest = UA_Model.build_schema_digest(DetectionInput)
    except Exception:
        # keep existing digest fallback
        pass

    # Build envelope matching uagents_core.envelope.Envelope schema
    payload_json = json.dumps(message.model_dump(), separators=(",", ":"), ensure_ascii=False)
    payload_b64 = base64.b64encode(payload_json.encode()).decode()

    # Build an Envelope and sign it if we have a client identity
    env = Envelope(
        version=1,
        sender=_CLIENT_IDENTITY.address if _CLIENT_IDENTITY else "fastapi",
        target=detect_agent.address,
        session=uuid.uuid4(),
        schema_digest=digest,
        payload=payload_b64,
    )

    if _CLIENT_IDENTITY:
        env.sign(_CLIENT_IDENTITY)

    envelope = env.model_dump()
    # model_dump may contain non-serializable types (UUID); convert to JSON-serializable
    if envelope.get("session") is not None:
        envelope["session"] = str(envelope["session"])

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

    # Update MongoDB with final report
    try:
        db_name = os.environ.get("MONGO_DB", "cruzhack")
        coll_name = os.environ.get("MONGO_COLLECTION", "reports")
        coll = client[db_name][coll_name]
        await run_in_threadpool(
            coll.update_one,
            {"request_id": request_id},
            {"$set": {"final_report": final_report, "status": "complete", "completed_at": datetime.utcnow()}},
        )
    except Exception:
        pass

    # 6) Render PDF and return it
    pdf_path = os.path.join(RESULTS_DIR, f"{request_id}.pdf")
    json_to_pdf(final_report, pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename="risk_report.pdf")

# Endpoint to fetch report history (for dashboard, etc.)
@app.get("/reports")
async def reports(user=Depends(verify_jwt)):
    db_name = os.environ.get("MONGO_DB", "cruzhack")
    coll_name = os.environ.get("MONGO_COLLECTION", "reports")
    coll = client[db_name][coll_name]

    def _fetch(limit: int = 20):
        cursor = coll.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)

    return await run_in_threadpool(_fetch, 50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="localhost", port=8080, reload=True)