# Evidence-backed stewardship case studies

These cases test recommendation quality, not just whether Open Growth Loop can parse a repository. Each case uses an unaffiliated public repository, an exact commit, the local-only audit, and the opt-in read-only GitHub evidence adapter. Target repositories were not modified or contacted.

The correct result is sometimes to reject the tool's recommendation. A rejected recommendation is evidence about the decision boundary; it is not an adoption failure and must not be presented as maintainer endorsement.

## Summary

| Case | Exact repository state | Initial recommendation | Human evidence review | Outcome in Open Growth Loop |
| --- | --- | --- | --- | --- |
| Purpose-aware onboarding | [`pypa/sampleproject@621e497`](https://github.com/pypa/sampleproject/commit/621e4974ca25ce531773def586ba3ed8e736b3fc) | Add an Install section | Rejected: this is an editable packaging example, not a normal end-user package README | Explicit purpose profiles implemented; no speculative detector added |
| Release notes versus changelog | [`sindresorhus/p-map@bc26cf0`](https://github.com/sindresorhus/p-map/commit/bc26cf03f81292325236a1188063dac8e7a4de0f) | Add `CHANGELOG.md` | Deferred: GitHub release notes already describe the latest change and link the comparison | Follow-up experiment defined; no claim that a file is required |
| Recovered CI and embedded disclosure guidance | [`BurntSushi/ripgrep@3fce3b5`](https://github.com/BurntSushi/ripgrep/commit/3fce3b5bb0236da2df87599ed666977333c162bfc9) | Investigate failing CI | Rejected: the selected scheduled failure was followed by six successful scheduled runs; README already documents private vulnerability reporting | Two regression-tested fixes shipped |

## Method

Date: 2026-08-12

For each repository:

1. Confirm local `HEAD` matches the public default-branch SHA.
2. Run the local audit without writing into the target repository.
3. Run `ogl steward --github OWNER/REPOSITORY --no-write` for bounded public issues, pull requests, default-branch runs, and release metadata.
4. Inspect only the public files and links needed to evaluate the selected action.
5. Record whether the recommendation is accepted, deferred, or rejected and why.
6. Change Open Growth Loop only when the correction generalizes and can be regression-tested.

Reproduction shape:

```console
git clone --depth=50 https://github.com/OWNER/REPOSITORY.git
git -C REPOSITORY checkout EXACT_SHA
ogl steward --workspace REPOSITORY --repo REPOSITORY --github OWNER/REPOSITORY --no-write
```

The GitHub snapshot is time-sensitive. The repository SHA is stable; issue, pull-request, workflow, and release state should be rechecked before acting.

## Case 1: purpose-aware onboarding

Repository: [`pypa/sampleproject`](https://github.com/pypa/sampleproject)  
Inspected commit: [`621e4974ca25ce531773def586ba3ed8e736b3fc`](https://github.com/pypa/sampleproject/commit/621e4974ca25ce531773def586ba3ed8e736b3fc)

### Raw decision

- Audit score: 4/14 (29%)
- Selected check: `install`
- Recommendation: “Add an Install section with the exact command a new user runs.”
- GitHub snapshot: 16 open issues, 8 open pull requests, no current failing default-branch workflow, no GitHub release.

### Evidence review

The README says the repository exists as an aid to the Python Packaging User Guide tutorial and explicitly does not aim to cover Python project-development best practices as a whole. It tells readers to edit the included metadata to adapt the sample. The exact example command, `pip install sampleproject`, is already annotated in `pyproject.toml`.

For a normal installable library, the heuristic is reasonable. For an educational template whose README is itself example material, automatically adding end-user installation guidance could weaken the artifact it is meant to teach from.

### Verdict

**Rejected for this repository.** No target-repository issue or pull request is justified by this evidence.

Open Growth Loop does not add a broad “sample project” exception because names and keywords are weak proxies for intent. Instead, the repository-purpose profile implemented for v0.3.0 lets a maintainer supply bounded context for `example`, `template`, or `monorepo` repositories. The declared reason stays visible and unverified, the check remains in the denominator, and it never becomes a pass. A runnable fixture and regression tests reproduce this decision boundary without claiming that `pypa/sampleproject` uses or endorses the tool.

## Case 2: release notes versus a changelog file

Repository: [`sindresorhus/p-map`](https://github.com/sindresorhus/p-map)  
Inspected commit: [`bc26cf03f81292325236a1188063dac8e7a4de0f`](https://github.com/sindresorhus/p-map/commit/bc26cf03f81292325236a1188063dac8e7a4de0f)

### Raw decision

- Audit score: 9/14 (64%)
- Selected check: `changelog`
- Recommendation: “Add a CHANGELOG.md and keep it updated with every release.”
- GitHub snapshot: latest release `v7.0.6`, published 2026-07-20; no current failing default-branch workflow.

### Evidence review

The public [`v7.0.6` release](https://github.com/sindresorhus/p-map/releases/tag/v7.0.6) identifies the shipped fix, links issue/PR `#91`, includes the commit, and links the comparison with `v7.0.5`. Users can see what changed without a repository-root changelog.

The local audit cannot see hosted release notes. The current GitHub adapter records the release tag and date, but not whether the release body is substantive. Therefore the available evidence is enough to question the recommendation, but not enough for a generic rule that every release page replaces a changelog.

### Verdict

**Deferred pending stronger evidence.** Do not open a target-repository issue asking for a changelog from this result alone.

The next Open Growth Loop experiment is to read the latest release body with a strict size bound, record its URL, and suppress the changelog recommendation only when user-visible notes or a comparison link are present.

## Case 3: recovered CI and embedded vulnerability reporting

Repository: [`BurntSushi/ripgrep`](https://github.com/BurntSushi/ripgrep)  
Inspected commit: [`3fce3b5bb0236da2df87599ed666977333c162bfc9`](https://github.com/BurntSushi/ripgrep/commit/3fce3b5bb0236da2df87599ed666977333c162bfc9)

### Initial raw decision

- Audit score: 11/14 (79%)
- GitHub adapter reported: 5 failing default-branch runs in its bounded window.
- Selected action: investigate [`ci` run `31139106620`](https://github.com/BurntSushi/ripgrep/actions/runs/31139106620).
- Confidence: high.

### Evidence review

The selected run was a scheduled run from 2026-08-07. Its failures occurred while installing the nightly Rust toolchain on Windows and macOS. The same default-branch SHA then passed scheduled CI on August 8, 9, 10, 11, 12, and 13. The latest push run also passed.

Counting every failure in the bounded history made a recovered transient failure look current. The local audit also warned that `SECURITY.md` was missing, even though the README has a dedicated “Vulnerability reporting” section with a private contact path and PGP-key option.

### Generalized fixes

1. GitHub evidence now groups runs by workflow and considers only the latest completed default-branch run for each workflow. A later success clears an older failure.
2. The security check now accepts explicit README vulnerability-reporting guidance as well as `SECURITY.md` in the standard community-file locations.

Both changes have regression tests. They are deliberately narrow: an in-progress run does not erase the latest completed result, and generic mentions of “security” do not satisfy the disclosure-guidance pattern.

### Rerun result

- Audit score: 12/14 (86%).
- Currently failing default-branch workflows: 0.
- The vulnerability-reporting check passes with evidence: “README contains explicit vulnerability-reporting guidance.”
- The next local heuristic becomes a medium-confidence pull-request-template suggestion, not a high-confidence CI incident.

### Verdict

**The initial action was rejected and Open Growth Loop was fixed.** No ripgrep change is proposed. The remaining pull-request-template suggestion is still a heuristic requiring maintainer judgment, not an instruction to open a pull request.

## What these cases establish

These cases provide public, reproducible evidence that:

- exact repository purpose can invalidate an otherwise reasonable onboarding heuristic;
- hosted release notes can be relevant counterevidence to a missing local changelog;
- historical CI failures must not be treated as current after a successful recovery;
- disclosure instructions can live in a README without a dedicated filename;
- human rejection is part of the safety model, not an error to hide.

They do **not** establish adoption, endorsement, maintainer agreement, time saved, or production impact. None of the three target projects has been asked to use Open Growth Loop. Independent maintainer feedback remains the next evidence tier.

## Review-ready follow-ups

These are Open Growth Loop experiments, not requests for the inspected projects:

1. [Add bounded latest-release-body evidence](https://github.com/R3ijar/open-growth-loop/issues/7) and test whether substantive hosted notes should qualify the changelog decision.
2. Completed: [the optional repository-purpose profile](https://github.com/R3ijar/open-growth-loop/issues/8) now handles examples, templates, and monorepos without guessing from names or inflating scores.
3. Ask maintainers to challenge these verdicts through the [structured field test](ADOPTION.md) before turning any case into an adoption claim.
