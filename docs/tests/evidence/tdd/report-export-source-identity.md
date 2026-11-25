# Report source-identity regression

Task: #16 #24 #44 #48. Codex assisted Berfin.

RED commit: 5140116298c37fdea9a2f95367d33d1f0f89c640, preceding exporter from a59556e. The source-mismatch case changes ci_revision to 40 zeroes. The old exporter returned 0 and wrote a PDF; assertNotEqual(returncode, 0) failed. The nested-directory case also failed with FileNotFoundError. Both failures were reproduced before changing the exporter using the pinned report dependencies.

GREEN: both regression cases pass with the refreshed exporter and retained current evidence. Mismatched identities are rejected before output creation; a valid export creates PDF/Markdown in an initially absent nested directory. Twenty-nine retained evidence files are hash-verified and backend/browser JUnit totals are compared with the source summary.

The resulting seven-page PDF was rendered with Poppler at 100 dpi and every page visually inspected. PDF text assertions confirm the exact source SHA, CI run ID and measured counts/coverage/load. This is report-tooling verification; application/CI evidence remains pinned to a59556e, not to the later report-only commit.
