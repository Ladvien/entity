# Entity Framework Plugin Migration - Jira Stories (Updated for gh CLI)

## Epic: Migrate Entity Framework Plugins to Submodules
**Epic Key:** ENTITY-100
**Epic Summary:** Migrate all Entity Framework plugins to separate repositories and integrate as Git submodules
**Business Value:** Enables independent plugin versioning, cleaner separation of concerns, and optional plugin loading

---



## 🧹 Story 3: Clean Plugin Directories from Main Repository
**Key:** ENTITY-103
**Type:** Task
**Priority:** High
**Story Points:** 2
**Blocked By:** ENTITY-102
**Assignee:** Backend Team

### Description
Remove plugin code from main repository that will conflict with submodules, after verifying successful push to new repositories.

### Acceptance Criteria
- [ ] Verify all plugin repos have code using `gh repo clone --dry-run`
- [ ] Create timestamped backup of directories being removed
- [ ] Remove src/entity/plugins/examples
- [ ] Remove src/entity/plugins/gpt_oss
- [ ] Evaluate and handle tests/plugins/gpt_oss
- [ ] Preserve src/entity/plugins/defaults
- [ ] No broken imports in main codebase

### Technical Notes
- Use `gh api repos/Ladvien/entity-plugin-*/contents` to verify files exist before deletion
- Document any import paths that need updating

### Definition of Done
- [ ] Backup archive created and verified
- [ ] Directories removed from main repo
- [ ] Main entity-core still runs

---

## 📦 Story 4: Add Plugins as Git Submodules
**Key:** ENTITY-104
**Type:** Task
**Priority:** High
**Story Points:** 2
**Blocked By:** ENTITY-103
**Assignee:** DevOps Team

### Description
Add plugin repositories as Git submodules under plugins/ directory using URLs obtained from gh CLI.

### Acceptance Criteria
- [ ] Use `gh repo view --json url` to get repository URLs programmatically
- [ ] plugins/ directory created
- [ ] All four plugins added as submodules
- [ ] .gitmodules file created with correct entries
- [ ] Original entity-plugin-* directories removed
- [ ] Changes committed to entity-core

### Technical Notes
- Script should use gh CLI to fetch repo URLs rather than hardcoding
- Submodule paths: plugins/examples, plugins/gpt-oss, plugins/stdlib, plugins/template

### Definition of Done
- [ ] `git submodule status` shows all four submodules
- [ ] Submodules initialized and populated
- [ ] Changes pushed to entity-core

---

## 🔧 Story 5: Update Plugin Import Paths
**Key:** ENTITY-105
**Type:** Task
**Priority:** Medium
**Story Points:** 5
**Blocked By:** ENTITY-104
**Assignee:** Backend Team

### Description
Update all import statements throughout codebase to reference new submodule locations.

### Acceptance Criteria
- [ ] Script created to find all old import patterns
- [ ] Plugin loader updated for new structure
- [ ] All imports updated to new paths
- [ ] No ImportError when running entity-core
- [ ] Tests pass with new structure

### Definition of Done
- [ ] Zero occurrences of old import patterns
- [ ] All tests passing
- [ ] Plugin discovery working

---

## 📚 Story 6: Update Documentation
**Key:** ENTITY-106
**Type:** Task
**Priority:** Medium
**Story Points:** 3
**Blocked By:** ENTITY-105
**Assignee:** Documentation Team

### Description
Update documentation to reflect new plugin structure and gh CLI workflow.

### Acceptance Criteria
- [ ] README includes submodule clone instructions
- [ ] Developer setup guide includes gh CLI setup
- [ ] Plugin development guide updated with new workflow
- [ ] Contributing guide explains plugin contribution process
- [ ] Security notes about using fine-grained PATs included

### Technical Notes
- Document `gh repo fork` workflow for contributors
- Include `gh pr create` workflow for plugin contributions

### Definition of Done
- [ ] All documentation reflects new structure
- [ ] No references to old plugin locations

---

## 🔄 Story 7: Update CI/CD Pipeline
**Key:** ENTITY-107
**Type:** Task
**Priority:** High
**Story Points:** 3
**Blocked By:** ENTITY-104
**Assignee:** DevOps Team

### Description
Update GitHub Actions to handle submodules and use gh CLI where beneficial.

### Acceptance Criteria
- [ ] CI/CD uses `actions/checkout@v3` with `submodules: recursive`
- [ ] GitHub Actions workflow uses gh CLI for any repo operations
- [ ] Secrets properly configured for gh CLI in Actions
- [ ] Plugin tests run in CI
- [ ] Documentation builds include plugin docs

### Definition of Done
- [ ] All workflows pass with submodules
- [ ] gh CLI operations in CI are using tokens with minimal permissions

---

## 🧪 Story 8: Validate Migration
**Key:** ENTITY-108
**Type:** Task
**Priority:** High
**Story Points:** 2
**Blocked By:** ENTITY-107
**Assignee:** QA Team

### Description
Comprehensive validation of the migration using gh CLI to verify repository state.

### Test Checklist
- [ ] Use `gh repo clone Ladvien/entity --recurse-submodules` for fresh test
- [ ] Verify with `gh repo list Ladvien --topic entity-plugin` (if topics added)
- [ ] Use `gh api` to verify repository metadata
- [ ] All example scripts work
- [ ] Performance benchmarks show no degradation
- [ ] Security scan shows no exposed secrets

### Definition of Done
- [ ] All validation checks pass
- [ ] Sign-off from tech lead
- [ ] Migration rollback plan documented

---

## 📈 Story 9: Create Management Tooling
**Key:** ENTITY-109
**Type:** Task
**Priority:** Low
**Story Points:** 2
**Blocked By:** ENTITY-108
**Assignee:** Backend Team

### Description
Create helper scripts using gh CLI for plugin management.

### Acceptance Criteria
- [ ] Script to update all plugins using gh CLI
- [ ] Script to check plugin versions using `gh release list`
- [ ] Script to create new plugin from template using `gh repo create` and `gh repo clone`
- [ ] Script to list all plugin PRs using `gh pr list`
- [ ] All scripts use gh CLI for GitHub operations

### Definition of Done
- [ ] Management scripts created and documented
- [ ] Scripts handle authentication gracefully
- [ ] README updated with management commands

---

## Dependencies Graph
```
ENTITY-101 (Create Repos with gh)
    ↓
ENTITY-102 (Push Code)
    ↓
ENTITY-103 (Clean Conflicts)
    ↓
ENTITY-104 (Add Submodules)
    ↓
    ├── ENTITY-105 (Update Imports)
    ├── ENTITY-106 (Update Docs)
    └── ENTITY-107 (Update CI/CD)
         ↓
    ENTITY-108 (Validate)
         ↓
    ENTITY-109 (Management Tools)
```

## Sprint Planning
- **Sprint 1:** ENTITY-101, ENTITY-102, ENTITY-103, ENTITY-104
- **Sprint 2:** ENTITY-105, ENTITY-106, ENTITY-107
- **Sprint 3:** ENTITY-108, ENTITY-109
