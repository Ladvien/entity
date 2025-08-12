# Entity Framework Plugin Migration - Jira Stories (Updated for gh CLI)

## Epic: Migrate Entity Framework Plugins to Submodules
**Epic Key:** ENTITY-100
**Epic Summary:** Migrate all Entity Framework plugins to separate repositories and integrate as Git submodules
**Business Value:** Enables independent plugin versioning, cleaner separation of concerns, and optional plugin loading

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
