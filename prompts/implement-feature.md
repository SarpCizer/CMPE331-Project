# Feature implementation prompt

Read issue <number>, #16, its US/AC definitions, affected feature ports and current PR dependencies. State the smallest behavior change and the assertions that would disprove it. Write and run the failing regression before changing production code. Record the exact source/test revision and failure.

Implement on a focused English branch, preserving owned data and the existing HTTP contract. Validate both empty and existing databases if storage changes. Run the regression and relevant integration/browser checks. Review the diff and write an English PR description with issue links, actual results, AI contribution and remaining limitations. Request an independent reviewer. Do not merge main or infer approval from a passing pipeline.
