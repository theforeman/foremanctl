# Release

## Version Scheme

- `master` always contains a tag with the current development version: `X.Y-develop`
- Stable branches are named `X.Y-stable`
- Release candidate tags on stable branches follow `X.Y.Z-rc` (e.g. `3.18.0-rc1`)
- Release tags on stable branches follow `X.Y.Z` (e.g., `3.18.0`, `3.18.1`)

## Branching for a Release

When ready to stabilize a version (e.g., 3.18):

1. Create the stable branch from master:

   ```
   git fetch origin
   git checkout -b 3.18-stable origin/master
   git push --set-upstream origin HEAD
   ```

2. Update `src/vars/images.yml` on the stable branch to reference the release images (e.g., `foreman-3.18`).

3. Bump master to the next development version:

   ```
   git checkout master
   git tag -s "3.19-develop" -m "Start 3.19 development"
   git push --follow-tags
   ```

## Cutting a Release

To release from a stable branch (e.g., 3.18.0):

```
git checkout 3.18-stable
git tag -s "3.18.0" -m "Release 3.18.0"
git push --follow-tags
```

This will create a GitHub release and attach the created tarball to it.

## Packaging

Once that is done, the packaging is handled in the [foreman-packaging](https://github.com/theforeman/foreman-packaging) repository where the spec file is maintained:

    obal update foremanctl --version $VERSION
    gh pr create --base rpm/develop
