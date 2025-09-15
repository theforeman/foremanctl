# Release

To create a release, bump `VERSION`, update `foremanctl.spec`, create a commit and tag.
It must follow the x.y.z pattern without any prefix.

```
VERSION=x.y.z
echo $VERSION > VERSION
sed -i -E "/^Version:/ s#[0-9.]+#$VERSION#" foremanctl.spec
git commit -m "Release $VERSION" VERSION foremanctl.spec
git tag -s "$VERSION" -m "Release $VERSION"
git push --follow-tags
```

This will create a GitHub release and attach the created tarball to it.

Once that is done, you can upload `foremanctl.spec` to the [@theforeman/foremanctl COPR](https://copr.fedorainfracloud.org/coprs/g/theforeman/foremanctl/).

```
copr build @theforeman/foremanctl foremanctl.spec
```
