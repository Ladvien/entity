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








## Definition of Done (for all stories)
- Code changes completed and committed
- Unit tests pass
- Integration tests pass
- Documentation updated
- Code reviewed by senior developer
- No reduction in code coverage
- Deprecation warnings are clear and actionable
- Changes work in both development and production environments
