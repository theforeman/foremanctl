# Contributing to foremanctl

## How to report bugs

Issues are tracked via [github.com/theforeman/foremanctl/issues](https://github.com/theforeman/foremanctl/issues).
When reporting new issues, please don't forget to specify:

- foremanctl version
- OS version
- installation method (RPM/source)
- error trace or logs with debug level (podman logs, journalctl output and ansible output logs)
- steps to reproduce

Since foremanctl is part of the Foreman project you can use its communication channels.

- [#theforeman on matrix.org](https://matrix.to/#/#theforeman:matrix.org) on Matrix for general discussions and
- [#theforeman-dev on matrix.org](https://matrix.to/#/#theforeman-dev:matrix.org) for technical topics.
You can also use the [Foreman community forum](https://community.theforeman.org/) to ask related questions.

## Code Contributions

For setting up a foremanctl development environment, see the [Developer setup](DEVELOPMENT.md) guide.

If you are looking to develop Foreman, checkout the [Foreman Development Environment](docs/developer/development-environment.md) guide.

### CodeRabbit Reviews

CodeRabbit automatically reviews pull requests in this repository.

For small or trivial changes where an automated review is not needed, you can skip it using either of the following options:

- Add the `skip-coderabbit` label when creating the pull request.
- Add `@coderabbitai ignore` to the pull request description.

CodeRabbit reviews are intended to assist contributors.

## Markdown linting

Markdown linting requires Node.js and npm.
`./setup-environment` installs the custom rule automatically, and `./forge markdown-lint` installs it if it is missing.
To install it separately from the repository root without adding a project dependency or lockfile, run:

```sh
npm install --no-save --package-lock=false markdownlint-rule-max-one-sentence-per-line@0.0.2
```

Run the lint command from the repository root.
Use `--fix` to apply supported automatic fixes, review the resulting diff, and then run it again without `--fix` to check the root-level Markdown files and files under `docs/` without modifying them:

```sh
./forge markdown-lint --fix
./forge markdown-lint
```

The lint scope is intentionally limited to root-level `*.md` files and `docs/**/*.md`.
Generated collections, virtual environments, pytest caches, temporary files, and `node_modules/` are ignored.
