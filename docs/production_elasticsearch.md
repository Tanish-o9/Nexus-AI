# Production Search Engine Architecture & Scaling Guide

This document defines the production Elasticsearch / Amazon OpenSearch Service configuration, node topologies, sharding strategies, backup processes, and network security boundaries for Nexus PM.

---

## 1. AWS OpenSearch Deployment Topology

In production, the search indexing engine is hosted on **Amazon OpenSearch Service** (compatible with Elasticsearch 8.x).

### 1.1 Node Layout (High Availability)
- **Deployment Strategy**: Multi-AZ (2-AZ) deployment enabled.
- **Node Allocation**:
  - **Data Nodes**: 2 nodes (e.g. `t3.medium.search` or `r6g.large.search` depending on data volume), distributed across two different Availability Zones. These nodes hold the indexes and execute search queries.
  - **Master Nodes**: For early production, combined master/data roles are used. As search volume scales, we provision 3 dedicated master nodes to handle cluster state operations and coordinator routing.

### 1.2 Shard & Replication Strategy
Proper shard count choices prevent memory fragmentation and "search storm" overhead:
- **Shards Mapping**:
  - **Primary Shards**: 1 primary shard per index. Since text indices for projects and document metadata are relatively small, a single primary shard handles up to 30GB of text data.
  - **Replica Shards**: 1 replica shard per index, placed in a different Availability Zone than the primary shard.
- **Benefits**: This topology guarantees that if one Availability Zone experiences an outage, search operations continue on the replica node in the healthy zone without data loss.

---

## 2. Backup & Retention (Snapshots)

- **Automated Snapshots**: Amazon OpenSearch Service automatically takes hourly/daily snapshots of the indices and stores them in a service-managed Amazon S3 bucket, retaining them for 14 days at no extra cost.
- **Custom Snapshot Policies (Index State Management)**:
  - We configure **ISM (Index State Management)** to automate lifecycle transitions.
  - Older indexes are transitioned from Hot storage (data nodes) to Warm storage (UltraWarm nodes) after 30 days, and automatically deleted or archived to cold storage (Glacier S3) after 90 days.

---

## 3. Security Policies & VPC Networking

Elasticsearch must never be exposed to the public internet (mitigating search database data leaks).

### 3.1 VPC Networking (Private Ingress)
- **Configuration**: OpenSearch endpoints are placed inside the private subnets of our Virtual Private Cloud (VPC).
- **Routing**: API services inside ECS Fargate communicate directly via VPC elastic network interfaces (ENIs), keeping search traffic completely off the public internet.

```
[ ECS Fargate (Private Subnets) ]
               │
               ▼ (Internal HTTPS Port 443)
[ AWS OpenSearch Domain (Private Subnets) ]
```

### 3.2 Security Group Configurations
- **Inbound Rules**: Allow TCP port `443` (HTTPS) ingress only from the Security Group of the API Backend/AI services. Reject all other traffic.

### 3.3 Domain Access Policies & Encryption
- **Transit Encryption**: HTTPS (TLS 1.2/1.3) enforced for all node-to-node and client-to-node communications.
- **At-Rest Encryption**: KMS key encryption enabled, securing all index segments, metadata, and snapshots.
- **Domain Access Policy**: Enforces IAM authorization to verify requests:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/nexus-ecs-task-role"
      },
      "Action": "es:ESHttp*",
      "Resource": "arn:aws:es:us-east-1:123456789012:domain/nexus-search/*"
    }
  ]
}
```
