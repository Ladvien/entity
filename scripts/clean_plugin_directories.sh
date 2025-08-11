#!/bin/bash

# Entity Framework Plugin Directory Cleanup Script
# Story: ENTITY-103 - Clean Plugin Directories from Main Repository
# This script removes plugin directories that will conflict with submodules

set -euo pipefail

# Configuration
ORGANIZATION="Ladvien"
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/plugin_cleanup_${TIMESTAMP}.log"
DRY_RUN=false
BACKUP_DIR="backups/plugin_cleanup_${TIMESTAMP}"

# Directories to remove
DIRECTORIES_TO_REMOVE=(
    "src/entity/plugins/examples"
    "src/entity/plugins/gpt_oss"
)

# Test directories to evaluate
TEST_DIRECTORIES_TO_EVALUATE=(
    "tests/plugins/gpt_oss"
)

# Directories to preserve
DIRECTORIES_TO_PRESERVE=(
    "src/entity/plugins/defaults"
)

# Plugin repositories to verify
PLUGIN_REPOS=(
    "entity-plugin-examples"
    "entity-plugin-gpt-oss"
    "entity-plugin-stdlib"
    "entity-plugin-template"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--help]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Perform a dry run without making changes"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

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

# Function to verify plugin repository has code
verify_plugin_repo() {
    local repo_name=$1

    log "INFO" "Verifying repository ${ORGANIZATION}/${repo_name} has code"

    # Check if repo exists and has content
    local file_count=$(gh api "repos/${ORGANIZATION}/${repo_name}/contents" --jq 'length' 2>/dev/null || echo "0")

    if [ "$file_count" -gt 2 ]; then
        log "SUCCESS" "Repository ${ORGANIZATION}/${repo_name} has $file_count files"
        return 0
    else
        log "ERROR" "Repository ${ORGANIZATION}/${repo_name} has insufficient files ($file_count)"
        return 1
    fi
}

# Function to create backup of directories
create_backup() {
    local dir_path=$1

    if [ ! -d "$dir_path" ]; then
        log "WARN" "Directory $dir_path does not exist, skipping backup"
        return 0
    fi

    log "INFO" "Creating backup of $dir_path"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would backup $dir_path to $BACKUP_DIR"
        echo -e "${BLUE}🔍 [DRY-RUN] Would backup: $dir_path${NC}"
        return 0
    fi

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Create backup with directory structure preserved
    local backup_path="$BACKUP_DIR/$dir_path"
    mkdir -p "$(dirname "$backup_path")"

    if cp -r "$dir_path" "$backup_path" 2>/dev/null; then
        log "SUCCESS" "Backup created: $backup_path"
        echo -e "${GREEN}✅ Backed up: $dir_path${NC}"
        return 0
    else
        log "ERROR" "Failed to create backup of $dir_path"
        echo -e "${RED}❌ Failed to backup: $dir_path${NC}"
        return 1
    fi
}

# Function to remove directory
remove_directory() {
    local dir_path=$1

    if [ ! -d "$dir_path" ]; then
        log "WARN" "Directory $dir_path does not exist, skipping removal"
        return 0
    fi

    log "INFO" "Removing directory $dir_path"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would remove $dir_path"
        echo -e "${BLUE}🔍 [DRY-RUN] Would remove: $dir_path${NC}"
        local file_count=$(find "$dir_path" -type f | wc -l)
        echo "   Contains $file_count files"
        return 0
    fi

    if rm -rf "$dir_path" 2>/dev/null; then
        log "SUCCESS" "Removed directory: $dir_path"
        echo -e "${GREEN}✅ Removed: $dir_path${NC}"
        return 0
    else
        log "ERROR" "Failed to remove directory: $dir_path"
        echo -e "${RED}❌ Failed to remove: $dir_path${NC}"
        return 1
    fi
}

# Function to check for broken imports
check_broken_imports() {
    log "INFO" "Checking for broken imports in Python files"

    # Look for imports that might reference removed directories
    local import_patterns=(
        "from entity.plugins.examples"
        "import entity.plugins.examples"
        "from entity.plugins.gpt_oss"
        "import entity.plugins.gpt_oss"
    )

    local found_imports=false

    for pattern in "${import_patterns[@]}"; do
        log "INFO" "Checking for pattern: $pattern"

        if grep -r "$pattern" src/ tests/ 2>/dev/null | grep -v "__pycache__" | grep -v ".pyc"; then
            log "WARN" "Found imports that may need updating: $pattern"
            found_imports=true
        fi
    done

    if [ "$found_imports" = false ]; then
        log "SUCCESS" "No problematic imports found"
        echo -e "${GREEN}✅ No broken imports detected${NC}"
        return 0
    else
        log "WARN" "Some imports may need attention after cleanup"
        echo -e "${YELLOW}⚠️ Some imports may need updating${NC}"
        return 1
    fi
}

# Function to evaluate test directories
evaluate_test_directory() {
    local test_dir=$1

    log "INFO" "Evaluating test directory: $test_dir"

    if [ ! -d "$test_dir" ]; then
        log "INFO" "Test directory $test_dir does not exist"
        return 0
    fi

    local test_file_count=$(find "$test_dir" -name "*.py" -type f | wc -l)
    log "INFO" "Found $test_file_count test files in $test_dir"

    if [ "$test_file_count" -gt 0 ]; then
        log "WARN" "Test directory $test_dir contains tests that may become obsolete"
        echo -e "${YELLOW}⚠️ Evaluate: $test_dir (contains $test_file_count test files)${NC}"

        # For gpt_oss tests, they are likely obsolete since the plugin was moved
        if [[ "$test_dir" == *"gpt_oss"* ]]; then
            log "INFO" "gpt_oss tests are likely obsolete - plugin moved to separate repo"

            # Create backup and remove
            if create_backup "$test_dir"; then
                remove_directory "$test_dir"
            fi
        fi
    fi
}

# Function to verify preserved directories
verify_preserved_directories() {
    log "INFO" "Verifying preserved directories exist"

    for dir_path in "${DIRECTORIES_TO_PRESERVE[@]}"; do
        if [ -d "$dir_path" ]; then
            log "SUCCESS" "Preserved directory exists: $dir_path"
            echo -e "${GREEN}✅ Preserved: $dir_path${NC}"
        else
            log "WARN" "Preserved directory missing: $dir_path"
            echo -e "${YELLOW}⚠️ Missing preserved directory: $dir_path${NC}"
        fi
    done
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Entity Framework Plugin Directory Cleanup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY-RUN mode - no changes will be made${NC}"
        echo ""
    fi

    log "INFO" "Starting plugin directory cleanup process"
    log "INFO" "Organization: ${ORGANIZATION}"
    log "INFO" "Dry run mode: ${DRY_RUN}"
    log "INFO" "Backup directory: ${BACKUP_DIR}"

    # Check if gh CLI is authenticated
    if ! gh auth status &>/dev/null; then
        log "ERROR" "gh CLI is not authenticated"
        echo -e "${RED}Error: gh CLI is not authenticated.${NC}"
        echo "Run: gh auth login"
        exit 1
    fi

    log "INFO" "gh CLI authentication verified"
    echo -e "${GREEN}✓ gh CLI authenticated${NC}"
    echo ""

    # Step 1: Verify all plugin repositories have code
    echo -e "${BLUE}Step 1: Verifying plugin repositories have code${NC}"
    local verification_failed=false

    for repo_name in "${PLUGIN_REPOS[@]}"; do
        if ! verify_plugin_repo "$repo_name"; then
            verification_failed=true
        fi
    done

    if [ "$verification_failed" = true ]; then
        log "ERROR" "Some plugin repositories lack sufficient code - aborting cleanup"
        echo -e "${RED}❌ Plugin repositories not ready - aborting${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All plugin repositories verified${NC}"
    echo ""

    # Step 2: Create backups of directories to be removed
    echo -e "${BLUE}Step 2: Creating backups of directories${NC}"
    local backup_failed=false

    for dir_path in "${DIRECTORIES_TO_REMOVE[@]}"; do
        if ! create_backup "$dir_path"; then
            backup_failed=true
        fi
    done

    # Also backup test directories
    for test_dir in "${TEST_DIRECTORIES_TO_EVALUATE[@]}"; do
        if [ -d "$test_dir" ]; then
            if ! create_backup "$test_dir"; then
                backup_failed=true
            fi
        fi
    done

    if [ "$backup_failed" = true ] && [ "$DRY_RUN" = false ]; then
        log "ERROR" "Backup creation failed - aborting cleanup"
        echo -e "${RED}❌ Backup failed - aborting${NC}"
        exit 1
    fi

    echo ""

    # Step 3: Remove plugin directories
    echo -e "${BLUE}Step 3: Removing plugin directories${NC}"
    local removal_failed=false

    for dir_path in "${DIRECTORIES_TO_REMOVE[@]}"; do
        if ! remove_directory "$dir_path"; then
            removal_failed=true
        fi
    done

    echo ""

    # Step 4: Evaluate test directories
    echo -e "${BLUE}Step 4: Evaluating test directories${NC}"

    for test_dir in "${TEST_DIRECTORIES_TO_EVALUATE[@]}"; do
        evaluate_test_directory "$test_dir"
    done

    echo ""

    # Step 5: Verify preserved directories
    echo -e "${BLUE}Step 5: Verifying preserved directories${NC}"
    verify_preserved_directories
    echo ""

    # Step 6: Check for broken imports
    echo -e "${BLUE}Step 6: Checking for broken imports${NC}"
    check_broken_imports
    echo ""

    # Summary
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}Dry run completed.${NC}"
        echo "Would remove: ${#DIRECTORIES_TO_REMOVE[@]} directories"
        echo "Would evaluate: ${#TEST_DIRECTORIES_TO_EVALUATE[@]} test directories"
    else
        if [ "$removal_failed" = true ]; then
            echo -e "${RED}Some directories could not be removed${NC}"
            exit 1
        else
            echo -e "${GREEN}Plugin directory cleanup completed successfully${NC}"
            echo "Removed: ${#DIRECTORIES_TO_REMOVE[@]} directories"
            echo "Evaluated: ${#TEST_DIRECTORIES_TO_EVALUATE[@]} test directories"
        fi
    fi

    echo ""
    echo "Log file: $LOG_FILE"
    if [ "$DRY_RUN" = false ]; then
        echo "Backup directory: $BACKUP_DIR"
    fi

    log "INFO" "Plugin directory cleanup process completed"
}

# Run main function
main
