#!/usr/bin/env sh
set -eu

echo "Running west-env round-trip test (POSIX)..."

west env doctor

echo "Testing shell startup..."
west env shell <<EOF
exit
EOF

echo "Round-trip test passed."
