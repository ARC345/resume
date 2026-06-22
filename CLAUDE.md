# Resume Project

## Stack
- **rendercv** renders a resume from YAML; managed with pixi.
- `base.yaml` is the canonical CV (source of truth). Job-specific variants live
  in `profiles/<name>.yaml` as overlays that override only the sections that
  differ — everything else is inherited from base.
- `merge.py` deep-merges `base.yaml` + a profile overlay (pyyaml; dicts merge
  recursively, lists replace). No yq.
- `render.sh <profile>` merges → renders → commits source → publishes a GitHub
  release tagged `<profile>-vYYYY.MM.DD` with pdf+html+md+png+source assets.
  No arg renders `base`. Run via `pixi run render <profile>`.

## Distribution
- Source (base.yaml, profiles/, scripts) lives in the private `resume` repo.
- Rendered artifacts are NOT committed — they ship as release assets.
- Releases page is the share hub: latest + history per profile, stable links.

## Rules
- Do NOT modify resume content unless explicitly asked.
