# Sarp's AI assistance and observed correction

Refs [#46](https://github.com/SarpCizer/CMPE331-Project/issues/46), [#16](https://github.com/SarpCizer/CMPE331-Project/issues/16).

## Contributions

OpenAI Codex assisted Sarp with the personal-collections implementation at `862005f` (19 November 2026), including the FastAPI/SQLAlchemy code, ZIP integration adapters and tests. On 23 November it inspected issues #30-#34 and the pinned teammate host, added contract tests and reproducible verification, and documented the boundaries. The new regression tests are commit `fc2a560`; their service correction is `63dcd7a`.

Automated execution verifies behavior; it is not a human code review. Sarp and independent teammates must review the changes. No human approval, live-provider success or cloud deployment is claimed here.

## Actual mistake caught: history clock evaluated before authorization lookup

The AI-assisted initial `service.py` implementation requested the view timestamp before resolving the owner-qualified recipe. A broken clock therefore masked a missing/foreign recipe's required 404 with 500 or 503; a thrown clock exception for an owned recipe also became 500. This violated the detail/history failure contract and made a dependency failure change ownership-denial behavior. No cross-account data disclosure was demonstrated.

Five new tests in `tests/test_history_dependency_failures.py`, committed first at `fc2a560`, reproduced the failures against `862005f`. Commit `63dcd7a` moved the owned lookup before the timestamp and mapped clock failures to a sanitized 503 inside the transaction. All five then passed, along with the standalone suite. Existing history and inventory remain intact on failure.

This records an observed defect and its correction. It does not fabricate earlier tests-first evidence: the 19 November implementation is not retroactively described as TDD. See [sarp-handoff.md](sarp-handoff.md) and [verification.json](verification.json) for the current checks and limitations.
