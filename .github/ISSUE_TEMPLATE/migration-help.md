---
name: Migration Help
about: Get help migrating to the new modular plugin architecture
title: '[MIGRATION] '
labels: 'migration, help wanted'
assignees: ''
---

## Migration Issue Description

**Brief description of your migration challenge:**
<!-- Describe what you're trying to migrate or what's not working -->

**Current situation:**
- [ ] Using Entity Framework v0.0.12 or earlier
- [ ] Upgraded to v0.1.0+ but seeing deprecation warnings
- [ ] Trying to migrate to new import paths
- [ ] Need help with specific plugin usage

## Environment Details

**Entity Framework Version:**
<!-- Run: python -c "import entity; print(entity.__version__)" -->

**Python Version:**
<!-- Run: python --version -->

**GPT-OSS Plugin Usage:**
- [ ] I use GPT-OSS plugins and need to migrate
- [ ] I don't use GPT-OSS plugins
- [ ] I'm not sure if I use GPT-OSS plugins

**Installation Method:**
- [ ] pip
- [ ] poetry
- [ ] conda
- [ ] Other: ________________

## Current Code Example

**Your current import/usage pattern:**
```python
# Paste your current code that needs migration
```

**Error messages or warnings (if any):**
```
# Paste any error messages or deprecation warnings
```

## What You've Tried

**Migration steps attempted:**
- [ ] Read the migration guide (MIGRATION.md)
- [ ] Installed entity-plugin-gpt-oss package
- [ ] Updated import statements
- [ ] Ran migration checker script
- [ ] Other: ________________

**Specific challenges:**
<!-- Describe what's blocking you from completing the migration -->

## Expected vs Actual Behavior

**What you expected:**
<!-- Describe what you thought should happen -->

**What actually happened:**
<!-- Describe what you observed instead -->

## Migration Checklist

Please check items you've completed:

**Basic Migration:**
- [ ] Backed up your project
- [ ] Installed entity-plugin-gpt-oss (if using GPT-OSS plugins)
- [ ] Updated import statements
- [ ] Tested basic functionality

**Advanced Migration:**
- [ ] Updated CI/CD configuration
- [ ] Updated dependency management (requirements.txt, pyproject.toml, etc.)
- [ ] Verified all tests pass
- [ ] Updated documentation/README

## Additional Context

**Project details:**
- Size of project (small/medium/large):
- Production usage (yes/no):
- Team size working on migration:
- Migration deadline (if any):

**Additional information:**
<!-- Add any other context about the migration challenge -->

## Help Level Needed

- [ ] Just need clarification on migration steps
- [ ] Need help with specific code patterns
- [ ] Encountering errors during migration
- [ ] Need guidance on testing migration
- [ ] Production deployment concerns
- [ ] Performance questions about new architecture

---

**Migration Resources:**
- [Migration Guide](../MIGRATION.md)
- [Performance Benchmarks](../benchmarks/import_performance_report.md)
- [Compatibility Timeline](../COMPATIBILITY_TIMELINE.md)
- [Release Notes](../RELEASE_NOTES.md)
