# Instructor-review evidence: fafd3fd

The actual source is `fafd3fdbfa0d8ccd2ff7679282687142615e0aed` and the
[integrated CI run is 45899635960](https://github.com/SarpCizer/CMPE331-Project/actions/runs/45899635960).
All eight jobs completed successfully. Every downloaded artifact archive was
checked against its SHA-256 digest from GitHub; `ci-artifacts.json` retains that
catalogue. `evidence-index.json` protects the 46 retained result/metadata files.
This README is a derived explanation, not an additional measured result.

The recorded results include 969 backend passes and three SQLite-specific skips,
32 acceptance passes, 50 browser passes and 12 real HTTP checks. Local SQLite
interleaving evidence has its own `32c73de` source and complementary PostgreSQL
skips; no skipped case is relabelled as a pass.

The 50-user/five-minute PostgreSQL scenario completed 50,532 requests with zero
errors and aggregate p95 144.05 ms. The ten-user controlled generation scenario
completed 498 requests with zero errors and p95 244.03 ms; five simultaneous
provider deadlines returned retryable 503 within 30 seconds and cancelled all
five calls without partial recipe writes or stock changes. No live AI call was made.

Local benchmarks retain their actual `6cc96e7` revision. The complete scoped Git
trees contain 126 identical blobs at the local and CI revisions; the proof keeps
both full commit identities. The fresh Windows non-AI profile failed its 500 ms
target (p95 1772.75 ms, zero errors); controlled generation passed (465 requests,
p95 419.08 ms). Earlier local attempts are retained separately and remain
version-qualified. None is represented as a production SLA or relabelled to CI.

The authenticated ZAP scan observed 4,129 HTTP requests, including 514 protected
successful requests. It records zero high/medium, two low and three informational
alert groups; individual instances remain in the raw JSON/HTML. One 503 during
active scanning remains an availability observation with an unisolated cause;
the absent CORP header remains hardening follow-up. Neither is called repaired.

Sonar's five actual server conditions passed, with 96.0% aggregate coverage and
zero bugs, vulnerabilities, BLOCKER and CRITICAL findings; an independent policy
requires zero hotspots. One MAJOR amount-regex warning remains open. The twelve
historical S2970 findings are a separate false-positive classification. The full
actual dashboard capture is retained; the PDF displays its upper summary viewport.

The older a59556e evidence and the frozen delivery branch are unchanged. This
corrected report is a review copy; CI success is not instructor approval, a merge,
deployment, or proof of learn.bilgi submission.
