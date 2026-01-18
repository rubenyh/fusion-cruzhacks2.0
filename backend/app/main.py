import asyncio, uuid, os, json, base64
import httpx
from pydantic import BaseModel
from uagents_core.envelope import Envelope
from uagents_core.identity import Identity
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .DetectService import read_image_bytes, detect_ingredients
from .json_to_pdf import json_to_pdf
from .db import client
from datetime import datetime
from uagents_core.models import Model as UA_Model
from .agents import DetectionInput, detect_agent
import boto3
from io import BytesIO
from .auth import verify_jwt
# AWS Config
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# FastAPI
app = FastAPI(title="Image -> Agents -> PDF")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

RESULTS_DIR = "report_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

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

PENDING: dict[str, asyncio.Future] = {}
DETECT_AGENT_SUBMIT = os.getenv("DETECT_AGENT_SUBMIT", "http://127.0.0.1:8000/submit")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8080")
DB_NAME = os.environ.get("MONGO_DB", "cruzhack")
COLL_NAME = os.environ.get("MONGO_COLLECTION", "reports")
coll = client[DB_NAME][COLL_NAME]

# Webhook endpoint
@app.post("/report/webhook/{request_id}")
async def report_webhook(request_id: str, request: Request):
    payload = await request.json()
    fut = PENDING.get(request_id)
    if fut and not fut.done():
        fut.set_result(payload)

    final_report = payload.get("final_report")
    if final_report:
        await asyncio.to_thread(
            coll.update_one,
            {"request_id": request_id},
            {"$set": {"final_report": final_report, "status": "complete", "completed_at": datetime.utcnow()}}
        )
    return {"ok": True}

# POST image -> generate report
@app.post("/report-json")
async def report_json(image: UploadFile = File(...), user=Depends(verify_jwt)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(400, "Upload must be an image")

    img_bytes = await image.read()
    await image.close()

    # Upload to S3 without ACL (avoid bucket errors)
    s3_key = f"images/{uuid.uuid4().hex}.{image.filename.split('.')[-1]}"
    await asyncio.to_thread(
        s3_client.upload_fileobj,
        BytesIO(img_bytes),
        AWS_S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": image.content_type}
    )

    # Proper URL to avoid 301 redirect
    if AWS_REGION == "us-east-1":
        s3_url = f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{s3_key}"
    else:
        s3_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

    detection = detect_ingredients(img_bytes)
    original_detection = detection.model_dump() if hasattr(detection, "model_dump") else detection

    request_id = uuid.uuid4().hex
    callback_url = f"{PUBLIC_BASE_URL}/report/webhook/{request_id}"

    # Insert initial report to MongoDB
    doc = {
        "user_id": user.get("sub"),
        "request_id": request_id,
        "detection": original_detection,
        "image_url": s3_url,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    await asyncio.to_thread(coll.insert_one, doc)

    # Prepare agent envelope
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    PENDING[request_id] = fut

    try:
        digest = UA_Model.build_schema_digest(DetectionInput)
    except Exception:
        digest = "detectioninput-v1"

    message = DetectionInput(
        detection_result=original_detection,
        request_id=request_id,
        callback_url=callback_url,
    )

    payload_json = json.dumps(message.model_dump(), separators=(",", ":"), ensure_ascii=False)
    payload_b64 = base64.b64encode(payload_json.encode()).decode()

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
    if envelope.get("session") is not None:
        envelope["session"] = str(envelope["session"])

    async with httpx.AsyncClient(timeout=30.0) as client_http:
        r = await client_http.post(DETECT_AGENT_SUBMIT, json=envelope)
        if r.status_code >= 300:
            PENDING.pop(request_id, None)
            raise HTTPException(500, f"detect_agent submit failed: {r.status_code} {r.text[:200]}")

    try:
        payload = await asyncio.wait_for(fut, timeout=90.0)
    except asyncio.TimeoutError:
        PENDING.pop(request_id, None)
        raise HTTPException(504, "Timed out waiting for writer webhook")

    final_report = payload.get("final_report")
    if not isinstance(final_report, dict):
        raise HTTPException(500, "Webhook did not return final_report")

    # Update MongoDB with final report
    await asyncio.to_thread(
        coll.update_one,
        {"request_id": request_id},
        {"$set": {"final_report": final_report, "status": "complete", "completed_at": datetime.utcnow()}}
    )

    return JSONResponse({"request_id": request_id, "final_report": final_report, "image_url": s3_url})

# GET reports for user history
@app.get("/reports")
async def get_reports(user=Depends(verify_jwt)):
    docs = await asyncio.to_thread(lambda: list(coll.find({"user_id": user["sub"]})))
    result = []
    for doc in docs:
        result.append({
            "request_id": doc.get("request_id"),
            "detection": doc.get("detection", {}),
            "final_report": doc.get("final_report"),
            "image_url": doc.get("image_url"),
            "status": doc.get("status"),
            "created_at": str(doc.get("created_at")) if doc.get("created_at") else None,
            "completed_at": doc.get("completed_at"),
        })
    return result

# GET PDF
@app.get("/report-pdf/{request_id}")
async def report_pdf(request_id: str, user=Depends(verify_jwt)):
    doc = await asyncio.to_thread(coll.find_one, {"request_id": request_id, "user_id": user.get("sub")})
    if not doc or "final_report" not in doc:
        raise HTTPException(404, "Report not found or incomplete")
    pdf_path = os.path.join(RESULTS_DIR, f"{request_id}.pdf")
    json_to_pdf(doc["final_report"], pdf_path)
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{request_id}.pdf")

# DELETE report (history remove)
@app.delete("/report/{request_id}")
async def delete_report(request_id: str, user=Depends(verify_jwt)):
    doc = await asyncio.to_thread(coll.find_one, {"request_id": request_id, "user_id": user.get("sub")})
    if not doc:
        raise HTTPException(404, "Report not found")
    image_url = doc.get("image_url")
    if image_url:
        # Handle both us-east-1 and other regions
        if AWS_REGION == "us-east-1":
            key = image_url.split(f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/")[-1]
        else:
            key = image_url.split(f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/")[-1]
        try:
            await asyncio.to_thread(s3_client.delete_object, Bucket=AWS_S3_BUCKET, Key=key)
        except Exception as e:
            print("Failed to delete image from S3:", e)

    await asyncio.to_thread(coll.delete_one, {"request_id": request_id, "user_id": user.get("sub")})
    return {"ok": True, "message": "Report deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
