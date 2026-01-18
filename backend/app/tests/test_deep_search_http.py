"""
HTTP-based test script for deep search agent
Sends test data via HTTP POST to the Bureau endpoint
"""
import httpx
import json
from DetectService import DetectionResultModel, ProductModel, EvidenceModel
from deep_search_agent import DeepSearchRequest

# Test data matching the user's specification
TEST_DATA = {
    "product": {
        "product_name": "MEGA MONSTER ENERGY",
        "brand": "MONSTER",
        "manufacturer_or_company": None,
        "category": "Energy Drink"
    },
    "research_queries": [
        "MONSTER MEGA MONSTER ENERGY lawsuit",
        "MEGA MONSTER ENERGY ingredients complaint",
        "Monster Energy drink recall",
        "Monster Energy warnings",
        "Monster Energy adverse events"
    ],
    "evidence": {
        "product_name_text": "MEGA MONSTER ENERGY",
        "brand_text": "MONSTER"
    },
    "confidence": 0.5
}

def create_detection_result():
    """Create DetectionResultModel from test data."""
    return DetectionResultModel(
        product=ProductModel(
            product_name=TEST_DATA["product"]["product_name"],
            brand=TEST_DATA["product"]["brand"],
            manufacturer_or_company=TEST_DATA["product"]["manufacturer_or_company"],
            category=TEST_DATA["product"]["category"]
        ),
        research_queries=TEST_DATA["research_queries"],
        evidence=EvidenceModel(
            product_name_text=TEST_DATA["evidence"]["product_name_text"],
            brand_text=TEST_DATA["evidence"]["brand_text"]
        ),
        confidence=TEST_DATA["confidence"]
    )

async def test_via_http():
    """Test the deep search agent via HTTP POST to Bureau endpoint."""
    
    detection_result = create_detection_result()
    
    # Create the DeepSearchRequest model instance
    request = DeepSearchRequest(detection_result=detection_result.model_dump())
    
    # Convert to dict using the Model's dict() method (Pydantic V1)
    request_dict = request.dict()
    
    # Bureau expects the envelope format with name, family, and payload
    bureau_payload = {
        "name": "deep_search_agent",
        "family": "Bearu",
        "payload": request_dict
    }
    
    print("=" * 80)
    print("Testing Deep Search Agent via HTTP")
    print("=" * 80)
    print(f"\nProduct: {detection_result.product.product_name}")
    print(f"Brand: {detection_result.product.brand}")
    print(f"Category: {detection_result.product.category}")
    print(f"Confidence: {detection_result.confidence}")
    print(f"\nResearch Queries ({len(detection_result.research_queries)}):")
    for i, query in enumerate(detection_result.research_queries, 1):
        print(f"  {i}. {query}")
    print("\n" + "=" * 80)
    print("Sending HTTP POST request to http://127.0.0.1:8000/submit...")
    print("=" * 80 + "\n")
    
    endpoint = "http://127.0.0.1:8000/submit"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                json=bureau_payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            print("✅ Successfully received response!")
            print("\n" + "=" * 80)
            print("Response Details")
            print("=" * 80)
            print(json.dumps(result, indent=2, default=str))
            print("\n" + "=" * 80)
            print("Test Complete!")
            print("=" * 80)
            
    except httpx.ConnectError:
        print("❌ Connection Error: Could not connect to the endpoint.")
        print(f"   Make sure the agents are running: python -m app.agents")
        print(f"   Expected endpoint: {endpoint}")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    print("\n🚀 Starting Deep Search Agent HTTP Test\n")
    asyncio.run(test_via_http())
