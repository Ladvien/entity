#!/bin/bash

# Check if branch name is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a branch name"
    echo "Usage: $0 <branch-name>"
    echo "Example: $0 9716pf-codex/refactor-repositories-to-inherit-from-baserepository"
    exit 1
fi

BRANCH_NAME="$1"

echo "Starting git operations for branch: $BRANCH_NAME"

# Pull from origin
echo "Pulling from origin $BRANCH_NAME..."
git pull origin "$BRANCH_NAME"

if [ $? -ne 0 ]; then
    echo "Merge conflicts detected. Continuing with merge conflict resolution..."
    echo "Files with conflicts will be staged as-is for the agent to resolve."
fi

# Add all changes
echo "Adding all changes..."
git add -A

# Commit with the specified message
echo "Committing changes..."
git commit -m "Prepping for agent to address merge conflicts."

if [ $? -ne 0 ]; then
    echo "Note: No changes to commit or commit failed"
fi

# Push to origin
echo "Pushing to origin..."
git push

if [ $? -ne 0 ]; then
    echo "Error: Failed to push to origin"
    exit 1
fi

echo "Git operations completed successfully!"