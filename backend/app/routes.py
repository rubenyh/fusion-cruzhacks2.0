from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from datetime import datetime
from typing import Dict, Any

router = APIRouter(
    prefix="/api",
    tags=["api"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload an image file and return metadata
    """
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        file_content = await file.read()
        file_size = len(file_content)

        if file_size > 5 * 1024 * 1024:  
            raise HTTPException(status_code=400, detail="File size too large (max 5MB)")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"image_{timestamp}{file_extension}"

        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        return {
            "success": True,
            "message": "Image uploaded successfully",
            "image": {
                "filename": unique_filename,
                "original_name": file.filename,
                "size": file_size,
                "mimetype": file.content_type,
                "path": file_path,
                "uploaded_at": datetime.now().isoformat()
            },
            "analysis": {
                "status": "processed"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/")
def api_root():
    return {"message": "API router working"}

@router.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
