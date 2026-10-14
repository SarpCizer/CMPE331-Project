# Add missing names without duplicates

Expands US-10 and its interaction with US-11. Every repeat reauthenticates and recomputes from current owned data. Failed writes roll back and return an error, not a partial success.

![Add missing names without duplicates](images/shopping-sequence.svg)

[Editable Mermaid source](shopping-sequence.mmd)

```mermaid
sequenceDiagram
autonumber
actor User
participant UI as Recipe details
participant App as Owned application operation
participant Store as Data store
User->>UI: Add missing ingredients
UI->>App: POST /recipes/:id/shopping-items with JWT
App->>App: US-15 verify token and recipe ownership
Note over App,Store: Denied requests end with 401 or 403/404 and no writes
App->>Store: Read owned recipe ingredients and inventory
Store-->>App: Names for verified account only
App->>App: Normalize and compute unique missing names
App->>Store: BEGIN, upsert absent shopping names using owner/name uniqueness
Note over App,Store: Concurrent duplicate attempts retain existing row ids
Store-->>App: COMMIT or rollback on error
App->>Store: Read resulting owned shopping list
Store-->>App: Items with stable ids
App-->>UI: 200 resulting list
UI-->>User: Added items or already on your list
User->>UI: Repeat same action
UI->>App: Repeat POST with same recipe id
App->>Store: Recheck ownership/data and upsert same missing names
Store-->>App: Existing entries unchanged
App-->>UI: Same collection without duplicates
Note over UI,Store: No inventory mutation, no quantities or purchase completion
```
