# Epic: Modularize Entity Framework Plugins and Reduce Code Duplication

## Epic Description
Refactor the Entity Framework to eliminate code duplication and move plugin suites into separate repositories as Git submodules. This will reduce the core framework size by approximately 40%, improve maintainability, and allow independent versioning of plugin suites.

---

---

## Story 3: Create Shared Plugin Utilities

### Description
Extract common patterns from plugins into reusable mixins and utilities to reduce code duplication across all plugins.

### Acceptance Criteria
- [ ] Common mixins created for repeated patterns
- [ ] Validation utilities consolidated
- [ ] Rate limiting extracted to shared component
- [ ] Caching utilities standardized
- [ ] All plugins updated to use shared utilities

### Subtasks

#### Task 3.1: Create Plugin Mixins Module
**Instructions for Junior Engineer:**
1. Create `entity/plugins/mixins.py` file
2. Identify and implement ConfigValidationMixin:
   - Find all plugins that validate configuration
   - Extract common validation pattern
   - Create method that validates and raises on error
   - Add method for validation with custom error messages
3. Implement LoggingMixin:
   - Analyze logging patterns across all plugins
   - Create convenience methods for each log level
   - Add structured logging helpers
   - Include automatic context extraction
4. Create MetricsMixin:
   - Extract metrics collection patterns
   - Provide methods for timing operations
   - Add counters and gauges helpers
   - Include aggregation utilities
5. Implement ErrorHandlingMixin:
   - Consolidate error handling patterns
   - Create decorators for common error scenarios
   - Add retry logic helpers
   - Include circuit breaker pattern

#### Task 3.2: Consolidate Validation Utilities
**Instructions for Junior Engineer:**
1. Create `entity/core/validators.py` module
2. Extract SQL validation from SecureDatabaseResource:
   - Move SQL injection detection patterns
   - Move table name validation
   - Move column name validation
   - Create reusable validation functions
3. Consolidate identifier validation:
   - Find all regex patterns for identifiers
   - Create single source of truth
   - Add validation functions with clear names
4. Extract JSON/YAML validation:
   - Consolidate schema validation logic
   - Create type checking utilities
   - Add format validators
5. Create validation result builders:
   - Standardize validation result format
   - Provide builder pattern for complex validations
   - Include helpers for common validation scenarios

#### Task 3.3: Extract Rate Limiting Component
**Instructions for Junior Engineer:**
1. Create `entity/core/rate_limiter.py` module
2. Analyze existing rate limiters:
   - GPTOSSToolOrchestrator.RateLimiter
   - BrowserTool rate limiting
   - PythonTool rate limiting
3. Design unified RateLimiter class:
   - Support different time windows
   - Allow multiple rate limit tiers
   - Include burst handling
   - Add distributed rate limiting hooks
4. Implement rate limiter features:
   - Sliding window algorithm
   - Token bucket algorithm option
   - Async-safe implementation
   - Reset and manual override methods
5. Create rate limiter factory:
   - Preset configurations for common use cases
   - Easy integration with plugins
   - Monitoring and metrics hooks

---

## Story 4: Refactor Memory Resources

### Description
Consolidate the four memory implementations using composition pattern to eliminate duplicate code while maintaining all functionality.

### Acceptance Criteria
- [ ] Base memory interface defined as Protocol
- [ ] Feature decorators implement TTL, LRU, locking
- [ ] Composition allows mixing features
- [ ] All existing memory classes maintain compatibility
- [ ] Performance is not degraded

### Subtasks

#### Task 4.1: Design Memory Component Architecture
**Instructions for Junior Engineer:**
1. Create `entity/resources/memory_components.py`
2. Define IMemory Protocol:
   - List all methods that must be implemented
   - Include both sync and async variants
   - Document expected behavior for each method
3. Design decorator pattern structure:
   - Each decorator wraps an IMemory instance
   - Decorators can be chained
   - Each adds specific functionality
4. Plan migration strategy:
   - How to maintain backward compatibility
   - Deprecation timeline
   - Testing approach
5. Document the architecture:
   - Create architecture diagram
   - Show how components compose
   - Provide usage examples

#### Task 4.2: Implement Memory Feature Decorators
**Instructions for Junior Engineer:**
1. Create TTLDecorator class:
   - Wrap base memory operations
   - Track expiration times for keys
   - Implement automatic cleanup
   - Add store_with_ttl method
2. Implement LRUDecorator:
   - Track access patterns
   - Implement eviction policy
   - Configure maximum entries
   - Add metrics collection
3. Create LockingDecorator:
   - Implement process-safe locking
   - Support timeout-based acquisition
   - Add deadlock detection
   - Include lock metrics
4. Build AsyncDecorator:
   - Convert sync operations to async
   - Handle connection pooling
   - Implement proper cleanup
5. Add MonitoringDecorator:
   - Track all operations
   - Collect performance metrics
   - Generate usage reports

#### Task 4.3: Migrate Existing Memory Classes
**Instructions for Junior Engineer:**
1. Refactor base Memory class:
   - Extract core functionality
   - Implement IMemory protocol
   - Remove duplicate code
2. Update AsyncMemory:
   - Use AsyncDecorator instead of reimplementing
   - Maintain exact same interface
   - Ensure all tests pass
3. Refactor ManagedMemory:
   - Compose using TTLDecorator and LRUDecorator
   - Preserve all existing methods
   - Maintain configuration compatibility
4. Update RobustMemory:
   - Use LockingDecorator for lock functionality
   - Keep all timeout configurations
   - Preserve metrics collection
5. Create compatibility layer:
   - Factory functions for each old class
   - Deprecation warnings
   - Migration guide documentation

---

## Story 5: Create Plugin Submodule Repositories

### Description
Create and configure the three new plugin repositories as Git submodules: examples, stdlib, and gpt-oss.

### Acceptance Criteria
- [ ] Three new repositories created and configured
- [ ] Plugins successfully moved to respective repositories
- [ ] Submodules integrated with main repository
- [ ] CI/CD passes with submodule structure
- [ ] Documentation updated for new structure

### Subtasks

#### Task 5.1: Initialize Plugin Repositories
**Instructions for Junior Engineer:**
1. Create `entity-plugin-examples` repository:
   - Use the plugin template as base
   - Set description for example/educational plugins
   - Configure as public repository
   - Enable GitHub Pages for documentation
2. Create `entity-plugin-stdlib` repository:
   - Use plugin template
   - Set description for standard/common plugins
   - Configure repository settings
   - Set up release automation
3. Configure `entity-plugin-gpt-oss` repository:
   - Already created in Story 2
   - Verify all settings are correct
   - Ensure CI/CD is working
4. Set up repository permissions:
   - Configure team access
   - Set up branch protection
   - Enable required reviews
5. Create initial releases:
   - Tag version 0.1.0
   - Create GitHub releases
   - Publish to PyPI

#### Task 5.2: Add Submodules to Core Repository
**Instructions for Junior Engineer:**
1. Remove the plugin files that will be moved:
   - Delete files from entity/plugins/examples/
   - Delete files from entity/plugins/gpt_oss/
   - Move smart_selector and web_search to stdlib
2. Add submodules to the core repository:
   - Run git submodule add for each repository
   - Place under libs/ or submodules/ directory
   - Configure .gitmodules file
3. Update import paths:
   - Create import compatibility layer
   - Update all references in core
   - Fix any broken imports
4. Configure development environment:
   - Update development setup instructions
   - Create script to initialize all submodules
   - Add submodule update to Makefile
5. Update CI/CD pipeline:
   - Ensure submodules are checked out
   - Run tests across all submodules
   - Verify integration tests pass

#### Task 5.3: Create Submodule Management Documentation
**Instructions for Junior Engineer:**
1. Create `docs/SUBMODULE_GUIDE.md`:
   - Explain what submodules are
   - Why Entity uses submodules
   - Benefits and tradeoffs
2. Document common operations:
   - How to clone with submodules
   - How to update submodules
   - How to make changes to submodules
   - How to handle merge conflicts
3. Create developer workflow guide:
   - Setting up development environment
   - Making changes across core and plugins
   - Testing changes locally
   - Submitting PRs with submodule changes
4. Add troubleshooting section:
   - Common submodule problems
   - How to fix detached HEAD
   - Recovering from submodule issues
5. Create quick reference card:
   - Most common git commands
   - Submodule-specific commands
   - Emergency recovery procedures

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
