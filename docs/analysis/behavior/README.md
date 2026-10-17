# Behavioral analysis: data flow diagrams

Revised 17 October 2026 in response to [Yeşim's review](https://github.com/SarpCizer/CMPE331-Project/pull/5#pullrequestreview-5538025802). The behavioral deliverables are **Data Flow Diagrams**, replacing the activity-style flowcharts and sequence diagrams. Editable .dfd.json sources declare typed nodes and labeled data flows; the renderer lays them out and draws the DFD symbols. No old activity/sequence model remains in this folder.

## Notation and how to read the diagrams

This set uses Yourdon-DeMarco-style circles for processes, rectangles for external entities, parallel horizontal lines for persistent data stores, and directed arrows labeled with the data exchanged. A process transforms input data into output data. An arrow is not execution order, a yes/no branch or a timing event. Validation, HTTP outcomes, atomicity and no-write conditions are the process specifications alongside each DFD. External entities and stores communicate through processes, never directly.

The [Microsoft DFD guide](https://support.microsoft.com/en-us/visio/create-a-data-flow-diagram-in-visio) describes external sources/destinations, data transformations and stores. The [Microsoft hierarchical modeling guide](https://support.microsoft.com/en-us/visio/create-a-gane-sarson-data-flow-model-diagram) also describes context and detail diagrams; its Gane-Sarson shape variant is not the circle notation selected here.

- [Context DFD](context-dfd.md): the complete system and six external interface groups.
- [Level 1 DFD](level-1-dfd.md): eight logical processes and their persistent data.
- [US-01 DFD](US-01.md)
- [US-02 DFD](US-02.md)
- [US-03 DFD](US-03.md)
- [US-04 DFD](US-04.md)
- [US-05 DFD](US-05.md)
- [US-06 DFD](US-06.md)
- [US-07 DFD](US-07.md)
- [US-08 DFD](US-08.md)
- [US-09 DFD](US-09.md)
- [US-10 DFD](US-10.md)
- [US-11 DFD](US-11.md)
- [US-12 DFD](US-12.md)
- [US-13 DFD](US-13.md)
- [US-14 DFD](US-14.md)
- [US-15 DFD](US-15.md)

Process groups: 1.0 identity (US-01/02), 2.0 preferences (US-03), 3.0 fridge (US-04/05/06), 4.0 generation/failures (US-07/09), 5.0 recipe details/history (US-08/14), 6.0 shopping (US-10/11), 7.0 favorites (US-12/13), 8.0 authorization (US-15). Per-story diagrams are **functional views**, not claims that every view independently balances an entire parent process. The context/level-1 interfaces balance by the group identifiers in the data sources; the union of story views provides the detailed behavior.

## Persistent store dictionary

| Store | Logical data | E-R mapping |
|---|---|---|
| D1 | Accounts | ACCOUNT |
| D2 | Ordered preference lists | DIETARY_PREFERENCE + ALLERGEN_EXCLUSION, ordered by position |
| D3 | Fridge inventory | INVENTORY_ENTRY |
| D4 | Accepted recipes and children | RECIPE + RECIPE_INGREDIENT + RECIPE_STEP |
| D5 | Shopping entries | SHOPPING_ENTRY |
| D6 | Favorite associations | FAVORITE |
| D7 | Recipe views | RECIPE_VIEW |
| D0 | Personal records (D2-D7) | Access-analysis aggregate of D2-D7; no additional entity |

## External interface balancing

| Group | Context data | Level 1 refinement |
|---|---|---|
| AUTH_IN / AUTH_OUT | Credentials; account or access result | Visitor to/from identity 1.0 |
| PERSONAL_IN | Personal request and access token | Account holder to authorization 8.0, then verified request data to the relevant feature |
| PERSONAL_OUT | Personal data or sanitized error | Authorization denial or feature-specific preference/fridge/recipe/shopping/favorite/history data/error |
| AI_IN / AI_OUT | Ingredient names and preference lists; recipe candidates or failure data | Recipe generation 4.0 to/from the external AI provider |

All protected operations enforce US-15, including IDs submitted in request bodies. A caller cannot bypass ownership by creating an association through a collection route. DFDs show data movement; the process constraints specify that invalid input creates no mutation, generation persists only a complete validated batch, and only manual fridge changes write D3. Failure views omit persistent writes deliberately.

[Traceability](../traceability.md) includes exact criterion wording and supporting models for cross-cutting criteria. [Tooling](../../../scripts/analysis/README.md) validates node/edge types, process inputs/outputs, interface balancing, requirement links and rendered-source hashes.
