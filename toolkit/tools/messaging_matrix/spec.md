# Messaging Matrix

## Purpose
Generate a structured Message House and platform-specific communication variants from a core policy position. Bridges strategic messaging (DiGiacomo Process #4) and operational content production — the step between "what is our position" and "what do we publish."

Grounded in professional PA practice: the Message House architecture (core message → 3 pillars → proof points) used by major firms (Edelman, APCO, FTI), validated by practitioners (Mike/Beekeeper Group: "working with clients to come up with a messaging matrix, and then using that to build out all the content").

## When to use
- A client or organization has a policy position and needs campaign-ready deliverables.
- Rapid response: news breaks and the team needs talking points, a press statement, and social posts fast.
- Preparing for a Hill fly-in or lobby day (talking points + leave-behind one-pager).
- Translating a hearing memo or bill summary into actionable communications.
- Building a coordinated multi-platform advocacy push.

## Inputs (Directive)
### Required
- `position` — Core policy position or message intent. Can be a sentence or a paragraph.
  Example: "Support the AI Safety Act — mandatory pre-deployment testing protects consumers without stifling innovation."

### Optional
- `context` — Supporting material to ground the messaging in facts. Paste a bill summary, hearing memo excerpt, media clips, or background research. The more context, the more specific the proof points.
- `organization` — Organization name for attribution (e.g., "TechForward Alliance"). Used in press statement and op-ed.
- `target_audience` — Primary audience to emphasize (e.g., "Senate Commerce Committee members"). Shifts emphasis across all variants.
- `variants` — Comma-separated list of which deliverables to generate. Options: `talking_points`, `press_statement`, `social_media`, `grassroots_email`, `op_ed`. Default: all five.

## Output Contract

### Message House (`message_house` section)
- **Core Message** — One sentence umbrella statement
- **Pillar 1-3** — Each with:
  - Pillar name
  - 2-3 sentence supporting argument
  - 2-3 proof points (specific facts, stats, case studies, third-party validators)
- **Key Terms** — Consistent terminology to use across all variants
- **Target Audiences** — Who the messaging addresses

### Platform Variants
Each variant follows format-specific constraints:

| Variant | Length | Tone | Structure |
|---------|--------|------|-----------|
| Hill Talking Points | 300-500 words | Direct, data-driven | Bulleted, one-page format |
| Press Statement | 300-500 words | Authoritative, third-person | Standard press release format with liftable quotes |
| Social Media Posts | Platform-specific | Conversational, sharp | Separate posts for X, LinkedIn, Facebook |
| Grassroots Email | 150-300 words | Personal, empowering | Action-oriented with clear CTA |
| Op-Ed Draft | 500-800 words | Authoritative, first-person | News peg → argument → call to action |

## Limitations / Failure Modes
- **No real-time data**: Proof points come from provided context or model knowledge — may be outdated or hallucinated. Always verify.
- **Generic without context**: If no supporting material is provided, variants will be strategically sound but vague on specifics. Provide context for better output.
- **Brand voice mismatch**: Generated tone is professional-generic. Organizations with strong brand voice should edit for consistency.
- **Political framing**: The model may introduce implicit framing. Review for unintended partisan lean.
- **Social media platform rules**: Posts should be reviewed for character limits, hashtag conventions, and platform-specific compliance.

## Human Review Checklist (Risk: Yellow)
- Verify all proof points and cited facts against primary sources.
- Check that the core message accurately reflects the organization's position.
- Review talking points for unintended concessions or framing the opposition could exploit.
- Confirm press statement quotes are attributable and approved by the spokesperson.
- Review social media posts for character limits, hashtags, and platform appropriateness.
- Ensure grassroots email CTA is actionable and links/actions exist.
- Check op-ed for a clear news peg and that it reads as authentic first-person voice.
- Confirm no confidential or embargoed information appears in public-facing variants.
