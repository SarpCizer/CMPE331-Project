# Conceptual domain model

Baseline: [approved user stories](../../requirements/README.md) and [decisions D-02 to D-09](../../requirements/decisions.md). This conceptual model describes business concepts, not ORM classes or a selected database. Multiplicities next to each end apply to one instance at the other end.

An account owns exactly one logical preference profile; both lists initially are empty, even if no preference rows exist. Inventory and shopping entries represent names only. An accepted recipe belongs to exactly one account and has at least one ingredient and ordered cooking step. A recipe has zero or one favorite and zero or one most-recent view record because it has one owner. Foreign accounts cannot reference it. Generation alone creates no RecipeView; opening details creates or updates it. Removing a favorite removes that association only.

Credentials are a domain concern; persistence stores only a salted password hash. The recipe provider, browser and JWT are boundary collaborators, not owned business entities. Recipe estimates and supplied ingredients require visible labels and user review. See [invariants and persistence choices](data-dictionary.md) for precise constraints.

![Conceptual domain model](images/domain-model.svg)

[Editable Mermaid source](domain-model.mmd)

```mermaid
classDiagram
direction TB
class Account {
  accountId
  email
  credential
}
class PreferenceProfile {
  dietaryChoices
  allergenExclusions
}
class InventoryEntry {
  entryId
  ingredientName
  addedAt
}
class Recipe {
  recipeId
  title
  estimatedCookingMinutes
  estimatedCaloriesPerServing
  servings
}
class RecipeIngredient {
  ingredientName
  position
}
class CookingStep {
  instruction
  position
}
class ShoppingEntry {
  entryId
  ingredientName
}
class Favorite {
  recipeReference
}
class RecipeView {
  recipeReference
  lastViewedAt
}
Account "1" *-- "1" PreferenceProfile : maintains
Account "1" *-- "0..*" InventoryEntry : owns
Account "1" *-- "0..*" Recipe : owns accepted results
Account "1" *-- "0..*" ShoppingEntry : owns
Account "1" *-- "0..*" Favorite : saves
Account "1" *-- "0..*" RecipeView : views
Recipe "1" *-- "1..*" RecipeIngredient : contains
Recipe "1" *-- "1..*" CookingStep : orders
Favorite "0..1" --> "1" Recipe : references owned recipe
RecipeView "0..1" --> "1" Recipe : records owned recipe
note for Recipe "Accept whole batch before storage. Provider candidates are transient."
note for InventoryEntry "Addition time only. No quantities or expiry."
note for Favorite "At most one favorite per account and recipe."
note for RecipeView "At most one view record per account and recipe."
```
