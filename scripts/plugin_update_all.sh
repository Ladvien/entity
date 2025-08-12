#!/bin/bash

# Entity Framework Plugin Management - Update All Plugins
# Story: ENTITY-109 - Create Management Tooling
# This script updates all plugin submodules using gh CLI

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLUGINS_DIR="$PROJECT_ROOT/plugins"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Plugin repositories
PLUGIN_REPOS=(
    "entity-plugin-examples"
    "entity-plugin-gpt-oss"
    "entity-plugin-stdlib"
    "entity-plugin-template"
)

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check gh CLI
    if ! command -v gh &> /dev/null; then
        error "gh CLI is not installed. Please install it first."
        echo "Visit: https://cli.github.com/manual/installation"
        exit 1
    fi

    # Check gh authentication
    if ! gh auth status &> /dev/null; then
        error "gh CLI is not authenticated."
        echo "Run: gh auth login"
        exit 1
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        error "git is not installed."
        exit 1
    fi

    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error "Not in a git repository."
        exit 1
    fi

    success "Prerequisites met"
}

# Update a single plugin submodule
update_plugin() {
    local plugin_name=$1
    local plugin_dir=""

    # Map repository name to plugin directory
    case "$plugin_name" in
        "entity-plugin-examples")
            plugin_dir="examples"
            ;;
        "entity-plugin-gpt-oss")
            plugin_dir="gpt-oss"
            ;;
        "entity-plugin-stdlib")
            plugin_dir="stdlib"
            ;;
        "entity-plugin-template")
            plugin_dir="template"
            ;;
        *)
            error "Unknown plugin: $plugin_name"
            return 1
            ;;
    esac

    local full_path="$PLUGINS_DIR/$plugin_dir"

    log "Updating plugin: $plugin_name"

    # Check if submodule exists
    if [ ! -d "$full_path/.git" ]; then
        warning "Plugin $plugin_name is not initialized as a submodule"
        log "Initializing submodule..."
        git submodule update --init "$full_path"
    fi

    # Save current directory
    local current_dir=$(pwd)

    # Navigate to plugin directory
    cd "$full_path"

    # Fetch latest changes
    log "Fetching latest changes for $plugin_name..."
    git fetch origin

    # Get current branch
    local current_branch=$(git branch --show-current)

    # Check for updates
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null)

    if [ "$local_commit" = "$remote_commit" ]; then
        success "$plugin_name is already up to date"
    else
        # Check for local changes
        if ! git diff --quiet || ! git diff --cached --quiet; then
            warning "$plugin_name has local changes. Skipping update."
            git status --short
        else
            # Update to latest
            log "Updating $plugin_name to latest commit..."
            git pull origin main 2>/dev/null || git pull origin master 2>/dev/null

            # Verify update
            local new_commit=$(git rev-parse HEAD)
            success "$plugin_name updated from ${local_commit:0:7} to ${new_commit:0:7}"
        fi
    fi

    # Return to original directory
    cd "$current_dir"

    return 0
}

# Update all plugins
update_all_plugins() {
    log "Starting update of all plugin submodules..."

    local updated_count=0
    local failed_count=0
    local skipped_count=0

    for repo in "${PLUGIN_REPOS[@]}"; do
        echo ""
        if update_plugin "$repo"; then
            ((updated_count++))
        else
            ((failed_count++))
        fi
    done

    echo ""
    log "Update Summary:"
    success "Successfully processed: $updated_count plugins"

    if [ $failed_count -gt 0 ]; then
        error "Failed to update: $failed_count plugins"
    fi

    # Check if submodules have updates to commit
    if ! git diff --quiet; then
        echo ""
        warning "Submodule references have been updated."
        log "To commit these updates, run:"
        echo "  git add ."
        echo "  git commit -m 'chore: Update plugin submodules to latest versions'"
    fi
}

# Main function
main() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}Entity Plugin Update Tool${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Change to project root
    cd "$PROJECT_ROOT"

    # Update all plugins
    update_all_plugins

    echo ""
    success "Plugin update process completed!"
}

# Handle script arguments
if [ $# -gt 0 ]; then
    case "$1" in
        -h|--help)
            echo "Usage: $0"
            echo ""
            echo "Updates all Entity Framework plugin submodules to their latest versions."
            echo ""
            echo "This script will:"
            echo "  1. Check each plugin submodule for updates"
            echo "  2. Pull the latest changes if no local modifications exist"
            echo "  3. Report the update status for each plugin"
            echo ""
            echo "Prerequisites:"
            echo "  - gh CLI installed and authenticated"
            echo "  - git installed"
            echo "  - Run from within the Entity Framework repository"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            echo "Run '$0 --help' for usage information."
            exit 1
            ;;
    esac
fi

# Run main function
main
