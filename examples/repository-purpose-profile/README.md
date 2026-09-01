# Repository Purpose Profile

This fixture models an editable tutorial repository rather than a conventional end-user package README. The nested repository is otherwise audit-ready, but its README deliberately omits a normal Install section.

Its repository-owned profile declares that context:

```toml
[audit_profile]
purpose = "example"

[audit_profile.checks.install]
disposition = "qualify"
reason = "This repository is editable packaging-tutorial material; installation is taught by the surrounding tutorial."
```

Expected result:

- `Install instructions` is `QUALIFIED`, not `PASS`;
- the profile reason remains visible in Markdown and JSON;
- the check stays in the score denominator;
- no Install action is recommended;
- removing `open-growth-loop.toml` restores the default Install warning and recommendation.

Run:

```bash
ogl audit --workspace examples/repository-purpose-profile/repository
ogl steward --workspace examples/repository-purpose-profile/repository --no-write
```
