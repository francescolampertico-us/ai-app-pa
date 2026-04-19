# Agent Instructions — Pitch Drafting

## Objective

Draft a short, personalized journalist pitch email for a single reporter. The output should read like a real public affairs professional writing to a real journalist — not like a PR template or an AI summary.

## Source hierarchy

1. `pitch_instructions/pitch_best_practices.txt` — foundational rules
2. `PITCH_STYLE_GUIDE.md` — house rules for structure, tone, and banned phrases
3. `pitch_agent_instructions.md` — this file; specific drafting rules
4. `pitch_examples/` — calibration only; do not copy topic framing or sentence structure

If sources conflict, follow this file and the style guide.

## Core behavior

- Write for one journalist at a time. Every sentence should make sense for this specific person at this specific outlet.
- Personalize the opener with the journalist's actual prior story — one sentence, not a paragraph of flattery.
- Lead with the development, not the issue category.
- State why this is newsworthy NOW — a specific event, deadline, vote, ruling, or newly available document.
- Make one concrete offer. Not a vague "briefing" — name what you are offering and who is providing it.
- End with one light CTA. Not three nested asks.

## Email structure

**Subject line:**
- Signal the development or access, not the topic
- Under 10 words
- No "EXCLUSIVE," "URGENT," or rhetorical questions
- Bad: "Story idea — emerging AI regulation landscape"
- Good: "Comment period closes Friday — FTC data broker rule"

**Opening line:**
- Reference the specific article the reporter wrote (title and approximate date if known)
- One sentence. Move on immediately.
- Bad: "I've been following your great coverage of telecom policy..."
- Good: "You covered the FCC spectrum auction in February — there's a direct follow."

**The development:**
- State specifically what happened, changed, or is imminent
- Name the bill, agency, ruling, date, filing, or person involved
- One short paragraph, 2–3 sentences max

**Why it matters to their audience:**
- One sentence. Not a paragraph explaining the issue.

**The offer:**
- One thing. Specific. Grounded.
- Bad: "We would be happy to provide a brief background briefing."
- Good: "Our policy director — who drafted the comment — is available for a background call this week."
- Bad: "We have exclusive data showing..."
- Good: "The filing is public — I can send the key passages."

**CTA:**
- One sentence. Light. Non-pushy.
- Bad: "Please let me know if you would be interested in learning more, scheduling a call, or reviewing our materials."
- Good: "Happy to connect you if useful."

## Hard rules

- Do not fabricate facts, sources, exclusives, attachments, data, or access.
- Do not imply the reporter will get exclusive information unless you actually have it.
- Do not overstate the evidence. If the issue is contested, say so.
- Do not use: "emerging legislative language," "timely update," "updating consensus," "brief briefing," "gaining traction," "given recent developments," "I think this could be a great fit."
- Do not write a mass-email tone. It must read as written for this person.
- Do not exceed 200 words in the body.
- Do not open with the organization's name or history.
- Do not pad the closing with multiple alternative offers.

## Degrading gracefully

If the `pitch_angle` or `why_now` fields are vague or missing:
- Build from whatever specific article title and reporter coverage is available
- Do not invent a hook — use what is grounded
- If no concrete development is available, state the issue clearly and offer the one specific thing you can provide (source name, filing, comment)

## Output

Return `subject` and `body`. The body should be ready to send after one human review pass.
