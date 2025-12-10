#!/bin/bash
set -e

TAG="0.0.5"
IMAGE="shark_event_payment_svc"
DOCKER_USERNAME=""
PLATFORMS="linux/amd64,linux/arm64"
PUSH_ONLY=false

while getopts i:t:u:p:P flag
do
    case "${flag}" in
        i) IMAGE=${OPTARG};;
        t) TAG=${OPTARG};;
        u) DOCKER_USERNAME=${OPTARG};;
        p) PLATFORMS=${OPTARG};;
        P) PUSH_ONLY=true;;
    esac
done

# Validate required parameters
if [ -z "$DOCKER_USERNAME" ]; then
    echo "❌ Error: Docker username is required. Use -u flag."
    exit 1
fi

IMAGE_NAME="$DOCKER_USERNAME/$IMAGE:$TAG"

# Create or use existing buildx builder
BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect $BUILDER_NAME >/dev/null 2>&1; then
    echo "🔧 Creating new buildx builder: $BUILDER_NAME"
    docker buildx create --name $BUILDER_NAME --use --bootstrap
else
    echo "🔧 Using existing buildx builder: $BUILDER_NAME"
    docker buildx use $BUILDER_NAME
fi

# Build and push the Docker image for multiple platforms
echo "🛠 Building and pushing Docker image: $IMAGE_NAME"
echo "📦 Platforms: $PLATFORMS"

if [ "$PUSH_ONLY" = true ]; then
    echo "🚀 Building and pushing directly to registry..."
    docker buildx build \
        --platform $PLATFORMS \
        --tag $IMAGE_NAME \
        --tag $DOCKER_USERNAME/$IMAGE:latest \
        --push \
        .
else
    echo "🔄 Building for local testing and registry..."
    # Build for local use (single platform)
    docker buildx build \
        --platform linux/amd64 \
        --tag $IMAGE_NAME \
        --load \
        .
    
    echo "🚀 Building and pushing multi-platform to registry..."
    docker buildx build \
        --platform $PLATFORMS \
        --tag $IMAGE_NAME \
        --tag $DOCKER_USERNAME/$IMAGE:latest \
        --push \
        .
fi

echo "✅ Successfully built and pushed to Docker Hub:"
echo "   📍 $IMAGE_NAME"
echo "   📍 $DOCKER_USERNAME/$IMAGE:latest"
echo "   🏗️  Platforms: $PLATFORMS"