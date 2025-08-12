#!/bin/bash

# Entity Framework Plugin Management - Check Plugin Versions
# Story: ENTITY-109 - Create Management Tooling
# This script checks plugin versions using gh release list

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLUGINS_DIR="$PROJECT_ROOT/plugins"
GITHUB_ORG="Ladvien"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

info() {
    echo -e "${CYAN}[INFO]${NC} $*"
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

    success "Prerequisites met"
}

# Get current commit for a plugin submodule
get_current_commit() {
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
    esac

    local full_path="$PLUGINS_DIR/$plugin_dir"

    if [ -d "$full_path/.git" ]; then
        cd "$full_path"
        git rev-parse --short HEAD
        cd - > /dev/null
    else
        echo "not-initialized"
    fi
}

# Check version for a single plugin
check_plugin_version() {
    local plugin_name=$1

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Plugin: ${CYAN}$plugin_name${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"

    # Get current commit
    local current_commit=$(get_current_commit "$plugin_name")
    info "Current commit: $current_commit"

    # Check if repository exists
    if ! gh repo view "$GITHUB_ORG/$plugin_name" &> /dev/null; then
        error "Repository $GITHUB_ORG/$plugin_name not found"
        return 1
    fi

    # Get latest commit from main/master branch
    local latest_commit=$(gh api "repos/$GITHUB_ORG/$plugin_name/commits/HEAD" --jq '.sha[0:7]' 2>/dev/null || echo "unknown")
    info "Latest commit:  $latest_commit"

    # Compare commits
    if [ "$current_commit" = "$latest_commit" ]; then
        success "Plugin is up to date"
    elif [ "$current_commit" = "not-initialized" ]; then
        warning "Plugin submodule not initialized"
    else
        warning "Plugin is behind latest commit"
    fi

    # Check for releases
    echo ""
    log "Checking releases..."

    local releases=$(gh release list --repo "$GITHUB_ORG/$plugin_name" --limit 5 2>/dev/null)

    if [ -z "$releases" ]; then
        info "No releases found for this plugin"
    else
        echo -e "${CYAN}Latest releases:${NC}"
        echo "$releases" | while IFS=$'\t' read -r title tag published status; do
            local release_date=$(echo "$published" | cut -d'T' -f1)
            local release_status=""

            if [ "$status" = "Pre-release" ]; then
                release_status="${YELLOW}[Pre-release]${NC}"
            elif [ "$status" = "Draft" ]; then
                release_status="${RED}[Draft]${NC}"
            else
                release_status="${GREEN}[Latest]${NC}"
            fi

            echo -e "  ${GREEN}$tag${NC} - $title ${release_status}"
            echo -e "    Published: $release_date"

            # Get release commit if available
            local release_commit=$(gh api "repos/$GITHUB_ORG/$plugin_name/releases/tags/$tag" --jq '.target_commitish[0:7]' 2>/dev/null || echo "")
            if [ -n "$release_commit" ]; then
                echo -e "    Commit: $release_commit"

                if [ "$current_commit" = "$release_commit" ]; then
                    success "    Currently on this release"
                fi
            fi
            echo ""
        done
    fi

    # Check for open PRs
    local pr_count=$(gh pr list --repo "$GITHUB_ORG/$plugin_name" --state open --json number --jq '. | length' 2>/dev/null || echo "0")
    if [ "$pr_count" -gt 0 ]; then
        info "Open pull requests: $pr_count"
    fi

    # Check for open issues
    local issue_count=$(gh issue list --repo "$GITHUB_ORG/$plugin_name" --state open --json number --jq '. | length' 2>/dev/null || echo "0")
    if [ "$issue_count" -gt 0 ]; then
        info "Open issues: $issue_count"
    fi

    return 0
}

# Generate summary report
generate_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Version Check Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"

    local update_needed=()
    local not_initialized=()
    local up_to_date=()

    for repo in "${PLUGIN_REPOS[@]}"; do
        local current=$(get_current_commit "$repo")
        local latest=$(gh api "repos/$GITHUB_ORG/$repo/commits/HEAD" --jq '.sha[0:7]' 2>/dev/null || echo "unknown")

        if [ "$current" = "not-initialized" ]; then
            not_initialized+=("$repo")
        elif [ "$current" = "$latest" ]; then
            up_to_date+=("$repo")
        else
            update_needed+=("$repo")
        fi
    done

    if [ ${#up_to_date[@]} -gt 0 ]; then
        success "Up to date (${#up_to_date[@]}):"
        for plugin in "${up_to_date[@]}"; do
            echo "  ✓ $plugin"
        done
    fi

    if [ ${#update_needed[@]} -gt 0 ]; then
        echo ""
        warning "Updates available (${#update_needed[@]}):"
        for plugin in "${update_needed[@]}"; do
            echo "  ⚠ $plugin"
        done
    fi

    if [ ${#not_initialized[@]} -gt 0 ]; then
        echo ""
        error "Not initialized (${#not_initialized[@]}):"
        for plugin in "${not_initialized[@]}"; do
            echo "  ✗ $plugin"
        done
    fi

    echo ""
    info "To update all plugins, run: ./scripts/plugin_update_all.sh"
}

# Main function
main() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}Entity Plugin Version Checker${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Change to project root
    cd "$PROJECT_ROOT"

    # Check versions for all plugins or specific plugin
    if [ $# -gt 0 ] && [ "$1" != "-h" ] && [ "$1" != "--help" ] && [ "$1" != "--summary" ]; then
        # Check specific plugin
        local found=false
        for repo in "${PLUGIN_REPOS[@]}"; do
            if [[ "$repo" == *"$1"* ]]; then
                check_plugin_version "$repo"
                found=true
                break
            fi
        done

        if [ "$found" = false ]; then
            error "Plugin not found: $1"
            echo "Available plugins:"
            for repo in "${PLUGIN_REPOS[@]}"; do
                echo "  - $repo"
            done
            exit 1
        fi
    else
        # Check all plugins
        for repo in "${PLUGIN_REPOS[@]}"; do
            check_plugin_version "$repo"
        done

        # Generate summary
        generate_summary
    fi

    echo ""
    success "Version check completed!"
}

# Handle script arguments
if [ $# -gt 0 ]; then
    case "$1" in
        -h|--help)
            echo "Usage: $0 [plugin-name]"
            echo ""
            echo "Check version information for Entity Framework plugins using gh CLI."
            echo ""
            echo "Examples:"
            echo "  $0                    # Check all plugins"
            echo "  $0 examples           # Check specific plugin"
            echo "  $0 --summary          # Show summary only"
            echo ""
            echo "This script will:"
            echo "  1. Check current commit for each plugin submodule"
            echo "  2. Compare with latest commit on GitHub"
            echo "  3. List recent releases using gh release list"
            echo "  4. Show open PRs and issues count"
            echo ""
            echo "Available plugins:"
            for repo in "${PLUGIN_REPOS[@]}"; do
                echo "  - $repo"
            done
            exit 0
            ;;
        --summary)
            cd "$PROJECT_ROOT"
            generate_summary
            exit 0
            ;;
    esac
fi

# Run main function
main "$@"
