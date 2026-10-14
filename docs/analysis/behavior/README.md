# Behavioral models

Activity-style flowcharts show success, alternatives and state changes for every approved story. Sequence diagrams expand generation, missing-ingredient shopping and access control. These formats expose validation/atomicity and boundary interactions without prematurely selecting a production framework.

- [US-01: Register an account](US-01.md)
- [US-02: Sign in](US-02.md)
- [US-03: Save dietary and allergen preferences](US-03.md)
- [US-04: Add an ingredient manually](US-04.md)
- [US-05: List fridge ingredients and dates](US-05.md)
- [US-06: Delete an ingredient manually](US-06.md)
- [US-07: Generate recipes](US-07.md)
- [US-08: Open recipe details](US-08.md)
- [US-09: Handle generation failures](US-09.md)
- [US-10: Add missing recipe ingredients](US-10.md)
- [US-11: Manage shopping items](US-11.md)
- [US-12: Save a favorite](US-12.md)
- [US-13: List and remove favorites](US-13.md)
- [US-14: Record and list recipe history](US-14.md)
- [US-15: Authorize personal data access](US-15.md)

- [Generation sequence](generation-sequence.md)
- [Shopping sequence](shopping-sequence.md)
- [Authorization sequence](authorization-sequence.md)

Every protected entry operation invokes the US-15 gate. US-09 is a conditional continuation of an already authenticated US-07 operation; a retry enters US-07 and authenticates again. A continuation edge from a gate means authentication succeeded; denial ends the request before feature logic. Every mutation's storage-error path rolls back and returns an error. The detailed alternative branches emphasize requirement-specific failures; a generic infrastructure failure is not evidence of success.

Sources are editable Mermaid, with rendered SVGs. [Traceability](../traceability.md) maps all criteria and non-functional requirements. [Rendering instructions](../../../scripts/analysis/README.md) include syntax and consistency checks.
