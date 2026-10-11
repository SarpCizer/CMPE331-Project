# Gantt schedule

This schedule uses the expected-duration forward pass from the [PERT network](pert.md). Start/finish dates below are inclusive calendar dates in Europe/Istanbul. Day 0 is 7 October 2026. Internal finish dates can precede the fixed course deadlines; estimates are not actual progress records. The charter's 2 October milestone precedes this baseline, and presentation remains TBA.

```mermaid
gantt
    title Fridgely parallel work baseline
    dateFormat YYYY-MM-DD
    axisFormat %d %b
    section Requirements and analysis
    A Requirements package :crit, a, 2026-10-07, 2d
    Q0 Acceptance and CI baseline : q0, 2026-10-07, 1d
    B Requirements review and PDF :crit, b, 2026-10-09, 3d
    C Requirements analysis :crit, c, 2026-10-12, 7d
    D Architecture and interfaces :crit, d, 2026-10-19, 5d
    section Parallel feature work and TDD
    E Accounts and preferences : e, 2026-10-24, 10d
    F Fridge services : f, 2026-10-24, 8d
    G Recipe integration :crit, g, 2026-10-24, 15d
    H Shopping favorites history : h, 2026-10-24, 12d
    I Responsive web interface : i, 2026-10-24, 14d
    Q1 Shared TDD and CI cycles : q1, 2026-10-24, 14d
    section Integration documentation and release
    J End-to-end integration : j, 2026-11-08, 3d
    K Design report finalization :crit, k, 2026-11-08, 4d
    L Design review and submission :crit, l, 2026-11-12, 3d
    M Testing evaluation and report :crit, m, 2026-11-15, 7d
    N Cloud release and code :crit, n, 2026-11-22, 8d
    section Course deadlines
    Requirements PR :milestone, 2026-10-08, 0d
    Requirements PDF :milestone, 2026-10-11, 0d
    Analysis report :milestone, 2026-10-18, 0d
    Design report :milestone, 2026-11-15, 0d
    Testing report :milestone, 2026-11-22, 0d
    Codebase :milestone, 2026-11-30, 0d
```

![Gantt schedule](images/gantt.png)

| ID | Activity | Start | Finish | Owner |
|---|---|---|---|---|
| A | Requirements package | 2026-10-07 | 2026-10-08 | İrem + all members |
| Q0 | Acceptance and CI baseline | 2026-10-07 | 2026-10-07 | Kerem + story owners |
| B | Requirements review and PDF | 2026-10-09 | 2026-10-11 | Team contact + all members |
| C | Requirements analysis | 2026-10-12 | 2026-10-18 | Berfin + İrem + all members |
| D | Architecture and interfaces | 2026-10-19 | 2026-10-23 | Berfin + Ayşe + Kerem |
| E | Accounts and preferences | 2026-10-24 | 2026-11-02 | Berfin |
| F | Fridge services | 2026-10-24 | 2026-10-31 | İrem |
| G | Recipe integration | 2026-10-24 | 2026-11-07 | Ayşe |
| H | Shopping favorites history | 2026-10-24 | 2026-11-04 | Sarp |
| I | Responsive web interface | 2026-10-24 | 2026-11-06 | Mustafa |
| Q1 | Shared TDD and CI cycles | 2026-10-24 | 2026-11-06 | Kerem + feature owners |
| J | End-to-end integration | 2026-11-08 | 2026-11-10 | Kerem + all members |
| K | Design report finalization | 2026-11-08 | 2026-11-11 | All members |
| L | Design review and submission | 2026-11-12 | 2026-11-14 | All members |
| M | Testing evaluation and report | 2026-11-15 | 2026-11-21 | Kerem + all members |
| N | Cloud release and code | 2026-11-22 | 2026-11-29 | Kerem + all members |

Parallel streams E-I and Q1 all start after architecture D. Integration J and design-report finalization K join the feature streams and run in parallel, before design review L. The critical recipe stream has no activity slack; delayed recipe integration delays the project unless other estimates or dependencies change. Q0, Q1 and J explicitly represent shared TDD/integration support; developer tests and regression remain part of every implementation, evaluation and release task.

Fixed course dates: requirements PR 8 October; PDF 11 October; analysis 18 October; design 15 November; testing 22 November; code 30 November. Expected internal design completion is 14 November, testing 21 November, release 29 November. The one-day finish reserve is not counted as an activity's slack. Risks remain reviewer availability, technology/provider decisions, malformed AI output and integration delays.
