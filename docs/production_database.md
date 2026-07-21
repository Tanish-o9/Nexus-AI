# Production Database Architecture & Scaling Guide

This document defines the production database configurations, high-availability setups, connection pooling models, and pgvector performance tuning parameters for Nexus PM.

---

## 1. AWS RDS PostgreSQL Configuration

For production deployment, PostgreSQL is hosted on **Amazon RDS** (PostgreSQL 15 or 16).

### 1.1 High Availability (Multi-AZ)
- **Configuration**: Multi-AZ deployment enabled.
- **Mechanics**: RDS automatically provisions and maintains a synchronous standby replica in a different Availability Zone (AZ). All database writes are committed to both the primary and standby databases simultaneously.
- **Failover**: If the primary zone suffers an outage (power loss, hardware failure, network break), RDS executes an automatic DNS failover to the standby replica, typically completed in under 60 seconds without requiring application restarts.

### 1.2 Backups & Retention
- **Automated Backups**: Enabled by default, scheduled during low-traffic hours.
- **Retention Period**: 7 to 30 days depending on recovery agreements.
- **Point-in-Time Recovery (PITR)**: Enabled by archiving transaction logs (Write-Ahead Logs) to S3 every 5 minutes. This allows restoring the database to any millisecond within the retention window.

---

## 2. Connection Pooling (PgBouncer)

Because Django and FastAPI open new connection sockets per request, direct database limits are easily exhausted under heavy traffic. We mitigate this using **PgBouncer**.

```
[ Django / FastAPI API Clients ]
               │
               ▼ (Fast connection handshake on port 6432)
       [ PgBouncer Pooler ]
               │
               ▼ (Persistent pooled connections on port 5432)
   [ Amazon RDS PostgreSQL ]
```

### 2.1 Configuration Modes
1. **Transaction Mode (`pool_mode = transaction`)**: Connections are assigned to the client only during active transactions. Once the transaction (query) completes, the connection returns to the pool immediately. This is the optimal configuration for web apps, allowing 100 database connections to serve 1,000+ concurrent clients.
2. **Session Mode (`pool_mode = session`)**: Connections are held for the duration of the client's session. This is not recommended for API runners, as it behaves like direct database connections.

### 2.2 Pool Allocation Settings (`pgbouncer.ini`)
- `max_client_conn = 1000`: Allows up to 1,000 parallel clients to open sockets to PgBouncer.
- `default_pool_size = 20`: Restricts PgBouncer to holding a maximum of 20 persistent connections open to RDS.

---

## 3. pgvector Performance Tuning

The document chunk embedding table utilizes pgvector for semantic search. To maintain sub-second response times, we tune indexing parameters:

### 3.1 HNSW (Hierarchical Navigable Small World) Indexing
Ensure the HNSW index is generated with adequate search boundaries:
```sql
CREATE INDEX ON document_chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);
```
- **`m = 16`**: Defines the max number of bi-directional links connected to each node in the graph. Higher values improve accuracy for high-dimensional vectors but increase memory footprint.
- **`ef_construction = 64`**: Controls index build speed vs. recall accuracy. Re-indexing should be executed with larger values (`ef_construction = 128`) during scheduled maintenance.

### 3.2 Memory Allocation Tuning (`postgresql.conf`)
Ensure pgvector graphs reside completely in memory:
- **`shared_buffers`**: Set to **25% to 40%** of total system RAM.
- **`work_mem`**: Set to **64MB** to allow index-scanning calculations to execute in memory without writing temp files to disk.
