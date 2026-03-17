# Agent Boundaries - What Lives in the Repo vs the App

## Repo responsibilities

The repo should own:
- tool contract
- style guide
- risk policy
- schemas
- reusable skills
- prompts
- heading policy
- speaker-label policy
- evaluation cases
- examples of good outputs

These assets define what the tool is.

## App responsibilities

The app should own:
- file upload and parsing
- data flow orchestration
- runtime model selection
- retries
- state management
- reviewer interface
- export to docx / pdf / email
- page footer rendering
- logging and version history

These assets define how the tool runs.

## Important formatting split

The content layer should output the confidentiality text once.
If the final document needs the confidentiality footer repeated on every page, that repetition belongs to the export layer, not to the text-generation layer.

## Rule of thumb

If a decision changes meaning, quality, tone, structure, or reviewability, it belongs in the repo.
If a decision changes transport, UI, document rendering, or execution plumbing, it belongs in the app.
