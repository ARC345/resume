#!/usr/bin/env python3
"""Deep-merge a profile overlay onto base.yaml for rendercv.

Usage:
    python merge.py base.yaml profiles/<name>.yaml > .build/<name>.yaml

Merge rules:
  - dicts merge recursively (so a profile can override a single nested key)
  - anything else, including lists, REPLACES the base value

Because base.yaml already contains every section key, a profile overriding a
section swaps its value in place without reordering keys -- so rendercv's
section order is preserved. Uses only pyyaml (already a pixi dependency); no yq.
"""
import sys
import yaml


def deep_merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for key, value in over.items():
            out[key] = deep_merge(base[key], value) if key in base else value
        return out
    return over


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: merge.py base.yaml profiles/<name>.yaml")
    base_path, over_path = sys.argv[1], sys.argv[2]

    with open(base_path) as f:
        first_line = f.readline()
        f.seek(0)
        base = yaml.safe_load(f)
    with open(over_path) as f:
        over = yaml.safe_load(f) or {}

    merged = deep_merge(base, over)

    # Preserve the editor schema hint if base.yaml started with one.
    if first_line.startswith("# yaml-language-server:"):
        sys.stdout.write(first_line if first_line.endswith("\n") else first_line + "\n")
    yaml.safe_dump(
        merged, sys.stdout, sort_keys=False, allow_unicode=True, width=4096
    )


if __name__ == "__main__":
    main()
