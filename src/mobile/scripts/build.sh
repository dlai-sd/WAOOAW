#!/bin/bash
# Build script for mobile app
# Automates EAS builds for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if EAS CLI is installed
if ! command -v eas &> /dev/null; then
    print_error "EAS CLI not found. Install it with: npm install -g eas-cli"
    exit 1
fi

# Check if logged in to Expo
if ! eas whoami &> /dev/null; then
    print_warning "Not logged in to Expo. Running 'eas login'..."
    eas login
fi

# Parse arguments
PROFILE=${1:-development}
PLATFORM=${2:-all}

print_info "Building WAOOAW Mobile App"
print_info "Profile: $PROFILE"
print_info "Platform: $PLATFORM"

# Validate profile
if [[ ! "$PROFILE" =~ ^(development|preview|production)$ ]]; then
    print_error "Invalid profile: $PROFILE. Must be one of: development, preview, production"
    exit 1
fi

# Validate platform
if [[ ! "$PLATFORM" =~ ^(ios|android|all)$ ]]; then
    print_error "Invalid platform: $PLATFORM. Must be one of: ios, android, all"
    exit 1
fi

# Change to mobile directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_info "Installing dependencies..."
    npm ci --legacy-peer-deps
fi

# Run tests before building (skip for development profile)
if [ "$PROFILE" != "development" ]; then
    print_info "Running tests..."
    npm test -- --passWithNoTests --bail || {
        print_error "Tests failed. Fix issues before building."
        exit 1
    }
fi

# Run TypeScript check
print_info "Running TypeScript check..."
npm run typecheck || {
    print_error "TypeScript errors found. Fix before building."
    exit 1
}

# Run linter
print_info "Running linter..."
npm run lint || {
    print_warning "Linter warnings found. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# Build with EAS
print_info "Starting EAS build..."

if [ "$PROFILE" == "production" ]; then
    print_warning "Building for PRODUCTION. Continue? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_info "Build cancelled."
        exit 0
    fi
fi

# Build command
eas build --platform "$PLATFORM" --profile "$PROFILE" --non-interactive

print_info "✅ Build initiated successfully!"
print_info "Check build status: https://expo.dev/accounts/YOUR_ACCOUNT/projects/waooaw-mobile/builds"
