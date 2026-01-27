#!/usr/bin/env sh
set -eu

echo "Running west-env container round-trip test..."

if ! command -v docker >/dev/null 2>&1 && ! command -v podman >/dev/null 2>&1; then
  echo "No container engine available, skipping"
  exit 0
fi

west env doctor --container

echo "Testing container shell startup..."
west env shell --container <<EOF
exit
EOF

echo "Container round-trip test passed."
