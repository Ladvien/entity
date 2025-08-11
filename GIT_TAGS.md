# Git Tags Documentation

**Document Version:** 1.0
**Last Updated:** Q2 2024
**Purpose:** Document git tagging strategy for Entity Framework releases

---

## 🏷️ Current Git Tags

### Release Tags

```bash
# View all release tags
git tag -l "v*" --sort=-version:refname

# Expected tags:
v0.1.0              # Current release target
v0.0.12             # Last pre-modularization release
pre-modularization  # Rollback reference point
```

### Checkpoint Tags

```bash
# Development checkpoint tags
checkpoint-40       # Story 1 completion
checkpoint-41       # Story 2 completion
checkpoint-42       # Story 3 completion
checkpoint-43       # Story 4 completion
checkpoint-44       # Story 5 completion
checkpoint-45       # Story 6 completion
checkpoint-46       # Story 7 completion (target)
```

---

## 📋 Tag Creation Commands

### Before Release (Pre-modularization Tag)

This tag serves as the rollback point if v0.1.0 has critical issues:

```bash
# Create the pre-modularization tag
git tag -a pre-modularization -m "Checkpoint before modularization

This tag marks the last stable commit before the major modularization
changes for v0.1.0. This serves as the rollback reference point.

Features at this checkpoint:
- All GPT-OSS plugins included in main repository
- Original import paths: from entity.plugins.gpt_oss import *
- No compatibility layer or deprecation warnings
- Stable baseline functionality

Use this tag for emergency rollback if v0.1.0 has critical issues.
See ROLLBACK.md for detailed rollback procedures.

Package versions:
- entity-core: 0.0.12
- All plugins: included in core

Test results: All 65+ tests passing
Performance baseline: Import time ~0.05s"

# Push the tag
git push origin pre-modularization
```

### Release Tag (v0.1.0)

Main release tag for the modularization:

```bash
# Create the release tag
git tag -a v0.1.0 -m "Release v0.1.0: Plugin Modularization

🎯 MAJOR RELEASE: Plugin Modularization Architecture

This release introduces a major architectural change by modularizing
GPT-OSS plugins into a separate, optional package.

🚀 KEY FEATURES:
✅ GPT-OSS plugins moved to separate 'entity-plugin-gpt-oss' package
✅ Reduced core framework size by ~40% (removed ~243KB of code)
✅ Improved import performance and memory footprint
✅ Backward compatibility layer with deprecation warnings
✅ Comprehensive migration documentation and tooling

📊 PERFORMANCE IMPROVEMENTS:
- Entity import time: 0.0187s (was ~0.05s)
- Plugin import time: 0.0736s
- GPT-OSS compatibility: 0.0008s overhead
- Memory usage reduced when GPT-OSS not used

⚠️  BREAKING CHANGES:
- GPT-OSS plugin import paths changed
- entity-plugin-gpt-oss package now required for GPT-OSS functionality
- Deprecation warnings for old import patterns

📦 PACKAGE VERSIONS:
- entity-core: 0.1.0 (this package)
- entity-plugin-gpt-oss: 0.1.0+ (separate install required)

🔄 MIGRATION:
1. Install: pip install entity-plugin-gpt-oss
2. Update imports: from entity_plugin_gpt_oss import ReasoningTracePlugin
3. See MIGRATION.md for detailed guide

📚 DOCUMENTATION:
- Migration Guide: MIGRATION.md
- Release Notes: RELEASE_NOTES.md
- Rollback Plan: ROLLBACK.md
- Version Strategy: VERSION_STRATEGY.md

🧪 TESTING:
- 81+ tests passing (16 new performance tests)
- Compatibility layer fully tested
- Migration path validated
- Performance benchmarks verified

🛡️ ROLLBACK:
If critical issues arise, use 'pre-modularization' tag
See ROLLBACK.md for detailed emergency procedures

🎖️ CONTRIBUTORS:
Special thanks to all contributors who made this modularization possible
through careful planning, implementation, testing, and documentation.

For support: See issue templates and MIGRATION.md"

# Push the tag
git push origin v0.1.0
```

### Post-Release Tag (post-modularization)

Mark completion of modularization process:

```bash
# Create post-modularization tag
git tag -a post-modularization -m "Checkpoint after modularization completion

This tag marks the completion of the modularization process for v0.1.0.

Modularization achievements:
✅ GPT-OSS plugins successfully moved to separate package
✅ Compatibility layer implemented and tested
✅ All tests passing (81+ tests)
✅ Performance improvements verified
✅ Migration documentation complete
✅ Release deployed to PyPI successfully

Package state:
- entity-core 0.1.0: Core framework only
- entity-plugin-gpt-oss 0.1.0: GPT-OSS plugins (separate)

This serves as a reference point for:
- Future modularization of other plugin suites
- Measuring success of the modular architecture
- Understanding the complete modularization implementation

Next phase: Monitor adoption and prepare for v0.2.0 (remove compat layer)"

# Push the tag
git push origin post-modularization
```

### Checkpoint Tag (checkpoint-46)

Development checkpoint for Story 7 completion:

```bash
# Create checkpoint for Story 7 completion
git tag -a checkpoint-46 -m "Checkpoint 46: Story 7 Complete - Release Preparation

Story 7 (Release Preparation and Rollback Plan) completed successfully.

Deliverables completed:
✅ Detailed release notes (RELEASE_NOTES.md)
✅ Emergency rollback procedure (ROLLBACK.md)
✅ Version bumping strategy (VERSION_STRATEGY.md)
✅ Git tags documentation (GIT_TAGS.md)
✅ User announcement template (ANNOUNCEMENT.md)
✅ Compatibility layer support timeline documented
✅ Issue templates created (.github/ISSUE_TEMPLATE/)
✅ PyPI package preparation verified

All Story 7 acceptance criteria met:
- Release documentation complete and comprehensive
- Rollback plan tested and validated
- Version strategy follows semantic versioning
- Git tags properly documented
- User communication materials ready
- Support timeline clearly defined
- Issue templates for migration support
- Package publishing process verified

Next: Ready for v0.1.0 release deployment

Test results: All release preparation tests pass
Documentation: Complete and reviewed"

# Push the tag
git push origin checkpoint-46
```

---

## 📖 Tag Usage Examples

### Viewing Tag Information

```bash
# List all tags
git tag -l

# List tags with pattern
git tag -l "v*"
git tag -l "checkpoint-*"

# Show tag details
git show v0.1.0
git show pre-modularization

# Check out specific tag
git checkout v0.1.0
git checkout pre-modularization

# Compare tags
git diff pre-modularization..v0.1.0
```

### Creating Release from Tag

```bash
# Build from specific tag
git checkout v0.1.0
poetry build

# Verify tag integrity
git tag -v v0.1.0  # If signed
git show-ref --tags
```

### Tag-based Rollback

```bash
# Emergency rollback to pre-modularization
git checkout pre-modularization
git checkout -b emergency-rollback
git push origin emergency-rollback

# Alternative: reset main to tag
git checkout main
git reset --hard pre-modularization
git push origin main --force-with-lease
```

---

## 🔍 Tag Verification

### Verify Tag Integrity

```bash
# Check tag exists
git tag -l | grep v0.1.0

# Verify tag points to correct commit
git rev-list -n 1 v0.1.0

# Check tag message
git tag -l --format='%(refname:short): %(contents:subject)' v0.1.0

# Verify working tree at tag
git checkout v0.1.0
python -c "import entity; print(entity.__version__)"
```

### Tag Validation Checklist

Before creating release tags:

- [ ] **Commit verified** - All changes committed and pushed
- [ ] **Tests passing** - All tests pass at tag point
- [ ] **Version updated** - pyproject.toml shows correct version
- [ ] **Documentation current** - All docs reflect new version
- [ ] **Clean working tree** - No uncommitted changes
- [ ] **Branch up to date** - Latest changes from main

After creating tags:

- [ ] **Tag pushed** - Tag exists in remote repository
- [ ] **Tag accessible** - Others can fetch and checkout tag
- [ ] **Tag message clear** - Descriptive message with key info
- [ ] **Package buildable** - Can build release package from tag
- [ ] **Installation works** - Package installs from tag

---

## 📊 Tag History Timeline

```
Timeline of Entity Framework Git Tags:

[Pre-modularization Era]
v0.0.12 ←─── Last stable release before modularization
    │
    ├─ checkpoint-40 (Story 1: Verification)
    ├─ checkpoint-41 (Story 2: Duplicate Removal)
    ├─ checkpoint-42 (Story 3: Enhanced Compatibility)
    ├─ checkpoint-43 (Story 4: Documentation)
    └─ checkpoint-44 (Story 5: Documentation & Dependencies)

pre-modularization ←─── Rollback reference point
    │
    │ [Modularization Implementation]
    │
    ├─ checkpoint-45 (Story 6: Performance Validation)
    └─ checkpoint-46 (Story 7: Release Preparation)

v0.1.0 ←─── Major release: Plugin modularization
    │
post-modularization ←─── Modularization completion marker

[Future releases]
v0.1.1 ←─── Planned patch release
v0.1.2 ←─── Additional patches
v0.2.0 ←─── Remove compatibility layer
```

---

## 🚨 Emergency Tag Procedures

### Critical Issue Tag Creation

If critical issues are found post-release:

```bash
# Create emergency rollback tag
git tag -a v0.1.0-rollback -m "Emergency rollback point for v0.1.0

Critical issues identified in v0.1.0 requiring rollback:
- Issue: [DESCRIBE CRITICAL ISSUE]
- Impact: [USER IMPACT SCOPE]
- Timeline: [WHEN DISCOVERED]

This tag marks the stable rollback state.
Rollback procedure: See ROLLBACK.md
Root cause analysis: [LINK TO ISSUE]"

# Create hotfix tag (if applicable)
git tag -a v0.1.1-hotfix -m "Critical hotfix for v0.1.0

Emergency hotfix addressing:
- [CRITICAL ISSUE 1]
- [CRITICAL ISSUE 2]

This is a critical patch release. All v0.1.0 users should upgrade immediately.
Hotfix details: [LINK TO HOTFIX PR]"
```

### Tag Cleanup (If needed)

```bash
# Remove incorrect tag (local)
git tag -d v0.1.0-incorrect

# Remove incorrect tag (remote)
git push origin :refs/tags/v0.1.0-incorrect

# WARNING: Only do this for tags that haven't been released publicly
```

---

## 📞 Tag Management Contacts

### Tag Creation Authority
- **Release Manager:** Creates official release tags
- **Technical Lead:** Approves tag content and timing
- **DevOps Lead:** Executes tag push and verification

### Tag Verification Team
- **QA Lead:** Validates tag builds and functionality
- **Documentation:** Ensures tag messages are accurate
- **Support:** Verifies tag accessibility for users

---

This git tags documentation ensures proper version control, clear release tracking, and reliable rollback capabilities for the Entity Framework modularization project.
