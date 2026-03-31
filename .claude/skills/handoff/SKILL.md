---
name: handoff
description: Generate a session handoff prompt so the next Claude Code session can resume work without losing context. Use at the end of any work session.
allowed-tools: Read, Glob, Grep, Bash
---

# Session Handoff Generator

## Goal
Produce a detailed continuation prompt that captures everything a fresh Claude Code session needs to pick up exactly where this one left off. Update the Project State section in CLAUDE.md so it stays current.

## Steps

1. **Gather context** — Review what was done this session:
   - Read recent git diff / git log to see what changed
   - Check the todo list for in-progress or pending items
   - Note any errors encountered or decisions made

2. **Update CLAUDE.md** — Edit the `## Project State` section at the bottom of CLAUDE.md with:
   - **Last session date**: today's date
   - **What was done**: bullet list of completed work
   - **What's in progress**: anything started but not finished
   - **Next steps**: prioritized list of what to do next
   - **Known issues**: any bugs, blockers, or things to watch out for

3. **Generate handoff prompt** — Output a ready-to-paste prompt formatted like this:

```
I'm continuing work on the PA AI Toolkit capstone project.

Last session ([date]), I:
- [what was done]

Still in progress:
- [anything unfinished]

Next priorities:
- [what to do next]

Known issues:
- [any blockers or gotchas]

Please read CLAUDE.md first, then pick up from where I left off.
```

## Rules
- Be specific with file paths and function names — generic summaries are useless
- Include the actual state of things (what works, what doesn't) not just what was attempted
- Keep the handoff prompt under 200 words — dense and actionable
- If there are no pending items, say so clearly
