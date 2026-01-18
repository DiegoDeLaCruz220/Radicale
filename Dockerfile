FROM python:3.11-slim

WORKDIR /app

# Install Radicale and dependencies
RUN pip install --no-cache-dir \
    radicale==3.2.0 \
    requests \
    bcrypt

# Copy configuration and storage plugin
COPY config /etc/radicale/config
COPY supabase_storage.py /app/supabase_storage.py
COPY supabase_auth.py /app/supabase_auth.py
COPY supabase_rights.py /app/supabase_rights.py
COPY supabase_rights.py /app/supabase_rights.py

# Set Python path so Radicale can find our custom storage module
ENV PYTHONPATH=/app

# Expose CardDAV port
EXPOSE 5232

# Run Radicale
CMD ["radicale", "--config", "/etc/radicale/config"]
