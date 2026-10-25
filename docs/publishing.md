# Publishing a release

How to publish a new version of `py-oauth-kit` to [TestPyPI](https://test.pypi.org)
and [PyPI](https://pypi.org).

## One-time setup

TestPyPI and PyPI are separate sites, with separate accounts and tokens.

1. On each site, open **Account settings > API tokens** and click **Add API token**. Scope it to the `py-oauth-kit` project. (For the very first upload, before the project exists, use an account-wide token, then replace it with a project-scoped one.)
2. Save both tokens in `~/.pypirc`, which [twine](https://twine.readthedocs.io) reads when uploading:

   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-...your PyPI token...

   [testpypi]
   username = __token__
   password = pypi-...your TestPyPI token...
   ```

3. The tokens are stored in plain text, so make the file readable only by you:

   ```sh
   chmod 600 ~/.pypirc
   ```

## Steps

### 1. Bump the version

Update `version` in `pyproject.toml`, using [semantic versioning](https://semver.org):

- Patch (`1.0.0` → `1.0.1`): bug fixes.
- Minor (`1.0.0` → `1.1.0`): new features, e.g. a new provider.
- Major (`1.0.0` → `2.0.0`): breaking changes.

Or run `uv version --bump patch` (or `minor`, `major`). It also updates the version in `uv.lock`.

A version can't be uploaded twice, even after deleting it. To fix a broken upload, publish a new version.

### 2. Test and build

```sh
uv run --frozen pytest
rm -rf dist
uv build
uvx twine check --strict dist/*
```

`twine check` makes sure PyPI can render the README.

### 3. Publish to TestPyPI

```sh
uvx twine upload -r testpypi dist/*
```

### 4. Check the TestPyPI release

Open `https://test.pypi.org/project/py-oauth-kit/` and check the page. Then install it in a clean environment, from outside the project folder:

```sh
cd /tmp
uv run --no-project --refresh \
  --index https://test.pypi.org/simple/ --index-strategy unsafe-best-match \
  --with "py-oauth-kit[apple]==X.Y.Z" \
  python -c "import py_oauth; print('ok')"
```

Replace `X.Y.Z` with the new version. `--index-strategy unsafe-best-match` installs httpx and cryptography from PyPI, as TestPyPI may not have them.

### 5. Publish to PyPI

```sh
uvx twine upload dist/*
```

Check `https://pypi.org/project/py-oauth-kit/`.

### 6. Tag the release

```sh
git tag vX.Y.Z
git push origin main --tags
```

Optionally, create a GitHub release from the tag with a summary of the changes.

## References

- [uv: Building and publishing a package](https://docs.astral.sh/uv/guides/package/)
- [The `.pypirc` file](https://packaging.python.org/en/latest/specifications/pypirc/)
- [Using TestPyPI](https://packaging.python.org/en/latest/guides/using-testpypi/)
- [PyPI API tokens](https://pypi.org/help/#apitoken)
