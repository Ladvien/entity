#!/bin/bash

# Entity Framework Plugin Submodule Addition Script
# Story: ENTITY-104 - Add Plugins as Git Submodules
# This script adds plugin repositories as Git submodules under plugins/ directory

set -euo pipefail

# Configuration
ORGANIZATION="Ladvien"
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/plugin_submodules_${TIMESTAMP}.log"
DRY_RUN=false
PLUGINS_DIR="plugins"

# Plugin repositories to add as submodules
PLUGIN_REPOS=(
    "entity-plugin-examples"
    "entity-plugin-gpt-oss"
    "entity-plugin-stdlib"
    "entity-plugin-template"
)

# Function to get submodule path for a repository
get_submodule_path() {
    local repo_name=$1
    case "$repo_name" in
        "entity-plugin-examples")
            echo "plugins/examples"
            ;;
        "entity-plugin-gpt-oss")
            echo "plugins/gpt-oss"
            ;;
        "entity-plugin-stdlib")
            echo "plugins/stdlib"
            ;;
        "entity-plugin-template")
            echo "plugins/template"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Original directories to remove after submodule addition
ORIGINAL_DIRECTORIES=(
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

# Function to get repository URL using gh CLI
get_repo_url() {
    local repo_name=$1

    log "INFO" "Getting URL for repository ${ORGANIZATION}/${repo_name}" >&2

    local repo_url=$(gh repo view "${ORGANIZATION}/${repo_name}" --json url --jq '.url' 2>/dev/null)

    if [ -n "$repo_url" ]; then
        log "SUCCESS" "Repository URL: $repo_url" >&2
        echo "$repo_url"
        return 0
    else
        log "ERROR" "Failed to get URL for repository ${ORGANIZATION}/${repo_name}" >&2
        return 1
    fi
}

# Function to create plugins directory
create_plugins_directory() {
    log "INFO" "Creating plugins directory: $PLUGINS_DIR"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would create directory: $PLUGINS_DIR"
        echo -e "${BLUE}🔍 [DRY-RUN] Would create: $PLUGINS_DIR${NC}"
        return 0
    fi

    if [ ! -d "$PLUGINS_DIR" ]; then
        if mkdir -p "$PLUGINS_DIR"; then
            log "SUCCESS" "Created plugins directory: $PLUGINS_DIR"
            echo -e "${GREEN}✅ Created: $PLUGINS_DIR${NC}"
            return 0
        else
            log "ERROR" "Failed to create plugins directory: $PLUGINS_DIR"
            echo -e "${RED}❌ Failed to create: $PLUGINS_DIR${NC}"
            return 1
        fi
    else
        log "INFO" "Plugins directory already exists: $PLUGINS_DIR"
        echo -e "${YELLOW}⚠️ Already exists: $PLUGINS_DIR${NC}"
        return 0
    fi
}

# Function to add repository as submodule
add_submodule() {
    local repo_name=$1
    local submodule_path=$(get_submodule_path "$repo_name")

    log "INFO" "Adding submodule: $repo_name -> $submodule_path"

    # Get repository URL
    local repo_url=$(get_repo_url "$repo_name")
    if [ $? -ne 0 ]; then
        log "ERROR" "Failed to get repository URL for $repo_name"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would add submodule: git submodule add $repo_url $submodule_path"
        echo -e "${BLUE}🔍 [DRY-RUN] Would add submodule: $repo_name -> $submodule_path${NC}"
        return 0
    fi

    # Check if submodule path already exists
    if [ -e "$submodule_path" ]; then
        log "WARN" "Path already exists: $submodule_path"

        # Check if it's already a submodule
        if git submodule status "$submodule_path" &>/dev/null; then
            log "INFO" "Path is already a submodule: $submodule_path"
            echo -e "${YELLOW}⚠️ Already submodule: $submodule_path${NC}"
            return 0
        else
            log "ERROR" "Path exists but is not a submodule: $submodule_path"
            echo -e "${RED}❌ Path conflict: $submodule_path${NC}"
            return 1
        fi
    fi

    # Add submodule
    if git submodule add "$repo_url" "$submodule_path"; then
        log "SUCCESS" "Added submodule: $submodule_path"
        echo -e "${GREEN}✅ Added submodule: $submodule_path${NC}"
        return 0
    else
        log "ERROR" "Failed to add submodule: $submodule_path"
        echo -e "${RED}❌ Failed to add submodule: $submodule_path${NC}"
        return 1
    fi
}

# Function to initialize and update submodules
initialize_submodules() {
    log "INFO" "Initializing and updating submodules"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would initialize and update submodules"
        echo -e "${BLUE}🔍 [DRY-RUN] Would initialize and update submodules${NC}"
        return 0
    fi

    if git submodule init && git submodule update; then
        log "SUCCESS" "Submodules initialized and updated"
        echo -e "${GREEN}✅ Submodules initialized and updated${NC}"
        return 0
    else
        log "ERROR" "Failed to initialize and update submodules"
        echo -e "${RED}❌ Failed to initialize submodules${NC}"
        return 1
    fi
}

# Function to remove original directories
remove_original_directories() {
    log "INFO" "Removing original plugin directories"

    local removal_failed=false

    for dir_name in "${ORIGINAL_DIRECTORIES[@]}"; do
        if [ ! -d "$dir_name" ]; then
            log "INFO" "Directory does not exist: $dir_name"
            continue
        fi

        log "INFO" "Removing original directory: $dir_name"

        if [ "$DRY_RUN" = true ]; then
            log "INFO" "[DRY-RUN] Would remove directory: $dir_name"
            echo -e "${BLUE}🔍 [DRY-RUN] Would remove: $dir_name${NC}"
            continue
        fi

        if rm -rf "$dir_name"; then
            log "SUCCESS" "Removed directory: $dir_name"
            echo -e "${GREEN}✅ Removed: $dir_name${NC}"
        else
            log "ERROR" "Failed to remove directory: $dir_name"
            echo -e "${RED}❌ Failed to remove: $dir_name${NC}"
            removal_failed=true
        fi
    done

    if [ "$removal_failed" = true ]; then
        return 1
    fi

    return 0
}

# Function to verify submodules are properly configured
verify_submodules() {
    log "INFO" "Verifying submodule configuration"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would verify submodules"
        echo -e "${BLUE}🔍 [DRY-RUN] Would verify submodules${NC}"
        return 0
    fi

    # Check git submodule status
    local submodule_count=$(git submodule status | wc -l | tr -d ' ')
    log "INFO" "Found $submodule_count configured submodules"

    if [ "$submodule_count" -ge 4 ]; then
        log "SUCCESS" "All submodules appear to be configured"
        echo -e "${GREEN}✅ All submodules configured${NC}"

        # Display submodule status
        echo ""
        echo -e "${BLUE}Submodule Status:${NC}"
        git submodule status
        echo ""

        return 0
    else
        log "ERROR" "Expected 4 submodules, found $submodule_count"
        echo -e "${RED}❌ Submodule count mismatch${NC}"
        return 1
    fi
}

# Function to check if .gitmodules file is created
verify_gitmodules_file() {
    log "INFO" "Verifying .gitmodules file"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would verify .gitmodules file"
        echo -e "${BLUE}🔍 [DRY-RUN] Would verify .gitmodules file${NC}"
        return 0
    fi

    if [ -f ".gitmodules" ]; then
        local entry_count=$(grep -c "^\[submodule" .gitmodules || echo "0")
        log "SUCCESS" ".gitmodules file exists with $entry_count entries"
        echo -e "${GREEN}✅ .gitmodules file exists${NC}"

        # Display .gitmodules content
        echo ""
        echo -e "${BLUE}.gitmodules content:${NC}"
        cat .gitmodules
        echo ""

        return 0
    else
        log "ERROR" ".gitmodules file does not exist"
        echo -e "${RED}❌ .gitmodules file missing${NC}"
        return 1
    fi
}

# Function to commit changes
commit_changes() {
    log "INFO" "Committing submodule changes"

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would commit changes to git"
        echo -e "${BLUE}🔍 [DRY-RUN] Would commit changes${NC}"
        return 0
    fi

    # Check if there are changes to commit
    if git diff --cached --quiet && git diff --quiet; then
        log "INFO" "No changes to commit"
        return 0
    fi

    # Add .gitmodules and plugins directory
    git add .gitmodules plugins/

    # Commit changes
    if git commit -m "feat: Add plugins as Git submodules

- Add entity-plugin-examples as plugins/examples
- Add entity-plugin-gpt-oss as plugins/gpt-oss
- Add entity-plugin-stdlib as plugins/stdlib
- Add entity-plugin-template as plugins/template
- Create .gitmodules configuration
- Remove original plugin directories

Story: ENTITY-104"; then
        log "SUCCESS" "Changes committed successfully"
        echo -e "${GREEN}✅ Changes committed${NC}"
        return 0
    else
        log "ERROR" "Failed to commit changes"
        echo -e "${RED}❌ Failed to commit changes${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Entity Framework Plugin Submodule Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY-RUN mode - no changes will be made${NC}"
        echo ""
    fi

    log "INFO" "Starting plugin submodule addition process"
    log "INFO" "Organization: ${ORGANIZATION}"
    log "INFO" "Dry run mode: ${DRY_RUN}"
    log "INFO" "Plugins directory: ${PLUGINS_DIR}"

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

    # Check if we're in a git repository
    if ! git rev-parse --git-dir &>/dev/null; then
        log "ERROR" "Not in a git repository"
        echo -e "${RED}Error: Not in a git repository${NC}"
        exit 1
    fi

    log "INFO" "Git repository verified"
    echo -e "${GREEN}✓ Git repository verified${NC}"
    echo ""

    # Step 1: Create plugins directory
    echo -e "${BLUE}Step 1: Creating plugins directory${NC}"
    if ! create_plugins_directory; then
        exit 1
    fi
    echo ""

    # Step 2: Add each plugin as a submodule
    echo -e "${BLUE}Step 2: Adding plugins as submodules${NC}"
    local submodule_failed=false

    for repo_name in "${PLUGIN_REPOS[@]}"; do
        if ! add_submodule "$repo_name"; then
            submodule_failed=true
        fi
    done

    if [ "$submodule_failed" = true ]; then
        log "ERROR" "Failed to add some submodules"
        echo -e "${RED}❌ Submodule addition failed${NC}"
        exit 1
    fi

    echo ""

    # Step 3: Initialize and update submodules
    echo -e "${BLUE}Step 3: Initializing submodules${NC}"
    if ! initialize_submodules; then
        exit 1
    fi
    echo ""

    # Step 4: Remove original directories
    echo -e "${BLUE}Step 4: Removing original directories${NC}"
    if ! remove_original_directories; then
        log "WARN" "Some original directories could not be removed"
    fi
    echo ""

    # Step 5: Verify submodules
    echo -e "${BLUE}Step 5: Verifying submodules${NC}"
    if ! verify_submodules; then
        exit 1
    fi

    # Step 6: Verify .gitmodules file
    echo -e "${BLUE}Step 6: Verifying .gitmodules file${NC}"
    if ! verify_gitmodules_file; then
        exit 1
    fi

    # Step 7: Commit changes
    echo -e "${BLUE}Step 7: Committing changes${NC}"
    if ! commit_changes; then
        log "WARN" "Failed to commit changes - manual commit may be required"
    fi
    echo ""

    # Summary
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}Dry run completed.${NC}"
        echo "Would add: ${#PLUGIN_REPOS[@]} submodules"
        echo "Would remove: ${#ORIGINAL_DIRECTORIES[@]} original directories"
    else
        echo -e "${GREEN}Plugin submodule setup completed successfully${NC}"
        echo "Added: ${#PLUGIN_REPOS[@]} submodules"
        echo "Removed: ${#ORIGINAL_DIRECTORIES[@]} original directories"
        echo "Created .gitmodules configuration file"
    fi

    echo ""
    echo "Log file: $LOG_FILE"

    log "INFO" "Plugin submodule addition process completed"
}

# Run main function
main
