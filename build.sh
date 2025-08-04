#!/bin/bash
# Deployment script for Render

echo "Starting Altona Village CMS deployment..."

# Build frontend
echo "Building frontend..."
cd altona-village-frontend
npm ci
npm run build

# Copy frontend build to Flask static folder
echo "Copying frontend build to Flask static folder..."
mkdir -p ../altona_village_cms/src/static
cp -r dist/* ../altona_village_cms/src/static/

echo "Build completed successfully!"
