# Decision Policy

Choose the first priority supported by current evidence:

1. Security or data-loss risk with a reproducible, authorized evidence path.
2. A blocked user or contributor in an open issue or pull request.
3. Failing required CI on the default branch or an active pull request.
4. A release blocker or substantial verified work waiting for a release.
5. An essential repository gap: license, install path, runnable quickstart, or CI.
6. The oldest high-confidence maintainer task with a clear completion test.
7. If no remote evidence is available, review the live issue and pull-request queue before proposing new code.

For the chosen action, record:

- Evidence: exact file, command output, issue, pull request, CI run, or release state.
- User or maintainer outcome: who is blocked and what becomes possible.
- Scope: one reviewable change with explicit non-goals.
- Validation: the smallest check that proves the action is complete.
- Authority: whether writing files or changing remote state requires approval.

Reject actions based only on vanity scores, speculative demand, or a desire to make the repository look active.
