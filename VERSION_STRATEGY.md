# Version Bumping Strategy

**Document Version:** 1.0
**Effective Date:** Q2 2024
**Scope:** Entity Framework Modularization Release

---

## 📊 Current Version Status

### Pre-Modularization
- **Last Stable Version:** `v0.0.12`
- **Git Tag:** `pre-modularization`
- **PyPI Package:** `entity-core==0.0.12`

### Post-Modularization Target
- **New Version:** `v0.1.0` (Major milestone)
- **Semantic Versioning:** Following semver.org principles
- **Breaking Changes:** Yes (import path changes)

---

## 🎯 Semantic Versioning Strategy

### Version Format: `MAJOR.MINOR.PATCH`

```
v0.1.0
│ │ │
│ │ └── PATCH: Bug fixes, documentation updates
│ └──── MINOR: New features, backward compatible
└────── MAJOR: Breaking changes, architectural changes
```

### Why v0.1.0 (Not v1.0.0)?

- **Pre-1.0 Development:** Framework still evolving
- **API Stability:** Not yet guaranteed for long-term
- **Modularization:** Major architectural change
- **Breaking Changes:** Expected during pre-1.0 period

---

## 🚀 Release Version Plan

### v0.1.0 - Modularization Release
**Target Date:** Q2 2024
**Type:** MAJOR (breaking changes)

#### Changes
- ✅ GPT-OSS plugins moved to separate package
- ✅ Import path changes (breaking)
- ✅ Compatibility layer added
- ✅ Performance improvements
- ✅ Architecture refactor

#### Version Components
```toml
[project]
name = "entity-core"
version = "0.1.0"
```

#### Git Tags
```bash
git tag -a v0.1.0 -m "Release v0.1.0: Plugin Modularization

Major Changes:
- Modularized GPT-OSS plugins into separate package
- Added compatibility layer for smooth migration
- Improved import performance and memory usage
- Breaking change: Import paths for GPT-OSS plugins

Migration guide: MIGRATION.md
Rollback plan: ROLLBACK.md"
```

### v0.1.x - Patch Releases
**Timeline:** As needed after v0.1.0

#### v0.1.1 (Potential hotfix)
- Bug fixes for compatibility layer
- Performance optimizations
- Documentation updates
- No breaking changes

#### v0.1.2, v0.1.3, etc.
- Additional bug fixes
- Minor improvements
- Maintained backward compatibility

### v0.2.0 - Compatibility Layer Removal
**Target Date:** Q4 2024 (6 months deprecation)
**Type:** MINOR (removal of deprecated features)

#### Changes
- Remove GPT-OSS compatibility layer
- Clean up deprecated import warnings
- Pure modular architecture
- Performance improvements from cleanup

#### Migration Requirements
- All users must migrate to new import paths
- `entity-plugin-gpt-oss` package required
- No backward compatibility for old imports

---

## 🏷️ Git Tagging Strategy

### Tag Naming Convention

```bash
# Release tags
v0.1.0          # Major release
v0.1.1          # Patch release
v0.1.0-rc.1     # Release candidate
v0.1.0-beta.1   # Beta release
v0.1.0-alpha.1  # Alpha release

# Milestone tags
pre-modularization   # Before major changes
post-modularization  # After modularization complete
checkpoint-45        # Development checkpoint

# Emergency tags
v0.1.0-rollback     # Emergency rollback point
v0.1.1-hotfix       # Critical hotfix
```

### Required Tags for v0.1.0

```bash
# 1. Pre-release snapshot
git tag -a pre-modularization -m "Checkpoint before modularization

This tag marks the last commit before the major modularization
changes. Use this tag for rollback if v0.1.0 has critical issues.

- All GPT-OSS plugins in main repository
- Original import paths working
- Stable functionality baseline"

# 2. Release candidate (if needed)
git tag -a v0.1.0-rc.1 -m "Release Candidate 1 for v0.1.0

- Modularization complete
- Ready for final testing
- Breaking changes implemented
- Documentation complete"

# 3. Official release
git tag -a v0.1.0 -m "Release v0.1.0: Plugin Modularization

Major milestone release introducing plugin modularization:

🎯 Key Features:
- GPT-OSS plugins moved to separate package
- Compatibility layer for smooth migration
- 40% reduction in core framework size
- Improved performance and memory usage

⚠️  Breaking Changes:
- Import paths changed for GPT-OSS plugins
- entity-plugin-gpt-oss package required
- Deprecation warnings for old imports

📚 Documentation:
- Migration guide: MIGRATION.md
- Release notes: RELEASE_NOTES.md
- Rollback plan: ROLLBACK.md

🔗 Related Packages:
- entity-core v0.1.0
- entity-plugin-gpt-oss v0.1.0"
```

### Tag Creation Commands

```bash
# Create and push tags
git tag -a v0.1.0 -m "Release v0.1.0: Plugin Modularization"
git push origin v0.1.0

# Create lightweight checkpoint tags
git tag checkpoint-46
git push origin checkpoint-46

# List all tags
git tag -l "v*" --sort=-version:refname
```

---

## 📦 Package Version Management

### PyPI Package Coordination

#### entity-core Package
```toml
[project]
name = "entity-core"
version = "0.1.0"
dependencies = [
    # Core dependencies only
    # NO entity-plugin-gpt-oss in required deps
]

[project.optional-dependencies]
gpt-oss = [
    "entity-plugin-gpt-oss>=0.1.0,<0.2.0"
]
```

#### entity-plugin-gpt-oss Package
```toml
[project]
name = "entity-plugin-gpt-oss"
version = "0.1.0"  # Independent versioning
dependencies = [
    "entity-core>=0.1.0,<0.2.0"  # Compatible core versions
]
```

### Version Compatibility Matrix

| entity-core | entity-plugin-gpt-oss | Status |
|-------------|----------------------|--------|
| 0.0.12 | N/A | Legacy (GPT-OSS included) |
| 0.1.0 | 0.1.0+ | Recommended |
| 0.1.x | 0.1.x | Compatible |
| 0.2.0 | 0.1.x+ | Compatible (no compat layer) |

---

## 🔄 Version Bump Process

### Automated Version Management

```bash
# 1. Update version in pyproject.toml
poetry version 0.1.0

# 2. Update version references in code (if any)
grep -r "0.0.12" src/ docs/ | head -5

# 3. Update CHANGELOG.md
echo "## [0.1.0] - $(date +%Y-%m-%d)" >> CHANGELOG.md

# 4. Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.1.0 for modularization release"

# 5. Create and push tag
git tag -a v0.1.0 -m "Release v0.1.0: Plugin Modularization"
git push origin main v0.1.0

# 6. Build and publish
poetry build
poetry publish
```

### Pre-Release Versions

For testing before official release:

```bash
# Alpha release
poetry version 0.1.0a1
poetry build
poetry publish --repository testpypi

# Beta release
poetry version 0.1.0b1
poetry build
poetry publish --repository testpypi

# Release candidate
poetry version 0.1.0rc1
poetry build
poetry publish --repository testpypi
```

---

## 📈 Future Version Roadmap

### Short-term (0.1.x series)
- **v0.1.0:** Initial modularization release
- **v0.1.1:** Bug fixes and improvements
- **v0.1.2:** Performance optimizations
- **v0.1.3:** Additional plugin packages

### Medium-term (0.2.x series)
- **v0.2.0:** Remove compatibility layer
- **v0.2.1:** Full modular architecture
- **v0.2.x:** New plugin ecosystems

### Long-term (0.3.x+ series)
- **v0.3.0:** Additional core improvements
- **v0.4.0:** Advanced plugin features
- **v1.0.0:** Stable API guarantee (when ready)

---

## 🚦 Release Readiness Criteria

### Version Bump Prerequisites

Before bumping to v0.1.0:

- [ ] **All acceptance criteria met** for modularization stories
- [ ] **Test coverage maintained** (no reduction)
- [ ] **Performance benchmarks** meet targets
- [ ] **Documentation complete** (migration guide, release notes)
- [ ] **Compatibility layer tested** and working
- [ ] **Rollback plan prepared** and tested
- [ ] **PyPI packages ready** for both core and plugin
- [ ] **Issue templates created** for migration support

### Version Validation

```bash
# 1. Version consistency check
poetry version  # Should show 0.1.0
git describe --tags  # Should show v0.1.0 or newer

# 2. Package build test
poetry build
ls dist/  # Should show entity_core-0.1.0.tar.gz and .whl

# 3. Installation test
pip install dist/entity_core-0.1.0-py3-none-any.whl
python -c "import entity; print(entity.__version__)"

# 4. Dependency resolution test
pip install entity-core==0.1.0
pip list | grep entity
```

---

## 🎯 Success Metrics

### Version Release Success Criteria

- **Installation Success Rate:** >95% successful installations
- **Import Success Rate:** >99% successful imports
- **Migration Completion:** >80% users migrate within 30 days
- **Performance Targets:** No regression from v0.0.12
- **Support Tickets:** <10 migration-related tickets per week

### Monitoring and Rollback Triggers

Monitor these metrics for 48 hours post-release:

- PyPI download statistics
- GitHub issue creation rate
- Community forum question volume
- Performance benchmark results
- User feedback sentiment

**Rollback triggers:**
- >10% installation failure rate
- >5% import failure rate
- >50% performance regression
- Critical security vulnerabilities

---

## 📞 Version Management Contacts

### Release Authority
- **Release Manager:** Responsible for version decisions
- **Technical Lead:** Technical approval for version bumps
- **Product Owner:** Business approval for breaking changes

### Execution Team
- **DevOps:** Git tagging and PyPI publishing
- **QA:** Version validation and testing
- **Documentation:** Version-specific documentation updates
- **Support:** Version-related user assistance

---

This version strategy ensures smooth releases, clear migration paths, and reliable rollback capabilities for the Entity Framework modularization.
