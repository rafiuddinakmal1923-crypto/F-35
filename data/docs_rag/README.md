# Documents for the field assistant and the report agent (RAG)

Only **approved** documents are indexed (SRS 5.3: approved versions, with owner and date). Each
Markdown file starts with front matter:

```
---
title: Field evidence checklist
version: 0.1
owner: Team F-35
date: 2026-10-27
approved: true
role_scope: [inspector, analyst, supervisor, manager]
---
```

`role_scope` limits who can retrieve the text (SDD 8.2 step 4). Re-index after changes with
`python -m voltguard index-docs` (also run by `make.ps1 seed`).

## Public legal texts

The Electricity Supply Act 1990, the Penal Code and Energy Commission guidance are not copied
into this repository. `python scripts/fetch_docs.py` downloads them into `DATA_ROOT/docs_rag/`
(sources in `sources.yaml`) and the indexer reads them from there. Until they are loaded, the
field assistant answers "not found in approved documents" for legal questions, and reports
cite the provision by name only.

No TNB procedure is invented here: where a utility procedure is needed, the text says
`[TNB procedure: to be supplied]`.
