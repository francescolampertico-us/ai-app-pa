---
name: messaging-matrix
description: Generate a messaging matrix with Message House and platform-specific deliverables from a policy position. Use when user asks to create talking points, press statement, messaging, social media posts, or campaign communications.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Messaging Matrix Generator

## Goal
Produce a Message House (core message, pillars, proof points) and platform-specific communication variants (Hill talking points, press statement, social media posts, grassroots email, op-ed draft) from a core policy position.

## Inputs
- **position**: Core policy position or message intent — REQUIRED
- **context**: Supporting material (bill summary, hearing excerpt, news clips) — optional but recommended
- **organization**: Organization name for attribution — optional
- **audience**: Primary target audience — optional
- **variants**: Comma-separated list of deliverables (talking_points, press_statement, social_media, grassroots_email, op_ed) — optional, defaults to all

## Scripts
- `tools/messaging_matrix/execution/run.py` — Full pipeline: Message House → variant generation → DOCX export

## Process

### Step 1: Run the generator
```bash
python3 tools/messaging_matrix/execution/run.py \
  --position "POSITION_TEXT" \
  --context "CONTEXT_TEXT" \
  --organization "ORG_NAME" \
  --audience "AUDIENCE" \
  --out output/
```

Or with context from a file:
```bash
python3 tools/messaging_matrix/execution/run.py \
  --position "Support the AI Safety Act" \
  --context-file path/to/bill_summary.md \
  --organization "TechForward Alliance" \
  --out output/
```

### Step 2: Verify outputs
- `output/messaging_matrix.md` — Full markdown report
- `output/messaging_matrix.docx` — Professional Word document

### Step 3: Review checklist (Risk: Yellow)
- Verify all proof points against primary sources
- Check core message reflects the organization's actual position
- Review talking points for unintended concessions
- Confirm press statement quotes are approved
- Check social media posts for character limits and platform rules
- Ensure no confidential information in public-facing variants

## Non-negotiables
- Never fabricate specific statistics, dates, or quotes
- Mark uncertain proof points with [VERIFY]
- All variants must be consistent with the Message House core message
- Do not add partisan framing unless explicitly requested

## Two-step LLM architecture
1. **Step 1** (gpt-4o): Generates the Message House — strategic, high-quality reasoning
2. **Step 2** (gpt-4o-mini per variant): Adapts the Message House into each format — cheaper, format-focused

This separation ensures strategic quality at the foundation level while keeping variant generation fast and cost-effective.
