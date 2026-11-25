# Main branch protection verification probe

Refs #22, #16.

This temporary PR exists only to verify enforced repository-owner settings. DO NOT MERGE.

Phase A: keep this documentation-only revision without any approving review, wait for the seven actual required CI checks, then observe that merging remains blocked for missing approval.

Phase B: add a deliberately failing test only on this probe branch, observe the actual required integrated test job fail, and verify GitHub also identifies failed required checks as a merge blocker.

The probe must never change main, production, deployment settings, course artifacts, or backend_work. Close it after retaining the evidence; keep its branch/history for audit.

Codex assisted Sarp in preparing this isolated owner-verification probe. No approval, failed-check result, merge attempt or completed verification is claimed by this file.
