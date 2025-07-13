#!/bin/bash
set -euo pipefail

# 0 * * * * /Users/ladvien/entity/merge_prs.sh /Users/ladvien/entity >> /Users/ladvien/merge.log 2>&1


# --- Check that a path was passed --- 
if [[ $# -lt 1 ]]; then
  echo "❌ Usage: $0 /Users/ladvien/entity"
  exit 1
fi

REPO_DIR="$1"

# --- Verify git repo ---
if [[ ! -d "$REPO_DIR/.git" ]]; then
  echo "❌ $REPO_DIR is not a valid Git repository"
  exit 1
fi

cd "$REPO_DIR"

# --- Load .env if it exists ---
if [[ -f .env ]]; then
  echo "📦 Loading .env"
  # Use `set -a` to export all variables temporarily
  set -a
  source .env
  set +a
fi

# --- Check dependencies ---
for cmd in git curl jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "❌ Required command '$cmd' not found in PATH"
    exit 1
  fi
done

# --- Validate GitHub token ---
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "❌ GITHUB_TOKEN is not set. Add it to .env or export it."
  exit 1
fi

# --- Parse remote repo ---
REMOTE_URL=$(git remote get-url origin 2>/dev/null || true)

if [[ -z "$REMOTE_URL" ]]; then
  echo "❌ Could not detect remote origin"
  exit 1
fi

REMOTE_CLEAN="${REMOTE_URL#*github.com[:/]}"
OWNER=$(echo "$REMOTE_CLEAN" | cut -d'/' -f1)
REPO=$(echo "$REMOTE_CLEAN" | cut -d'/' -f2 | sed 's/\.git$//')

if [[ -z "$OWNER" || -z "$REPO" ]]; then
  echo "❌ Failed to extract owner/repo from: $REMOTE_URL"
  exit 1
fi

echo "🔍 Repo detected: $OWNER/$REPO"

# --- Checkout and update main ---
echo "📂 Checking out and updating 'main'..."
git checkout main
git pull origin main

# --- Fetch open PRs ---
echo "📡 Fetching open PRs from GitHub..."
PR_API_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open&per_page=100")

if ! echo "$PR_API_RESPONSE" | jq -e 'type == "array"' > /dev/null; then
  echo "❌ GitHub API error:"
  echo "$PR_API_RESPONSE" | jq .
  exit 1
fi

PR_NUMBERS=$(echo "$PR_API_RESPONSE" | jq -r '.[].number')

if [[ -z "$PR_NUMBERS" ]]; then
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

# --- Push changes ---
echo "🚀 Pushing merged 'main' to origin..."
git push origin main

# --- Clean up remote branches ---
echo "🧹 Deleting all remote branches except 'main'..."
REMOTE_BRANCHES=$(git ls-remote --heads origin | awk '{print $2}' | sed 's|refs/heads/||' | grep -v '^main$')

for BR in $REMOTE_BRANCHES; do
  echo "❌ Deleting remote branch: $BR"
  git push origin --delete "$BR" || echo "⚠️ Failed to delete branch: $BR"
done

echo "✅ All PRs merged, main pushed, and remote branches cleaned up."



