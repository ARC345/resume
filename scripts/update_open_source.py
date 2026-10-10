#!/usr/bin/env python3
"""Update resume open_source sections from merged GitHub PRs."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

AUTHOR = "ARC345"
API_URL = "https://api.github.com/search/issues"
PR_URL_RE = re.compile(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)")


@dataclass(frozen=True)
class Contribution:
    repository: str
    url: str
    title: str
    merged_at: str


def github_request(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def fetch_merged_pull_requests(author: str, token: str) -> list[Contribution]:
    query = f"type:pr is:merged author:{author}"
    deduped: dict[tuple[str, str], Contribution] = {}

    for page in range(1, 11):
        params = urllib.parse.urlencode(
            {
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": 100,
                "page": page,
            }
        )
        payload = github_request(f"{API_URL}?{params}", token)
        items = payload.get("items", [])
        if not items:
            break

        for item in items:
            repo_url = item.get("repository_url", "")
            repo = repo_url.split("/repos/")[-1]
            pr_url = item.get("html_url", "")
            merged_at = item.get("closed_at", "")
            title = item.get("title", "")
            if not repo or not pr_url or not merged_at:
                continue
            key = (repo, pr_url)
            if key not in deduped:
                deduped[key] = Contribution(
                    repository=repo,
                    url=pr_url,
                    title=title,
                    merged_at=merged_at,
                )

        if len(items) < 100:
            break

    return sorted(deduped.values(), key=lambda c: c.merged_at, reverse=True)


def extract_pr_keys(entry: dict) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for field in ("name", "details"):
        value = entry.get(field)
        if isinstance(value, str):
            for match in PR_URL_RE.finditer(value):
                keys.add((match.group(1), match.group(0)))

    highlights = entry.get("highlights", [])
    if isinstance(highlights, list):
        for highlight in highlights:
            if isinstance(highlight, str):
                for match in PR_URL_RE.finditer(highlight):
                    keys.add((match.group(1), match.group(0)))

    return keys


def contribution_to_entry(contribution: Contribution) -> dict:
    year = contribution.merged_at[:4]
    return {
        "name": f"{contribution.repository} ([PR]({contribution.url}))",
        "date": int(year),
        "highlights": [contribution.title],
    }


def merge_open_source_entries(existing: list, contributions: Iterable[Contribution]) -> list:
    merged: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for raw_entry in existing:
        if not isinstance(raw_entry, dict):
            continue
        entry = copy.deepcopy(raw_entry)
        entry_keys = extract_pr_keys(entry)
        if entry_keys and entry_keys.issubset(seen_keys):
            continue
        seen_keys.update(entry_keys)
        merged.append(entry)

    for contribution in contributions:
        key = (contribution.repository, contribution.url)
        if key in seen_keys:
            continue
        merged.append(contribution_to_entry(contribution))
        seen_keys.add(key)

    return merged


def render_open_source_block(entries: list) -> list[str]:
    dumped = yaml.safe_dump(
        {"open_source": entries},
        sort_keys=False,
        allow_unicode=True,
        width=4096,
    ).splitlines()
    return [f"    {line}" if line else "" for line in dumped]


def find_sections_block(lines: list[str]) -> tuple[int, int] | None:
    sections_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == "sections:" and line.startswith("  "):
            sections_idx = idx
            break

    if sections_idx is None:
        return None

    end = len(lines)
    for idx in range(sections_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped and not lines[idx].startswith("    "):
            end = idx
            break

    return sections_idx + 1, end


def upsert_open_source_section(text: str, entries: list) -> str:
    lines = text.splitlines()
    newline = "\n" if text.endswith("\n") else ""

    section_bounds = find_sections_block(lines)
    if section_bounds is None:
        raise ValueError("cv.sections block not found")

    start, end = section_bounds
    open_start = None
    open_end = None

    for idx in range(start, end):
        if lines[idx].startswith("    open_source:"):
            open_start = idx
            open_end = idx + 1
            for inner in range(idx + 1, end):
                candidate = lines[inner]
                if candidate.strip() and candidate.startswith("    ") and not candidate.startswith("      "):
                    open_end = inner
                    break
                open_end = inner + 1
            break

    block = render_open_source_block(entries)

    if open_start is None:
        insert_at = end
        while insert_at > start and not lines[insert_at - 1].strip():
            insert_at -= 1
        new_lines = lines[:insert_at] + ([""] if insert_at > start else []) + block + lines[insert_at:]
    else:
        new_lines = lines[:open_start] + block + lines[open_end:]

    return "\n".join(new_lines) + newline


def update_resume_file(path: Path, contributions: list[Contribution]) -> bool:
    original_text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(original_text) or {}

    sections = (((data.get("cv") or {}).get("sections")) or {})
    existing = sections.get("open_source", [])
    if not isinstance(existing, list):
        existing = []

    merged_entries = merge_open_source_entries(existing, contributions)
    updated_text = upsert_open_source_section(original_text, merged_entries)

    if updated_text == original_text:
        return False

    path.write_text(updated_text, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author", default=AUTHOR)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--base", default="base.yaml")
    parser.add_argument("--profiles-dir", default="profiles")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.token:
        raise SystemExit("GITHUB_TOKEN is required")

    contributions = fetch_merged_pull_requests(args.author, args.token)

    targets = [Path(args.base)]
    targets.extend(sorted(Path(args.profiles_dir).glob("*.yaml")))

    changed_files = [str(path) for path in targets if update_resume_file(path, contributions)]

    if changed_files:
        print("Changed files:")
        for path in changed_files:
            print(path)
    else:
        print("No changes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
