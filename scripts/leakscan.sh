#!/usr/bin/env bash
# Pre-publish leak gate. Refuses to let the four "never ships" categories out:
#   1. model-relay / subscription-resale internals   2. customer data
#   3. secrets (keys/tokens/private keys/htpasswd)    4. infrastructure topology
#
# Run before every push:  bash scripts/leakscan.sh
# Exit non-zero on any hit. Tune patterns to your environment.
set -u
cd "$(dirname "$0")/.." || exit 2

# Scan tracked + untracked files, excluding the repo's own scanner and git internals.
# Exclude the scanner and .gitignore: both legitimately list these keywords as patterns.
mapfile -t FILES < <(git ls-files --cached --others --exclude-standard 2>/dev/null \
  | grep -vE '^(scripts/leakscan\.sh|\.gitignore)$')
[ "${#FILES[@]}" -eq 0 ] && { echo "leakscan: no files to scan"; exit 0; }

# pattern|human-readable reason
PATTERNS=(
  'relay|model-relay internals must not ship'
  'oauth[_-]?token|OAuth token / pooling must not ship'
  'envelope[_-]?spoof|identity-spoof internals must not ship'
  'resell|subscription resale internals must not ship'
  'BEGIN [A-Z ]*PRIVATE KEY|private key material'
  'sk-[A-Za-z0-9]{16,}|API key / secret token'
  'htpasswd|credential file'
  'chipflowai\.com|internal hostname'
  '\b(8\.211\.[0-9]+\.[0-9]+|192\.168\.66\.[0-9]+)\b|internal IP address'
  'BEGIN OPENSSH PRIVATE KEY|ssh private key'
)

hits=0
for entry in "${PATTERNS[@]}"; do
  pat="${entry%%|*}"; reason="${entry#*|}"
  if matches=$(grep -rInE --binary-files=without-match "$pat" "${FILES[@]}" 2>/dev/null); then
    echo "LEAK [$reason]:"
    echo "$matches" | sed 's/^/    /'
    hits=$((hits + 1))
  fi
done

if [ "$hits" -gt 0 ]; then
  echo "leakscan: $hits category/categories tripped -- DO NOT PUBLISH."
  exit 1
fi
echo "leakscan: clean."
