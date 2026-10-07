# Work breakdown structure

Work packages are grouped by deliverable. Owners are proposed from the charter, not new role assignments.

| ID | Work package | Planned window | Owner | Exit artifact |
|---|---|---|---|---|
| 1.1 | Requirements plan and definitions | 7–8 Oct | İrem + all members | WBS, PERT, Gantt, user stories, traceability |
| 1.2 | Requirements tests and report | 7–8 Oct | Kerem + story owners | Failing functional tests, NFR cases, Markdown report |
| 1.3 | Requirements review and PDF | 9–11 Oct | Team contact + all members | Reviewer responses, approved report and PDF |
| 2.1 | Domain and data models | 12–18 Oct | Berfin + İrem | Domain model and ER diagram |
| 2.2 | Behavioral models and analysis report | 12–18 Oct | Sarp + Ayşe + Mustafa | Meaningful flows, analysis report |
| 3.1 | Architecture and interfaces | 19 Oct–1 Nov | Berfin + Ayşe + Kerem | Architecture, API contracts, deployment design |
| 3.2 | Authentication and preferences | 19 Oct–15 Nov | Berfin | US-01–03 and US-15 implementation |
| 3.3 | Fridge services | 19 Oct–15 Nov | İrem | US-04–06 implementation |
| 3.4 | Recipe integration | 19 Oct–15 Nov | Ayşe | US-07–09, deterministic provider tests |
| 3.5 | Shopping, favorites and history | 19 Oct–15 Nov | Sarp | US-10–14 implementation |
| 3.6 | Responsive web interface | 19 Oct–15 Nov | Mustafa | All user flows, responsive UI |
| 3.7 | Design models and report | 2–15 Nov | All members | Class/sequence models, design decisions and report |
| 4.1 | Continuous TDD and integration | 7 Oct–30 Nov | Kerem + all members | Tests, CI/CD, traceability, reviewed PRs |
| 4.2 | Testing evaluation and report | 16–22 Nov | Kerem + all members | Unit coverage, performance/security results, SonarQube and penetration findings |
| 5.1 | Cloud deployment and release | 23–30 Nov | Kerem + all members | Release validation, deployment scripts, source-only code archive |
| 5.2 | Presentation and AI workflow evidence | Throughout; presentation TBA | All members | Use-case walkthrough, AI workflow, human-caught AI errors |

```mermaid
flowchart TD
    F[Fridgely] --> R[1 Requirements]
    F --> A[2 Analysis]
    F --> D[3 Design and implementation]
    F --> T[4 Quality assurance]
    F --> L[5 Release and presentation]
    R --> R1[1.1 Plan and stories]
    R --> R2[1.2 Tests and report]
    R --> R3[1.3 Review and PDF]
    A --> A1[2.1 Domain and ER models]
    A --> A2[2.2 Flows and report]
    D --> D1[3.1 Architecture]
    D --> D2[3.2 to 3.6 Feature implementation]
    D --> D3[3.7 Design report]
    T --> T1[4.1 Continuous TDD and CI]
    T --> T2[4.2 Evaluation and report]
    L --> L1[5.1 Deployment and code]
    L --> L2[5.2 Presentation and AI evidence]
```
