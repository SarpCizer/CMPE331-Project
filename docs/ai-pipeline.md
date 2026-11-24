# AI tooling and runtime recipe pipeline

Refs #16, #45. The repository includes AGENTS.md, reusable prompts and an AI contribution/incident log. The development workflow uses Codex for repository inspection, integration, regression generation, schema changes, browser checks and CI diagnosis. That is broader than inline autocomplete. Human team members own the changes and final review.

```mermaid
flowchart LR
  I[Issue and approved US/AC] --> P[Read existing code and teammate ports]
  P --> R[Write regression and record red result]
  R --> C[Generate and inspect focused change]
  C --> T[Run actual application and tests]
  T --> Q[Coverage, browser, security, load and Sonar evidence]
  Q --> H[Independent human PR review]
  H --> D[Authorized deployment and live smoke checks]
```

This is a documented workflow, not a claim that every older commit followed TDD. PR #49 has an actual test-only red commit before the green implementation. See the contribution and mistakes logs for reproducible evidence and limits.

## Runtime pipeline

```mermaid
sequenceDiagram
  participant UI as React client
  participant API as Authenticated FastAPI host
  participant DB as PostgreSQL
  participant AI as Configured recipe provider
  UI->>API: POST /api/recipes/generate + bearer JWT
  API->>API: Verify signature, claims, expiry and account
  API->>DB: Read owned inventory and saved preferences
  Note over API,DB: PostgreSQL request-input snapshot uses REPEATABLE READ
  alt Empty fridge
    API-->>UI: 400, no provider call
  else Input available
    API->>AI: Instructions + ingredient/dietary/allergen JSON + response schema
    alt Timeout or provider unavailable
      API-->>UI: Retryable sanitized 503, no persistence
    else Candidate batch
      API->>API: Validate all fields, numbers and declared exclusions
      alt Invalid or excluded candidate
        API-->>UI: 502 or 422, no accepted rows
      else Complete valid batch
        API->>DB: Insert owned recipes and ordered children atomically
        DB-->>API: Commit
        API-->>UI: Accepted recipe objects with internal IDs
      end
    end
  end
```

The shared instructions and schema are in `backend/src/fridgely_recipes/provider.py`. Both providers receive the current ingredient names and exact preference lists with a 2400-token output limit. The OpenAI adapter uses Responses with `store:false`. The Cloudflare adapter uses Workers AI JSON Mode for Llama 3.3 70B. The host applies a 28-second generation budget with a shorter connection timeout. [Server configuration](cloud-deployment.md#recipe-provider-settings)

Validation checks the complete batch before storage. Declared exclusion comparison is trimmed/casefolded name matching, not a synonym taxonomy, allergy certification or medical advice. No recipe operation deducts inventory. Controlled providers belong only to isolated tests. Missing production credentials yield the actual retryable error; no fixture replaces the live service.
