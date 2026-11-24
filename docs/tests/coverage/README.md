# Coverage definitions

The approved repository requirements contain **15 stories and 48 acceptance
criteria**. `traceability.csv` preserves every criterion and names its assertions;
`traceability.md` provides the story summary. A mapped row is not by itself a
passing result: the report links the actual runner evidence and states its scope.

Python source measurements come from coverage.py/pytest-cov. Read line/statement
and branch percentages separately. The combined `percent_covered` in coverage.py
includes branch opportunities and is not a line-only percentage. The test-only
acceptance bridge is excluded explicitly; production feature modules and migration
code remain in the denominator.

Frontend measurements collect Chromium V8 execution of the production bundle and
map it through the build source maps to `frontend/src`. Third-party React/Vite
code is excluded from product-source metrics. LCOV paths are rewritten relative
to the repository so SonarQube can resolve them in its container.

V8 mapped line coverage can be high while functions or branches remain uncovered.
It is not equivalent to full behavioral coverage. The report includes all three
measures and preserves the actual summaries. Controlled provider fixtures do not
establish live-provider accuracy, hidden-allergen safety, staging availability or
production performance.
