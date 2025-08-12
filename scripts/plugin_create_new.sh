#!/bin/bash

# Entity Framework Plugin Management - Create New Plugin
# Story: ENTITY-109 - Create Management Tooling
# This script creates a new plugin from template using gh repo create and gh repo clone

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLUGINS_DIR="$PROJECT_ROOT/plugins"
GITHUB_ORG="Ladvien"
TEMPLATE_REPO="entity-plugin-template"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

    # Check git
    if ! command -v git &> /dev/null; then
        error "git is not installed."
        exit 1
    fi

    # Check template repository exists
    if ! gh repo view "$GITHUB_ORG/$TEMPLATE_REPO" &> /dev/null; then
        error "Template repository $GITHUB_ORG/$TEMPLATE_REPO not found"
        exit 1
    fi

    success "Prerequisites met"
}

# Validate plugin name
validate_plugin_name() {
    local name=$1

    # Check if name is provided
    if [ -z "$name" ]; then
        error "Plugin name cannot be empty"
        return 1
    fi

    # Check name format (letters, numbers, hyphens only)
    if ! [[ "$name" =~ ^[a-z0-9-]+$ ]]; then
        error "Plugin name must contain only lowercase letters, numbers, and hyphens"
        return 1
    fi

    # Check if name starts with entity-plugin-
    if ! [[ "$name" =~ ^entity-plugin- ]]; then
        warning "Plugin name should start with 'entity-plugin-'"
        echo -n "Do you want to use 'entity-plugin-$name' instead? (y/n): "
        read -r response
        if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
            echo "entity-plugin-$name"
            return 0
        fi
    fi

    echo "$name"
    return 0
}

# Create new plugin repository
create_plugin_repo() {
    local plugin_name=$1
    local description=$2
    local visibility=${3:-public}

    log "Creating new repository: $GITHUB_ORG/$plugin_name"

    # Check if repository already exists
    if gh repo view "$GITHUB_ORG/$plugin_name" &> /dev/null; then
        error "Repository $GITHUB_ORG/$plugin_name already exists"
        return 1
    fi

    # Create repository from template
    log "Creating repository from template..."
    gh repo create "$GITHUB_ORG/$plugin_name" \
        --template "$GITHUB_ORG/$TEMPLATE_REPO" \
        --description "$description" \
        --$visibility \
        --clone=false

    if [ $? -eq 0 ]; then
        success "Repository created successfully"
        return 0
    else
        error "Failed to create repository"
        return 1
    fi
}

# Clone and set up the new plugin
setup_plugin() {
    local plugin_name=$1
    local plugin_dir=$2

    log "Setting up plugin locally..."

    # Create temporary directory for initial setup
    local temp_dir="/tmp/entity-plugin-setup-$$"
    mkdir -p "$temp_dir"

    # Clone the new repository
    log "Cloning repository..."
    cd "$temp_dir"
    if ! gh repo clone "$GITHUB_ORG/$plugin_name"; then
        error "Failed to clone repository"
        rm -rf "$temp_dir"
        return 1
    fi

    cd "$plugin_name"

    # Update template files
    log "Customizing plugin files..."

    # Update README.md
    if [ -f "README.md" ]; then
        sed -i.bak "s/entity-plugin-template/$plugin_name/g" README.md
        sed -i.bak "s/Template Plugin/${plugin_name#entity-plugin-}/g" README.md
        rm README.md.bak
    fi

    # Update pyproject.toml if it exists
    if [ -f "pyproject.toml" ]; then
        sed -i.bak "s/entity-plugin-template/$plugin_name/g" pyproject.toml
        sed -i.bak "s/name = \".*\"/name = \"$plugin_name\"/g" pyproject.toml
        rm pyproject.toml.bak
    fi

    # Update setup.py if it exists
    if [ -f "setup.py" ]; then
        sed -i.bak "s/entity-plugin-template/$plugin_name/g" setup.py
        sed -i.bak "s/name=\".*\"/name=\"$plugin_name\"/g" setup.py
        rm setup.py.bak
    fi

    # Commit customizations
    if ! git diff --quiet; then
        git add -A
        git commit -m "feat: Customize plugin from template

- Updated plugin name references
- Configured package metadata
- Prepared for development"

        log "Pushing customizations..."
        git push origin main || git push origin master
    fi

    # Add as submodule to main project
    log "Adding plugin as submodule to main project..."
    cd "$PROJECT_ROOT"

    local submodule_path="plugins/$plugin_dir"

    # Check if submodule already exists
    if [ -d "$submodule_path" ]; then
        error "Directory $submodule_path already exists"
        rm -rf "$temp_dir"
        return 1
    fi

    # Add submodule
    git submodule add "git@github.com:$GITHUB_ORG/$plugin_name.git" "$submodule_path"

    if [ $? -eq 0 ]; then
        success "Plugin added as submodule at $submodule_path"

        # Initialize and update submodule
        git submodule update --init "$submodule_path"

        info "To commit the new submodule, run:"
        echo "  git add .gitmodules $submodule_path"
        echo "  git commit -m 'feat: Add $plugin_name plugin as submodule'"
    else
        error "Failed to add submodule"
        rm -rf "$temp_dir"
        return 1
    fi

    # Clean up
    rm -rf "$temp_dir"

    return 0
}

# Interactive plugin creation
interactive_create() {
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}Create New Entity Plugin${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""

    # Get plugin name
    echo -n "Enter plugin name (e.g., entity-plugin-myfeature): "
    read -r input_name

    plugin_name=$(validate_plugin_name "$input_name")
    if [ $? -ne 0 ]; then
        exit 1
    fi

    # Get plugin directory name
    local default_dir="${plugin_name#entity-plugin-}"
    echo -n "Enter plugin directory name [$default_dir]: "
    read -r plugin_dir
    plugin_dir=${plugin_dir:-$default_dir}

    # Get description
    echo -n "Enter plugin description: "
    read -r description

    # Get visibility
    echo -n "Repository visibility (public/private) [public]: "
    read -r visibility
    visibility=${visibility:-public}

    # Confirm
    echo ""
    echo "Plugin Configuration:"
    echo "  Name:        $plugin_name"
    echo "  Directory:   plugins/$plugin_dir"
    echo "  Description: $description"
    echo "  Visibility:  $visibility"
    echo ""
    echo -n "Create this plugin? (y/n): "
    read -r confirm

    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        warning "Plugin creation cancelled"
        exit 0
    fi

    # Create the plugin
    if create_plugin_repo "$plugin_name" "$description" "$visibility"; then
        setup_plugin "$plugin_name" "$plugin_dir"
    fi
}

# Main function
main() {
    # Check prerequisites
    check_prerequisites

    # Handle arguments
    if [ $# -eq 0 ]; then
        # Interactive mode
        interactive_create
    else
        # Parse arguments
        local plugin_name=""
        local plugin_dir=""
        local description=""
        local visibility="public"

        while [[ $# -gt 0 ]]; do
            case $1 in
                --name)
                    plugin_name="$2"
                    shift 2
                    ;;
                --dir)
                    plugin_dir="$2"
                    shift 2
                    ;;
                --description)
                    description="$2"
                    shift 2
                    ;;
                --private)
                    visibility="private"
                    shift
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

        # Validate required arguments
        if [ -z "$plugin_name" ]; then
            error "Plugin name is required"
            echo "Run '$0 --help' for usage information."
            exit 1
        fi

        # Validate and set defaults
        plugin_name=$(validate_plugin_name "$plugin_name")
        if [ $? -ne 0 ]; then
            exit 1
        fi

        if [ -z "$plugin_dir" ]; then
            plugin_dir="${plugin_name#entity-plugin-}"
        fi

        if [ -z "$description" ]; then
            description="Entity Framework plugin: $plugin_name"
        fi

        # Create the plugin
        if create_plugin_repo "$plugin_name" "$description" "$visibility"; then
            setup_plugin "$plugin_name" "$plugin_dir"
        fi
    fi

    echo ""
    success "Plugin creation completed!"
}

# Show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Create a new Entity Framework plugin from template using gh CLI."
    echo ""
    echo "Options:"
    echo "  --name NAME           Plugin repository name (required in non-interactive mode)"
    echo "  --dir DIR             Plugin directory name under plugins/ (default: plugin name without prefix)"
    echo "  --description DESC    Plugin description"
    echo "  --private             Create as private repository (default: public)"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Interactive mode:"
    echo "  $0                    # Run in interactive mode"
    echo ""
    echo "Command mode:"
    echo "  $0 --name entity-plugin-auth --description \"Authentication plugin\""
    echo "  $0 --name entity-plugin-cache --dir cache --private"
    echo ""
    echo "This script will:"
    echo "  1. Create a new repository from entity-plugin-template"
    echo "  2. Clone and customize the template files"
    echo "  3. Add the plugin as a submodule to the main project"
    echo "  4. Set up the plugin for development"
}

# Run main function
main "$@"
