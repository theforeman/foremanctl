# Contributing to foremanctl

## How to report bugs

Issues are tracked via [github.com/theforeman/foremanctl/issues](https://github.com/theforeman/foremanctl/issues). When reporting new issues, please don't forget to specify:

- foremanctl version
- OS version
- installation method (RPM/source)
- error trace or logs with debug level (podman logs, journalctl output)
- steps to reproduce

Since foremanctl is part of the Foreman project you can use its communication channels. 
- [#theforeman on matrix.org](https://matrix.to/#/#theforeman:matrix.org) on Matrix for general discussions and
- [#theforeman-dev on matrix.org](https://matrix.to/#/#theforeman-dev:matrix.org) for technical topics.
You can also use the [Foreman community forum](https://community.theforeman.org/) to ask related questions.


## Code Contributions
To get started:

1. Fork and clone the repository
2. Set up development environment
3. Make the required changes
4. Test the changes and add tests to `tests/`
5. Run `ansible-lint` to check for linting errors (if you changed ansible code)
6. Submit a pull request with a description of changes

Need help with setting up foremanctl? Have a look at: [Developer setup](DEVELOPMENT.md)
