#!/bin/bash

# Entity Framework Plugin Management - List Plugin PRs
# Story: ENTITY-109 - Create Management Tooling
# This script lists all plugin PRs using gh pr list

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GITHUB_ORG="Ladvien"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Plugin repositories
PLUGIN_REPOS=(
    "entity-plugin-examples"
    "entity-plugin-gpt-oss"
    "entity-plugin-stdlib"
    "entity-plugin-template"
)

# PR states to check
PR_STATES=("open" "closed" "merged")

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

# Format PR state with color
format_pr_state() {
    local state=$1
    case "$state" in
        "OPEN")
            echo -e "${GREEN}● OPEN${NC}"
            ;;
        "CLOSED")
            echo -e "${RED}● CLOSED${NC}"
            ;;
        "MERGED")
            echo -e "${MAGENTA}● MERGED${NC}"
            ;;
        *)
            echo -e "${YELLOW}● $state${NC}"
            ;;
    esac
}

# Format PR labels
format_labels() {
    local labels=$1
    if [ -z "$labels" ] || [ "$labels" = "null" ]; then
        echo ""
    else
        echo -e " ${CYAN}[$labels]${NC}"
    fi
}

# List PRs for a single plugin
list_plugin_prs() {
    local plugin_name=$1
    local state_filter=${2:-"all"}
    local show_details=${3:-false}

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Plugin: ${CYAN}$plugin_name${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"

    # Check if repository exists
    if ! gh repo view "$GITHUB_ORG/$plugin_name" &> /dev/null; then
        error "Repository $GITHUB_ORG/$plugin_name not found"
        return 1
    fi

    # Determine state parameter for gh CLI
    local gh_state=""
    case "$state_filter" in
        "open")
            gh_state="open"
            ;;
        "closed")
            gh_state="closed"
            ;;
        "merged")
            gh_state="closed"
            ;;
        "all")
            gh_state="all"
            ;;
    esac

    # Get PRs using gh CLI with JSON output
    local prs_json=$(gh pr list \
        --repo "$GITHUB_ORG/$plugin_name" \
        --state "$gh_state" \
        --limit 30 \
        --json number,title,state,author,createdAt,updatedAt,labels,isDraft,mergeable,mergedAt \
        2>/dev/null || echo "[]")

    # Check if any PRs found
    if [ "$prs_json" = "[]" ]; then
        info "No pull requests found (state: $state_filter)"
        return 0
    fi

    # Parse and display PRs
    local pr_count=0
    echo "$prs_json" | jq -r '.[] | @json' | while IFS= read -r pr; do
        # Extract PR fields
        local number=$(echo "$pr" | jq -r '.number')
        local title=$(echo "$pr" | jq -r '.title')
        local state=$(echo "$pr" | jq -r '.state')
        local author=$(echo "$pr" | jq -r '.author.login // "unknown"')
        local created=$(echo "$pr" | jq -r '.createdAt' | cut -d'T' -f1)
        local updated=$(echo "$pr" | jq -r '.updatedAt' | cut -d'T' -f1)
        local is_draft=$(echo "$pr" | jq -r '.isDraft')
        local merged_at=$(echo "$pr" | jq -r '.mergedAt // ""')
        local labels=$(echo "$pr" | jq -r '.labels | map(.name) | join(", ")')

        # Filter merged PRs if needed
        if [ "$state_filter" = "merged" ] && [ -z "$merged_at" ]; then
            continue
        fi

        # Determine actual state
        local display_state="$state"
        if [ -n "$merged_at" ]; then
            display_state="MERGED"
        fi

        # Format draft indicator
        local draft_indicator=""
        if [ "$is_draft" = "true" ]; then
            draft_indicator="${YELLOW}[DRAFT]${NC} "
        fi

        # Display PR info
        echo ""
        echo -e "  ${GREEN}#$number${NC} - ${draft_indicator}$title$(format_labels "$labels")"
        echo -e "  $(format_pr_state "$display_state") by ${CYAN}@$author${NC}"
        echo -e "  Created: $created | Updated: $updated"

        if [ -n "$merged_at" ]; then
            local merged_date=$(echo "$merged_at" | cut -d'T' -f1)
            echo -e "  ${MAGENTA}Merged: $merged_date${NC}"
        fi

        # Show additional details if requested
        if [ "$show_details" = "true" ]; then
            # Get PR details
            local pr_details=$(gh pr view "$number" \
                --repo "$GITHUB_ORG/$plugin_name" \
                --json additions,deletions,files,reviews \
                2>/dev/null || echo "{}")

            if [ "$pr_details" != "{}" ]; then
                local additions=$(echo "$pr_details" | jq -r '.additions // 0')
                local deletions=$(echo "$pr_details" | jq -r '.deletions // 0')
                local files=$(echo "$pr_details" | jq -r '.files | length // 0')
                local reviews=$(echo "$pr_details" | jq -r '.reviews | length // 0')

                echo -e "  Files: $files | ${GREEN}+$additions${NC} ${RED}-$deletions${NC} | Reviews: $reviews"
            fi
        fi

        ((pr_count++))
    done

    if [ $pr_count -eq 0 ] && [ "$state_filter" = "merged" ]; then
        info "No merged pull requests found"
    else
        echo ""
        info "Total PRs shown: $pr_count"
    fi

    return 0
}

# Generate summary report
generate_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}Pull Request Summary${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""

    local total_open=0
    local total_closed=0
    local total_merged=0

    for repo in "${PLUGIN_REPOS[@]}"; do
        # Count PRs for each repository
        local open_count=$(gh pr list --repo "$GITHUB_ORG/$repo" --state open --json number --jq '. | length' 2>/dev/null || echo "0")
        local closed_count=$(gh pr list --repo "$GITHUB_ORG/$repo" --state closed --limit 100 --json number,mergedAt --jq '[.[] | select(.mergedAt == null)] | length' 2>/dev/null || echo "0")
        local merged_count=$(gh pr list --repo "$GITHUB_ORG/$repo" --state closed --limit 100 --json number,mergedAt --jq '[.[] | select(.mergedAt != null)] | length' 2>/dev/null || echo "0")

        echo -e "${CYAN}$repo:${NC}"
        echo -e "  ${GREEN}Open: $open_count${NC} | ${RED}Closed: $closed_count${NC} | ${MAGENTA}Merged: $merged_count${NC}"

        total_open=$((total_open + open_count))
        total_closed=$((total_closed + closed_count))
        total_merged=$((total_merged + merged_count))
    done

    echo ""
    echo -e "${BLUE}─────────────────────────────────────${NC}"
    echo -e "${CYAN}Total across all plugins:${NC}"
    echo -e "  ${GREEN}Open: $total_open${NC} | ${RED}Closed: $total_closed${NC} | ${MAGENTA}Merged: $total_merged${NC}"

    # List PRs needing review
    echo ""
    echo -e "${YELLOW}PRs needing review:${NC}"
    local review_needed=false

    for repo in "${PLUGIN_REPOS[@]}"; do
        local prs_needing_review=$(gh pr list \
            --repo "$GITHUB_ORG/$repo" \
            --state open \
            --json number,title,isDraft \
            --jq '.[] | select(.isDraft == false) | "#\(.number) - \(.title)"' \
            2>/dev/null)

        if [ -n "$prs_needing_review" ]; then
            echo -e "${CYAN}$repo:${NC}"
            echo "$prs_needing_review" | while IFS= read -r pr; do
                echo "  $pr"
            done
            review_needed=true
        fi
    done

    if [ "$review_needed" = false ]; then
        echo "  None - all open PRs are drafts or no open PRs"
    fi
}

# Main function
main() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}Entity Plugin PR Tracker${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Parse arguments
    local state_filter="open"
    local show_details=false
    local show_summary=false
    local specific_plugin=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --state)
                state_filter="$2"
                shift 2
                ;;
            --all)
                state_filter="all"
                shift
                ;;
            --open)
                state_filter="open"
                shift
                ;;
            --closed)
                state_filter="closed"
                shift
                ;;
            --merged)
                state_filter="merged"
                shift
                ;;
            --details)
                show_details=true
                shift
                ;;
            --summary)
                show_summary=true
                shift
                ;;
            --plugin)
                specific_plugin="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                echo "Run '$0 --help' for usage information."
                exit 1
                ;;
        esac
    done

    # Show summary if requested
    if [ "$show_summary" = true ]; then
        generate_summary
    elif [ -n "$specific_plugin" ]; then
        # Check specific plugin
        local found=false
        for repo in "${PLUGIN_REPOS[@]}"; do
            if [[ "$repo" == *"$specific_plugin"* ]]; then
                list_plugin_prs "$repo" "$state_filter" "$show_details"
                found=true
                break
            fi
        done

        if [ "$found" = false ]; then
            error "Plugin not found: $specific_plugin"
            echo "Available plugins:"
            for repo in "${PLUGIN_REPOS[@]}"; do
                echo "  - $repo"
            done
            exit 1
        fi
    else
        # List PRs for all plugins
        for repo in "${PLUGIN_REPOS[@]}"; do
            list_plugin_prs "$repo" "$state_filter" "$show_details"
        done

        # Show summary at the end
        generate_summary
    fi

    echo ""
    success "PR listing completed!"
}

# Show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "List pull requests for Entity Framework plugins using gh CLI."
    echo ""
    echo "Options:"
    echo "  --state STATE    Filter by PR state (open|closed|merged|all) [default: open]"
    echo "  --open           Show only open PRs (default)"
    echo "  --closed         Show only closed PRs"
    echo "  --merged         Show only merged PRs"
    echo "  --all            Show all PRs"
    echo "  --details        Show additional PR details (files, additions, deletions)"
    echo "  --summary        Show summary only"
    echo "  --plugin NAME    Show PRs for specific plugin only"
    echo "  -h, --help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # List all open PRs"
    echo "  $0 --merged                  # List all merged PRs"
    echo "  $0 --all --details           # List all PRs with details"
    echo "  $0 --plugin examples         # List PRs for examples plugin only"
    echo "  $0 --summary                 # Show summary of all PRs"
    echo ""
    echo "Available plugins:"
    for repo in "${PLUGIN_REPOS[@]}"; do
        echo "  - $repo"
    done
}

# Run main function
main "$@"
