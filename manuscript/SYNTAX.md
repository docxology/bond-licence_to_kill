# licence_to_kill manuscript syntax

Pandoc-processing conventions for the ROGUE (Licence to Kill) manuscript.

## Tokens

Numeric results are injected as `{{TOKEN}}`. The authoritative token set is
the return value of `src/licence_to_kill/manuscript_variables.py::generate_variables()`;
the live cross-reference gate in `tests/test_manuscript_variables.py` fails
unless every `{{TOKEN}}` in a numbered prose section (`manuscript/[0-9]*.md`)
is generated. To add a token: (1) add it to `generate_variables()`, (2)
reference it in prose, (3) ensure the test still passes.

Do **not** write literal `{{TOKEN}}` placeholder strings in numbered prose —
the cross-ref gate flags any non-generated token. Explain the mechanism
without spelling the braces.

## Citations

Cite with Pandoc keys resolved from `references.bib`:

- `[@tarjan1972]` parenthetical · `@tarjan1972` narrative.
- Registered keys: `tarjan1972`, `imo1969`, `bellman1957`, `licence1989`, `fatf2020`.

## Figures

Reference figures by Pandoc-crossref label and name generated files under
`output/figures/` (relative path from the project root):

| Label | Source | Generator |
|---|---|---|
| `{#fig:laundering}` | `figures/laundering_network.png` | `src/licence_to_kill/figures/plots.py::plot_laundering_network` |
| `{#fig:rogue}` | `figures/rogue_escalation.png` | `...::plot_rogue_escalation` |
| `{#fig:vessel}` | `figures/vessel_forensics.png` | `...::plot_vessel_forensic_scan` |

Embed with a markdown image line carrying the label (see `03_results.md`);
reference in prose as `[@fig:label]` or `@fig:label`.

## Rendering

`scripts/z_generate_manuscript_variables.py` writes substituted sections to
`output/manuscript/*.md` and the variable map to
`output/data/manuscript_variables.json`. Rendering infrastructure is outside
this package's scope (local-only tree; no remote, no publishing).
