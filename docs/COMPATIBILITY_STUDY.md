# Public Repository Compatibility Study

This study records an unaffiliated, read-only run of the Open Growth Loop v0.2.0 release candidate across ten independent public repositories. It tests whether the local audit and steward pipeline can inspect varied repository layouts and produce a reviewable result. It does **not** claim that these projects use, endorse, or agree with Open Growth Loop.

## Result

- Date: 2026-08-12
- Repositories: 10
- Ecosystems: Python, Go, Rust, and Node.js
- Completed after compatibility fixes: 10 of 10
- Remote mutations: 0
- Files written inside target repositories: 0
- Maintainer validation of recommendations: 0 of 10

The initial run found two compatibility defects in Open Growth Loop. Both were fixed, covered by regression tests, and rerun successfully:

1. `pytest-dev/pytest` exposed a Windows locale crash when `git log` returned an international contributor name. Git output is now decoded explicitly as UTF-8 with replacement fallback.
2. `sharkdp/bat` exposed a false missing-license result because it uses `LICENSE-APACHE` and `LICENSE-MIT`. The audit now recognizes common root-level `LICENSE*`, `LICENCE*`, and `COPYING*` filenames.

## Method

Each repository was cloned from its public GitHub default branch with `--depth=50`. The exact inspected commit is recorded below. The following local-only command was run with report writing disabled:

```bash
ogl steward --workspace path/to/clone --repo path/to/clone --no-write
```

No GitHub evidence adapter was used for this study, so issue, pull-request, workflow, and release API data did not affect the recommendations. The target repositories were not modified. A second pass used the same commits after the two compatibility fixes.

## Recorded outputs

The "selected heuristic" column is raw tool output, not advice from this document and not a statement that the target maintainer should make the change.

| Repository | Ecosystem | Inspected commit | Audit score | Selected heuristic |
| --- | --- | --- | ---: | --- |
| [pypa/sampleproject](https://github.com/pypa/sampleproject) | Python | [`621e497`](https://github.com/pypa/sampleproject/commit/621e4974ca25ce531773def586ba3ed8e736b3fc) | 4/14 (29%) | Add an Install section with an exact command. |
| [pallets/click](https://github.com/pallets/click) | Python | [`9c4dfda`](https://github.com/pallets/click/commit/9c4dfdaebe0e6b2aabc566eb81f6f10eb5cd6ea1) | 10/14 (71%) | Add an Install section with an exact command. |
| [psf/requests](https://github.com/psf/requests) | Python | [`8068356`](https://github.com/psf/requests/commit/8068356288978c4f54661ae6f95afe0e0831885e) | 11/14 (79%) | Add a Quickstart with expected output. |
| [cli/cli](https://github.com/cli/cli) | Go | [`a526307`](https://github.com/cli/cli/commit/a526307b621c90dca18734bfedaa5533318edd1a) | 9/14 (64%) | Add a Quickstart with expected output. |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | Rust | [`3fce3b5`](https://github.com/BurntSushi/ripgrep/commit/3fce3b5bb0236da2df6d99672afb8a719642eca7) | 11/14 (79%) | Add a `SECURITY.md`. |
| [sharkdp/bat](https://github.com/sharkdp/bat) | Rust | [`b671e53`](https://github.com/sharkdp/bat/commit/b671e53c2cd0177beb357cf6cb997ee4215c7155) | 11/14 (79%) | Review accumulated commits since the detected tag. |
| [sindresorhus/p-map](https://github.com/sindresorhus/p-map) | Node.js | [`bc26cf0`](https://github.com/sindresorhus/p-map/commit/bc26cf03f81292325236a1188063dac8e7a4de0f) | 9/14 (64%) | Add a `CHANGELOG.md`. |
| [chalk/chalk](https://github.com/chalk/chalk) | Node.js | [`661317e`](https://github.com/chalk/chalk/commit/661317e6f91fe7c90306c2c48ea9354562ee9146) | 10/14 (71%) | Add a `CHANGELOG.md`. |
| [charmbracelet/gum](https://github.com/charmbracelet/gum) | Go | [`7423ddf`](https://github.com/charmbracelet/gum/commit/7423ddf1c810e2df87599ed666977333c162bfc9) | 9/14 (64%) | Add a `CHANGELOG.md`. |
| [pytest-dev/pytest](https://github.com/pytest-dev/pytest) | Python | [`68308aa`](https://github.com/pytest-dev/pytest/commit/68308aa288e00ff84880572ed9b3590f6cd7d470) | 9/14 (64%) | Add an Install section with an exact command. |

## What this proves—and what it does not

This run provides evidence that the v0.2.0 code path can read common Python, Go, Rust, and Node.js repository layouts on Windows, tolerate international Git author names, recognize dual-license filenames, and return structured output without writing to the target.

It does not establish recommendation quality, maintainer adoption, time saved, ecosystem importance, or production safety. Several projects deliberately keep installation, usage, security, or change history on external documentation and release surfaces. A filename-based audit can therefore produce a technically consistent but contextually weak recommendation. That is why every result is a lead for human review rather than an automatic task.

The next useful evidence is independent maintainer feedback on whether the selected action was relevant. The [20-minute field test](ADOPTION.md) is designed to collect counterexamples without requiring a call or ongoing partnership.
