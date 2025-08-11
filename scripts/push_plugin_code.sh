#!/bin/bash

# Entity Framework Plugin Code Push Script
# Story: ENTITY-102 - Initialize and Push Plugin Code
# This script initializes plugin directories as Git repos and pushes to GitHub

set -euo pipefail

# Configuration
ORGANIZATION="Ladvien"
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/plugin_push_${TIMESTAMP}.log"
DRY_RUN=false
TEMP_DIR="/tmp/entity-plugins-${TIMESTAMP}"

# Plugin mappings (source directory -> repository name)
declare -a PLUGINS
PLUGINS=(
    "src/entity/plugins/examples:entity-plugin-examples:Example plugins for Entity Framework"
    "src/entity/plugins/gpt_oss:entity-plugin-gpt-oss:GPT-OSS plugins for Entity Framework"
)

# Additional plugin directories that don't exist yet but repos do
ADDITIONAL_PLUGINS=(
    "entity-plugin-stdlib:Standard library plugins for Entity Framework"
    "entity-plugin-template:Template for creating Entity Framework plugins"
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
            echo "  --dry-run    Perform a dry run without pushing code"
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

# Function to get repository URL
get_repo_url() {
    local repo_name=$1
    gh repo view "${ORGANIZATION}/${repo_name}" --json url --jq '.url' 2>/dev/null || echo ""
}

# Function to check if repository has code
repo_has_code() {
    local repo_name=$1
    local file_count=$(gh api "repos/${ORGANIZATION}/${repo_name}/contents" --jq 'length' 2>/dev/null || echo "0")
    # Repository has more than just LICENSE and README
    if [ "$file_count" -gt 2 ]; then
        return 0
    else
        return 1
    fi
}

# Function to create initial plugin structure
create_plugin_structure() {
    local temp_repo_dir=$1
    local repo_name=$2
    local description=$3

    log "INFO" "Creating plugin structure for ${repo_name}"

    # Create standard Python package structure
    mkdir -p "${temp_repo_dir}/src/${repo_name//-/_}"
    mkdir -p "${temp_repo_dir}/tests"
    mkdir -p "${temp_repo_dir}/docs"

    # Create .gitignore
    cat > "${temp_repo_dir}/.gitignore" << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyTest
.pytest_cache/
.coverage
htmlcov/

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Project specific
*.log
logs/
EOF

    # Create pyproject.toml
    cat > "${temp_repo_dir}/pyproject.toml" << EOF
[project]
name = "${repo_name}"
version = "0.1.0"
description = "${description}"
authors = [
    {name = "Entity Framework Team", email = "team@entity-framework.org"}
]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "entity-core>=0.1.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]
EOF

    # Update README.md
    cat > "${temp_repo_dir}/README.md" << EOF
# ${repo_name}

${description}

## Installation

\`\`\`bash
pip install ${repo_name}
\`\`\`

## Usage

\`\`\`python
from ${repo_name//-/_} import ...
\`\`\`

## Development

\`\`\`bash
git clone https://github.com/${ORGANIZATION}/${repo_name}.git
cd ${repo_name}
pip install -e ".[dev]"
\`\`\`

## License

MIT License - see LICENSE file for details.
EOF
}

# Function to push plugin code
push_plugin_code() {
    local source_dir=$1
    local repo_name=$2
    local description=$3

    log "INFO" "Processing plugin: ${repo_name}"

    # Check if repository exists
    local repo_url=$(get_repo_url "$repo_name")
    if [ -z "$repo_url" ]; then
        log "ERROR" "Repository ${ORGANIZATION}/${repo_name} does not exist"
        echo -e "${RED}❌ Repository ${ORGANIZATION}/${repo_name} does not exist${NC}"
        return 1
    fi

    # Check if repository already has code
    if repo_has_code "$repo_name"; then
        log "WARN" "Repository ${ORGANIZATION}/${repo_name} already has code. Skipping."
        echo -e "${YELLOW}⚠️  Repository ${ORGANIZATION}/${repo_name} already has code${NC}"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log "INFO" "[DRY-RUN] Would push code to: ${ORGANIZATION}/${repo_name}"
        echo -e "${BLUE}🔍 [DRY-RUN] Would push to: ${ORGANIZATION}/${repo_name}${NC}"
        if [ -d "$source_dir" ]; then
            echo "   Source: $source_dir"
            local file_count=$(find "$source_dir" -type f -name "*.py" | wc -l)
            echo "   Python files: $file_count"
        else
            echo "   Would create new plugin structure"
        fi
        return 0
    fi

    # Create temporary directory for the repository
    local temp_repo_dir="${TEMP_DIR}/${repo_name}"
    mkdir -p "$temp_repo_dir"

    log "INFO" "Cloning repository ${repo_name}"

    # Clone the repository
    if ! gh repo clone "${ORGANIZATION}/${repo_name}" "$temp_repo_dir" -- --quiet; then
        log "ERROR" "Failed to clone repository ${repo_name}"
        echo -e "${RED}❌ Failed to clone ${repo_name}${NC}"
        return 1
    fi

    # Copy source code if it exists
    if [ -d "$source_dir" ]; then
        log "INFO" "Copying source code from $source_dir"

        # Create package directory
        local package_name="${repo_name//-/_}"
        mkdir -p "${temp_repo_dir}/src/${package_name}"

        # Copy Python files
        cp -r "$source_dir"/* "${temp_repo_dir}/src/${package_name}/" 2>/dev/null || true

        # Copy tests if they exist
        local test_dir="${source_dir/plugins/tests/plugins}"
        if [ -d "$test_dir" ]; then
            log "INFO" "Copying tests from $test_dir"
            cp -r "$test_dir"/* "${temp_repo_dir}/tests/" 2>/dev/null || true
        fi
    else
        log "INFO" "No source directory found, creating plugin structure"
    fi

    # Create plugin structure
    create_plugin_structure "$temp_repo_dir" "$repo_name" "$description"

    # Initialize git and commit
    cd "$temp_repo_dir"

    # Add all files
    git add -A

    # Check if there are changes to commit
    if git diff --cached --quiet; then
        log "WARN" "No changes to commit for ${repo_name}"
        echo -e "${YELLOW}No changes to commit for ${repo_name}${NC}"
        cd - > /dev/null
        return 0
    fi

    # Commit changes
    git commit -m "feat: Initial plugin code and structure

- Add Python package structure
- Add pyproject.toml for package configuration
- Add .gitignore for Python projects
- Add initial plugin code
- Set up development environment

Part of Entity Framework plugin migration (Story ENTITY-102)"

    log "INFO" "Pushing code to ${ORGANIZATION}/${repo_name}"

    # Push to repository
    if git push origin main; then
        log "SUCCESS" "Successfully pushed code to ${repo_name}"
        echo -e "${GREEN}✅ Pushed code to: ${ORGANIZATION}/${repo_name}${NC}"
    else
        log "ERROR" "Failed to push code to ${repo_name}"
        echo -e "${RED}❌ Failed to push to ${repo_name}${NC}"
        cd - > /dev/null
        return 1
    fi

    cd - > /dev/null
    return 0
}

# Main execution
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Entity Framework Plugin Code Push${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY-RUN mode - no code will be pushed${NC}"
        echo ""
    fi

    log "INFO" "Starting plugin code push process"
    log "INFO" "Organization: ${ORGANIZATION}"
    log "INFO" "Dry run mode: ${DRY_RUN}"

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

    # Create temporary directory
    mkdir -p "$TEMP_DIR"

    # Process each plugin with source code
    local success_count=0
    local skip_count=0
    local fail_count=0

    echo -e "${BLUE}Processing plugins with existing source code:${NC}"
    for plugin_entry in "${PLUGINS[@]}"; do
        IFS=':' read -r source_dir repo_name description <<< "$plugin_entry"

        if push_plugin_code "$source_dir" "$repo_name" "$description"; then
            if repo_has_code "$repo_name" || [ "$DRY_RUN" = true ]; then
                ((success_count++))
            else
                ((skip_count++))
            fi
        else
            ((fail_count++))
        fi
        echo ""
    done

    # Process additional plugins without source code
    echo -e "${BLUE}Processing additional plugin repositories:${NC}"
    for plugin_entry in "${ADDITIONAL_PLUGINS[@]}"; do
        IFS=':' read -r repo_name description <<< "$plugin_entry"

        if push_plugin_code "" "$repo_name" "$description"; then
            if repo_has_code "$repo_name" || [ "$DRY_RUN" = true ]; then
                ((success_count++))
            else
                ((skip_count++))
            fi
        else
            ((fail_count++))
        fi
        echo ""
    done

    # Cleanup
    if [ "$DRY_RUN" = false ]; then
        rm -rf "$TEMP_DIR"
    fi

    # Summary
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Summary${NC}"
    echo -e "${BLUE}========================================${NC}"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${BLUE}Dry run completed.${NC}"
        echo "Would push to: $success_count repositories"
    else
        echo -e "${GREEN}Pushed: $success_count repositories${NC}"
        echo -e "${YELLOW}Skipped (already have code): $skip_count repositories${NC}"
        if [ $fail_count -gt 0 ]; then
            echo -e "${RED}Failed: $fail_count repositories${NC}"
        fi
    fi

    echo ""
    echo "Log file: $LOG_FILE"

    log "INFO" "Plugin code push process completed"
    log "INFO" "Success: $success_count, Skipped: $skip_count, Failed: $fail_count"

    # Verify all repositories if not in dry-run mode
    if [ "$DRY_RUN" = false ]; then
        echo ""
        echo -e "${BLUE}Verifying repositories...${NC}"
        for plugin_entry in "${PLUGINS[@]}"; do
            IFS=':' read -r source_dir repo_name description <<< "$plugin_entry"
            if repo_has_code "$repo_name"; then
                echo -e "${GREEN}✓${NC} ${ORGANIZATION}/${repo_name} has code"
            else
                echo -e "${RED}✗${NC} ${ORGANIZATION}/${repo_name} missing code"
            fi
        done

        for plugin_entry in "${ADDITIONAL_PLUGINS[@]}"; do
            IFS=':' read -r repo_name description <<< "$plugin_entry"
            if repo_has_code "$repo_name"; then
                echo -e "${GREEN}✓${NC} ${ORGANIZATION}/${repo_name} has code"
            else
                echo -e "${YELLOW}⚠${NC} ${ORGANIZATION}/${repo_name} has basic structure only"
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
