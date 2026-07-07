#!/usr/bin/env bash
set -euo pipefail

# Enforce the repo policy on master via the GitHub API — version-controlled and
# reproducible instead of hand-clicked in Settings. Idempotent (PUT), re-runnable.
#
# Requires: `gh` authenticated with admin on the repo.
# Run this AFTER the first PR's CI has run at least once, so the required check
# contexts below are known to GitHub (otherwise they'd block every PR).
#
# Policy enforced:
#   - PRs only (no direct pushes), ≥1 approving review, stale reviews dismissed
#   - CI must pass (strict = branch up to date): lint + pytest on 3.10–3.13
#   - Signed commits required
#   - Linear history; no force-pushes, no branch deletion
#   - Conversation resolution required before merge

REPO="${1:-unidoc/isms-python}"
BRANCH="master"

echo "→ applying branch protection to ${REPO}@${BRANCH}"

gh api -X PUT "repos/${REPO}/branches/${BRANCH}/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["lint", "test (3.10)", "test (3.11)", "test (3.12)", "test (3.13)"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
JSON

# Signed-commit enforcement lives on its own endpoint.
gh api -X POST "repos/${REPO}/branches/${BRANCH}/protection/required_signatures" \
  -H "Accept: application/vnd.github+json" >/dev/null

echo "✅ ${REPO}@${BRANCH}: PR + 1 review, CI required (strict), signed commits, linear history, no force-push/deletion"
echo "   (enforce_admins is false so an owner keeps an emergency escape hatch — flip to true to bind admins too.)"
