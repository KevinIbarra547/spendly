#!/bin/sh
# One-time setup on each computer: turn on the Spendly loop guards.
cd "$(git rev-parse --show-toplevel)" || exit 1
chmod +x .githooks/pre-commit .githooks/pre-push
git config core.hooksPath .githooks
echo "Spendly loop guards are on (core.hooksPath = $(git config core.hooksPath))."
