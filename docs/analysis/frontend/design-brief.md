# Frontend design brief for the next iteration

This project-specific reference was prepared for the first UI/UX iteration; it is not an additional course-supplied policy or a new requirements baseline. Use it with the [approved stories](../../requirements/README.md), [API contract](../../requirements/api-contract.md) and [analysis models](../README.md) when discussing changes with a design tool or AI assistant.

## Product and users

Fridgely helps students, busy home cooks and people with dietary preferences manage the ingredient names they already have and discover AI-generated recipes. Prioritize manual fridge entry, understandable suggestions, clear shopping actions and easy return to saved/viewed recipes. The product should feel practical, calm and friendly rather than like an analytics dashboard.

## Information each screen may contain

- Fridge: ingredient name and **date added**; an add form and manual remove action. Empty state asks for an ingredient. No freshness score, expiry badge, quantity tracker or OCR upload.
- Recipes: title, estimated cooking minutes, estimated calories **per serving**, serving count, full ingredient list and ordered steps. Show generated estimates honestly. Dietary/allergen selections accompany the next request; never promise guaranteed allergen safety.
- Recipe actions: view details, save as favorite, add missing ingredients in one action. These actions never deduct fridge contents. Shopping uses normalized ingredient names and should communicate repeated no-op actions clearly.
- Shopping: names, manual add/remove and empty state. Removal does not automatically restock the fridge. No checked/purchased state is part of the current baseline.
- Saved: favorites and recently viewed recipes; newest viewed first. Saving alone does not mean viewed. Removing a favorite leaves viewed history intact.
- Preferences: editable dietary/allergen lists; empty lists are valid; clearing must replace stored selections, not merge with them.
- Identity: email/password registration and sign-in; no verification-email flow. Expired/invalid sessions need a sign-in message; an object access error must not reveal someone else's private data.

## Required states and accessibility

Design populated, empty, loading, validation error and service error states. A failed generation keeps prior content and all personal data. Show a clear retry action without an automatic infinite retry. All controls must have accessible names; associate validation with fields, expose status feedback, preserve visible keyboard focus, support modal focus/escape and honor reduced motion. Check at 360, 768 and 1440 px without horizontal scrolling. Meaning cannot rely on color or symbols alone.

## Constraints for AI-assisted iterations

Provide only fictional ingredients, recipes and account labels. Do not include real passwords, JWTs, API keys, production user data or private dietary profiles in prompts, fixtures or screenshots. Use local original vector assets or appropriately licensed assets; document new asset provenance. Keep the approved scope exclusions visible in the design discussion. Ask the team to review behavior/terminology changes against story IDs before adding controls that imply new features.

The browser prototype is an exploration artifact. Do not reuse its in-memory data or fake sign-in as production code. Production React/Next and Tailwind choices, database, provider and hosting remain for software design. Future iterations should preserve the traceability in [coverage.json](../coverage.json).
