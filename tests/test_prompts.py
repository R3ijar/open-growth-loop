from __future__ import annotations

import unittest

from open_growth_loop.candidates import release_evidence_checklist
from open_growth_loop.planner import DailyPlan
from open_growth_loop.prompts import render_codex_prompt


class PromptTests(unittest.TestCase):
    def test_release_evidence_prompt_includes_concrete_checklist(self) -> None:
        plan = DailyPlan(
            action_type="release_evidence",
            asset="/docs/setup",
            title="Verify staged release for /docs/setup",
            reason="Staged work should be proven public before creating another asset.",
            confidence="high",
            next_steps=release_evidence_checklist(),
            evidence={"status": "staged"},
        )

        prompt = render_codex_prompt(plan)

        self.assertIn("Open the public URL or release artifact", prompt)
        self.assertIn("avoids unverified adoption or impact claims", prompt)
        self.assertIn("Record the public artifact URL", prompt)


if __name__ == "__main__":
    unittest.main()
