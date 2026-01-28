#!/usr/bin/env sh
set -eu

# =====================================================
# Build configuration
# =====================================================
IMAGE_REGISTRY="ghcr.io"
IMAGE_NAMESPACE="bitconcepts"
IMAGE_NAME="zephyr-build-env"

ZEPHYR_VERSION="4.3.0"
ZEPHYR_SDK_VERSION="0.17.4"
UBUNTU_VERSION="22.04"

IMAGE_TAG="${ZEPHYR_VERSION}-sdk${ZEPHYR_SDK_VERSION}-ubuntu${UBUNTU_VERSION}"
IMAGE_FULL="${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"
IMAGE_LATEST="${IMAGE_REGISTRY}/${IMAGE_NAMESPACE}/${IMAGE_NAME}:latest"

# =====================================================
# Preconditions
# =====================================================
if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker not found in PATH"
  exit 1
fi

if [ ! -f "Dockerfile" ]; then
  echo "ERROR: Dockerfile not found in current directory"
  echo "Please run this script from the directory containing the Dockerfile"
  exit 1
fi

echo "Building Zephyr build container"
echo
echo "  Image:   $IMAGE_FULL"
echo "  Latest:  $IMAGE_LATEST"
echo "  Zephyr:  $ZEPHYR_VERSION"
echo "  SDK:     $ZEPHYR_SDK_VERSION"
echo "  Ubuntu:  $UBUNTU_VERSION"
echo

# =====================================================
# Build image
# =====================================================
if ! docker build \
  --build-arg ZEPHYR_SDK_VERSION="$ZEPHYR_SDK_VERSION" \
  -t "$IMAGE_FULL" \
  .; then
  echo "ERROR: docker build failed"
  exit 1
fi

# =====================================================
# Tag latest
# =====================================================
if ! docker tag "$IMAGE_FULL" "$IMAGE_LATEST"; then
  echo "ERROR: docker tag failed"
  exit 1
fi

echo
echo "Build complete."
echo
echo "To push the image:"
echo "  docker login $IMAGE_REGISTRY"
echo "  docker push $IMAGE_FULL"
echo "  docker push $IMAGE_LATEST"
echo
