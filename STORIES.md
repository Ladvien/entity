# Epic: Modularize Entity Framework Plugins and Reduce Code Duplication

## Epic Description
Refactor the Entity Framework to eliminate code duplication and move plugin suites into separate repositories as Git submodules. This will reduce the core framework size by approximately 40%, improve maintainability, and allow independent versioning of plugin suites.

---

---

---

## Instructions for Setting Up Separate Repositories as Submodules

### For Repository Administrators:

1. **Create New Plugin Repository**
   - Go to GitHub/GitLab and create new repository
   - Name it `entity-plugin-[name]`
   - Initialize with README, .gitignore (Python), and LICENSE
   - Clone the entity-plugin-template repository content

2. **Configure Repository Settings**
   - Set repository description and topics
   - Configure branch protection for main/master
   - Set up required status checks
   - Enable Dependabot for dependencies
   - Configure security scanning

3. **Set Up CI/CD Secrets**
   - Add PYPI_API_TOKEN for package publishing
   - Add CODECOV_TOKEN for coverage reports
   - Configure any plugin-specific secrets

4. **Initialize Package Structure**
   - Update pyproject.toml with correct package name
   - Set initial version to 0.1.0
   - Update author and maintainer information
   - Configure build and test requirements

5. **Add as Submodule to Core**
   ```
   cd entity-core
   git submodule add https://github.com/org/entity-plugin-[name] submodules/[name]
   git submodule update --init --recursive
   ```

### For Developers:

1. **Clone with Submodules**
   - Use `git clone --recursive` for initial clone
   - Or run `git submodule update --init --recursive` after cloning

2. **Work with Submodules**
   - Make changes in submodule directory
   - Commit changes in submodule first
   - Then commit submodule reference update in main repo

3. **Update Submodules**
   - Run `git submodule update --remote` to get latest
   - Test integration before committing update
   - Submit PR with both submodule and main repo changes

4. **Release Process**
   - Tag version in submodule repository
   - Publish to PyPI from submodule
   - Update version reference in main repository
   - Document compatibility in release notes


# Jira Epic: Complete GPT-OSS Plugin Modularization

## Epic Description
Complete the modularization of GPT-OSS plugins by removing code duplication between the main entity-core repository and the entity-plugin-gpt-oss package. Currently, the same plugin code exists in three places, creating maintenance burden and confusion.

---


## Story 2: Remove Duplicate GPT-OSS Plugin Implementations

### Summary
Delete the duplicate full implementations of GPT-OSS plugins from src/entity/plugins/gpt_oss/ directory

### Description
Remove all full plugin implementation files from the legacy location, keeping only the __init__.py file which will be updated to show deprecation warnings and import from the compatibility layer.

### Acceptance Criteria
- [ ] Delete all 9 individual plugin implementation files from src/entity/plugins/gpt_oss/
- [ ] Keep only the __init__.py file in the gpt_oss directory
- [ ] Update __init__.py to import from gpt_oss_compat module instead of local files
- [ ] Ensure __init__.py maintains the same public API (all plugin classes remain importable)
- [ ] Add clear deprecation warnings in __init__.py indicating the new import path
- [ ] Verify no other parts of the codebase directly import from the deleted files

### Technical Notes
- Files to remove: reasoning_trace.py, structured_output.py, developer_override.py, adaptive_reasoning.py, native_tools.py, multi_channel_aggregator.py, harmony_safety_filter.py, function_schema_registry.py, reasoning_analytics_dashboard.py
- Search entire codebase for any direct imports from these files
- The __init__.py should only contain imports and deprecation warnings, no actual implementation

### Story Points: 3

---

## Story 3: Enhance Compatibility Layer Error Handling

### Summary
Improve the gpt_oss_compat.py compatibility shim to provide better error messages and migration guidance

### Description
The current compatibility layer provides basic functionality but needs enhancement to better guide users through the migration process and handle edge cases where the new package might not be installed.

### Acceptance Criteria
- [ ] Add version checking to ensure entity-plugin-gpt-oss is installed when compatibility layer is used
- [ ] Provide clear, actionable error messages when the package is missing
- [ ] Include migration instructions in error messages
- [ ] Add logging for deprecation warnings (not just warnings.warn)
- [ ] Implement fallback behavior that clearly indicates the plugin is not available rather than failing silently
- [ ] Add a migration guide comment block at the top of the file
- [ ] Ensure all 9 plugin shims follow the same pattern and quality standards

### Technical Notes
- Consider environment detection (development vs. production) for warning verbosity
- Error messages should include: pip install command, new import path, deprecation timeline
- Consider adding a environment variable to suppress deprecation warnings for CI/CD systems

### Story Points: 3

---

## Story 4: Update Integration Tests

### Summary
Create or update integration tests to verify both import paths work correctly during the transition period

### Description
Ensure the codebase has comprehensive tests that verify both the legacy import path (with deprecation warnings) and the new modular import path work correctly. This will help catch any issues during the transition period.

### Acceptance Criteria
- [ ] Create test file test_gpt_oss_migration.py if it doesn't exist
- [ ] Add tests that import plugins using the legacy path (entity.plugins.gpt_oss)
- [ ] Add tests that import plugins using the new path (entity_plugin_gpt_oss)
- [ ] Verify deprecation warnings are properly raised for legacy imports
- [ ] Ensure both import methods result in the same functional behavior
- [ ] Add tests for error cases (package not installed, etc.)
- [ ] Verify all 9 plugins can be instantiated and basic functionality works
- [ ] Document any test environment setup requirements

### Technical Notes
- Use pytest's warning capture functionality to verify deprecation warnings
- Consider using mock/patch for testing package-not-installed scenarios
- Tests should cover both successful imports and error conditions
- May need to update CI/CD configuration to install entity-plugin-gpt-oss package

### Story Points: 5

---

## Story 5: Update Documentation and Dependencies

### Summary
Update all documentation, README files, and dependency declarations to reflect the new modular structure

### Description
Ensure all documentation accurately reflects the new plugin structure and provides clear migration guidance for users. Update dependency files to properly reference the new package.

### Acceptance Criteria
- [ ] Update main README.md with migration notice and new import instructions
- [ ] Create MIGRATION.md guide for moving from legacy to new imports
- [ ] Update requirements.txt/setup.py/pyproject.toml to include entity-plugin-gpt-oss as optional dependency
- [ ] Update any example code in documentation to use new import paths
- [ ] Add deprecation timeline to relevant documentation
- [ ] Update developer documentation explaining the modular architecture
- [ ] Ensure docstrings in compatibility layer are comprehensive
- [ ] Update CHANGELOG.md with breaking change notice

### Technical Notes
- Consider adding the new package as an optional/extras dependency
- Documentation should explain why modularization was done (maintenance, optional features, etc.)
- Include troubleshooting section for common migration issues
- Timeline should specify when compatibility layer will be removed (entity-core 0.1.0)

### Story Points: 3

---

## Story 6: Performance and Import Time Validation

### Summary
Verify that the modularization doesn't negatively impact import times or runtime performance

### Description
Ensure that the new modular structure doesn't introduce performance regressions, particularly around import times and module loading. This is especially important for users who might not need GPT-OSS functionality.

### Acceptance Criteria
- [ ] Measure import time of entity.plugins with and without GPT-OSS plugins
- [ ] Verify lazy loading works correctly (plugins only imported when needed)
- [ ] Ensure no circular import issues exist
- [ ] Confirm memory footprint is reduced when GPT-OSS plugins aren't used
- [ ] Document performance improvements from modularization
- [ ] Create benchmark script for future performance regression testing

### Technical Notes
- Use Python's -X importtime flag for measuring import performance
- Consider using memory_profiler for memory footprint analysis
- Document the performance benefits of the modular approach
- Ensure the compatibility layer doesn't negate performance benefits

### Story Points: 3

---

## Story 7: Release Preparation and Rollback Plan

### Summary
Prepare for release including version bumping, release notes, and a rollback plan if issues are discovered

### Description
Create a comprehensive release plan for the modularization changes, including contingency plans if critical issues are discovered post-release.

### Acceptance Criteria
- [ ] Create detailed release notes explaining the change and migration path
- [ ] Document rollback procedure if critical issues are found
- [ ] Update version numbers appropriately (consider semantic versioning implications)
- [ ] Create git tags for before/after the change
- [ ] Prepare announcement for users about the upcoming change
- [ ] Document support timeline for compatibility layer
- [ ] Create issue templates for migration-related problems
- [ ] Ensure PyPI package is properly published and tested

### Technical Notes
- This is a breaking change for some import patterns, consider major version bump
- Rollback plan should include reverting commits and republishing if needed
- Consider a phased rollout or beta release first
- Monitor issue tracker for migration problems after release

### Story Points: 3

---

## Definition of Done (for all stories)
- Code changes completed and committed
- Unit tests pass
- Integration tests pass
- Documentation updated
- Code reviewed by senior developer
- No reduction in code coverage
- Deprecation warnings are clear and actionable
- Changes work in both development and production environments
