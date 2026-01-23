#!/usr/bin/env bash

# Map a Codespaces secret (DLAISD_PAT) to standard GitHub CLI env vars.
# This does not store the token value in the repo; it only aliases an env var.

if [[ -n "${DLAISD_PAT:-}" ]]; then
	# Prefer not to overwrite any existing tokens.
	export GH_TOKEN="${GH_TOKEN:-$DLAISD_PAT}"
	export GITHUB_TOKEN="${GITHUB_TOKEN:-$DLAISD_PAT}"
fi
