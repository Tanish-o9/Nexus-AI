FROM nginx:1.25-alpine

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Ensure SSL directories exist
RUN mkdir -p /etc/nginx/ssl/live/localhost

# Generate mock self-signed SSL certificate so Nginx starts successfully
# out-of-the-box locally. In production, this folder is overridden via certbot volume binds.
RUN apk add --no-cache openssl && \
    openssl req -x509 -nodes -days 365 \
    -subj "/C=US/ST=Dev/L=Local/O=Nexus/CN=localhost" \
    -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/live/localhost/privkey.pem \
    -out /etc/nginx/ssl/live/localhost/fullchain.pem

EXPOSE 80 443
