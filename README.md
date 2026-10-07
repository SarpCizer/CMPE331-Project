# Fridgely

CMPE 331 group project: a responsive web assistant for manual fridge inventory, AI recipe suggestions, shopping lists, favorites and viewed recipe history.

- [Project charter](docs/CHARTER.MD)
- [Requirements specification](docs/requirements-specification.md)
- [Project plans](docs/plans/README.md)
- [User stories and traceability](docs/requirements/README.md)
- [Tests and initial results](tests/README.md)
- [Submission checklist](docs/submission-checklist.md)

## Run the requirements tests

Use Node 20 or newer and run `npm test`. No package installation is necessary. All 21 acceptance cases currently fail because application behavior is unimplemented. Backend, database and runtime AI provider choices remain open for team agreement.

## Export the review PDF

Install the documentation-only packages in `requirements-docs.txt`, then run:

```text
python scripts/export_pdf.py --output Fridgely_Requirements_Review.pdf
```

The script reads the Markdown report and embeds the WBS, PERT and Gantt PNGs. Mermaid diagram sources remain in the plan documents. Windows Arial is used when available; bundled Vera is the fallback. The export is labeled a review copy. After approval, update the report and review footer to reflect the final status, regenerate the PDF, and inspect every page before submitting on learn.bilgi.
