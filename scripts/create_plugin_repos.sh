#!/bin/bash

# Entity Framework Plugin Repository Creation Script
# Story: ENTITY-101 - Create GitHub Repositories Using gh CLI
# This script creates plugin repositories for the Entity Framework

set -euo pipefail

# Configuration
ORGANIZATION="Ladvien"
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/repo_creation_${TIMESTAMP}.log"
DRY_RUN=false

# Repository definitions (using parallel arrays for bash 3.2 compatibility)
REPO_NAMES=(
    "entity-plugin-examples"
    "entity-plugin-gpt-oss"
    "entity-plugin-stdlib"
    "entity-plugin-template"
)

REPO_DESCRIPTIONS=(
    "Example plugins demonstrating Entity Framework plugin development"
    "GPT-OSS plugins for Entity Framework - advanced AI capabilities"
    "Standard library plugins for Entity Framework - core utilities"
    "Template repository for creating new Entity Framework plugins"
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
            echo "  --dry-run    Perform a dry run without creating repositories"
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

# Function to check if repository exists
repo_exists() {
    local repo_name=$1
    if gh repo view "${ORGANIZATION}/${repo_name}" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to create repository
create_repository() {
    local repo_name=$1
    local description=$2

    log "INFO" "Processing repository: ${repo_name}"

    # Check if repository already exists
    if repo_exists "$repo_name"; then
        log "WARN" "Repository ${ORGANIZATION}/${repo_name} already exists. Skipping."
        echo -e "${YELLOW}⚠️  Repository ${ORGANIZATION}/${repo_name} already exists${NC}"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would create repository: ${ORGANIZATION}/${repo_name}"
        echo -e "${BLUE}🔍 [DRY-RUN] Would create: ${ORGANIZATION}/${repo_name}${NC}"
        echo "   Description: $description"
        echo "   License: MIT"
        echo "   Visibility: Public"
    else
        log "INFO" "Creating repository: ${ORGANIZATION}/${repo_name}"

        # Create the repository
        if gh repo create "${ORGANIZATION}/${repo_name}" \
            --public \
            --description "$description" \
            --license MIT \
            --add-readme 2>&1 | tee -a "$LOG_FILE"; then

            log "SUCCESS" "Repository ${ORGANIZATION}/${repo_name} created successfully"
            echo -e "${GREEN}✅ Created: ${ORGANIZATION}/${repo_name}${NC}"

            # Add topics to help with discovery
            log "INFO" "Adding topics to ${repo_name}"
            gh repo edit "${ORGANIZATION}/${repo_name}" \
                --add-topic "entity-framework" \
                --add-topic "entity-plugin" \
                --add-topic "python" 2>&1 | tee -a "$LOG_FILE"

        else
            log "ERROR" "Failed to create repository ${ORGANIZATION}/${repo_name}"
            echo -e "${RED}❌ Failed to create: ${ORGANIZATION}/${repo_name}${NC}"
            return 1
        fi
    fi
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Entity Framework Plugin Repository Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY-RUN mode - no repositories will be created${NC}"
        echo ""
    fi

    log "INFO" "Starting repository creation process"
    log "INFO" "Organization: ${ORGANIZATION}"
    log "INFO" "Dry run mode: ${DRY_RUN}"

    # Check if gh CLI is installed and authenticated
    if ! command -v gh &> /dev/null; then
        log "ERROR" "gh CLI is not installed"
        echo -e "${RED}Error: gh CLI is not installed. Please install it first.${NC}"
        echo "Visit: https://cli.github.com/"
        exit 1
    fi

    # Check gh authentication
    if ! gh auth status &>/dev/null; then
        log "ERROR" "gh CLI is not authenticated"
        echo -e "${RED}Error: gh CLI is not authenticated.${NC}"
        echo "Run: gh auth login"
        exit 1
    fi

    log "INFO" "gh CLI authentication verified"
    echo -e "${GREEN}✓ gh CLI authenticated${NC}"
    echo ""

    # Display current auth status
    echo "Current GitHub authentication:"
    gh auth status 2>&1 | grep -E "Logged in to|Token:" | head -3
    echo ""

    # Create repositories
    local success_count=0
    local skip_count=0
    local fail_count=0

    # Process each repository
    for i in "${!REPO_NAMES[@]}"; do
        repo_name="${REPO_NAMES[$i]}"
        description="${REPO_DESCRIPTIONS[$i]}"

        if create_repository "$repo_name" "$description"; then
            if repo_exists "$repo_name" || [ "$DRY_RUN" = true ]; then
                ((success_count++))
            else
                ((skip_count++))
            fi
        else
            ((fail_count++))
        fi
        echo ""
    done

    # Summary
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}Dry run completed.${NC}"
        echo "Would create/update: $success_count repositories"
    else
        echo -e "${GREEN}Created: $success_count repositories${NC}"
        echo -e "${YELLOW}Skipped (already exist): $skip_count repositories${NC}"
        if [ $fail_count -gt 0 ]; then
            echo -e "${RED}Failed: $fail_count repositories${NC}"
        fi
    fi

    echo ""
    echo "Log file: $LOG_FILE"

    log "INFO" "Repository creation process completed"
    log "INFO" "Success: $success_count, Skipped: $skip_count, Failed: $fail_count"

    # Verify all repositories if not in dry-run mode
    if [ "$DRY_RUN" = false ]; then
        echo ""
        echo -e "${BLUE}Verifying repositories...${NC}"
        for repo_name in "${REPO_NAMES[@]}"; do
            if repo_exists "$repo_name"; then
                echo -e "${GREEN}✓${NC} ${ORGANIZATION}/${repo_name}"
            else
                echo -e "${RED}✗${NC} ${ORGANIZATION}/${repo_name}"
            fi
        done
    fi

    if [ $fail_count -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main
