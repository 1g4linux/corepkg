#!/usr/bin/env bash
set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

export PYTHONPATH="${repo_root}/lib${PYTHONPATH:+:${PYTHONPATH}}"

pytest_args=(
  -vv
  -ra
  -l
  -o
  console_output_style=count
)

# Keep one stable entry command and use xdist when available.
if pytest --help 2>/dev/null | grep -q -- "--dist="; then
  pytest_args+=(-n auto --dist=worksteal)
fi

exec pytest "${pytest_args[@]}" "$@"
