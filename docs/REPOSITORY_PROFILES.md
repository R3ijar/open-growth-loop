# Repository Purpose Profiles

Repository audits often fail for a reasonable reason: the same missing surface means different things in a library, an example, a template, or a monorepo. Open Growth Loop does not guess that context from a repository name, topic, or README keyword. A maintainer can declare it explicitly in the repository-owned `open-growth-loop.toml` file.

Profiles are optional. Without one, `ogl audit` and `ogl steward` keep their zero-config behavior.

## Declare Context

```toml
[audit_profile]
purpose = "example"

[audit_profile.checks.install]
disposition = "qualify"
reason = "This repository is editable packaging-tutorial material; installation is taught by the surrounding tutorial."
```

Supported purposes are:

- `standard` — a conventional library, application, service, or command-line tool;
- `example` — runnable or editable teaching material;
- `template` — source material used to generate another project;
- `monorepo` — a repository whose onboarding or release surfaces live in packages or subprojects.

Each check disposition must be either:

- `qualify` — keep the gap visible, attach the declared context, and defer it as the selected next action;
- `skip` — declare the check outside this repository's intended surface while keeping it visible as `PROFILE_SKIP`.

Every disposition requires a human-readable reason of 300 characters or fewer. Unknown purposes, check identifiers, dispositions, or fields fail configuration validation.

The configurable check identifiers are `install`, `quickstart`, `docs`, `examples`, `contributing`, `code_of_conduct`, `security_policy`, `issue_templates`, `pr_template`, `changelog`, `ci`, and `release_tags`. The essential `readme` and `license` identifiers are deliberately rejected in a profile.

## Integrity Rules

A profile cannot turn a gap into a pass.

- Profile-qualified and profile-skipped checks remain in the score denominator and never increment the pass count.
- The report labels the profile as repository-supplied context that Open Growth Loop has not independently verified.
- `README` and license checks are essential and cannot be overridden.
- A disposition changes only a warning. It cannot hide a failed essential check or rewrite a check that already passes.
- Markdown and JSON retain the original gap, the disposition, and the maintainer's reason.

This makes the profile useful as counterevidence without making it a score-inflation switch.

## Example and Expected Decision

The [`repository-purpose-profile`](../examples/repository-purpose-profile/README.md) fixture models an editable tutorial repository. Its README deliberately has no end-user Install section. With no profile, the audit recommends adding one. With the included profile, the Install check is `QUALIFIED`, the report explains why, the readiness score remains below 100%, and no speculative Install action is selected.

Run it from a checkout:

```bash
ogl audit --workspace examples/repository-purpose-profile/repository
ogl steward --workspace examples/repository-purpose-profile/repository --no-write
```

Use `qualify` when the surface still deserves periodic review. Reserve `skip` for cases where the check is structurally owned elsewhere, such as package-level onboarding in a monorepo.
