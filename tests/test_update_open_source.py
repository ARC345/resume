import unittest

from scripts.update_open_source import (
    Contribution,
    merge_open_source_entries,
    upsert_open_source_section,
)


class MergeOpenSourceEntriesTests(unittest.TestCase):
    def test_preserves_manual_and_adds_new_contributions(self):
        existing = [
            {
                "name": "OmniRoute ([PRs](https://github.com/diegosouzapw/OmniRoute/pulls?q=is%3Apr+author%3AARC345+is%3Amerged))",
                "date": 2026,
                "highlights": ["Manual profile summary"],
            }
        ]
        contributions = [
            Contribution(
                repository="owner/repo",
                url="https://github.com/owner/repo/pull/7",
                title="Improve docs",
                merged_at="2026-10-10T00:00:00Z",
            )
        ]

        merged = merge_open_source_entries(existing, contributions)

        self.assertEqual(2, len(merged))
        self.assertEqual(existing[0]["name"], merged[0]["name"])
        self.assertEqual("owner/repo ([PR](https://github.com/owner/repo/pull/7))", merged[1]["name"])

    def test_deduplicates_existing_and_generated_pr_entries(self):
        existing = [
            {
                "name": "owner/repo ([PR](https://github.com/owner/repo/pull/7))",
                "date": 2026,
                "highlights": ["First"],
            },
            {
                "name": "owner/repo ([PR](https://github.com/owner/repo/pull/7))",
                "date": 2026,
                "highlights": ["Duplicate"],
            },
        ]
        contributions = [
            Contribution(
                repository="owner/repo",
                url="https://github.com/owner/repo/pull/7",
                title="Improve docs",
                merged_at="2026-10-10T00:00:00Z",
            )
        ]

        merged = merge_open_source_entries(existing, contributions)

        self.assertEqual(1, len(merged))
        self.assertEqual("First", merged[0]["highlights"][0])


class UpsertOpenSourceSectionTests(unittest.TestCase):
    def test_inserts_section_when_missing(self):
        source = """cv:\n  sections:\n    projects:\n      - name: Example\ndesign:\n  theme: engineeringresumes\n"""
        entries = [
            {
                "name": "owner/repo ([PR](https://github.com/owner/repo/pull/1))",
                "date": 2026,
                "highlights": ["Title"],
            }
        ]

        updated = upsert_open_source_section(source, entries)

        self.assertIn("    open_source:", updated)
        self.assertIn("owner/repo ([PR](https://github.com/owner/repo/pull/1))", updated)
        self.assertIn("design:\n  theme", updated)

    def test_replaces_existing_open_source_block(self):
        source = """cv:\n  sections:\n    open_source:\n      - name: old/repo ([PR](https://github.com/old/repo/pull/1))\n        date: 2025\n        highlights:\n          - old\n    projects:\n      - name: Example\n"""
        entries = [
            {
                "name": "new/repo ([PR](https://github.com/new/repo/pull/2))",
                "date": 2026,
                "highlights": ["new"],
            }
        ]

        updated = upsert_open_source_section(source, entries)

        self.assertNotIn("old/repo", updated)
        self.assertIn("new/repo ([PR](https://github.com/new/repo/pull/2))", updated)
        self.assertIn("    projects:", updated)


if __name__ == "__main__":
    unittest.main()
