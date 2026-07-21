# Static Assets & CDN Scaling Guide

This document defines the production CDN (Content Delivery Network) topology and Amazon S3 asset bucket parameters for serving frontend and backend static assets in Nexus PM.

---

## 1. CDN & S3 Topology

We offload static assets from web containers to a combined **Amazon CloudFront** and **Amazon S3** distribution:

```
[ User Browser ]
       │
       ├──► (Asset request /static/* or /_next/*)
       ▼
 [ Amazon CloudFront Edge ] ───(Cache Hit: returns file in milliseconds)
       │
       ├──(Cache Miss)
       ▼
 [ Amazon S3 Static Bucket ]  (Private, bucket lock down enforced)
```

### 1.1 Origin Access Control (OAC) Bucket Lockdown
Direct public access to the S3 bucket is completely disabled. To allow CloudFront to fetch assets while keeping the bucket private, we use **Origin Access Control (OAC)**:
1. S3 bucket **Block all public access** is set to `True`.
2. The S3 bucket policy is restricted to accept requests originating only from our CloudFront distribution:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::nexus-pm-static-assets/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/E2T1EXAMPLECFID"
        }
      }
    }
  ]
}
```

---

## 2. S3 Bucket CORS Parameters

Certain assets (such as web fonts, SVG files, and JSON templates) require Cross-Origin Resource Sharing (CORS) configurations to load correctly in web browsers. We apply a strict CORS policy on the S3 bucket:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": ["https://nexuspm.io", "http://localhost:3000"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```
- **AllowedOrigins**: Specifies domain origins permitted to read these assets. Wildcards (`*`) are disabled in production.

---

## 3. Cache Invalidation Workflow

CloudFront caches static files at edge locations based on `Cache-Control` headers (defaulting to 24 hours or up to 1 year for versioned Next.js bundles). When deploying code updates, we trigger a **Cache Invalidation** to force edges to pull the new files:

- **Command**:
  ```bash
  aws cloudfront create-invalidation --distribution-id E2T1EXAMPLECFID --paths "/static/*" "/_next/*"
  ```
- **Automated Sync**: The deployment script [sync_assets.sh](file:///c:/Users/tanis/OneDrive/Desktop/nexus/scripts/sync_assets.sh) automatically coordinates building files, syncing them to S3, and calling the CloudFront invalidation hook in sequence.
