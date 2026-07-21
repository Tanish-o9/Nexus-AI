# Production SSL/TLS Certificate & Renewal Guide

This document defines the SSL/TLS configuration, domain verification steps, and automated renewal procedures for securing traffic ingress. It covers both AWS-managed setups (ACM) and self-managed containers (Certbot).

---

## 1. Managed SSL/TLS: AWS Certificate Manager (ACM)

For serverless deployments (ECS Fargate behind Application Load Balancers or CloudFront):
- **Provider**: AWS Certificate Manager (ACM).
- **SSL Termination Point**: Enforced at the **Application Load Balancer (ALB)** or CloudFront Edge, removing encryption/decryption CPU overhead from container nodes.
- **Verification Method**: DNS Validation (recommended over Email).
  - AWS generates a CNAME record mapping to a verification domain.
  - Inserting this CNAME into the Amazon Route 53 Hosted Zone completes verification.
- **Renewal Lifecycle**: **Fully Managed**. AWS ACM automatically renews certificates 60 days before expiration, requiring zero manual configuration.

---

## 2. Self-Managed SSL/TLS: Certbot (Let's Encrypt)

For single-host EC2 Docker Compose deployments, we terminate SSL directly on the host using Nginx and Certbot:

```
[ Client Browser ] ────► Port 80/443 ────► [ Nginx Container ]
                                                 │
                                                 ▼ (Challenge file checking)
                                           [ Certbot Volume ]
```

### 2.1 The ACME Challenge Setup
To issue a certificate without stopping Nginx, we use the **Webroot plugin**:
1. Nginx exposes a public directory for HTTP challenges:
   ```nginx
   location /.well-known/acme-challenge/ {
       root /var/www/certbot;
   }
   ```
2. Certbot writes a token file to the shared volume `/var/www/certbot`.
3. Let's Encrypt servers query `http://yourdomain.com/.well-known/acme-challenge/token`.
4. Once verified, Certbot downloads the private key and certificate chain to `/etc/letsencrypt/live/yourdomain/`.

### 2.2 Bootstrapping the Certificates
Since Nginx crashes if it has `ssl` server blocks but no certificate files exist, use the following bootstrap order:
1. **Initial Dry-run**: Spin up Nginx with HTTP (port 80) configs only.
2. **Issue Certs**: Execute the Certbot command to generate certificates:
   ```bash
   docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com -d www.yourdomain.com --email admin@yourdomain.com --agree-tos --no-eff-email
   ```
3. **Reload Nginx**: Mount the generated certificates, reload Nginx config to enable the HTTPS blocks.

---

## 3. Automated Renewal (Certbot Cron loop)

Let's Encrypt certificates are valid for 90 days. We automate verification check loops to run twice daily.

### 3.1 Docker Compose Renew Loop
The `nexus_certbot` container defined in `docker-compose.yml` runs a sleep loop that periodically checks Let's Encrypt status:
```yaml
entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
```
- **Frequency**: Runs `certbot renew` every 12 hours.
- **Nginx Reload Hook**: To ensure Nginx picks up the renewed certificate keys on the host, configure a host systemd cron job or docker trigger:
  ```bash
  # Cron trigger on host executing every day at 03:00 AM
  0 3 * * * docker exec nexus_nginx nginx -s reload
  ```
