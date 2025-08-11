---
name: Compatibility Issue
about: Report problems with the compatibility layer or plugin interactions
title: '[COMPAT] Compatibility issue with v0.1.0'
labels: 'compatibility, bug'
assignees: ''
---

## Compatibility Issue Description

**Issue Summary:**
<!-- Brief description of the compatibility problem -->

**Compatibility Layer Involved:**
- [ ] GPT-OSS plugin compatibility layer
- [ ] Old import patterns not working as expected
- [ ] Mixed import patterns causing issues
- [ ] Dependency conflicts between packages
- [ ] Other: ________________

## Environment Details

**Entity Framework Version:**
<!-- Run: python -c "import entity; print(entity.__version__)" -->

**Package Versions:**
```bash
# Run: pip list | grep entity
entity-core:
entity-plugin-gpt-oss: <!-- if installed -->
```

**Python Environment:**
- Python version: <!-- python --version -->
- Virtual environment: <!-- venv, conda, poetry, etc. -->
- Operating System: <!-- OS and version -->

## Issue Details

**What's not working:**
- [ ] Old imports failing unexpectedly
- [ ] New imports not working as documented
- [ ] Deprecation warnings not appearing when expected
- [ ] Compatibility layer causing errors
- [ ] Plugin functionality differs between old/new imports
- [ ] Performance issues with compatibility layer

**Specific error messages:**
```
# Paste any error messages, tracebacks, or unexpected warnings
```

## Code Examples

**Working code (if any):**
```python
# Paste code that works correctly
```

**Problematic code:**
```python
# Paste code that's causing the compatibility issue
```

**Expected behavior:**
<!-- Describe what should happen according to documentation -->

**Actual behavior:**
<!-- Describe what actually happens -->

## Import Pattern Details

**Current import approach:**
- [ ] Exclusively old imports (from entity.plugins.gpt_oss import ...)
- [ ] Exclusively new imports (from entity_plugin_gpt_oss import ...)
- [ ] Mixed imports (some old, some new)
- [ ] Trying to migrate from old to new

**Specific imports causing issues:**
```python
# List the specific import statements that aren't working
```

## Compatibility Testing

**Have you tested both import methods?**
- [ ] Old imports: Working / Not working / Partially working
- [ ] New imports: Working / Not working / Partially working / Not tested

**Deprecation warning status:**
- [ ] Seeing expected deprecation warnings
- [ ] Not seeing deprecation warnings when expected
- [ ] Seeing unexpected warnings
- [ ] Warnings suppressed with ENTITY_SUPPRESS_GPT_OSS_DEPRECATION

## System Configuration

**Installation method:**
- [ ] Fresh install of v0.1.0+
- [ ] Upgrade from v0.0.12
- [ ] Upgrade from earlier version
- [ ] Development/editable install

**Package installation:**
```bash
# Show your installation commands
pip install ...
```

**Dependencies:**
```bash
# Run: pip list | grep -E "(entity|plugin)" or paste requirements.txt
```

## Troubleshooting Attempted

**Steps you've tried:**
- [ ] Reinstalled entity-core package
- [ ] Installed/reinstalled entity-plugin-gpt-oss
- [ ] Cleared Python cache (__pycache__ directories)
- [ ] Tested in fresh virtual environment
- [ ] Checked for conflicting packages
- [ ] Reviewed migration documentation
- [ ] Tested with environment variables (ENTITY_SUPPRESS_GPT_OSS_DEPRECATION)

**Other debugging efforts:**
<!-- Describe any other troubleshooting you've done -->

## Context and Impact

**Project context:**
- [ ] Personal/hobby project
- [ ] Professional development
- [ ] Production application
- [ ] Enterprise deployment

**Impact level:**
- [ ] Blocking development work
- [ ] Preventing production deployment
- [ ] Causing warnings/noise but functional
- [ ] Minor inconvenience
- [ ] Other: ________________

**Timeline pressure:**
- [ ] No urgency
- [ ] Would like fix within a week
- [ ] Blocking urgent work
- [ ] Production issue

## Expected Compatibility Behavior

Based on our [Compatibility Timeline](../COMPATIBILITY_TIMELINE.md):

**During v0.1.x (compatibility period):**
- Old imports should work with deprecation warnings
- New imports should work without warnings
- Both should provide identical functionality
- Performance may differ (new imports optimized)

**Is this your experience?**
<!-- Describe how your experience differs from expectations -->

## Workarounds

**Current workaround (if any):**
<!-- Describe any temporary solutions you're using -->

**Acceptable workarounds:**
<!-- Let us know what types of workarounds would help you -->

## Additional Information

**Related issues:**
<!-- Link any related GitHub issues -->

**Environment variables set:**
```bash
# List any relevant environment variables
ENTITY_SUPPRESS_GPT_OSS_DEPRECATION=
# Other entity-related env vars
```

**Logs or additional output:**
```
# Paste any relevant log output or detailed error information
```

---

**Compatibility Resources:**
- [Compatibility Timeline](../COMPATIBILITY_TIMELINE.md)
- [Migration Guide](../MIGRATION.md)
- [Troubleshooting Section](../MIGRATION.md#troubleshooting)
- [Known Issues](../RELEASE_NOTES.md#known-issues)
