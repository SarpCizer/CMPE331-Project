# Mood-based recipes

Issue [#92](https://github.com/SarpCizer/CMPE331-Project/issues/92) extends US-07 while preserving US-03 and US-15. In **Find recipes**, select one mood and choose **Generate recipes**. Click the selected card again or **Clear mood** to return to standard suggestions. Selecting a mood alone makes no AI request. Changing it clears the old displayed suggestions so they are not presented as results for the new choice; previously saved recipes remain available in the catalog.

| Choice | Guidance |
| --- | --- |
| I'm Lazy | Minimal preparation, few steps and washing up; at most 15 minutes total |
| High Protein | Prefer suitable protein-rich ingredients; no measured protein target |
| Sweet Cravings | Sweet snacks, desserts or naturally sweet dishes |
| Low Budget | Favor existing stock, affordable staples and fewer extras; no quoted prices |
| Quick & Easy | Straightforward preparation; at most 20 minutes total |
| Healthy | Favor balanced meals; no medical or guaranteed health claims |

`POST /api/recipes/generate` accepts an optional `mood`: `lazy`, `high-protein`, `sweet`, `budget`, `quick` or `healthy`. Empty/omitted bodies retain the existing behavior. Unknown choices, non-string values and extra owner fields return 400 before inference. The authenticated account's current ingredients, measured amounts and saved preferences still supply generation input; no client ownership is trusted. Both the OpenAI and Cloudflare adapters receive the same trusted guidance. Preferences/exclusions take priority over mood. Existing exact declared-name allergen validation applies; the feature introduces no new synonym or safety guarantee.

The server rejects an entire batch exceeding the lazy/quick time limit with 502 before saving any recipe. Times and calories remain estimates. Other mood labels guide AI selection, rather than asserting verified nutrition or price data. No schema migration, background inference or automatic inventory deduction is added. Requested weekly dishes and the saved-recipe wheel keep their existing behavior.

The picker follows the existing cream/green design, uses a labelled native fieldset and pressed buttons, supports keyboard selection, and disables changes while a request is pending. Empty-fridge generation stays disabled. Errors keep the selected mood for retry. The existing small recipe-card artwork caption was darkened within the same palette after the new full-page accessibility audit detected insufficient contrast.

## Verification

- RED: `2dfba3a` adds tests against unchanged production source `1f004ac845a79942f0e36d3d1b90532796860bf7`. Actual result: 15 failed, 6 passed; valid mood requests were rejected by the old empty-body contract.
- Backend regressions cover every mood through both provider adapters, owner isolation, current quantities/preferences, invalid input, no stock mutation, authentication, empty fridge, allergen priority and whole-batch time-limit rejection.
- Browser regressions exercise all six selections, reset/toggle behavior, mobile/desktop layout, keyboard selection, accessibility/contrast, no inventory changes, loading controls, sanitized provider failure and successful retry.
- Tests use synthetic accounts, temporary SQL databases and controlled external responses. PostgreSQL/container, source identity, security, measured coverage and load evidence must be read from the actual source-pinned CI run; local SQLite passes are not PostgreSQL or live-provider passes.

Codex assisted implementation and verification. Main integration requires independent team review and the existing mandatory checks. Existing free provider/deployment settings and historical course artifacts are preserved.
