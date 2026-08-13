# Design-Partner Outreach

You do not need an existing network. The goal is five useful maintainer conversations, not a large launch.

## Make the Ask Small

Ask for one 20-minute field test on a public repository. Do not ask someone to adopt the project, join a call, or become an ongoing advisor.

The tester runs:

```bash
pip install git+https://github.com/R3ijar/open-growth-loop
ogl steward --workspace path/to/repository --no-write
```

They submit the structured [maintainer field-test form](https://github.com/R3ijar/open-growth-loop/issues/new?template=design_partner.yml). One detailed correction is more valuable than a star.

## Where to Start Without Contacts

1. Publish one Show HN only after a clean install from the public release works. Lead with the runnable local tool and stay available to answer questions.
2. On an Open Source Friday, share the field test from your own account and ask maintainers to challenge the selected action.
3. Write one short technical post showing a real public repository audit, the wrong assumptions it avoided, and the exact command readers can run.
4. Reply only where a maintainer is already discussing triage, release backlog, or contributor onboarding. Do not paste generic promotions into unrelated issues or discussions.
5. Thank every tester publicly, turn actionable feedback into a linked issue, and report what changed.

Do not contact stargazers or maintainers in bulk. Do not ask friends to coordinate votes or comments.

## Ready-to-Post Short Message

> I maintain Open Growth Loop, a local CLI that chooses one evidence-backed repository maintenance action instead of generating a backlog. I need five maintainers to challenge its judgment on a public repo. The test takes about 20 minutes, requires no account or API key, and has a structured feedback form. If it chooses the wrong priority, that is especially useful feedback: https://github.com/R3ijar/open-growth-loop/blob/main/docs/ADOPTION.md

## Show HN Draft

Title:

> Show HN: Open Growth Loop – one evidence-backed OSS maintenance action

Body:

> I kept losing time to long, generic audit backlogs. I built Open Growth Loop to inspect repository hygiene and local Git state, then choose exactly one reviewable maintenance action with its evidence and confidence.
>
> It runs locally, needs no account or API key, and has a no-write mode:
>
> `ogl steward --workspace path/to/repo --no-write`
>
> The project is early. I am looking for maintainers willing to test whether it chooses the wrong priority on a public repository. The most valuable response is a concrete counterexample.
>
> Repository: https://github.com/R3ijar/open-growth-loop

Before posting, replace the install instructions with the verified public package command and run it in a clean environment.

## Weekly Cadence

- Friday 1: publish the short message in one relevant place.
- During the week: respond to feedback and ship one evidenced fix.
- Friday 2: publish the fix and what the maintainer feedback changed.
- Stop after three posts if nobody completes the test; improve onboarding or positioning before posting again.

Record only public, consented evidence in `docs/ADOPTION.md`.
