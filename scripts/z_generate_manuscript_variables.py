"""ROGUE manuscript variable hydration + figure generation (runs last).

Executes the deterministic mission, persists the canonical analysis outputs
(``output/data/mission_results.json``), writes the ``{{TOKEN}}`` mapping
(``output/data/manuscript_variables.json``), renders every ``manuscript/NN_*.md``
section into ``output/manuscript/`` with tokens substituted, and generates the
ROGUE figures into ``output/figures/``.

Strict by default: any unresolved ``{{...}}`` placeholder in a numbered
section fails the run (exit 1). ``--allow-draft`` relaxes the resolve check.
"""

from __future__ import annotations

import argparse
import json
import re

from _bootstrap import OUTPUT, PROVIDER, ROOT
from licence_to_kill.figures.plots import generate_figures
from licence_to_kill.manuscript_variables import generate_variables, substitute

_UNRESOLVED = re.compile(r"\{\{[A-Z_][A-Z0-9_]*\}\}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Hydrate ROGUE manuscript variables and figures")
    parser.add_argument("--allow-draft", action="store_true", help="allow unresolved placeholders")
    args = parser.parse_args()

    outcome = PROVIDER.execute(PROVIDER.plan(PROVIDER.brief()))

    (OUTPUT / "data").mkdir(parents=True, exist_ok=True)
    results_path = OUTPUT / "data" / "mission_results.json"
    results_path.write_text(json.dumps(outcome.results, sort_keys=True, indent=2), encoding="utf-8")

    tokens = generate_variables()
    variables_path = OUTPUT / "data" / "manuscript_variables.json"
    variables_path.write_text(json.dumps(tokens, sort_keys=True, indent=2), encoding="utf-8")

    manuscript_dir = ROOT / "manuscript"
    rendered_dir = OUTPUT / "manuscript"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    unresolved: list[str] = []
    for section in sorted(manuscript_dir.glob("[0-9]*.md")):
        text = section.read_text(encoding="utf-8")
        resolved = substitute(text, tokens)
        leftovers = set(_UNRESOLVED.findall(resolved))
        if leftovers:
            unresolved.append(f"{section.name}: {sorted(leftovers)}")
        (rendered_dir / section.name).write_text(resolved, encoding="utf-8")

    figures = generate_figures(OUTPUT / "figures")

    if unresolved and not args.allow_draft:
        for entry in unresolved:
            print(f"UNRESOLVED {entry}", flush=True)
        return 1
    for entry in unresolved:
        print(f"warn (draft) {entry}", flush=True)

    print(f"ROGUE variables: {len(tokens)} tokens -> {variables_path.relative_to(ROOT)}")
    print(f"ROGUE results:   {results_path.relative_to(ROOT)}")
    print(f"ROGUE figures:   {', '.join(str(p.name) for p in figures.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
