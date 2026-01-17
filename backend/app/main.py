from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from DetectService import read_image_bytes, detect_ingredients, DetectionResultModel
import asyncio
import uuid
import httpx
import os
import json


app = FastAPI(title="My FastAPI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "API is running"}


@app.post("/detect", response_model=DetectionResultModel)
async def detect_product(image: UploadFile = File(...)):
    """
    Upload a product image to detect ingredients and product information.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_bytes = read_image_bytes(image)
    result = detect_ingredients(image_bytes)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8080, reload=True)