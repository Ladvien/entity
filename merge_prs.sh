#!/bin/bash
set -euo pipefail

# --- Usage: cron job with path argument ---
# 0 * * * * /Users/ladvien/entity/merge_prs.sh /Users/ladvien/entity >> /Users/ladvien/merge.log 2>&1

if [[ $# -lt 1 ]]; then
  echo "❌ Usage: $0 /Users/ladvien/entity/"
  exit 1
fi

REPO_DIR="$1"
cd "$REPO_DIR"

# --- Load .env if it exists ---
if [[ -f .env ]]; then
  echo "📦 Loading .env"
  set -a
  source .env
  set +a
fi

# --- Check tools ---
for cmd in git curl jq; do
  if ! command -v "$cmd" >/dev/null; then
    echo "❌ Required command '$cmd' not found"
    exit 1
  fi
done

# --- Check for token ---
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "❌ GITHUB_TOKEN is not set"
  exit 1
fi

# --- Detect repo info ---
REMOTE_URL=$(git remote get-url origin)
REMOTE_CLEAN=${REMOTE_URL#*github.com[:/]}
OWNER=$(echo "$REMOTE_CLEAN" | cut -d'/' -f1)
REPO=$(echo "$REMOTE_CLEAN" | cut -d'/' -f2 | sed 's/\.git$//')

echo "🔍 Repo detected: $OWNER/$REPO"

# --- Update main ---
echo "📂 Checking out and updating 'main'..."
git checkout main
git pull origin main

# --- Fetch PRs ---
echo "📡 Fetching open PRs..."
PR_API_RESPONSE=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open&per_page=100")

if ! echo "$PR_API_RESPONSE" | jq -e 'type == "array"' > /dev/null; then
  echo "❌ GitHub API error:"
  echo "$PR_API_RESPONSE" | jq .
  exit 1
fi

# --- Filter PRs that are not checkpoint-related ---
PR_INFO=$(echo "$PR_API_RESPONSE" | jq -c '.[] | {number: .number, head: .head.ref}')
PR_NUMBERS=$(echo "$PR_INFO" | jq -r 'select(.head | contains("checkpoint") | not) | .number')

if [[ -z "$PR_NUMBERS" ]]; then
  echo "✅ No mergeable PRs (excluding checkpoint-related ones)."
  exit 0
fi

# --- Merge PRs ---
for PR in $PR_NUMBERS; do
  echo "🔀 Merging PR #$PR..."
  PR_BRANCH="pr-$PR"

  if git fetch origin "refs/pull/$PR/head:$PR_BRANCH"; then
    echo "✅ Fetched PR #$PR"
  else
    echo "⏭️  Skipping PR #$PR — fetch failed"
    continue
  fi

  if git merge --no-edit "$PR_BRANCH"; then
    echo "✅ Merged PR #$PR cleanly"
  else
    echo "⚠️ Conflict in PR #$PR — committing with markers"
    git add -A
    git commit -m "Merge PR #$PR with conflict markers"
  fi

  git branch -D "$PR_BRANCH"
done

# --- Push all merges (with or without conflicts) ---
echo "🚀 Pushing merged 'main' to origin..."
git push origin main

# --- Optional cleanup ---
# echo "🧹 Deleting all remote branches except 'main' and those with 'checkpoint'..."
# REMOTE_BRANCHES=$(git ls-remote --heads origin | awk '{print $2}' | sed 's|refs/heads/||' | grep -vE '^(main|.*checkpoint.*)$')
# for BR in $REMOTE_BRANCHES; do
#   echo "❌ Deleting remote branch: $BR"
#   git push origin --delete "$BR" || echo "⚠️ Failed to delete branch: $BR"
# done

echo "✅ All applicable PRs merged, conflicts preserved with markers, main pushed."
