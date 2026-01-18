# Product Safety Detection Agents

Simple and clean agent system for product safety detection using Perplexity search.

## Architecture

```
test_agent → detect_agent → deep_search_agent
```

### Flow:
1. **test_agent**: Sends test data automatically on startup
2. **detect_agent**: Receives detection result and forwards to deep search
3. **deep_search_agent**: Performs Perplexity searches and cleans evidence

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables in `.env`:
   ```
   PREPLEXITY_API_KEY=your_preplexity_api_key_here
   ```

## Running

Start all agents:
```bash
python agents.py
```

The test agent will automatically send test data after 5 seconds.

## Test Data

The test agent sends data for "MEGA MONSTER ENERGY":
- Product: MEGA MONSTER ENERGY
- Brand: MONSTER
- Category: Energy Drink
- 5 research queries for recalls, lawsuits, warnings

## Agent Addresses

When agents start, they will log their addresses. Use these addresses to send messages between agents.

## Output

The deep search agent will:
1. Search Perplexity for each research query
2. Clean and deduplicate evidence
3. Categorize findings into recalls, lawsuits, and warnings
4. Return cleaned evidence with confidence score

## Ports

- Bureau: 8000
- detect_agent: 8001
- deep_search_agent: 8002
- test_agent: 8010
