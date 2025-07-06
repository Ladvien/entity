#!/bin/bash
set -euo pipefail

# --- Load token from .env if present ---
if [[ -f .env ]]; then
  echo "📦 Loading .env"
  source .env
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "❌ GITHUB_TOKEN is not set. Add it to .env or export it."
  exit 1
fi

# --- Detect repo ---
REMOTE_URL=$(git remote get-url origin)
if [[ "$REMOTE_URL" =~ github\.com[:/](.+)/(.+)\.git ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
else
  echo "❌ Unsupported remote URL: $REMOTE_URL"
  exit 1
fi

echo "🔍 Repo: $OWNER/$REPO"

# --- Ensure we're on main and up to date ---
git checkout main
git pull origin main

# --- Get all open PR numbers via GitHub API ---
echo "📡 Fetching open PRs..."
PR_NUMBERS=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open&per_page=100" \
  | jq -r '.[].number')

if [[ -z "$PR_NUMBERS" ]]; then
  echo "✅ No open PRs to merge"
  exit 0
fi

# --- Merge loop ---
for PR in $PR_NUMBERS; do
  echo "🔀 Merging PR #$PR..."

  PR_BRANCH="pr-$PR"
  if git fetch origin "refs/pull/$PR/head:$PR_BRANCH"; then
    echo "✅ Fetched PR #$PR"
  else
    echo "⏭️ Skipping PR #$PR — fetch failed"
    continue
  fi

  if git merge --no-edit --strategy=recursive --strategy-option=theirs "$PR_BRANCH"; then
    echo "✅ Merged PR #$PR cleanly"
  else
    echo "⚠️ Merge conflict in PR #$PR — committing with markers"
    git add -A
    git commit -m "Merge PR #$PR with conflict markers"
  fi

  git branch -D "$PR_BRANCH"
done

# --- Push merged main branch ---
echo "🚀 Pushing updated main branch to origin..."
git push origin main

# --- Delete all remote branches except main ---
echo "🧹 Deleting all remote branches except main..."
REMOTE_BRANCHES=$(git ls-remote --heads origin | awk '{print $2}' | sed 's|refs/heads/||' | grep -v '^main$')

for BR in $REMOTE_BRANCHES; do
  echo "❌ Deleting remote branch: $BR"
  git push origin --delete "$BR" || echo "⚠️ Failed to delete $BR"
done

echo "✅ Done merging and cleaning up."
