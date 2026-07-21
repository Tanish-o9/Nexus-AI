#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

BUCKET_NAME=${AWS_STATIC_BUCKET_NAME:-"nexus-pm-static-assets"}
DISTRIBUTION_ID=${AWS_CLOUDFRONT_DIST_ID:-""}

echo "=== 1. Building Django Backend Static Files ==="
cd backend
python manage.py collectstatic --noinput
cd ..

echo "=== 2. Building Next.js Frontend Static Files ==="
cd frontend
npm run build
cd ..

echo "=== 3. Syncing Assets to Amazon S3 ==="
# Sync backend static assets
aws s3 sync backend/staticfiles s3://$BUCKET_NAME/static/ --delete

# Sync frontend public and static assets
aws s3 sync frontend/public s3://$BUCKET_NAME/public/ --delete
aws s3 sync frontend/.next/static s3://$BUCKET_NAME/_next/static/ --delete

echo "=== 4. Creating CloudFront Invalidation ==="
if [ -n "$DISTRIBUTION_ID" ]; then
  aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/static/*" "/_next/*"
  echo "CloudFront invalidation triggered successfully."
else
  echo "Warning: AWS_CLOUDFRONT_DIST_ID not set. Skipping cache invalidation."
fi

echo "=== Asset Synchronization Complete ==="
