# Release

To create a release, bump `VERSION`, create a commit and tag.
It must follow the x.y.z pattern without any prefix.

```
VERSION=x.y.z
echo $VERSION > VERSION
git commit -m "Release $VERSION" VERSION
git tag -s "$VERSION" -m "Release $VERSION"
git push --follow-tags
```

This will create a GitHub release and attach the created tarball to it.

Once that is done, the packaging is handled in the `foreman-packaging` repository where the spec file is maintained:

    obal update foremanctl --version $VERSION
    gh pr create --base rpm/develop
