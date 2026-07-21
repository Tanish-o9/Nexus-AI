# AWS Minimal Deployment Architecture

This document defines the cloud infrastructure design for Nexus PM. In alignment with starting with the "smallest viable version first," we present a cost-efficient MVP setup alongside a migration blueprint for production-scale serverless deployment.

---

## 1. Cloud Architecture Overview

### Option A: The Minimum Viable Product (Single-Host EC2)
For early-stage testing and low budget:
- **Compute**: A single `t3.medium` EC2 instance (2 vCPUs, 4GB RAM) running Docker Compose. All microservices (`frontend`, `backend`, `ai-service`, `ml-service`) along with `redis` and `postgres/pgvector` run as Docker containers on this single VM.
- **Reverse Proxy**: Nginx handles SSL termination (Let's Encrypt) and routes traffic locally.
- **Estimated Cost**: ~$25–$35/month.

### Option B: The Production Target (Serverless ECS Fargate)
When ready to scale and decouple services:

```mermaid
flowchart TD
    Internet[Internet] -->|HTTPS| ALB[Application Load Balancer]
    
    subgraph Private Subnets (VPC)
        ALB -->|Route /| FE[ECS Fargate: Frontend]
        ALB -->|Route /api/v1/| BE[ECS Fargate: Backend]
        
        BE -->|Internal API| AI[ECS Fargate: AI Service]
        BE -->|Internal API| ML[ECS Fargate: ML Service]
        
        BE -->|Cache & Celery| Redis[(ElastiCache Redis)]
        BE -->|Query SQL| RDS[(RDS PostgreSQL pgvector)]
        AI -->|Vector Search| RDS
    end

    subgraph AWS Services (Shared)
        BE & AI -->|Save/Load Docs| S3[Amazon S3 Bucket]
        BE & AI & ML & FE -->|Write Logs| CW[CloudWatch Logs]
        BE & AI & ML & FE -->|Inject Credentials| SM[Secrets Manager]
    end
```

---

## 2. Infrastructure Component Specifications

### 2.1 Amazon S3 (Object Storage)
- **Use Case**: Holds uploaded user documents (PDFs, docx, CSVs) for the Document Ingestion Pipeline (Module 5.1).
- **Configuration**:
  - Block all public access enabled.
  - Encryption enabled by default (SSE-S3).
  - Versioning enabled (protects against accidental deletion of document chunks).

### 2.2 AWS Secrets Manager (Secrets Strategy)
- Avoid committing secrets to Git or raw environment variables.
- Store sensitive values (`DATABASE_URL`, `OPENAI_API_KEY`, `JWT_SECRET`) as a JSON secret in AWS Secrets Manager.
- **ECS Task Integration**: Map secrets directly in the ECS Task Definition. Fargate fetches and injects them into the container env on startup, ensuring raw secrets never touch disk or Github repositories.

### 2.3 CloudWatch (Logging & Telemetry)
- Set up the `awslogs` log driver in ECS Task Definitions or Docker daemon:
```json
"logConfiguration": {
    "logDriver": "awslogs",
    "options": {
        "awslogs-group": "/ecs/nexus-pm",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "backend"
    }
}
```
- Restrict retention period to 14 or 30 days to avoid billing inflation.

---

## 3. IAM Least-Privilege Policies

We define separate, narrow roles to restrict access boundaries.

### 3.1 ECS Task Execution Role (Container Lifecycle)
Allows Fargate to download images from ECR and fetch credentials from Secrets Manager.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789012:secret:nexus/prod/*"
    }
  ]
}
```

### 3.2 ECS Task Role (Runtime Permissions)
Grants the *running container process* permission to communicate with other AWS resources (e.g. S3).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::nexus-pm-document-vault",
        "arn:aws:s3:::nexus-pm-document-vault/*"
      ]
    }
  ]
}
```

---

## 4. Cost Optimization & Smallest Viable Steps

To launch the stack with minimal cash layout:
1. **DB**: Use a `db.t4g.micro` RDS PostgreSQL instance. It is covered under the AWS Free Tier and runs the standard PG vector extension.
2. **Cache**: Run `redis` inside the EC2 Docker context instead of provisioning a dedicated AWS ElastiCache node.
3. **SSL**: Terminate SSL on EC2 using Certbot Nginx. This avoids the requirement (and ~$20/month cost) of an AWS Application Load Balancer and AWS Certificate Manager (ACM) for the initial MVP.
