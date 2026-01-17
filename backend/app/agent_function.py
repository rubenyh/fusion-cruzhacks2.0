from groq import Groq
from dotenv import load_dotenv
import os
import re
load_dotenv()
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

async def write_summary(msg): 
    writing_prompt = f"""You are a risk intelligence analyst generating a standardized, executive-ready,
1-page report based on deep search results (lawsuits, recalls, and regulatory warnings)
for a specific product.

Your goal is to produce a report that is:
- Consistent in structure across all products
- Risk-weighted (severity over volume)
- Concise enough to fit on a single PDF page
- Neutral, factual, and compliance-safe

You must strictly follow the format, limits, and rules below.

========================
INPUTS (PROVIDED EACH RUN)
========================
- Product name : "{msg['product_name']}"
- Cleaned Evidence :"{msg['cleaned_evidence']}"
- Aggregated answers :"{msg['aggregated_answers']}"
- All sources : "{msg['all_sources']}"
- Confidence : "{msg['confidence']}"

Do NOT invent facts, infer legal conclusions, or speculate beyond the provided data.

========================
OUTPUT REQUIREMENTS
========================
- Use headings, tables, and bullet points only
- Maintain the same structure every time
- Aggregate by themes when data volume is large
- Use neutral, professional language
- Ensure the content fits on ONE PAGE when converted to PDF

========================
REQUIRED REPORT FORMAT
========================

Title:
Risk Summary: [Product Name]

Subtitle:
Category: [Product Category] | Timeframe: [Timeframe Reviewed]

---

Executive Summary (STRICT: 3–4 bullets only)
- Total findings reviewed: X lawsuits, Y recalls, Z warnings
- Primary risk themes identified (1–2 themes only)
- Most material exposure area (legal / regulatory / reputational)
- Overall risk level: Low / Medium / High (based on severity, not count)

---

Findings Overview (TABLE – required)

| Category  | Count | Key Issues Identified (themes only) | Timeframe |
|----------|-------|------------------------------------|-----------|
| Lawsuits | X     | Aggregated themes                  | YYYY–YYYY |
| Recalls  | Y     | Aggregated themes                  | YYYY–YYYY |
| Warnings | Z     | Aggregated themes                  | YYYY–YYYY |

---

Key Notable Examples
STRICT LIMIT: MAX 2 bullets per category. Never exceed this.

Lawsuits:
- One-line example describing issue + status
- One-line example describing issue + status

Recalls:
- One-line example describing risk + scope
- One-line example describing risk + scope

Warnings:
- One-line example describing compliance issue
- One-line example describing compliance issue

If a category has no material examples, state:
"No material examples identified."

---

Risk Implications (STRICT: 2–3 bullets only)
- What Ingredients can cause what health risks (example: Ingredient A can cause Cancer(Cancer Risks))

---

Recommendations (STRICT: 2–4 bullets only)
- Advice whether or not the user should eat it and if there should be a limit
- Also give general advice to this product if needed

---

Footer (STRICT: 1–2 lines only)
Methodology: Publicly available lawsuits, recall databases, and regulatory warnings reviewed via deep search.
Disclaimer: Informational summary only.

========================
ENFORCEMENT RULES
========================
- Never exceed bullet limits in any section
- Never exceed 2 bullets per category in Key Notable Examples
- Prioritize severity and decision impact over volume
- Use aggregation when findings are numerous
- Total bullet count across the report should remain concise (target ≤16)
- The report must be readable in under 90 seconds

Before finalizing output, internally verify that all constraints are satisfied.
 Example:
{{
  "title": "Risk Summary: <string>",
  "subtitle": {{
    "category": "<string>",
    "timeframe_reviewed": "<string>"
  }},

  "executive_summary": {{
    "bullets": [
      "<string>",
      "<string>",
      "<string>"
    ],
    "overall_risk_level": "Low|Medium|High",
    "totals": {{
      "lawsuits": "<integer>",
      "recalls": "<integer>",
      "warnings": "<integer>"
    }},
    "primary_risk_themes": [
      "<string>",
      "<string>"
    ],
    "most_material_exposure_area": "legal|regulatory|reputational|operational"
  }},

  "findings_overview_table": [
    {{
      "category": "Lawsuits",
      "count": "<integer>",
      "key_issues_themes_only": [
        "<string>",
        "<string>"
      ],
      "timeframe": "<string>"
    }},
    {{
      "category": "Recalls",
      "count": "<integer>",
      "key_issues_themes_only": [
        "<string>",
        "<string>"
      ],
      "timeframe": "<string>"
    }},
    {{
      "category": "Warnings",
      "count": "<integer>",
      "key_issues_themes_only": [
        "<string>",
        "<string>"
      ],
      "timeframe": "<string>"
    }}
  ],

  "key_notable_examples": {{
    "lawsuits": [
      {{
        "bullet": "<string>",
        "status": "<string|null>",
        "source_urls": ["<string>"]
      }}
    ],
    "recalls": [
      {{
        "bullet": "<string>",
        "scope": "<string|null>",
        "source_urls": ["<string>"]
      }}
    ],
    "warnings": [
      {{
        "bullet": "<string>",
        "source_urls": ["<string>"]
      }}
    ]
  }},

  "risk_implications": {{
    "bullets": [
      "bullet": "<string>"
    ]
  }},

  "recommendations": {{
    "bullets": [
      "<string>",
      "<string>"
    ]
  }},

  "footer": {{
    "methodology_line": "Methodology: Publicly available lawsuits, recall databases, and regulatory warnings reviewed via deep search.",
    "disclaimer_line": "Disclaimer: Informational summary only; not legal advice."
  }},

  "constraints_check": {{
    "executive_summary_bullets_count": "<integer>",
    "implications_bullets_count": "<integer>",
    "recommendations_bullets_count": "<integer>",
    "notable_examples_counts": {{
      "lawsuits": "<integer>",
      "recalls": "<integer>",
      "warnings": "<integer>"
    }},
    "total_bullets_estimate": "<integer>",
    "fits_one_page_estimate": "pass|fail",
    "notes": ["<string>"]
  }}
}}
Now process this message: "{msg}"
Before returning, always check that all brackets and quotes are closed and the JSON is valid.
Return ONLY valid JSON. No markdown.

"""
    
    response = client.chat.completions.create(
        model="moonshotai/kimi-k2-instruct-0905",  # Updated model
        messages=[
            {"role": "system", "content": "You are a risk intelligence analyst. Return ONLY valid JSON. No markdown."},
            {"role": "user", "content": writing_prompt}
        ],
        max_tokens=1200
    )
    
    result = response.choices[0].message.content.strip()
    return result


def clean_json_response(text: str) -> str:
    text = text.strip()
    # strip markdown fences if any
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

