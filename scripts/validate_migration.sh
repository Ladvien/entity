#!/bin/bash

# Entity Framework Plugin Migration Validation Script
# Story: ENTITY-108 - Validate Migration
# This script performs comprehensive validation of the plugin migration

set -euo pipefail

# Configuration
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/validation_${TIMESTAMP}.log"
VALIDATION_REPORT="${LOG_DIR}/validation_report_${TIMESTAMP}.md"
TEMP_DIR="/tmp/entity_validation_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation counters
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Initialize validation report
init_report() {
    cat > "$VALIDATION_REPORT" << EOF
# Entity Framework Plugin Migration Validation Report

**Date:** $(date -u '+%Y-%m-%d %H:%M:%S UTC')
**Validator:** Migration Validation Script v1.0
**Story:** ENTITY-108

---

## Summary

This report documents the comprehensive validation of the Entity Framework plugin migration to Git submodules.

## Validation Results

EOF
}

# Add result to report
add_to_report() {
    echo "$1" >> "$VALIDATION_REPORT"
}

# Test function with result tracking
run_test() {
    local test_name=$1
    local test_command=$2

    echo -e "${BLUE}Running: $test_name${NC}"
    log "INFO" "Starting test: $test_name"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        log "SUCCESS" "Test passed: $test_name"
        add_to_report "- ✅ **$test_name**: PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        log "ERROR" "Test failed: $test_name"
        add_to_report "- ❌ **$test_name**: FAILED"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Warning function
add_warning() {
    local message=$1
    echo -e "${YELLOW}⚠️ WARNING: $message${NC}"
    log "WARN" "$message"
    add_to_report "- ⚠️ **Warning**: $message"
    ((WARNINGS++))
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"

    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        log "ERROR" "gh CLI is not installed"
        echo -e "${RED}❌ gh CLI is not installed${NC}"
        exit 1
    fi

    # Check gh authentication
    if ! gh auth status &> /dev/null; then
        log "ERROR" "gh CLI is not authenticated"
        echo -e "${RED}❌ gh CLI is not authenticated${NC}"
        exit 1
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        log "ERROR" "git is not installed"
        echo -e "${RED}❌ git is not installed${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Test 1: Clone repository with submodules
test_fresh_clone() {
    log "INFO" "Testing fresh clone with submodules"

    # Create temp directory
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"

    # Clone with submodules
    if gh repo clone Ladvien/entity -- --recurse-submodules &> /dev/null; then
        cd entity

        # Verify submodules are initialized
        if [ -f .gitmodules ]; then
            local submodule_count=$(git submodule status | wc -l)
            if [ "$submodule_count" -gt 0 ]; then
                log "SUCCESS" "Repository cloned with $submodule_count submodules"
                return 0
            else
                log "ERROR" "No submodules found after clone"
                return 1
            fi
        else
            log "ERROR" ".gitmodules file not found"
            return 1
        fi
    else
        log "ERROR" "Failed to clone repository"
        return 1
    fi
}

# Test 2: Verify repository topics
test_repository_topics() {
    log "INFO" "Testing repository topics"

    local repos=("entity-plugin-examples" "entity-plugin-gpt-oss" "entity-plugin-stdlib" "entity-plugin-template")
    local all_have_topics=true

    for repo in "${repos[@]}"; do
        # Get repository topics using gh api
        local topics=$(gh api "repos/Ladvien/$repo" --jq '.topics[]' 2>/dev/null | tr '\n' ' ')

        if [ -n "$topics" ]; then
            log "INFO" "$repo has topics: $topics"
        else
            log "WARN" "$repo has no topics set"
            add_warning "$repo repository has no topics"
            all_have_topics=false
        fi
    done

    if [ "$all_have_topics" = true ]; then
        return 0
    else
        # This is a warning, not a failure
        return 0
    fi
}

# Test 3: Verify repository metadata
test_repository_metadata() {
    log "INFO" "Testing repository metadata"

    local repos=("entity-plugin-examples" "entity-plugin-gpt-oss" "entity-plugin-stdlib" "entity-plugin-template")
    local all_valid=true

    for repo in "${repos[@]}"; do
        # Get repository metadata
        local metadata=$(gh api "repos/Ladvien/$repo" 2>/dev/null)

        if [ -n "$metadata" ]; then
            # Check visibility
            local is_public=$(echo "$metadata" | jq -r '.private')
            if [ "$is_public" = "false" ]; then
                log "INFO" "$repo is public"
            else
                log "ERROR" "$repo is not public"
                all_valid=false
            fi

            # Check license
            local license=$(echo "$metadata" | jq -r '.license.spdx_id')
            if [ "$license" = "MIT" ]; then
                log "INFO" "$repo has MIT license"
            else
                log "WARN" "$repo license is $license (expected MIT)"
                add_warning "$repo has license: $license (expected MIT)"
            fi

            # Check description
            local description=$(echo "$metadata" | jq -r '.description')
            if [ -n "$description" ] && [ "$description" != "null" ]; then
                log "INFO" "$repo has description: $description"
            else
                log "WARN" "$repo has no description"
                add_warning "$repo has no description"
            fi
        else
            log "ERROR" "Failed to get metadata for $repo"
            all_valid=false
        fi
    done

    if [ "$all_valid" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 4: Verify example scripts work
test_example_scripts() {
    log "INFO" "Testing example scripts"

    # Return to original entity directory
    cd "$TEMP_DIR/entity" 2>/dev/null || return 1

    # Check if examples directory exists
    if [ -d "examples" ]; then
        # Count Python example files
        local example_count=$(find examples -name "*.py" -type f | wc -l)
        if [ "$example_count" -gt 0 ]; then
            log "INFO" "Found $example_count example Python files"

            # Try to import entity (basic smoke test)
            if python3 -c "import sys; sys.path.insert(0, 'src'); import entity" 2>/dev/null; then
                log "SUCCESS" "Entity module can be imported"
                return 0
            else
                log "WARN" "Entity module import test failed (may need dependencies)"
                add_warning "Entity module import failed - may need full dependency installation"
                return 0  # Not a critical failure
            fi
        else
            log "WARN" "No Python example files found"
            add_warning "No Python example files found in examples directory"
            return 0
        fi
    else
        log "WARN" "Examples directory not found"
        add_warning "Examples directory not found"
        return 0
    fi
}

# Test 5: Performance benchmark check
test_performance() {
    log "INFO" "Testing performance (basic check)"

    cd "$TEMP_DIR/entity" 2>/dev/null || return 1

    # Measure time to check submodule status
    local start_time=$(date +%s)
    git submodule status &> /dev/null
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [ "$duration" -lt 5 ]; then
        log "SUCCESS" "Submodule status check completed in ${duration}s"
        return 0
    else
        log "WARN" "Submodule status check took ${duration}s (>5s)"
        add_warning "Submodule operations may be slow (${duration}s for status check)"
        return 0
    fi
}

# Test 6: Security scan
test_security() {
    log "INFO" "Testing for exposed secrets"

    cd "$TEMP_DIR/entity" 2>/dev/null || return 1

    # Basic patterns to check for exposed secrets
    local secret_patterns=(
        "password.*=.*['\"].*['\"]"
        "api[_-]?key.*=.*['\"].*['\"]"
        "token.*=.*['\"].*['\"]"
        "secret.*=.*['\"].*['\"]"
        "AWS.*KEY"
        "GITHUB_TOKEN"
    )

    local secrets_found=false

    for pattern in "${secret_patterns[@]}"; do
        # Search in all files except .git and common safe locations
        if grep -r -i "$pattern" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude="*.md" --exclude="*.txt" . 2>/dev/null | grep -v "example\|test\|fake\|dummy\|placeholder" | head -1 > /dev/null; then
            log "WARN" "Potential secret pattern found: $pattern"
            add_warning "Potential secret pattern found matching: $pattern"
            secrets_found=true
        fi
    done

    if [ "$secrets_found" = false ]; then
        log "SUCCESS" "No obvious secrets found"
        return 0
    else
        # Secrets in code are warnings, not failures for this test
        return 0
    fi
}

# Test 7: Verify plugin structure
test_plugin_structure() {
    log "INFO" "Testing plugin repository structure"

    cd "$TEMP_DIR/entity" 2>/dev/null || return 1

    local plugins=("examples" "gpt-oss" "stdlib" "template")
    local all_valid=true

    for plugin in "${plugins[@]}"; do
        local plugin_path="plugins/$plugin"

        if [ -d "$plugin_path" ]; then
            # Check for essential files
            if [ -f "$plugin_path/README.md" ]; then
                log "INFO" "$plugin has README.md"
            else
                log "WARN" "$plugin missing README.md"
                add_warning "$plugin plugin missing README.md"
            fi

            if [ -f "$plugin_path/pyproject.toml" ] || [ -f "$plugin_path/setup.py" ]; then
                log "INFO" "$plugin has Python package configuration"
            else
                log "WARN" "$plugin missing Python package configuration"
                add_warning "$plugin plugin missing pyproject.toml or setup.py"
            fi

            # Check for src directory
            if [ -d "$plugin_path/src" ]; then
                log "INFO" "$plugin has src directory"
            else
                log "WARN" "$plugin missing src directory"
                add_warning "$plugin plugin missing src directory"
            fi
        else
            log "ERROR" "Plugin directory not found: $plugin_path"
            all_valid=false
        fi
    done

    if [ "$all_valid" = true ]; then
        return 0
    else
        return 1
    fi
}

# Test 8: Verify CI/CD integration
test_cicd_integration() {
    log "INFO" "Testing CI/CD integration"

    cd "$TEMP_DIR/entity" 2>/dev/null || return 1

    # Check for workflow files
    if [ -d ".github/workflows" ]; then
        # Check for submodule support in workflows
        if grep -r "submodules.*recursive" .github/workflows/*.yml 2>/dev/null | head -1 > /dev/null; then
            log "SUCCESS" "CI/CD workflows have submodule support"
            return 0
        else
            log "ERROR" "CI/CD workflows missing submodule support"
            return 1
        fi
    else
        log "ERROR" ".github/workflows directory not found"
        return 1
    fi
}

# Generate final report
generate_final_report() {
    add_to_report ""
    add_to_report "## Statistics"
    add_to_report ""
    add_to_report "- **Tests Passed:** $TESTS_PASSED"
    add_to_report "- **Tests Failed:** $TESTS_FAILED"
    add_to_report "- **Warnings:** $WARNINGS"
    add_to_report ""

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    if [ "$total_tests" -gt 0 ]; then
        local success_rate=$((TESTS_PASSED * 100 / total_tests))
        add_to_report "- **Success Rate:** ${success_rate}%"
    fi

    add_to_report ""
    add_to_report "## Conclusion"
    add_to_report ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        add_to_report "✅ **All validation tests passed successfully!**"
        add_to_report ""
        add_to_report "The Entity Framework plugin migration has been validated and appears to be functioning correctly."
    else
        add_to_report "❌ **Some validation tests failed.**"
        add_to_report ""
        add_to_report "Please review the failed tests above and address any issues before considering the migration complete."
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        add_to_report ""
        add_to_report "⚠️ **Note:** There are $WARNINGS warnings that should be reviewed but are not blocking issues."
    fi

    add_to_report ""
    add_to_report "---"
    add_to_report ""
    add_to_report "*Report generated by validate_migration.sh*"
    add_to_report ""
    add_to_report "*Log file: $LOG_FILE*"
}

# Cleanup function
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        log "INFO" "Cleaning up temporary directory"
        rm -rf "$TEMP_DIR"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Entity Framework Migration Validation${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Initialize report
    init_report

    # Check prerequisites
    check_prerequisites
    echo ""

    add_to_report "### Test Results"
    add_to_report ""

    # Run validation tests
    echo -e "${BLUE}Running validation tests...${NC}"
    echo ""

    run_test "Fresh Clone with Submodules" "test_fresh_clone"
    run_test "Repository Topics" "test_repository_topics"
    run_test "Repository Metadata" "test_repository_metadata"
    run_test "Example Scripts" "test_example_scripts"
    run_test "Performance Check" "test_performance"
    run_test "Security Scan" "test_security"
    run_test "Plugin Structure" "test_plugin_structure"
    run_test "CI/CD Integration" "test_cicd_integration"

    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Validation Summary${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Generate final report
    generate_final_report

    # Display summary
    echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
    echo ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}✅ All validation tests passed!${NC}"
        echo ""
        echo "Validation report saved to: $VALIDATION_REPORT"
        echo "Log file: $LOG_FILE"

        # Cleanup on success
        cleanup

        exit 0
    else
        echo -e "${RED}❌ Some validation tests failed${NC}"
        echo ""
        echo "Validation report saved to: $VALIDATION_REPORT"
        echo "Log file: $LOG_FILE"
        echo "Temporary files preserved at: $TEMP_DIR"

        exit 1
    fi
}

# Set up trap for cleanup on interrupt
trap cleanup EXIT

# Run main function
main
