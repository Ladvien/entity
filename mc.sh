#!/usr/bin/env bash
set -euo pipefail

# --- Load GitHub token from .env if present ---
if [ -f .env ]; then
  echo "📦 Loading .env"
  # shellcheck disable=SC1091
  source .env
fi

# --- Validate token ---
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "❌ GITHUB_TOKEN is not set. Add it to .env or export it."
  exit 1
fi

# --- Detect and parse repo info ---
if git remote get-url origin >/dev/null 2>&1; then
  REMOTE_URL=$(git remote get-url origin)
else
  REMOTE_URL=$(git config --get remote.origin.url)
fi

# Normalize and extract owner/repo
REMOTE_CLEAN="${REMOTE_URL#*github.com[:/]}"
OWNER_REPO=$(echo "$REMOTE_CLEAN" | awk -F'[:/]' '{print $(NF-1) "/" $NF}' | sed 's/\.git$//')
OWNER=$(echo "$OWNER_REPO" | awk -F/ '{print $1}')
REPO=$(echo "$OWNER_REPO" | awk -F/ '{print $2}')

if [ -z "$OWNER" ] || [ -z "$REPO" ]; then
  echo "❌ Failed to extract owner/repo from: $REMOTE_URL"
  exit 1
fi

echo "🔍 Repo detected: $OWNER/$REPO"

# --- Checkout and update main branch ---
echo "📂 Checking out and updating 'main'..."
git checkout main
git pull origin main

# --- Fetch open PRs ---
echo "📡 Fetching open PRs from GitHub..."
PR_API_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open&per_page=100")

# Validate response is a JSON array
if ! echo "$PR_API_RESPONSE" | jq -e 'type == "array"' >/dev/null; then
  echo "❌ GitHub API error:"
  echo "$PR_API_RESPONSE" | jq .
  exit 1
fi

PR_NUMBERS=$(echo "$PR_API_RESPONSE" | jq -r '.[].number')

if [ -z "$PR_NUMBERS" ]; then
  echo "✅ No open PRs to merge."
  exit 0
fi

# --- Merge each PR ---
for PR in $PR_NUMBERS; do
  echo "🔀 Merging PR #$PR..."
  PR_BRANCH="pr-$PR"

  if git fetch origin "refs/pull/$PR/head:$PR_BRANCH"; then
    echo "✅ Fetched PR #$PR"
  else
    echo "⏭️  Skipping PR #$PR — fetch failed"
    continue
  fi

  if git merge --no-edit --strategy=recursive --strategy-option=theirs "$PR_BRANCH"; then
    echo "✅ Merged PR #$PR cleanly"
  else
    echo "⚠️ Conflict in PR #$PR — committing with markers"
    git add -A
    git commit -m "Merge PR #$PR with conflict markers"
  fi

  git branch -D "$PR_BRANCH"
done

# --- Push merged main branch ---
echo "🚀 Pushing merged 'main' to origin..."
git push origin main

# --- Delete all remote branches except main ---
echo "🧹 Deleting all remote branches except 'main'..."
REMOTE_BRANCHES=$(git ls-remote --heads origin | awk '{print $2}' | sed 's|refs/heads/||' | grep -v '^main$')

for BR in $REMOTE_BRANCHES; do
  echo "❌ Deleting remote branch: $BR"
  git push origin --delete "$BR" || echo "⚠️ Failed to delete branch: $BR"
done

echo "✅ All PRs merged, main pushed, and remote branches cleaned up."
