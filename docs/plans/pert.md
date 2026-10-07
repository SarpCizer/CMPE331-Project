# PERT plan

The baseline begins 7 October and ends 30 November 2026. Durations are inclusive calendar days, not person-days. Estimates are proposed. Expected duration is `(optimistic + 4 × most likely + pessimistic) / 6`; variance is `((pessimistic - optimistic) / 6)²`.

| ID | Phase | Predecessor | Optimistic | Most likely | Pessimistic | Expected days | Variance |
|---|---|---|---:|---:|---:|---:|---:|
| A | Requirements package | Start | 1 | 2 | 3 | 2 | 0.11 |
| B | Review and PDF | A | 1 | 3 | 5 | 3 | 0.44 |
| C | Requirements analysis | B | 5 | 7 | 9 | 7 | 0.44 |
| D | Architecture and initial development | C | 10 | 14 | 18 | 14 | 1.78 |
| E | Detailed design and integration | D | 10 | 14 | 18 | 14 | 1.78 |
| F | Testing evaluation | E | 5 | 7 | 9 | 7 | 0.44 |
| G | Release and code submission | F | 6 | 8 | 10 | 8 | 0.44 |

```mermaid
flowchart LR
    S[Start 7 Oct] --> A[A Requirements 2d]
    A --> B[B Review and PDF 3d]
    B --> C[C Analysis 7d]
    C --> D[D Architecture 14d]
    D --> E[E Design and integration 14d]
    E --> F[F Testing 7d]
    F --> G[G Release 8d]
    G --> Z[Code due 30 Nov]
```

For this conservative milestone network, the critical path is A → B → C → D → E → F → G, totaling 55 expected calendar days. Each phase has zero baseline float. This is a phase-level scheduling model; parallel feature work is shown in the WBS and Gantt plan. A late phase threatens the next deadline unless scope or sequencing is revised. No completion probability is claimed from these uncalibrated estimates.

Requirements creation has one day remaining after the 7 October start before the 8 October PR deadline. Review is an external dependency. Reserve 9–11 October for comments and PDF preparation, but adjust immediately if feedback arrives late. Continuous TDD runs from the requirements phase onward; formal testing evaluation in F does not postpone testing until November.
