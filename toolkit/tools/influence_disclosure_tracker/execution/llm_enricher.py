import os
import json
import re
try:
    import openai
except ImportError:
    openai = None

_DEFAULT_MODEL = "ChangeAgent"


def _active_model() -> str:
    return os.environ.get("LLM_MODEL_OVERRIDE") or _DEFAULT_MODEL


def _response_format_kwarg() -> dict:
    # Skip JSON mode when a model override is active (e.g. ChangeAgent may not support it)
    if os.environ.get("LLM_MODEL_OVERRIDE"):
        return {}
    return {"response_format": {"type": "json_object"}}


def _parse_json_content(content: str) -> dict:
    if not content:
        return {}
    text = content.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    last = text.rfind("}")
    if last != -1:
        try:
            return json.loads(text[: last + 1])
        except json.JSONDecodeError:
            pass
    return {}


class IRS990LLMEnricher:
    """
    Phase 3: Selective LLM Enrichment.
    Reads deterministic 990 data + narratives and outputs subjective PA relevance fields.
    Respects LLM_MODEL_OVERRIDE and OPENAI_BASE_URL env vars so it works with
    any model including ChangeAgent.
    """
    def __init__(self, api_key: str = None):
        if not openai:
            raise ImportError("The 'openai' package is not installed. Run: pip install openai")

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for deep mode.")

        # Respect OPENAI_BASE_URL so ChangeAgent and other compatible endpoints work
        base_url = os.environ.get("OPENAI_BASE_URL")
        client_kwargs: dict = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = openai.OpenAI(**client_kwargs)

    def extract_insights(self, org_name: str, narrative_blocks: str, structured_data: dict) -> dict:
        """
        Calls the active LLM to derive subjective tags and summaries
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
                model=_active_model(),
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                **_response_format_kwarg(),
            )

            content = response.choices[0].message.content or ""
            result = _parse_json_content(content)
            if not result:
                print(f"[WARNING] LLM Enrichment: could not parse JSON response for {org_name}")
            return result

        except Exception as e:
            print(f"[WARNING] LLM Enrichment Error for {org_name}: {e}")
            return {}
