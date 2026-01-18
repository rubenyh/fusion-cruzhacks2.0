"""
Simple and clean agents configuration - Product Safety Detection System
Flow: test_agent -> detect_agent -> deep_search_agent -> writer_agent
"""
from uagents import Agent, Bureau, Context, Model
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import os
import httpx
import asyncio
from agent_function import *
import json
load_dotenv()

# ============================================================================
# Models
# ============================================================================

class DetectionInput(Model):
    detection_result: Dict[str, Any]
    request_id: str
    callback_url: str

class DeepSearchRequest(Model):
    detection_result: Dict[str, Any]
    request_id: str
    callback_url: str

class CleanedEvidence(Model):
    product_name_text: Optional[str] = None
    brand_text: Optional[str] = None
    additional_findings: List[str] = []
    recalls: List[Dict[str, Any]] = []
    lawsuits: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []

class WriterRequest(Model):
    request_id: str
    callback_url: str
    product_name: str
    cleaned_evidence: CleanedEvidence
    aggregated_answers: List[str] = []
    all_sources: List[Dict[str, Any]] = []
    confidence: float = 0.0

class WriterResponse(Model):
    final_report: Dict[str, Any]
    status: str
# ============================================================================
# Test Agent - Sends test data to detect agent
# ============================================================================

# test_agent = Agent(
#     name="test_agent",
#     seed="test agent seed phrase",
#     port=8010,
# )

# @test_agent.on_event("startup")
# async def test_startup(ctx: Context):
#     ctx.logger.info(f"🧪 Test Agent Address: {test_agent.address}")
#     ctx.logger.info("Waiting 5 seconds before sending test message...")
#     await asyncio.sleep(5)
    
#     # Test data for MEGA MONSTER ENERGY
#     test_data = {
#         "product": {
#             "product_name": "MEGA MONSTER ENERGY",
#             "brand": "MONSTER",
#             "manufacturer_or_company": None,
#             "category": "Energy Drink"
#         },
#         "research_queries": [
#             "MONSTER MEGA MONSTER ENERGY lawsuit",
#             "MEGA MONSTER ENERGY ingredients complaint",
#             "Monster Energy drink recall",
#             "Monster Energy warnings",
#             "Monster Energy adverse events"
#         ],
#         "evidence": {
#             "product_name_text": "MEGA MONSTER ENERGY",
#             "brand_text": "MONSTER"
#         },
#         "confidence": 0.5
#     }
    
#     test_message = DetectionInput(detection_result=test_data)
    
#     ctx.logger.info(f"📤 Sending test message to Detect Agent...")
#     ctx.logger.info(f"   Product: {test_data['product']['product_name']}")
#     ctx.logger.info(f"   Brand: {test_data['product']['brand']}")
#     ctx.logger.info(f"   Queries: {len(test_data['research_queries'])}")
    
#     await ctx.send(detect_agent.address, test_message)
#     ctx.logger.info("✅ Test message sent!")

# ============================================================================
# Detect Agent - Receives detection and forwards to deep search
# ============================================================================

detect_agent = Agent(
    name="detect_agent",
    seed="detect agent seed",
    port=8001,
    endpoint=["http://127.0.0.1:8001/submit"],
)

@detect_agent.on_message(model=DetectionInput)
async def handle_detection(ctx: Context, sender: str, msg: DetectionInput):
    detection_dict = msg.detection_result
    product_name = detection_dict.get("product", {}).get("product_name", "Unknown")
    ctx.logger.info(f"🔍 Detect got product: {product_name}")

    await ctx.send(
        deep_search_agent.address,
        DeepSearchRequest(
            detection_result=detection_dict,
            request_id=msg.request_id,
            callback_url=msg.callback_url,
        )
    )


@detect_agent.on_event("startup")
async def detect_startup(ctx: Context):
    ctx.logger.info(f"🔍 Detect Agent Address: {detect_agent.address}")

# ============================================================================
# Deep Search Agent - Performs Perplexity searches and cleans evidence
# ============================================================================

deep_search_agent = Agent(
    name="deep_search_agent",
    seed="deep search agent seed",
    port=8002,
    endpoint=["http://127.0.0.1:8002/submit"],
)

async def perplexity_search(query: str) -> tuple[str, List[Dict[str, Any]]]:
    """Search using Perplexity API"""
    api_key = os.getenv("PREPLEXITY_API_KEY")
    if not api_key:
        return "API key not found", []
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use "sonar" model - it works (200 OK confirmed)
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides accurate information about product recalls, lawsuits, warnings, and safety concerns. Always cite your sources."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            # Get error details if request failed
            if response.status_code != 200:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get("error", {}).get("message", error_text)
                    error_type = error_json.get("error", {}).get("type", "unknown")
                    return f"Perplexity API Error ({response.status_code}): {error_type} - {error_msg}", []
                except:
                    return f"Perplexity API Error ({response.status_code}): {error_text[:200]}", []
            
            # Success - parse response
            data = response.json()
            
            # Extract answer
            answer = data.get("choices", [{}])[0].get("message", {}).get("content", "No answer found.")
            
            # Extract sources/citations and normalize to dicts
            sources = []
            raw_sources = []
            
            if "citations" in data:
                raw_sources = data["citations"]
            elif "sources" in data:
                raw_sources = data["sources"]
            elif "choices" in data and len(data["choices"]) > 0:
                # Sometimes citations are in the choice
                choice = data["choices"][0]
                if "citations" in choice:
                    raw_sources = choice["citations"]
            
            # Normalize sources to dictionaries
            for source in raw_sources:
                if isinstance(source, dict):
                    sources.append(source)
                elif isinstance(source, str):
                    # Convert string to dict
                    sources.append({"url": source, "title": source})
                else:
                    # Convert other types to dict
                    sources.append({"source": str(source)})
            
            return answer, sources
            
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        return f"Perplexity API Error: {error_msg}", []
    except Exception as e:
        return f"Error: {str(e)}", []


def clean_evidence(detection_dict: Dict, search_results: List[tuple]) -> CleanedEvidence:
    """Clean and deduplicate evidence from search results"""
    evidence = detection_dict.get("evidence", {})
    
    cleaned = CleanedEvidence(
        product_name_text=evidence.get("product_name_text"),
        brand_text=evidence.get("brand_text")
    )
    
    all_recalls = []
    all_lawsuits = []
    all_warnings = []
    all_findings = []
    
    for answer, sources in search_results:
        answer_lower = answer.lower()
        
        # Categorize findings
        if any(kw in answer_lower for kw in ["recall", "recalled", "recalls"]):
            all_recalls.append({"description": answer[:500], "sources": sources})
        
        if any(kw in answer_lower for kw in ["lawsuit", "litigation", "sued"]):
            all_lawsuits.append({"description": answer[:500], "sources": sources})
        
        if any(kw in answer_lower for kw in ["warning", "advisory", "alert", "caution"]):
            all_warnings.append({"description": answer[:500], "sources": sources})
        
        if answer and answer not in all_findings:
            all_findings.append(answer[:300])
    
    # Deduplicate findings
    unique_findings = []
    for finding in all_findings:
        is_duplicate = False
        for existing in unique_findings:
            words_finding = set(finding.lower().split())
            words_existing = set(existing.lower().split())
            if words_finding and words_existing:
                overlap = len(words_finding & words_existing) / len(words_finding | words_existing)
                if overlap > 0.8:
                    is_duplicate = True
                    break
        if not is_duplicate:
            unique_findings.append(finding)
    
    cleaned.additional_findings = unique_findings[:10]
    cleaned.recalls = all_recalls[:5]
    cleaned.lawsuits = all_lawsuits[:5]
    cleaned.warnings = all_warnings[:5]
    
    return cleaned

@deep_search_agent.on_message(model=DeepSearchRequest)
async def handle_deep_search(ctx: Context, sender: str, msg: DeepSearchRequest):
    ctx.logger.info(f"🔎 Deep Search Agent received request from {sender}")
    
    detection_dict = msg.detection_result
    product_name = detection_dict.get("product", {}).get("product_name", "Unknown")
    ctx.logger.info(f"   Product: {product_name}")
    

    request_id = detection_dict.get("request_id")
    callback_url = detection_dict.get("callback_url")
    # Get research queries
    queries = detection_dict.get("research_queries", [])
    
    if not queries:
        # Fallback queries
        product = detection_dict.get("product", {})
        if product.get("product_name"):
            queries.append(f"{product['product_name']} recall lawsuit warning")
        if product.get("brand"):
            queries.append(f"{product['brand']} product safety concerns")
    
    # Perform searches
    ctx.logger.info(f"🔍 Performing {len(queries[:5])} searches...")
    search_results = []
    all_sources = []
    aggregated_answers = []
    
    for query in queries[:5]:  # Limit to 5
        ctx.logger.info(f"   Searching: {query}")
        answer, sources = await perplexity_search(query)
        search_results.append((answer, sources))
        aggregated_answers.append(answer)
        # Ensure all sources are dicts before extending
        normalized_sources = []
        for source in sources:
            if isinstance(source, dict):
                normalized_sources.append(source)
            elif isinstance(source, str):
                normalized_sources.append({"url": source, "title": source})
            else:
                normalized_sources.append({"source": str(source)})
        all_sources.extend(normalized_sources)
    
    # Clean evidence
    cleaned_evidence = clean_evidence(detection_dict, search_results)
    
    # Calculate confidence
    confidence = detection_dict.get("confidence", 0.0)
    if cleaned_evidence.recalls or cleaned_evidence.lawsuits or cleaned_evidence.warnings:
        confidence = min(1.0, confidence + 0.2)
    
    
    
    # Create response
    response = DeepSearchResponse(
        cleaned_evidence=cleaned_evidence,
        aggregated_answers=aggregated_answers,
        all_sources=all_sources,
        confidence=confidence,
        
    )
    
    ctx.logger.info(f"✅ Search completed!")
    ctx.logger.info(f"   Recalls: {len(cleaned_evidence.recalls)}")
    ctx.logger.info(f"   Lawsuits: {len(cleaned_evidence.lawsuits)}")
    ctx.logger.info(f"   Warnings: {len(cleaned_evidence.warnings)}")
    
    
    # Forward to writer agent
    ctx.logger.info(f"📤 Forwarding formatted report to Writer Agent...")
    writer_request = WriterRequest(
        cleaned_evidence=cleaned_evidence,
        aggregated_answers=aggregated_answers,
        all_sources=all_sources,
        confidence=confidence,
        product_name = product_name
    )
    
    writer_response = await ctx.send(writer_agent.address, writer_request)
    
    if isinstance(writer_response, WriterResponse):
        ctx.logger.info(f"✅ Writer Agent completed report generation")
        # Send both responses back
        await ctx.send(sender, response)
    else:
        # Send deep search response even if writer fails
        await ctx.send(sender, response)

@deep_search_agent.on_event("startup")
async def deep_search_startup(ctx: Context):
    ctx.logger.info(f"🔎 Deep Search Agent Address: {deep_search_agent.address}")

# ============================================================================
# Writer Agent - Generates final report from formatted data
# ============================================================================

writer_agent = Agent(
    name="writer_agent",
    seed="writer agent seed",
    port=8003,
    endpoint=["http://127.0.0.1:8003/submit"],
)

@writer_agent.on_message(model=WriterRequest)
async def handle_writer(ctx: Context, sender: str, msg: WriterRequest):
    ctx.logger.info(f"✍️  Writer Agent received report for {msg.product_name}")
    payload = msg.model_dump()   # IMPORTANT (convert Model -> dict)
    result = await write_summary(payload)
    cleaned = clean_json_response(result)
    final_report = json.loads(cleaned)

    ctx.logger.info(f"✅ Final report generated")
    
    
    response = WriterResponse(
        final_report=final_report,
        status="success"
    )
    ctx.logger.info(f"🔍 Final report: {final_report}")
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            msg.callback_url,
            json={"final_report": final_report}
        )
    await ctx.send(sender, response)
    ctx.logger.info(f"✅ Report sent to webhook for request_id={msg.request_id}")
@writer_agent.on_event("startup")
async def writer_startup(ctx: Context):
    ctx.logger.info(f"✍️  Writer Agent Address: {writer_agent.address}")

# advisor_agent = Agent(
#     name="advisor_agent",
#     seed="advisor agent seed",
#     port=8004,
#     endpoint=["http://127.0.0.1:8004/submit"],
# )

# class AdvisorRequest(Model):
#     final_report : Dict

# class AdvisorResponse(Model):
#     test:any

# @advisor_agent.on_message(model=AdvisorRequest)
# async def handle_writer(ctx: Context, sender: str, msg: WriterRequest):
#     ctx.logger.info(f"✍️  Writer Agent received report for {msg.product_name}")
#     payload = msg.model_dump()   # IMPORTANT (convert Model -> dict)
#     result = await write_summary(payload)
#     cleaned = clean_json_response(result)
#     final_report = json.loads(cleaned)

#     ctx.logger.info(f"✅ Final report generated")
    
    
#     response = WriterResponse(
#         final_report=final_report,
#         status="success"
#     )
#     ctx.logger.info(f"🔍 Final report: {final_report}")
    
#     await ctx.send(sender, response)

# @writer_agent.on_event("startup")
# async def writer_startup(ctx: Context):
#     ctx.logger.info(f"✍️  Writer Agent Address: {writer_agent.address}")



# ============================================================================
# Bureau Family Setup
# ============================================================================

family = Bureau(
    port=8000,
    endpoint="http://127.0.0.1:8000/submit"
)

family.add(detect_agent)
family.add(deep_search_agent)
family.add(writer_agent)
# family.add(test_agent)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    family.run()
