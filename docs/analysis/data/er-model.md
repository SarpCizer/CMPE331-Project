# Draft logical E-R model

This preliminary relational view remains required and useful if MongoDB is selected. It does not select PostgreSQL or require an ORM. UUID denotes an opaque application-assigned identifier; its physical representation is a design decision. PK, FK and UK label primary, foreign and unique keys. See [the data dictionary](data-dictionary.md) for composite uniqueness and owner constraints that the diagram alone cannot express.

Solid relationships are identifying: the child primary key includes the parent key. Dashed relationships are non-identifying: inventory, recipe and shopping entries have independent identifiers. Line style does not specify database cascade policy. Every child has exactly one parent; each recipe must have one or more ingredient and step rows after a successful transaction. No row represents an expiry date, ingredient quantity, persistent JWT session or provider secret. PreferenceProfile in the domain maps to the two optional preference collections below.

![Draft logical E-R model](images/er-model.svg)

[Editable Mermaid source](er-model.mmd)

```mermaid
erDiagram
    ACCOUNT ||--o{ DIETARY_PREFERENCE : selects
    ACCOUNT ||--o{ ALLERGEN_EXCLUSION : declares
    ACCOUNT ||..o{ INVENTORY_ENTRY : owns
    ACCOUNT ||..o{ RECIPE : owns
    ACCOUNT ||..o{ SHOPPING_ENTRY : owns
    ACCOUNT ||--o{ FAVORITE : saves
    ACCOUNT ||--o{ RECIPE_VIEW : views
    RECIPE ||--|{ RECIPE_INGREDIENT : contains
    RECIPE ||--|{ RECIPE_STEP : orders
    RECIPE ||--o| FAVORITE : has
    RECIPE ||--o| RECIPE_VIEW : has
    ACCOUNT {
        uuid account_id PK
        string email
        string normalized_email UK
        string password_hash
    }
    DIETARY_PREFERENCE {
        uuid account_id PK,FK
        string value_key PK
        string display_value
    }
    ALLERGEN_EXCLUSION {
        uuid account_id PK,FK
        string value_key PK
        string display_value
    }
    INVENTORY_ENTRY {
        uuid entry_id PK
        uuid account_id FK
        string ingredient_name
        string normalized_name
        timestamp added_at
    }
    RECIPE {
        uuid recipe_id PK
        uuid account_id FK
        string title
        decimal cooking_minutes
        decimal calories_per_serving
        integer servings
    }
    RECIPE_INGREDIENT {
        uuid recipe_id PK,FK
        integer position PK
        string ingredient_name
        string normalized_name
    }
    RECIPE_STEP {
        uuid recipe_id PK,FK
        integer position PK
        string instruction
    }
    SHOPPING_ENTRY {
        uuid entry_id PK
        uuid account_id FK
        string ingredient_name
        string normalized_name
    }
    FAVORITE {
        uuid account_id PK,FK
        uuid recipe_id PK,FK
    }
    RECIPE_VIEW {
        uuid account_id PK,FK
        uuid recipe_id PK,FK
        timestamp last_viewed_at
    }
```
