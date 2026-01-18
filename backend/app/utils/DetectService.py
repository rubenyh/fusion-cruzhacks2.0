import os
import io
import json
from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
from dotenv import load_dotenv
from rapidfuzz import process as rf_process, fuzz as rf_fuzz
import google.generativeai as genai
from pydantic import BaseModel, Field


class ProductModel(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    manufacturer_or_company: Optional[str] = None
    category: Optional[str] = None
    


class EvidenceModel(BaseModel):
    product_name_text: Optional[str] = None
    brand_text: Optional[str] = None


class DetectionResultModel(BaseModel):
    product: ProductModel
    research_queries: List[str] = Field(default_factory=list)
    evidence: EvidenceModel = Field(default_factory=EvidenceModel)
    confidence: float = 0.0

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Set GEMINI_API_KEY in .env")

genai.configure(api_key=api_key)
gem_model = genai.GenerativeModel("gemini-2.5-flash")


CANON_PRODUCT_TYPES = [
  # Food & drink
  "snack", "cereal", "bread", "pasta", "sauce", "frozen_meal", "dairy", "beverage", "supplement",

  # Personal care
  "shampoo", "conditioner", "soap", "body_wash", "deodorant", "toothpaste", "mouthwash",
  "skincare", "sunscreen", "makeup",

  # Household
  "laundry_detergent", "dish_soap", "all_purpose_cleaner", "disinfectant", "air_freshener",
  "paper_towel", "toilet_paper", "trash_bag",

  # Baby
  "baby_formula", "baby_food", "diaper", "baby_wipes",

  # Pet
  "pet_food", "pet_treat", "pet_shampoo"
]


def best_match(token: str, choices: List[str], thr: int = 85):
    """Match a token to the best canonical ingredient name."""
    token = (token or "").strip().lower()
    if not token:
        return None
    match, score, _ = rf_process.extractOne(token, choices, scorer=rf_fuzz.WRatio)
    return match if score >= thr else None


def read_image_bytes(upload: UploadFile) -> bytes:
    """Read and normalize image to JPEG bytes for Gemini."""
    raw = upload.file.read()
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()
    except Exception:
        
        return raw


def detect_ingredients(image_bytes: bytes) -> Dict:
    """
    Detect ingredients from image using Gemini Vision API.
    
    Args:
        image_bytes: JPEG image bytes
        
    Returns:
        Dict with keys: ingredients (List[str]), confidence (float), raw_items (List[dict])
    """
    prompt = (
  "You are a consumer product label + packaging extractor. The image shows a packaged consumer product "
  "(food/drink/personal care/household). Your job is to extract identifiers that a downstream research agent "
  "can use to find public reports, recalls, warnings, and lawsuits about THIS exact product or its maker.\n\n"

  "Rules:\n"
  "- Use ONLY information visible in the image. "
  "- Prefer exact text as printed on the package.\n"
  "- If a field is not visible or uncertain, set it to null.\n"
  "- Ignore marketing fluff unless it is a formal claim (e.g., 'organic', 'gluten free', 'paraben free').\n"
  "- Extract UPC/barcode digits ONLY if clearly readable.\n"
  "- Find the ingredients for this product"
  "- Return ONLY valid JSON (no markdown, no commentary).\n\n"

  "Output JSON schema:\n"
  "{"
    "\"product_name\": string|null,"
    "\"brand\": string|null,"
    "\"manufacturer_or_company\": string|null,"
    "\"category\": string|null,"
    "\"research_queries\": [string],"
    "\"evidence\": {"
      "\"product_name_text\": string|null,"
      "\"brand_text\": string|null,"
    "}"
  "}\n\n"

  "research_queries: include 3–6 short search-ready strings using extracted fields, e.g. "
  "\"<brand> <product_name> lawsuit\", \"<manufacturer> recall\", \"<product_name> ingredients complaint\", "
  "and if UPC exists include \"UPC <digits>\".\n\n"

  "Now extract the data."
)


    image_part = {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}}
    
    try:
        resp = gem_model.generate_content(
            [prompt, image_part],
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(resp.text)
    except Exception as e:
        raise HTTPException(500, f"Vision model error: {e}")

    # Calculate confidence based on how many fields were extracted
    fields_to_check = ["product_name", "brand", "manufacturer_or_company", "category", "upc", "ingredients"]
    filled_fields = sum(1 for f in fields_to_check if data.get(f))
    confidence = filled_fields / len(fields_to_check)
    
    return DetectionResultModel(
        product=ProductModel(
            product_name=data.get("product_name"),
            brand=data.get("brand"),
            manufacturer_or_company=data.get("manufacturer_or_company"),
            category=data.get("category"),
            
        ),
        research_queries=data.get("research_queries", []),
        evidence=EvidenceModel(**data.get("evidence", {})),
        confidence=confidence
    )