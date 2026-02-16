# git_repository

A role that clones a git repository from GitHub and optionally adds an additional remote to it.

Roughly corresponds to

```shell
$ su {{ git_repository_user }}

$ git clone https://github.com/{{ git_repository_repository_owner }}/{{ git_repository_repository_name }} \
    --branch {{ git_repository_revision }} \
    --remote {{ git repository_remote_name || "origin" }}
    {{ git_repository_destination_dir }}

$ if {{ git_repository_secondary_remote_owner }}; then
    cd {{ git_repository_destination_dir }}
    git remote add \
        {{ git_repository_secondary_remote_name || git_repository_secondary_remote_owner }} \
        git@github.com:{{ git_repository_secondary_remote_owner }}/{{ git_repository_repository_name }}
fi
```

## Parameters

| Variable | Description | Required |
|----------|-------------|------|
| `git_repository_repository_owner` | The owner of the repository to clone from | Yes |
| `git_repository_repository_name` | The name of the repository to clone | Yes |
| `git_repository_revision` | The revision to clone the repository at | No, defaults to `HEAD` |
| `git_repository_remote_name` | The name of the remote the repository was cloned from | No, defaults to `origin` |
| `git_repository_destination_dir` | Path to the directory where the repository will be cloned to | Yes |
| `git_repository_secondary_remote_owner` | Name of the owner of the secondary remote to be added to the local clone | No, secondary remote will not be added if left blank |
| `git_repository_secondary_remote_name` | Name of the remote of the secondary repository | No, defaults to `{{ git_repository_secondary_remote_owner }}` |
| `git_repository_user` | The owner of the git checkout | Yes |

Generally it would be preferrable to avoid the need for `git_repository_user` by controlling the user with `become` and `become_user`, but those are not available in all contexts.
