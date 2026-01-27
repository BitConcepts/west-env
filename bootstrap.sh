#!/usr/bin/env bash
set -e

echo "Bootstrapping west-env..."

if ! command -v west >/dev/null; then
  echo "west not found"
  exit 1
fi

pip install -e .

if [ ! -f west-env.yml ]; then
  cp example/west-env.yml .
  echo "Created west-env.yml"
fi

echo
echo "Done."
echo
echo "Try:"
echo "  west env build"
echo "  west env shell"
