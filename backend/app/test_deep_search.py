"""
Test script for deep search agent
Sends test data to the deep_search_agent via HTTP (Bureau endpoint)
This is the recommended way to test agents in uagents
"""
import asyncio
import httpx
import json
from DetectService import DetectionResultModel, ProductModel, EvidenceModel

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

async def test_deep_search_agent():
    """Test the deep search agent with the provided test data via HTTP."""
    
    # Build the DetectionResultModel from test data
    detection_result = DetectionResultModel(
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
    print("Sending HTTP POST request to Bureau endpoint...")
    print("=" * 80 + "\n")
    
    # Create the DeepSearchRequest model instance
    from deep_search_agent import DeepSearchRequest
    request = DeepSearchRequest(detection_result=detection_result.model_dump())
    
    # Convert to dict using the Model's dict() method (Pydantic V1)
    request_dict = request.dict()
    
    # Bureau expects the envelope format with name, family, and payload
    bureau_payload = {
        "name": "deep_search_agent",
        "family": "Bearu",
        "payload": request_dict
    }
    
    endpoint = "http://127.0.0.1:8000/submit"
    
    print("Request payload:")
    print(json.dumps(bureau_payload, indent=2, default=str))
    print("\n")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                endpoint,
                json=bureau_payload,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            
            print("✅ Successfully received response from deep_search_agent!")
            print("\n" + "=" * 80)
            print("Response Details")
            print("=" * 80)
            
            # Parse the response
            if "message" in result:
                result = result["message"]
            
            confidence = result.get("confidence", 0.0)
            cleaned_evidence = result.get("cleaned_evidence", {})
            
            print(f"\nConfidence: {confidence}")
            print(f"\nCleaned Evidence:")
            print(f"  Product Name Text: {cleaned_evidence.get('product_name_text', 'N/A')}")
            print(f"  Brand Text: {cleaned_evidence.get('brand_text', 'N/A')}")
            
            recalls = cleaned_evidence.get("recalls", [])
            lawsuits = cleaned_evidence.get("lawsuits", [])
            warnings = cleaned_evidence.get("warnings", [])
            findings = cleaned_evidence.get("additional_findings", [])
            
            print(f"\n  Recalls Found: {len(recalls)}")
            for i, recall in enumerate(recalls[:5], 1):
                desc = recall.get('description', '')[:100] if isinstance(recall, dict) else str(recall)[:100]
                print(f"    {i}. {desc}...")
            
            print(f"\n  Lawsuits Found: {len(lawsuits)}")
            for i, lawsuit in enumerate(lawsuits[:5], 1):
                desc = lawsuit.get('description', '')[:100] if isinstance(lawsuit, dict) else str(lawsuit)[:100]
                print(f"    {i}. {desc}...")
            
            print(f"\n  Warnings Found: {len(warnings)}")
            for i, warning in enumerate(warnings[:5], 1):
                desc = warning.get('description', '')[:100] if isinstance(warning, dict) else str(warning)[:100]
                print(f"    {i}. {desc}...")
            
            print(f"\n  Additional Findings: {len(findings)}")
            for i, finding in enumerate(findings[:3], 1):
                print(f"    {i}. {str(finding)[:100]}...")
            
            print(f"\n  Total Sources: {len(result.get('all_sources', []))}")
            print(f"  Aggregated Answers: {len(result.get('aggregated_answers', []))}")
            
            print("\n" + "=" * 80)
            print("Full Response (JSON):")
            print("=" * 80)
            print(json.dumps(result, indent=2, default=str))
            
            print("\n" + "=" * 80)
            print("Test Complete!")
            print("=" * 80)
            
    except httpx.ConnectError:
        print("❌ Connection Error: Could not connect to the endpoint.")
        print(f"   Make sure the agents are running: python agents.py")
        print(f"   Expected endpoint: {endpoint}")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🚀 Starting Deep Search Agent Test\n")
    asyncio.run(test_deep_search_agent())
