# Production Cache Architecture & Scaling Guide

This document defines the production cache configuration, high-availability replication groups, eviction policies, and security parameters for AWS ElastiCache Redis in the Nexus PM ecosystem.

---

## 1. AWS ElastiCache Redis Configuration

In production, caching and message queuing are hosted on **Amazon ElastiCache for Redis** (Redis 7.x).

### 1.1 Replication Group (High Availability)
- **Topology**: 1 Primary node + 1 Read Replica.
- **Multi-AZ with Auto-Failover**: Enabled.
- **Failover Mechanics**: ElastiCache continuously monitors the primary node. If it becomes unresponsive, the read replica in the separate Availability Zone is promoted to primary, updating DNS configurations in under 30 seconds.
- **Read Scaling**: Read requests can be routed to the replica node to scale caching throughput, leaving the primary node focused on writes and queuing operations.

### 1.2 Redis Sharding (Cluster Mode)
- **Cluster Mode Disabled**: Recommended for early-scale. A single primary node supports up to 250MB/s bandwidth and over 50,000 requests/sec, which is more than sufficient for the Nexus stack.
- **Cluster Mode Enabled**: When memory requirements exceed 250GB, we migrate to Cluster Mode, distributing keys across multiple shards using hash slots.

---

## 2. Eviction Policies

Enforcing correct eviction rules prevents out-of-memory (OOM) crashes while protecting critical messaging queues.

### 2.1 Caching vs. Queuing Isolation
Because Redis is used both as a Django cache and a Celery message broker:
- **Cache Eviction (`allkeys-lru`)**: Evicts the least recently used keys when memory limits are reached. This is ideal for sessions, dashboard matrices, and query results.
- **Queue Eviction (`noeviction`)**: If Celery messages are evicted, background tasks (like recommendation training or notifications) are lost.
- **Architectural Fix**: We provision **two separate Redis databases/namespaces** (or separate ElastiCache clusters in high-load production):
  1. **Cache Cluster**: Configured with `maxmemory-policy allkeys-lru`.
  2. **Broker Cluster**: Configured with `maxmemory-policy noeviction`.

---

## 3. Encryption & Security

Cache data contains sensitive user session tokens and draft documents. We lock down the boundaries:

### 3.1 Encryption in Transit (TLS)
- **Configuration**: Enabled.
- **Access Control**: Connection strings require TLS negotiation and **Redis AUTH** password tokens.
- **Django Config**:
  ```python
  CACHES = {
      'default': {
          'BACKEND': 'django_redis.cache.RedisCache',
          'LOCATION': 'rediss://:auth_token_here@redis-primary.nexus.cache.amazonaws.com:6379/0',
          'OPTIONS': {
              'CONNECTION_POOL_KWARGS': {'ssl_cert_reqs': None}
          }
      }
  }
  ```
  *(Note the `rediss://` scheme which enforces TLS)*.

### 3.2 Encryption at Rest
- Enforce KMS encryption key management. Backups and cached snapshots on disk are encrypted using AWS-managed keys.

### 3.3 Network Security (Security Groups)
- Lock down the ElastiCache Security Group:
  - **Inbound Rules**: Allow TCP port `6379` ingress ONLY from the Security Group of the ECS Fargate Tasks (Backend / ML / Celery runners).
  - **Outbound Rules**: Restrict egress.
  - Reject all public internet traffic.
