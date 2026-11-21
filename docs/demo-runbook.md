# Presentation and walkthrough runbook

Refs #16, #48. Use a reviewed build and synthetic accounts. Verify the actual site/API health before presenting. A local fixture demonstration must be labelled as such; a live-AI demonstration requires the server-side provider credential and an observed successful request.

1. Show the site and `/api/docs`; explain browser -> authenticated API -> PostgreSQL -> external provider. Identify the deployed commit/environment.
2. Register Alice and Bob. Add ingredients for Alice, reload, then switch to Bob and show that his fridge and personal lists are empty. Show a foreign ID request being rejected in the API evidence.
3. Save dietary/allergen preferences, generate from Alice's fridge and open a recipe. Show ingredients, ordered steps, estimated time/calories and servings. Demonstrate missing shopping ingredients, favorite save/remove and newest-first viewing history; inventory remains manual.
4. Demonstrate empty-fridge and controlled provider-failure states using the isolated test environment. Show that data remains unchanged. Do not break the shared provider or present fixture output as live AI.
5. Walk through the issue -> small branch -> PR -> independent review -> CI -> deployment workflow. Show #16 links, source revisions, actual tests, coverage denominators, five-minute load, penetration results and Sonar before/after evidence.
6. Explain the modular FastAPI decision, shared PostgreSQL ownership/transactions, the ordered-preference migration and the one-origin React/API deployment. Link editable architecture diagrams and the API contract.
7. Show the Codex instructions/prompts, real red/green history and actual incidents from the AI log. Each member explains their own contribution; do not manufacture another member's commits or experience.

Rehearse with the team: decide speakers, time transitions, pre-open the evidence, test both accounts, keep a labelled local fallback, and assign one person to operate the demo. Record the rehearsal date and issues after it happens. This document prepares the presentation; it is not evidence that a rehearsal or final presentation occurred.
