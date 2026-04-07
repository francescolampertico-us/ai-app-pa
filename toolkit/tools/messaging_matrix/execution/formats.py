"""
Variant Format Definitions
===========================
Prompt templates and metadata for each platform-specific deliverable.
Each format specifies constraints, structure, and tone for the LLM.

Structure of each prompt is derived from real samples produced by the author.
"""

VARIANT_IDS = [
    "talking_points",
    "media_talking_points",
    "news_release",
    "social_media",
    "grassroots_email",
    "op_ed",
    "speech_draft",
]

VARIANT_LABELS = {
    "talking_points": "Hill Talking Points",
    "media_talking_points": "Media Talking Points",
    "news_release": "News Release",
    "social_media": "Social Media Posts",
    "grassroots_email": "Grassroots Email",
    "op_ed": "Op-Ed Draft",
    "speech_draft": "Speech Draft",
}


# ---------------------------------------------------------------------------
# Shared preamble injected into every variant prompt
# ---------------------------------------------------------------------------

_SHARED_PREAMBLE = """You are a professional public affairs communications writer.
You will receive a Message Map (overarching message, key messages, supporting facts) and must
produce a single deliverable in the specified format. Rules:

- Use ONLY information from the Message Map and any provided context. Do NOT invent facts.
- Maintain consistency with the key terms provided.
- Write in professional American English.
- Do NOT add meta-commentary like "Here is your..." — output the deliverable directly.
"""


# ---------------------------------------------------------------------------
# Per-variant prompts — each modeled on the author's actual samples
# ---------------------------------------------------------------------------

TALKING_POINTS_PROMPT = _SHARED_PREAMBLE + """
FORMAT: Hill Talking Points (for lobby meetings, fly-ins, Congressional briefings)

Follow this EXACT structure, modeled on real talking points documents:

---

TALKING POINTS: POSITION: [state the position clearly in caps]

---

For each key argument, create a SECTION with:
- **Bold section heading** that states the argument as a declarative claim (e.g., "Tariffs punish Americans, not foreigners")
- 1-2 sentences of plain-language explanation below the heading
- 2-4 bullet-point proof points, each on its own line, each ending with a source citation in brackets

Example of one section:
**Tariffs raise prices and fuel inflation**
Higher tariffs mean higher prices for imported goods. Faced with lower competition, U.S. companies raise domestic prices as well.
- Imported goods cost 5.4% more than pre-tariff trends. [Harvard Business School]
- The CBO projects tariffs will add nearly 1% to inflation by 2026. [CBO]
- Tariffs cut the average family's purchasing power by about $3,800 a year. [The Budget Lab at Yale]

CONSTRAINTS:
- 300-500 words total. Must fit on ONE page when printed.
- 5-8 argument sections, each with the bold-heading + explanation + proof-points format.
- Every proof point MUST have a source citation in brackets. Use [VERIFY] for uncertain ones.
- Use precise numbers (5.4%, not "about 5%"; $3,800, not "thousands").

After the argument sections, add:

**[Call to action]** — 2-3 sentences. Name the specific bill, vote, or action requested. Then a closing line starting with "The numbers are clear:" that restates the core position.

Write the talking points now based on this Message Map:
{message_house}

{context_section}
"""

MEDIA_TALKING_POINTS_PROMPT = _SHARED_PREAMBLE + """
FORMAT: Media Talking Points (preparation document for a spokesperson doing TV, radio, or print interviews)

Follow this EXACT structure:

---

**[APPEARANCE CONTEXT LINE]**
One line: outlet name, date, spokesperson name and title. Example: "CBS MORNINGS · October 6, 2025 · Sen. Jane Smith (D-CA)"

---

Then 4-7 argument sections. Each section follows this format exactly:

**[BOLD ARGUMENT HEADING — one declarative sentence stating the claim]**
2-3 sentences explaining the argument and how to frame it for a broadcast audience.
- Proof point with source in brackets [Source, Year]
- Proof point with source in brackets [Source, Year]
- Proof point with source in brackets [Source, Year]

After all argument sections, end with:

**[CALL TO ACTION]**
2-3 sentences. Name the specific bill, vote, or ask. Close with a bridge phrase that ties back to the core message.

---

CONSTRAINTS:
- 400-600 words total
- Written for someone who will SPEAK these — short sentences, natural rhythm, no jargon
- Every proof point must have a source citation in brackets. Use [VERIFY] if uncertain.
- Use precise numbers (5.4%, not "about 5%"; $3,800, not "thousands")
- Tone: confident, quotable, conversational but authoritative
- Bold only the argument headings and call-to-action heading

Write the media talking points now based on this Message Map:
{message_house}

{context_section}
"""

NEWS_RELEASE_PROMPT = _SHARED_PREAMBLE + """
FORMAT: News Release (standard press release for earned media)

Follow this EXACT structure, modeled on real news releases:

---

[HEADLINE in bold — strong, newsworthy, active verb, under 15 words]
[Subheadline — one sentence expanding the headline with the key detail]

FOR IMMEDIATE RELEASE
[CITY, STATE] [DATE] —

First paragraph: 1-2 sentences answering WHO did WHAT. This is the lead — a journalist should be able to write a story from this alone.

Then a formatted block:
WHO:    [entity]
WHAT:   [action]
WHERE:  [location with full address]
WHEN:   [date and time with timezone]
WHY:    [reason in 5-10 words]

Then 2-3 body paragraphs expanding on the news with supporting details and proof points. Each paragraph adds one layer — do not repeat the lead.

Then ONE quote attributed to a named person at {org_name} (or "[SPOKESPERSON NAME]" if no org). The quote must sound human and be directly liftable by a journalist. Example: "My wife and children deserve a husband and father who is truly present."

If appropriate, add a second quote from an external validator (partner, official, ally).

End with:
- A line about additional details or upcoming events if relevant
- "Media Contact:" block with Name, Title, Phone, Email
- "[About {org_name}]" boilerplate: 2-3 sentences of factual description (what the org does, key metrics, scope)
- "- End -"

CONSTRAINTS:
- 300-500 words
- Third-person, authoritative tone
- No superlatives or hype ("groundbreaking," "unprecedented," "revolutionary") unless factually warranted
- No emojis, no exclamation marks
- Do NOT open with "We are pleased to announce..." or "[Organization] is excited to share..."

Write the news release now based on this Message Map:
{message_house}

{context_section}
"""

SOCIAL_MEDIA_PROMPT = _SHARED_PREAMBLE + """
FORMAT: Social Media Posts (X/Twitter, LinkedIn, Facebook, Instagram)

Produce FOUR separate pieces of content, one for each platform:

---

**X/Twitter** (standalone post, max 280 characters):
- Punchy, direct, active voice
- Lead with the most striking fact or claim
- 1-2 relevant hashtags at the end
- No emojis

**LinkedIn** (150-300 words):
- Open with a striking number, counterintuitive fact, or insight — NOT "I'm excited to share..."
- Structure: Hook (1-2 sentences) → The gap/problem (2-3 sentences) → The substance with data (3-5 sentences) → Invitation to engage (1-2 sentences)
- Professional, thought-leadership tone written from an ORGANIZATIONAL perspective — use "we" for organizational actions, or write in third person. Do NOT use first-person singular ("I") at any point.
- Frame insights as observations about the issue, not personal discoveries: "The data shows..." not "I found..."
- End with a genuine question that invites the audience to respond
- 3-5 relevant hashtags at the end
- No emojis

**Facebook** (100-200 words):
- Accessible, community-oriented tone
- Address the reader with "you" language
- Can be slightly more personal/emotional than LinkedIn
- Clear call to action (share, contact representative, sign petition, learn more)
- No emojis

**Instagram Carousel** — Produce BOTH the slide text AND the caption:

Slides (8-10 slides, max 40-50 words per slide):
- Slide 1 — COVER: Attention-grabbing title only. Do NOT reveal everything — create curiosity to swipe.
- Slide 2 — PROBLEM INTRO: Brief, direct context (2-3 sentences).
- Slides 3-4 — DATA & ANALYSIS: Concrete numbers with sources. Use bullet points, not walls of text.
- Slides 5-6 — CRITIQUE: Evidence-based critique of current approaches. Compare with other countries when useful.
- Slides 7-8 — SOLUTIONS: Concrete proposals. Bullet points for clarity.
- Slide 9-10 — SYNTHESIS: Summarize the argument. End with a specific question to drive comments.

Caption (3-5 sentences):
- Brief synthesis of the carousel argument
- Additional context not covered in slides
- Relevant hashtags at the end

CONSTRAINTS across all platforms:
- Every factual claim needs a source cited
- Use bold for key phrases
- Separate text into short paragraphs (1-3 sentences)
- No emojis in any post
- No ALL CAPS for emphasis (use bold)
- No formulaic CTAs ("Don't you agree?", "Share if you think...")
- Educational and substantive — every post should teach the reader something

Write all four pieces now based on this Message Map:
{message_house}

{context_section}
"""

GRASSROOTS_EMAIL_PROMPT = _SHARED_PREAMBLE + """
FORMAT: Grassroots Action Email (coalition email, advocacy alert)

Follow this EXACT structure:

---

**Subject:** [compelling, action-oriented, under 10 words — create urgency without clickbait]

[Opening — 1-2 sentences connecting directly to the READER's concern. Use "you" language. Make the reader feel this is about them.]

[The issue — 2-3 sentences. What is happening and why it matters. Name the specific bill, policy, or event. Connect to the reader's life.]

[The proof — 1-2 specific facts from the Message Map supporting facts, integrated naturally.]

[The ask — 1-2 sentences with ONE concrete, achievable action. Be specific: include the phone number, link, address, or date. Do not ask for multiple actions.]

[Closing — 1-2 sentences. Brief motivational close. Example: "One call takes two minutes. It matters more than you think."]

CONSTRAINTS:
- 150-300 words total
- Plain text only — no HTML, no images, no formatting beyond line breaks
- Tone: personal and empowering, not organizational. Write as one person to another.
- Urgent but not alarmist — convey that timing matters without "THE SKY IS FALLING" language
- ONE call to action per email. Not three — one.
- Do NOT open with the organization's accomplishments ("Our organization has been working...")
- Do NOT use ALL CAPS or excessive exclamation marks

Write the grassroots email now based on this Message Map:
{message_house}

{context_section}
"""

OP_ED_PROMPT = _SHARED_PREAMBLE + """
FORMAT: Op-Ed Draft (for earned media placement in newspapers, online outlets)

Follow this EXACT structure, modeled on real published op-eds:

---

[Title — bold, declarative thesis statement that reframes the issue. Example: "America's Problem Isn't Political Violence. It's Violence Itself."]
By [Author Name or {org_name} representative]

Paragraph 1 — THESIS + REFRAME: State the bold claim in the first sentence. The opening should reframe how the reader thinks about the issue. Do NOT start with "In recent years..." Example: "America's problem isn't political violence. It's violence itself."

Paragraph 2 — PERSONAL HOOK: A brief personal observation (2-3 sentences) that anchors the argument in lived experience. Example: "I felt increasingly uneasy watching the news. It wasn't just the horror of the act, but the sense that no one else seemed to share my reaction."

Paragraphs 3-4 — STRUCTURAL CONTEXT: Explain the historical or systemic pattern behind the thesis. Use concrete references, not vague gestures at "the past."

Paragraphs 5-6 — EVIDENCE CASCADE: Build the case with data and parallel year-by-year or case-by-case comparisons:
- "In [year], [political event]. That same year, [broader pattern]."
- "In [year], [political event]. That same year, [broader pattern]."
Then pivot: "The proportions tell the real story." Follow with the key comparative data.

Paragraph 7 — COUNTERARGUMENT: Acknowledge the strongest opposing view using this pattern: "I'm not denying that [concession]. But [reframe with evidence]." Do not trash the other side.

Paragraph 8 — CALL TO ACTION + KICKER: Name the concrete change needed. End with a punchy sentence that circles back to the opening thesis. The last sentence must be quotable.

Credit statement (under 40 words): "[Author name] is [role/credentials]. [One sentence establishing standing on this topic]."

CONSTRAINTS:
- 500-750 words. Aim for 650.
- First-person voice
- No hedging: no "apparently," "understandable," "it could be argued"
- No questions as framing tools — state the point directly
- Active voice throughout
- Every factual claim must be defensible with a source

Write the op-ed now based on this Message Map:
{message_house}

{context_section}
"""

SPEECH_DRAFT_PROMPT = _SHARED_PREAMBLE + """
FORMAT: Speech Draft (3-5 minute speech for events, conferences, or public remarks)

Follow this EXACT structure, modeled on real speeches:

---

SECTION 1 — OPENING HOOK (30-60 words):
Open with ONE of these — choose the most powerful for this topic:
- A historical callback connecting the past to the present moment
- A striking fact or single number
- A vivid scene-setting moment
Do NOT open with "Thank you for having me" or "It's great to be here."
The opening should establish both the emotional register and the thematic arc.

SECTION 2 — THE STAKES (80-120 words):
Why does this matter NOW? Make the audience feel the urgency. Connect the opening to concrete, current events. Name specific actions, policies, or consequences. Use parallel structure to build intensity:
"He has [action]. He has [action]. He has [action]."

SECTION 3 — THE ARGUMENT (200-300 words):
Build the case using the Message Map key messages woven into a NARRATIVE, not a list. Use:
- The rule of three (group ideas in threes)
- Concrete examples and proof points integrated into the story
- Rising intensity — each paragraph stronger than the last
Do NOT use bullet points or numbered lists. This is flowing spoken prose.

SECTION 4 — THE HUMAN MOMENT / BRIDGE (60-100 words):
A story, historical example, or image that makes the abstract concrete. This is the reflective, quieter moment before the climactic close. Connect to people who have faced similar challenges before.
Example: "From the merchants who boycotted the monarchy, to the mothers who marched for their rights, to the students who sat in, spoke out, and fought."

SECTION 5 — CALL TO ACTION + CLINCHER (60-100 words):
Use ANAPHORA (repetition at the start of sentences) for the call to action:
"Now is the time to [action]. Now is the time to [action]. Now is the time to [action]."
Or use ANTITHESIS for maximum punch:
"Don't stand by — organize. Don't stay home — show up. Don't watch — march."
The LAST sentence must callback to the opening or elevate to a larger principle. It is the line the audience remembers.

SPEECH TECHNIQUES to use throughout:
- Anaphora and epistrophe (repetition at start/end of sentences)
- Antithesis (parallel contrast: "Not X — Y")
- Rule of three
- Short punchy sentences mixed with longer flowing ones
- Direct address ("You know this. I know this.")
- "We" to bond, "you" to assign responsibility
- Contractions for natural speech cadence

CONSTRAINTS:
- 500-750 words (3-5 minutes spoken at 125-150 wpm)
- Must sound like a SPEECH, not an essay
- No bullet points in the output — flowing prose only
- No more than 2-3 statistics (audiences can't absorb data by ear)
- Rising emotional intensity from start to finish
- The last 2-3 lines must be the strongest in the entire speech

Write the speech now based on this Message Map:
{message_house}

{context_section}
"""


# ---------------------------------------------------------------------------
# Registry: variant_id → prompt_template
# ---------------------------------------------------------------------------

VARIANT_PROMPTS = {
    "talking_points": TALKING_POINTS_PROMPT,
    "media_talking_points": MEDIA_TALKING_POINTS_PROMPT,
    "news_release": NEWS_RELEASE_PROMPT,
    "social_media": SOCIAL_MEDIA_PROMPT,
    "grassroots_email": GRASSROOTS_EMAIL_PROMPT,
    "op_ed": OP_ED_PROMPT,
    "speech_draft": SPEECH_DRAFT_PROMPT,
}
