import os
import json
try:
    import openai
except ImportError:
    openai = None


class IRS990LLMEnricher:
    """
    Phase 3: Selective LLM Enrichment.
    Uses GPT-4o-mini to read deterministic data + narratives and output
    subjective PA relevance fields.
    """
    def __init__(self, api_key: str = None):
        if not openai:
            raise ImportError("The 'openai' package is not installed. Run: pip install openai")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for deep mode.")

        self.client = openai.OpenAI(api_key=self.api_key)

    def extract_insights(self, org_name: str, narrative_blocks: str, structured_data: dict) -> dict:
        """
        Calls GPT-4o-mini to derive subjective tags and summaries
        based on raw 990 segments.
        """
        system_prompt = """You are a senior Public Affairs and Compliance analyst.
Your task is to review segments of an IRS Form 990 for a nonprofit organization and extract subjective, interpretive insights regarding their policy relevance, influence capacity, and operational risks.

Return a JSON object with these exact keys:
- pa_relevance_score: integer 1-5 (5 = highly relevant to public policy/advocacy)
- one_sentence_org_profile: one sentence summary of what they do
- issue_area_tags: comma-separated list of 3-5 policy topics
- top_influence_signals: comma-separated list of how they wield influence
- top_risk_flags: comma-separated list of governance/reputational risks identified
- likely_advocacy_tactics_named: comma-separated list (e.g. litigation, direct lobbying, issue ads)
- likely_target_institutions_named: comma-separated list of targets (e.g. Congress, EPA, State Legislatures)"""

        prompt = f"""Organization: {org_name}

Structured Data Context (Lobbying, Grants, Execs):
{json.dumps(structured_data, indent=2)}

Narrative Blocks (Mission, Programs, Schedule O explanations):
{narrative_blocks}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content.strip()
            return json.loads(content)

        except Exception as e:
            print(f"[WARNING] LLM Enrichment Error for {org_name}: {e}")
            return {}
