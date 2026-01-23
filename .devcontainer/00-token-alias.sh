#!/usr/bin/env bash

# Map a Codespaces secret (DLAISD_PAT) to standard GitHub CLI env vars.
# This does not store the token value in the repo; it only aliases an env var.

if [[ -n "${DLAISD_PAT:-}" ]]; then
	# If a user explicitly provided DLAISD_PAT, prefer it over any existing values.
	# This prevents subtle failures when a default/placeholder GH_TOKEN is present.
	export GH_TOKEN="$DLAISD_PAT"
	export GITHUB_TOKEN="$DLAISD_PAT"
fi
