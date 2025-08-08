# Release Process

This document describes the process for releasing new versions of Entity to PyPI.

## Prerequisites

1. Ensure you have maintainer access to the GitHub repository
2. Configure PyPI trusted publishing (see below)
3. Ensure all tests pass on the main branch
4. Update the CHANGELOG.md with release notes

## Trusted Publishing Setup (One-time setup)

### PyPI Configuration

1. Log in to [PyPI](https://pypi.org)
2. Go to your account settings → Publishing
3. Add a new trusted publisher:
   - Owner: Ladvien
   - Repository: entity
   - Workflow: publish.yml
   - Environment: pypi

### TestPyPI Configuration

1. Log in to [TestPyPI](https://test.pypi.org)
2. Go to your account settings → Publishing
3. Add a new trusted publisher:
   - Owner: Ladvien
   - Repository: entity
   - Workflow: publish.yml
   - Environment: testpypi

## Release Steps

### 1. Prepare the Release

```bash
# Ensure you're on main branch
git checkout main
git pull origin main

# Run all quality checks
poetry run poe check

# Update version in pyproject.toml
poetry version patch  # or minor/major

# Update CHANGELOG.md
# Move items from [Unreleased] to new version section

# Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.0.2"
git push origin main
```

### 2. Create GitHub Release

1. Go to [GitHub Releases](https://github.com/Ladvien/entity/releases)
2. Click "Draft a new release"
3. Create a new tag (e.g., `v0.0.2`)
4. Set release title: `v0.0.2`
5. Copy the CHANGELOG entries for this version into the description
6. Click "Publish release"

The GitHub Action will automatically:
- Build the package
- Publish to PyPI using trusted publishing
- Verify the installation

### 3. Test with TestPyPI (Optional)

To test the release process without publishing to PyPI:

1. Go to Actions → Publish to PyPI workflow
2. Click "Run workflow"
3. Check "Publish to TestPyPI instead of PyPI"
4. Click "Run workflow"

Install from TestPyPI:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ entity
```

## Verify Release

After publishing:

```bash
# Wait a minute for PyPI to update
sleep 60

# Install the new version
pip install entity --upgrade

# Verify version
python -c "from entity import __version__; print(__version__)"
```

## Rollback Process

If issues are discovered after release:

1. Delete the release on GitHub (keeps the tag)
2. Fix the issues
3. Create a new patch version
4. Follow the release process again

Note: Packages cannot be deleted from PyPI, only new versions can be uploaded.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0 → 2.0.0): Incompatible API changes
- **MINOR** version (0.1.0 → 0.2.0): New functionality, backwards compatible
- **PATCH** version (0.0.1 → 0.0.2): Bug fixes, backwards compatible

## Checklist

Before each release, ensure:

- [ ] All tests pass (`poetry run poe test`)
- [ ] Documentation builds (`poetry run sphinx-build -b html docs/source docs/build`)
- [ ] CHANGELOG.md is updated
- [ ] Version number is bumped in pyproject.toml
- [ ] No security vulnerabilities (`poetry run bandit -r src`)
- [ ] Code is formatted (`poetry run black src tests`)
- [ ] All changes are committed and pushed