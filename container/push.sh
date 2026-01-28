#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------
# Load env file
# --------------------------------------------------
ENV_FILE="${ENV_FILE:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] Env file not found: $ENV_FILE"
  echo "[HINT ] Copy .env.example.posix to .env"
  exit 1
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

# --------------------------------------------------
# Validate required variables
# --------------------------------------------------
: "${GHCR_USERNAME:?ERROR: GHCR_USERNAME not set}"
: "${GHCR_TOKEN:?ERROR: GHCR_TOKEN not set}"
: "${GHCR_REGISTRY:?ERROR: GHCR_REGISTRY not set}"
: "${IMAGE_NAME:?ERROR: IMAGE_NAME not set}"

if [[ -z "${TAGS[*]:-}" ]]; then
  echo "[ERROR] TAGS not set"
  exit 1
fi

# --------------------------------------------------
# Login to GHCR (idempotent)
# --------------------------------------------------
echo "[INFO ] Logging into $GHCR_REGISTRY as $GHCR_USERNAME"

echo "$GHCR_TOKEN" | docker login "$GHCR_REGISTRY" \
  --username "$GHCR_USERNAME" \
  --password-stdin

# --------------------------------------------------
# Push images
# --------------------------------------------------
for tag in "${TAGS[@]}"; do
  image="$GHCR_REGISTRY/$IMAGE_NAME:$tag"
  echo "[PUSH ] $image"
  docker push "$image"
done

echo "[DONE ] All images pushed successfully"
