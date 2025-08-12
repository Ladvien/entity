# Entity Framework Plugin Migration Rollback Plan

## Overview

This document provides a comprehensive rollback plan for the Entity Framework plugin migration to Git submodules. If critical issues are discovered post-migration, this plan enables a safe return to the previous monolithic structure.

## Risk Assessment

### Low Risk Items
- Documentation updates
- CI/CD configuration changes
- New utility scripts

### Medium Risk Items
- Import path changes
- Package structure modifications
- Development workflow changes

### High Risk Items
- Git submodule dependencies
- Breaking changes to public APIs
- Data loss from removed plugin code

## Pre-Rollback Checklist

Before initiating rollback:

1. **Document the Issue**
   - [ ] Record the specific problem requiring rollback
   - [ ] Capture error messages and logs
   - [ ] Note affected systems and users

2. **Backup Current State**
   - [ ] Create a backup branch: `git checkout -b backup-migration-state`
   - [ ] Push to remote: `git push origin backup-migration-state`
   - [ ] Export submodule states: `git submodule status > submodule-state.txt`

3. **Notify Stakeholders**
   - [ ] Inform development team
   - [ ] Alert users of potential disruption
   - [ ] Coordinate rollback timing

## Rollback Procedures

### Phase 1: Restore Plugin Code (Priority: HIGH)

#### Step 1.1: Create Rollback Branch
```bash
# Create rollback branch from last known good commit
git checkout -b rollback-plugins
git reset --hard <last-good-commit-before-migration>
```

#### Step 1.2: Restore Plugin Directories
```bash
# Restore plugins from commit history
git checkout <commit-before-ENTITY-103> -- src/entity/plugins/

# Verify restoration
ls -la src/entity/plugins/
```

#### Step 1.3: Remove Submodules
```bash
# Remove submodule entries
git submodule deinit -f plugins/examples
git submodule deinit -f plugins/gpt-oss
git submodule deinit -f plugins/stdlib
git submodule deinit -f plugins/template

# Remove submodule directories
rm -rf plugins/

# Remove .gitmodules file
rm -f .gitmodules

# Clean git cache
git rm --cached -r plugins/ 2>/dev/null || true

# Commit changes
git add -A
git commit -m "rollback: Remove git submodules, restore monolithic structure"
```

### Phase 2: Revert Import Paths (Priority: HIGH)

#### Step 2.1: Restore Original Imports
```bash
# Create and run import restoration script
cat > scripts/restore_original_imports.sh << 'EOF'
#!/bin/bash

# Restore original import patterns
FILES=$(find . -name "*.py" -type f -not -path "./.venv/*" -not -path "./plugins/*")

for file in $FILES; do
    # Restore entity.plugins imports
    sed -i.bak 's/from entity_plugin_examples/from entity.plugins.examples/g' "$file"
    sed -i.bak 's/import entity_plugin_examples/import entity.plugins.examples/g' "$file"
    sed -i.bak 's/from entity_plugin_gpt_oss/from entity.plugins.gpt_oss/g' "$file"
    sed -i.bak 's/import entity_plugin_gpt_oss/import entity.plugins.gpt_oss/g' "$file"

    # Remove backup files
    rm -f "${file}.bak"
done

echo "Import paths restored"
EOF

chmod +x scripts/restore_original_imports.sh
./scripts/restore_original_imports.sh
```

#### Step 2.2: Update Compatibility Layers
```bash
# Restore original compatibility layers
git checkout <commit-before-ENTITY-105> -- src/entity/plugins/*_compat.py
```

### Phase 3: Revert CI/CD Changes (Priority: MEDIUM)

#### Step 3.1: Restore Workflow Files
```bash
# Restore original workflow files
git checkout <commit-before-ENTITY-107> -- .github/workflows/

# Remove new workflow files
rm -f .github/workflows/plugin-management.yml
rm -f .github/workflows/release-automation.yml
```

#### Step 3.2: Verify Workflows
```bash
# Validate YAML syntax
for workflow in .github/workflows/*.yml; do
    python3 -c "import yaml; yaml.safe_load(open('$workflow'))"
    echo "✓ $workflow is valid"
done
```

### Phase 4: Revert Documentation (Priority: LOW)

#### Step 4.1: Restore Documentation
```bash
# Restore original documentation
git checkout <commit-before-ENTITY-106> -- README.md
git checkout <commit-before-ENTITY-106> -- CONTRIBUTING.md

# Remove new documentation
rm -f PLUGIN_DEVELOPMENT.md
rm -f MIGRATION_ROLLBACK_PLAN.md
```

### Phase 5: Clean Up Scripts (Priority: LOW)

#### Step 5.1: Remove Migration Scripts
```bash
# Remove migration-specific scripts
rm -f scripts/create_plugin_repos.sh
rm -f scripts/push_plugin_code.sh
rm -f scripts/clean_plugin_directories.sh
rm -f scripts/add_plugin_submodules.sh
rm -f scripts/update_plugin_imports.sh
rm -f scripts/validate_migration.sh
```

## Post-Rollback Verification

### Verification Checklist

1. **Code Structure**
   - [ ] Verify `src/entity/plugins/` directory exists
   - [ ] Confirm all plugin code is present
   - [ ] Check no submodule references remain

2. **Import Testing**
   ```python
   # Test imports work
   from entity.plugins.examples import ExamplePlugin
   from entity.plugins.gpt_oss import GPTOSSPlugin
   print("✓ Imports successful")
   ```

3. **Run Test Suite**
   ```bash
   # Run all tests
   poetry run pytest

   # Run specific plugin tests
   poetry run pytest tests/plugins/
   ```

4. **CI/CD Verification**
   ```bash
   # Trigger CI manually
   git push origin rollback-plugins
   # Monitor GitHub Actions for success
   ```

5. **Documentation Check**
   - [ ] Verify README reflects monolithic structure
   - [ ] Check contributing guide is accurate
   - [ ] Remove references to submodules

## Emergency Hotfix Procedure

If immediate action is required without full rollback:

### Option 1: Vendor Submodules
```bash
# Convert submodules to vendored code
git submodule foreach 'git archive HEAD | tar -x -C "$toplevel/src/entity/plugins/$name"'
git rm .gitmodules
git add src/entity/plugins/
git commit -m "hotfix: Vendor submodules for stability"
```

### Option 2: Pin Submodule Versions
```bash
# Pin all submodules to specific commits
git submodule foreach 'git checkout <stable-commit>'
git add .
git commit -m "hotfix: Pin submodule versions"
```

### Option 3: Fallback Branch
```bash
# Maintain parallel non-submodule branch
git checkout -b main-no-submodules
# Cherry-pick only non-submodule changes
git cherry-pick <commits>
```

## Recovery Timeline

| Phase | Priority | Estimated Time | Dependencies |
|-------|----------|---------------|--------------|
| Backup Current State | Critical | 5 minutes | None |
| Restore Plugin Code | High | 15 minutes | Backup complete |
| Revert Import Paths | High | 20 minutes | Plugin code restored |
| Revert CI/CD | Medium | 10 minutes | Code restored |
| Revert Documentation | Low | 5 minutes | None |
| Verification | Critical | 30 minutes | All phases complete |

**Total Estimated Time: 1.5 hours**

## Rollback Decision Matrix

| Issue Severity | User Impact | Rollback Decision |
|---------------|-------------|-------------------|
| Critical - Production broken | All users affected | Immediate rollback |
| High - Major features broken | >50% users affected | Rollback within 4 hours |
| Medium - Some features broken | <50% users affected | Hotfix first, rollback if needed |
| Low - Minor issues | Minimal impact | Fix forward, no rollback |

## Contact Information

### Rollback Approval Authority
- Technical Lead: [Contact Info]
- Project Manager: [Contact Info]

### Support During Rollback
- DevOps Team: [Contact Info]
- QA Team: [Contact Info]

## Lessons Learned Log

After any rollback, document:

1. **What triggered the rollback?**
2. **What could have prevented it?**
3. **How can we improve the migration process?**
4. **What additional testing is needed?**

## Appendix: Reference Commands

### Useful Git Commands
```bash
# Show commits before migration
git log --oneline --before="2024-08-01" -20

# Find specific file in history
git log --all --full-history -- "**/plugin_name.py"

# Show file content at specific commit
git show <commit>:path/to/file

# List all branches including remote
git branch -a

# Show submodule commit history
git log -p --submodule
```

### Checkpoint Branches
The following checkpoint branches contain pre-migration states:
- `checkpoint-52`: Before Story ENTITY-105
- `checkpoint-53`: Before Story ENTITY-106
- `checkpoint-54`: Before Story ENTITY-107
- `checkpoint-55`: Current migration state

---

**Document Version:** 1.0
**Last Updated:** 2024-08-11
**Status:** Active

*This rollback plan should be reviewed and updated after each significant change to the migration process.*
