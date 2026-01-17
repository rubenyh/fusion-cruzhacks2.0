# Testing Deep Search Agent

## Setup

1. Make sure you have all dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment variables in `.env`:
   ```
   PREPLEXITY_API_KEY=your_preplexity_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

## Running the Agents

Start the Bureau family with all agents:

```bash
cd backend/app
python agents.py
```

This will start all agents in the Bearu family on port 8000 with endpoint `http://127.0.0.1:8000/submit`.

## Testing the Deep Search Agent

### Option 1: Using the HTTP Test Script

```bash
python test_deep_search_http.py
```

This script sends the test data via HTTP POST to the Bureau endpoint.

### Option 2: Using the Direct Test Script

```bash
python test_deep_search.py
```

This script uses direct agent communication (requires agents to be running).

## Test Data

The test uses the following data for "MEGA MONSTER ENERGY":

```json
{
    "product": {
        "product_name": "MEGA MONSTER ENERGY",
        "brand": "MONSTER",
        "manufacturer_or_company": null,
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
```

## Expected Output

The deep search agent should:
1. Receive the DetectionResultModel
2. Perform searches for each research query
3. Clean and deduplicate evidence
4. Return a DeepSearchResponse with:
   - Cleaned evidence (recalls, lawsuits, warnings)
   - Aggregated answers
   - All sources
   - Updated confidence score

## Troubleshooting

- **Connection Error**: Make sure `agents.py` is running before running the test scripts
- **API Key Error**: Verify your `PREPLEXITY_API_KEY` is set correctly in `.env`
- **Import Error**: Make sure you're running from the `backend/app` directory or adjust imports
