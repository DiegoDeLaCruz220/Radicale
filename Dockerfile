FROM python:3.11-slim

WORKDIR /app

# Install Radicale and dependencies
RUN pip install --no-cache-dir \
    radicale==3.2.0 \
    psycopg2-binary \
    bcrypt

# Copy configuration and storage plugin
COPY config /etc/radicale/config
COPY supabase_storage.py /app/supabase_storage.py

# Create data directory
RUN mkdir -p /data/radicale

# Expose CardDAV port
EXPOSE 5232

# Run Radicale
CMD ["radicale", "--config", "/etc/radicale/config"]
