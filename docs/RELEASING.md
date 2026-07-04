# Releasing

Releases are tag-driven. Pushing a `v*` tag builds the package and publishes it to PyPI through [trusted publishing](https://docs.pypi.org/trusted-publishers/) — no API token is stored in the repository.

## One-time setup (before the first PyPI release)

1. Create a PyPI account and verify the email address.
2. On PyPI, go to **Your account -> Publishing -> Add a new pending publisher** and register:
   - PyPI project name: `open-growth-loop`
   - Owner: `R3ijar`
   - Repository: `open-growth-loop`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. In the GitHub repository, go to **Settings -> Environments -> New environment** and create an environment named `pypi`. Optionally add yourself as a required reviewer so publishes need a manual approval click.

## Cutting a release

1. Update the `version` in `pyproject.toml`.
2. Move the `Unreleased` notes in `CHANGELOG.md` under a new version heading with today's date.
3. Run the release brief and fix anything blocked:

   ```bash
   python -m open_growth_loop --workspace . release-brief
   ```

4. Commit, tag, and push:

   ```bash
   git commit -am "Prepare vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

5. The `Release` workflow builds the sdist and wheel and publishes to PyPI. Watch it in the Actions tab.
6. Create a GitHub release from the tag and paste the changelog section as the notes.

## GitHub Action versioning

The reusable action is versioned by the same tags. After tagging, update the pinned version in README examples (`uses: R3ijar/open-growth-loop@vX.Y.Z`).

To list the action on the GitHub Marketplace, open the repository on GitHub after tagging — a banner on the release page offers **Publish this Action to the Marketplace**. The `action.yml` already has the name, description, and branding fields the listing requires.
