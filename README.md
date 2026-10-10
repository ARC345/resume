# Resume automation

## Open-source contribution updater

This repository includes an automation workflow at `.github/workflows/update-open-source.yml` that:

- runs weekly and on manual dispatch,
- searches GitHub for merged pull requests authored by `ARC345`,
- updates `base.yaml` and every `profiles/*.yaml` file independently,
- preserves existing manual `open_source` entries (including OmniRoute in `profiles/research.yaml`),
- deduplicates contribution entries by repository and PR URL,
- opens a **draft** pull request only when changes exist.

### Local run

```bash
GITHUB_TOKEN=<token> python scripts/update_open_source.py
python -m unittest discover -s tests
```
