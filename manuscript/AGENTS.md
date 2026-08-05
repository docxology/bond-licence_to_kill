# Manuscript directory: licence_to_kill (ROGUE)

This is the ROGUE manuscript for PROJECT BOND's `licence_to_kill` film
package. It is written from `manuscript/config.yaml` plus
`src/licence_to_kill/manuscript_variables.py`; every numeric value in the
prose is an injected token, never handwritten.

## File inventory

| File | Role |
|---|---|
| `00_abstract.md` | Mission abstract + headline results |
| `01_introduction.md` | The ROGUE mission, design principles |
| `02_methodology.md` | Laundering graph, vessel physics, rogue DP, finance, logistics, surveillance |
| `03_results.md` | All results + all four figures |
| `04_conclusion.md` | Takeaways |
| `05_experimental_setup.md` | Parameters, software environment |
| `06_reproducibility.md` | Determinism contract, provenance, artifacts |
| `07_scope_and_related_work.md` | Scope, related literature, limitations |
| `99_references.md` | Bibliography index (rendered from `references.bib`) |
| `config.yaml` | Canonical mission parameters + identity |
| `references.bib` | BibTeX bibliography |
| `SYNTAX.md` | Token / citation / figure syntax reference |

## Editing rules

- Read [`../docs/agent_instructions.md`](../docs/agent_instructions.md) first.
- Never hardcode a result in prose — use the matching token from
  `generate_variables()`.
- Never write literal `{{TOKEN}}` placeholder text in numbered sections.
- Reference figures via `[@fig:...]`, never with raw numbers.

## {{TOKEN}} protocol

1. Add/replace a token value in `generate_variables()`.
2. Reference it in prose as `{{TOKEN}}`.
3. `tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
   gates completeness automatically.
4. Re-run `scripts/z_generate_manuscript_variables.py` to regenerate
   `output/manuscript/*.md`.
