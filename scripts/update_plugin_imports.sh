#!/bin/bash

# Entity Framework Plugin Import Path Update Script
# Story: ENTITY-105 - Update Plugin Import Paths
# This script updates all import statements to reference new submodule locations

set -euo pipefail

# Configuration
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/plugin_import_update_${TIMESTAMP}.log"
DRY_RUN=false
BACKUP_DIR="backups/import_update_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Import mapping
declare -a OLD_PATTERNS=(
    "from entity.plugins.examples"
    "import entity.plugins.examples"
    "from entity.plugins.gpt_oss"
    "import entity.plugins.gpt_oss"
    "from entity.plugins.stdlib"
    "import entity.plugins.stdlib"
    "from entity.plugins.template"
    "import entity.plugins.template"
)

declare -a NEW_PATTERNS=(
    "from entity_plugin_examples"
    "import entity_plugin_examples"
    "from entity_plugin_gpt_oss"
    "import entity_plugin_gpt_oss"
    "from entity_plugin_stdlib"
    "import entity_plugin_stdlib"
    "from entity_plugin_template"
    "import entity_plugin_template"
)

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

# Function to find files with old import patterns
find_files_with_old_imports() {
    log "INFO" "Searching for files with old import patterns"

    local files_found=()

    for pattern in "${OLD_PATTERNS[@]}"; do
        log "INFO" "Searching for pattern: $pattern"

        # Find Python files with the pattern (excluding backups and .git)
        while IFS= read -r file; do
            if [ ${#files_found[@]} -eq 0 ] || [[ ! " ${files_found[@]} " =~ " ${file} " ]]; then
                files_found+=("$file")
            fi
        done < <(grep -r "$pattern" --include="*.py" --exclude-dir=".git" --exclude-dir="backups" --exclude-dir="__pycache__" --exclude-dir="plugins" . 2>/dev/null | cut -d: -f1 | sort -u)
    done

    if [ ${#files_found[@]} -gt 0 ]; then
        echo "${files_found[@]}"
    fi
}

# Function to backup files before modification
backup_files() {
    local files=("$@")

    if [ ${#files[@]} -eq 0 ]; then
        log "INFO" "No files to backup"
        return 0
    fi

    log "INFO" "Creating backup directory: $BACKUP_DIR"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would create backup directory: $BACKUP_DIR"
        echo -e "${BLUE}🔍 [DRY-RUN] Would backup ${#files[@]} files${NC}"
        return 0
    fi

    mkdir -p "$BACKUP_DIR"

    for file in "${files[@]}"; do
        local backup_path="$BACKUP_DIR/$file"
        local backup_dir=$(dirname "$backup_path")

        mkdir -p "$backup_dir"

        if cp "$file" "$backup_path"; then
            log "SUCCESS" "Backed up: $file"
        else
            log "ERROR" "Failed to backup: $file"
            return 1
        fi
    done

    echo -e "${GREEN}✅ Backed up ${#files[@]} files${NC}"
    return 0
}

# Function to update imports in a single file
update_imports_in_file() {
    local file=$1
    local changes_made=false

    log "INFO" "Processing file: $file"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would update imports in: $file"

        # Show what would be changed
        for i in "${!OLD_PATTERNS[@]}"; do
            if grep -q "${OLD_PATTERNS[$i]}" "$file" 2>/dev/null; then
                echo -e "${BLUE}   Would replace: ${OLD_PATTERNS[$i]}${NC}"
                echo -e "${BLUE}           with: ${NEW_PATTERNS[$i]}${NC}"
                changes_made=true
            fi
        done

        if [ "$changes_made" = true ]; then
            echo -e "${BLUE}🔍 [DRY-RUN] Would update: $file${NC}"
        fi

        return 0
    fi

    # Create temporary file
    local temp_file="${file}.tmp"
    cp "$file" "$temp_file"

    # Replace all old patterns with new ones
    for i in "${!OLD_PATTERNS[@]}"; do
        if grep -q "${OLD_PATTERNS[$i]}" "$temp_file" 2>/dev/null; then
            sed -i.bak "s/${OLD_PATTERNS[$i]}/${NEW_PATTERNS[$i]}/g" "$temp_file"
            changes_made=true
            log "SUCCESS" "Replaced '${OLD_PATTERNS[$i]}' with '${NEW_PATTERNS[$i]}'"
        fi
    done

    if [ "$changes_made" = true ]; then
        mv "$temp_file" "$file"
        rm -f "${temp_file}.bak"
        log "SUCCESS" "Updated imports in: $file"
        echo -e "${GREEN}✅ Updated: $file${NC}"
    else
        rm -f "$temp_file" "${temp_file}.bak"
        log "INFO" "No changes needed in: $file"
    fi

    return 0
}

# Function to update plugin loader configuration
update_plugin_loader() {
    log "INFO" "Checking plugin loader configuration"

    # Look for plugin loader files
    local loader_files=(
        "src/entity/plugins/__init__.py"
        "src/entity/core/agent.py"
        "src/entity/plugins/base.py"
    )

    for file in "${loader_files[@]}"; do
        if [ -f "$file" ]; then
            log "INFO" "Checking plugin loader in: $file"

            if [ "$DRY_RUN" = true ]; then
                log "INFO" "[DRY-RUN] Would check plugin loader in: $file"
                continue
            fi

            # Check if file contains plugin discovery logic
            if grep -q "plugin" "$file" 2>/dev/null; then
                log "INFO" "Found plugin references in: $file"
                # Note: Actual plugin loader update logic would go here
                # For now, we'll just log that it needs review
                log "WARN" "Manual review recommended for plugin loader: $file"
            fi
        fi
    done
}

# Function to verify no old imports remain
verify_no_old_imports() {
    log "INFO" "Verifying no old import patterns remain"

    local found_old=false

    for pattern in "${OLD_PATTERNS[@]}"; do
        # Exclude backups directory and plugins directory
        local occurrences=$(grep -r "$pattern" --include="*.py" --exclude-dir=".git" --exclude-dir="backups" --exclude-dir="__pycache__" --exclude-dir="plugins" . 2>/dev/null | wc -l || echo "0")

        if [ "$occurrences" -gt 0 ]; then
            log "WARN" "Found $occurrences occurrences of old pattern: $pattern"
            found_old=true

            # Show where they are (first 5)
            echo -e "${YELLOW}⚠️ Old pattern still exists: $pattern${NC}"
            grep -r "$pattern" --include="*.py" --exclude-dir=".git" --exclude-dir="backups" --exclude-dir="__pycache__" --exclude-dir="plugins" . 2>/dev/null | head -5
        fi
    done

    if [ "$found_old" = false ]; then
        log "SUCCESS" "No old import patterns found"
        echo -e "${GREEN}✅ All imports updated successfully${NC}"
        return 0
    else
        log "WARN" "Some old patterns still exist"
        echo -e "${YELLOW}⚠️ Some old patterns may need manual review${NC}"
        return 1
    fi
}

# Function to test imports
test_imports() {
    log "INFO" "Testing updated imports"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would test imports"
        echo -e "${BLUE}🔍 [DRY-RUN] Would test imports${NC}"
        return 0
    fi

    # Create a test script to verify imports work
    local test_script="test_imports_${TIMESTAMP}.py"

    cat > "$test_script" << 'EOF'
#!/usr/bin/env python3
"""Test script to verify plugin imports work correctly."""

import sys
import importlib

# Add plugins to path
sys.path.insert(0, 'plugins/examples/src')
sys.path.insert(0, 'plugins/gpt-oss/src')
sys.path.insert(0, 'plugins/stdlib/src')
sys.path.insert(0, 'plugins/template/src')

def test_imports():
    """Test that new import paths work."""
    success = True

    # Test plugin package imports
    test_packages = [
        'entity_plugin_examples',
        'entity_plugin_gpt_oss',
        'entity_plugin_stdlib',
        'entity_plugin_template'
    ]

    for package in test_packages:
        try:
            importlib.import_module(package)
            print(f"✅ Successfully imported: {package}")
        except ImportError as e:
            print(f"❌ Failed to import {package}: {e}")
            success = False

    return success

if __name__ == "__main__":
    if test_imports():
        print("\n✅ All imports successful!")
        sys.exit(0)
    else:
        print("\n❌ Some imports failed!")
        sys.exit(1)
EOF

    # Run the test script
    if python3 "$test_script"; then
        log "SUCCESS" "Import test passed"
        echo -e "${GREEN}✅ Import test passed${NC}"
        rm -f "$test_script"
        return 0
    else
        log "ERROR" "Import test failed"
        echo -e "${RED}❌ Import test failed${NC}"
        rm -f "$test_script"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Entity Framework Plugin Import Update${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY-RUN mode - no changes will be made${NC}"
        echo ""
    fi

    log "INFO" "Starting plugin import update process"
    log "INFO" "Dry run mode: ${DRY_RUN}"

    # Step 1: Find files with old imports
    echo -e "${BLUE}Step 1: Finding files with old import patterns${NC}"

    # Get files as a string, then convert to array
    local files_string="$(find_files_with_old_imports)"
    local files_to_update=()

    if [ -n "$files_string" ]; then
        IFS=' ' read -r -a files_to_update <<< "$files_string"
    fi

    if [ ${#files_to_update[@]} -eq 0 ]; then
        log "INFO" "No files found with old import patterns"
        echo -e "${GREEN}✅ No import updates needed${NC}"
        echo ""

        # Still run verification
        echo -e "${BLUE}Verifying imports${NC}"
        verify_no_old_imports

        echo ""
        echo -e "${GREEN}Plugin import update completed - no changes needed${NC}"
        log "INFO" "Plugin import update process completed - no changes needed"
        return 0
    fi

    echo -e "${YELLOW}Found ${#files_to_update[@]} files with old import patterns${NC}"
    for file in "${files_to_update[@]}"; do
        echo "  - $file"
    done
    echo ""

    # Step 2: Backup files
    echo -e "${BLUE}Step 2: Creating backups${NC}"
    if ! backup_files "${files_to_update[@]}"; then
        log "ERROR" "Backup failed - aborting"
        echo -e "${RED}❌ Backup failed - aborting${NC}"
        exit 1
    fi
    echo ""

    # Step 3: Update imports
    echo -e "${BLUE}Step 3: Updating import statements${NC}"
    local update_failed=false

    for file in "${files_to_update[@]}"; do
        if ! update_imports_in_file "$file"; then
            update_failed=true
        fi
    done

    if [ "$update_failed" = true ]; then
        log "ERROR" "Some files could not be updated"
        echo -e "${RED}❌ Some updates failed${NC}"
    fi
    echo ""

    # Step 4: Update plugin loader
    echo -e "${BLUE}Step 4: Checking plugin loader${NC}"
    update_plugin_loader
    echo ""

    # Step 5: Verify no old imports remain
    echo -e "${BLUE}Step 5: Verifying import updates${NC}"
    verify_no_old_imports
    echo ""

    # Step 6: Test imports
    echo -e "${BLUE}Step 6: Testing imports${NC}"
    test_imports
    echo ""

    # Summary
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}Dry run completed.${NC}"
        echo "Would update: ${#files_to_update[@]} files"
    else
        echo -e "${GREEN}Plugin import update completed successfully${NC}"
        echo "Updated: ${#files_to_update[@]} files"

        if [ -d "$BACKUP_DIR" ]; then
            echo "Backups saved in: $BACKUP_DIR"
        fi
    fi

    echo ""
    echo "Log file: $LOG_FILE"

    log "INFO" "Plugin import update process completed"
}

# Run main function
main
