from __future__ import annotations

import json
import unittest

from open_growth_loop.github_evidence import read_github_snapshot


class GitHubEvidenceTests(unittest.TestCase):
    def test_reads_a_bounded_read_only_snapshot(self) -> None:
        calls: list[list[str]] = []

        def runner(args: list[str]) -> str:
            calls.append(args)
            command = args[:2]
            if command == ["repo", "view"]:
                return json.dumps({"defaultBranchRef": {"name": "trunk"}})
            if command == ["issue", "list"]:
                return json.dumps(
                    [
                        {
                            "number": 12,
                            "title": "Crash on startup",
                            "labels": [{"name": "bug"}],
                            "createdAt": "2026-06-01T00:00:00Z",
                            "updatedAt": "2026-06-02T00:00:00Z",
                            "url": "https://example.org/issues/12",
                        }
                    ]
                )
            if command == ["pr", "list"]:
                return json.dumps(
                    [
                        {
                            "number": 21,
                            "title": "Improve docs",
                            "isDraft": False,
                            "createdAt": "2026-06-02T00:00:00Z",
                            "updatedAt": "2026-06-03T00:00:00Z",
                            "url": "https://example.org/pull/21",
                        }
                    ]
                )
            if command == ["run", "list"]:
                return json.dumps(
                    [
                        {
                            "databaseId": 31,
                            "workflowName": "CI",
                            "conclusion": "failure",
                            "createdAt": "2026-06-03T00:00:00Z",
                            "url": "https://example.org/actions/31",
                        }
                    ]
                )
            if command == ["release", "list"]:
                return json.dumps([{"tagName": "v0.1.0", "publishedAt": "2026-06-02T00:10:00Z"}])
            raise AssertionError(f"unexpected gh command: {args}")

        snapshot = read_github_snapshot("owner/repo", limit=5, runner=runner)

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.default_branch, "trunk")
        self.assertEqual(snapshot.open_issues, 1)
        self.assertEqual(snapshot.open_pull_requests, 1)
        self.assertEqual(snapshot.failing_default_branch_runs, 1)
        self.assertEqual(snapshot.actionable_issue.number, "12")
        self.assertEqual(snapshot.failing_run.title, "CI")
        self.assertTrue(all(call[:2] in [["repo", "view"], ["issue", "list"], ["pr", "list"], ["run", "list"], ["release", "list"]] for call in calls))

    def test_rejects_an_invalid_repo_locator(self) -> None:
        with self.assertRaises(ValueError):
            read_github_snapshot("not-a-repo", runner=lambda args: "[]")

    def test_returns_an_explicit_unavailable_snapshot_on_gh_failure(self) -> None:
        snapshot = read_github_snapshot("owner/repo", runner=lambda args: (_ for _ in ()).throw(RuntimeError("not authenticated")))

        self.assertFalse(snapshot.available)
        self.assertEqual(snapshot.repo, "owner/repo")
        self.assertIn("authenticated", snapshot.error)


if __name__ == "__main__":
    unittest.main()
